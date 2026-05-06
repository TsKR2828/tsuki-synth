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

struct FactoryPreset
{
    const char* name;
    EngineType engine;
    int subParam;
    const char* material;
    float strikePos;
    float reverbWet;
};

static const FactoryPreset factoryPresets[] =
{
    { "Steel Cimbalom",    EngineType::Cimbalom,  0, "steel",    0.3f, 0.25f },
    { "Bronze Cimbalom",   EngineType::Cimbalom,  0, "bronze",   0.25f, 0.3f },
    { "Wood Cimbalom",     EngineType::Cimbalom,  0, "wood_spruce", 0.4f, 0.2f },
    { "Tongue Drum",       EngineType::Chromatic, 0, "aluminum", 0.5f, 0.3f },
    { "Water Gong",        EngineType::Chromatic, 1, "bronze",   0.4f, 0.35f },
    { "Custom Harmonics",  EngineType::Chromatic, 2, "steel",    0.3f, 0.2f },
    { "FM Piano",          EngineType::FMPiano,   0, "steel",    0.3f, 0.2f },
    { "FM Electric Piano", EngineType::FMPiano,   1, "steel",    0.3f, 0.25f },
    { "FM Vibraphone",     EngineType::FMPiano,   2, "steel",    0.3f, 0.35f },
    { "FM Bell",           EngineType::FMPiano,   3, "steel",    0.3f, 0.4f },
    { "FM Organ",          EngineType::FMPiano,   4, "steel",    0.3f, 0.15f },
    { "FM Bass",           EngineType::FMPiano,   5, "steel",    0.3f, 0.1f },
};

static constexpr int numFactoryPresets = 12;

int TsukiSynthProcessor::getNumPrograms()  { return numFactoryPresets; }
int TsukiSynthProcessor::getCurrentProgram() { return currentProgram; }

void TsukiSynthProcessor::setCurrentProgram (int index)
{
    if (index < 0 || index >= numFactoryPresets)
        return;

    currentProgram = index;
    const auto& p = factoryPresets[index];

    engineType = p.engine;
    cimbalomParams.materialKey = p.material;
    chromaticParams.materialKey = p.material;
    cimbalomParams.strikePosition = p.strikePos;
    chromaticParams.strikePosition = p.strikePos;

    if (p.engine == EngineType::Chromatic)
    {
        static const ChromaticSubEngine subs[] = {
            ChromaticSubEngine::TongueDrum,
            ChromaticSubEngine::WaterGong,
            ChromaticSubEngine::CustomHarmonics };
        if (p.subParam >= 0 && p.subParam < 3)
            chromaticParams.subEngine = subs[p.subParam];
    }
    else if (p.engine == EngineType::FMPiano)
    {
        static const FMPreset fmPresets[] = {
            FMPreset::Piano, FMPreset::ElectricPiano,
            FMPreset::Vibraphone, FMPreset::Bell,
            FMPreset::Organ, FMPreset::Bass };
        if (p.subParam >= 0 && p.subParam < 6)
            fmParams.preset = fmPresets[p.subParam];
    }

    effectsParams.reverbWet = p.reverbWet;
    effectsParams.reverbEnabled = p.reverbWet > 0.001f;
    effectsChain.setParameters (effectsParams);

    updateVoiceParams();
}

const juce::String TsukiSynthProcessor::getProgramName (int index)
{
    if (index >= 0 && index < numFactoryPresets)
        return factoryPresets[index].name;
    return {};
}

void TsukiSynthProcessor::changeProgramName (int, const juce::String&) {}

void TsukiSynthProcessor::prepareToPlay (double sampleRate, int)
{
    synth.setCurrentPlaybackSampleRate (sampleRate);
    midiCollector.reset (sampleRate);
    effectsChain.prepare (sampleRate);
    effectsChain.setParameters (effectsParams);
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

    int numSamples = buffer.getNumSamples();
    int numChannels = buffer.getNumChannels();

    if (numChannels >= 2)
    {
        float* left  = buffer.getWritePointer (0);
        float* right = buffer.getWritePointer (1);
        for (int i = 0; i < numSamples; ++i)
            effectsChain.processStereo (left[i], right[i]);
    }
    else if (numChannels == 1)
    {
        float* mono = buffer.getWritePointer (0);
        for (int i = 0; i < numSamples; ++i)
        {
            float dummy = mono[i];
            effectsChain.processStereo (mono[i], dummy);
        }
    }
}

bool TsukiSynthProcessor::hasEditor() const { return true; }

juce::AudioProcessorEditor* TsukiSynthProcessor::createEditor()
{
    return new TsukiSynthEditor (*this);
}

