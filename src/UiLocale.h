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
    //  Returns "Chinese English" when in Chinese mode (if translation exists).
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
                return { T("鋼 Steel"),     T("銅 Copper"),   T("青銅 Bronze"),
                         T("鋁 Aluminum"),  T("黃銅 Brass"),
                         T("雲杉木 Spruce"), T("楓木 Maple"),
                         T("玻璃 Glass"),    T("橡膠 Rubber") };
            return { "Steel", "Copper", "Bronze", "Aluminum", "Brass",
                     "Spruce", "Maple", "Glass", "Rubber" };
        }

        // ---- Hammer ----
        if (paramID == "cim_hammer")
        {
            if (isChinese())
                return { T("棉槌 Cotton"), T("氈槌 Felt"),
                         T("木槌 Wood"),   T("金屬槌 Metal") };
            return { "Cotton", "Felt", "Wood", "Metal" };
        }

        // ---- Chromatic sub-engine ----
        if (paramID == "chr_sub_engine")
        {
            if (isChinese())
                return { T("空靈鼓 Tongue Drum"), T("水鑼 Water Gong"),
                         T("自訂泛音 Custom") };
            return { "Tongue Drum", "Water Gong", "Custom" };
        }

        // No localized items for this param -> caller uses APVTS choices
        return {};
    }

    // ------------------------------------------------------------------
    //  toggleLabel()  -- text for the language toggle button
    // ------------------------------------------------------------------
    static juce::String toggleLabel()
    {
        return isChinese() ? "EN" : T("中文");
    }

private:
    static inline UiLanguage lang_ = UiLanguage::Chinese;

    // Safe juce::String from raw UTF-8 bytes
    static juce::String T (const char* utf8)
    {
        return juce::String (juce::CharPointer_UTF8 (utf8));
    }

    // Label lookup table: { paramID, englishLabel, chineseLabel }
    // Empty zh string "" means no Chinese translation -> use English.
    struct Entry { const char* key; const char* en; const char* zh; };

    static const std::vector<Entry>& labelTable()
    {
        static const std::vector<Entry> t = {
            // -- Macro knobs --
            { "macro_material",    "MATERIAL",    "材質 Material"    },
            { "macro_tension",     "TENSION",     "張力 Tension"     },
            { "macro_damping",     "DAMPING",     "阻尼 Damping"    },
            { "macro_strike",      "STRIKE",      "敲擊位置 Strike"  },
            { "macro_brightness",  "BRIGHT",      "亮度 Brightness"  },
            { "macro_body",        "BODY",        "共鳴體 Body"      },
            { "macro_noise",       "NOISE",       "雜質 Noise"       },
            { "macro_output",      "OUTPUT",      "輸出 Output"      },

            // -- Cimbalom combo labels --
            { "cim_material",      "MATERIAL",    "材質 Material"    },
            { "cim_hammer",        "HAMMER",      "槌頭 Hammer"      },

            // -- Cimbalom knob labels --
            { "cim_strike_pos",    "STRIKE POS",  ""                 },
            { "cim_diameter",      "DIAMETER",    ""                 },
            { "cim_num_strings",   "STRINGS",     ""                 },
            { "cim_detuning",      "DETUNING",    ""                 },

            // -- Chromatic combo labels --
            { "chr_sub_engine",    "SUB-ENGINE",  "子引擎 Sub Engine" },
            { "chr_material",      "MATERIAL",    "材質 Material"    },
            { "chr_exciter",       "EXCITER",     ""                 },

            // -- Chromatic knob labels --
            { "chr_strike_pos",    "STRIKE POS",  ""                 },
            { "chr_thickness",     "THICKNESS",   ""                 },
            { "chr_size",          "SIZE",        ""                 },
            { "chr_pitch_glide",   "PITCH GLIDE", ""                 },

            // -- FM Piano --
            { "fm_type",           "SOUND TYPE",  ""                 },
            { "fm_ratio",          "RATIO",       ""                 },
            { "fm_index",          "MOD INDEX",   ""                 },
            { "fm_brightness",     "BRIGHTNESS",  ""                 },
            { "fm_feedback",       "FEEDBACK",    ""                 },
            { "fm_attack",         "ATTACK",      ""                 },
            { "fm_release",        "RELEASE",     ""                 },

            // -- Effects --
            { "fx_reverb_mix",     "MIX",         ""                 },
            { "fx_reverb_size",    "SIZE",        ""                 },
            { "fx_delay_time",     "TIME",        ""                 },
            { "fx_delay_feedback", "FB",          ""                 },
            { "fx_delay_mix",      "MIX",         ""                 },
            { "fx_comp_threshold", "THRESH",      ""                 },
            { "fx_comp_ratio",     "RATIO",       ""                 },

            // -- Distortion --
            { "fx_dist_type",      "TYPE",        ""                 },
            { "fx_dist_drive",     "DRIVE",       ""                 },
            { "fx_dist_instability","INSTABILITY", ""                },
            { "fx_dist_mix",       "MIX",         ""                 },
        };
        return t;
    }
};
