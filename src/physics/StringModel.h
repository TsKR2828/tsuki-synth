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
 * 衰減時間：  T60(n) = 1 / ((eta + Q⁻¹_air + Q⁻¹_visc + Q⁻¹_disl)·f(n)/2.2 + bridgeLoss)
 *             （見 decayTimeForFrequency() 的完整推導註解）
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

    // ── Cuesta & Valette (1988) 弦阻尼三機制的物理常數 ──
    // 來源：docs/STRING_DAMPING_SOURCES.md §2（逐字轉錄自引用該研究的開放全文，
    // Improved frequency-dependent damping for time domain modelling of linear
    // string vibration, ICA 2016, NESS 專案）。

    // 空氣密度，標準大氣（ISA，海平面，15°C）。文獻表列常數，非量測、非推導。
    static constexpr float kAirDensity = 1.225f;               // kg/m^3

    // 空氣運動黏度。docs/STRING_DAMPING_SOURCES.md §2 表列「論文用 1.619e-5」，
    // 逐字轉錄自 Cuesta & Valette (1988)（經 ICA 2016 全文引用）。
    static constexpr float kAirKinematicViscosity = 1.619e-5f; // m^2/s

    // 位錯（dislocation）損耗，頻率無關的擬合 Q^-1。docs/STRING_DAMPING_SOURCES.md
    // §2：原文無法從量測資料區分位錯損耗與熱傳導損耗，兩者擬合同樣好，取此值。
    // 這是原始文獻的擬合常數本身（不是本專案自己擬合的），故仍符合 Rule 4
    // 「文獻」類來源，但注意它是單一數字、不隨材質變化（見 docs/workcards/B3.md §11 風險）。
    static constexpr float kDislocationQInv = 1.0f / 18000.0f; // 無量綱

    /** Cuesta & Valette (1988) 弦阻尼空氣黏滯＋黏彈性＋位錯三機制，零自由參數。
     *  見 docs/STRING_DAMPING_SOURCES.md §2。只適用圓截面弦（r^6/r^2 幾何內建），
     *  不適用 Beam/Plate。回傳值是三項相加的 Q^-1（無量綱），與 eta 同一把尺，
     *  呼叫端把它跟 eta 加在一起再乘 f/kEtaToDecayRate（見本檔 decayTimeForFrequency）。
     *
     *    M         = (r/2)·√(ω/μa)                        ω = 2πf
     *    Q⁻¹_air   = (ρa/ρ)·[√2/M + 1/(2M²)]              ρ = 弦材料密度
     *    Q⁻¹_visc  = 0.003·E·ρ·π²·r⁶·ω²/(4T²)             E = 楊氏模數, T = 張力
     *    Q⁻¹_disl  = 1/18000
     *
     *  無效輸入（頻率/半徑/張力非正或非有限）時回傳 0 = 不貢獻，交由呼叫端
     *  既有的 denominator>0 保護接手（fail-closed：不產生 NaN/Inf/負 T60）。
     */
    static float stringAirViscDislQInv (float frequency, float radius, float tension,
                                        const MaterialDB::Material& material)
    {
        if (! std::isfinite (frequency) || frequency <= 0.0f
            || ! std::isfinite (radius) || radius <= 0.0f
            || ! std::isfinite (tension) || tension <= 0.0f)
            return 0.0f; // 無效輸入時不貢獻，交由既有 denominator>0 保護接手

        const float omega = juce::MathConstants<float>::twoPi * frequency;
        const float M = (radius * 0.5f) * std::sqrt (omega / kAirKinematicViscosity);
        const float qInvAir = (kAirDensity / material.density)
            * (std::sqrt (2.0f) / M + 1.0f / (2.0f * M * M));
        const float qInvVisc = 0.003f * material.youngsModulus * material.density
            * juce::MathConstants<float>::pi * juce::MathConstants<float>::pi
            * std::pow (radius, 6.0f) * omega * omega
            / (4.0f * tension * tension);
        const float qInv = qInvAir + qInvVisc + kDislocationQInv;
        return std::isfinite (qInv) && qInv > 0.0f ? qInv : 0.0f;
    }

    /** T60(f) = 1 / ((eta + Q⁻¹_air + Q⁻¹_visc + Q⁻¹_disl)·f/2.2 + bridgeLoss)
     *
     * 分母四個損耗通道（docs/STRING_DAMPING_SOURCES.md §2/§2.1/§4.1）：
     *
     *   1. 內部摩擦 eta·f/2.2 —— 自 2026-08-10 起寬頻（見 MaterialDB.h 頂端
     *      註解）：損耗因子 eta 為頻率無關的材質常數，衰減率貢獻與頻率成正比。
     *   2.-3.-4. 空氣黏滯＋黏彈性＋位錯 —— 2026-08-24 B3 起換成 Cuesta &
     *      Valette (1988) 的零自由參數三機制（stringAirViscDislQInv()），由
     *      頻率/弦半徑/張力/材質 (rho, E) 直接算出，取代舊的
     *      beta_air·f²＋gamma_radiation·f 兩個查無出處的擬合項；materials.json
     *      改名後的 beam_plate_beta_air/beam_plate_gamma_radiation 只給
     *      Beam/Plate 用，本函式**不讀**。代數化簡（B3 卡 §4.1）：因
     *      kEtaToDecayRate = 2.2 = ln(1000)/π 且 1/T60 = π·f·Q⁻¹/ln(1000)
     *      = Q⁻¹·f/2.2，三機制 Q⁻¹ 與 eta 同一把尺，先加總再統一乘
     *      f/kEtaToDecayRate（即 internalFrictionRate()），不另引入 π 或
     *      ln(1000) 字面值。
     *   5. 琴橋/共鳴板耦合 bridgeLoss（2026-08-16 B1）——**頻率無關**，見
     *      `bridgeLossRate()` 與 `docs/BRIDGE_ADMITTANCE_SOURCES.md` §2.1–§2.3。
     *      弦端其餘各項在 f→0 時趨近 0，導致低音 T60 發散
     *      （`reports/damping_broadband_findings.md` §3.1）；此項是缺掉的
     *      低音端損耗通道。
     *
     * @param frequency        模態頻率 (Hz)
     * @param material         弦材質（提供 eta 與三機制用的 density/youngsModulus）
     * @param dampingOverride  >=0 覆寫內部摩擦項；數字語意是「MIDI 60 錨點
     *                         上的衰減率」（舊 alpha 尺度，既有樂譜不需改），
     *                         內部經 MaterialDB::etaFromAnchoredDamping()
     *                         轉成 eta 後同樣寬頻求值。三機制項與 bridgeLoss
     *                         永遠疊加、不受覆寫影響。**注意（B3）**：因三機制
     *                         項頻率相依且不可覆寫，damping_override 在 MIDI 60
     *                         錨點「逐位元保留舊 T60」的保證自 B3 起不再成立。
     * @param bridgeLoss       頻率無關的橋耦合損耗率貢獻 (1/s)，來自
     *                         `bridgeLossRate()`。傳 0.0f = 不加這項；正式
     *                         Cimbalom/Piano 渲染路徑一定要傳非零值
     *                         （`CimbalomEngine.h`）。
     * @param radius           弦半徑 r (m)（= diameter/2；B3 新增）。<=0 或非
     *                         有限值時三機制項不貢獻（fail-closed）。
     * @param tension          弦張力 T (N)（B3 新增）。<=0 或非有限值時同上。
     *                         （兩個新參數刻意**無預設值**：漏改的呼叫端要在
     *                         編譯期爆掉，不准悄悄退回沒有三機制項的物理。）
     */
    static float decayTimeForFrequency (
        float frequency, const MaterialDB::Material& material,
        float dampingOverride, float bridgeLoss,
        float radius, float tension)
    {
        const float eta = dampingOverride >= 0.0f
            ? MaterialDB::etaFromAnchoredDamping (dampingOverride)
            : material.damping.eta;
        const float qInvTotal = eta
            + stringAirViscDislQInv (frequency, radius, tension, material);
        const float denominator =
            MaterialDB::internalFrictionRate (qInvTotal, frequency)
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

    /** Soundboard D / rhoS / G triple, exposed for the --dump-modes
     *  diagnostic path (B6, docs/workcards/B6.md SS3/SS6 step 6). This does
     *  NOT add any new physics: it is the exact same D/rhoS/Y_inf algebra
     *  bridgeLossRate() already computes internally above, just returned as
     *  a triple instead of being collapsed straight into the final
     *  bridgeLoss scalar -- B1's own already-computed quantities, factored
     *  out into their own getter so RadiationModel.h's criticalFrequency()/
     *  radiationLossFactor() can be called from the diagnostic path without
     *  re-deriving D/rhoS or duplicating bridgeLossRate()'s fail-closed
     *  checks by hand. bridgeLossRate() itself is left untouched (B6.md SS3
     *  "do not touch" boundary does not list this function, but it is B1's
     *  code, not B6's -- this getter reads the same inputs, it does not
     *  modify how bridgeLossRate() computes the real render-path bridgeLoss).
     *
     *  @param soundboardMaterial    soundboard material (same one
     *                               bridgeLossRate() takes).
     *  @param soundboardThicknessM  soundboard thickness h (m); must be > 0.
     *  @return {D, rhoS, G, valid}. valid=false (all other fields 0.0f) on
     *          the same fail-closed conditions as bridgeLossRate() (non-
     *          finite/non-positive thickness or material properties).
     */
    struct SoundboardDynamics
    {
        float D    = 0.0f;   // bending stiffness (N*m)
        float rhoS = 0.0f;   // areal density (kg/m^2)
        float G    = 0.0f;   // Re(Y_inf), infinite-plate driving-point admittance (s/kg)
        bool valid = false;
    };

    static SoundboardDynamics soundboardDynamics (const MaterialDB::Material& soundboardMaterial,
                                                  float soundboardThicknessM)
    {
        SoundboardDynamics r;
        if (! std::isfinite (soundboardThicknessM) || soundboardThicknessM <= 0.0f)
            return r;

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
            return r;

        const float Y_inf = 1.0f / (8.0f * std::sqrt (DrhoS));
        if (! std::isfinite (Y_inf) || Y_inf <= 0.0f)
            return r;

        r.D = D;
        r.rhoS = rhoS;
        r.G = Y_inf;
        r.valid = true;
        return r;
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

            // 衰減時間（無 override、無橋耦合——與 B3 前的預設引數行為一致；
            // CimbalomEngine 的兩條渲染路徑都會用含 bridgeLoss 的呼叫重算）
            float decay = decayTimeForFrequency (freq, material,
                                                 -1.0f, 0.0f, r, T);

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
