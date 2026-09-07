#pragma once

#include <juce_core/juce_core.h>
#include <vector>

// Centralized display text for the plugin UI.
// APVTS parameter IDs, parameter names, and AudioParameterChoice values stay
// in their original English form; this layer only changes visible UI text.
enum class UiLanguage { English, Chinese };

class UiLocale
{
public:
    static UiLanguage getLanguage() { return lang_; }
    static bool isChinese()         { return lang_ == UiLanguage::Chinese; }

    static void setLanguage (UiLanguage language)
    {
        lang_ = language;
        syncFrameworkTranslations();
    }

    static void syncFrameworkTranslations()
    {
        if (! isChinese())
        {
            juce::LocalisedStrings::setCurrentMappings (nullptr);
            return;
        }

        static const char* const translations = R"locale(
language: Traditional Chinese
countries: tw hk mo

"Options" = "選項"
"Audio/MIDI Settings..." = "音訊／MIDI 設定..."
"Audio/MIDI Settings" = "音訊／MIDI 設定"
"Save current state..." = "儲存目前狀態..."
"Load a saved state..." = "載入已儲存狀態..."
"Reset to default state" = "重設為預設狀態"
"Save" = "儲存"
"Cancel" = "取消"
"OK" = "確定"
)locale";

        juce::LocalisedStrings::setCurrentMappings (
            new juce::LocalisedStrings (T (translations), false));
    }

    static juce::String text (const juce::String& key)
    {
        if (const auto* entry = findEntry (textTable(), key))
            return isChinese() ? T (entry->zh) : juce::String (entry->en);

        return key;
    }

    static juce::String label (const juce::String& paramID)
    {
        return text (paramID);
    }

    static juce::String toggleLabel()
    {
        return isChinese() ? text ("languageChinese") : text ("languageEnglish");
    }

    static juce::String paramCount (int count)
    {
        return isChinese()
            ? juce::String (count) + T (" 個參數")
            : juce::String (count) + " params";
    }

    static juce::String engineHeaderName (int engine)
    {
        switch (engine)
        {
            case 0:  return text ("engineHeaderCimbalom");
            case 1:  return text ("engineHeaderChromatic");
            case 2:  return text ("engineHeaderFm");
            default: return text ("engine");
        }
    }

    static juce::String engineHeaderSubtitle (int engine)
    {
        switch (engine)
        {
            case 0:  return text ("engineSubtitleCimbalom");
            case 1:  return text ("engineSubtitleChromatic");
            case 2:  return text ("engineSubtitleFm");
            default: return {};
        }
    }

    static juce::String tabName (int engine)
    {
        switch (engine)
        {
            case 0:  return text ("tabCimbalom");
            case 1:  return text ("tabChromatic");
            case 2:  return text ("tabFm");
            default: return {};
        }
    }

    static juce::String factoryPresetName (const juce::String& englishName)
    {
        if (! isChinese())
            return englishName;

        if (const auto* entry = findEntry (presetTable(), englishName))
            return T (entry->zh);

        return englishName;
    }

    static juce::StringArray comboItems (const juce::String& paramID)
    {
        if (paramID == "cim_material" || paramID == "chr_material")
            return isChinese()
                ? juce::StringArray { T ("鋼"), T ("銅"), T ("青銅"), T ("鋁"), T ("黃銅"),
                                      T ("雲杉"), T ("楓木"), T ("玻璃"), T ("橡膠") }
                : juce::StringArray { "Steel", "Copper", "Bronze", "Aluminum", "Brass",
                                      "Spruce", "Maple", "Glass", "Rubber" };

        if (paramID == "cim_hammer")
            return isChinese()
                ? juce::StringArray { T ("棉槌"), T ("毛氈槌"), T ("木槌"), T ("金屬槌") }
                : juce::StringArray { "Cotton", "Felt", "Wood", "Metal" };

        if (paramID == "chr_sub_engine")
            return isChinese()
                ? juce::StringArray { T ("舌鼓"), T ("水鑼"), T ("自訂") }
                : juce::StringArray { "Tongue Drum", "Water Gong", "Custom" };

        if (paramID == "chr_exciter")
            return isChinese()
                ? juce::StringArray { T ("柔和"), T ("中等"), T ("強硬"), T ("尖銳") }
                : juce::StringArray { "Soft", "Medium", "Hard", "Sharp" };

        if (paramID == "fm_type")
            return isChinese()
                ? juce::StringArray { T ("鋼琴"), T ("電鋼琴"), T ("顫音琴"), T ("鐘聲"),
                                      T ("風琴"), T ("音墊"), T ("貝斯"), T ("銅管") }
                : juce::StringArray { "Piano", "E.Piano", "Vibraphone", "Bell",
                                      "Organ", "Pad", "Bass", "Brass" };

        if (paramID == "fx_dist_type")
            return isChinese()
                ? juce::StringArray { T ("過載"), T ("位元破碎"), T ("波形摺疊") }
                : juce::StringArray { "Overdrive", "Bitcrush", "Wavefold" };

        return {};
    }

