#pragma once
#include <cmath>
#include <juce_core/juce_core.h>

/**
 * 音板輻射效率骨架 — B6 施工卡 Phase 1（`docs/workcards/B6.md`）
 *
 * 這個檔案只做「輻射骨架」：`σ(f)`（無量綱輻射效率，0~1）與
 * `η_rad(f)`（輻射損耗因子）。**不**把它們接成絕對 Pa/瓦特——那條校準鏈
 * 需要 `docs/workcards/B6.md` §6 Phase 2 的月月裁決（見該卡 §4.3），本檔
 * 完全不碰。純函式、無副作用、不依賴任何 B1/B5 的具名 struct（呼叫端把
 * 數值抽出來傳進來，見 `StringModel::soundboardDynamics()`）。
 *
 * 溯源等級（三種，不可混為一談，見 `docs/RADIATION_POWER_SOURCES.md`）：
 *   - `criticalFrequency()`／`acousticCutoffFrequency()`：**直接查到**，
 *     `docs/RADIATION_POWER_SOURCES.md` §2.1（`fc`，已更正原施工卡誤讀）
 *     與 §4.1（`fga`，原式無誤，B6.md 引用一致）。
 *   - `radiationLossFactor()`：**推導**自兩個標準定義（輻射效率的定義
 *     `σ ≡ W_rad/(ρ₀c₀S⟨v²⟩)` ＋ SEA 損耗因子定義 `η≡P/(ωE)`），代數消去
 *     `S`／`⟨v²⟩` 後得到，**不是**逐字引用某本教科書的頁碼——
 *     `docs/RADIATION_POWER_SOURCES.md` §2.2 有完整推導過程。
 *   - `radiationEfficiency()` 的 `σ(f)` 形狀：**工程近似**，非 Ege &
 *     Boutillon 論文給的曲線（兩篇論文查過，沒有），是「緊緻聲源輻射電阻
 *     ∝ (ka)² ∝ f²」這個聲學通識的類比套用，`docs/RADIATION_POWER_SOURCES.md`
 *     §4 第 2 點已指出真實次臨界輻射曲線（Maidanik 1962 邊緣輻射理論）比
 *     單純 `f²` 複雜，本近似只保證量級（§3 自洽檢查），不保證形狀精確。
 *   - `radiatedEnergyFraction()`：`docs/RADIATION_POWER_SOURCES.md` §5 建議
 *     的 `η_i(f) = η_total − η_rad(f)` 自洽減法之下，
 *     `fraction_radiated = η_rad/(η_i+η_rad) = η_rad/η_total` 代數化簡
 *     （分母的 `η_i`／`η_rad` 相加剛好等於常數 `η_total`，不需要分別算
 *     `η_i`）。這是 B6.md §4.2「能量守恆捷徑」的核心量，**不是**逐音準確值
 *     （音板被當成單一集總 SEA 子系統，丟失相鄰半音 T60 相差 5 倍的峰谷
 *     結構，`docs/RADIATION_POWER_SOURCES.md` §4 第 4 點已指出）。
 */
class RadiationModel
{
public:
    /** 空氣中聲速 (m/s)，全 repo 沿用的 `ca` 常數同一個值
     *  （`docs/BRIDGE_ADMITTANCE_SOURCES.md`／`StringModel::bridgeLossRate()`）。*/
    static constexpr float kSpeedOfSoundAir = 340.0f;

    /** 空氣密度 (kg/m^3)，`docs/RADIATION_POWER_SOURCES.md` §3 沿用值。*/
    static constexpr float kAirDensity = 1.2f;

    /** 肋距 p (m)，`docs/BRIDGE_ADMITTANCE_SOURCES.md` §4 第 2 點／
     *  `EXTERNAL_ANCHOR_SOURCES.md` §3 一致給出，無符號歧義。*/
    static constexpr float kRibSpacingM = 0.13f;

