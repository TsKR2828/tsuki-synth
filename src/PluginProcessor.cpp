#include "PluginProcessor.h"
#include "PluginEditor.h"
#include "BinaryData.h"

TsukiSynthProcessor::TsukiSynthProcessor()
    : AudioProcessor (BusesProperties()
                          .withOutput ("Output",
                                       juce::AudioChannelSet::stereo(), true))
{
    materialDB.loadFromString (juce::String::fromUTF8 (
        BinaryData::materials_json, static_cast<int> (BinaryData::materials_jsonSize)));

    synth.addSound (new MultiSound());

    for (int i = 0; i < numVoices; ++i)
        synth.addVoice (new MultiVoice());

    updateVoiceParams();
}

TsukiSynthProcessor::~TsukiSynthProcessor() {}

const juce::String TsukiSynthProcessor::getName() const { return JucePlugin_Name; }
bool TsukiSynthProcessor::acceptsMidi() const  { return true; }
bool TsukiSynthProcessor::producesMidi() const { return false; }
bool TsukiSynthProcessor::isMidiEffect() const { return false; }
double TsukiSynthProcessor::getTailLengthSeconds() const { return 3.0; }

int TsukiSynthProcessor::getNumPrograms()                    { return 1; }
int TsukiSynthProcessor::getCurrentProgram()                 { return 0; }
void TsukiSynthProcessor::setCurrentProgram (int)            {}
const juce::String TsukiSynthProcessor::getProgramName (int) { return {}; }
void TsukiSynthProcessor::changeProgramName (int, const juce::String&) {}

void TsukiSynthProcessor::prepareToPlay (double sampleRate, int)
{
    synth.setCurrentPlaybackSampleRate (sampleRate);
    midiCollector.reset (sampleRate);
}

void TsukiSynthProcessor::releaseResources() {}

bool TsukiSynthProcessor::isBusesLayoutSupported (const BusesLayout& layouts) const
{
    const auto& mainOut = layouts.getMainOutputChannelSet();
    return mainOut == juce::AudioChannelSet::mono()
        || mainOut == juce::AudioChannelSet::stereo();
}

void TsukiSynthProcessor::processBlock (juce::AudioBuffer<float>& buffer,
                                         juce::MidiBuffer& midiMessages)
{
    juce::ScopedNoDenormals noDenormals;
    buffer.clear();
    midiCollector.removeNextBlockOfMessages (midiMessages, buffer.getNumSamples());
    synth.renderNextBlock (buffer, midiMessages, 0, buffer.getNumSamples());
}

bool TsukiSynthProcessor::hasEditor() const { return true; }

juce::AudioProcessorEditor* TsukiSynthProcessor::createEditor()
{
    return new TsukiSynthEditor (*this);
}

void TsukiSynthProcessor::getStateInformation (juce::MemoryBlock&) {}
void TsukiSynthProcessor::setStateInformation (const void*, int) {}

void TsukiSynthProcessor::addMidiMessage (const juce::MidiMessage& message)
{
    midiCollector.addMessageToQueue (message);
}

void TsukiSynthProcessor::setEngineType (EngineType e)
{
    engineType = e;
    updateVoiceParams();
}

void TsukiSynthProcessor::setMaterial (const std::string& key)
{
    cimbalomParams.materialKey = key;
    chromaticParams.materialKey = key;
    updateVoiceParams();
}

void TsukiSynthProcessor::updateVoiceParams()
{
    const Material* mat = nullptr;
    if (engineType != EngineType::FMPiano)
    {
        mat = materialDB.getMaterial (
            engineType == EngineType::Cimbalom
                ? cimbalomParams.materialKey
                : chromaticParams.materialKey);
    }

    for (int i = 0; i < synth.getNumVoices(); ++i)
    {
        if (auto* voice = dynamic_cast<MultiVoice*> (synth.getVoice (i)))
        {
            voice->setEngine (engineType);
            voice->setMaterial (mat);
            voice->setCimbalomParams (&cimbalomParams);
            voice->setChromaticParams (&chromaticParams);
            voice->setFMParams (&fmParams);
        }
    }
}

juce::AudioProcessor* JUCE_CALLTYPE createPluginFilter()
{
    return new TsukiSynthProcessor();
}
