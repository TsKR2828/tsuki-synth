#include "PluginProcessor.h"
#include "PluginEditor.h"
#include "engines/CimbalomEngine.h"
#include "engines/ChromaticEngine.h"
#include "engines/FMPianoEngine.h"
#include "Presets.h"
#include "BinaryData.h"

// == Parameter Layout ==
juce::AudioProcessorValueTreeState::ParameterLayout
TsukiSynthProcessor::createParameterLayout()
{
    std::vector<std::unique_ptr<juce::RangedAudioParameter>> params;

    // ---- Global ----
    params.push_back (std::make_unique<juce::AudioParameterChoice> (
        juce::ParameterID { "engine", 1 },
        "Engine",
        juce::StringArray { "Cimbalom", "Chromatic", "FM Piano" },
        0));

    // ---- Cimbalom parameters ----
    params.push_back (std::make_unique<juce::AudioParameterChoice> (
        juce::ParameterID { "cim_material", 1 },
        "Material",
        juce::StringArray {
            "Steel", "Copper", "Bronze", "Aluminum", "Brass",
            "Spruce", "Maple", "Glass", "Rubber" },
        0));

    params.push_back (std::make_unique<juce::AudioParameterFloat> (
        juce::ParameterID { "cim_strike_pos", 1 },
        "Strike Position",
        juce::NormalisableRange<float> (0.05f, 0.95f, 0.01f),
        0.3f));

    params.push_back (std::make_unique<juce::AudioParameterFloat> (
        juce::ParameterID { "cim_diameter", 1 },
        "String Diameter (mm)",
        juce::NormalisableRange<float> (0.3f, 2.0f, 0.01f),
        0.8f));

    params.push_back (std::make_unique<juce::AudioParameterChoice> (
        juce::ParameterID { "cim_hammer", 1 },
        "Hammer",
        juce::StringArray { "Cotton", "Felt", "Wood", "Metal" },
        2));

    params.push_back (std::make_unique<juce::AudioParameterInt> (
        juce::ParameterID { "cim_num_strings", 1 },
        "Strings / Course",
        1, 5, 3));

    params.push_back (std::make_unique<juce::AudioParameterFloat> (
        juce::ParameterID { "cim_detuning", 1 },
        "Detuning (cents)",
        juce::NormalisableRange<float> (0.0f, 15.0f, 0.1f),
        5.0f));

    // ---- Chromatic parameters ----
    params.push_back (std::make_unique<juce::AudioParameterChoice> (
        juce::ParameterID { "chr_sub_engine", 1 },
        "Sub-Engine",
        juce::StringArray { "Tongue Drum", "Water Gong", "Custom" },
        0));

    params.push_back (std::make_unique<juce::AudioParameterChoice> (
        juce::ParameterID { "chr_material", 1 },
        "Chr Material",
        juce::StringArray {
            "Steel", "Copper", "Bronze", "Aluminum", "Brass",
            "Spruce", "Maple", "Glass", "Rubber" },
        0));

    params.push_back (std::make_unique<juce::AudioParameterFloat> (
        juce::ParameterID { "chr_strike_pos", 1 },
        "Chr Strike Position",
        juce::NormalisableRange<float> (0.0f, 1.0f, 0.01f),
        0.35f));

    params.push_back (std::make_unique<juce::AudioParameterFloat> (
        juce::ParameterID { "chr_thickness", 1 },
        "Thickness (mm)",
        juce::NormalisableRange<float> (0.5f, 10.0f, 0.1f),
        3.0f));

    params.push_back (std::make_unique<juce::AudioParameterFloat> (
        juce::ParameterID { "chr_size", 1 },
        "Size (mm)",
        juce::NormalisableRange<float> (10.0f, 100.0f, 1.0f),
        20.0f));

    params.push_back (std::make_unique<juce::AudioParameterChoice> (
        juce::ParameterID { "chr_exciter", 1 },
        "Exciter",
        juce::StringArray { "Soft", "Medium", "Hard", "Sharp" },
        1));

    params.push_back (std::make_unique<juce::AudioParameterFloat> (
        juce::ParameterID { "chr_pitch_glide", 1 },
        "Pitch Glide",
        juce::NormalisableRange<float> (0.0f, 1.0f, 0.01f),
        0.0f));

    // ---- FM Piano parameters ----
    params.push_back (std::make_unique<juce::AudioParameterChoice> (
        juce::ParameterID { "fm_type", 1 },
        "Sound Type",
        juce::StringArray { "Piano", "E.Piano", "Vibraphone", "Bell",
                            "Organ", "Pad", "Bass", "Brass" },
        0));

    params.push_back (std::make_unique<juce::AudioParameterFloat> (
        juce::ParameterID { "fm_ratio", 1 },
        "FM Ratio",
        juce::NormalisableRange<float> (0.5f, 16.0f, 0.01f, 0.4f),
        1.0f));

    params.push_back (std::make_unique<juce::AudioParameterFloat> (
        juce::ParameterID { "fm_index", 1 },
        "Mod Index",
        juce::NormalisableRange<float> (0.0f, 25.0f, 0.1f),
        5.0f));

    params.push_back (std::make_unique<juce::AudioParameterFloat> (
        juce::ParameterID { "fm_brightness", 1 },
        "Brightness",
        juce::NormalisableRange<float> (0.0f, 1.0f, 0.01f),
        0.6f));

    params.push_back (std::make_unique<juce::AudioParameterFloat> (
        juce::ParameterID { "fm_feedback", 1 },
        "Feedback",
        juce::NormalisableRange<float> (0.0f, 1.0f, 0.01f),
        0.0f));

    params.push_back (std::make_unique<juce::AudioParameterFloat> (
        juce::ParameterID { "fm_attack", 1 },
        "FM Attack (ms)",
        juce::NormalisableRange<float> (1.0f, 2000.0f, 1.0f, 0.4f),
        10.0f));

    params.push_back (std::make_unique<juce::AudioParameterFloat> (
        juce::ParameterID { "fm_release", 1 },
        "FM Release (ms)",
        juce::NormalisableRange<float> (10.0f, 5000.0f, 1.0f, 0.4f),
        300.0f));

    // ---- Effect chain parameters ----
    params.push_back (std::make_unique<juce::AudioParameterFloat> (
        juce::ParameterID { "fx_reverb_mix", 1 },
        "Reverb Mix",
        juce::NormalisableRange<float> (0.0f, 1.0f, 0.01f),
        0.2f));

    params.push_back (std::make_unique<juce::AudioParameterFloat> (
        juce::ParameterID { "fx_reverb_size", 1 },
        "Room Size",
        juce::NormalisableRange<float> (0.0f, 1.0f, 0.01f),
        0.5f));

    params.push_back (std::make_unique<juce::AudioParameterFloat> (
        juce::ParameterID { "fx_delay_time", 1 },
        "Delay Time (ms)",
        juce::NormalisableRange<float> (50.0f, 2000.0f, 1.0f, 0.4f),
        300.0f));

    params.push_back (std::make_unique<juce::AudioParameterFloat> (
        juce::ParameterID { "fx_delay_feedback", 1 },
        "Delay Feedback",
        juce::NormalisableRange<float> (0.0f, 0.95f, 0.01f),
        0.3f));

    params.push_back (std::make_unique<juce::AudioParameterFloat> (
        juce::ParameterID { "fx_delay_mix", 1 },
        "Delay Mix",
        juce::NormalisableRange<float> (0.0f, 1.0f, 0.01f),
        0.0f));

    params.push_back (std::make_unique<juce::AudioParameterFloat> (
        juce::ParameterID { "fx_comp_threshold", 1 },
        "Comp Threshold (dB)",
        juce::NormalisableRange<float> (-40.0f, 0.0f, 0.1f),
        -12.0f));

    params.push_back (std::make_unique<juce::AudioParameterFloat> (
        juce::ParameterID { "fx_comp_ratio", 1 },
        "Comp Ratio",
        juce::NormalisableRange<float> (1.0f, 20.0f, 0.1f, 0.5f),
        4.0f));

    return { params.begin(), params.end() };
}

