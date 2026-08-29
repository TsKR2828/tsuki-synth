#pragma once
#include <juce_core/juce_core.h>
#include <cmath>
#include <map>

/**
 * 材質數據庫 — 載入 data/materials.json
 *
 * 每種材質包含：
 *   density        (kg/m³)   — 影響模態頻率
 *   youngs_modulus  (Pa)      — 材質剛性
 *   poisson_ratio   (無量綱)  — 橫向變形
 *   damping.eta               — 材質內部阻尼「損耗因子」(loss factor，無量綱)
 *   damping.beam_plate_beta_air          — 空氣黏滯阻尼（**只給 Beam/Plate**）
 *   damping.beam_plate_gamma_radiation   — 「聲輻射」損耗（**只給 Beam/Plate**）
 *
 * ── 三個 damping 欄位各自的引擎適用範圍（2026-08-24 B3）──
 *
 *   eta                        ： 所有引擎（String/Beam/Plate）。Phase H 已溯源
 *                                的材質損耗因子（文獻表）。
 *   beam_plate_beta_air        ： **只有 Beam/Plate（Chromatic 引擎）讀取**。
 *   beam_plate_gamma_radiation ： 同上。兩者仍是「查無出處」的擬合值
 *                                （TODO.md D1，Beam/Plate 的阻尼溯源未搜尋）。
 *
 * 弦（StringModel，Cimbalom/Piano）自 B3 起**完全不讀**這兩個欄位：弦的
 * 空氣黏滯＋黏彈性＋位錯損耗改用 Cuesta & Valette (1988) 的零自由參數
 * 三機制公式，由頻率/弦半徑/張力/材質 (rho, E) 直接算出
 * （StringModel::stringAirViscDislQInv()，docs/STRING_DAMPING_SOURCES.md §2）。
 * 欄位名帶 beam_plate_ 前綴正是為了讓「改這兩個數字不會影響弦音色」這件事
 * 從名字上就看得出來。舊 schema（bare beta_air/gamma_radiation）fail-closed
 * 拒載，見 parseJson()。
 *
 * ── eta 取代舊 alpha 的理由（2026-08-10 阻尼寬頻化）──
 *
 * 舊欄位 `alpha` 是「頻率無關常數」，但它的來源推導本身
 * （`reports/materials_physicalization_proposal.md` §1.2-§1.3）是
 *   T60(f) = 2.2 / (f · eta)   =>   內部摩擦項 = eta · f / 2.2
 * 也就是**與頻率成正比**。舊實作把它凍結在單一錨點（MIDI 60，
 * f=261.6256 Hz，alpha = eta × 118.921），所以只在那一個音高上與文獻一致，
 * 其他音高都是近似（該檔 §1.3 的 "Critical caveat" 已誠實標註）。
 * 本次改為直接存 eta、在每個模態頻率上求值，內部摩擦項因此在**全音域**
 * 都與文獻損耗因子一致（見 StringModel/BeamModel/PlateModel 的
 * decayTimeForFrequency）。eta 數值本身完全沿用該提案 §2 的文獻表，
 * 未重新選值；舊 alpha 逐項驗證為 eta×118.921（捨入誤差 ≤6.7e-4 相對）。
 *
 * ── wood_spruce 的雙重語意（2026-08-16 B1 琴橋導納）──
 *
 * `wood_spruce` 這個材質項目自 B1 起同時被用在兩種不同語意：(1) 弦材質候選
 * （Cimbalom/Chromatic 引擎 UI 可選的木弦，走 density/youngsModulus 算弦本身
 * 的模態），(2) CimbalomEngine.h::kBridgeSoundboardMaterialKey 的橋耦合預設
 * 共鳴板參照材質（StringModel::bridgeLossRate() 用同一個 Material 的
 * youngsModulus/poissonRatio/density 算共鳴板彎曲剛度）。兩種語意互不影響
 * （前者算的是弦本身的振動，後者算的是共鳴板本身的導納），只是巧合共用同
 * 一份 JSON 條目——這與 docs/RESEARCH_INDEX.md §6 已預見的「同一份
 * materials.json 對不同引擎語意不同」是同類情形。若之後有人把 cimbalom 的
 * 弦材質也設成 wood_spruce，橋耦合公式仍會用同一個 wood_spruce 物件的彈性
 * 參數算共鳴板，這不是 bug，只是容易被誤會，故留此註解。
 *
 * ── Orthotropic（正交異向常數，2026-08-28 B5 草稿）──
 *
 * `Material::orthotropic` 是**死資料**：目前沒有任何引擎/PlateModel/BeamModel
 * 讀它。任何未來的消費端在讀取前**必須**先檢查 `orthotropic.present == true`；
 * `present == false` 時所有數值欄位都是結構預設值，不得被當成「等向性
 * =0」之類的隱含語意使用。同理 `hasGRT == false` 時 `ratioGRT_EL` 是未定義
 * 用途的預設值 0.0f（原文獻表「—」，不是量測出來的 0）。詳見 `Orthotropic`
 * struct 上方註解與 `docs/workcards/B5.md`。
 */
