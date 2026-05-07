#include "PluginProcessor.h"
#include "PluginEditor.h"
#include "engines/CimbalomEngine.h"
#include "BinaryData.h"

// ── Parameter Layout ──
juce::AudioProcessorValueTreeState::ParameterLayout
TsukiSynthProcessor::createParameterLayout()
{
    std::vector<std::unique_ptr<juce::RangedAudioParameter>> params;

    // 材質選擇
    params.push_back (std::make_unique<juce::AudioParameterChoice> (
        juce::ParameterID { "cim_material", 1 },
        "Material",
        juce::StringArray {
            "Steel", "Copper", "Bronze", "Aluminum", "Brass",
            "Spruce", "Maple", "Glass", "Rubber" },
        0));  // default: Steel

    // 擊打位置
    params.push_back (std::make_unique<juce::AudioParameterFloat> (
        juce::ParameterID { "cim_strike_pos", 1 },
        "Strike Position",
        juce::NormalisableRange<float> (0.05f, 0.95f, 0.01f),
        0.3f));

    // 弦徑 (mm)
    params.push_back (std::make_unique<juce::AudioParameterFloat> (
        juce::ParameterID { "cim_diameter", 1 },
        "String Diameter (mm)",
        juce::NormalisableRange<float> (0.3f, 2.0f, 0.01f),
        0.8f));

    // 槌硬度
    params.push_back (std::make_unique<juce::AudioParameterChoice> (
        juce::ParameterID { "cim_hammer", 1 },
        "Hammer",
        juce::StringArray { "Cotton", "Felt", "Wood", "Metal" },
        2));  // default: Wood

    // 弦數 (per course)
    params.push_back (std::make_unique<juce::AudioParameterInt> (
        juce::ParameterID { "cim_num_strings", 1 },
        "Strings / Course",
        1, 5, 3));

    // 失諧量 (cents)
    params.push_back (std::make_unique<juce::AudioParameterFloat> (
        juce::ParameterID { "cim_detuning", 1 },
        "Detuning (cents)",
        juce::NormalisableRange<float> (0.0f, 15.0f, 0.1f),
        5.0f));

    return { params.begin(), params.end() };
}

// ── Constructor ──
TsukiSynthProcessor::TsukiSynthProcessor()
    : AudioProcessor (BusesProperties()
                        .withOutput ("Output", juce::AudioChannelSet::stereo(), true)),
      apvts (*this, nullptr, "PARAMETERS", createParameterLayout())
{
    // 載入材質數據庫
    materialDB.loadFromBinary (BinaryData::materials_json,
                               BinaryData::materials_jsonSize);

    // 取得參數 raw pointer
    auto* pMaterial  = apvts.getRawParameterValue ("cim_material");
    auto* pStrike    = apvts.getRawParameterValue ("cim_strike_pos");
    auto* pDiameter  = apvts.getRawParameterValue ("cim_diameter");
    auto* pHammer    = apvts.getRawParameterValue ("cim_hammer");
    auto* pNStrings  = apvts.getRawParameterValue ("cim_num_strings");
    auto* pDetuning  = apvts.getRawParameterValue ("cim_detuning");

    // 建立 Cimbalom 引擎
    synth.addSound (new CimbalomSound());

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
        synth.addVoice (voice);
    }
}

TsukiSynthProcessor::~TsukiSynthProcessor() {}

// ── Audio ──
void TsukiSynthProcessor::prepareToPlay (double sampleRate, int)
{
    synth.setCurrentPlaybackSampleRate (sampleRate);
}

void TsukiSynthProcessor::releaseResources() {}

void TsukiSynthProcessor::processBlock (juce::AudioBuffer<float>& buffer,
                                        juce::MidiBuffer& midiMessages)
{
    juce::ScopedNoDenormals noDenormals;
    buffer.clear();
    synth.renderNextBlock (buffer, midiMessages, 0, buffer.getNumSamples());
}

// ── State ──
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

// ── Editor ──
juce::AudioProcessorEditor* TsukiSynthProcessor::createEditor()
{
    return new TsukiSynthEditor (*this);
}

// ── Factory ──
juce::AudioProcessor* JUCE_CALLTYPE createPluginFilter()
{
    return new TsukiSynthProcessor();
}
