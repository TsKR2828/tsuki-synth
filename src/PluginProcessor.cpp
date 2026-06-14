#include "PluginProcessor.h"
#include "PluginEditor.h"
#include "engines/CimbalomEngine.h"
#include "engines/ChromaticEngine.h"
#include "engines/FMPianoEngine.h"
#include "Presets.h"
#include "BinaryData.h"
#include <algorithm>
#include <cmath>

// == Parameter Layout (grouped for DAW automation lanes) ==
juce::AudioProcessorValueTreeState::ParameterLayout
TsukiSynthProcessor::createParameterLayout()
{
    using FloatParam  = juce::AudioParameterFloat;
    using ChoiceParam = juce::AudioParameterChoice;
    using IntParam    = juce::AudioParameterInt;
    using Group       = juce::AudioProcessorParameterGroup;
    using Range       = juce::NormalisableRange<float>;
    using PID         = juce::ParameterID;

    auto global = std::make_unique<Group> ("global", "Global", "|");
    global->addChild (std::make_unique<ChoiceParam> (
        PID { "engine", 1 }, "Engine",
        juce::StringArray { "Cimbalom", "Chromatic", "FM Piano" }, 0));

    auto macro = std::make_unique<Group> ("macro", "Macro", "|");
    macro->addChild (std::make_unique<FloatParam> (
        PID { "macro_material", 1 }, "Material",
        Range (0.0f, 1.0f, 0.01f), 0.5f));
    macro->addChild (std::make_unique<FloatParam> (
        PID { "macro_tension", 1 }, "Tension",
        Range (0.0f, 1.0f, 0.01f), 0.5f));
    macro->addChild (std::make_unique<FloatParam> (
        PID { "macro_damping", 1 }, "Damping",
        Range (0.0f, 1.0f, 0.01f), 0.5f));
    macro->addChild (std::make_unique<FloatParam> (
        PID { "macro_strike", 1 }, "Strike",
        Range (0.0f, 1.0f, 0.01f), 0.5f));
    macro->addChild (std::make_unique<FloatParam> (
        PID { "macro_brightness", 1 }, "Brightness",
        Range (0.0f, 1.0f, 0.01f), 0.5f));
    macro->addChild (std::make_unique<FloatParam> (
        PID { "macro_body", 1 }, "Body",
        Range (0.0f, 1.0f, 0.01f), 0.5f));
    macro->addChild (std::make_unique<FloatParam> (
        PID { "macro_noise", 1 }, "Noise",
        Range (0.0f, 1.0f, 0.01f), 0.0f));
    macro->addChild (std::make_unique<FloatParam> (
        PID { "macro_output", 1 }, "Output",
        Range (0.0f, 1.0f, 0.01f), 1.0f));

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
        Range (0.05f, 0.95f, 0.01f), 0.3f));
    cim->addChild (std::make_unique<FloatParam> (
        PID { "cim_diameter", 1 }, "String Diameter (mm)",
        Range (0.3f, 2.0f, 0.01f), 0.8f));
    cim->addChild (std::make_unique<IntParam> (
        PID { "cim_num_strings", 1 }, "Strings / Course", 1, 5, 3));
    cim->addChild (std::make_unique<FloatParam> (
        PID { "cim_detuning", 1 }, "Detuning (cents)",
        Range (0.0f, 15.0f, 0.1f), 5.0f));

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
        Range (0.0f, 1.0f, 0.01f), 0.35f));
    chr->addChild (std::make_unique<FloatParam> (
        PID { "chr_thickness", 1 }, "Thickness (mm)",
        Range (0.5f, 10.0f, 0.1f), 3.0f));
    chr->addChild (std::make_unique<FloatParam> (
        PID { "chr_size", 1 }, "Size (mm)",
        Range (10.0f, 100.0f, 1.0f), 20.0f));
    chr->addChild (std::make_unique<FloatParam> (
        PID { "chr_pitch_glide", 1 }, "Pitch Glide",
        Range (0.0f, 1.0f, 0.01f), 0.0f));

    {
        static constexpr float defRatios[] = { 1.0f, 2.0f, 3.0f, 4.16f, 5.43f, 6.98f, 8.21f, 10.0f };
        static constexpr float defAmps[]   = { 1.0f, 0.7f, 0.5f, 0.35f, 0.25f, 0.18f, 0.12f, 0.08f };
        for (int i = 0; i < 8; ++i)
        {
            chr->addChild (std::make_unique<FloatParam> (
                PID { "chr_ratio_" + juce::String (i), 1 },
                "Harmonic " + juce::String (i + 1) + " Ratio",
                Range (0.25f, 20.0f, 0.01f, 0.4f), defRatios[i]));
            chr->addChild (std::make_unique<FloatParam> (
                PID { "chr_amp_" + juce::String (i), 1 },
                "Harmonic " + juce::String (i + 1) + " Amp",
                Range (0.0f, 1.0f, 0.01f), defAmps[i]));
        }
    }

    auto fm = std::make_unique<Group> ("fm", "FM Piano", "|");
    fm->addChild (std::make_unique<ChoiceParam> (
        PID { "fm_type", 1 }, "Sound Type",
        juce::StringArray { "Piano", "E.Piano", "Vibraphone", "Bell",
                            "Organ", "Pad", "Bass", "Brass" }, 0));
    fm->addChild (std::make_unique<FloatParam> (
        PID { "fm_ratio", 1 }, "FM Ratio",
        Range (0.5f, 16.0f, 0.01f, 0.4f), 1.0f));           // Piano: 1:1
    fm->addChild (std::make_unique<FloatParam> (
        PID { "fm_index", 1 }, "Mod Index",
        Range (0.0f, 25.0f, 0.1f), 4.5f));                   // was 5.0 → Acoustic Piano direction
    fm->addChild (std::make_unique<FloatParam> (
        PID { "fm_brightness", 1 }, "Tone Decay",
        Range (0.0f, 1.0f, 0.01f), 0.6f));                   // label: body modulation decay speed
    fm->addChild (std::make_unique<FloatParam> (
        PID { "fm_feedback", 1 }, "Feedback",
        Range (0.0f, 1.0f, 0.01f), 0.02f));                  // was 0.0 → subtle odd harmonics
    fm->addChild (std::make_unique<FloatParam> (
        PID { "fm_attack", 1 }, "FM Attack (ms)",
        Range (1.0f, 2000.0f, 1.0f, 0.4f), 5.0f));           // was 10 → quick hammer
    fm->addChild (std::make_unique<FloatParam> (
        PID { "fm_release", 1 }, "FM Release (ms)",
        Range (10.0f, 5000.0f, 1.0f, 0.4f), 500.0f));

    auto rev = std::make_unique<Group> ("reverb", "Reverb", "|");
    rev->addChild (std::make_unique<FloatParam> (
        PID { "fx_reverb_mix", 1 }, "Reverb Mix",
        Range (0.0f, 1.0f, 0.01f), 0.2f));
    rev->addChild (std::make_unique<FloatParam> (
        PID { "fx_reverb_size", 1 }, "Room Size",
        Range (0.0f, 1.0f, 0.01f), 0.5f));

    auto dly = std::make_unique<Group> ("delay", "Delay", "|");
    dly->addChild (std::make_unique<FloatParam> (
        PID { "fx_delay_time", 1 }, "Delay Time (ms)",
        Range (50.0f, 2000.0f, 1.0f, 0.4f), 300.0f));
    dly->addChild (std::make_unique<FloatParam> (
        PID { "fx_delay_feedback", 1 }, "Delay Feedback",
        Range (0.0f, 0.95f, 0.01f), 0.3f));
    dly->addChild (std::make_unique<FloatParam> (
        PID { "fx_delay_mix", 1 }, "Delay Mix",
        Range (0.0f, 1.0f, 0.01f), 0.0f));

    auto comp = std::make_unique<Group> ("comp", "Compressor", "|");
    comp->addChild (std::make_unique<FloatParam> (
        PID { "fx_comp_threshold", 1 }, "Threshold (dB)",
        Range (-40.0f, 0.0f, 0.1f), -12.0f));
    comp->addChild (std::make_unique<FloatParam> (
        PID { "fx_comp_ratio", 1 }, "Ratio",
        Range (1.0f, 20.0f, 0.1f, 0.5f), 4.0f));

    auto dist = std::make_unique<Group> ("dist", "Distortion", "|");
    dist->addChild (std::make_unique<ChoiceParam> (
        PID { "fx_dist_type", 1 }, "Type",
        juce::StringArray { "Overdrive", "Bitcrush", "Wavefold" }, 0));
    dist->addChild (std::make_unique<FloatParam> (
        PID { "fx_dist_drive", 1 }, "Drive",
        Range (0.0f, 1.0f, 0.01f), 0.0f));
    dist->addChild (std::make_unique<FloatParam> (
        PID { "fx_dist_instability", 1 }, "Instability",
        Range (0.0f, 1.0f, 0.01f), 0.0f));
    dist->addChild (std::make_unique<FloatParam> (
        PID { "fx_dist_mix", 1 }, "Mix",
        Range (0.0f, 1.0f, 0.01f), 0.5f));

    juce::AudioProcessorValueTreeState::ParameterLayout layout;
    layout.add (std::move (global), std::move (macro), std::move (cim),
                std::move (chr), std::move (fm), std::move (rev),
                std::move (dly), std::move (comp), std::move (dist));
    return layout;
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

        std::atomic<float>* ratioParams[8] = {};
        std::atomic<float>* ampParams[8]   = {};
        for (int h = 0; h < 8; ++h)
        {
            ratioParams[h] = apvts.getRawParameterValue ("chr_ratio_" + juce::String (h));
            ampParams[h]   = apvts.getRawParameterValue ("chr_amp_"   + juce::String (h));
        }

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
            for (int h = 0; h < 8; ++h)
            {
                voice->pRatio[h] = ratioParams[h];
                voice->pAmp[h]   = ampParams[h];
            }
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
        pFMRelease = pRelease;

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

    // ---- Macro parameters ----
    {
        auto* pMM = apvts.getRawParameterValue ("macro_material");
        auto* pMT = apvts.getRawParameterValue ("macro_tension");
        auto* pMD = apvts.getRawParameterValue ("macro_damping");
        auto* pMS = apvts.getRawParameterValue ("macro_strike");
        auto* pMB = apvts.getRawParameterValue ("macro_brightness");
        auto* pMY = apvts.getRawParameterValue ("macro_body");
        auto* pMN = apvts.getRawParameterValue ("macro_noise");
        pMacroDamping = pMD;
        pMacroOutput = apvts.getRawParameterValue ("macro_output");

        auto wireMacros = [=] (auto* voice)
        {
            voice->pMacroMaterial   = pMM;
            voice->pMacroTension    = pMT;
            voice->pMacroDamping    = pMD;
            voice->pMacroStrike     = pMS;
            voice->pMacroBrightness = pMB;
            voice->pMacroBody       = pMY;
            voice->pMacroNoise      = pMN;
        };

        for (int i = 0; i < cimbalomSynth.getNumVoices(); ++i)
            if (auto* v = dynamic_cast<CimbalomVoice*> (cimbalomSynth.getVoice (i)))
                wireMacros (v);

        for (int i = 0; i < chromaticSynth.getNumVoices(); ++i)
            if (auto* v = dynamic_cast<ChromaticVoice*> (chromaticSynth.getVoice (i)))
                wireMacros (v);

        for (int i = 0; i < fmPianoSynth.getNumVoices(); ++i)
            if (auto* v = dynamic_cast<FMPianoVoice*> (fmPianoSynth.getVoice (i)))
                wireMacros (v);
    }

    // ---- Effect chain ----
    effectChain.pReverbMix     = apvts.getRawParameterValue ("fx_reverb_mix");
    effectChain.pReverbSize    = apvts.getRawParameterValue ("fx_reverb_size");
    effectChain.pDelayTime     = apvts.getRawParameterValue ("fx_delay_time");
    effectChain.pDelayFeedback = apvts.getRawParameterValue ("fx_delay_feedback");
    effectChain.pDelayMix      = apvts.getRawParameterValue ("fx_delay_mix");
    effectChain.pCompThreshold = apvts.getRawParameterValue ("fx_comp_threshold");
    effectChain.pCompRatio     = apvts.getRawParameterValue ("fx_comp_ratio");

    // ---- Distortion ----
    effectChain.pDistType        = apvts.getRawParameterValue ("fx_dist_type");
    effectChain.pDistDrive       = apvts.getRawParameterValue ("fx_dist_drive");
    effectChain.pDistInstability = apvts.getRawParameterValue ("fx_dist_instability");
    effectChain.pDistMix         = apvts.getRawParameterValue ("fx_dist_mix");

    recordingThread.startThread();
}