class MaterialDB
{
public:
    struct Damping
    {
        /// 損耗因子 eta（Q = 1/eta）。內部摩擦對衰減率的貢獻 = eta·f/2.2。
        float eta             = 2.0e-4f;
        /// 只給 Beam/Plate 用（B3 改名，見類別頂端註解）；StringModel 不讀。
        float beam_plate_beta_air        = 1.2e-7f;
        /// 只給 Beam/Plate 用（B3 改名，見類別頂端註解）；StringModel 不讀。
        float beam_plate_gamma_radiation = 2e-5f;
    };

    /// T60 = 2.2/(f·eta) 推導出的內部摩擦係數（見上方註解與提案 §1.2）。
    /// 2.2 = ln(1000)/pi = 6.9078/pi，與 ModalResonator 的 -60dB 慣例同源。
    static constexpr float kEtaToDecayRate = 2.2f;

    /// 舊 alpha 的凍結錨點（MIDI 60 中央 C）。只有 damping_override 的
    /// 相容換算還需要它；材質路徑已不再有單一錨點。
    static constexpr float kLegacyAnchorHz = 261.6256f;

    /** 內部摩擦對衰減率（1/T60）的貢獻 = eta · f / 2.2。 */
    static float internalFrictionRate (float eta, float frequency)
    {
        return eta * frequency / kEtaToDecayRate;
    }

    /** score 的 `damping_override` 數字語意不變：它一直是、現在仍是
        「**MIDI 60 錨點上**的內部摩擦衰減率」（即舊 alpha 的尺度，
        32 首既有樂譜的授權值落在 0.28~1.15）。寬頻化後把它換算成等效
        eta——而不是把樂譜裡的數字重新解釋成 eta（那會讓 0.4 之類的值變成
        橡膠等級的阻尼）。覆寫只換掉內部摩擦項；弦的空氣黏滯＋黏彈＋位錯
        三機制（B3，StringModel::stringAirViscDislQInv()）與橋耦合項
        （bridgeLoss，2026-08-16 B1，見 StringModel::bridgeLossRate()）永遠
        疊加、不受 damping_override 影響。注意 B3 之後「錨點 T60 逐位元保留」
        的保證不再成立：MIDI 60 上除了被覆寫的內部摩擦項，還會疊加頻率相依的
        三機制項（見 CimbalomEngine.h 的 dampingOverride 註解區塊）。 */
    static float etaFromAnchoredDamping (float anchoredRate)
    {
        return anchoredRate * kEtaToDecayRate / kLegacyAnchorHz;
    }

