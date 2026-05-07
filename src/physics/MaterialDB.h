#pragma once
#include <juce_core/juce_core.h>
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
    static juce::StringArray getOrderedKeys()
    {
        return { "steel", "copper", "bronze", "aluminum", "brass",
                 "wood_spruce", "wood_maple", "glass", "rubber" };
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

        materials.clear();
        for (const auto& prop : materialsObj->getProperties())
        {
            auto key = prop.name.toString();
            auto* matObj = prop.value.getDynamicObject();
            if (matObj == nullptr) continue;

            Material mat;
            mat.displayName  = matObj->getProperty ("display_name").toString();
            mat.density      = (float) (double) matObj->getProperty ("density");
            mat.youngsModulus = (float) (double) matObj->getProperty ("youngs_modulus");
            mat.poissonRatio  = (float) (double) matObj->getProperty ("poisson_ratio");

            auto dampingVar = matObj->getProperty ("damping");
            if (auto* dampObj = dampingVar.getDynamicObject())
            {
                mat.damping.alpha           = (float) (double) dampObj->getProperty ("alpha");
                mat.damping.beta_air        = (float) (double) dampObj->getProperty ("beta_air");
                mat.damping.gamma_radiation  = (float) (double) dampObj->getProperty ("gamma_radiation");
            }

            materials[key] = mat;
        }

        return ! materials.empty();
    }

    std::map<juce::String, Material> materials;
};