TsukiSynthProcessor::~TsukiSynthProcessor()
{
    stopRecording();
    recordingThread.stopThread (1000);
}

// == Audio ==
void TsukiSynthProcessor::prepareToPlay (double sampleRate, int)
{
    currentSampleRate = sampleRate;
    cimbalomSynth.setCurrentPlaybackSampleRate (sampleRate);
    chromaticSynth.setCurrentPlaybackSampleRate (sampleRate);
    fmPianoSynth.setCurrentPlaybackSampleRate (sampleRate);
    effectChain.prepare (sampleRate);
    smoothedOutput.reset (sampleRate, 0.02);
}

void TsukiSynthProcessor::releaseResources()
{
    stopRecording();
}

double TsukiSynthProcessor::getTailLengthSeconds() const
{
    double fmRelease = pFMRelease != nullptr
        ? (double) pFMRelease->load() * 0.001
        : 5.0;
    if (pMacroDamping != nullptr)
    {
        const double damping = pMacroDamping->load();
        fmRelease *= 1.0 + (0.5 - damping) * 1.4;
    }
    double tailSeconds = std::max (2.0, fmRelease);

    if (effectChain.pDelayMix != nullptr
        && effectChain.pDelayMix->load() > 0.001f
        && effectChain.pDelayTime != nullptr)
    {
        const double delaySeconds = effectChain.pDelayTime->load() * 0.001;
        const double feedback = effectChain.pDelayFeedback != nullptr
            ? effectChain.pDelayFeedback->load()
            : 0.0;
        const double repeats = feedback > 0.0
            ? std::log (0.001) / std::log (feedback)
            : 1.0;
        tailSeconds += delaySeconds * 1.12 * repeats;
    }

    if (effectChain.pReverbMix != nullptr
        && effectChain.pReverbMix->load() > 0.001f)
    {
        const double roomSize = effectChain.pReverbSize != nullptr
            ? effectChain.pReverbSize->load()
            : 0.5;
        const double feedback = roomSize * 0.28 + 0.7;
        const double longestCombSeconds = 1617.0 / 44100.0;
        const double repeats = std::log (0.001) / std::log (feedback);
        tailSeconds += longestCombSeconds * repeats;
    }

    return std::clamp (tailSeconds, 0.0, 300.0);
}

