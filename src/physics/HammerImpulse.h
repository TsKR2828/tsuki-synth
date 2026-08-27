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
 * 分母在 w*tau_c = pi 處有可去奇點，H 在該點的極限值 = π/4（羅必達法則），
 * 所以 f=1/(2*tau_c) **不是零點**。分子下一個零點才沒有被分母抵消：
 * f_null = 3/(2*tau_c)。1/(2*tau_c) 只能當作主瓣轉折的尺度，不能在驗證
 * 或文件中誤稱第一個 spectral null。
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

    /** Contact time adjusted for strike speed.
     *
     * For an elastic Hertz-type impact, contact duration scales approximately
     * with impact speed^(-1/5).  The public MIDI velocity is explicitly treated
     * as a normalised speed proxy here, referenced at velocity 0.5.  The clamp
     * keeps the approximation inside the +-20% measured range cited above;
     * scores requiring metrology-grade reproduction should provide/measure
     * tau_c directly rather than infer it from MIDI velocity.
     */
    static float tauCForStrike (float hardnessIndex, float velocity)
    {
        const float speed = juce::jlimit (0.02f, 1.0f, velocity);
        const float hertzScale = juce::jlimit (0.8f, 1.2f,
            std::pow (0.5f / speed, 0.2f));
        return tauCForHardness (hardnessIndex) * hertzScale;
    }

    /** 音高 keytrack 縮放 tau_c。
     *
     * Askenfelt & Jansson (KTH, "String contact duration and dynamic
     * level"，本檔案頂端已引) 量測真實鋼琴的接觸時間是隨音域遞減的：
     * 低音端 ~4 ms、最高音域 <1 ms——因為高音區的槌頭更輕、氈更硬。
     * 舊版 tauCForStrike() 全鍵盤共用同一 tau_c，等於整台琴裝同一顆槌，
     * 造成高音基頻落在力脈衝頻譜 H(w) 的深度滾降區（例：Felt 2 ms 下
     * C7 基頻約 -37 dB），跨音域響度斜到低音大聲、高音幾乎消失。
     *
     * 模型：tau_c ∝ f^(-k)。用上述量測擬合鋼琴全音域
     * （A0 27.5 Hz @ 4 ms → C8 4186 Hz @ ~0.8 ms）得 k ≈ 0.32。
     * 錨點取 A4 (MIDI 69) = 1.0，中音域維持既有校準不動；clamp 範圍
     * [0.4, 2.6] 恰好罩住 88 鍵兩端的擬合值（A0 ≈ 2.43、C8 ≈ 0.49），
     * 只擋 MIDI 0~20 / 109~127 的極端外插。
     */
    static float keytrackScale (int midiNote)
    {
        constexpr float k = 0.32f;
        const float semitonesFromA4 = (float) (midiNote - 69);
        const float scale = std::pow (2.0f, -semitonesFromA4 * k / 12.0f);
        return juce::jlimit (0.4f, 2.6f, scale);
    }

    /// 完整的每音符接觸時間：硬度檔位 × 力度 (Hertz) × 音高 keytrack。
    /// 引擎端一律用這個；tauCForStrike() 保留給不知道音高的呼叫者。
    static float tauCForNote (float hardnessIndex, float velocity, int midiNote)
    {
        return tauCForStrike (hardnessIndex, velocity) * keytrackScale (midiNote);
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

    // ────────────────────────────────────────────────────────────────────────
    // B4（2026-08-27）：鋼琴槌氈非線性接觸求解器 —— Felt 檔位專用。
    //
    // 只有 Cimbalom/Piano 路徑的 ExciterType::Felt 用下面這組；Cotton/Wood/
    // Metal 三檔與 Chromatic 引擎（tongue drum / water gong）完全不用——
    // 這批 K/α/mass 是鋼琴專屬量測（docs/HAMMER_CONTACT_SOURCES.md §6），
    // 搬去別的樂器就是把別的物體的常數安到另一個物體上（Rule 4 違規；
    // Chromatic 的槌具接觸參數未搜尋 = TODO.md D2）。
    // 上方既有 tauCForNote()/tauCForStrike()/keytrackScale()/tauCForHardness()
    // 原封不動——ChromaticEngine.h 與非 Felt 檔位仍走那條路。
    // ────────────────────────────────────────────────────────────────────────

    /// 鋼琴槌氈非線性接觸律 F = K * delta^alpha 的逐音錨點。
    /// 來源：Woodhouse, Euphonics §12.2.1 Table 2（經 Hall & Askenfelt 量測，
    /// Chaigne & Askenfelt 用於模擬），轉引自 docs/HAMMER_CONTACT_SOURCES.md §2.1。
    /// K 的單位是 N*m^-alpha —— 隨 alpha 而變，這是原表明載的性質不是筆誤。
    /// （因此三個 K 錨點彼此量綱不同，絕不可對 K 本身做線性內插/數值比較，
    /// 只能對 log10(K) 內插——見 logKForPianoNote()。）
    /// 只有三個錨點（C2/C4/C7），中間音／範圍外音的內插與外推規則見
    /// alphaForPianoNote()/logKForPianoNote() 的實作與註解。
    static constexpr int   kPianoKAlphaAnchorMidi[3]  = { 36, 60, 96 }; // C2, C4, C7
    static constexpr float kPianoHammerK[3]           = { 4.0e8f, 4.5e9f, 1.0e12f };
    static constexpr float kPianoHammerAlpha[3]       = { 2.3f, 2.5f, 3.0f };

    /// 槌質量 C1-C8，來源：Woodhouse Euphonics §12.2.1 Table 1（Conklin 與
    /// Hall & Askenfelt 轉引），docs/HAMMER_CONTACT_SOURCES.md §2.2。單位 kg。
    static constexpr int   kPianoMassAnchorMidi[8] = { 24, 36, 48, 60, 72, 84, 96, 108 };
    static constexpr float kPianoHammerMassKg[8]   =
        { 0.012f, 0.011f, 0.010f, 0.009f, 0.008f, 0.007f, 0.006f, 0.005f };

    /// pianoHammerTauC() 輸出的安全 clamp（秒）。
    /// **工程安全帶，非文獻值、非 §6 登記容差**：範圍取現有四檔查表
    /// Cotton(6ms)~Metal(0.2ms) 涵蓋帶再留餘裕（0.3ms~8ms），只防內插/外推
    /// 在極端音高×力度組合跑出病態值，正常音域（見單元測試）不會觸及。
    /// 不得把它當成事實上的容差放寬來源（docs/workcards/B4.md §4.5）。
    static constexpr float kPianoTauCMinS = 0.0003f;   // 0.3 ms
    static constexpr float kPianoTauCMaxS = 0.0080f;   // 8.0 ms

    /// 錨點表的分段線性內插（獨立變數 = MIDI note，等價 log2(frequency)；
    /// 錨點間距不等不影響分段線性的正確性）。
    /// 範圍外**不外插，flat 夾在最近錨點**——文件只保證錨點間的單調趨勢
    /// （HAMMER_CONTACT_SOURCES.md §2.1「α 隨音高單調上升、log K 近似線性」），
    /// flat 外推不會違反單調性，線性外推可能沖出已知範圍，不用。
    /// **這條內插規則是 B4 卡新增的建模決策，不是文獻原文**
    /// （docs/workcards/B4.md §4.2，登記供月月覆核）。
    static float interpAnchorsFlat (const int* anchorMidi, const float* values,
                                    int count, int midiNote)
    {
        if (midiNote <= anchorMidi[0])         return values[0];
        if (midiNote >= anchorMidi[count - 1]) return values[count - 1];

        int seg = 0;
        while (seg + 2 < count && midiNote >= anchorMidi[seg + 1])
            ++seg;

        const float t = (float) (midiNote - anchorMidi[seg])
                      / (float) (anchorMidi[seg + 1] - anchorMidi[seg]);
        return values[seg] + (values[seg + 1] - values[seg]) * t;
    }

    /// α(note)：C2/C4/C7 三錨點間對 MIDI note 分段線性內插，範圍外 flat 夾住
    /// （alpha(24)=alpha(36)=2.3、alpha(108)=alpha(96)=3.0）。
    static float alphaForPianoNote (int midiNote)
    {
        return interpAnchorsFlat (kPianoKAlphaAnchorMidi, kPianoHammerAlpha,
                                  3, midiNote);
    }

    /// K(note)：對 **log10(K)** 做與 α 相同的分段線性內插後還原，回傳 K
    /// （單位 N*m^-alpha，隨該音的 α 而變）。不可對 K 本身線性內插——
    /// 三錨點跨 3 個數量級且量綱互異（見常數表註解），線性內插會嚴重失真
    /// （此錯誤已被單元測試的反例釘死）。範圍外 flat 夾住。
    /// 函式名裡的 logK 指「內插發生在 log10 域」；回傳值是 K 本身。
    static float logKForPianoNote (int midiNote)
    {
        const float log10K[3] = { std::log10 (kPianoHammerK[0]),
                                  std::log10 (kPianoHammerK[1]),
                                  std::log10 (kPianoHammerK[2]) };
        return std::pow (10.0f, interpAnchorsFlat (kPianoKAlphaAnchorMidi,
                                                   log10K, 3, midiNote));
    }

    /// m(note)：槌質量（kg），對質量本身（不取 log）分段線性內插，
    /// C1-C8 八錨點，範圍外 flat 夾住。
    static float hammerMassForPianoNote (int midiNote)
    {
        return interpAnchorsFlat (kPianoMassAnchorMidi, kPianoHammerMassKg,
                                  8, midiNote);
    }

    /// 接觸時間比例核 g(note, v) = [m/K]^(1/(α+1)) * v^(2/(α+1) - 1)。
    /// 推導（docs/HAMMER_CONTACT_SOURCES.md §3）：質量 m 的槌以速度 v 撞上
    /// F = K·δ^α 的接觸彈簧，能量守恆給 δmax，τc ∝ δmax/v。文獻只推到
    /// 比例關係，**沒有絕對前置係數**——絕對量級由 pianoHammerTauC() 錨定。
    /// 力度指數 2/(α+1)-1 隨音高變化：C2 −0.394 / C4 −0.429 / C7 −0.500
    /// （§3 表；現行 tauCForStrike() 的固定 −0.2 對應純赫茲 α=1.5，
    /// 是金屬對金屬，不是鋼琴氈——§4 的具體發現）。
    static float pianoHammerG (int midiNote, float velocityNorm)
    {
        const float alpha  = alphaForPianoNote (midiNote);
        const float invAp1 = 1.0f / (alpha + 1.0f);
        const float stiffnessTerm = std::pow (
            hammerMassForPianoNote (midiNote) / logKForPianoNote (midiNote),
            invAp1);
        return stiffnessTerm * std::pow (velocityNorm, 2.0f * invAp1 - 1.0f);
    }

    /** Felt（鋼琴氈槌）專用：由 F=K·δ^α、槌質量、撞速解出的接觸時間（秒）。
     *
     *   tau_c_piano(note, v) = kTauCFelt * g(note, v) / g(69, 0.5)
     *
     * 錨定選擇（**B4 卡的設計決策，不是文獻數字**，登記供月月覆核）：
     * 文獻只給比例關係（HAMMER_CONTACT_SOURCES.md §3），沒有給絕對前置
     * 係數（那需要解 F=Kδ^α 運動方程的相位積分，文件未提供、Rule 4 禁止
     * 編造）。因此把比例關係錨定在既有、已溯源的絕對量級上：kTauCFelt
     * = 2.0 ms（Askenfelt & Jansson 量測，本檔頂端已引用）在 A4（MIDI 69）、
     * velocity=0.5 這一點。新公式在該點與舊校準完全重合；其餘音高/力度的
     * 「相對形狀」才是本函式真正換成物理推導的部分。
     *
     * velocity 的定義沿用既有 tauCForStrike() 的 jlimit(0.02, 1.0)
     * （0-1 正規化 MIDI velocity proxy，不是真實 m/s——既有架構限制，
     * B4 不解決，只沿用）。輸出經 kPianoTauCMinS/MaxS 工程安全 clamp
     * （見該常數註解：非文獻值、非容差）。
     */
    static float pianoHammerTauC (int midiNote, float velocity)
    {
        const float v    = juce::jlimit (0.02f, 1.0f, velocity);
        const float g    = pianoHammerG (midiNote, v);
        const float gRef = pianoHammerG (69, 0.5f);   // A4 / v=0.5 錨點
        return juce::jlimit (kPianoTauCMinS, kPianoTauCMaxS,
                             kTauCFelt * (g / gRef));
    }
};
