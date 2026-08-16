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
 *   damping.beta_air          — 空氣黏滯阻尼
 *   damping.gamma_radiation   — 聲輻射損耗
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
        float beta_air        = 1.2e-7f;
        float gamma_radiation = 2e-5f;
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
        eta，使既有樂譜在錨點上的作者意圖逐位元保留，其他音高則與材質
        路徑一致地隨頻率變化——而不是把樂譜裡的數字重新解釋成 eta
        （那會讓 0.4 之類的值變成橡膠等級的阻尼）。beta_air/gamma_radiation
        永遠維持材質驅動、不受覆寫影響；橋耦合項（bridgeLoss，2026-08-16 B1，
        見 StringModel::bridgeLossRate()）同理，永遠疊加、不受 damping_override
        影響。 */
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
            auto* dampObj = matObj->getProperty ("damping").getDynamicObject();
            double eta = 0.0, betaAir = 0.0, gammaRadiation = 0.0;
            if (dampObj == nullptr
                || dampObj->hasProperty ("alpha")
                || ! finiteNumber (dampObj->getProperty ("eta"), eta)
                || ! finiteNumber (dampObj->getProperty ("beta_air"), betaAir)
                || ! finiteNumber (dampObj->getProperty ("gamma_radiation"), gammaRadiation)
                || eta < 0.0 || betaAir < 0.0 || gammaRadiation < 0.0)
                return false;

            Material mat;
            mat.displayName = displayName.toString();
            mat.density = (float) density;
            mat.youngsModulus = (float) youngsModulus;
            mat.poissonRatio = (float) poissonRatio;
            mat.damping.eta = (float) eta;
            mat.damping.beta_air = (float) betaAir;
            mat.damping.gamma_radiation = (float) gammaRadiation;
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