void TsukiSynthProcessor::processBlock (juce::AudioBuffer<float>& buffer,
                                        juce::MidiBuffer& midiMessages)
{
    juce::ScopedNoDenormals noDenormals;
    buffer.clear();

    keyboardState.processNextMidiBuffer (midiMessages, 0,
                                         buffer.getNumSamples(), true);

    // Track most recent noteOn (any source) for synth-aware tuner display.
    // Scan after keyboardState injection so on-screen keyboard hits are captured.
    for (const auto meta : midiMessages)
    {
        const auto msg = meta.getMessage();
        if (msg.isNoteOn())
            lastNoteOnMidi.store (msg.getNoteNumber(), std::memory_order_release);
    }

    int currentEngine = (int) pEngine->load();

    // On engine switch, release held notes on the engine we left so they tail
    // off (instead of sustaining forever) while the new engine plays.
    if (currentEngine != lastEngine)
    {
        if (lastEngine == 0)      cimbalomSynth.allNotesOff (0, true);
        else if (lastEngine == 1) chromaticSynth.allNotesOff (0, true);
        else if (lastEngine == 2) fmPianoSynth.allNotesOff (0, true);
        // Drop stale noteOn so the new engine's tuner starts on "Awaiting note"
        lastNoteOnMidi.store (-1, std::memory_order_release);
        lastEngine = currentEngine;
    }

    // Render every engine each block so tails from ANY previously-played engine
    // ring out naturally (idle synths early-return). Only the current engine
    // receives MIDI; the others get an empty buffer.
    juce::MidiBuffer empty;
    cimbalomSynth.renderNextBlock  (buffer, currentEngine == 0 ? midiMessages : empty,
                                    0, buffer.getNumSamples());
    chromaticSynth.renderNextBlock (buffer, currentEngine == 1 ? midiMessages : empty,
                                    0, buffer.getNumSamples());
    fmPianoSynth.renderNextBlock   (buffer, currentEngine == 2 ? midiMessages : empty,
                                    0, buffer.getNumSamples());

    // Push dry (pre-FX) mono signal for tuner pitch detection
    {
        constexpr int kMaxBlock = 2048;
        float mono[kMaxBlock];
        int n = juce::jmin (buffer.getNumSamples(), kMaxBlock);
        const float* L = buffer.getReadPointer (0);
        const float* R = buffer.getNumChannels() > 1
                             ? buffer.getReadPointer (1) : L;
        for (int i = 0; i < n; ++i)
            mono[i] = (L[i] + R[i]) * 0.5f;
        analyzerDryFifo.push (mono, n);
    }

    // Global effect chain: Compressor → Delay → Reverb
    effectChain.processBlock (buffer);

    // Macro: Output — final gain (post-FX, per-sample smoothed)
    {
        smoothedOutput.setTargetValue (pMacroOutput->load());
        int n  = buffer.getNumSamples();
        int ch = buffer.getNumChannels();
        for (int i = 0; i < n; ++i)
        {
            float g = smoothedOutput.getNextValue();
            for (int c = 0; c < ch; ++c)
                buffer.getWritePointer (c)[i] *= g;
        }
    }

    // Standalone recorder captures the final audible output.
    if (recordingActive.load())
    {
        if (recordingLock.tryEnter())
        {
            if (recordingWriter != nullptr)
                recordingWriter->write (buffer.getArrayOfReadPointers(), buffer.getNumSamples());
            recordingLock.exit();
        }
    }

    // Mix to mono and push to analyzer FIFO (no lock, no alloc)
    {
        constexpr int kMaxBlock = 2048;
        float mono[kMaxBlock];
        int n = juce::jmin (buffer.getNumSamples(), kMaxBlock);
        const float* L = buffer.getReadPointer (0);
        const float* R = buffer.getNumChannels() > 1
                             ? buffer.getReadPointer (1) : L;
        for (int i = 0; i < n; ++i)
            mono[i] = (L[i] + R[i]) * 0.5f;
        analyzerFifo.push (mono, n);
    }
}

