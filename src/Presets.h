#pragma once
#include <juce_audio_processors/juce_audio_processors.h>

/**
 * Factory preset system for TsukiSynth
 *
 * Values are RAW parameter values (not normalized 0~1).
 * Applied via param->convertTo0to1(raw) then setValueNotifyingHost().
 *
 * Presets grouped by engine:
 *   0-5:  Cimbalom (physical modeling string)
 *   6-11: Chromatic (beam / plate / custom)
 *  12-19: FM Piano (frequency modulation, 8 presets matching 8 sound types)
 */
struct PresetEntry
{
    const char* paramID;
    float rawValue;
};

struct FactoryPreset
{
    const char* name;
    const PresetEntry* params;
    int numParams;
};

// Macro helper for static preset arrays
#define PRESET_BEGIN(varName) static const PresetEntry varName[] = {
#define PRESET_END };

// ========== Cimbalom presets ==========

PRESET_BEGIN (preset_steel_dulcimer)
    { "engine",           0 },
    { "cim_material",     0 },       // Steel
    { "cim_strike_pos",   0.30f },
    { "cim_diameter",     0.80f },   // mm
    { "cim_hammer",       2 },       // Wood
    { "cim_num_strings",  3 },
    { "cim_detuning",     5.0f },    // cents
    { "fx_reverb_mix",    0.20f },
    { "fx_reverb_size",   0.50f },
    { "fx_delay_mix",     0.00f },
    { "fx_comp_threshold", -12.0f },
    { "fx_comp_ratio",    4.0f },
PRESET_END

PRESET_BEGIN (preset_copper_warm)
    { "engine",           0 },
    { "cim_material",     1 },       // Copper
    { "cim_strike_pos",   0.45f },
    { "cim_diameter",     1.20f },
    { "cim_hammer",       1 },       // Felt
    { "cim_num_strings",  4 },
    { "cim_detuning",     8.0f },
    { "fx_reverb_mix",    0.35f },
    { "fx_reverb_size",   0.70f },
    { "fx_delay_mix",     0.00f },
    { "fx_comp_threshold", -15.0f },
    { "fx_comp_ratio",    3.0f },
PRESET_END

PRESET_BEGIN (preset_glass_chimes)
    { "engine",           0 },
    { "cim_material",     7 },       // Glass
    { "cim_strike_pos",   0.15f },
    { "cim_diameter",     0.40f },
    { "cim_hammer",       3 },       // Metal
    { "cim_num_strings",  5 },
    { "cim_detuning",     12.0f },
    { "fx_reverb_mix",    0.50f },
    { "fx_reverb_size",   0.80f },
    { "fx_delay_time",    400.0f },
    { "fx_delay_feedback", 0.25f },
    { "fx_delay_mix",     0.15f },
    { "fx_comp_threshold", -8.0f },
    { "fx_comp_ratio",    2.0f },
PRESET_END

PRESET_BEGIN (preset_muted_felt)
    { "engine",           0 },
    { "cim_material",     0 },       // Steel
    { "cim_strike_pos",   0.50f },
    { "cim_diameter",     1.00f },
    { "cim_hammer",       0 },       // Cotton
    { "cim_num_strings",  2 },
    { "cim_detuning",     3.0f },
    { "fx_reverb_mix",    0.15f },
    { "fx_reverb_size",   0.40f },
    { "fx_delay_mix",     0.00f },
    { "fx_comp_threshold", -10.0f },
    { "fx_comp_ratio",    3.0f },
PRESET_END

PRESET_BEGIN (preset_brass_gamelan)
    { "engine",           0 },
    { "cim_material",     4 },       // Brass
    { "cim_strike_pos",   0.12f },   // near edge — bright attack
    { "cim_diameter",     1.50f },
    { "cim_hammer",       3 },       // Metal
    { "cim_num_strings",  1 },
    { "cim_detuning",     0.0f },
    { "fx_reverb_mix",    0.40f },
    { "fx_reverb_size",   0.75f },
    { "fx_delay_mix",     0.00f },
    { "fx_comp_threshold", -6.0f },
    { "fx_comp_ratio",    5.0f },
PRESET_END

