#pragma once
#include <juce_audio_processors/juce_audio_processors.h>
#include "../dsp/ModalResonator.h"
#include "../dsp/NoiseGen.h"
#include "../dsp/BiquadFilter.h"
#include "../dsp/BodyResonance.h"
#include "../dsp/Envelope.h"
#include "../dsp/DiagnosticOverrides.h"
#include "../physics/StringModel.h"
#include "../physics/MaterialDB.h"
#include "../physics/HammerImpulse.h"
#include <array>

/**
 * Cimbalom 引擎 — 物理建模弦振動
 *
 * 架構：
 *   MIDI Note On → Exciter (槌頭噪音脈衝)
 *                → String Resonator ×N (微失諧 beating)
 *                → output
 *
 *   MIDI Note Off / CC#64 → Damper (加速衰減)
 */

static constexpr int kMaxStringsPerCourse = 5;

// 跨音域響度補償錨點：A4、預設參數（steel / strike 0.3 / Ø0.8mm / Wood 槌）
// 下、以 velocity=0.5 Hertz 錨 τc 預估的攻擊窗能量 Σ modeAttackEnergy()
// （2026-08-21 B2 收尾重測值〔量測，非文獻/推導〕：B1 琴橋導納落地後
// A4 的 T60 因新增第四項損耗再次縮短，攻擊能量由 0.1497 降為 0.0874。
// 量測方法＝中央弦反解法，逐步數字與一次性腳本見
// reports/gate_outputs/b2_attack_energy_remeasure.txt；歷史：0.1609 →
// 0.1497〔2026-08-10 寬頻化〕→ 0.0874〔B1〕）。
// gain(A4) = 1，中音域維持既有 equal-RMS 校準；
// 見 ModalResonator::loudnessCompensationGain() 與 noteOn() 內 tauCRef 註解。
static constexpr float kCimbalomAttackEnergyRefA4 = 0.0874f;

// ── 琴橋導納／共鳴板耦合（2026-08-16 B1，見 StringModel::bridgeLossRate()
// 與 docs/BRIDGE_ADMITTANCE_SOURCES.md）──
//
// 這兩個常數是 bridgeLossRate() 的 h（共鳴板厚度）與共鳴板材質選擇。都不是
// TsukiSynth cimbalom 的實測值，是文獻類比預設值——待月月確認，見 TODO.md
// A11。**不開放為 score.json 參數**（原因：數值本身還沒定案，先固化 schema
// 之後要改會動到樂譜相容性，見 docs/workcards/B1.md §5）。
//
// kBridgeSoundboardThicknessM = 9mm：docs/BRIDGE_ADMITTANCE_SOURCES.md §5
// 只給「鋼琴音板 8-10mm」的文獻範圍，取中點。這是鋼琴文獻值，不是 TsukiSynth
// cimbalom 的實測值。
static constexpr float kBridgeSoundboardThicknessM = 0.009f;

// kBridgeSoundboardMaterialKey = "wood_spruce"：materials.json 既有項；
// 鋼琴/揚琴音板慣用雲杉，但這是類比選擇，不是實測。見 MaterialDB.h 檔頭
// 「wood_spruce 的雙重語意」註解。
static constexpr const char* kBridgeSoundboardMaterialKey = "wood_spruce";

enum class ExciterType { Cotton = 0, Felt = 1, Wood = 2, Metal = 3 };

struct CimbalomParams
{
    std::string materialKey;
    double strikePosition   = 0.3;
    ExciterType exciter     = ExciterType::Wood;
    double diameterMm       = 0.8;
    int    numStrings       = 3;
    float  detuningCents    = 5.0f;
    double tensionOverride  = 0.0;   // >0 = use this tension (N), 0 = auto-calculate
    double dampingOverride  = -1.0;  // >=0 = override internal friction (MIDI 60 anchor scale)
    bool   tuneToMidi       = true;  // false = tension/geometry determine absolute pitch
    uint64_t randomSeed     = 0x5453554B4953594Eull;
    uint64_t eventIndex     = 0;
};