// == Recorder ==
bool TsukiSynthProcessor::startRecording()
{
    const juce::ScopedLock sl (recordingLock);

    if (recordingWriter != nullptr)
        return true;

    auto dir = juce::File::getSpecialLocation (juce::File::userDocumentsDirectory)
                   .getChildFile ("TsukiSynth")
                   .getChildFile ("Recordings");
    dir.createDirectory();

    if (! dir.isDirectory())
    {
        recordingStatus = "Recording folder unavailable";
        return false;
    }

    auto stamp = juce::Time::getCurrentTime().formatted ("%Y%m%d_%H%M%S");
    auto file = dir.getChildFile ("TsukiSynth_" + stamp + ".wav");
    int suffix = 1;
    while (file.existsAsFile())
        file = dir.getChildFile ("TsukiSynth_" + stamp + "_" + juce::String (suffix++) + ".wav");

    juce::WavAudioFormat wavFormat;
    auto fileStream = file.createOutputStream();

    if (fileStream == nullptr || ! fileStream->openedOk())
    {
        recordingStatus = "Could not create recording file";
        return false;
    }

    std::unique_ptr<juce::OutputStream> stream (std::move (fileStream));
    const auto options = juce::AudioFormatWriterOptions()
        .withSampleRate (currentSampleRate)
        .withNumChannels (juce::jmax (1, getTotalNumOutputChannels()))
        .withBitsPerSample (24);
    auto writer = wavFormat.createWriterFor (stream, options);
    if (writer == nullptr)
    {
        recordingStatus = "Could not create WAV writer";
        return false;
    }

    recordingWriter = std::make_unique<juce::AudioFormatWriter::ThreadedWriter> (
        writer.release(), recordingThread, 32768);

    lastRecordingFile = file;
    recordingStatus = "Recording: " + file.getFullPathName();
    recordingActive.store (true);
    return true;
}