PRESET_BEGIN (preset_rubber_pluck)
    { "engine",           0 },
    { "cim_material",     8 },       // Rubber
    { "cim_strike_pos",   0.50f },   // center — fundamental emphasis
    { "cim_diameter",     0.60f },
    { "cim_hammer",       2 },       // Wood
    { "cim_num_strings",  1 },
    { "cim_detuning",     0.0f },
    { "fx_reverb_mix",    0.10f },
    { "fx_reverb_size",   0.30f },
    { "fx_delay_mix",     0.00f },
    { "fx_comp_threshold", -18.0f },
    { "fx_comp_ratio",    6.0f },
PRESET_END

// ========== Chromatic presets ==========

PRESET_BEGIN (preset_crystal_tongue)
    { "engine",           1 },
    { "chr_sub_engine",   0 },       // Tongue Drum
    { "chr_material",     3 },       // Aluminum
    { "chr_strike_pos",   0.40f },
    { "chr_thickness",    3.0f },    // mm
    { "chr_size",         25.0f },   // mm
    { "chr_exciter",      1 },       // Medium
    { "chr_pitch_glide",  0.0f },
    { "fx_reverb_mix",    0.30f },
    { "fx_reverb_size",   0.60f },
    { "fx_delay_mix",     0.00f },
PRESET_END

PRESET_BEGIN (preset_bronze_gong)
    { "engine",           1 },
    { "chr_sub_engine",   1 },       // Water Gong
    { "chr_material",     2 },       // Bronze
    { "chr_strike_pos",   0.30f },
    { "chr_thickness",    4.0f },
    { "chr_size",         40.0f },
    { "chr_exciter",      2 },       // Hard
    { "chr_pitch_glide",  0.60f },
    { "fx_reverb_mix",    0.45f },
    { "fx_reverb_size",   0.85f },
    { "fx_delay_mix",     0.00f },
PRESET_END

PRESET_BEGIN (preset_wooden_kalimba)
    { "engine",           1 },
    { "chr_sub_engine",   0 },       // Tongue Drum
    { "chr_material",     5 },       // Spruce
    { "chr_strike_pos",   0.50f },
    { "chr_thickness",    2.0f },
    { "chr_size",         15.0f },
    { "chr_exciter",      1 },       // Medium
    { "chr_pitch_glide",  0.0f },
    { "fx_reverb_mix",    0.20f },
    { "fx_reverb_size",   0.40f },
    { "fx_delay_mix",     0.00f },
PRESET_END

PRESET_BEGIN (preset_ethereal_bells)
    { "engine",           1 },
    { "chr_sub_engine",   2 },       // Custom
    { "chr_material",     0 },       // Steel
    { "chr_strike_pos",   0.25f },
    { "chr_thickness",    5.0f },
    { "chr_size",         30.0f },
    { "chr_exciter",      2 },       // Hard
    { "chr_pitch_glide",  0.0f },
    { "fx_reverb_mix",    0.55f },
    { "fx_reverb_size",   0.90f },
    { "fx_delay_time",    500.0f },
    { "fx_delay_feedback", 0.30f },
    { "fx_delay_mix",     0.20f },
PRESET_END

PRESET_BEGIN (preset_glass_singing_bowl)
    { "engine",           1 },
    { "chr_sub_engine",   1 },       // Water Gong
    { "chr_material",     7 },       // Glass
    { "chr_strike_pos",   0.50f },
    { "chr_thickness",    6.0f },
    { "chr_size",         55.0f },
    { "chr_exciter",      0 },       // Soft
    { "chr_pitch_glide",  0.35f },
    { "fx_reverb_mix",    0.60f },
    { "fx_reverb_size",   0.92f },
    { "fx_delay_time",    600.0f },
    { "fx_delay_feedback", 0.35f },
    { "fx_delay_mix",     0.18f },
PRESET_END

PRESET_BEGIN (preset_rubber_tongue_pad)
    { "engine",           1 },
    { "chr_sub_engine",   0 },       // Tongue Drum
    { "chr_material",     8 },       // Rubber
    { "chr_strike_pos",   0.45f },
    { "chr_thickness",    5.0f },
    { "chr_size",         35.0f },
    { "chr_exciter",      0 },       // Soft
    { "chr_pitch_glide",  0.0f },
    { "fx_reverb_mix",    0.35f },
    { "fx_reverb_size",   0.65f },
    { "fx_delay_time",    450.0f },
    { "fx_delay_feedback", 0.40f },
    { "fx_delay_mix",     0.22f },
PRESET_END

// ========== FM Piano presets ==========