// ─── Sound ───
class CimbalomSound : public juce::SynthesiserSound
{
public:
    bool appliesToNote (int) override    { return true; }
    bool appliesToChannel (int) override { return true; }
};

// ─── Voice ───
class CimbalomVoice : public juce::SynthesiserVoice
{
public:
    CimbalomVoice()
    {
        baseModesScratch.reserve (40);
        for (int i = 0; i < kMaxStringsPerCourse; ++i)
        {
            stringModesScratch[(size_t) i].reserve (40);
            strings[i].reserveModes (40);
        }
    }

    void setMaterialDB (MaterialDB* db) { materialDB = db; }
    void setNoiseIdentity (uint64_t identity) { noiseIdentity = identity; }

    // 參數指標（由 Processor 設定，指向 APVTS 的 raw parameter）
    std::atomic<float>* pMaterial       = nullptr;  // index
    std::atomic<float>* pStrikePos      = nullptr;  // 0.05 ~ 0.95
    std::atomic<float>* pDiameter       = nullptr;  // mm
    std::atomic<float>* pHammerHardness = nullptr;  // 0~3
    std::atomic<float>* pNumStrings     = nullptr;  // 1~5
    std::atomic<float>* pDetuning       = nullptr;  // cents

    // Macro 參數指標
    std::atomic<float>* pMacroMaterial   = nullptr;
    std::atomic<float>* pMacroTension    = nullptr;
    std::atomic<float>* pMacroDamping    = nullptr;
    std::atomic<float>* pMacroStrike     = nullptr;
    std::atomic<float>* pMacroBrightness = nullptr;
    std::atomic<float>* pMacroBody       = nullptr;
    std::atomic<float>* pMacroNoise      = nullptr;

    bool canPlaySound (juce::SynthesiserSound* sound) override
    {
        return dynamic_cast<CimbalomSound*> (sound) != nullptr;
    }

