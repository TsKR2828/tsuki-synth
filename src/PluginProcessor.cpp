#include "PluginProcessor.h"
#include "PluginEditor.h"
#include "BinaryData.h"

bool ModalVoice::canPlaySound (juce::SynthesiserSound* sound)
{
    return dynamic_cast<ModalSound*> (sound) != nullptr;
}

void ModalVoice::startNote (int midiNoteNumber, float velocity,
                             juce::SynthesiserSound*, int)
{
    if (material == nullptr)
        return;

    double targetFreq = juce::MidiMessage::getMidiNoteInHertz (midiNoteNumber);

    // Calculate tension needed to produce target frequency:
    // f1 = (1/2L) * sqrt(T/mu)  =>  T = mu * (2L * f1)^2
    double radius = baseDiameter * 0.5;
    double mu = material->density * juce::MathConstants<double>::pi * radius * radius;
    double tension = mu * std::pow (2.0 * baseLength * targetFreq, 2.0);

    StringParams params;
    params.stringLength   = baseLength;
    params.stringDiameter = baseDiameter;
    params.tension        = tension;
    params.strikePosition = strikePosition;
    params.numModes       = numModes;

    auto modes = StringModel::calculateModes (*material, params);

    resonator.prepare (getSampleRate());
    resonator.setModes (modes);
    resonator.trigger (velocity);
}

void ModalVoice::stopNote (float, bool allowTailOff)
{
    if (allowTailOff)
    {
        resonator.release();
    }
    else
    {
        clearCurrentNote();
    }
}

void ModalVoice::renderNextBlock (juce::AudioBuffer<float>& outputBuffer,
                                   int startSample, int numSamples)
{
    if (! resonator.isActive())
    {
        if (! isVoiceActive())
            return;
        clearCurrentNote();
        return;
    }

    for (int sample = 0; sample < numSamples; ++sample)
    {
        float value = resonator.getNextSample() * 0.15f;

        for (int ch = 0; ch < outputBuffer.getNumChannels(); ++ch)
            outputBuffer.addSample (ch, startSample + sample, value);

        if (! resonator.isActive())
        {
            clearCurrentNote();
            break;
        }
    }
}

TsukiSynthProcessor::TsukiSynthProcessor()
    : AudioProcessor (BusesProperties()
                          .withOutput ("Output",
                                       juce::AudioChannelSet::stereo(), true))
{
    materialDB.loadFromString (juce::String::fromUTF8 (
        BinaryData::materials_json, static_cast<int> (BinaryData::materials_jsonSize)));

    synth.addSound (new ModalSound());

    for (int i = 0; i < numVoices; ++i)
        synth.addVoice (new ModalVoice());

    updateVoiceParams();
}

TsukiSynthProcessor::~TsukiSynthProcessor() {}

const juce::String TsukiSynthProcessor::getName() const { return JucePlugin_Name; }
bool TsukiSynthProcessor::acceptsMidi() const  { return true; }
bool TsukiSynthProcessor::producesMidi() const { return false; }
bool TsukiSynthProcessor::isMidiEffect() const { return false; }
double TsukiSynthProcessor::getTailLengthSeconds() const { return 2.0; }

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

void TsukiSynthProcessor::setMaterial (const std::string& key)
{
    currentMaterialKey = key;
    updateVoiceParams();
}

void TsukiSynthProcessor::setStrikePosition (double pos)
{
    currentStrikePosition = juce::jlimit (0.05, 0.95, pos);
    updateVoiceParams();
}

void TsukiSynthProcessor::updateVoiceParams()
{
    const Material* mat = materialDB.getMaterial (currentMaterialKey);

    for (int i = 0; i < synth.getNumVoices(); ++i)
    {
        if (auto* voice = dynamic_cast<ModalVoice*> (synth.getVoice (i)))
        {
            voice->setMaterial (mat);
            voice->setStringParams (0.8e-3, 0.35, currentStrikePosition, 40);
        }
    }
}

juce::AudioProcessor* JUCE_CALLTYPE createPluginFilter()
{
    return new TsukiSynthProcessor();
}