PRESET_BEGIN (preset_acoustic_piano)
    { "engine",           2 },
    { "fm_type",          0 },       // Piano
    { "fm_ratio",         1.0f },
    { "fm_index",         4.5f },    // two-stage: 70% attack peak (fast decay) + 30% body (slow)
    { "fm_brightness",    0.77f },   // body index decay ~1.1s (attack index decays in ~45ms regardless)
    { "fm_feedback",      0.02f },   // tiny feedback → subtle odd harmonics for body character
    { "fm_attack",        5.0f },    // quick hammer
    { "fm_release",       500.0f },  // natural string ring
    { "fx_reverb_mix",    0.18f },
    { "fx_reverb_size",   0.48f },
    { "fx_delay_mix",     0.00f },
PRESET_END

PRESET_BEGIN (preset_electric_rhodes)
    { "engine",           2 },
    { "fm_type",          1 },       // E.Piano
    { "fm_ratio",         1.0f },
    { "fm_index",         3.5f },
    { "fm_brightness",    0.50f },
    { "fm_feedback",      0.05f },
    { "fm_attack",        5.0f },
    { "fm_release",       400.0f },
    { "fx_reverb_mix",    0.15f },
    { "fx_reverb_size",   0.40f },
    { "fx_delay_time",    350.0f },
    { "fx_delay_feedback", 0.30f },
    { "fx_delay_mix",     0.15f },
PRESET_END

PRESET_BEGIN (preset_dx7_bell)
    { "engine",           2 },
    { "fm_type",          3 },       // Bell
    { "fm_ratio",         7.0f },
    { "fm_index",         8.0f },
    { "fm_brightness",    0.20f },
    { "fm_feedback",      0.00f },
    { "fm_attack",        3.0f },
    { "fm_release",       1500.0f },
    { "fx_reverb_mix",    0.50f },
    { "fx_reverb_size",   0.85f },
    { "fx_delay_mix",     0.00f },
PRESET_END

PRESET_BEGIN (preset_church_organ)
    { "engine",           2 },
    { "fm_type",          4 },       // Organ
    { "fm_ratio",         1.0f },
    { "fm_index",         2.0f },
    { "fm_brightness",    0.00f },
    { "fm_feedback",      0.50f },
    { "fm_attack",        50.0f },
    { "fm_release",       200.0f },
    { "fx_reverb_mix",    0.40f },
    { "fx_reverb_size",   0.90f },
    { "fx_delay_mix",     0.00f },
PRESET_END

PRESET_BEGIN (preset_ambient_pad)
    { "engine",           2 },
    { "fm_type",          5 },       // Pad
    { "fm_ratio",         2.0f },
    { "fm_index",         3.0f },
    { "fm_brightness",    0.35f },
    { "fm_feedback",      0.30f },
    { "fm_attack",        800.0f },
    { "fm_release",       3000.0f },
    { "fx_reverb_mix",    0.55f },
    { "fx_reverb_size",   0.88f },
    { "fx_delay_time",    500.0f },
    { "fx_delay_feedback", 0.45f },
    { "fx_delay_mix",     0.25f },
PRESET_END

PRESET_BEGIN (preset_fm_vibraphone)
    { "engine",           2 },
    { "fm_type",          2 },       // Vibraphone
    { "fm_ratio",         3.0f },
    { "fm_index",         4.2f },
    { "fm_brightness",    0.35f },
    { "fm_feedback",      0.02f },
    { "fm_attack",        8.0f },
    { "fm_release",       1200.0f },
    { "fx_reverb_mix",    0.25f },
    { "fx_reverb_size",   0.55f },
    { "fx_delay_mix",     0.00f },
PRESET_END

PRESET_BEGIN (preset_fm_bass)
    { "engine",           2 },
    { "fm_type",          6 },       // Bass
    { "fm_ratio",         1.0f },
    { "fm_index",         6.0f },
    { "fm_brightness",    0.80f },
    { "fm_feedback",      0.08f },
    { "fm_attack",        3.0f },
    { "fm_release",       150.0f },
    { "fx_reverb_mix",    0.05f },
    { "fx_reverb_size",   0.20f },
    { "fx_delay_mix",     0.00f },
    { "fx_comp_threshold", -8.0f },
    { "fx_comp_ratio",    6.0f },
PRESET_END