private:
    struct Entry { const char* key; const char* en; const char* zh; };

    static inline UiLanguage lang_ = UiLanguage::Chinese;

    static juce::String T (const char* utf8)
    {
        return juce::String (juce::CharPointer_UTF8 (utf8));
    }

    static const Entry* findEntry (const std::vector<Entry>& table,
                                   const juce::String& key)
    {
        for (const auto& entry : table)
            if (key == entry.key)
                return &entry;

        return nullptr;
    }

    static const std::vector<Entry>& textTable()
    {
        static const std::vector<Entry> table {
            { "languageEnglish", "English", "英文" },
            { "languageChinese", "Chinese", "中文" },

            { "appTitle", "TsukiSynth", "TsukiSynth" },
            { "options", "Options", "選項" },
            { "save", "Save", "儲存" },
            { "init", "Init", "初始化" },
            { "cancel", "Cancel", "取消" },
            { "presetSaveTitle", "Save Preset", "儲存預設" },
            { "presetSaveMessage", "Enter a name for the preset:", "請輸入預設名稱：" },
            { "presetNameLabel", "Preset Name:", "預設名稱：" },
            { "presetDefaultName", "My Preset", "我的預設" },

            { "macro", "Macro", "巨集" },
            { "engine", "Engine", "音源引擎" },
            { "effects", "Effects", "效果" },
            { "scope", "Scope", "示波器" },
            { "reverb", "Reverb", "殘響" },
            { "delay", "Delay", "延遲" },
            { "compressor", "Compressor", "壓縮器" },
            { "distortion", "Distortion", "失真" },
            { "noSignal", "No signal", "無訊號" },

            { "tabCimbalom", "Cimbalom", "揚琴" },
            { "tabChromatic", "Chromatic", "半音音源" },
            { "tabFm", "FM Piano", "調頻鋼琴" },
            { "engineHeaderCimbalom", "Cimbalom Engine", "揚琴音源" },
            { "engineHeaderChromatic", "Chromatic Engine", "半音音源" },
            { "engineHeaderFm", "FM Piano Engine", "調頻鋼琴音源" },
            { "engineSubtitleCimbalom", "Physical Modeling String", "物理模型弦鳴" },
            { "engineSubtitleChromatic", "Beam / Plate / Custom", "簧片、板鳴、自訂" },
            { "engineSubtitleFm", "Frequency Modulation", "頻率調變" },

            { "macro_material", "Material", "材質" },
            { "macro_tension", "Tension", "張力" },
            { "macro_damping", "Damping", "阻尼" },
            { "macro_strike", "Strike", "擊弦" },
            { "macro_brightness", "Brightness", "亮度" },
            { "macro_body", "Body", "共鳴體" },
            { "macro_noise", "Noise", "噪音" },
            { "macro_output", "Output", "輸出" },

            { "cim_material", "Material", "材質" },
            { "cim_hammer", "Hammer", "琴槌" },
            { "cim_strike_pos", "Strike", "擊弦" },
            { "cim_diameter", "Diameter", "弦徑" },
            { "cim_num_strings", "Strings", "弦數" },
            { "cim_detuning", "Detuning", "微調" },

            { "chr_sub_engine", "Sub Engine", "子音源" },
            { "chr_material", "Material", "材質" },
            { "chr_exciter", "Exciter", "激發器" },
            { "chr_strike_pos", "Strike", "擊弦" },
            { "chr_thickness", "Thickness", "厚度" },
            { "chr_size", "Size", "尺寸" },
            { "chr_pitch_glide", "Pitch Glide", "滑音" },

            { "fm_type", "Sound Type", "音色類型" },
            { "fm_ratio", "Ratio", "比率" },
            { "fm_index", "Mod Index", "調變指數" },
            { "fm_brightness", "Brightness", "亮度" },
            { "fm_feedback", "Feedback", "回授" },
            { "fm_attack", "Attack", "起音" },
            { "fm_release", "Release", "釋放" },

            { "fx_reverb_mix", "Mix", "混合" },
            { "fx_reverb_size", "Size", "空間大小" },
            { "fx_delay_time", "Time", "時間" },
            { "fx_delay_feedback", "Feedback", "回授" },
            { "fx_delay_mix", "Mix", "混合" },
            { "fx_comp_threshold", "Threshold", "閾值" },
            { "fx_comp_ratio", "Ratio", "比率" },

            { "fx_dist_type", "Type", "類型" },
            { "fx_dist_drive", "Drive", "驅動" },
            { "fx_dist_instability", "Instability", "不穩定度" },
            { "fx_dist_mix", "Mix", "混合" },
        };

        return table;
    }

    static const std::vector<Entry>& presetTable()
    {
        static const std::vector<Entry> table {
            { "Steel Hammered Dulcimer", "Steel Hammered Dulcimer", "鋼弦擊奏揚琴" },
            { "Copper Warm Strings", "Copper Warm Strings", "暖銅弦鳴" },
            { "Glass Wind Chimes", "Glass Wind Chimes", "玻璃風鈴" },
            { "Muted Felt Piano", "Muted Felt Piano", "柔氈悶音琴" },
            { "Crystal Tongue Drum", "Crystal Tongue Drum", "水晶舌鼓" },
            { "Bronze Water Gong", "Bronze Water Gong", "青銅水鑼" },
            { "Wooden Kalimba", "Wooden Kalimba", "木質卡林巴" },
            { "Ethereal Steel Bells", "Ethereal Steel Bells", "空靈鋼鐘" },
            { "Acoustic Piano", "Acoustic Piano", "原聲鋼琴" },
            { "Electric Rhodes", "Electric Rhodes", "電鋼琴" },
            { "DX7 Crystal Bell", "DX7 Crystal Bell", "水晶鐘聲" },
            { "Church Organ", "Church Organ", "教堂風琴" },
        };

        return table;
    }
};
