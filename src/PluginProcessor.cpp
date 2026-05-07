#include "PluginProcessor.h"
#include "PluginEditor.h"
#include "engines/CimbalomEngine.h"
#include "engines/ChromaticEngine.h"
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
        juce::StringArray { "Cimbalom", "Chromatic" },
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
}

TsukiSynthProcessor::~TsukiSynthProcessor() {}

// == Audio ==
void TsukiSynthProcessor::prepareToPlay (double sampleRate, int)
{
    cimbalomSynth.setCurrentPlaybackSampleRate (sampleRate);
    chromaticSynth.setCurrentPlaybackSampleRate (sampleRate);
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
        lastEngine = currentEngine;
    }

    if (currentEngine == 0)
        cimbalomSynth.renderNextBlock (buffer, midiMessages,
                                       0, buffer.getNumSamples());
    else
        chromaticSynth.renderNextBlock (buffer, midiMessages,
                                        0, buffer.getNumSamples());
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