// == Constructor ==
TsukiSynthProcessor::TsukiSynthProcessor()
    : AudioProcessor (BusesProperties()
                        .withOutput ("Output", juce::AudioChannelSet::stereo(), true)),
      apvts (*this, nullptr, "PARAMETERS", createParameterLayout())
{
    // Load material database
    materialDB.loadFromBinary (BinaryData::materials_json,
                               BinaryData::materials_jsonSize);

    // Global engine selector
    pEngine = apvts.getRawParameterValue ("engine");

    // ---- Cimbalom engine ----
    {
        auto* pMaterial  = apvts.getRawParameterValue ("cim_material");
        auto* pStrike    = apvts.getRawParameterValue ("cim_strike_pos");
        auto* pDiameter  = apvts.getRawParameterValue ("cim_diameter");
        auto* pHammer    = apvts.getRawParameterValue ("cim_hammer");
        auto* pNStrings  = apvts.getRawParameterValue ("cim_num_strings");
        auto* pDetuning  = apvts.getRawParameterValue ("cim_detuning");

        cimbalomSynth.addSound (new CimbalomSound());

        for (int i = 0; i < 16; ++i)
        {
            auto* voice = new CimbalomVoice();
            voice->setMaterialDB (&materialDB);
            voice->pMaterial       = pMaterial;
            voice->pStrikePos      = pStrike;
            voice->pDiameter       = pDiameter;
            voice->pHammerHardness = pHammer;
            voice->pNumStrings     = pNStrings;
            voice->pDetuning       = pDetuning;
            cimbalomSynth.addVoice (voice);
        }
    }

    // ---- Chromatic engine ----
    {
        auto* pSubEngine  = apvts.getRawParameterValue ("chr_sub_engine");
        auto* pMaterial   = apvts.getRawParameterValue ("chr_material");
        auto* pStrike     = apvts.getRawParameterValue ("chr_strike_pos");
        auto* pThickness  = apvts.getRawParameterValue ("chr_thickness");
        auto* pSize       = apvts.getRawParameterValue ("chr_size");
        auto* pExciter    = apvts.getRawParameterValue ("chr_exciter");
        auto* pPitchGlide = apvts.getRawParameterValue ("chr_pitch_glide");

        chromaticSynth.addSound (new ChromaticSound());

        for (int i = 0; i < 16; ++i)
        {
            auto* voice = new ChromaticVoice();
            voice->setMaterialDB (&materialDB);
            voice->pSubEngine  = pSubEngine;
            voice->pMaterial   = pMaterial;
            voice->pStrikePos  = pStrike;
            voice->pThickness  = pThickness;
            voice->pSize       = pSize;
            voice->pExciter    = pExciter;
            voice->pPitchGlide = pPitchGlide;
            chromaticSynth.addVoice (voice);
        }
    }

    // ---- FM Piano engine ----
    {
        auto* pType       = apvts.getRawParameterValue ("fm_type");
        auto* pRatio      = apvts.getRawParameterValue ("fm_ratio");
        auto* pIndex      = apvts.getRawParameterValue ("fm_index");
        auto* pBrightness = apvts.getRawParameterValue ("fm_brightness");
        auto* pFeedback   = apvts.getRawParameterValue ("fm_feedback");
        auto* pAttack     = apvts.getRawParameterValue ("fm_attack");
        auto* pRelease    = apvts.getRawParameterValue ("fm_release");

        fmPianoSynth.addSound (new FMPianoSound());

        for (int i = 0; i < 16; ++i)
        {
            auto* voice = new FMPianoVoice();
            voice->pType       = pType;
            voice->pRatio      = pRatio;
            voice->pIndex      = pIndex;
            voice->pBrightness = pBrightness;
            voice->pFeedback   = pFeedback;
            voice->pAttack     = pAttack;
            voice->pRelease    = pRelease;
            fmPianoSynth.addVoice (voice);
        }
    }

    // ---- Effect chain ----
    effectChain.pReverbMix     = apvts.getRawParameterValue ("fx_reverb_mix");
    effectChain.pReverbSize    = apvts.getRawParameterValue ("fx_reverb_size");
    effectChain.pDelayTime     = apvts.getRawParameterValue ("fx_delay_time");
    effectChain.pDelayFeedback = apvts.getRawParameterValue ("fx_delay_feedback");
    effectChain.pDelayMix      = apvts.getRawParameterValue ("fx_delay_mix");
    effectChain.pCompThreshold = apvts.getRawParameterValue ("fx_comp_threshold");
    effectChain.pCompRatio     = apvts.getRawParameterValue ("fx_comp_ratio");
}

