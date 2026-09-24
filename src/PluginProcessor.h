#pragma once
#include <juce_audio_processors/juce_audio_processors.h>
#include <juce_audio_utils/juce_audio_utils.h>
#include "physics/MaterialDB.h"
#include "effects/EffectChain.h"
#include "dsp/AudioFIFO.h"
#include "dsp/MidiNoteTracker.h"
#include "PresetManager.h"
#include "IRLibrary.h"

class TsukiSynthProcessor : public juce::AudioProcessor
{
public:
    TsukiSynthProcessor();
    ~TsukiSynthProcessor() override;

    void prepareToPlay (double sampleRate, int samplesPerBlock) override;
    void releaseResources() override;
    void processBlock (juce::AudioBuffer<float>&, juce::MidiBuffer&) override;

    juce::AudioProcessorEditor* createEditor() override;
    bool hasEditor() const override { return true; }

    const juce::String getName() const override { return JucePlugin_Name; }
    bool acceptsMidi() const override  { return true; }
    bool producesMidi() const override { return false; }
    bool isMidiEffect() const override { return false; }
    double getTailLengthSeconds() const override;
    bool isBusesLayoutSupported (const BusesLayout& layouts) const override
    {
        return layouts.getMainOutputChannelSet() == juce::AudioChannelSet::stereo();
    }

    int getNumPrograms() override;
    int getCurrentProgram() override;
    void setCurrentProgram (int index) override;
    const juce::String getProgramName (int index) override;
    void changeProgramName (int, const juce::String&) override {}

    bool startRecording();
    void stopRecording();
    bool isRecording() const { return recordingActive.load(); }
    juce::String getRecordingStatus() const;
    juce::File getLastRecordingFile() const;

    void getStateInformation (juce::MemoryBlock& destData) override;
    void setStateInformation (const void* data, int sizeInBytes) override;

    juce::AudioProcessorValueTreeState apvts;
    PresetManager presetManager { apvts };
    AudioFIFO analyzerFifo { 16384 };
    // At 192 kHz this retains >340 ms, enough for six cycles at the A0
    // detector's lowest search frequency even
    // across a delayed GUI timer tick. AudioFIFO always keeps newest history.
    AudioFIFO analyzerDryFifo { 65536 };
    juce::MidiKeyboardState keyboardState;
    MaterialDB materialDB;

    /** Most recent still-held or sustained MIDI note across all channels. */
    std::atomic<int> lastNoteOnMidi { -1 };

    /** Direct access to the engine choice param so analyzer/tuner can branch. */
    std::atomic<float>* getEngineParam() noexcept { return pEngine; }

    // ---- Reverb profile / impulse-response loading (editor API) ----------
    /** Load a convolution IR (.wav) chosen directly by the user (GUI file
        picker), importing it into the managed IR library (IRLibrary.h,
        WF0908-P3 / F-03 decision packet §7.1 B+). Switches fx_reverb_mode to
        IR on success unless switchModeToIR is false. Returns false and fills
        `error` on failure. */
    bool loadReverbIRFile (const juce::File& file, juce::String& error,
                           bool switchModeToIR = true);
    /** Load a reverb profile: either a scene_reverb JSON fragment
        {"reverb":{"decay":..,"wet":..}} or a full score whose
        global.effects.reverb carries the same keys. Sets fx_reverb_decay +
        fx_reverb_mix and switches fx_reverb_mode to Algorithmic. */
    bool loadReverbProfileFile (const juce::File& file, juce::String& error);

    // ---- IR status: single source of truth (WF0908-P3 §2.4) --------------
    // `loaded` is assigned directly from effectChain.hasImpulseResponse() --
    // there is no second, independently-tracked bool that could drift from
    // audio truth (red line 2 of the F-03 decision packet §7.2: "UI 顯示
    // IR 而音訊在跑 algorithmic，這種狀態不可以存在").
    struct IRStatus
    {
        bool loaded = false;      // == effectChain.hasImpulseResponse()
        juce::String name;        // loaded IR's original name, or (if
                                   // `missing`) the preset-recorded name that
                                   // could not be resolved
        bool mismatch = false;    // loaded, but its content hash differs
                                   // from what the active preset/state named
        bool missing = false;     // preset/state named an IR that could not
                                   // be resolved with no GUI to ask; forced
                                   // to algorithmic (red line 1: never keeps
                                   // the instance's previous IR across this)
    };
    IRStatus getIRStatus() const;

    /** One-shot: returns and clears the pending "IR file named by this
        preset/state could not be found -- forced back to algorithmic" alert
        text, or an empty string when nothing is pending. Polled by the
        editor's timer (state restore is not guaranteed to happen on the
        message thread in every host) so the warning surfaces exactly once
        per missing-IR event, never silently. */
    juce::String getAndClearIRWarning();

private:
    juce::Synthesiser cimbalomSynth;
    juce::Synthesiser chromaticSynth;
    juce::Synthesiser fmPianoSynth;

    EffectChain effectChain;

    std::atomic<float>* pEngine = nullptr;
    std::atomic<float>* pMacroOutput = nullptr;
    std::atomic<float>* pMacroDamping = nullptr;
    std::atomic<float>* pFMRelease = nullptr;
    juce::SmoothedValue<float> smoothedOutput { 1.0f };
    int lastEngine = -1;
    MidiNoteTracker tunerNoteTracker;
    std::atomic<int> restoredProgramToIgnore { -1 };
    double currentSampleRate = 44100.0;