void TsukiSynthProcessor::stopRecording()
{
    recordingActive.store (false);

    const juce::ScopedLock sl (recordingLock);
    if (recordingWriter != nullptr)
    {
        recordingWriter.reset();
        recordingStatus = "Saved: " + lastRecordingFile.getFullPathName();
    }
}

juce::String TsukiSynthProcessor::getRecordingStatus() const
{
    const juce::ScopedLock sl (recordingLock);
    return recordingStatus;
}

juce::File TsukiSynthProcessor::getLastRecordingFile() const
{
    const juce::ScopedLock sl (recordingLock);
    return lastRecordingFile;
}

// == Logging (Release-safe, writes to %APPDATA%/TsukiSynth/debug.log) ==
static void tsukiLog (const juce::String& msg)
{
    static auto logFile = juce::File::getSpecialLocation (
                              juce::File::userApplicationDataDirectory)
                              .getChildFile ("TsukiSynth")
                              .getChildFile ("debug.log");
    logFile.getParentDirectory().createDirectory();
    logFile.appendText (juce::Time::getCurrentTime().toString (true, true, true, true)
                        + "  " + msg + "\n");
}

// == State ==
void TsukiSynthProcessor::getStateInformation (juce::MemoryBlock& destData)
{
    auto state = apvts.copyState();
    state.setProperty ("presetIndex", presetManager.getCurrentIndex(), nullptr);
    auto xml = state.createXml();
    copyXmlToBinary (*xml, destData);

    auto v = [&] (const char* id) -> juce::String {
        if (auto* p = apvts.getParameter (id))
            return juce::String (id) + "=" + juce::String (p->getValue(), 4);
        return {};
    };
    tsukiLog ("SAVE  presetIdx=" + juce::String (presetManager.getCurrentIndex())
              + "  " + v ("engine") + "  " + v ("chr_sub_engine")
              + "  " + v ("chr_thickness") + "  " + v ("chr_size")
              + "  " + v ("chr_pitch_glide") + "  " + v ("chr_strike_pos"));
}

