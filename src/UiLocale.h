#pragma once
#include <juce_core/juce_core.h>

// ======================================================================
//  UiLocale -- centralized UI text for English / Traditional Chinese
//
//  All Chinese text is constructed via juce::CharPointer_UTF8 to avoid
//  u8/char8_t type issues and ensure correct decoding on all platforms.
//  APVTS parameter IDs and choice values are NEVER modified by this layer.
// ======================================================================

enum class UiLanguage { English, Chinese };

class UiLocale
{
public:
    static UiLanguage getLanguage()              { return lang_; }
    static void       setLanguage (UiLanguage l) { lang_ = l; }
    static bool       isChinese()                { return lang_ == UiLanguage::Chinese; }

    // ------------------------------------------------------------------
    //  label()  -- get the display label for a UI control by paramID
    //  Returns English text when in English mode.
    //  Returns pure Chinese when in Chinese mode (if translation exists).
    //  Falls back to English text if no Chinese entry.
    // ------------------------------------------------------------------
    static juce::String label (const juce::String& key)
    {
        if (isChinese())
        {
            for (const auto& e : labelTable())
                if (key == e.key && e.zh[0] != '\0')
                    return T (e.zh);
        }
        for (const auto& e : labelTable())
            if (key == e.key)
                return juce::String (e.en);
        return key;
    }

    // ------------------------------------------------------------------
    //  comboItems()  -- get localized ComboBox display items
    //  Returns localized items for paramIDs that have translations.
    //  Returns empty array for params without translations -> caller
    //  should fall back to APVTS choices.
    //  Item count and order always match the APVTS ChoiceParam.
    // ------------------------------------------------------------------
    static juce::StringArray comboItems (const juce::String& paramID)
    {
        // ---- Materials (shared by cim_material and chr_material) ----
        if (paramID == "cim_material" || paramID == "chr_material")
        {
            if (isChinese())
                return { T("鋼"), T("銅"), T("青銅"),
                         T("鋁"), T("黃銅"),
                         T("雲杉木"), T("楓木"),
                         T("玻璃"), T("橡膠") };
            return { "Steel", "Copper", "Bronze", "Aluminum", "Brass",
                     "Spruce", "Maple", "Glass", "Rubber" };
        }

        // ---- Hammer ----
        if (paramID == "cim_hammer")
        {
            if (isChinese())
                return { T("棉槌"), T("氈槌"), T("木槌"), T("金屬槌") };
            return { "Cotton", "Felt", "Wood", "Metal" };
        }

        // ---- Chromatic sub-engine ----
        if (paramID == "chr_sub_engine")
        {
            if (isChinese())
                return { T("空靈鼓"), T("水鑼"), T("自訂泛音") };
            return { "Tongue Drum", "Water Gong", "Custom" };
        }

        // ---- Chromatic exciter ----
        if (paramID == "chr_exciter")
        {
            if (isChinese())
                return { T("柔"), T("中"), T("硬"), T("銳") };
            return { "Soft", "Medium", "Hard", "Sharp" };
        }

        // ---- FM Sound Type ----
        if (paramID == "fm_type")
        {
            if (isChinese())
                return { T("鋼琴"), T("電鋼琴"), T("顫音琴"), T("鐘"),
                         T("風琴"), T("墊底"), T("貝斯"), T("銅管") };
            return { "Piano", "E.Piano", "Vibraphone", "Bell",
                     "Organ", "Pad", "Bass", "Brass" };
        }

        // ---- Distortion type ----
        if (paramID == "fx_dist_type")
        {
            if (isChinese())
                return { T("過載"), T("位元破碎"), T("波形摺疊") };
            return { "Overdrive", "Bitcrush", "Wavefold" };
        }

        // No localized items for this param -> caller uses APVTS choices
        return {};
    }

    // ------------------------------------------------------------------
    //  presetName()  -- localized factory preset display name
    // ------------------------------------------------------------------
    static juce::String presetName (const juce::String& englishName)
    {
        if (! isChinese())
            return englishName;

        for (const auto& p : presetNameTable())
            if (englishName == p.en)
                return T (p.zh);
        return englishName;
    }

    // ------------------------------------------------------------------
    //  paramCountText()  -- "8 params" / "8 個參數"
    // ------------------------------------------------------------------
    static juce::String paramCountText (int n)
    {
        if (isChinese())
            return juce::String (n) + T (" 個參數");
        return juce::String (n) + " params";
    }

    // ------------------------------------------------------------------
    //  toggleLabel()  -- text for the language toggle button
    // ------------------------------------------------------------------
    static juce::String toggleLabel()
    {
        return isChinese() ? T("中文") : "EN";
    }

private:
    static inline UiLanguage lang_ = UiLanguage::Chinese;

    static juce::String T (const char* utf8)
    {
        return juce::String (juce::CharPointer_UTF8 (utf8));
    }

    // Label lookup table: { paramID, englishLabel, chineseLabel }
    struct Entry { const char* key; const char* en; const char* zh; };

