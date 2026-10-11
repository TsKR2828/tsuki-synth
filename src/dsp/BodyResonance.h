#pragma once
#include "BiquadFilter.h"
#include "ModalResonator.h"
#include <cmath>
#include <complex>
#include <algorithm>

// Procedural body resonance — two resonant bandpass filters
// driven by the engine output, adding low-end weight and fullness.
// Designed to be lightweight and per-voice.

class BodyResonance
{
public:
    void prepare (double sampleRate)
    {
        sr = sampleRate;
        updateFilters();
    }

    void setAmount (float amt)
    {
        amount = std::clamp (amt, 0.0f, 1.0f);
    }

    void setFrequencies (float lowHz, float lowMidHz)
    {
        lowFreq    = lowHz;
        lowMidFreq = lowMidHz;
        updateFilters();
    }

    // ── WF1003-B2 (月月 2026-10-03 裁決 B2＝A)：Body 層響度正規化 ───────────
    //
    // 問題：Body 兩個共振帶通被 configureCreativeBodyLayer() 調到「這顆音自己
    // 的第 1、2 個模態」，所以 dry+wet 的轉移函數在基頻上是 +6.5～+16.8 dB
    // （Body 0.2～1.0；預設 0.5 為 +11.9 dB，0.8 為 +15.2 dB），Body 旋鈕因此
    // 同時改了音色與音量（reports/wf1002_preset_overshoot_root_cause.zh-TW.md §4）。
    //
    // 做法（推導見 reports/wf1003_b2_body_normalization_before_after.zh-TW.md §2；
    // 登記在 ROADMAP_PHYSICS.md §6 的「Body 層響度正規化」列）：對整個 dry+wet
    // 輸出乘一個 note-on 時算好的 scalar g，使 Body 開／關的「起音能量」相等：
    //
    //     g = sqrt( E_dry / E_body ),
    //     E_dry  = Σ_i  Ê_i                    Ê_i = ModalResonator::modeAttackEnergy
    //                                                (f_i, a_i, T60_i, sr)
    //     E_body = Σ_i  Ê_i · |H(f_i)|²        H = totalResponse()（dry+wet 穩態轉移）
    //
    // 其中 Ê_i 是引擎本來就在用的「前 0.3 s 模態攻擊能量」(同一支函式、同一個
    // 0.3 s 視窗，跨音域響度補償 loudnessCompensationGain() 用的就是它)，|H(f_i)|
    // 直接讀本類別的 BiquadFilter 係數（和 --dump-modes 的 body_mag 同一份），
    // 所以 g 是 Body 旋鈕值（amount）與該音模態表的解析函數，沒有任何手調常數；
    // 模態彼此正交（Parseval），能量逐模態相加是精確的。
    // WF1004-B2b（月月 2026-10-07 裁決）：實際套用的增益是 min(g, 1)——只准衰減、不准放大，
    // 1＝不放大（等於改前未補償行為），無新常數。套用後起音能量 E_out = min(g,1)²·E_body = min(E_dry, E_body)
    // ≤ E_dry（穩態近似下）；g>1 的情況（能量落在 H 的陷波上）等於不補償＝WF1003 之前的行為，
    // 輸出恆不大於改前（逐樣本 |g·y| ≤ |y|）。見報告 §2。
    // 當能量集中在基頻（弦、梁的典型情況）時，g 趨近 1/|H(f1)|；當能量分散在不
    // 和諧模態（鑼）時，g 比單看基頻小得多——這正是能量法比「只看基頻」準的地方。
    //
    // 僅外掛的 startNote() 路徑呼叫；CLI／ScoreRenderer 的 noteOn() 路徑
    // 呼叫 clearLevelNormalisation()（Body 預設 0，CLI 位元不受影響）。
    // 未呼叫時 processSample()／totalResponse() 與 WF1003 之前逐位元相同。
    // 限制：只涵蓋模態（弦／梁／板／自訂泛音）能量，不含槌頭噪音脈衝（數 ms）；
    // 水鑼的 pitch glide 會讓模態頻率漸漸偏離 note-on 時的濾波器中心，g 不隨之更新。
    void setLevelNormalisation (const ModalResonator::Mode* modes, size_t numModes)
    {
        normGain = 1.0f;
        levelNormalised = true;

        if (amount < 0.001f || modes == nullptr || sr <= 0.0)
            return;

        double eDry = 0.0, eBody = 0.0;
        for (size_t i = 0; i < numModes; ++i)
        {
            const float w = ModalResonator::modeAttackEnergy (
                modes[i].frequency, modes[i].amplitude, modes[i].decayTime, sr);
            if (! (w > 0.0f))
                continue;
            const float h = std::abs (rawTotalResponse (modes[i].frequency));
            eDry  += (double) w;
            eBody += (double) w * (double) h * (double) h;
        }

        if (eDry > 1.0e-18 && eBody > 1.0e-18)
        {
            // WF1004-B2b (月月 2026-10-07 裁決「照 Fable 建議」＝g = min(g, 1)):
            // normalisation may only ATTENUATE, never amplify. 1 means no amplification, i.e. the pre-B2
            // baseline, so this introduces no new constant. Why: the g above comes
            // from a steady-state |H|; when most modal energy sits in a deep notch
            // of H, g is huge, but the filters need a few ms to build up, during
            // which the output is ~dry -- g would then amplify the onset transient
            // (WF1003-B2 audit: +14.8 dBFS, +22.7 dB louder than pre-B2). With
            // g <= 1 the output can never exceed the pre-B2 behaviour.
            // This is the ONLY place normGain is assigned a non-1 value
            // (clearLevelNormalisation() resets it to 1).
            const float g = (float) std::sqrt (eDry / eBody);
            if (std::isfinite (g))
                normGain = std::min (g, 1.0f);
        }
    }