    void startNote (int midiNoteNumber, float velocity,
                    juce::SynthesiserSound*, int) override
    {
        if (materialDB == nullptr) return;

        // ── 讀取參數 ──
        const auto& keys = MaterialDB::getOrderedKeys();
        int matIdx = juce::jlimit (0, keys.size() - 1,
                                   (int) pMaterial->load());
        auto* mat = materialDB->getMaterial (keys[matIdx]);
        if (mat == nullptr) return;

        // Bridge/soundboard coupling loss (2026-08-16 B1) needs a soundboard
        // material lookup separate from the string material above. materialDB
        // must already contain wood_spruce, so this guard should never trigger
        // in practice -- but it is written anyway (fail-closed, not skipped).
        auto* soundboardMat = materialDB->getMaterial (kBridgeSoundboardMaterialKey);
        if (soundboardMat == nullptr) return;

        float strikePos = pStrikePos->load();
        float diameter  = pDiameter->load() * 0.001f;   // mm → m
        int   nStrings  = juce::jlimit (1, kMaxStringsPerCourse,
                                        (int) pNumStrings->load());
        float detCents  = pDetuning->load();
        float hammer    = pHammerHardness->load();

        // ── 讀取 Macro（中心 0.5 = 無變化）──
        float mMaterial   = pMacroMaterial   ? pMacroMaterial->load()   : 0.5f;
        float mTension    = pMacroTension    ? pMacroTension->load()    : 0.5f;
        float mDamping    = pMacroDamping    ? pMacroDamping->load()    : 0.5f;
        float mStrike     = pMacroStrike     ? pMacroStrike->load()     : 0.5f;
        float mBrightness = pMacroBrightness ? pMacroBrightness->load() : 0.5f;
        float mBody       = pMacroBody       ? pMacroBody->load()       : 0.5f;
        float mNoise      = pMacroNoise      ? pMacroNoise->load()      : 0.0f;

        // Macro: Strike → blend with per-engine strike
        strikePos *= (0.5f + mStrike);
        strikePos = juce::jlimit (0.05f, 0.95f, strikePos);

        // Macro: Body → detuning spread + body resonance layer
        detCents *= (0.4f + mBody * 1.2f);

        bodyRes.prepare (getSampleRate());
        bodyRes.setAmount (mBody);
        bodyRes.reset();

        // ── 弦參數 ──
        StringModel::Params sp;
        sp.length         = StringModel::lengthFromMidiNote (midiNoteNumber);
        sp.tension        = StringModel::tensionForNote (midiNoteNumber,
                                sp.length, diameter, mat->density);
        sp.diameter       = diameter;
        sp.strikePosition = strikePos;
        sp.numModes       = 40;

        // Bridge/soundboard coupling loss (2026-08-16 B1): frequency-independent,
        // computed once from the string's tension/length (already fixed above)
        // and the soundboard material/thickness, then shared by BOTH decayTime
        // call sites below (attack-energy estimate loop + final per-string loop)
        // -- see StringModel::bridgeLossRate() for the derivation. Recomputing
        // it separately in each loop would be numerically equal today but is
        // exactly the kind of drift that caused the 2026-08-06 tongue_drum
        // velocity-law regression (+4.72 dB), so it is deliberately one shared
        // local instead.
        const float bridgeLoss = StringModel::bridgeLossRate (
            sp.tension, sp.length, *soundboardMat, kBridgeSoundboardThicknessM);

        StringModel::calculateModes (sp, *mat, baseModesScratch);
        auto& baseModes = baseModesScratch;

        // ── spectralTilt: CREATIVE / HEURISTIC LAYER (not physics) ──────────
        // "Stiffer materials sustain more overtones" is a sound-design
        // intuition, NOT a derived result. Every constant here is an
        // empirical tuning value with no literature/derivation/measurement
        // source (repo Rule 4 traceability: NONE):
        //   7.5  -- log10(E) anchor ("softest" material, E = 10^7.5 Pa)
        //   4.0  -- log10(E) span mapped onto the 0..1 tilt range
        //   0.2  -- exponent scale per (partialN - 1) applied below
        //   2.0  -- materialBright = spectralTilt * 2.0 (exciter block below)
        // Impact: multiplies PHYSICAL modal amplitudes (StringModel mode
        // shapes) and therefore also flows into --dump-modes "amp"; it does
        // NOT touch modal frequencies or decay times. DO NOT change these
        // numbers casually -- they alter the rendered sound (Rule 10
        // before/after audio re-render applies). Whether this layer should
        // be removed / separated from the physical amplitude path is an open
        // question awaiting 月月's decision.
        float logE = std::log10 (mat->youngsModulus);
        float spectralTilt = juce::jlimit (0.1f, 1.0f, (logE - 7.5f) / 4.0f);

        if (! baseModes.empty())
        {
            float f1ref = baseModes[0].frequency;
            for (auto& m : baseModes)
            {
                float partialN = m.frequency / f1ref;
                m.amplitude *= std::pow (spectralTilt, (partialN - 1.0f) * 0.2f);
            }
        }

        // Macro: Tension → mode frequency, Material → sustain, Damping → decay
        float tScale = 0.85f + mTension * 0.30f;
        float matScale = 0.5f + mMaterial;
        float dmpScale = 1.0f + (0.5f - mDamping) * 1.4f;

        // Tune fundamental to the exact MIDI pitch. A stiff string's actual f1 is
        // target·√(1+B) (inharmonic sharpening), so divide it out. Modal ratios and
        // the multi-string detuning (applied per string below) are preserved.
        float tuneScale = 1.0f;
        if (! baseModes.empty() && std::isfinite (baseModes[0].frequency)
            && baseModes[0].frequency > 0.0f)
        {
            const float target = 440.0f
                * std::pow (2.0f, (float) (midiNoteNumber - 69) / 12.0f);
            tuneScale = target / baseModes[0].frequency;
        }

        for (auto& m : baseModes)
        {
            m.frequency *= tScale * tuneScale;
            m.decayTime = StringModel::decayTimeForFrequency (
                              m.frequency, *mat, -1.0f, bridgeLoss)
                        * matScale * dmpScale;
        }

        const float tauC = HammerImpulse::tauCForNote (hammer, velocity,
                                                       midiNoteNumber);

        // ── 跨音域響度補償（見 ModalResonator::loudnessCompensationGain）──
        // 攻擊能量用 baseModes（此時 freq/decay 已定案）+ 槌頭頻譜預估；
        // 不含 velocity（excite() 才乘）也不含 1/√N（N 弦不相干疊加的
        // 總能量 ≈ N × (amp/√N)²，兩者相消）。detune ±數 cents 對能量的
        // 影響 << 1 dB，忽略。
        // 預估一律用 velocity=0.5（Hertz 錨，hertzScale=1）的 τc，而非實際
        // τc(velocity)：補償只管跨音域平衡，若把 velocity 相依 τc 算進來，
        // 增益會隨力度變動、把 excite() 的線性 velocity 律拉成次線性
        // （F3 +6.0206±1.0 dB 判定會破——tongue_drum 實測 +4.72 dB FAIL 的
        // 教訓）。實際渲染振幅（下方弦迴圈）仍用實際 τc，物理不變。
        const float tauCRef = HammerImpulse::tauCForNote (hammer, 0.5f,
                                                          midiNoteNumber);
        float attackE = 0.0f;
        for (const auto& m : baseModes)
        {
            const float a = m.amplitude * HammerImpulse::forceSpectrumMagnitude (
                juce::MathConstants<float>::twoPi * m.frequency, tauCRef);
            attackE += ModalResonator::modeAttackEnergy (
                m.frequency, a, m.decayTime, getSampleRate());
        }
        const float noteComp = ModalResonator::loudnessCompensationGain (
            attackE, kCimbalomAttackEnergyRefA4);

        // ── 多弦 beating ──
        numActiveStrings = nStrings;
        float gain = noteComp / std::sqrt ((float) numActiveStrings);

        for (int s = 0; s < numActiveStrings; ++s)
        {
            float centOffset = 0.0f;
            if (numActiveStrings > 1)
                centOffset = detCents
                    * (2.0f * (float) s / (float) (numActiveStrings - 1) - 1.0f);

            float freqMul = std::pow (2.0f, centOffset / 1200.0f);

            auto& modes = stringModesScratch[(size_t) s];
            modes.assign (baseModes.begin(), baseModes.end());
            for (auto& m : modes)
            {
                m.frequency *= freqMul;
                m.decayTime = StringModel::decayTimeForFrequency (
                                  m.frequency, *mat, -1.0f, bridgeLoss)
                            * matScale * dmpScale;
                m.amplitude *= HammerImpulse::forceSpectrumMagnitude (
                    juce::MathConstants<float>::twoPi * m.frequency, tauC);
                m.amplitude *= gain;
            }

            strings[s].setSampleRate (getSampleRate());
            strings[s].setModes (modes);
            strings[s].excite (velocity);
        }

        // ── Exciter（槌頭噪音脈衝）──
        float materialBright = juce::jlimit (0.15f, 2.0f, spectralTilt * 2.0f);
        setupExciter (hammer, velocity, mBrightness, mNoise, materialBright, getSampleRate());
        seedNoise (0x504C5547494Eull, noiseEventCounter++, midiNoteNumber, velocity);
        configureCreativeBodyLayer (baseModes);
        damped = false;
    }

