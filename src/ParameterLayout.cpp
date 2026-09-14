#include "ParameterLayout.h"

// == Parameter Layout (grouped for DAW automation lanes) ==
// WF0908-E10b: moved verbatim out of PluginProcessor.cpp (formerly
// TsukiSynthProcessor::createParameterLayout(), a private static member) --
// see src/ParameterLayout.h for why. No parameter id, range, or default was
// changed by this move.
juce::AudioProcessorValueTreeState::ParameterLayout createTsukiParameterLayout()
{
    // A12 (2026-08-22, 月月裁決選 (a)): every float parameter is CONTINUOUS
    // (interval 0). The former 0.01/0.1/1.0 steps made setValue (no snap)
    // and state save/restore (snap) disagree by up to half a step, so a DAW
    // project reload rendered differently from the pre-save live state
    // (HostProbe H5 catch, reports/gate_outputs/l1_l2_l3a_melody_gate.txt).
    // With interval 0 the normalised<->plain mapping is lossless both ways
    // and the state round-trip is bit-exact. CLI rendering never reads
    // APVTS, so corpus output is untouched (Rule 10 not triggered).
    using FloatParam  = juce::AudioParameterFloat;
    using ChoiceParam = juce::AudioParameterChoice;
    using IntParam    = juce::AudioParameterInt;
    using Group       = juce::AudioProcessorParameterGroup;
    using Range       = juce::NormalisableRange<float>;
    using PID         = juce::ParameterID;

    auto global = std::make_unique<Group> ("global", "Global", "|");
    global->addChild (std::make_unique<ChoiceParam> (
        PID { "engine", 1 }, "Engine",
        juce::StringArray { "Cimbalom", "Chromatic", "FM Piano", "Piano" }, 0));

    auto macro = std::make_unique<Group> ("macro", "Macro", "|");
    macro->addChild (std::make_unique<FloatParam> (
        PID { "macro_material", 1 }, "Material",
        Range (0.0f, 1.0f, 0.0f), 0.5f));
    macro->addChild (std::make_unique<FloatParam> (
        PID { "macro_tension", 1 }, "Tension",
        Range (0.0f, 1.0f, 0.0f), 0.5f));
    macro->addChild (std::make_unique<FloatParam> (
        PID { "macro_damping", 1 }, "Damping",
        Range (0.0f, 1.0f, 0.0f), 0.5f));
    macro->addChild (std::make_unique<FloatParam> (
        PID { "macro_strike", 1 }, "Strike",
        Range (0.0f, 1.0f, 0.0f), 0.5f));
    macro->addChild (std::make_unique<FloatParam> (
        PID { "macro_brightness", 1 }, "Brightness",
        Range (0.0f, 1.0f, 0.0f), 0.5f));
    macro->addChild (std::make_unique<FloatParam> (
        PID { "macro_body", 1 }, "Body",
        Range (0.0f, 1.0f, 0.0f), 0.5f));
    macro->addChild (std::make_unique<FloatParam> (
        PID { "macro_noise", 1 }, "Noise",
        Range (0.0f, 1.0f, 0.0f), 0.0f));
    macro->addChild (std::make_unique<FloatParam> (
        PID { "macro_output", 1 }, "Output",
        Range (0.0f, 1.0f, 0.0f), 1.0f));

    auto cim = std::make_unique<Group> ("cimbalom", "Cimbalom", "|");
    cim->addChild (std::make_unique<ChoiceParam> (
        PID { "cim_material", 1 }, "Material",
        juce::StringArray { "Steel", "Copper", "Bronze", "Aluminum", "Brass",
                            "Spruce", "Maple", "Glass", "Rubber" }, 0));
    cim->addChild (std::make_unique<ChoiceParam> (
        PID { "cim_hammer", 1 }, "Hammer",
        juce::StringArray { "Cotton", "Felt", "Wood", "Metal" }, 2));
    cim->addChild (std::make_unique<FloatParam> (
        PID { "cim_strike_pos", 1 }, "Strike Position",
        Range (0.05f, 0.95f, 0.0f), 0.3f));
    cim->addChild (std::make_unique<FloatParam> (
        PID { "cim_diameter", 1 }, "String Diameter (mm)",
        Range (0.3f, 2.0f, 0.0f), 0.8f));
    cim->addChild (std::make_unique<IntParam> (
        PID { "cim_num_strings", 1 }, "Strings / Course", 1, 5, 3));
    cim->addChild (std::make_unique<FloatParam> (
        PID { "cim_detuning", 1 }, "Detuning (cents)",
        Range (0.0f, 15.0f, 0.0f), 5.0f));

    auto chr = std::make_unique<Group> ("chromatic", "Chromatic", "|");
    chr->addChild (std::make_unique<ChoiceParam> (
        PID { "chr_sub_engine", 1 }, "Sub-Engine",
        juce::StringArray { "Tongue Drum", "Water Gong", "Custom" }, 0));
    chr->addChild (std::make_unique<ChoiceParam> (
        PID { "chr_material", 1 }, "Material",
        juce::StringArray { "Steel", "Copper", "Bronze", "Aluminum", "Brass",
                            "Spruce", "Maple", "Glass", "Rubber" }, 0));
    chr->addChild (std::make_unique<ChoiceParam> (
        PID { "chr_exciter", 1 }, "Exciter",
        juce::StringArray { "Soft", "Medium", "Hard", "Sharp" }, 1));
    chr->addChild (std::make_unique<FloatParam> (
        PID { "chr_strike_pos", 1 }, "Strike Position",
        Range (0.0f, 1.0f, 0.0f), 0.35f));
    chr->addChild (std::make_unique<FloatParam> (
        PID { "chr_thickness", 1 }, "Thickness (mm)",
        Range (0.5f, 10.0f, 0.0f), 3.0f));
    chr->addChild (std::make_unique<FloatParam> (
        PID { "chr_size", 1 }, "Size (mm)",
        Range (10.0f, 100.0f, 0.0f), 20.0f));
    chr->addChild (std::make_unique<FloatParam> (
        PID { "chr_pitch_glide", 1 }, "Pitch Glide",
        Range (0.0f, 1.0f, 0.0f), 0.0f));

    {
        static constexpr float defRatios[] = { 1.0f, 2.0f, 3.0f, 4.16f, 5.43f, 6.98f, 8.21f, 10.0f };
        static constexpr float defAmps[]   = { 1.0f, 0.7f, 0.5f, 0.35f, 0.25f, 0.18f, 0.12f, 0.08f };
        for (int i = 0; i < 8; ++i)
        {
            chr->addChild (std::make_unique<FloatParam> (
                PID { "chr_ratio_" + juce::String (i), 1 },
                "Harmonic " + juce::String (i + 1) + " Ratio",
                Range (0.25f, 20.0f, 0.0f, 0.4f), defRatios[i]));
            chr->addChild (std::make_unique<FloatParam> (
                PID { "chr_amp_" + juce::String (i), 1 },
                "Harmonic " + juce::String (i + 1) + " Amp",
                Range (0.0f, 1.0f, 0.0f), defAmps[i]));
        }
    }

    auto fm = std::make_unique<Group> ("fm", "FM Piano", "|");
    fm->addChild (std::make_unique<ChoiceParam> (
        PID { "fm_type", 1 }, "Sound Type",
        juce::StringArray { "Piano", "E.Piano", "Vibraphone", "Bell",
                            "Organ", "Pad", "Bass", "Brass" }, 0));
    fm->addChild (std::make_unique<FloatParam> (
        PID { "fm_ratio", 1 }, "FM Ratio",
        Range (0.5f, 16.0f, 0.0f, 0.4f), 1.0f));           // Piano: 1:1
    fm->addChild (std::make_unique<FloatParam> (
        PID { "fm_index", 1 }, "Mod Index",
        Range (0.0f, 25.0f, 0.0f), 4.5f));                   // was 5.0 → Acoustic Piano direction
    fm->addChild (std::make_unique<FloatParam> (
        PID { "fm_brightness", 1 }, "Tone Decay",
        Range (0.0f, 1.0f, 0.0f), 0.6f));                   // label: body modulation decay speed
    fm->addChild (std::make_unique<FloatParam> (
        PID { "fm_feedback", 1 }, "Feedback",
        Range (0.0f, 1.0f, 0.0f), 0.02f));                  // was 0.0 → subtle odd harmonics
    fm->addChild (std::make_unique<FloatParam> (
        PID { "fm_attack", 1 }, "FM Attack (ms)",
        Range (1.0f, 2000.0f, 0.0f, 0.4f), 5.0f));           // was 10 → quick hammer
    fm->addChild (std::make_unique<FloatParam> (
        PID { "fm_release", 1 }, "FM Release (ms)",
        Range (10.0f, 5000.0f, 0.0f, 0.4f), 500.0f));

    auto rev = std::make_unique<Group> ("reverb", "Reverb", "|");
    rev->addChild (std::make_unique<FloatParam> (
        PID { "fx_reverb_mix", 1 }, "Reverb Mix",
        Range (0.0f, 1.0f, 0.0f), 0.2f));
    rev->addChild (std::make_unique<FloatParam> (
        PID { "fx_reverb_size", 1 }, "Room Size",
        Range (0.0f, 1.0f, 0.0f), 0.5f));
    // Authored T60 in seconds; below 0.01 the room-size knob stays in
    // control. Range mirrors the score schema's reverb.decay [0, 30].
    rev->addChild (std::make_unique<FloatParam> (
        PID { "fx_reverb_decay", 1 }, "Reverb T60 (s)",
        Range (0.0f, 30.0f, 0.0f, 0.35f), 0.0f));
    rev->addChild (std::make_unique<ChoiceParam> (
        PID { "fx_reverb_mode", 1 }, "Reverb Mode",
        juce::StringArray { "Algorithmic", "Impulse Response" }, 0));

    auto dly = std::make_unique<Group> ("delay", "Delay", "|");
    dly->addChild (std::make_unique<FloatParam> (
        PID { "fx_delay_time", 1 }, "Delay Time (ms)",
        Range (50.0f, 2000.0f, 0.0f, 0.4f), 300.0f));
    dly->addChild (std::make_unique<FloatParam> (
        PID { "fx_delay_feedback", 1 }, "Delay Feedback",
        Range (0.0f, 0.95f, 0.0f), 0.3f));
    dly->addChild (std::make_unique<FloatParam> (
        PID { "fx_delay_mix", 1 }, "Delay Mix",
        Range (0.0f, 1.0f, 0.0f), 0.0f));

    auto comp = std::make_unique<Group> ("comp", "Compressor", "|");
    comp->addChild (std::make_unique<FloatParam> (
        PID { "fx_comp_threshold", 1 }, "Threshold (dB)",
        Range (-40.0f, 0.0f, 0.0f), -12.0f));
    comp->addChild (std::make_unique<FloatParam> (
        PID { "fx_comp_ratio", 1 }, "Ratio",
        Range (1.0f, 20.0f, 0.0f, 0.5f), 4.0f));

    auto dist = std::make_unique<Group> ("dist", "Distortion", "|");
    dist->addChild (std::make_unique<ChoiceParam> (
        PID { "fx_dist_type", 1 }, "Type",
        juce::StringArray { "Overdrive", "Bitcrush", "Wavefold" }, 0));
    dist->addChild (std::make_unique<FloatParam> (
        PID { "fx_dist_drive", 1 }, "Drive",
        Range (0.0f, 1.0f, 0.0f), 0.0f));
    dist->addChild (std::make_unique<FloatParam> (
        PID { "fx_dist_instability", 1 }, "Instability",
        Range (0.0f, 1.0f, 0.0f), 0.0f));
    dist->addChild (std::make_unique<FloatParam> (
        PID { "fx_dist_mix", 1 }, "Mix",
        Range (0.0f, 1.0f, 0.0f), 0.5f));

    // Brightness-compensation high shelf (documented creative layer,
    // 2026-08-06 月月 ruling) -- gain 0 dB bypasses the filter entirely.
    auto eqg = std::make_unique<Group> ("eqfx", "EQ", "|");
    eqg->addChild (std::make_unique<FloatParam> (
        PID { "fx_eq_freq", 1 }, "EQ Shelf Freq (Hz)",
        Range (100.0f, 16000.0f, 0.0f, 0.3f), 2000.0f));
    eqg->addChild (std::make_unique<FloatParam> (
        PID { "fx_eq_gain", 1 }, "EQ Shelf Gain (dB)",
        Range (-24.0f, 24.0f, 0.0f), 0.0f));

    juce::AudioProcessorValueTreeState::ParameterLayout layout;
    layout.add (std::move (global), std::move (macro), std::move (cim),
                std::move (chr), std::move (fm), std::move (rev),
                std::move (dly), std::move (comp), std::move (dist),
                std::move (eqg));
    return layout;
}
