#pragma once
#include <vector>
#include <cmath>
#include <algorithm>
#include <juce_core/juce_core.h>

/**
 * Modal Resonator - core DSP component of TsukiSynth
 *
 * Decomposes vibration into N independent decaying sinusoids (modes).
 * Each mode has its own frequency, amplitude, and decay time.
 *
 *   output(t) = sum[ amp[n] * 10^(-3t/T60[n]) * sin(2*pi*freq[n]*t) ]
 *
 * Mode parameters are computed by physics models (StringModel / BeamModel / PlateModel)
 * and passed in. This module only handles efficient rendering.
 */
class ModalResonator
{
public:
    static constexpr float minimumRenderableFrequency = 20.0f;
    static constexpr float productMaximumFrequency = 20000.0f;

    /// Physical description of a single mode
    struct Mode
    {
        float frequency = 440.0f;   // Hz
        float amplitude = 1.0f;     // initial amplitude (from strike position)
        float decayTime = 1.0f;     // seconds (from material damping)
    };

    void setSampleRate (double sr) { sampleRate = sr; }
    void reserveModes (size_t count) { modes.reserve (count); }

    static float maximumRenderableFrequency (double sr)
    {
        return (float) std::min ((double) productMaximumFrequency,
                                 sr * 0.5 * 0.98);
    }

    /** True only when a mode is inside the frequency domain that the DSP
        actually synthesizes.  Model generation, diagnostic dumps and the
        renderer must share this predicate: otherwise an inaudible model can
        be reported as verified while ModalResonator silently discards it. */
    static bool isRenderableFrequency (float frequency, double sr)
    {
        return std::isfinite (frequency)
            && frequency >= minimumRenderableFrequency
            && frequency <= maximumRenderableFrequency (sr);
    }

    /// Set modes (computed by physics model, passed in)
    void setModes (const std::vector<Mode>& newModes)
    {
        modes.clear();
        modes.reserve (newModes.size());

        for (const auto& newMode : newModes)
        {
            if (! isRenderableFrequency (newMode.frequency, sampleRate)
                || ! std::isfinite (newMode.amplitude)
                || ! std::isfinite (newMode.decayTime)
                || newMode.decayTime <= 0.0f)
                continue;

            ModeState state;
            state.freq       = newMode.frequency;
            state.baseAmp    = newMode.amplitude;
            state.decayTime  = newMode.decayTime;
            modes.push_back (state);
        }
    }

    /// Excite (MIDI note on)
    void excite (float velocity)
    {
        active = false;
        for (auto& m : modes)
        {
            // setModes() already filters this domain; retain a defensive check
            // in case a future real-time frequency update crosses the limit.
            if (! isRenderableFrequency (m.freq, sampleRate))
            {
                m.currentAmp = 0.0f;
                m.stopAmp = 0.0f;
                continue;
            }

            m.currentAmp = m.baseAmp * velocity;
            m.stopAmp    = std::abs (m.currentAmp) * 0.001f; // exactly -60 dB
            m.phase      = 0.0f;
            m.phaseDelta = m.freq * (float) juce::MathConstants<double>::twoPi / (float) sampleRate;

            // decay coefficient: reach -60dB (~0.001) after decayTime seconds
            if (m.decayTime > 0.0f)
                m.decayCoeff = std::exp (-6.9078f / (m.decayTime * (float) sampleRate));
            else
                m.decayCoeff = 0.0f;

            if (std::isfinite (m.currentAmp) && m.stopAmp > 0.0f
                && std::isfinite (m.decayTime) && m.decayTime > 0.0f)
                active = true;
        }
    }

    /// Damp (damper off / note off - accelerate decay)
    void damp (float factor = 0.05f)
    {
        for (auto& m : modes)
        {
            float shortened = m.decayTime * factor;
            if (shortened > 0.0f)
                m.decayCoeff = std::exp (-6.9078f / (shortened * (float) sampleRate));
            else
                m.decayCoeff = 0.0f;
        }
    }

    /** 單一 mode 在攻擊窗（前 windowSeconds 秒）內的能量預測。
     *
     * 包絡 amp·exp(-6.9078·t/T60)（processSample() 用的同一 -60dB 衰減律）、
     * sin² 時間平均 = 1/2，解析積分：
     *   e = amp² · (1/2) · (1 - exp(-2λ·Tw)) / (2λ)，λ = 6.9078 / T60
     * 不可渲染的頻率回傳 0，與 setModes() 的過濾一致——否則超出
     * Nyquist / 20kHz 而不會發聲的模態會虛增能量估計。
     *
     * 窗長 0.3s 的取捨：太短會被單一模態的相位巧合主導，太長則高音
     * （T60 短）被「音本來就短」二次懲罰——這裡要補償的是攻擊段響度，
     * 不是把整體衰減長度也拉平（那是真實樂器本來就有的音域個性）。
     */
    static float modeAttackEnergy (float frequency, float amplitude,
                                   float decayTime, double sr,
                                   float windowSeconds = 0.3f)
    {
        if (! isRenderableFrequency (frequency, sr)
            || ! std::isfinite (amplitude)
            || ! std::isfinite (decayTime) || decayTime <= 0.0f)
            return 0.0f;

        const float twoLambda = 2.0f * 6.9078f / decayTime;
        return amplitude * amplitude * 0.5f
               * (1.0f - std::exp (-twoLambda * windowSeconds)) / twoLambda;
    }