    void stopNote (float, bool allowTailOff) override
    {
        if (allowTailOff)
        {
            applyDamp();
        }
        else
        {
            // Quick fade-out to avoid click on voice stealing
            for (int s = 0; s < numActiveStrings; ++s)
                strings[s].damp (0.002f);
            clearCurrentNote();
        }
    }

    void pitchWheelMoved (int) override {}

    void controllerMoved (int controller, int value) override
    {
        // CC#64 Sustain Pedal：放開時制音
        if (controller == 64 && value < 64)
            applyDamp();
    }

    // ── Standalone API (CLI / ScoreRenderer) ──

    void prepare (double sr) { standaloneSR = sr; }

    void noteOn (int midiNote, float velocity,
                 const MaterialDB::Material& mat,
                 const MaterialDB::Material& soundboardMat,   // bridge coupling (2026-08-16 B1)
                 const CimbalomParams& params)
    {
        double sr = standaloneSR;

        float strikePos = juce::jlimit (0.05f, 0.95f,
                                        static_cast<float> (params.strikePosition));
        float diameter  = static_cast<float> (params.diameterMm) * 0.001f;
        // DIAGNOSTIC-ONLY (see DiagnosticOverrides.h): --num-strings lets
        // physics_verify.py isolate multi-string beating. Sentinel <= 0
        // means "no override" -> identical to the pre-existing behavior.
        int   nStringsRequested = (DiagnosticOverrides::numStringsOverride > 0)
                                     ? DiagnosticOverrides::numStringsOverride
                                     : params.numStrings;
        int   nStrings  = juce::jlimit (1, kMaxStringsPerCourse, nStringsRequested);
        float detCents  = params.detuningCents;
        int   hammerIdx = juce::jlimit (0, 3, static_cast<int> (params.exciter));

        StringModel::Params sp;
        sp.length         = StringModel::lengthFromMidiNote (midiNote);
        sp.tension        = (params.tensionOverride > 0.0)
                                ? static_cast<float> (params.tensionOverride)
                                : StringModel::tensionForNote (midiNote,
                                      sp.length, diameter, mat.density);
        sp.diameter       = diameter;
        sp.strikePosition = strikePos;
        sp.numModes       = 40;

        // Bridge/soundboard coupling loss (2026-08-16 B1) -- see the matching
        // comment in startNote() for why this is computed exactly once and
        // shared between the attack-energy estimate loop and the final
        // per-string render loop below.
        const float bridgeLoss = StringModel::bridgeLossRate (
            sp.tension, sp.length, soundboardMat, kBridgeSoundboardThicknessM);

        StringModel::calculateModes (sp, mat, baseModesScratch);
        auto& baseModes = baseModesScratch;

        // ── spectralTilt: CREATIVE / HEURISTIC LAYER (not physics) ──────────
        // Same untraced empirical constants (7.5 / 4.0 / 0.2, plus the 2.0
        // in materialBright below) as startNote() -- see the full comment
        // block there. NOTE this is the CLI/ScoreRenderer path: the tilt is
        // multiplied into the physical modal amplitudes BEFORE
        // strings[s].setModes(), so it is baked into --dump-modes "amp"
        // values as well as the rendered audio. Frequencies and decay times
        // are unaffected. Values must not be changed without 月月's sign-off
        // (Rule 10); removal/separation of this layer is likewise 月月's
        // call.
        float logE = std::log10 (mat.youngsModulus);
        float spectralTilt = juce::jlimit (0.1f, 1.0f, (logE - 7.5f) / 4.0f);

        if (! baseModes.empty())
        {
            float f1ref = baseModes[0].frequency;
            for (auto& m : baseModes)
            {
                float partialN = m.frequency / f1ref;
                m.amplitude *= std::pow (spectralTilt, (partialN - 1.0f) * 0.2f);
            }
        }

        // Tune fundamental to the exact MIDI pitch (compensate stiff-string
        // inharmonic sharpening: actual f1 = target·√(1+B)). Ratios + detuning kept.
        if (params.tuneToMidi && ! baseModes.empty() && std::isfinite (baseModes[0].frequency)
            && baseModes[0].frequency > 0.0f)
        {
            const float target = 440.0f
                * std::pow (2.0f, (float) (midiNote - 69) / 12.0f);
            const float tuneScale = target / baseModes[0].frequency;
            for (auto& m : baseModes)
                m.frequency *= tuneScale;
        }

        const float tauC = HammerImpulse::tauCForNote ((float) hammerIdx, velocity,
                                                       midiNote);
        // dampingOverride semantics: >= 0 replaces ONLY the internal-friction
        // term of the decay law
        //   T60(f) = 1 / (eta*f/2.2 + beta_air*f^2 + gamma_radiation*f + bridgeLoss);
        // the beta_air*f^2 and gamma_radiation*f terms always stay
        // material-driven (see StringModel::decayTimeForFrequency). It is
        // NOT a scale factor on the whole damping. Sentinel -1 = no
        // override (pure material damping). bridgeLoss (2026-08-16 B1) is
        // likewise always additive and never affected by this override --
        // see StringModel::bridgeLossRate().
        // The score-facing NUMBER is unchanged by the 2026-08-10 broadbanding:
        // it still means "internal-friction decay rate at the MIDI 60 anchor"
        // (the old alpha scale), and is converted to an equivalent eta inside
        // decayTimeForFrequency() -- so the 32 authored scores using it keep
        // their intent exactly at the anchor and broadband elsewhere like the
        // material path. See MaterialDB::etaFromAnchoredDamping().
        const float dampingOverride = params.dampingOverride >= 0.0
            ? (float) params.dampingOverride : -1.0f;

        // ── 跨音域響度補償 —— 與 startNote() 相同（見該處註解，含 τc 用
        // velocity=0.5 Hertz 錨的理由）。此路徑的 baseModes 尚未設 decayTime，
        // 預估時套用與下方弦迴圈同一條衰減律（含 alphaOverride），確保預估
        // 與實際渲染一致。
        const float tauCRef = HammerImpulse::tauCForNote ((float) hammerIdx, 0.5f,
                                                          midiNote);
        float attackE = 0.0f;
        for (const auto& m : baseModes)
        {
            const float a = m.amplitude * HammerImpulse::forceSpectrumMagnitude (
                juce::MathConstants<float>::twoPi * m.frequency, tauCRef);
            attackE += ModalResonator::modeAttackEnergy (
                m.frequency, a,
                StringModel::decayTimeForFrequency (
                    m.frequency, mat, dampingOverride, bridgeLoss),
                sr);
        }
        const float noteComp = ModalResonator::loudnessCompensationGain (
            attackE, kCimbalomAttackEnergyRefA4);

        numActiveStrings = nStrings;
        float gain = noteComp / std::sqrt ((float) numActiveStrings);

        for (int s = 0; s < numActiveStrings; ++s)
        {
            float centOffset = 0.0f;
            if (numActiveStrings > 1)
                centOffset = detCents
                    * (2.0f * (float) s / (float) (numActiveStrings - 1) - 1.0f);

            float freqMul = std::pow (2.0f, centOffset / 1200.0f);

            auto& modes = stringModesScratch[(size_t) s];
            modes.assign (baseModes.begin(), baseModes.end());
            for (auto& m : modes)
            {
                m.frequency *= freqMul;
                m.decayTime = StringModel::decayTimeForFrequency (
                    m.frequency, mat, dampingOverride, bridgeLoss);
                m.amplitude *= HammerImpulse::forceSpectrumMagnitude (
                    juce::MathConstants<float>::twoPi * m.frequency, tauC);
                m.amplitude *= gain;
            }

            strings[s].setSampleRate (sr);
            strings[s].setModes (modes);
            strings[s].excite (velocity);
        }

        float materialBright = juce::jlimit (0.15f, 2.0f, spectralTilt * 2.0f);
        setupExciter (static_cast<float> (hammerIdx), velocity,
                      0.5f, 0.0f, materialBright, sr);
        seedNoise (params.randomSeed, params.eventIndex, midiNote, velocity);

        bodyRes.prepare (sr);
        // DIAGNOSTIC-ONLY: --body-amount overrides the CLI default body mix
        // of 0.0f, i.e. the body-resonance layer is OFF in this standalone /
        // physics-verified path unless the flag is passed (the plugin's
        // Macro Body knob is a separate path via startNote()). See
        // DiagnosticOverrides.h. Sentinel < 0 -> unchanged 0.0f behavior.
        bodyRes.setAmount (DiagnosticOverrides::bodyAmountOverride >= 0.0f
                                ? DiagnosticOverrides::bodyAmountOverride
                                : 0.0f);
        configureCreativeBodyLayer (baseModes);
        bodyRes.reset();
        damped = false;
    }

