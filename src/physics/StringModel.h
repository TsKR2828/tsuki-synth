#pragma once
#include "MaterialDB.h"
#include "../dsp/ModalResonator.h"
#include <vector>
#include <cmath>
#include <juce_core/juce_core.h>

/**
 * 弦振動物理模型 — Phase 3 Cimbalom 引擎的核心
 *
 * 模態頻率：  f(n) = (n / 2L) × √(T / μ) × √(1 + B × n²)
 * 非諧性：    B = (π³ × E × d⁴) / (64 × T × L²)
 * 衰減時間：  τ(n) = 1 / (α + β_air × f(n)² + γ_radiation × f(n))
 * 激發振幅：  a(n) = sin(n × π × x_hit / L)
 *
 * 其中：
 *   L = 弦長 (m),  T = 張力 (N),  d = 弦徑 (m)
 *   μ = 線密度 = ρ × π × (d/2)²  (kg/m)
 *   E = 楊氏模量 (Pa),  ρ = 密度 (kg/m³)
 */
class StringModel
{
public:
    struct Params
    {
        float length         = 0.35f;    // 弦長 (m)
        float tension        = 800.0f;   // 張力 (N)
        float diameter       = 0.0008f;  // 弦徑 (m)  = 0.8mm
        float strikePosition = 0.3f;     // 擊打位置 (0~1)
        int   numModes       = 40;       // 模態數
    };

    /** T60(f) = 1 / (eta·f/2.2 + beta_air·f² + gamma_radiation·f + bridgeLoss)
     *
     * 內部摩擦項自 2026-08-10 起是**寬頻**的（eta·f/2.2，見 MaterialDB.h
     * 頂端註解）：損耗因子 eta 為頻率無關的材質常數，其衰減率貢獻與頻率
     * 成正比，這正是當初 alpha 的推導式本身（T60 = 2.2/(f·eta)）所要求的。
     * 舊實作把該項凍結在 MIDI 60 錨點，只有那一個音高與文獻一致。
     *
     * 第四項（`bridgeLoss`，2026-08-16 B1）是**頻率無關**的琴橋/共鳴板耦合
     * 損耗——弦端能量經琴橋流向共鳴板，見 `bridgeLossRate()` 上方的完整
     * 溯源註解與 `docs/BRIDGE_ADMITTANCE_SOURCES.md` §2.1–§2.3。舊三項在
     * f→0 時全部趨近 0，導致低音 T60 發散（`reports/damping_broadband_findings.md`
     * §3.1：C2 從 39s 拉長到 129s）；這第四項正是缺掉的低音端損耗通道。
     *
     * @param frequency        模態頻率 (Hz)
     * @param material         弦材質（提供 eta/beta_air/gamma_radiation）
     * @param dampingOverride  >=0 覆寫內部摩擦項；數字語意是「MIDI 60 錨點
     *                         上的衰減率」（舊 alpha 尺度，既有樂譜不需改），
     *                         內部經 MaterialDB::etaFromAnchoredDamping()
     *                         轉成 eta 後同樣寬頻求值。beta_air/gamma_radiation
     *                         永遠維持材質驅動，不受覆寫影響；bridgeLoss 同理，
     *                         永遠疊加、不受 damping_override 影響。
     * @param bridgeLoss       頻率無關的橋耦合損耗率貢獻 (1/s)，來自
     *                         `bridgeLossRate()`。預設 0.0f = 不加這項，保證
     *                         既有呼叫端（不傳這個參數）行為位元不變；正式
     *                         Cimbalom/Piano 渲染路徑一定要傳非零值
     *                         （`CimbalomEngine.h`）。
     */
    static float decayTimeForFrequency (
        float frequency, const MaterialDB::Material& material,
        float dampingOverride = -1.0f, float bridgeLoss = 0.0f)
    {
        const float eta = dampingOverride >= 0.0f
            ? MaterialDB::etaFromAnchoredDamping (dampingOverride)
            : material.damping.eta;
        const float denominator = MaterialDB::internalFrictionRate (eta, frequency)
            + material.damping.beta_air * frequency * frequency
            + material.damping.gamma_radiation * frequency
            + bridgeLoss;
        return denominator > 0.0f ? 1.0f / denominator : 10.0f;
    }