    /**
     * 正交異向常數（僅木材，2026-08-28 新增，B5 施工卡草稿階段）
     *
     * 來源：USDA Forest Service, Forest Products Laboratory, "Wood Handbook —
     * Wood as an Engineering Material," General Technical Report FPL-GTR-190,
     * Chapter 5. Table 5-1（彈性比，12% 含水率）與 Table 5-2（泊松比，12%
     * 含水率）。逐字轉錄，未從任何曲線圖讀值（docs/WOOD_ANISOTROPY_SOURCES.md
     * §7 已記錄取得方式）。ratio_* 皆以 E_L 為 1 的比值；E_L 本身沿用既有
     * `youngsModulus`（`docs/MATERIALS_SOURCES.md` 已文件化為縱向 E）。
     * poisson_RL / poisson_TL 與其餘 4 個泊松比是文獻各自獨立量測值，
     * **刻意不用互易關係（μij/Ei = μji/Ej）相互推算或修正**——原文明確警告
     * 該關係在實測上並非總是嚴格成立（見上述文件 §3）。
     *
     * 樹種對應（可能有選種歧義，見 docs/workcards/B5.md §4.2「選種說明」，
     * 月月裁決 2026-08-28：照建議值走（Sitka / sugar maple / red oak；
     * birch 唯一條目無歧義））：
     *   wood_spruce -> Spruce, Sitka
     *   wood_maple  -> Maple, sugar
     *   wood_birch  -> Birch, yellow（唯一表列條目，無歧義）
     *   wood_oak    -> Oak, red
     *
     * ⚠️ 這批資料目前沒有任何程式碼路徑消費（PlateModel/BeamModel 仍是
     * 單一標量 E/nu 的 Kirchhoff/Euler-Bernoulli 公式）。present=false 或
     * 欄位不存在時，呼叫端不得假設任何隱含語意。
     */
    struct Orthotropic
    {
        bool present = false;                 // false = 這個材質沒有正交異向資料
        juce::String sourceSpecies;
        float moistureContentPct = 12.0f;
        float mpPercent          = 25.0f;
        float ratioET_EL = 0.0f, ratioER_EL = 0.0f;
        float ratioGLR_EL = 0.0f, ratioGLT_EL = 0.0f;
        bool  hasGRT = false;                 // false = 原表「—」，ratioGRT_EL 未定義
        float ratioGRT_EL = 0.0f;
        float poissonLR = 0.0f, poissonLT = 0.0f, poissonRT = 0.0f;
        float poissonTR = 0.0f, poissonRL = 0.0f, poissonTL = 0.0f;
    };

    struct Material
    {
        juce::String displayName;
        float density        = 7800.0f;   // kg/m³
        float youngsModulus   = 200e9f;    // Pa
        float poissonRatio    = 0.29f;
        Damping damping;
        Orthotropic orthotropic;
    };

    bool loadFromString (const juce::String& jsonText)
    {
        auto parsed = juce::JSON::parse (jsonText);
        return parseJson (parsed);
    }

    bool loadFromBinary (const char* data, int sizeInBytes)
    {
        return loadFromString (juce::String::fromUTF8 (data, sizeInBytes));
    }

    bool loadFromFile (const juce::File& jsonFile)
    {
        if (! jsonFile.existsAsFile())
            return false;

        auto text = jsonFile.loadFileAsString();
        auto parsed = juce::JSON::parse (text);
        return parseJson (parsed);
    }

    const Material* getMaterial (const juce::String& name) const
    {
        auto it = materials.find (name);
        return it != materials.end() ? &it->second : nullptr;
    }

    std::vector<juce::String> getMaterialNames() const
    {
        std::vector<juce::String> names;
        for (const auto& pair : materials)
            names.push_back (pair.first);
        return names;
    }

    int size() const { return (int) materials.size(); }