    void noteOff() { applyDamp(); }

    bool isActive() const
    {
        for (int s = 0; s < numActiveStrings; ++s)
            if (strings[s].isActive()) return true;
        return exciterEnv.isActive();
    }

    float getNextSample()
    {
        float sample = 0.0f;
        for (int s = 0; s < numActiveStrings; ++s)
            if (strings[s].isActive())
                sample += strings[s].processSample();

        if (exciterEnv.isActive())
        {
            float noise = noiseGen.processSample();
            noise = exciterFilter.processSample (noise);
            sample += noise * exciterEnv.process();
        }

        sample += bodyRes.processSample (sample);
        return sample * 0.069f;   // equal-RMS re-calibrated (2026-07): the
                                   // BodyResonance velocity-linearity fix removed
                                   // a v^2 envelope term that was inflating body-
                                   // resonance level. RMS-only re-anchoring to the
                                   // pre-fix vel=0.85 reference would put peak at
                                   // 0.0 dBFS (violates verify_score.py's
                                   // PEAK_LIMIT_DBFS = -0.3), so this value instead
                                   // restores the pre-fix peak headroom (-2.0 dBFS
                                   // @ vel=0.85) — closest achievable equal-RMS
                                   // anchor without breaching the peak ceiling.
    }

    void scaleFrequencies (double factor)
    {
        for (int s = 0; s < numActiveStrings; ++s)
            strings[s].scaleFrequencies (factor);
    }