    static const std::vector<Entry>& labelTable()
    {
        static const std::vector<Entry> t = {
            // -- Macro knobs --
            { "macro_material",    "MATERIAL",    "材質"       },
            { "macro_tension",     "TENSION",     "張力"       },
            { "macro_damping",     "DAMPING",     "阻尼"       },
            { "macro_strike",      "STRIKE",      "敲擊位置"   },
            { "macro_brightness",  "BRIGHT",      "亮度"       },
            { "macro_body",        "BODY",        "共鳴體"     },
            { "macro_noise",       "NOISE",       "雜質"       },
            { "macro_output",      "OUTPUT",      "輸出"       },

            // -- Cimbalom combo labels --
            { "cim_material",      "MATERIAL",    "材質"       },
            { "cim_hammer",        "HAMMER",      "槌頭"       },

            // -- Cimbalom knob labels --
            { "cim_strike_pos",    "STRIKE POS",  "敲擊點"     },
            { "cim_diameter",      "DIAMETER",    "直徑"       },
            { "cim_num_strings",   "STRINGS",     "弦數"       },
            { "cim_detuning",      "DETUNING",    "解諧"       },

            // -- Chromatic combo labels --
            { "chr_sub_engine",    "SUB-ENGINE",  "子引擎"     },
            { "chr_material",      "MATERIAL",    "材質"       },
            { "chr_exciter",       "EXCITER",     "激振器"     },

            // -- Chromatic knob labels --
            { "chr_strike_pos",    "STRIKE POS",  "敲擊點"     },
            { "chr_thickness",     "THICKNESS",   "厚度"       },
            { "chr_size",          "SIZE",        "尺寸"       },
            { "chr_pitch_glide",   "PITCH GLIDE", "滑音"       },

            // -- FM Piano --
            { "fm_type",           "SOUND TYPE",  "音色類型"   },
            { "fm_ratio",          "RATIO",       "比率"       },
            { "fm_index",          "MOD INDEX",   "調變指數"   },
            { "fm_brightness",     "TONE DECAY",  "音色衰減"   },
            { "fm_feedback",       "FEEDBACK",    "回饋"       },
            { "fm_attack",         "ATTACK",      "起音"       },
            { "fm_release",        "RELEASE",     "釋放"       },

            // -- Effects --
            { "fx_reverb_mix",     "MIX",         "混合"       },
            { "fx_reverb_size",    "SIZE",        "空間大小"   },
            { "fx_delay_time",     "TIME",        "時間"       },
            { "fx_delay_feedback", "FB",          "回授"       },
            { "fx_delay_mix",      "MIX",         "混合"       },
            { "fx_comp_threshold", "THRESH",      "閾值"       },
            { "fx_comp_ratio",     "RATIO",       "比率"       },

            // -- Distortion --
            { "fx_dist_type",      "TYPE",        "類型"       },
            { "fx_dist_drive",     "DRIVE",       "驅動"       },
            { "fx_dist_instability","INSTABILITY", "不穩定度"   },
            { "fx_dist_mix",       "MIX",         "混合"       },

            // -- Section dividers --
            { "ui_section_macro",    "MACRO",      "巨集"       },
            { "ui_section_engine",   "ENGINE",     "音源引擎"   },
            { "ui_section_effects",  "EFFECTS",    "效果"       },

            // -- Effect panels --
            { "ui_panel_reverb",     "REVERB",     "殘響"       },
            { "ui_panel_delay",      "DELAY",      "延遲"       },
            { "ui_panel_compressor", "COMPRESSOR", "壓縮器"     },
            { "ui_panel_distortion", "DISTORTION", "失真"       },

            // -- Engine tabs --
            { "ui_tab_cimbalom",     "Cimbalom",   "揚琴"       },
            { "ui_tab_chromatic",    "Chromatic",  "半音音源"   },
            { "ui_tab_fm",           "FM Piano",   "頻率鋼琴"   },

            // -- Buttons --
            { "ui_btn_save",         "Save",       "儲存"       },
            { "ui_btn_init",         "Init",       "初始化"     },
            { "ui_btn_rec",          "REC",        "REC"        },
            { "ui_btn_stop",         "STOP",       "STOP"       },

            // -- Analyzer --
            { "ui_scope",            "SCOPE",      "示波器"     },

            // -- Save dialog --
            { "ui_save_title",       "Save Preset",                 "儲存預設"       },
            { "ui_save_prompt",      "Enter a name for the preset:", "輸入預設名稱：" },
            { "ui_save_field",       "Preset Name:",                "預設名稱："     },
            { "ui_btn_cancel",       "Cancel",                      "取消"           },

            // -- Recorder status --
            { "ui_record_ready",     "Ready to record",             "準備錄音"       },
            { "ui_recording",        "Recording",                   "錄音中"         },
            { "ui_record_saved",     "Saved recording",             "已儲存錄音"     },
            { "ui_record_failed",    "Recording failed",            "錄音失敗"       },
        };
        return t;
    }

    // Preset name lookup table
    struct PresetNameEntry { const char* en; const char* zh; };

    static const std::vector<PresetNameEntry>& presetNameTable()
    {
        static const std::vector<PresetNameEntry> t = {
            { "Steel Hammered Dulcimer", "鋼製揚琴"       },
            { "Copper Warm Strings",     "銅弦暖音"       },
            { "Glass Wind Chimes",       "玻璃風鈴"       },
            { "Muted Felt Piano",        "氈槌柔音"       },
            { "Crystal Tongue Drum",     "水晶空靈鼓"     },
            { "Bronze Water Gong",       "青銅水鑼"       },
            { "Wooden Kalimba",          "木製拇指琴"     },
            { "Ethereal Steel Bells",    "空靈鋼鐘"       },
            { "Acoustic Piano",          "原聲鋼琴"       },
            { "Electric Rhodes",         "電鋼琴"         },
            { "DX7 Crystal Bell",        "DX7 水晶鐘"     },
            { "Church Organ",            "教堂風琴"       },
        };
        return t;
    }
};