void TsukiSynthProcessor::setStateInformation (const void* data, int sizeInBytes)
{
    auto xml = getXmlFromBinary (data, sizeInBytes);
    if (xml != nullptr && xml->hasTagName (apvts.state.getType()))
    {
        auto tree = juce::ValueTree::fromXml (*xml);
        int idx = tree.getProperty ("presetIndex", -1);
        apvts.replaceState (tree);
        presetManager.reattachListener();
        presetManager.setCurrentIndex (idx);
        restoredProgramToIgnore.store (idx, std::memory_order_release);

        auto v = [&] (const char* id) -> juce::String {
            if (auto* p = apvts.getParameter (id))
                return juce::String (id) + "=" + juce::String (p->getValue(), 4);
            return {};
        };
        tsukiLog ("RESTORE  presetIdx=" + juce::String (idx)
                  + "  " + v ("engine") + "  " + v ("chr_sub_engine")
                  + "  " + v ("chr_thickness") + "  " + v ("chr_size")
                  + "  " + v ("chr_pitch_glide") + "  " + v ("chr_strike_pos"));
    }
}

// == Programs (routed through PresetManager) ==
int TsukiSynthProcessor::getNumPrograms()
{
    return juce::jmax (1, presetManager.getNumPresets());
}

int TsukiSynthProcessor::getCurrentProgram()
{
    return juce::jmax (0, presetManager.getCurrentIndex());
}

void TsukiSynthProcessor::setCurrentProgram (int index)
{
    const int restoredIndex = restoredProgramToIgnore.exchange (
        -1, std::memory_order_acq_rel);
    if (restoredIndex >= 0
        && index == restoredIndex
        && presetManager.getCurrentIndex() == restoredIndex)
    {
        tsukiLog ("setCurrentProgram(" + juce::String (index)
                  + ")  SKIPPED (duplicate post-restore)");
        return;
    }

    tsukiLog ("setCurrentProgram(" + juce::String (index) + ")  LOADING");
    presetManager.loadPreset (index);
}

const juce::String TsukiSynthProcessor::getProgramName (int index)
{
    return presetManager.getPresetName (index);
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