    void clearLevelNormalisation()
    {
        levelNormalised = false;
        normGain = 1.0f;
    }

    /// Applied level scalar (1.0 when normalisation is off). Read by tests/HostProbe-style
    /// probes and by the B2 report; not used by the audio path (processSample() has it cached).
    float levelNormalisationGain() const { return levelNormalised ? normGain : 1.0f; }

    void reset()
    {
        lpLow.reset();
        bpLow.reset();
        bpMid.reset();
    }

    // Process one sample: returns the body component to be mixed in
    //
    // M1-1d velocity-linearity fix (2026-07): this used to also multiply by an
    // envelope follower (envLevel) tracking |input|. Since the resonant filters
    // below are already linear and driven by `input` (which is itself
    // proportional to velocity via ModalResonator::excite()), multiplying their
    // output by a SECOND input-derived envelope made the body-resonance term
    // scale as velocity^2, not velocity^1 -- the source of the M1-1d superlinear
    // RMS failures (cimbalom/tongue_drum/water_gong/piano all route through this
    // shared component). A passive resonant body (soundboard) is a linear
    // system in the small-signal regime: output amplitude ∝ driving force
    // (F = m·a, struck body's response scales with impulse strength), so the
    // resonant bandpass filters alone -- already amplitude- and time-envelope-
    // following because they are driven sample-by-sample by the decaying
    // `input` -- are the correct and sufficient body-resonance model. No
    // separate multiplicative envelope is applied.
    float processSample (float input)
    {
        if (amount < 0.001f)
            return 0.0f;

        // Drive the resonant filters with the input signal
        float low = bpLow.processSample (input);
        float mid = bpMid.processSample (input);

        // Low-pass to tame any harshness from the BP resonance
        float body = lpLow.processSample (low * 1.4f + mid * 0.8f);

        if (! levelNormalised)
            return body * amount * 4.0f;

        // WF1003-B2: caller adds this to `input` (sample += processSample(sample)),
        // so returning (g-1)*dry + g*wet makes the summed output g*(dry+wet).
        return (normGain - 1.0f) * input + normGain * (body * amount * 4.0f);
    }

    // 2026-07 (--amps GATE fix, ROADMAP_PHYSICS.md M2-2d root-cause: see
    // reports/gate_outputs/amps_rootcause_analysis.md Experiment 2/3). This
    // component is mixed additively as `sample += bodyRes.processSample
    // (sample)`, i.e. the *actual* rendered path is `dry + wet`, not `wet`
    // alone. --dump-modes previously reported the pre-BodyResonance
    // ModalResonator amplitude, silently comparing to a signal that is never
    // rendered. totalResponse() closes that gap by evaluating the exact
    // steady-state complex transfer function of the full dry+wet path at a
    // given frequency, built from the SAME BiquadFilter coefficient objects
    // (bpLow/bpMid/lpLow) that processSample() drives sample-by-sample above
    // -- i.e. this is a read of the model's own linear operator, not an
    // independent re-derivation and not anything derived from rendered audio.
    // Steady-state (as opposed to a full per-sample convolution) is a
    // deliberate, documented approximation: valid when the filters' own
    // settling time (~Q/(pi*f), a few ms for these Q=1.4-1.8 resonances) is
    // short relative to the modal partial's decay time, which holds for every
    // partial inside physics_verify's "weak, not assessed" floor. Matches
    // Python `bodyres.py` prototype's analytic result to within rounding.
    std::complex<float> totalResponse (float freqHz) const
    {
        const std::complex<float> h = rawTotalResponse (freqHz);
        return levelNormalised ? h * normGain : h;   // WF1003-B2: g = 1 unless normalised
    }

    // |dry+wet| at freqHz -- the number --dump-modes needs (Experiment 3's
    // "|H_total(f)|" table), read straight from the live filter state.
    float magnitudeAt (float freqHz) const { return std::abs (totalResponse (freqHz)); }

private:
    // dry+wet steady-state transfer function WITHOUT the B2 level scalar.
    std::complex<float> rawTotalResponse (float freqHz) const
    {
        if (amount < 0.001f)
            return { 1.0f, 0.0f };
        std::complex<float> hLow = bpLow.responseAt (freqHz);
        std::complex<float> hMid = bpMid.responseAt (freqHz);
        std::complex<float> hLp  = lpLow.responseAt (freqHz);
        std::complex<float> wet  = amount * 4.0f * (1.4f * hLow + 0.8f * hMid) * hLp;
        return std::complex<float> (1.0f, 0.0f) + wet;
    }

    double sr         = 44100.0;
    float  amount     = 0.0f;
    bool   levelNormalised = false;   // WF1003-B2: plug-in startNote() path only
    float  normGain   = 1.0f;
    float  lowFreq    = 120.0f;
    float  lowMidFreq = 280.0f;

    BiquadFilter bpLow;   // resonant BP at ~120 Hz
    BiquadFilter bpMid;   // resonant BP at ~280 Hz
    BiquadFilter lpLow;   // LP to smooth the combined body

    void updateFilters()
    {
        if (sr <= 0.0) return;

        bpLow.setSampleRate (sr);
        bpLow.setParams (BiquadFilter::Type::BandPass, lowFreq, 1.8f);

        bpMid.setSampleRate (sr);
        bpMid.setParams (BiquadFilter::Type::BandPass, lowMidFreq, 1.4f);

        lpLow.setSampleRate (sr);
        lpLow.setParams (BiquadFilter::Type::LowPass, 500.0f, 0.707f);
    }
};