    /** Frequency-independent bridge/soundboard coupling loss-rate contribution
     *  to 1/T60 -- energy flowing from the string end, through the bridge, into
     *  the soundboard. Closed-form literature result, not a fitted constant.
     *  Full derivation chain: docs/BRIDGE_ADMITTANCE_SOURCES.md §2.1-§2.3.
     *
     *  D    = E*h^3 / (12*(1-nu^2))     soundboard bending stiffness (N*m)
     *         [Cremer, Heckl & Ungar, "Structure-Borne Sound"; classic
     *          thin-plate bending-stiffness result]
     *  rhoS = rho*h                     soundboard areal density (kg/m^2)
     *  Y_inf = 1 / (8*sqrt(D*rhoS))     infinite-plate driving-point admittance
     *         (s/kg), REAL and frequency-independent
     *         [Cremer/Heckl/Ungar + Skudrzyk mean-value theorem; algebraically
     *          verified equal to Ege & Boutillon's Y_C = (1/(4h^2))*sqrt(3*(1-nu^2)/(E*rho)),
     *          see BRIDGE_ADMITTANCE_SOURCES.md §2.1]
     *  G    = Re(Y_inf) = Y_inf         (already real-valued; imaginary part
     *         dropped by construction -- see BRIDGE_ADMITTANCE_SOURCES.md §4
     *         point 3, no detuning contribution modeled here)
     *  alpha = (T/L)*G                  string-end amplitude decay rate (1/s)
     *         [derived from the reflection coefficient at a bridge terminated
     *          by admittance Y; cross-checked against Chaigne ICA 2010's
     *          alpha_n = (T/L)*G(omega); see BRIDGE_ADMITTANCE_SOURCES.md §2.2]
     *  1/T60_bridge = alpha / ln(1000) = T*G / (ln(1000)*L)
     *         ln(1000) = 6.907755278982137, same constant as
     *         tools/physics_verify.py's MODAL_DECAY_LN1000 and
     *         ModalResonator::excite()'s 6.9078f literal.
     *
     *  Deliberately NO coupling-reduction fudge factor here (Rule 4): adding
     *  one would turn a traceable closed-form result into an untraceable
     *  tunable knob. See BRIDGE_ADMITTANCE_SOURCES.md §5.
     *
     *  @param tension              string tension T (N)
     *  @param length                string length L (m)
     *  @param soundboardMaterial    soundboard material (NOT the string material)
     *  @param soundboardThicknessM  soundboard thickness h (m); must be > 0
     *  @return  1/T60 contribution (1/s). Returns 0.0f (fail-closed: no
     *           contribution, NOT a crash/NaN/negative-T60) if any input is
     *           non-finite or non-positive.
     */
    static float bridgeLossRate (float tension, float length,
                                 const MaterialDB::Material& soundboardMaterial,
                                 float soundboardThicknessM)
    {
        // ln(1000), same constant as MaterialDB::kEtaToDecayRate's derivation
        // and ModalResonator::excite()'s 6.9078f literal -- see doc comment above.
        static constexpr float kLn1000 = 6.907755278982137f;

        if (! std::isfinite (tension) || tension <= 0.0f
            || ! std::isfinite (length) || length <= 0.0f
            || ! std::isfinite (soundboardThicknessM) || soundboardThicknessM <= 0.0f)
            return 0.0f;

        const float E  = soundboardMaterial.youngsModulus;
        const float nu = soundboardMaterial.poissonRatio;
        const float rho = soundboardMaterial.density;
        const float h  = soundboardThicknessM;

        const float D = (E * h * h * h) / (12.0f * (1.0f - nu * nu));
        const float rhoS = rho * h;
        const float DrhoS = D * rhoS;

        if (! std::isfinite (D) || D <= 0.0f
            || ! std::isfinite (rhoS) || rhoS <= 0.0f
            || ! std::isfinite (DrhoS) || DrhoS <= 0.0f)
            return 0.0f;

        const float Y_inf = 1.0f / (8.0f * std::sqrt (DrhoS));
        if (! std::isfinite (Y_inf) || Y_inf <= 0.0f)
            return 0.0f;

        const float G = Y_inf;   // Re(Y_inf) = Y_inf, see doc comment above.
        const float bridgeLoss = (tension * G) / (kLn1000 * length);
        return std::isfinite (bridgeLoss) && bridgeLoss > 0.0f ? bridgeLoss : 0.0f;
    }