    /** 臨界（重合）頻率。
     *
     *   fc = ca^2 / (2*pi * sqrt(D / rhoS))
     *
     *  **這是對 `docs/workcards/B6.md` §4.1 原式的更正**：施工卡原文寫
     *  `fc = ca^2/(2*pi*sqrt(Dx*H))`，是對 Ege & Boutillon
     *  (arXiv:1305.3057) §5.1 公式(29) `fc = ca^2/(2π·(D̄ₓᴴ)^(1/2))` 的
     *  誤讀——`D̄ₓᴴ` 是單一符號，`H` 是「homogenised（肋條均質化）」的
     *  上標，不是第二個要相乘的量；`D̄ = D/μ`（`μ`=面密度=`rhoS`）本身
     *  才是那個符號的完整定義，量綱 `m^4/s^2` 也只吻合除法而非乘法。
     *  完整查證與頁碼：`docs/RADIATION_POWER_SOURCES.md` §2.1。
     *
     *  @param D     音板彎曲剛度 (N*m)，即 B1 `StringModel::bridgeLossRate()`
     *               內部算的 `D = E*h^3/(12*(1-nu^2))`（見
     *               `StringModel::soundboardDynamics()`）。
     *  @param rhoS  音板面密度 (kg/m^2)，`rho*h`。
     *  @param ca    空氣中聲速 (m/s)，預設 `kSpeedOfSoundAir`。
     *  @return fc (Hz)；輸入非有限或非正值時 fail-closed 回傳 `-1.0f`
     *          （呼叫端不得把 -1 當成一個真的頻率使用）。
     */
    static float criticalFrequency (float D, float rhoS, float ca = kSpeedOfSoundAir)
    {
        if (! std::isfinite (D) || D <= 0.0f
            || ! std::isfinite (rhoS) || rhoS <= 0.0f
            || ! std::isfinite (ca) || ca <= 0.0f)
            return -1.0f;

        const float ratio = D / rhoS;
        if (! std::isfinite (ratio) || ratio <= 0.0f)
            return -1.0f;

        const float fc = (ca * ca) / (2.0f * juce::MathConstants<float>::pi * std::sqrt (ratio));
        return (std::isfinite (fc) && fc > 0.0f) ? fc : -1.0f;
    }

    /** 波導聲學截止頻率（模型有效範圍上限）。
     *
     *   fga = ca / (2*p)     p = 肋距 (m)
     *
     *  無符號歧義，`docs/BRIDGE_ADMITTANCE_SOURCES.md` §4 第 2 點與
     *  `EXTERNAL_ANCHOR_SOURCES.md` §3 一致，`docs/workcards/B6.md` §4.1
     *  原式不需要更正。`f >= fga` 時均質板模型本身失效（音板變成被肋條
     *  界定的波導集合），本模型對這個範圍**不給任何預測**（見
     *  `radiationEfficiency()` 的 sentinel 行為）。
     *
     *  @param ca  空氣中聲速 (m/s)，預設 `kSpeedOfSoundAir`。
     *  @param p   肋距 (m)，預設 `kRibSpacingM`。
     *  @return fga (Hz)；輸入非有限或非正值時 fail-closed 回傳 `-1.0f`。
     */
    static float acousticCutoffFrequency (float ca = kSpeedOfSoundAir, float p = kRibSpacingM)
    {
        if (! std::isfinite (ca) || ca <= 0.0f || ! std::isfinite (p) || p <= 0.0f)
            return -1.0f;
        const float fga = ca / (2.0f * p);
        return (std::isfinite (fga) && fga > 0.0f) ? fga : -1.0f;
    }

    /** 輻射效率 sigma(f) 的次臨界頻率近似——來源：緊緻/次波長聲源的輻射阻抗
     *  隨頻率平方增長是聲學的通用結果（monopole 輻射電阻 ∝ (ka)^2 ∝ f^2，見
     *  任一聲學教科書的小聲源輻射章節，例如 Kinsler & Frey *Fundamentals of
     *  Acoustics* 或 Fahy *Foundations of Engineering Acoustics* 的緊緻聲源章節）。
     *  **這不是 Ege & Boutillon 論文逐字給出的公式**（兩篇論文查過，沒有
     *  給出量化的 `σ(f)` 曲線，只有定性的「哪個頻段輻射有效」判斷，見
     *  `docs/RADIATION_POWER_SOURCES.md` §2.2），是本卡在查無更精確公式時
     *  採用的工程近似，2026-08-28 依 `docs/RADIATION_POWER_SOURCES.md` §5
     *  的建議啟用（Phase 0 判定：量級站得住，形狀本身非逐字文獻曲線）。
     *  若之後借到 Cremer/Heckl/Ungar 或 Fahy & Gardonio 原文，或找到
     *  Maidanik (1962) 邊緣輻射理論的完整曲線，應優先替換本近似式。
     *
     *  @param f    partial 頻率 (Hz)。
     *  @param fc   臨界頻率 (Hz)，見 `criticalFrequency()`。
     *  @param fga  波導聲學截止頻率 (Hz)，見 `acousticCutoffFrequency()`。
     *  @return
     *    - `f >= fga`：`-1.0f`（模型有效範圍外的 sentinel，呼叫端必須據此
     *      排除該 partial 的輻射欄位，不是輸出一個 -1 當作預測值）；
     *    - `fc <= f < fga`：`1.0f`（重合頻率以上，輻射效率飽和）；
     *    - `f < fc`：`(f/fc)^2`，clamp 到 `[0,1]`；
     *    - `fc`／`fga` 非有限或非正值：`-1.0f`（fail-closed，與範圍外同一個
     *      sentinel，呼叫端一樣要排除）。
     */
    static float radiationEfficiency (float f, float fc, float fga)
    {
        if (! std::isfinite (f) || f < 0.0f
            || ! std::isfinite (fc) || fc <= 0.0f
            || ! std::isfinite (fga) || fga <= 0.0f)
            return -1.0f;

        if (f >= fga) return -1.0f;               // 模型有效範圍外，呼叫端須排除
        if (f >= fc)  return 1.0f;

        const float ratio = f / fc;
        return juce::jlimit (0.0f, 1.0f, ratio * ratio);
    }

