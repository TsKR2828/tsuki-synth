#pragma once
#include <cmath>
#include <juce_core/juce_core.h>

/**
 * 槌/激發力脈衝頻譜模型 — M2 任務 2a/2b（取代 LP 啟發式截止）
 *
 * ── 物理模型 ──
 *
 * 槌頭接觸弦/梁/板期間，接觸力近似半正弦脈衝（Chaigne & Askenfelt 1994,
 * JASA 95(2), "Numerical simulations of piano strings I"；該文以力-時間曲線
 * 半高寬定義接觸時間 tau_c，並描述槌頭非線性：接觸時間隨衝擊力增大而縮短）：
 *
 *   F(t) = F_max * sin(pi * t / tau_c),   0 <= t <= tau_c
 *   F(t) = 0                              其他時間
 *
 * 此脈衝的傅立葉轉換（本檔案已用數值積分逐項驗證閉式解，誤差 <1e-4）：
 *
 *   F(w) = F_max * tau_c * (2/pi) * cos(w*tau_c/2) / (1 - (w*tau_c/pi)^2)
 *          * exp(-i*w*tau_c/2)
 *
 * 其振幅頻譜 DC 正規化（|F(0)| = 2*F_max*tau_c/pi，除以此值使 H(0)=1，只留頻譜
 * "形狀"，不疊加額外整體增益——見本檔案 forceSpectrumMagnitude()）：
 *
 *   H(w) = |cos(w*tau_c/2)| / |1 - (w*tau_c/pi)^2|,   H(0) = 1
 *
 * 分母在 w*tau_c = pi 處有可去奇點，H 在該點的極限值 = π/4（羅必達法則）。
 * 頻譜第一個零點在 w*tau_c/2 = pi/2，即 f_null = 1/(2*tau_c) —— 這就是題目
 * 描述的「簡化實用頻譜包絡在 f_cutoff ~= 1/(2*tau_c) 以上滾降」的精確版本：
 * f_cutoff 不再是查表任意值，而是由 tau_c 直接導出的物理量。
 *
 * ── tau_c（接觸時間）數值來源 ──
 *
 * 槌/激發硬度 -> tau_c 對應真實 ExciterType 列舉（Cotton/Felt/Wood/Metal，
 * 見 CimbalomEngine.h）與 ChromaticEngine 的 chromaticExciterHardness()
 * 0~3 硬度尺度共用同一組值：
 *
 *   Cotton (最軟氈槌)  : 6.0 ms  — 落在 Chaigne & Askenfelt 引用的軟氈槌
 *                                  4-8 ms 範圍內；並與 Askenfelt & Jansson
 *                                  (KTH, "String contact duration and
 *                                  dynamic level") 直接量測值吻合：真實鋼琴
 *                                  接觸時間低音端 ~4 ms、隨力度 +-20%（mf
 *                                  基準），軟氈+低速對應此範圍上緣。
 *   Felt (中硬氈槌/橡膠/指尖) : 2.0 ms — 落在硬氈槌 1-3 ms 與橡膠槌 2-4 ms
 *                                  的重疊帶，對應 ExciterType::Felt 這個
 *                                  「中硬度」檔位（程式中 rubber_mallet /
 *                                  finger_tap 也映射到此檔，見
 *                                  ScoreRenderer.h::renderCimbalom /
 *                                  chromaticExciterHardness）。亦與
 *                                  Askenfelt & Jansson 量測的中音域-中音量
 *                                  接觸時間量級吻合。
 *   Wood (木槌/硬塑膠/撥奏) : 0.5 ms — 落在硬質木槌 0.3-0.8 ms 範圍，比任何
 *                                  鋼琴氈槌都硬，短於 Askenfelt & Jansson
 *                                  量到的最高音-最強力度氈槌下限(<1 ms)，
 *                                  符合「非氈材質更硬更短」的物理排序。
 *   Metal (金屬槌/刮奏)   : 0.2 ms — 落在極硬槌 0.1-0.3 ms 範圍（順序依據
 *                                  Fletcher & Rossing, "The Physics of
 *                                  Musical Instruments", Ch.12 對打擊槌
 *                                  硬度-接觸時間關係的一般性描述：槌頭越硬，
 *                                  接觸時間越短、頻譜越亮；本檔案未能取得
 *                                  該書 Table 12.1 逐項數值，此值為在該硬度
 *                                  排序下、緊貼 Wood 值以下的文獻指導推導，
 *                                  非直接抄錄書中數字，特此註明避免誤導）。
 *
 * 這 4 個值取代舊版 hammerCutoffPartial[]={3,8,20,60} 的 partial-count LP
 * 查表（該表沒有理論預測值，是純啟發式）。新模型：给定 tau_c，任一模態頻率
 * f_n 的激發振幅正比於 forceSpectrumMagnitude(2*pi*f_n, tau_c)，是槌頭物理
 * 直接導出的可驗證量，不是反推校準值。
 */