    /// 以固定順序取得材質 key（給 AudioParameterChoice 用）
    static const juce::StringArray& getOrderedKeys()
    {
        static const juce::StringArray keys {
            "steel", "copper", "bronze", "aluminum", "brass",
            "wood_spruce", "wood_maple", "glass", "rubber"
        };
        return keys;
    }

private:
    bool parseJson (const juce::var& parsed)
    {
        if (parsed.isVoid())
            return false;

        auto* obj = parsed.getDynamicObject();
        if (obj == nullptr)
            return false;

        auto materialsVar = obj->getProperty ("materials");
        auto* materialsObj = materialsVar.getDynamicObject();
        if (materialsObj == nullptr)
            return false;

        std::map<juce::String, Material> parsedMaterials;
        for (const auto& prop : materialsObj->getProperties())
        {
            auto key = prop.name.toString();
            auto* matObj = prop.value.getDynamicObject();
            if (key.isEmpty() || matObj == nullptr)
                return false;

            auto finiteNumber = [] (const juce::var& value, double& result)
            {
                if (! value.isInt() && ! value.isInt64() && ! value.isDouble())
                    return false;
                result = (double) value;
                return std::isfinite (result);
            };

            const auto displayName = matObj->getProperty ("display_name");
            double density = 0.0, youngsModulus = 0.0, poissonRatio = 0.0;
            if (! displayName.isString() || displayName.toString().trim().isEmpty()
                || ! finiteNumber (matObj->getProperty ("density"), density)
                || ! finiteNumber (matObj->getProperty ("youngs_modulus"), youngsModulus)
                || ! finiteNumber (matObj->getProperty ("poisson_ratio"), poissonRatio)
                || density <= 0.0 || youngsModulus <= 0.0
                || poissonRatio < 0.0 || poissonRatio >= 0.5)
                return false;

            // Fail-closed on the pre-2026-08-10 schema: a file that still carries the
            // frequency-independent `alpha` is REJECTED rather than silently reinterpreted
            // — the two fields differ by the 118.921 anchor factor, so accepting an alpha
            // as an eta would under-damp every material by ~5 orders of magnitude.
            //
            // Fail-closed on the pre-B3 schema too: a file that still carries the bare
            // `beta_air`/`gamma_radiation` keys is REJECTED rather than silently
            // reinterpreted as the renamed beam_plate_* fields — those two names now
            // mean "Beam/Plate-only" and no longer feed StringModel at all, so a file
            // written for the old schema must not load until it is explicitly migrated.
            auto* dampObj = matObj->getProperty ("damping").getDynamicObject();
            double eta = 0.0, betaAir = 0.0, gammaRadiation = 0.0;
            if (dampObj == nullptr
                || dampObj->hasProperty ("alpha")
                || dampObj->hasProperty ("beta_air")
                || dampObj->hasProperty ("gamma_radiation")
                || ! finiteNumber (dampObj->getProperty ("eta"), eta)
                || ! finiteNumber (dampObj->getProperty ("beam_plate_beta_air"), betaAir)
                || ! finiteNumber (dampObj->getProperty ("beam_plate_gamma_radiation"), gammaRadiation)
                || eta < 0.0 || betaAir < 0.0 || gammaRadiation < 0.0)
                return false;

            // ── Orthotropic (B5, 2026-08-28 draft) — optional, wood-only, fail-closed ──
            // Key absent entirely -> present = false (legal: non-wood materials, or wood
            // not yet backfilled). Key present but not a JSON object -> reject whole file.
            // Key present and object -> every sub-field must validate or the WHOLE file
            // is rejected (all-or-nothing, same convention as density/youngs_modulus/etc
            // above) — this is NOT a per-material rejection.
            Orthotropic ortho;
            if (matObj->hasProperty ("orthotropic"))
            {
                auto* orthoObj = matObj->getProperty ("orthotropic").getDynamicObject();
                if (orthoObj == nullptr)
                    return false;

                // The four species this workcard has transcribed literature tables for
                // (docs/workcards/B5.md §4.2). Anything else is an unsourced number —
                // fail closed rather than silently accepting an untranscribed species.
                static const juce::StringArray allowedSpecies {
                    "Spruce, Sitka", "Maple, sugar", "Birch, yellow", "Oak, red"
                };

                const auto sourceSpeciesVar = orthoObj->getProperty ("source_species");
                double moistureContentPct = 0.0, mpPercent = 0.0;
                double ratioET_EL = 0.0, ratioER_EL = 0.0, ratioGLR_EL = 0.0, ratioGLT_EL = 0.0;
                double poissonLR = 0.0, poissonLT = 0.0, poissonRT = 0.0;
                double poissonTR = 0.0, poissonRL = 0.0, poissonTL = 0.0;

                if (! sourceSpeciesVar.isString()
                    || sourceSpeciesVar.toString().trim().isEmpty()
                    || ! allowedSpecies.contains (sourceSpeciesVar.toString())
                    // moisture_content_pct must be exactly 12 (Wood Handbook Table 5-1/5-2
                    // measurement basis) — no source supports any other reference value.
                    || ! finiteNumber (orthoObj->getProperty ("moisture_content_pct"), moistureContentPct)
                    || moistureContentPct != 12.0
                    || ! finiteNumber (orthoObj->getProperty ("mp_percent"), mpPercent)
                    || mpPercent <= 0.0 || mpPercent > 40.0
                    // ratio_* are open interval (0,1): cross-grain stiffness is strictly
                    // less than longitudinal for orthotropic wood — this is definitional.
                    || ! finiteNumber (orthoObj->getProperty ("ratio_ET_EL"), ratioET_EL)
                    || ratioET_EL <= 0.0 || ratioET_EL >= 1.0
                    || ! finiteNumber (orthoObj->getProperty ("ratio_ER_EL"), ratioER_EL)
                    || ratioER_EL <= 0.0 || ratioER_EL >= 1.0
                    || ! finiteNumber (orthoObj->getProperty ("ratio_GLR_EL"), ratioGLR_EL)
                    || ratioGLR_EL <= 0.0 || ratioGLR_EL >= 1.0
                    || ! finiteNumber (orthoObj->getProperty ("ratio_GLT_EL"), ratioGLT_EL)
                    || ratioGLT_EL <= 0.0 || ratioGLT_EL >= 1.0
                    || ! finiteNumber (orthoObj->getProperty ("poisson_LR"), poissonLR)
                    || poissonLR < 0.0 || poissonLR >= 1.0
                    || ! finiteNumber (orthoObj->getProperty ("poisson_LT"), poissonLT)
                    || poissonLT < 0.0 || poissonLT >= 1.0
                    || ! finiteNumber (orthoObj->getProperty ("poisson_RT"), poissonRT)
                    || poissonRT < 0.0 || poissonRT >= 1.0
                    || ! finiteNumber (orthoObj->getProperty ("poisson_TR"), poissonTR)
                    || poissonTR < 0.0 || poissonTR >= 1.0
                    || ! finiteNumber (orthoObj->getProperty ("poisson_RL"), poissonRL)
                    || poissonRL < 0.0 || poissonRL >= 1.0
                    || ! finiteNumber (orthoObj->getProperty ("poisson_TL"), poissonTL)
                    || poissonTL < 0.0 || poissonTL >= 1.0)
                    return false;

                // ratio_GRT_EL: the ONE field allowed to be explicit JSON `null` (Table
                // 5-1 lists "—" for maple/oak — no measured value exists). `null` is NOT
                // the same as absent: the key must be present (explicit null or a number
                // in (0,1)); a missing key, or any other type (e.g. the string "n/a"),
                // is rejected. This line is the fix for the exact bug §11 of B5.md warns
                // about — if it is ever relaxed to "missing key defaults to hasGRT=false"
                // or "null coerces to 0", a future consumer could silently read a
                // physically-nonsensical zero shear modulus. testOrthotropicSchemaFailClosed
                // must FAIL if this is loosened.
                if (! orthoObj->hasProperty ("ratio_GRT_EL"))
                    return false;
                const auto grtVar = orthoObj->getProperty ("ratio_GRT_EL");
                bool hasGRT = false;
                double ratioGRT_EL = 0.0;
                if (grtVar.isVoid())
                    hasGRT = false;
                else if (finiteNumber (grtVar, ratioGRT_EL) && ratioGRT_EL > 0.0 && ratioGRT_EL < 1.0)
                    hasGRT = true;
                else
                    return false;

                ortho.present = true;
                ortho.sourceSpecies = sourceSpeciesVar.toString();
                ortho.moistureContentPct = (float) moistureContentPct;
                ortho.mpPercent = (float) mpPercent;
                ortho.ratioET_EL = (float) ratioET_EL;
                ortho.ratioER_EL = (float) ratioER_EL;
                ortho.ratioGLR_EL = (float) ratioGLR_EL;
                ortho.ratioGLT_EL = (float) ratioGLT_EL;
                ortho.hasGRT = hasGRT;
                ortho.ratioGRT_EL = hasGRT ? (float) ratioGRT_EL : 0.0f;
                ortho.poissonLR = (float) poissonLR;
                ortho.poissonLT = (float) poissonLT;
                ortho.poissonRT = (float) poissonRT;
                ortho.poissonTR = (float) poissonTR;
                ortho.poissonRL = (float) poissonRL;
                ortho.poissonTL = (float) poissonTL;
            }
            // else: "orthotropic" key absent entirely -> ortho stays at struct defaults
            // (present = false). This is a legal state, not an error (§0/§5.1 of B5.md).

            Material mat;
            mat.displayName = displayName.toString();
            mat.density = (float) density;
            mat.youngsModulus = (float) youngsModulus;
            mat.poissonRatio = (float) poissonRatio;
            mat.damping.eta = (float) eta;
            mat.damping.beam_plate_beta_air = (float) betaAir;
            mat.damping.beam_plate_gamma_radiation = (float) gammaRadiation;
            mat.orthotropic = ortho;
            parsedMaterials.emplace (key, mat);
        }

        if (parsedMaterials.empty())
            return false;

        // Commit only after every entry is valid.  A failed reload must not
        // destroy the last known-good database used by active voices.
        materials = std::move (parsedMaterials);
        return true;
    }

    std::map<juce::String, Material> materials;
};