    /** 輻射損耗因子 η_rad(f)。
     *
     *   η_rad(f) = rhoAir * cAir * sigma(f) / (omega * rhoS)     omega = 2*pi*f
     *
     *  **推導**（非逐字引用，見 `docs/RADIATION_POWER_SOURCES.md` §2.2）：
     *  由輻射效率的定義 `sigma ≡ W_rad/(rhoAir*cAir*S*<v^2>)` 與 SEA
     *  慣用的損耗因子定義 `eta ≡ P/(omega*E)`（`E = rhoS*S*<v^2>` 為平板
     *  儲能的 SEA 慣例寫法）代入相除，`S`／`<v^2>` 代數消去後得到。
     *
     *  @param f       partial 頻率 (Hz)，用來算 `omega = 2*pi*f`。
     *  @param sigma   `radiationEfficiency()` 的回傳值。若為 sentinel
     *                 `< 0.0f`（表示呼叫端本該排除這個 partial），本函式
     *                 同樣 fail-closed 回傳 `-1.0f`，不會把 sentinel 當成
     *                 一個真的 sigma 值代入公式。
     *  @param rhoAir  空氣密度 (kg/m^3)，預設 `kAirDensity`。
     *  @param cAir    空氣中聲速 (m/s)，預設 `kSpeedOfSoundAir`。
     *  @param rhoS    音板面密度 (kg/m^2)。
     *  @return η_rad(f)（無量綱）；任何輸入非有限、`f<=0`、`rhoS<=0` 或
     *          `sigma<0`（sentinel）時 fail-closed 回傳 `-1.0f`。
     */
    static float radiationLossFactor (float f, float sigma,
                                      float rhoAir = kAirDensity,
                                      float cAir = kSpeedOfSoundAir,
                                      float rhoS = 0.0f)
    {
        if (! std::isfinite (f) || f <= 0.0f
            || ! std::isfinite (sigma) || sigma < 0.0f
            || ! std::isfinite (rhoAir) || rhoAir <= 0.0f
            || ! std::isfinite (cAir) || cAir <= 0.0f
            || ! std::isfinite (rhoS) || rhoS <= 0.0f)
            return -1.0f;

        const float omega = 2.0f * juce::MathConstants<float>::pi * f;
        const float etaRad = (rhoAir * cAir * sigma) / (omega * rhoS);
        return (std::isfinite (etaRad) && etaRad >= 0.0f) ? etaRad : -1.0f;
    }

    /** 輻射佔比 fraction_radiated(f) = eta_rad(f) / eta_total。
     *
     *  `docs/RADIATION_POWER_SOURCES.md` §5 的建議：`eta_i(f) = eta_total -
     *  eta_rad(f)`（自洽減法，不借用弦材質的 `eta` 欄位），代入
     *  `fraction_radiated = eta_rad/(eta_i+eta_rad)` 後，分母
     *  `eta_i+eta_rad = eta_total`（常數）直接消掉，化簡成這條除法——
     *  **不需要**先算 `eta_i` 再相加，代數上是同一件事。
     *
     *  這是 B6.md §4.2「能量守恆捷徑」的核心無量綱量：音板被當成單一集總
     *  SEA 子系統時，這是「弦流入音板的功率裡，最終以聲輻射（而非結構
     *  內耗）離開的比例」的骨架版本。**不是逐音準確值**（見本檔類別註解
     *  最後一點）。
     *
     *  @param etaRad    `radiationLossFactor()` 的回傳值。若為 sentinel
     *                   `< 0.0f`，fail-closed 回傳 `-1.0f`。
     *  @param etaTotal  音板總損耗因子（結構內耗+輻射），
     *                   `docs/BRIDGE_ADMITTANCE_SOURCES.md` §2.1 轉引
     *                   Ege & Boutillon 的 `eta ≈ 0.02 ± 0.01`。
     *  @return 比例，clamp 到 `[0,1]`（若某個材質/幾何組合讓
     *          `eta_rad(f)` 算出來超過 `eta_total`，代表模型的骨架數字
     *          在那個頻率已經不自洽——clamp 到 1.0 是 fail-safe，不是
     *          聲稱「100% 輻射」為物理事實，呼叫端不應依賴這種邊界情況）。
     *          `etaTotal<=0`、非有限值、或 `etaRad` 為 sentinel 時
     *          fail-closed 回傳 `-1.0f`。
     */
    static float radiatedEnergyFraction (float etaRad, float etaTotal)
    {
        if (! std::isfinite (etaRad) || etaRad < 0.0f
            || ! std::isfinite (etaTotal) || etaTotal <= 0.0f)
            return -1.0f;

        return juce::jlimit (0.0f, 1.0f, etaRad / etaTotal);
    }
};