TsukiSynthProcessor::~TsukiSynthProcessor() {}

// == Audio ==
void TsukiSynthProcessor::prepareToPlay (double sampleRate, int)
{
    cimbalomSynth.setCurrentPlaybackSampleRate (sampleRate);
    chromaticSynth.setCurrentPlaybackSampleRate (sampleRate);
    fmPianoSynth.setCurrentPlaybackSampleRate (sampleRate);
    effectChain.prepare (sampleRate);
}

void TsukiSynthProcessor::releaseResources() {}

void TsukiSynthProcessor::processBlock (juce::AudioBuffer<float>& buffer,
                                        juce::MidiBuffer& midiMessages)
{
    juce::ScopedNoDenormals noDenormals;
    buffer.clear();

    int currentEngine = (int) pEngine->load();

    // Handle engine switch: kill notes on the old engine
    if (currentEngine != lastEngine)
    {
        if (lastEngine == 0)
            cimbalomSynth.allNotesOff (0, false);
        else if (lastEngine == 1)
            chromaticSynth.allNotesOff (0, false);
        else if (lastEngine == 2)
            fmPianoSynth.allNotesOff (0, false);
        lastEngine = currentEngine;
    }

    if (currentEngine == 0)
        cimbalomSynth.renderNextBlock (buffer, midiMessages,
                                       0, buffer.getNumSamples());
    else if (currentEngine == 1)
        chromaticSynth.renderNextBlock (buffer, midiMessages,
                                        0, buffer.getNumSamples());
    else
        fmPianoSynth.renderNextBlock (buffer, midiMessages,
                                      0, buffer.getNumSamples());

    // Global effect chain: Compressor → Delay → Reverb
    effectChain.processBlock (buffer);
}