PRESET_BEGIN (preset_fm_brass)
    { "engine",           2 },
    { "fm_type",          7 },       // Brass
    { "fm_ratio",         1.0f },
    { "fm_index",         5.8f },
    { "fm_brightness",    0.65f },
    { "fm_feedback",      0.12f },
    { "fm_attack",        35.0f },
    { "fm_release",       350.0f },
    { "fx_reverb_mix",    0.15f },
    { "fx_reverb_size",   0.40f },
    { "fx_delay_mix",     0.00f },
    { "fx_comp_threshold", -10.0f },
    { "fx_comp_ratio",    3.0f },
PRESET_END

// ========== Preset registry ==========

#define REGISTER_PRESET(var) { #var, var, (int) (sizeof(var) / sizeof(var[0])) }

inline const FactoryPreset* getFactoryPresetList (int& count)
{
    static const FactoryPreset presets[] =
    {
        // Cimbalom (0-5)
        { "Steel Hammered Dulcimer",  preset_steel_dulcimer,      (int)(sizeof(preset_steel_dulcimer)/sizeof(preset_steel_dulcimer[0]))          },
        { "Copper Warm Strings",      preset_copper_warm,         (int)(sizeof(preset_copper_warm)/sizeof(preset_copper_warm[0]))                },
        { "Glass Wind Chimes",        preset_glass_chimes,        (int)(sizeof(preset_glass_chimes)/sizeof(preset_glass_chimes[0]))              },
        { "Muted Felt Piano",         preset_muted_felt,          (int)(sizeof(preset_muted_felt)/sizeof(preset_muted_felt[0]))                  },
        { "Brass Gamelan",            preset_brass_gamelan,       (int)(sizeof(preset_brass_gamelan)/sizeof(preset_brass_gamelan[0]))             },
        { "Rubber Muted Pluck",       preset_rubber_pluck,        (int)(sizeof(preset_rubber_pluck)/sizeof(preset_rubber_pluck[0]))              },
        // Chromatic (6-11)
        { "Crystal Tongue Drum",      preset_crystal_tongue,      (int)(sizeof(preset_crystal_tongue)/sizeof(preset_crystal_tongue[0]))          },
        { "Bronze Water Gong",        preset_bronze_gong,         (int)(sizeof(preset_bronze_gong)/sizeof(preset_bronze_gong[0]))                },
        { "Wooden Kalimba",           preset_wooden_kalimba,      (int)(sizeof(preset_wooden_kalimba)/sizeof(preset_wooden_kalimba[0]))          },
        { "Ethereal Steel Bells",     preset_ethereal_bells,      (int)(sizeof(preset_ethereal_bells)/sizeof(preset_ethereal_bells[0]))          },
        { "Glass Singing Bowl",       preset_glass_singing_bowl,  (int)(sizeof(preset_glass_singing_bowl)/sizeof(preset_glass_singing_bowl[0]))  },
        { "Rubber Tongue Pad",        preset_rubber_tongue_pad,   (int)(sizeof(preset_rubber_tongue_pad)/sizeof(preset_rubber_tongue_pad[0]))    },
        // FM Piano (12-19) — one preset per sound type
        { "Acoustic Piano",           preset_acoustic_piano,      (int)(sizeof(preset_acoustic_piano)/sizeof(preset_acoustic_piano[0]))          },
        { "Electric Rhodes",          preset_electric_rhodes,     (int)(sizeof(preset_electric_rhodes)/sizeof(preset_electric_rhodes[0]))         },
        { "FM Vibraphone",            preset_fm_vibraphone,       (int)(sizeof(preset_fm_vibraphone)/sizeof(preset_fm_vibraphone[0]))             },
        { "DX7 Crystal Bell",         preset_dx7_bell,            (int)(sizeof(preset_dx7_bell)/sizeof(preset_dx7_bell[0]))                      },
        { "Church Organ",             preset_church_organ,        (int)(sizeof(preset_church_organ)/sizeof(preset_church_organ[0]))               },
        { "Ambient Pad",              preset_ambient_pad,         (int)(sizeof(preset_ambient_pad)/sizeof(preset_ambient_pad[0]))                 },
        { "FM Bass",                  preset_fm_bass,             (int)(sizeof(preset_fm_bass)/sizeof(preset_fm_bass[0]))                         },
        { "FM Brass",                 preset_fm_brass,            (int)(sizeof(preset_fm_brass)/sizeof(preset_fm_brass[0]))                       },
    };

    count = (int) (sizeof (presets) / sizeof (presets[0]));
    return presets;
}
