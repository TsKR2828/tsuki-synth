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

    struct Material
    {
        juce::String displayName;
        float density        = 7800.0f;   // kg/m³
        float youngsModulus   = 200e9f;    // Pa
        float poissonRatio    = 0.29f;
        Damping damping;
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

            Material mat;
            mat.displayName = displayName.toString();
            mat.density = (float) density;
            mat.youngsModulus = (float) youngsModulus;
            mat.poissonRatio = (float) poissonRatio;
            mat.damping.eta = (float) eta;
            mat.damping.beam_plate_beta_air = (float) betaAir;
            mat.damping.beam_plate_gamma_radiation = (float) gammaRadiation;
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
