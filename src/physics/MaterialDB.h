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
 *   damping.alpha             — 材質內部阻尼
 *   damping.beta_air          — 空氣黏滯阻尼
 *   damping.gamma_radiation   — 聲輻射損耗
 */
class MaterialDB
{
public:
    struct Damping
    {
        float alpha          = 0.5f;
        float beta_air       = 1.2e-7f;
        float gamma_radiation = 2e-5f;
    };

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

            auto* dampObj = matObj->getProperty ("damping").getDynamicObject();
            double alpha = 0.0, betaAir = 0.0, gammaRadiation = 0.0;
            if (dampObj == nullptr
                || ! finiteNumber (dampObj->getProperty ("alpha"), alpha)
                || ! finiteNumber (dampObj->getProperty ("beta_air"), betaAir)
                || ! finiteNumber (dampObj->getProperty ("gamma_radiation"), gammaRadiation)
                || alpha < 0.0 || betaAir < 0.0 || gammaRadiation < 0.0)
                return false;

            Material mat;
            mat.displayName = displayName.toString();
            mat.density = (float) density;
            mat.youngsModulus = (float) youngsModulus;
            mat.poissonRatio = (float) poissonRatio;
            mat.damping.alpha = (float) alpha;
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
