#include "PluginProcessor.h"
#include "PluginEditor.h"
#include "ParameterLayout.h"
#include "engines/CimbalomEngine.h"
#include "engines/ChromaticEngine.h"
#include "engines/FMPianoEngine.h"
#include "Presets.h"
#include "BinaryData.h"
#include <algorithm>
#include <cmath>

// Voices per engine (one juce::Synthesiser each). Stays 16: WF1003-V measured
// 16 vs 32 and 32 failed the pre-registered real-time criteria (32 Piano voices
// held at once need 7.3 ms mean / 20.5 ms p99 per 512-sample block vs a 10.67 ms
// budget) -- reports/wf1003_v_voice_pool.zh-TW.md. The CLI renderer does NOT use
// this pool (one voice per event; src/cli/RenderApp.cpp does not compile this file).
// TSUKI_VOICE_POOL_SIZE is a compile-time override that exists only so the
// 16-vs-32 evidence can be re-run (method: reports/gate_outputs/wf1003_V_method.txt).
#ifndef TSUKI_VOICE_POOL_SIZE
 #define TSUKI_VOICE_POOL_SIZE 16
#endif
static constexpr int kVoicePoolSize = TSUKI_VOICE_POOL_SIZE;

// == Constructor ==
TsukiSynthProcessor::TsukiSynthProcessor()
    : AudioProcessor (BusesProperties()
                        .withOutput ("Output", juce::AudioChannelSet::stereo(), true)),
      apvts (*this, nullptr, "PARAMETERS", createTsukiParameterLayout())
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

        for (int i = 0; i < kVoicePoolSize; ++i)
        {
            auto* voice = new CimbalomVoice();
            voice->setMaterialDB (&materialDB);
            voice->setNoiseIdentity ((uint64_t) i);
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

        for (int i = 0; i < kVoicePoolSize; ++i)
        {
            auto* voice = new ChromaticVoice();
            voice->setMaterialDB (&materialDB);
            voice->setNoiseIdentity ((uint64_t) i);
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

        for (int i = 0; i < kVoicePoolSize; ++i)
        {
            auto* voice = new FMPianoVoice();
            voice->setNoiseIdentity ((uint64_t) i);
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
    effectChain.pReverbDecay   = apvts.getRawParameterValue ("fx_reverb_decay");
    effectChain.pReverbMode    = apvts.getRawParameterValue ("fx_reverb_mode");
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

    // ---- Brightness EQ ----
    effectChain.pEqFreq = apvts.getRawParameterValue ("fx_eq_freq");
    effectChain.pEqGain = apvts.getRawParameterValue ("fx_eq_gain");

    // ---- IR library extra state block (WF0908-P3 §2.5) ----
    presetManager.getExtraStateBlock = [this] () -> juce::ValueTree
    {
        return buildReverbIRBlock();
    };
    presetManager.applyExtraStateBlock = [this] (const juce::ValueTree& extra)
    {
        restoreReverbIR (extra);
    };

    recordingThread.startThread();

    // WF0925-K1 (E9): publish the default-parameter tails before any host can
    // ask, then keep them fresh from the message thread. 20 Hz = the same
    // poll cadence PluginEditor.cpp already uses (startTimerHz (20));
    // engineering choice, not physics, no GATE threshold depends on it. Each
    // tick only hashes ~40 parameter atomics unless something changed.
    refreshEngineTailCache();
    startTimerHz (20);
}

TsukiSynthProcessor::~TsukiSynthProcessor()
{
    stopTimer();
    stopRecording();
    recordingThread.stopThread (1000);
}

// == Audio ==
void TsukiSynthProcessor::prepareToPlay (double sampleRate, int samplesPerBlock)
{
    currentSampleRate = sampleRate;
    cimbalomSynth.setCurrentPlaybackSampleRate (sampleRate);
    chromaticSynth.setCurrentPlaybackSampleRate (sampleRate);
    fmPianoSynth.setCurrentPlaybackSampleRate (sampleRate);
    effectChain.prepare (sampleRate, samplesPerBlock);
    smoothedOutput.reset (sampleRate, 0.02);

    // WF0925-K1 (E9): hosts typically query the tail right after activation
    // (VST3 setActive -> here), so refresh synchronously when we are on the
    // message thread; otherwise the timer picks it up within one tick.
    if (juce::MessageManager::existsAndIsCurrentThread())
        refreshEngineTailCache();
}

void TsukiSynthProcessor::refreshEngineTailCache()
{
    // All 16 voices of a synth share identical APVTS parameter pointers
    // (only materialDB/noiseIdentity differ per voice), so voice 0 is
    // representative -- same reasoning getTailLengthSeconds() documents.
    if (auto* v = dynamic_cast<CimbalomVoice*> (cimbalomSynth.getVoice (0)))
        cimbalomTailSeconds.store (v->getWorstCaseTailSecondsCached());
    if (auto* v = dynamic_cast<ChromaticVoice*> (chromaticSynth.getVoice (0)))
        chromaticTailSeconds.store (v->getWorstCaseTailSecondsCached());
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

    // WF0907-E5: for the physics-modeled engines (Cimbalom/"Piano" preset
    // share cimbalomSynth via engine==0||3; Chromatic==1 covers Tongue
    // Drum/Water Gong/Custom Harmonics), report the engine's own worst-case
    // modal decay (T60) instead of relying on the FM envelope estimate above
    // -- see engines/CimbalomEngine.h / ChromaticEngine.h ::
    // worstCaseTailSeconds() (docs/AUDIT_STRUCTURAL_FINDINGS_2026-08-31.
    // zh-TW.md §1/§4-B: Tongue Drum measured T60 30.18 s vs the old
    // envelope-only estimate of 2-3.45 s). FM Piano (engine==2) is out of
    // the physics-verified domain (ROADMAP_PHYSICS.md §0) and stays on the
    // envelope estimate. All 16 voices of a synth share identical APVTS
    // parameter pointers (only materialDB/noiseIdentity differ per voice --
    // see the constructor's addVoice() loops), so voice 0 is representative
    // of the live parameter state.
    // WF0925-K1 (E9): voice 0's value is computed by refreshEngineTailCache()
    // on the message thread; this function only READS the published atomic
    // (the VST3 SDK marks getTailSamples() "[UI-thread & Setup Done]", but
    // that is the host's promise, not ours -- this makes a host that breaks
    // it harmless instead of a data race + audio-thread allocation).
    const int currentEngineForTail = pEngine != nullptr ? (int) pEngine->load() : -1;
    double engineTailSeconds = 0.0;
    if (currentEngineForTail == 0 || currentEngineForTail == 3)
        engineTailSeconds = cimbalomTailSeconds.load();
    else if (currentEngineForTail == 1)
        engineTailSeconds = chromaticTailSeconds.load();
    tailSeconds = std::max (tailSeconds, engineTailSeconds);

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
        const bool irMode = effectChain.pReverbMode != nullptr
                         && effectChain.pReverbMode->load() >= 0.5f
                         && effectChain.hasImpulseResponse();
        const double decay = effectChain.pReverbDecay != nullptr
            ? effectChain.pReverbDecay->load()
            : 0.0;

        if (irMode)
        {
            tailSeconds += reverbIRSeconds;
        }
        else if (decay >= 0.01)
        {
            // Authored T60 mode: the tail is the T60 itself.
            tailSeconds += decay;
        }
        else
        {
            const double roomSize = effectChain.pReverbSize != nullptr
                ? effectChain.pReverbSize->load()
                : 0.5;
            const double feedback = roomSize * 0.28 + 0.7;
            const double longestCombSeconds = 1617.0 / 44100.0;
            const double repeats = std::log (0.001) / std::log (feedback);
            tailSeconds += longestCombSeconds * repeats;
        }
    }

    // WF0907-E5: no upper clamp -- there is no traceable reason to cap the
    // reported tail (JUCE hosts accept long tails; the previous 300 s ceiling
    // had no cited source). Only floor at 0.
    return std::max (tailSeconds, 0.0);
}

void TsukiSynthProcessor::processBlock (juce::AudioBuffer<float>& buffer,
                                        juce::MidiBuffer& midiMessages)
{
    juce::ScopedNoDenormals noDenormals;
    buffer.clear();

    keyboardState.processNextMidiBuffer (midiMessages, 0,
                                         buffer.getNumSamples(), true);

    int currentEngine = (int) pEngine->load();

    // On engine switch, release held notes on the engine we left so they tail
    // off (instead of sustaining forever) while the new engine plays.
    if (currentEngine != lastEngine)
    {
        if (lastEngine == 0 || lastEngine == 3) cimbalomSynth.allNotesOff (0, true);
        else if (lastEngine == 1) chromaticSynth.allNotesOff (0, true);
        else if (lastEngine == 2) fmPianoSynth.allNotesOff (0, true);
        // Drop stale targets so the new engine starts with a clean tuner state.
        tunerNoteTracker.clear();
        lastNoteOnMidi.store (-1, std::memory_order_release);
        lastEngine = currentEngine;
    }

    // Track the most recently struck note that is still held or sustained.
    // State is per channel/per note, retrigger-aware, and follows CC64/120/121/123.
    for (const auto meta : midiMessages)
    {
        const auto msg = meta.getMessage();
        const int channel = msg.getChannel() - 1;
        if (msg.isNoteOn())
            tunerNoteTracker.noteOn (channel, msg.getNoteNumber());
        else if (msg.isNoteOff())
            tunerNoteTracker.noteOff (channel, msg.getNoteNumber());
        else if (msg.isSustainPedalOn())
            tunerNoteTracker.sustainPedal (channel, true);
        else if (msg.isSustainPedalOff())
            tunerNoteTracker.sustainPedal (channel, false);
        else if (msg.isAllSoundOff())
            tunerNoteTracker.allSoundOff (channel);
        else if (msg.isAllNotesOff())
            tunerNoteTracker.allNotesOff (channel);
        else if (msg.isResetAllControllers())
            tunerNoteTracker.resetControllers (channel);
    }
    lastNoteOnMidi.store (tunerNoteTracker.selectedNote(),
                          std::memory_order_release);

    // Render every engine each block so tails from ANY previously-played engine
    // ring out naturally (idle synths early-return). Only the current engine
    // receives MIDI; the others get an empty buffer.
    juce::MidiBuffer empty;
    cimbalomSynth.renderNextBlock  (buffer, (currentEngine == 0 || currentEngine == 3) ? midiMessages : empty,
                                    0, buffer.getNumSamples());
    chromaticSynth.renderNextBlock (buffer, currentEngine == 1 ? midiMessages : empty,
                                    0, buffer.getNumSamples());
    fmPianoSynth.renderNextBlock   (buffer, currentEngine == 2 ? midiMessages : empty,
                                    0, buffer.getNumSamples());

    // Push dry (pre-FX) mono signal for tuner pitch detection
    {
        constexpr int kMaxBlock = 2048;
        float mono[kMaxBlock];
        const float* L = buffer.getReadPointer (0);
        const float* R = buffer.getNumChannels() > 1
                             ? buffer.getReadPointer (1) : L;
        int remaining = buffer.getNumSamples();
        int offset = 0;
        while (remaining > 0)
        {
            int n = juce::jmin (remaining, kMaxBlock);
            for (int i = 0; i < n; ++i)
                mono[i] = (L[offset + i] + R[offset + i]) * 0.5f;
            analyzerDryFifo.push (mono, n);
            offset += n;
            remaining -= n;
        }
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

    // WF1002-C1 (月月 2026-10-02 Q05=C): record the final output peak for the
    // editor's clip indicator. Read-only (the buffer is not modified), no
    // allocation, no lock -- see dsp/OutputPeakMeter.h.
    outputPeakMeter.pushBlock (buffer);

    // Standalone recorder captures the final audible output.
    if (recordingActive.load())
    {
        if (recordingLock.tryEnter())
        {
            if (recordingWriter != nullptr)
            {
                if (! recordingWriter->write (buffer.getArrayOfReadPointers(), buffer.getNumSamples()))
                    recordingDroppedBlocks.fetch_add (1, std::memory_order_relaxed);
            }
            recordingLock.exit();
        }
        else
        {
            recordingDroppedBlocks.fetch_add (1, std::memory_order_relaxed);
        }
    }

    // Mix to mono and push to analyzer FIFO (no lock, no alloc)
    {
        constexpr int kMaxBlock = 2048;
        float mono[kMaxBlock];
        const float* L = buffer.getReadPointer (0);
        const float* R = buffer.getNumChannels() > 1
                             ? buffer.getReadPointer (1) : L;
        int remaining = buffer.getNumSamples();
        int offset = 0;
        while (remaining > 0)
        {
            int n = juce::jmin (remaining, kMaxBlock);
            for (int i = 0; i < n; ++i)
                mono[i] = (L[offset + i] + R[offset + i]) * 0.5f;
            analyzerFifo.push (mono, n);
            offset += n;
            remaining -= n;
        }
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
        { const juce::ScopedLock sl2 (statusLock); recordingStatus = "Recording folder unavailable"; }
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
        { const juce::ScopedLock sl2 (statusLock); recordingStatus = "Could not create recording file"; }
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
        { const juce::ScopedLock sl2 (statusLock); recordingStatus = "Could not create WAV writer"; }
        return false;
    }

    recordingWriter = std::make_unique<juce::AudioFormatWriter::ThreadedWriter> (
        writer.release(), recordingThread, 32768);

    {
        const juce::ScopedLock sl2 (statusLock);
        lastRecordingFile = file;
        recordingStatus = "Recording: " + file.getFullPathName();
    }
    recordingDroppedBlocks.store (0);
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
        int dropped = recordingDroppedBlocks.load (std::memory_order_relaxed);
        const juce::ScopedLock sl2 (statusLock);
        if (dropped > 0)
            recordingStatus = "Saved (WARNING: " + juce::String (dropped)
                            + " audio blocks dropped): " + lastRecordingFile.getFullPathName();
        else
            recordingStatus = "Saved: " + lastRecordingFile.getFullPathName();
    }
}

juce::String TsukiSynthProcessor::getRecordingStatus() const
{
    const juce::ScopedLock sl (statusLock);
    return recordingStatus;
}

juce::File TsukiSynthProcessor::getLastRecordingFile() const
{
    const juce::ScopedLock sl (statusLock);
    return lastRecordingFile;
}

// == State ==
void TsukiSynthProcessor::getStateInformation (juce::MemoryBlock& destData)
{
    auto state = apvts.copyState();
    // WF0925-K1 (E14): always the version of the format this build actually
    // WRITES (kStateVersion, history in PluginProcessor.h) -- never echoes a
    // newer number carried in from a newer build's state, because what is
    // written below is this build's format, not that one.
    state.setProperty ("state_version", kStateVersion, nullptr);
    state.setProperty ("presetIndex", presetManager.getCurrentIndex(), nullptr);
    state.setProperty ("presetId", presetManager.getCurrentPresetId(), nullptr);
    state.setProperty ("presetDirty", presetManager.isDirty() ? 1 : 0, nullptr);

    if (auto* p = dynamic_cast<juce::AudioParameterChoice*> (apvts.getParameter ("engine")))
        state.setProperty ("engine_index", p->getIndex(), nullptr);
    if (auto* p = dynamic_cast<juce::AudioParameterChoice*> (apvts.getParameter ("chr_sub_engine")))
        state.setProperty ("chr_sub_engine_index", p->getIndex(), nullptr);

    // WF0908-P3 §2.2/§2.4: the reverb_ir child is the single source of truth
    // for "which IR does this state carry" (present only when effectChain
    // genuinely has convolution audio loaded -- reverbIRRef is cleared by
    // restoreReverbIR() whenever the missing-file fallback fires, so a save
    // taken right after that correctly carries NO reverb_ir block; red line
    // 1 forbids remembering a stale IR across saves). ir_missing/ir_mismatch
    // are informational snapshots of the live IRStatus at capture time --
    // setStateInformation() below never reads them back, it always
    // re-resolves from reverb_ir itself; they exist so a host-generic reader
    // (tests/host_probe.cpp H7, which only has the opaque VST3 ABI) can
    // observe the three-state outcome without any custom API (§2.5's "VST3
    // 實例側用 getStateInformation() 讀回的 state 檢查 reverb_ir 區塊與 IR
    // 狀態一致").
    const auto irStatusForState = getIRStatus();
    state.setProperty ("ir_missing",  irStatusForState.missing  ? 1 : 0, nullptr);
    state.setProperty ("ir_mismatch", irStatusForState.mismatch ? 1 : 0, nullptr);
    auto existingIRChild = state.getChildWithName ("reverb_ir");
    if (existingIRChild.isValid())
        state.removeChild (existingIRChild, nullptr);
    auto irBlock = buildReverbIRBlock();
    if (irBlock.isValid())
        state.addChild (irBlock, -1, nullptr);

    auto xml = state.createXml();
    copyXmlToBinary (*xml, destData);

}

void TsukiSynthProcessor::setStateInformation (const void* data, int sizeInBytes)
{
    auto xml = getXmlFromBinary (data, sizeInBytes);
    if (xml != nullptr && xml->hasTagName (apvts.state.getType()))
    {
        auto tree = juce::ValueTree::fromXml (*xml);

        // WF0925-K1 (E14): state format version (history: PluginProcessor.h
        // kStateVersion). Absent = saved before WF0925-K1 -> exactly the same
        // load path as before this field existed (0 is used as "absent" below
        // and is <= kStateVersion, so nothing branches differently). Present
        // and NEWER than this build knows -> read everything this build
        // understands by name (APVTS parameters, the reverb_ir block, preset
        // bookkeeping) exactly as usual, but conservatively skip the D12
        // legacy reverb_ir_path migration further down: that key belongs to
        // pre-versioning formats, and acting on it (importing a file from a
        // path / forcing Algorithmic mode) inside a format whose semantics
        // this build does not know would be a guess. A non-numeric value reads
        // as 0 (= absent) -- never a crash. The property is dropped from
        // `tree` before replaceState(): it is envelope metadata, not live
        // parameter state, so apvts.state stays byte-for-byte what it was
        // before this field existed (getStateInformation() re-adds it).
        const int stateVersion = tree.hasProperty ("state_version")
                                     ? (int) tree.getProperty ("state_version") : 0;
        const bool stateNewerThanKnown = stateVersion > kStateVersion;
        tree.removeProperty ("state_version", nullptr);

        int presetIdx  = tree.getProperty ("presetIndex", -1);
        const juce::String presetId = tree.getProperty ("presetId", juce::String()).toString();
        int engineIdx  = tree.hasProperty ("engine_index")
                             ? (int) tree.getProperty ("engine_index") : -1;
        int subEngIdx  = tree.hasProperty ("chr_sub_engine_index")
                             ? (int) tree.getProperty ("chr_sub_engine_index") : -1;

        apvts.replaceState (tree);

        auto restoreChoice = [] (juce::AudioProcessorValueTreeState& vts,
                                 const char* paramID, int savedIdx)
        {
            if (savedIdx < 0) return;
            if (auto* p = dynamic_cast<juce::AudioParameterChoice*> (vts.getParameter (paramID)))
            {
                int clamped = juce::jlimit (0, p->choices.size() - 1, savedIdx);
                if (p->getIndex() != clamped)
                    *p = clamped;
            }
        };
        restoreChoice (apvts, "engine",         engineIdx);
        restoreChoice (apvts, "chr_sub_engine", subEngIdx);

        // WF0908-P3 §2.2/§2.4: DAW project state carries the IR by identity
        // (reverb_ir: kind/sha256/original_name), resolved through the
        // managed library -- restoreReverbIR() always clears any IR first,
        // then implements the three-state contract (§2.3): resolved+matched
        // loads silently, resolved-but-content-mismatched loads with a
        // mismatch flag, and unresolved forces fx_reverb_mode back to
        // Algorithmic and raises a one-shot warning (never silently keeps
        // whatever IR this instance happened to have loaded before -- red
        // line 1).
        const auto irChild = tree.getChildWithName ("reverb_ir");
        restoreReverbIR (irChild);

        // WF0914-D12: pre-F-03 project state (saved before WF0908-P3) never
        // wrote a "reverb_ir" block at all -- it wrote a bare
        // "reverb_ir_path" property instead (the old PluginProcessor.cpp's
        // now-removed reload-on-DAW-state-restore path). Since
        // restoreReverbIR() above has no code that looks for that old
        // property name, loading such a project used to silently leave no
        // IR loaded -- this is the workcard's motivating defect. Migrate
        // only when the new schema was genuinely absent from this state
        // (irChild.isValid() reflects what was actually in `tree`, not
        // restoreReverbIR()'s outcome, so a malformed-but-present reverb_ir
        // block still correctly skips migration -- card §1 item 3, "新
        // schema 已存在 → 舊鍵忽略").
        // WF0925-K1 (E14): gated off only for a state_version NEWER than this
        // build knows (see the version read at the top); every state this
        // build or an older one wrote takes the unchanged D12 path.
        bool migratedLegacyIR = false;
        if (! irChild.isValid() && ! stateNewerThanKnown)
        {
            const auto legacyIRPath = tree.getProperty ("reverb_ir_path", juce::String()).toString();
            if (legacyIRPath.isNotEmpty())
            {
                migrateLegacyReverbIRPath (legacyIRPath);
                migratedLegacyIR = true;
                // The legacy key has now been consumed (imported, or
                // recorded as missing via expectedIRRef) -- drop it from the
                // live state so it does not linger in every future save this
                // session produces. `tree` shares its underlying ValueTree
                // SharedObject with apvts.state after apvts.replaceState()
                // above (AudioProcessorValueTreeState::replaceState() is a
                // plain `state = newState` handle assignment, not a deep
                // copy), so this mutation is visible to
                // TsukiSynthProcessor::getStateInformation() too. This does
                // NOT affect the original DAW project file on disk -- only
                // this session's in-memory state -- so reopening that same
                // old, unmodified project file again still re-migrates
                // correctly (card §1 item 3 only forbids re-migrating once a
                // "reverb_ir" block already exists, which removing this
                // unrelated property does not create).
                tree.removeProperty ("reverb_ir_path", nullptr);
            }
        }
        else if (irChild.isValid() && ! stateNewerThanKnown)
        {
            // WF1002-C1（月月 2026-10-02 裁決 Q10=B）：情境 3（新 schema 的
            // "reverb_ir" 區塊已存在）——舊鍵照 D12 卡 §1 item 3 一律忽略、不遷移，
            // 但以前會原封不動留在 live state 裡，之後每次存檔都帶著它。現在跟
            // 情境 1/2 一樣把它從這個 session 的記憶體 state 拿掉（理由同上方
            // 註解：只動記憶體、不動磁碟上的 DAW 專案檔）。這不是遷移，不呼叫
            // setDirty()——舊鍵本來就不影響任何行為，拿掉它不改變這個 instance
            // 的聲音或 IR 狀態。比 kStateVersion 新的 state 維持不動（決策包 Q10：
            // 那個邊角只記錄、不處理）。在 reattachListener() 之前做，跟上面的
            // removeProperty 同理，不會觸發 PresetManager 的 dirty 監聽。
            tree.removeProperty ("reverb_ir_path", nullptr);
        }

        presetManager.reattachListener();
        const int resolvedPreset = presetId.isNotEmpty()
            ? presetManager.findPresetById (presetId) : presetIdx;
        presetManager.restoreIndex (resolvedPreset);
        const bool missingSavedPreset = presetId.isNotEmpty() && resolvedPreset < 0;
        presetManager.restoreDirty (
            (int) tree.getProperty ("presetDirty", 0) != 0 || missingSavedPreset);
        // WF0914-D12 audit fix: migrateLegacyReverbIRPath() (above) may have
        // called loadReverbIRFile() -- which calls presetManager.setDirty()
        // internally -- or forced fx_reverb_mode to Algorithmic via
        // forceAlgorithmicMissingIR(). Either way the live state this
        // instance now holds has diverged from the bytes the DAW project
        // still has on disk (a "reverb_ir" block now exists in memory where
        // the saved project only had the bare legacy path, or the mode
        // param moved), the same kind of divergence setDirty() exists to
        // flag elsewhere. restoreDirty() just above reads `presetDirty` from
        // the OLD saved state and unconditionally overwrites whatever
        // setDirty() calls happened during this function -- so without this,
        // a migrated project would silently come back up as "not dirty"
        // even though its in-memory state no longer matches what a
        // subsequent getStateInformation() would write. Run after
        // restoreDirty(), not merged into it, so it can never accidentally
        // clear a legitimate presetDirty=1 that had nothing to do with the
        // migration.
        if (migratedLegacyIR)
            presetManager.setDirty();
        restoredProgramToIgnore.store (resolvedPreset, std::memory_order_release);

        // WF0925-K1 (E9): restored parameters change the engine tail; refresh
        // now when on the message thread, else the timer does it next tick.
        if (juce::MessageManager::existsAndIsCurrentThread())
            refreshEngineTailCache();
    }
}

// == Reverb profile / IR loading (WF0908-P3: managed IR library) ==

bool TsukiSynthProcessor::validateAndLoadIRFile (const juce::File& file,
                                                 juce::String& error,
                                                 double& seconds)
{
    if (! file.existsAsFile())
    {
        error = "File not found: " + file.getFullPathName();
        return false;
    }

    juce::AudioFormatManager formats;
    formats.registerBasicFormats();
    std::unique_ptr<juce::AudioFormatReader> reader (
        formats.createReaderFor (file));
    if (reader == nullptr)
    {
        error = "Not a readable audio file: " + file.getFileName();
        return false;
    }
    if (reader->lengthInSamples <= 0 || reader->sampleRate <= 0.0)
    {
        error = "Impulse response is empty: " + file.getFileName();
        return false;
    }

    seconds = (double) reader->lengthInSamples / reader->sampleRate;
    if (seconds > 30.0)   // matches the score schema's reverb.decay ceiling
    {
        error = "Impulse response longer than 30 s refused ("
              + juce::String (seconds, 1) + " s)";
        return false;
    }
    reader.reset();

    effectChain.loadImpulseResponse (file);
    return true;
}

bool TsukiSynthProcessor::loadReverbIRFile (const juce::File& file,
                                            juce::String& error,
                                            bool switchModeToIR)
{
    double seconds = 0.0;
    if (! validateAndLoadIRFile (file, error, seconds))
        return false;

    juce::String importError;
    auto ref = IRLibrary::importFile (file, importError);
    if (ref.sha256.isEmpty())
    {
        error = importError.isNotEmpty() ? importError
                                          : "Failed to import IR into library";
        effectChain.clearImpulseResponse();
        return false;
    }

    reverbIRRef = ref;
    reverbIRName = ref.originalName;
    reverbIRPath = file.getFullPathName();
    reverbIRSeconds = seconds;
    reverbIRMissing = false;
    // A GUI pick made while a preset/state load's IR was left unresolved
    // (expectedIRRef still set from that failed restore) is "the user
    // pointed at a different file" (F-03 decision packet §2.3 row 2). With
    // no such pending expectation this is an ordinary fresh load: no
    // mismatch to report.
    reverbIRMismatch = expectedIRRef.sha256.isNotEmpty()
                        && expectedIRRef.sha256 != ref.sha256;
    presetManager.setDirty();

    if (switchModeToIR)
        if (auto* p = dynamic_cast<juce::AudioParameterChoice*> (
                apvts.getParameter ("fx_reverb_mode")))
            *p = 1;

    return true;
}

bool TsukiSynthProcessor::tryLoadIRRef (const IRLibrary::IRRef& ref, juce::String& error)
{
    auto file = IRLibrary::resolve (ref);
    if (! file.existsAsFile())
    {
        error = "IR not found in library: " + ref.originalName;
        return false;
    }

    double seconds = 0.0;
    if (! validateAndLoadIRFile (file, error, seconds))
        return false;

    // Content-hash re-verification, not just the name-based lookup resolve()
    // just did: a library entry whose actual bytes no longer match its own
    // sha-derived filename (corrupted, or -- in the no-GUI HostProbe -- a
    // deliberately rewritten entry standing in for "the user picked a
    // different file", per the card's documented simulation strategy) is
    // exactly the §2.3 row 2 mismatch case, not row 1.
    const auto actualSha = IRLibrary::hashFile (file);
    reverbIRRef = ref;
    reverbIRRef.sha256 = actualSha;
    reverbIRName = ref.originalName.isNotEmpty() ? ref.originalName : file.getFileName();
    reverbIRPath = file.getFullPathName();
    reverbIRSeconds = seconds;
    reverbIRMissing = false;
    reverbIRMismatch = (actualSha != ref.sha256);
    return true;
}

void TsukiSynthProcessor::restoreReverbIR (const juce::ValueTree& irBlock)
{
    // §2.4: "loadPreset / setStateInformation 一開始先 clear IR，再依區塊
    // 決定載入" -- unconditional, so a preset/state that carries no IR
    // genuinely leaves none loaded (red line 1: never keep the instance's
    // previous IR across this event).
    effectChain.clearImpulseResponse();
    reverbIRRef = {};
    reverbIRName.clear();
    reverbIRPath.clear();
    reverbIRSeconds = 0.0;
    reverbIRMismatch = false;
    reverbIRMissing = false;
    expectedIRRef = {};

    if (! irBlock.isValid() || ! irBlock.hasType ("reverb_ir"))
        return;

    IRLibrary::IRRef expected;
    expected.kind = irBlock.getProperty ("kind", "user").toString();
    expected.sha256 = irBlock.getProperty ("sha256", juce::String()).toString();
    expected.originalName = irBlock.getProperty ("original_name", juce::String()).toString();
    if (expected.sha256.isEmpty())
        return;   // malformed block -- nothing to restore

    expectedIRRef = expected;

    juce::String loadError;
    if (tryLoadIRRef (expected, loadError))
        return;

    // §2.3 row 3: not found, and there is no GUI to ask (this runs from
    // preset load / DAW state restore) -- force algorithmic and warn once,
    // never leave the UI claiming IR while audio silently runs algorithmic
    // (red line 2) or clip/mute the transport (§4/§7.2's "不可靜音").
    reverbIRMissing = true;
    forceAlgorithmicMissingIR (expected.originalName);
}

void TsukiSynthProcessor::forceAlgorithmicMissingIR (const juce::String& originalName,
                                                     const juce::String& loadFailureReason)
{
    if (auto* p = dynamic_cast<juce::AudioParameterChoice*> (
            apvts.getParameter ("fx_reverb_mode")))
        *p = 0;

    // WF1002-C1（月月 2026-10-02 裁決 Q38=A）：文案改成
    // docs/uiux/UI_FUNCTIONAL_SPEC.zh-TW.md v1.2 §5-3「缺檔警告文案」的定案
    // 文字（舊句「音量會和 IR 模式不同」在 09-16 D9c 補償後已不準）。
    // WF1002-C1（Q10=B）：D12 遷移時「檔案存在但載入失敗」也走這裡，
    // loadFailureReason 非空時把「找不到」那句換成「無法載入（原因：…）」，
    // 其餘照規格文字；原因字串來自 validateAndLoadIRFile()/IRLibrary 的
    // 英文錯誤訊息。純畫面文字，聲音不變。
    const bool zh = UiLocale::isChinese();
    juce::String message = zh ? juce::String (juce::CharPointer_UTF8 ("未載入："))
                              : juce::String ("Not loaded: ");
    message << originalName;
    if (loadFailureReason.isEmpty())
        message << (zh ? juce::String (juce::CharPointer_UTF8 (
                             "——這個 preset 記的 IR 在這台電腦上找不到。"))
                       : juce::String (" -- this preset's IR could not be found on this computer."));
    else
        message << (zh ? juce::String (juce::CharPointer_UTF8 (
                             "——這個 preset 記的 IR 檔案在這台電腦上無法載入（原因："))
                           + loadFailureReason
                           + juce::String (juce::CharPointer_UTF8 ("）。"))
                       : " -- this preset's IR file could not be loaded on this computer"
                         " (reason: " + loadFailureReason + ").");
    message << (zh ? juce::String (juce::CharPointer_UTF8 (
                         "已切回演算法殘響，殘響的音色會和原本的 IR 不同。"))
                   : juce::String (" Switched back to algorithmic reverb;"
                                   " the reverb will sound different from the original IR."));
    setIRWarning (message);
}

void TsukiSynthProcessor::migrateLegacyReverbIRPath (const juce::String& legacyPath)
{
    // WF0914-D12: see the header comment for the full behaviour contract.
    // Precondition (enforced by the only caller, setStateInformation()):
    // restoreReverbIR() already ran this state load and found no "reverb_ir"
    // block, so effectChain/reverbIRRef/reverbIRMissing/expectedIRRef are
    // already the freshly-cleared "nothing loaded" state -- this function
    // never needs to (and does not) clear anything itself.
    const juce::File file (legacyPath);
    if (file.existsAsFile())
    {
        // §1 item 1: file still resolves -- ordinary IRLibrary import
        // (hash/dedupe/kind=user), same function a GUI file pick uses. Mode
        // is NOT force-switched (switchModeToIR=false): apvts.replaceState()
        // already restored fx_reverb_mode to whatever this project's saved
        // state carries, and "reverb_ir_path present" does not imply
        // "fx_reverb_mode was Impulse Response" -- a user can load an IR,
        // switch back to Algorithmic, then save (the old key was written
        // independently of the mode, see the pre-F-03 write site kept for
        // reference at `git show 31eb7ae^:src/PluginProcessor.cpp` lines
        // 699-700). Forcing IR mode here would silently overwrite that
        // user's own saved choice -- exactly the kind of silent state
        // change this card exists to prevent, just on the other field. The
        // removed pre-F-03 migration code made the same call
        // (`/*switchModeToIR*/ false`, same source line range 743-745),
        // so this also matches historic behaviour, not just avoids
        // regressing it.
        juce::String importError;
        if (loadReverbIRFile (file, importError, false))
            return;

        // WF1002-C1（月月 2026-10-02 裁決 Q10=B）：檔案在、但載不進來（讀不到、
        // 空檔、超過 30 s、匯入 IR 庫失敗）以前會靜默丟掉這條路徑——下一次存檔
        // 這個 IR 的線索就永遠消失，反而比「檔案不存在」分支更安靜。現在改走
        // 跟下面缺檔分支相同的三態「缺檔」路徑：reverbIRMissing、保留原檔名
        // （UI 顯示「未載入：〈原檔名〉」）、強制切回演算法、跳一次性警告，
        // 警告附上 importError 的失敗原因。loadReverbIRFile() 失敗時不會留下
        // 已載入的 IR（validateAndLoadIRFile() 在載入前就擋下；匯入失敗那條
        // 會 clearImpulseResponse()），reverbIRRef 也沒被寫入，所以紅線 1
        // 仍成立。聲音：IR 沒載入時本來就走 ALGO，聲音不變。
        reverbIRMissing = true;
        expectedIRRef = {};
        expectedIRRef.originalName = file.getFileName();
        forceAlgorithmicMissingIR (expectedIRRef.originalName,
                                   importError.isNotEmpty() ? importError
                                                            : juce::String ("unknown error"));
        return;
    }

    // §1 item 2: file does not resolve -- F-03's normal missing-IR path
    // (§2.3 row 3), NOT the silent "leave algorithmic without saying
    // anything" behaviour this card exists to remove. There is no content
    // hash to carry (the file cannot be read), so this cannot go through
    // restoreReverbIR()'s ValueTree-based path (which requires a real
    // "reverb_ir" block with a non-empty sha256) -- it sets the same fields
    // that path's row-3 branch sets, directly, recording the legacy path's
    // filename as `original_name` for UI display (getIRStatus().name reads
    // expectedIRRef.originalName whenever reverbIRMissing is true).
    reverbIRMissing = true;
    expectedIRRef = {};
    expectedIRRef.originalName = file.getFileName();
    forceAlgorithmicMissingIR (expectedIRRef.originalName);
}

juce::ValueTree TsukiSynthProcessor::buildReverbIRBlock() const
{
    if (reverbIRRef.sha256.isEmpty())
        return {};
    juce::ValueTree v ("reverb_ir");
    v.setProperty ("kind", reverbIRRef.kind, nullptr);
    v.setProperty ("sha256", reverbIRRef.sha256, nullptr);
    v.setProperty ("original_name", reverbIRRef.originalName, nullptr);
    return v;
}

TsukiSynthProcessor::IRStatus TsukiSynthProcessor::getIRStatus() const
{
    IRStatus s;
    // Single source of truth (§2.4 red line 2): `loaded` IS the audio
    // engine's own bool, not a second variable that could drift from it.
    s.loaded = effectChain.hasImpulseResponse();
    s.mismatch = reverbIRMismatch;
    s.missing = reverbIRMissing;
    s.name = s.loaded ? reverbIRName
                       : (reverbIRMissing ? expectedIRRef.originalName : juce::String());
    return s;
}

void TsukiSynthProcessor::setIRWarning (const juce::String& message)
{
    const juce::ScopedLock sl (statusLock);
    irWarningMessage = message;
}

juce::String TsukiSynthProcessor::getAndClearIRWarning()
{
    const juce::ScopedLock sl (statusLock);
    auto msg = irWarningMessage;
    irWarningMessage.clear();
    return msg;
}

bool TsukiSynthProcessor::loadReverbProfileFile (const juce::File& file,
                                                 juce::String& error)
{
    if (! file.existsAsFile())
    {
        error = "File not found: " + file.getFullPathName();
        return false;
    }

    const auto parsed = juce::JSON::parse (file.loadFileAsString());

    // Accept the scene_reverb.py output fragment {"reverb": {...}} or a full
    // score whose global.effects.reverb carries the same keys.
    auto rev = parsed.getProperty ("reverb", juce::var());
    if (! rev.isObject())
        rev = parsed.getProperty ("global", juce::var())
                    .getProperty ("effects", juce::var())
                    .getProperty ("reverb", juce::var());
    if (! rev.isObject())
    {
        error = "No reverb object found (expected {\"reverb\":{\"decay\",\"wet\"}}"
                " or a score with global.effects.reverb)";
        return false;
    }

    const double decay = (double) rev.getProperty ("decay", -1.0);
    const double wet   = (double) rev.getProperty ("wet",   -1.0);
    if (decay < 0.0 || decay > 30.0 || wet < 0.0 || wet > 1.0)
    {
        error = "reverb.decay must be 0-30 and reverb.wet 0-1 (got decay="
              + juce::String (decay) + ", wet=" + juce::String (wet) + ")";
        return false;
    }

    auto setParam = [this] (const char* id, float value)
    {
        if (auto* p = apvts.getParameter (id))
            p->setValueNotifyingHost (p->convertTo0to1 (value));
    };
    setParam ("fx_reverb_decay", (float) decay);
    setParam ("fx_reverb_mix",   (float) wet);

    if (auto* p = dynamic_cast<juce::AudioParameterChoice*> (
            apvts.getParameter ("fx_reverb_mode")))
        *p = 0;   // profile values drive the algorithmic engine

    return true;
}

// == Programs (routed through PresetManager) ==
// WF1002-C1（月月 2026-10-02 裁決 Q06=A，盤點 E7）：host 看得到的 program
// 只有工廠 preset（PresetManager 的 index 0..N-1，N＝src/Presets.h 的工廠數，
// 目前 27）。理由：JUCE VST3 wrapper 在外掛建立時就固定 program 參數的
// stepCount（juce_audio_plugin_client_VST3.cpp 的 ProgramChangeParameter），
// 使用者 preset 又會增減、依名稱排序——以前把它們接在後面，會造成「新存的
// DAW 叫不到」「插隊讓舊編號整體位移、自動化載到別的 preset」「換電腦編號
// 就不同」三種錯位。使用者 preset 仍在外掛自己的 preset 選單裡（editor 走
// selectPresetFromEditor()，不經 program 編號），DAW 專案 state 也照舊用
// presetId 還原。工廠 preset 的 program 編號與先前完全相同（使用者 preset
// 本來就排在工廠之後），聲音不變。
int TsukiSynthProcessor::programIndexForPreset (int presetIndex) const
{
    // 使用者 preset（index >= 工廠數）與 Init（-1）沒有對應的 host program；
    // 回報 0，跟先前 Init 狀態回報 0 的作法一致（getCurrentProgram() 必須
    // 落在 [0, getNumPrograms())）。
    return presetManager.isFactory (presetIndex) ? presetIndex : 0;
}

int TsukiSynthProcessor::getNumPrograms()
{
    return juce::jmax (1, presetManager.getNumFactoryPresets());
}

int TsukiSynthProcessor::getCurrentProgram()
{
    return programIndexForPreset (presetManager.getCurrentIndex());
}

void TsukiSynthProcessor::setCurrentProgram (int index)
{
    // restoredProgramToIgnore holds the PRESET index the last
    // setStateInformation() resolved (factory, user, or -1). Some hosts
    // re-assert the program they saved right after restoring state; that
    // echo must not reload a preset over the restored (possibly dirty)
    // parameters. Factory restores behave exactly as before (program index
    // == preset index). WF1002-C1: a restored USER preset is reported as
    // program 0 (programIndexForPreset), so its echo is program 0 and is
    // ignored the same way -- otherwise it would load factory 0 over it.
    const int restoredIndex = restoredProgramToIgnore.exchange (
        -1, std::memory_order_acq_rel);
    if (restoredIndex >= 0
        && index == programIndexForPreset (restoredIndex)
        && presetManager.getCurrentIndex() == restoredIndex)
    {
        return;
    }

    if (! presetManager.isFactory (index))
        return;   // host programs are factory presets only (Q06=A)

    presetManager.loadPreset (index);
}

void TsukiSynthProcessor::selectPresetFromEditor (int presetIndex)
{
    // Same one-shot restore-echo guard the pre-WF1002 setCurrentProgram()
    // applied to the editor's combo (which used to call setCurrentProgram()
    // with any preset index, factory or user), but WITHOUT the factory-only
    // restriction: the plug-in's own preset menu still lists user presets.
    const int restoredIndex = restoredProgramToIgnore.exchange (
        -1, std::memory_order_acq_rel);
    if (restoredIndex >= 0
        && presetIndex == restoredIndex
        && presetManager.getCurrentIndex() == restoredIndex)
    {
        return;
    }

    presetManager.loadPreset (presetIndex);
}

const juce::String TsukiSynthProcessor::getProgramName (int index)
{
    return presetManager.isFactory (index) ? presetManager.getPresetName (index)
                                           : juce::String();
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
