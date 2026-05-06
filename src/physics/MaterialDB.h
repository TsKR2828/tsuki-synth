#pragma once

#include <juce_core/juce_core.h>
#include <map>
#include <string>

struct MaterialDamping
{
    double alpha          = 0.0;
    double betaAir        = 0.0;
    double gammaRadiation = 0.0;
};

struct Material
{
    std::string key;
    std::string displayName;
    double density       = 0.0;
    double youngsModulus  = 0.0;
    double poissonRatio   = 0.0;
    MaterialDamping damping;
};

class MaterialDB
{
public:
    bool loadFromString (const juce::String& jsonText)
    {
        auto parsed = juce::JSON::parse (jsonText);
        return parseJson (parsed);
    }

    bool loadFromFile (const juce::File& jsonFile)
    {
        if (! jsonFile.existsAsFile())
            return false;

        auto parsed = juce::JSON::parse (jsonFile.loadFileAsString());
        return parseJson (parsed);
    }

    const Material* getMaterial (const std::string& key) const
    {
        auto it = materials.find (key);
        return it != materials.end() ? &it->second : nullptr;
    }

    std::vector<std::string> getMaterialKeys() const
    {
        std::vector<std::string> keys;
        for (const auto& pair : materials)
            keys.push_back (pair.first);
        return keys;
    }

    int getNumMaterials() const { return static_cast<int> (materials.size()); }

private:
    bool parseJson (const juce::var& parsed)
    {
        if (! parsed.isObject())
            return false;

        materials.clear();

        auto materialsVar = parsed.getProperty ("materials", {});
        auto* obj = materialsVar.isObject()
                  ? materialsVar.getDynamicObject()
                  : parsed.getDynamicObject();

        if (obj == nullptr)
            return false;

        for (const auto& prop : obj->getProperties())
        {
            auto key = prop.name.toString().toStdString();
            auto& val = prop.value;

            Material mat;
            mat.key           = key;
            mat.displayName   = val["display_name"].toString().toStdString();
            mat.density       = static_cast<double> (val["density"]);
            mat.youngsModulus  = static_cast<double> (val["youngs_modulus"]);
            mat.poissonRatio  = static_cast<double> (val["poisson_ratio"]);

            auto damp = val["damping"];
            mat.damping.alpha          = static_cast<double> (damp["alpha"]);
            mat.damping.betaAir        = static_cast<double> (damp["beta_air"]);
            mat.damping.gammaRadiation = static_cast<double> (damp["gamma_radiation"]);

            materials[key] = mat;
        }

        return ! materials.empty();
    }

    std::map<std::string, Material> materials;
};