void TsukiSynthProcessor::getStateInformation (juce::MemoryBlock& destData)
{
    auto xml = std::make_unique<juce::XmlElement> ("TsukiSynthState");
    xml->setAttribute ("version", 1);
    xml->setAttribute ("engine", static_cast<int> (engineType));
    xml->setAttribute ("program", currentProgram);

    auto* cim = xml->createNewChildElement ("Cimbalom");
    cim->setAttribute ("material", juce::String (cimbalomParams.materialKey));
    cim->setAttribute ("strikePos", cimbalomParams.strikePosition);
    cim->setAttribute ("exciter", static_cast<int> (cimbalomParams.exciter));
    cim->setAttribute ("strings", cimbalomParams.stringsPerCourse);
    cim->setAttribute ("detune", cimbalomParams.detuneAmount);
    cim->setAttribute ("soundboard", cimbalomParams.soundboardAmount);

    auto* chr = xml->createNewChildElement ("Chromatic");
    chr->setAttribute ("material", juce::String (chromaticParams.materialKey));
    chr->setAttribute ("strikePos", chromaticParams.strikePosition);
    chr->setAttribute ("subEngine", static_cast<int> (chromaticParams.subEngine));
    chr->setAttribute ("waterLevel", chromaticParams.waterLevel);

    auto* fm = xml->createNewChildElement ("FMPiano");
    fm->setAttribute ("preset", static_cast<int> (fmParams.preset));
    fm->setAttribute ("detune", fmParams.detune);
    fm->setAttribute ("volume", fmParams.masterVolume);

    auto* fx = xml->createNewChildElement ("Effects");
    fx->setAttribute ("reverbOn", effectsParams.reverbEnabled);
    fx->setAttribute ("reverbWet", effectsParams.reverbWet);
    fx->setAttribute ("reverbRoom", effectsParams.reverbRoomSize);
    fx->setAttribute ("reverbDamp", effectsParams.reverbDamping);
    fx->setAttribute ("delayOn", effectsParams.delayEnabled);
    fx->setAttribute ("delayWet", effectsParams.delayWet);
    fx->setAttribute ("delayTime", effectsParams.delayTime);
    fx->setAttribute ("delayFeedback", effectsParams.delayFeedback);
    fx->setAttribute ("compOn", effectsParams.compressorEnabled);
    fx->setAttribute ("master", effectsParams.masterVolume);

    copyXmlToBinary (*xml, destData);
}

void TsukiSynthProcessor::setStateInformation (const void* data, int sizeInBytes)
{
    auto xml = getXmlFromBinary (data, sizeInBytes);
    if (xml == nullptr || ! xml->hasTagName ("TsukiSynthState"))
        return;

    engineType = static_cast<EngineType> (xml->getIntAttribute ("engine", 0));
    currentProgram = xml->getIntAttribute ("program", 0);

    if (auto* cim = xml->getChildByName ("Cimbalom"))
    {
        cimbalomParams.materialKey = cim->getStringAttribute ("material", "steel").toStdString();
        cimbalomParams.strikePosition = cim->getDoubleAttribute ("strikePos", 0.3);
        cimbalomParams.exciter = static_cast<ExciterType> (cim->getIntAttribute ("exciter", 2));
        cimbalomParams.stringsPerCourse = cim->getIntAttribute ("strings", 3);
        cimbalomParams.detuneAmount = cim->getDoubleAttribute ("detune", 3.0);
        cimbalomParams.soundboardAmount = cim->getDoubleAttribute ("soundboard", 0.3);
    }

    if (auto* chr = xml->getChildByName ("Chromatic"))
    {
        chromaticParams.materialKey = chr->getStringAttribute ("material", "aluminum").toStdString();
        chromaticParams.strikePosition = chr->getDoubleAttribute ("strikePos", 0.5);
        chromaticParams.subEngine = static_cast<ChromaticSubEngine> (chr->getIntAttribute ("subEngine", 0));
        chromaticParams.waterLevel = chr->getDoubleAttribute ("waterLevel", 0.0);
    }

    if (auto* fm = xml->getChildByName ("FMPiano"))
    {
        fmParams.preset = static_cast<FMPreset> (fm->getIntAttribute ("preset", 0));
        fmParams.detune = fm->getDoubleAttribute ("detune", 0.0);
        fmParams.masterVolume = fm->getDoubleAttribute ("volume", 0.8);
    }

    if (auto* fx = xml->getChildByName ("Effects"))
    {
        effectsParams.reverbEnabled = fx->getBoolAttribute ("reverbOn", true);
        effectsParams.reverbWet = static_cast<float> (fx->getDoubleAttribute ("reverbWet", 0.25));
        effectsParams.reverbRoomSize = static_cast<float> (fx->getDoubleAttribute ("reverbRoom", 0.5));
        effectsParams.reverbDamping = static_cast<float> (fx->getDoubleAttribute ("reverbDamp", 0.3));
        effectsParams.delayEnabled = fx->getBoolAttribute ("delayOn", false);
        effectsParams.delayWet = static_cast<float> (fx->getDoubleAttribute ("delayWet", 0.2));
        effectsParams.delayTime = fx->getDoubleAttribute ("delayTime", 0.3);
        effectsParams.delayFeedback = static_cast<float> (fx->getDoubleAttribute ("delayFeedback", 0.3));
        effectsParams.compressorEnabled = fx->getBoolAttribute ("compOn", false);
        effectsParams.masterVolume = static_cast<float> (fx->getDoubleAttribute ("master", 1.0));
        effectsChain.setParameters (effectsParams);
    }

    updateVoiceParams();
}

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