    /** 跨音域響度補償增益（noteOn 時一次算好的決定性 scalar，非 AGC）。
     *
     *   gain = (refEnergy / attackEnergy)^(amount/2)
     *
     * amount = 部分補償：真實樂器音域間本來就有響度差
     * （高音短而稍弱），補滿 1.0 會把這個個性完全抹平，聽感假。
     * 0.78 為月月 2026-08-06 審聽裁決（0.7 版「高音偏低一點點」→上調；
     * 0.85 試過後定案 0.78，兼顧聽感與 78 的吉祥寓意——月月欽點，勿改）。
     * refEnergy 是各引擎在 A4、預設參數下量到的攻擊能量錨點
     * （gain(A4) = 1，中音域維持既有 equal-RMS 校準）。
     * clamp ±12 dB 防止病態模態組合（例如全部被 Nyquist 濾掉）爆增益。
     * 對整組 mode 乘同一 scalar：模態間相對振幅不變，--dump-modes 的
     * relative_modal_amplitude 檢驗與頻譜形狀完全不受影響。
     */
    static float loudnessCompensationGain (float attackEnergy, float refEnergy,
                                           float amount = 0.78f)
    {
        if (! (attackEnergy > 1.0e-12f) || ! (refEnergy > 0.0f))
            return 1.0f;

        const float g = std::pow (refEnergy / attackEnergy, 0.5f * amount);
        return juce::jlimit (0.25f, 4.0f, g);
    }

    /// Render one sample
    float processSample()
    {
        if (! active)
            return 0.0f;

        float output = 0.0f;
        bool anyActive = false;

        for (auto& m : modes)
        {
            if (std::abs (m.currentAmp) <= m.stopAmp || m.stopAmp <= 0.0f)
                continue;

            output += m.currentAmp * std::sin (m.phase);

            m.phase += m.phaseDelta;
            if (m.phase >= (float) juce::MathConstants<double>::twoPi)
                m.phase -= (float) juce::MathConstants<double>::twoPi;

            m.currentAmp *= m.decayCoeff;
            anyActive = true;
        }

        if (! anyActive)
            active = false;

        return output;
    }

    /// Render into a buffer (additive)
    void processBlock (float* buffer, int numSamples)
    {
        for (int i = 0; i < numSamples; ++i)
            buffer[i] += processSample();
    }

    /// Update mode frequencies without resetting phase or amplitude (for pitch glide)
    void updateFrequencies (const std::vector<Mode>& newModes)
    {
        int n = juce::jmin ((int) modes.size(), (int) newModes.size());
        for (int i = 0; i < n; ++i)
        {
            modes[(size_t) i].freq = newModes[(size_t) i].frequency;
            modes[(size_t) i].phaseDelta = newModes[(size_t) i].frequency
                * (float) juce::MathConstants<double>::twoPi / (float) sampleRate;
        }
    }

    void scaleFrequencies (double factor)
    {
        for (auto& m : modes)
            m.phaseDelta = m.freq * (float) factor
                           * (float) juce::MathConstants<double>::twoPi / (float) sampleRate;
    }

    bool isActive() const { return active; }

    int getActiveModeCount() const
    {
        int count = 0;
        for (const auto& m : modes)
            if (std::abs (m.currentAmp) > m.stopAmp && m.stopAmp > 0.0f) ++count;
        return count;
    }

    /// Snapshot current modes (frequency / amplitude / decay) for the CLI
    /// --dump-modes single-source-of-truth verification path.
    std::vector<Mode> getModes() const
    {
        std::vector<Mode> out;
        out.reserve (modes.size());
        for (const auto& m : modes)
            out.push_back ({ m.freq, m.baseAmp, m.decayTime });
        return out;
    }

private:
    struct ModeState
    {
        float freq       = 0.0f;
        float baseAmp    = 0.0f;
        float decayTime  = 0.0f;
        float phase      = 0.0f;
        float phaseDelta = 0.0f;
        float currentAmp = 0.0f;
        float stopAmp    = 0.0f;
        float decayCoeff = 1.0f;
    };

    double sampleRate = 44100.0;
    std::vector<ModeState> modes;
    bool active = false;
};