    /**
     * 從物理參數計算所有模態
     * @return 模態列表，可直接傳入 ModalResonator::setModes()
     */
    static std::vector<ModalResonator::Mode> calculateModes (
        const Params& params,
        const MaterialDB::Material& material)
    {
        std::vector<ModalResonator::Mode> modes;
        calculateModes (params, material, modes);
        return modes;
    }

    static void calculateModes (
        const Params& params,
        const MaterialDB::Material& material,
        std::vector<ModalResonator::Mode>& modes)
    {
        modes.clear();
        modes.reserve ((size_t) params.numModes);

        const float L = params.length;
        const float T = params.tension;
        const float d = params.diameter;
        const float r = d / 2.0f;

        // 線密度 μ = ρ × π × r²
        const float mu = material.density
                         * juce::MathConstants<float>::pi * r * r;

        // 基頻 f1 = 1/(2L) × √(T/μ)
        const float f1 = (1.0f / (2.0f * L))
                         * std::sqrt (T / mu);

        // 非諧性係數 B = π³ × E × d⁴ / (64 × T × L²)
        const float pi3 = juce::MathConstants<float>::pi
                         * juce::MathConstants<float>::pi
                         * juce::MathConstants<float>::pi;
        const float d4 = d * d * d * d;
        const float B = (pi3 * material.youngsModulus * d4)
                        / (64.0f * T * L * L);

        for (int n = 1; n <= params.numModes; ++n)
        {
            float fn = (float) n;

            // 模態頻率（含剛性修正）
            float freq = fn * f1 * std::sqrt (1.0f + B * fn * fn);

            // 超出人耳範圍就截斷
            if (freq > 20000.0f)
                break;

            // 衰減時間
            float decay = decayTimeForFrequency (freq, material);

            // 擊打位置影響振幅
            //
            // ── Modal amplitude convention: VELOCITY (equal-weight) ────────
            // amp = |mode shape at the strike point|, one factor per mode,
            // with NO 1/omega_n or omega_n weighting. For an impulsive point
            // force at x_hit each mode's initial modal VELOCITY is
            // proportional to phi_n(x_hit)/m_n; with the equal modal mass of
            // the ideal string (m_n = mu*L/2 for every n) that reduces to
            // amp ∝ |phi_n(x_hit)| -- i.e. this is the modal-velocity
            // amplitude convention. All three modal sources (StringModel /
            // BeamModel / PlateModel) deliberately use this SAME convention
            // so cross-engine spectra are comparable. Alternative
            // conventions differ by an overall spectral slope, not by
            // per-mode structure:
            //   displacement convention  = velocity × 1/omega_n
            //                              (≈ −6 dB/oct relative tilt)
            //   acceleration / far-field pressure convention
            //                            = velocity × omega_n
            //                              (≈ +6 dB/oct relative tilt)
            float amp = std::abs (std::sin (fn * juce::MathConstants<float>::pi
                                            * params.strikePosition));

            modes.push_back ({ freq, amp, decay });
        }

    }

    /**
     * 從 MIDI 音符計算弦長
     * 假設基準：A4 (MIDI 69) = 0.35m，每升一個八度弦長減半
     */
    static float lengthFromMidiNote (int midiNote, float referenceLength = 0.35f)
    {
        float semitoneOffset = (float) (midiNote - 69);
        return referenceLength * std::pow (2.0f, -semitoneOffset / 12.0f);
    }

    /**
     * 從 MIDI 音符計算所需張力
     * 給定弦長、弦徑、材質密度，反推需要多少張力才能得到正確基頻
     *   T = μ × (2L × f1)²
     */
    static float tensionForNote (int midiNote, float length, float diameter,
                                 float density)
    {
        float targetFreq = 440.0f * std::pow (2.0f, (float) (midiNote - 69) / 12.0f);
        float r = diameter / 2.0f;
        float mu = density * juce::MathConstants<float>::pi * r * r;
        float v = 2.0f * length * targetFreq;  // 弦上波速
        return mu * v * v;
    }
};