    /// Predicted modes of the course (representative string 0) — CLI --dump-modes.
    std::vector<ModalResonator::Mode> getModes() const
    {
        return numActiveStrings > 0 ? strings[0].getModes()
                                    : std::vector<ModalResonator::Mode>{};
    }

    /// 2026-07 (--amps GATE fix): predicted modes of EVERY active string in
    /// the course (already detuned + gain-scaled exactly as noteOn() set
    /// them up, i.e. the real per-string frequency/amplitude the renderer
    /// sums at getNextSample() time) -- not just string 0. Needed so
    /// --dump-modes' theory can reconstruct the true multi-string beating
    /// pattern (ROADMAP_PHYSICS.md M2-2d root-cause Experiment 4/5) instead
    /// of reporting a single undetuned string as if it were the whole course.
    std::vector<std::vector<ModalResonator::Mode>> getAllStringModes() const
    {
        std::vector<std::vector<ModalResonator::Mode>> out;
        for (int s = 0; s < numActiveStrings; ++s)
            out.push_back (strings[s].getModes());
        return out;
    }

    /// |dry + BodyResonance(dry)| at freqHz for THIS voice's live body-filter
    /// state (amount/frequencies as set in noteOn()) -- see BodyResonance::
    /// magnitudeAt(). Single source of truth for --dump-modes' body-filter
    /// column; not a re-derivation, reads the same bodyRes the renderer uses.
    float getBodyMagnitudeAt (float freqHz) const { return bodyRes.magnitudeAt (freqHz); }

