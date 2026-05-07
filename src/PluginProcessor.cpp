#include "PluginProcessor.h"
#include "PluginEditor.h"

bool SineVoice::canPlaySound (juce::SynthesiserSound* sound)
{
    return dynamic_cast<SineSound*> (sound) != nullptr;
}

void SineVoice::startNote (int midiNoteNumber, float velocity,
                           juce::SynthesiserSound*, int)
{
    currentAngle = 0.0;
    level = velocity * 0.25;
    tailOff = 0.0;

    auto freq = juce::MidiMessage::getMidiNoteInHertz (midiNoteNumber);
    angleDelta = freq * juce::MathConstants<double>::twoPi / getSampleRate();
}

void SineVoice::stopNote (float, bool allowTailOff)
{
    if (allowTailOff)
    {
        if (tailOff == 0.0)
            tailOff = 1.0;
    }
    else
    {
        clearCurrentNote();
        angleDelta = 0.0;
    }
}

void SineVoice::renderNextBlock (juce::AudioBuffer<float>& outputBuffer,
                                 int startSample, int numSamples)
{
    if (angleDelta == 0.0)
        return;

    while (--numSamples >= 0)
    {
        auto sample = (float) (std::sin (currentAngle) * level);

        if (tailOff > 0.0)
        {
            sample *= (float) tailOff;
            tailOff *= 0.9997;

            if (tailOff <= 0.005)
            {
                clearCurrentNote();
                angleDelta = 0.0;
                break;
            }
        }

        for (int ch = 0; ch < outputBuffer.getNumChannels(); ++ch)
            outputBuffer.addSample (ch, startSample, sample);

        currentAngle += angleDelta;
        ++startSample;
    }
}

TsukiSynthProcessor::TsukiSynthProcessor()
    : AudioProcessor (BusesProperties()
                        .withOutput ("Output", juce::AudioChannelSet::stereo(), true))
{
    synth.addSound (new SineSound());

    for (int i = 0; i < 16; ++i)
        synth.addVoice (new SineVoice());
}

TsukiSynthProcessor::~TsukiSynthProcessor() {}

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

juce::AudioProcessorEditor* TsukiSynthProcessor::createEditor()
{
    return new TsukiSynthEditor (*this);
}

juce::AudioProcessor* JUCE_CALLTYPE createPluginFilter()
{
    return new TsukiSynthProcessor();
}