    juce::TimeSliceThread recordingThread { "TsukiSynth Recorder" };
    mutable juce::CriticalSection recordingLock;
    mutable juce::CriticalSection statusLock;
    std::unique_ptr<juce::AudioFormatWriter::ThreadedWriter> recordingWriter;
    std::atomic<bool> recordingActive { false };
    std::atomic<int> recordingDroppedBlocks { 0 };
    juce::File lastRecordingFile;
    juce::String recordingStatus;

    // ---- Reverb IR state (WF0908-P3: identity now persisted via the
    // "reverb_ir" block -- see buildReverbIRBlock()/restoreReverbIR() --
    // instead of a raw path; reverbIRPath below is informational only). ----
    juce::String reverbIRPath;
    juce::String reverbIRName;
    double reverbIRSeconds = 0.0;
    IRLibrary::IRRef reverbIRRef;      // identity of what's ACTUALLY loaded (empty = nothing loaded)
    IRLibrary::IRRef expectedIRRef;    // identity the active preset/state recorded, for mismatch checks
    bool reverbIRMismatch = false;
    bool reverbIRMissing  = false;
    juce::String irWarningMessage;     // guarded by statusLock (shared with recordingStatus below)

    /** Clears any currently-loaded IR, then (if `irBlock` is a valid
        "reverb_ir" tree) resolves and loads the identity it names -- forcing
        fx_reverb_mode back to Algorithmic and raising a one-shot warning if
        it cannot be found. Called at the start of every preset/state load
        (WF0908-P3 §2.4: "loadPreset / setStateInformation 一開始先 clear
        IR，再依區塊決定載入"), including with an invalid tree when the
        preset/state carries none. */
    void restoreReverbIR (const juce::ValueTree& irBlock);
    /** No-GUI load of a library-resolved IR by identity: used by
        restoreReverbIR(). Sets reverbIRMismatch when the resolved file's
        actual content hash differs from `ref.sha256` (§2.3 row 2 -- this is
        also how a corrupted/rewritten library entry is detected, not only a
        manual GUI override). Returns false (does not touch effectChain) when
        the file cannot be found at all (§2.3 row 3). */
    bool tryLoadIRRef (const IRLibrary::IRRef& ref, juce::String& error);
    /** Validates an IR file (readable, non-empty, <= 30 s) and loads it into
        effectChain without touching the library or any identity bookkeeping
        -- the shared tail of loadReverbIRFile()/tryLoadIRRef(). */
    bool validateAndLoadIRFile (const juce::File& file, juce::String& error, double& seconds);
    /** The "reverb_ir" block for whatever is CURRENTLY loaded (reverbIRRef),
        or an invalid ValueTree when nothing is loaded -- the block that both
        saveUserPreset() (via PresetManager::getExtraStateBlock) and
        getStateInformation() embed. */
    juce::ValueTree buildReverbIRBlock() const;
    void setIRWarning (const juce::String& message);
    /** WF0914-D12: the "resolved to nothing, no GUI to ask" tail shared by
        restoreReverbIR()'s §2.3 row 3 and migrateLegacyReverbIRPath()'s
        missing-file case -- forces fx_reverb_mode back to Algorithmic and
        raises the one-shot "not loaded" warning naming `originalName`
        (F03_IR_PRESET_RECALL.zh-TW.md §7.2/§7.6 wording). Does not touch
        reverbIRMissing/expectedIRRef: the two callers populate those
        differently (a real IRRef with a sha256 vs. a migration placeholder
        that has none), and centralising just the mode-force + warning text
        here is what the card means by "遷移邏輯集中一處". */
    void forceAlgorithmicMissingIR (const juce::String& originalName);
    /** WF0914-D12: migrates a pre-F-03 DAW project state's bare
        "reverb_ir_path" property (the only IR identity that existed before
        WF0908-P3 introduced the "reverb_ir" {kind,sha256,original_name}
        schema) into the current three-state contract. Called by
        setStateInformation() only when that state has NO "reverb_ir" block
        (checked by the caller -- new-schema state always wins, the old key
        is then ignored for good, workcard §1 item 3) and the legacy key is
        present. Must run AFTER restoreReverbIR() has already cleared any
        loaded IR (red line 1: never carries a previous instance's IR across
        a state load), so this function itself never calls
        effectChain.clearImpulseResponse() again.
        - Path still resolves to a file on disk: ordinary IRLibrary import
          (hash/dedupe/kind=user) via the same loadReverbIRFile() a GUI file
          pick uses -- workcard §1 item 1, "等同使用者手動載入該 .wav", BUT
          with switchModeToIR=false: unlike an interactive GUI pick, this is
          a state *restore*, and apvts.replaceState() (called earlier in
          setStateInformation(), before restoreReverbIR()/this function run)
          has already put fx_reverb_mode wherever the saved project left it
          -- which may be Algorithmic even though reverb_ir_path is present
          (a user can load an IR, then switch back to Algorithmic, then
          save; the old code never coupled the two). The pre-F-03
          implementation this replaces (see `git show 31eb7ae^` for the
          removed original) made the same choice --
          `loadReverbIRFile (juce::File (irPath), irError, switchModeToIR=false)`
          -- specifically to avoid silently
          overriding the mode the user's own saved state carries. "等同使用者
          手動載入該 .wav" (workcard §1 item 1) describes the import
          mechanics (hash/dedupe/kind=user, same function as a GUI pick),
          not a claim that mode-switching should also be replayed.
        - Path does not resolve: F-03's normal missing-IR path (§2.3 row 3)
          via forceAlgorithmicMissingIR() -- workcard §1 item 2, never a
          silent fallback to algorithmic with no UI indication. */
    void migrateLegacyReverbIRPath (const juce::String& legacyPath);

    JUCE_DECLARE_NON_COPYABLE_WITH_LEAK_DETECTOR (TsukiSynthProcessor)
};