    void renderNextBlock (juce::AudioBuffer<float>& outputBuffer,
                          int startSample, int numSamples) override
    {
        bool anyActive = false;

        while (--numSamples >= 0)
        {
            float sample = 0.0f;

            // 弦共振
            for (int s = 0; s < numActiveStrings; ++s)
            {
                if (strings[s].isActive())
                {
                    sample += strings[s].processSample();
                    anyActive = true;
                }
            }

            // 槌頭瞬態噪音
            if (exciterEnv.isActive())
            {
                float noise = noiseGen.processSample();
                noise = exciterFilter.processSample (noise);
                sample += noise * exciterEnv.process();
                anyActive = true;
            }

            // Body resonance layer
            sample += bodyRes.processSample (sample);

            // 輸出（master gain 防 clipping）
            sample *= 0.069f;   // equal-RMS re-calibrated (2026-07, see getNextSample())

            for (int ch = 0; ch < outputBuffer.getNumChannels(); ++ch)
                outputBuffer.addSample (ch, startSample, sample);

            ++startSample;
        }

        if (! anyActive)
            clearCurrentNote();
    }

private:
    void applyDamp()
    {
        if (! damped)
        {
            for (int s = 0; s < numActiveStrings; ++s)
                strings[s].damp (0.05f);
            damped = true;
        }
    }