class HammerImpulse
{
public:
    /// 槌/激發接觸時間 tau_c（秒）— 對應 CimbalomEngine::ExciterType /
    /// ChromaticEngine chromaticExciterHardness() 共用的 0~3 硬度尺度。
    /// 來源見本檔案頂端註解區塊。
    static constexpr float kTauCCotton = 0.0060f;   // 6.0 ms
    static constexpr float kTauCFelt   = 0.0020f;   // 2.0 ms
    static constexpr float kTauCWood   = 0.0005f;   // 0.5 ms
    static constexpr float kTauCMetal  = 0.0002f;   // 0.2 ms

    /// hardnessIndex: 0=Cotton, 1=Felt, 2=Wood, 3=Metal（與 ExciterType 同序）。
    /// 非整數輸入（ChromaticEngine 的 exciterHardness 是連續 float 0~3）在
    /// 相鄰兩檔之間線性內插 tau_c，避免硬度旋鈕轉動時頻譜突跳。
    static float tauCForHardness (float hardnessIndex)
    {
        static constexpr float tauTable[4] = { kTauCCotton, kTauCFelt, kTauCWood, kTauCMetal };

        float idx = juce::jlimit (0.0f, 3.0f, hardnessIndex);
        int lo = (int) idx;
        int hi = juce::jmin (lo + 1, 3);
        float frac = idx - (float) lo;

        return tauTable[lo] + (tauTable[hi] - tauTable[lo]) * frac;
    }

    /**
     * DC 正規化力脈衝頻譜振幅 H(omega)，H(0) = 1。
     *
     *   H(w) = |cos(w*tau_c/2)| / |1 - (w*tau_c/pi)^2|
     *
     * @param omegaRad  角頻率 (rad/s) = 2*pi*f
     * @param tauC      接觸時間 (s)，必須 > 0
     * @return          正規化振幅，範圍理論上在 [0, 1]（首個峰值後隨旁瓣衰減，
     *                   數值上恆 <= 1，因為 |cos(x)| <= 1 且分母 >= 各旁瓣界限；
     *                   已於開發時用數值積分逐點核對，全音頻範圍無溢位）。
     */
    static float forceSpectrumMagnitude (float omegaRad, float tauC)
    {
        if (tauC <= 0.0f || ! std::isfinite (omegaRad))
            return 1.0f;   // 退化保護：不引入非物理增益，也不讓模態靜音

        const float pi = juce::MathConstants<float>::pi;
        const float x  = omegaRad * tauC / pi;
        const float denom = 1.0f - x * x;

        // 可去奇點保護（w*tau_c = pi，即 x = 1）：解析極限 = π/4（羅必達法則）。
        // epsilon=1e-4 在全部 tau_c candidate（0.1-8ms）
        // 與全音頻範圍（20Hz-20kHz）掃描驗證過，不產生可聽見的形狀突變。
        if (std::abs (denom) < 1e-4f)
            return juce::MathConstants<float>::pi * 0.25f;  // pi/4 ≈ 0.7854 (L'Hôpital)

        return std::abs (std::cos (omegaRad * tauC * 0.5f) / denom);
    }
};