// == State ==
void TsukiSynthProcessor::getStateInformation (juce::MemoryBlock& destData)
{
    auto state = apvts.copyState();
    auto xml = state.createXml();
    copyXmlToBinary (*xml, destData);
}

void TsukiSynthProcessor::setStateInformation (const void* data, int sizeInBytes)
{
    auto xml = getXmlFromBinary (data, sizeInBytes);
    if (xml != nullptr && xml->hasTagName (apvts.state.getType()))
        apvts.replaceState (juce::ValueTree::fromXml (*xml));
}

// == Programs (Factory Presets) ==
int TsukiSynthProcessor::getNumPrograms()
{
    int count = 0;
    getFactoryPresetList (count);
    return count;
}

int TsukiSynthProcessor::getCurrentProgram()
{
    return currentProgram;
}

void TsukiSynthProcessor::setCurrentProgram (int index)
{
    int count = 0;
    auto* presets = getFactoryPresetList (count);

    if (index < 0 || index >= count)
        return;

    currentProgram = index;
    const auto& preset = presets[index];

    for (int i = 0; i < preset.numParams; ++i)
    {
        const auto& entry = preset.params[i];
        if (auto* param = apvts.getParameter (entry.paramID))
        {
            float normalized = param->convertTo0to1 (entry.rawValue);
            param->setValueNotifyingHost (normalized);
        }
    }
}

const juce::String TsukiSynthProcessor::getProgramName (int index)
{
    int count = 0;
    auto* presets = getFactoryPresetList (count);

    if (index >= 0 && index < count)
        return presets[index].name;

    return {};
}

// == Editor ==
juce::AudioProcessorEditor* TsukiSynthProcessor::createEditor()
{
    return new TsukiSynthEditor (*this);
}

// == Factory ==
juce::AudioProcessor* JUCE_CALLTYPE createPluginFilter()
{
    return new TsukiSynthProcessor();
}