    void configureCreativeBodyLayer (
        const std::vector<ModalResonator::Mode>& modes)
    {
        if (modes.empty())
            return;
        const float first = juce::jlimit (40.0f, 4000.0f, modes[0].frequency);
        const float second = juce::jlimit (40.0f, 4000.0f,
            modes.size() > 1 ? modes[1].frequency : modes[0].frequency * 2.0f);
        bodyRes.setFrequencies (first, second);
        bodyRes.reset();
    }

    void seedNoise (uint64_t scoreSeed, uint64_t eventIndex,
                    int midiNote, float velocity)
    {
        const uint32_t velocityCode = (uint32_t) std::lround (
            juce::jlimit (0.0f, 1.0f, velocity) * 16777215.0f);
        const uint64_t streamEvent = (eventIndex << 8) ^ noiseIdentity;
        noiseGen.setSeed (NoiseGen::mixSeed (
            scoreSeed, streamEvent, (uint32_t) midiNote, velocityCode));
    }

    void setupExciter (float hardness, float velocity,
                       float brightMacro, float noiseMacro,
                       float materialBright, double sr)
    {
        static constexpr float cutoffs[]   = { 500.0f, 1500.0f, 4000.0f, 10000.0f };
        static constexpr float durations[] = { 0.004f, 0.003f,  0.002f,  0.001f };

        int idx = juce::jlimit (0, 3, (int) hardness);

        float cutoff = cutoffs[idx] * (0.3f + brightMacro * 1.4f) * materialBright;
        cutoff = juce::jlimit (200.0f, 16000.0f, cutoff);

        exciterFilter.setSampleRate (sr);
        exciterFilter.setParams (BiquadFilter::Type::LowPass, cutoff, 0.707f);
        exciterFilter.reset();

        noiseGen.setType (NoiseGen::Type::White);
        noiseGen.reset();

        static constexpr float noiseAmps[] = { 0.10f, 0.20f, 0.40f, 0.70f };
        float amp = velocity * noiseAmps[idx] * (1.0f + noiseMacro * 3.0f);
        float durScale = juce::jlimit (0.5f, 3.0f, 1.5f / (materialBright + 0.5f));
        // DIAGNOSTIC-ONLY: --no-exciter-noise skips the trigger entirely, so
        // exciterEnv.isActive() stays false for this voice's whole lifetime
        // (ExpDecay::level defaults to 0.0f) -- see DiagnosticOverrides.h.
        if (! DiagnosticOverrides::disableExciterNoise)
            exciterEnv.trigger (amp, durations[idx] * durScale, sr);
    }

    MaterialDB*    materialDB = nullptr;
    double         standaloneSR = 0.0;
    ModalResonator strings[kMaxStringsPerCourse];
    std::vector<ModalResonator::Mode> baseModesScratch;
    std::array<std::vector<ModalResonator::Mode>, kMaxStringsPerCourse> stringModesScratch;
    int            numActiveStrings = 1;
    bool           damped = false;
    uint64_t       noiseIdentity = 0;
    uint64_t       noiseEventCounter = 0;

    NoiseGen           noiseGen;
    BiquadFilter       exciterFilter;
    Envelope::ExpDecay exciterEnv;
    BodyResonance      bodyRes;
};
