// TsukiSynthHostProbe -- ear-free, human-free VST3 host-integration probe
// (EARFREE_MELODY_GATE_DESIGN.zh-TW.md L2, 2026-08-20).
//
// WHY: A9's "Cubase four manual steps" (host scan / play MIDI in / draw an
// automation lane / project state save-reload) were the last human links in
// the verification chain, and pluginval -- while it covers the VST3
// *contract* -- never checks AUDIO CONTENT: nothing ever verified that the
// plug-in's realtime path (CimbalomVoice::startNote via APVTS, a different
// code path from the CLI's ScoreRenderer that all 73 corpus renders use)
// places notes at the right time and pitch. This probe loads the BUILT
// .vst3 bundle from disk through juce::VST3PluginFormat -- the same binary
// a DAW loads, not linked-in source -- and turns all four steps into
// command-output judgments (R1):
//
//   H1 scan          the VST3 format finds + describes the bundle
//   H2 instantiate   an instance is created and prepared
//   H3 MIDI render   the sentinel melody (scores/tests/melody_sentinel.
//                    score.json: notes 60,64,67,71,74 at 0.0/0.6/1.2/1.8/
//                    2.4 s, vel 0.7 -- the plug-in's default parameters ARE
//                    that fixture's params) is streamed as sample-accurate
//                    MidiBuffer events and rendered offline to WAV. The
//                    melody-position verdict itself is issued by
//                    tools/melody_verify.py on that WAV (one judge for CLI,
//                    host and DAW renders alike); this program only asserts
//                    non-silence here.
//   H4 automation    the "EQ Shelf Gain (dB)" parameter is ramped 0 -> +12
//                    dB across the render. Judgments: (a) two identically-
//                    automated renders are byte-identical (determinism
//                    under automation); (b) the 3-12 kHz band gains >= 6 dB
//                    vs the unautomated render (the RBJ high shelf's
//                    documented 2026-08-06 behaviour: +6 dB setting gave
//                    +5.67 dB in-band, so a +12 dB endpoint whose ramp
//                    spends >= half the render above +6 dB must lift the
//                    band well past 6 dB; the exact number is printed).
//   H5 state         set a non-default parameter, capture state, restore it
//                    into TWO fresh instances: the parameter must read back
//                    exactly, and both restores must render byte-identically
//                    (the DAW semantic -- "reload the project, play from
//                    bar 1, get the same audio every time"; see the comment
//                    at the H5 block for why live-vs-fresh is NOT the claim).
//   H6 variable block size (WF0907-E10) the sentinel melody is rendered
//                    through FRESH instances at host block sizes
//                    {64, 256, 512(=kBlockSize), 1024, 4096}; each size's WAV
//                    is judged by the SAME tools/melody_verify.py used for H3
//                    (GATE step, not this program's exit code) -- onset ms /
//                    pitch cents must hold at every size. This program only
//                    PRINTS max-sample-delta (LSB @ 24-bit) and RMS delta
//                    (dB re signal) of each size against the 64-sample
//                    baseline -- informational, no new tolerance (per
//                    WF0907_E10 design doc, R2). It also renders (WAV only,
//                    informational, NOT melody_verify-judged -- there is no
//                    validated --dump-modes expected-pitch fixture for these
//                    two combinations yet, and inventing one is out of this
//                    card's scope) a water_gong note with Pitch Glide macro
//                    at max, and a high FM-Piano note, at the same five sizes
//                    -- the two engine paths named in the WF0907-E10 design
//                    doc as needing coverage, notably ChromaticEngine.h's
//                    glide-phase-advance fix (cdf2017) whose whole point was
//                    block-size independence.
//   H7 user preset round-trip (WF0908-E10b design doc §10.2 option B; IR
//                    three-state hardened to real CHECKs by WF0908-P3).
//                    SAVE side: PresetManager::saveUserPreset()/loadPreset()
//                    are TsukiSynthProcessor members reached, in production,
//                    only by PluginEditor's Save-preset button running
//                    IN-PROCESS with the AudioProcessor -- but this probe, by
//                    its own stated design above ("loads the BUILT .vst3
//                    bundle ... not linked-in source"), only holds a generic
//                    juce::AudioPluginInstance across the VST3 ABI boundary,
//                    which exposes no host-callable "save current state as a
//                    new named user preset" operation. WF0908-E10b's answer
//                    (design doc §10.2 option B): build a "shadow" AudioProcessor
//                    (ShadowProcessor below) around src/ParameterLayout.h's
//                    createTsukiParameterLayout() -- the REAL product
//                    parameter layout, extracted there specifically so a
//                    GUI-free target can build one -- and attach the REAL,
//                    header-only PresetManager (src/PresetManager.h) to it,
//                    so saveUserPreset() runs for real without linking
//                    PluginProcessor.cpp / the GUI module chain. LOAD side:
//                    setCurrentProgram() on a real VST3 instance, same
//                    already-verified real code path every other H-check in
//                    this file uses (TsukiSynthProcessor::setCurrentProgram()
//                    routes it to presetManager.loadPreset()).
//                    WF0908-P3 adds the managed IR library (IRLibrary.h,
//                    also header-only/GUI-free) and its three-state load
//                    contract (F03_IR_PRESET_RECALL.zh-TW.md §2.3/§7.2): the
//                    SAVE side supplies a "reverb_ir" extra block directly
//                    (PresetManager stays IR-agnostic per its own §2.5
//                    design -- see PresetManager.h's getExtraStateBlock/
//                    applyExtraStateBlock comment), and each LOAD-side
//                    instance's getStateInformation() is byte-searched (this
//                    file's existing memoryBlockContainsAscii() technique)
//                    for the reverb_ir block and the ir_missing/ir_mismatch
//                    flags TsukiSynthProcessor::getStateInformation() now
//                    embeds -- the only window this opaque-ABI probe has into
//                    TsukiSynthProcessor's internal IRStatus, since it cannot
//                    call getIRStatus() directly across the VST3 boundary.
//                    The row-2 "使用者在 GUI 指了別的檔" scenario has no GUI
//                    here either, so it is simulated the way the card
//                    documents: after row-3's missing-file resolve failure,
//                    the test itself overwrites the library's sha-named
//                    entry with different IR content ("改寫 IR 庫索引指向
//                    另一檔") -- behaviourally identical to a user picking a
//                    different file, since both leave the processor having
//                    loaded audio whose content hash disagrees with what the
//                    preset recorded.
//   H8 tail length   (WF0907-E5) the loaded VST3's getTailLengthSeconds()
//                    must be >= the corresponding physics engine's own
//                    worstCaseTailSeconds() at that preset's DEFAULT
//                    parameter state, for each of cimbalom/tongue_drum/
//                    water_gong (FM Piano excluded -- out of physics scope,
//                    ROADMAP_PHYSICS.md §0). The comparison value is computed
//                    by an INDEPENDENTLY COMPILED instance of the same
//                    engine header (CimbalomEngine.h / ChromaticEngine.h,
//                    included directly -- this program does not link the
//                    product's compiled objects, consistent with the "loads
//                    the BUILT binary, does not trust linked-in source"
//                    design above; here it is instead a same-formula
//                    cross-check, exactly like bandRmsDb()/melody_verify.py
//                    independently judging the rendered WAV rather than
//                    trusting the plug-in's own claims). It also renders a
//                    held tongue_drum MIDI 40 note and checks the tail
//                    is still audible (RMS > -60 dBFS relative to peak) at
//                    10 s, tying the host-facing NUMBER to something that
//                    actually still needs to be there. WF0925-K2: the
//                    engine cross-check's data/materials.json is looked up
//                    in the cwd first, then under $TSUKI_REPO_ROOT, then in
//                    the executable's ancestor directories (see
//                    findMaterialsJson()); the path used is printed.
//   D12 legacy IR migration (WF0914-D12) three synthetic-state scenarios
//                    (docs/workcards/WF0914_D12_state_migration.md §1/§2)
//                    for TsukiSynthProcessor::migrateLegacyReverbIRPath(),
//                    which upgrades a pre-F-03 DAW project state's bare
//                    "reverb_ir_path" property (no "reverb_ir" block existed
//                    before WF0908-P3) into the current three-state
//                    contract instead of silently leaving no IR loaded.
//                    Reached, like H7, only through the real VST3-ABI
//                    setStateInformation() -- this probe has no linked-in
//                    TsukiSynthProcessor to call the migration function on
//                    directly -- fed a synthetic pre-F-03 state blob built by
//                    buildLegacyMigrationStateBlob() (no real old project
//                    file exists to load from disk). Scenario 1: legacy path
//                    resolves to a file -> ordinary IRLibrary import,
//                    fx_reverb_mode left as the saved state had it (migration
//                    imports the IR but does not force-switch the mode,
//                    switchModeToIR=false). Scenario 2:
//                    legacy path does not resolve -> F-03's normal
//                    missing-IR path (mode forced to Algorithmic, no
//                    reverb_ir block, ir_missing=1) -- the same signature H7
//                    scenario 3 already validates for the new schema.
//                    Scenario 3: a "reverb_ir" block is already present ->
//                    the legacy key is ignored entirely, proven by the
//                    migrated state still naming the new schema's own IR
//                    (never the legacy path's IR) and that IR never
//                    appearing in the managed library. WF0925-K1 adds to
//                    scenarios 1/2: the migrated output state no longer
//                    carries "reverb_ir_path" (the consumed legacy key is
//                    dropped); scenario 3's behaviour is untouched (月月's
//                    decision). The synthetic blobs carry NO "state_version"
//                    (they model states saved before WF0925-K1 existed).
//   E14 state/preset format version (WF0925-K1): H5's captured state
//                    carries state_version=3 and a restore->re-capture keeps
//                    it; a state claiming a NEWER version is loaded without
//                    crashing, its parameters read, the D12 migration
//                    conservatively skipped, and re-saved as version 3; the
//                    H7 user preset reads back as file format 2; a preset
//                    file claiming a NEWER format is listed and loaded but
//                    saveUserPreset() refuses to overwrite it.
//   E16 factory presets (WF0925-K2): every src/Presets.h factory preset's
//                    paramIDs must all resolve in the real parameter layout
//                    (PresetManager::loadFactoryPreset() would otherwise skip
//                    a bad one silently); each preset, selected on a fresh
//                    real VST3 instance via setCurrentProgram(), renders one
//                    C4 note whose output must be entirely finite. Peak/RMS
//                    are printed only (no new threshold, R2).
//
// HONEST SCOPE: this is a JUCE host, not Cubase. It proves VST3-contract
// behaviour of the shipped binary; Cubase-specific behaviour is L3
// (tools/cubase_scan_verify.py = scan; AI-driven export = playback).
//
// Usage: TsukiSynthHostProbe <path-to-TsukiSynth.vst3> <out-dir>
// (relative bundle/out-dir paths resolve against the cwd; H8's
// data/materials.json no longer requires the cwd to be the repo root --
// WF0925-K2, see findMaterialsJson())
// Exit 0 = all checks pass.

#include <juce_audio_processors/juce_audio_processors.h>
#include <juce_audio_formats/juce_audio_formats.h>
#include <juce_events/juce_events.h>
#include <juce_dsp/juce_dsp.h>
#include "physics/MaterialDB.h"
#include "engines/CimbalomEngine.h"
#include "engines/ChromaticEngine.h"
#include "ParameterLayout.h"
#include "PresetManager.h"
#include "IRLibrary.h"
#include <cmath>
#include <cstring>
#include <iostream>
#include <memory>

namespace
{
int failures = 0;

#define CHECK(condition, message) do { \
    if (condition) std::cout << "[PASS] " << message << '\n'; \
    else { std::cout << "[FAIL] " << message << '\n'; ++failures; } \
} while (false)

constexpr double kSampleRate = 48000.0;
constexpr int    kBlockSize  = 512;
constexpr double kRenderLenS = 4.5;

struct NoteSpec { double time; int midi; double durS; float vel; };
// MUST mirror scores/tests/melody_sentinel.score.json exactly -- the
// rendered WAV is judged against that score by melody_verify.py.
constexpr NoteSpec kMelody[] = {
    { 0.0, 60, 0.5, 0.7f }, { 0.6, 64, 0.5, 0.7f }, { 1.2, 67, 0.5, 0.7f },
    { 1.8, 71, 0.5, 0.7f }, { 2.4, 74, 0.5, 0.7f },
};

juce::AudioProcessorParameter* findParam (juce::AudioPluginInstance& inst,
                                          const juce::String& nameContains)
{
    for (auto* p : inst.getParameters())
        if (p->getName (64).containsIgnoreCase (nameContains))
            return p;
    return nullptr;
}

// Renders an arbitrary note list through `inst` at `blockSize`. If
// eqGain != nullptr, ramps it linearly 0 -> 1 (normalised) across the
// render, one step per block, BEFORE each processBlock -- a deterministic
// stand-in for a DAW automation lane.
juce::AudioBuffer<float> renderNotes (juce::AudioPluginInstance& inst,
                                      juce::AudioProcessorParameter* eqGain,
                                      const NoteSpec* notes, size_t numNotes,
                                      double lengthS, int blockSize)
{
    // The sentinel score declares an FX-FREE render (reverb/delay wet 0),
    // but the plug-in's APVTS default is fx_reverb_mix = 0.2 -- a creative
    // default, not part of the melody-position claim. Left on, its build-up
    // registered phantom band rises ~80 ms after strikes (first probe run,
    // 2026-08-20). Zero it so host renders match the fixture's declaration,
    // exactly as a DAW project for this test would.
    if (auto* rev = findParam (inst, "Reverb Mix"))
        rev->setValue (0.0f);
    const int totalSamples = (int) (lengthS * kSampleRate);
    const int numBlocks = (totalSamples + blockSize - 1) / blockSize;
    inst.setNonRealtime (true);
    inst.prepareToPlay (kSampleRate, blockSize);
    const int chans = juce::jmax (2, inst.getTotalNumOutputChannels());
    juce::AudioBuffer<float> out (2, numBlocks * blockSize);
    out.clear();
    juce::AudioBuffer<float> block (chans, blockSize);
    juce::MidiBuffer midi;

    for (int b = 0; b < numBlocks; ++b)
    {
        const int blockStart = b * blockSize;
        midi.clear();
        for (size_t i = 0; i < numNotes; ++i)
        {
            const auto& n = notes[i];
            const int on  = (int) std::llround (n.time * kSampleRate);
            const int off = (int) std::llround ((n.time + n.durS) * kSampleRate);
            if (on >= blockStart && on < blockStart + blockSize)
                midi.addEvent (juce::MidiMessage::noteOn  (1, n.midi, n.vel),
                               on - blockStart);
            if (off >= blockStart && off < blockStart + blockSize)
                midi.addEvent (juce::MidiMessage::noteOff (1, n.midi),
                               off - blockStart);
        }
        if (eqGain != nullptr)
        {
            // Ramp from the parameter's DEFAULT (0 dB for the shelf; its
            // normalised range is -24..+24 dB, so normalised 0.0 would be a
            // -24 dB CUT, not "off" -- first probe run made exactly that
            // mistake and measured a net band cut) up to full boost.
            const float def = eqGain->getDefaultValue();
            const float frac = (float) b / (float) juce::jmax (1, numBlocks - 1);
            eqGain->setValue (def + frac * (1.0f - def));
        }
        block.clear();
        inst.processBlock (block, midi);
        for (int c = 0; c < 2; ++c)
            out.copyFrom (c, blockStart, block,
                          juce::jmin (c, chans - 1), 0, blockSize);
    }
    inst.releaseResources();
    return out;
}

// kMelody through `inst` at the host's normal block size -- unchanged
// behaviour/signature-compatible wrapper kept so every existing H1-H5/H8
// call site is untouched.
juce::AudioBuffer<float> renderMelody (juce::AudioPluginInstance& inst,
                                       juce::AudioProcessorParameter* eqGain,
                                       int blockSize = kBlockSize)
{
    return renderNotes (inst, eqGain, kMelody,
                        sizeof (kMelody) / sizeof (kMelody[0]),
                        kRenderLenS, blockSize);
}

// H6 helper: max |sample delta| (in LSB @ 24-bit signed, i.e. delta * 2^23)
// and RMS delta (dB re the reference signal's own RMS) between two renders,
// compared over the common core length (both buffers may be padded to
// different block-size multiples of the same nominal render length).
// Informational only -- WF0907-E10 design forbids a new pass/fail tolerance
// here; judging is melody_verify.py's job (GATE step 2).
void printBlockSizeDelta (const juce::AudioBuffer<float>& reference,
                          const juce::AudioBuffer<float>& other,
                          int refBlockSize, int otherBlockSize,
                          double nominalLenS)
{
    const int n = juce::jmin ((int) (nominalLenS * kSampleRate),
                              reference.getNumSamples(),
                              other.getNumSamples());
    double maxAbs = 0.0, sumSq = 0.0, refSumSq = 0.0;
    for (int c = 0; c < 2; ++c)
    {
        const float* a = reference.getReadPointer (c);
        const float* b = other.getReadPointer (c);
        for (int i = 0; i < n; ++i)
        {
            const double d = (double) a[i] - (double) b[i];
            maxAbs = juce::jmax (maxAbs, std::abs (d));
            sumSq += d * d;
            refSumSq += (double) a[i] * (double) a[i];
        }
    }
    const double maxLsb24 = maxAbs * 8388608.0; // 2^23
    const long   denom    = juce::jmax (1, n * 2);
    const double rms      = std::sqrt (sumSq / (double) denom);
    const double refRms   = std::sqrt (refSumSq / (double) denom);
    const double rmsDb    = 20.0 * std::log10 (juce::jmax (rms, 1e-12)
                                              / juce::jmax (refRms, 1e-12));
    std::cout << "  [INFO] block " << otherBlockSize << " vs " << refBlockSize
               << ": max|delta|=" << juce::String (maxLsb24, 3)
               << " LSB@24bit, RMS delta=" << juce::String (rmsDb, 2)
               << " dB re signal (n=" << n << " samples/ch)\n";
}

// H6 hardening (WF0908-E10b 2.3): max |sample delta| over the common core
// length, as a plain double the caller can assert on -- same computation as
// printBlockSizeDelta()'s maxAbs above, exposed separately so the water_gong
// glide CHECK below can require it to be EXACTLY 0.0 (byte-identical), the
// SAME judgment the plain kMelody sweep already reaches at every block size
// (0.000 LSB@24bit, per reports/gate_outputs/wf0907_E10_hostprobe.txt) --
// not a new tolerance (R2).
double maxAbsDeltaOverCore (const juce::AudioBuffer<float>& reference,
                           const juce::AudioBuffer<float>& other,
                           double nominalLenS)
{
    const int n = juce::jmin ((int) (nominalLenS * kSampleRate),
                              reference.getNumSamples(),
                              other.getNumSamples());
    double maxAbs = 0.0;
    for (int c = 0; c < 2; ++c)
    {
        const float* a = reference.getReadPointer (c);
        const float* b = other.getReadPointer (c);
        for (int i = 0; i < n; ++i)
            maxAbs = juce::jmax (maxAbs, std::abs ((double) a[i] - (double) b[i]));
    }
    return maxAbs;
}

// Direct byte comparison -- stronger than any hash, and needs no
// cryptography module.
bool buffersEqual (const juce::AudioBuffer<float>& a,
                   const juce::AudioBuffer<float>& b)
{
    if (a.getNumChannels() != b.getNumChannels()
        || a.getNumSamples() != b.getNumSamples())
        return false;
    for (int c = 0; c < a.getNumChannels(); ++c)
        if (std::memcmp (a.getReadPointer (c), b.getReadPointer (c),
                         (size_t) a.getNumSamples() * sizeof (float)) != 0)
            return false;
    return true;
}

double bandRmsDb (const juce::AudioBuffer<float>& buf, double fLo, double fHi)
{
    // Long-FFT band RMS (mono mixdown). Order-of-magnitude judgment only.
    const int n = juce::nextPowerOfTwo (buf.getNumSamples());
    juce::dsp::FFT fft ((int) std::log2 ((double) n));
    std::vector<float> data ((size_t) n * 2, 0.0f);
    for (int i = 0; i < buf.getNumSamples(); ++i)
        data[(size_t) i] = 0.5f * (buf.getSample (0, i) + buf.getSample (1, i));
    fft.performRealOnlyForwardTransform (data.data());
    double acc = 0.0;
    const double binHz = kSampleRate / (double) n;
    for (int k = 1; k < n / 2; ++k)
    {
        const double f = k * binHz;
        if (f >= fLo && f <= fHi)
        {
            const double re = data[(size_t) (2 * k)];
            const double im = data[(size_t) (2 * k + 1)];
            acc += re * re + im * im;
        }
    }
    return 10.0 * std::log10 (juce::jmax (acc, 1e-30));
}

bool writeWav (const juce::AudioBuffer<float>& buf, const juce::File& file)
{
    file.deleteFile();
    juce::WavAudioFormat wav;
    auto stream = file.createOutputStream();
    if (stream == nullptr) return false;
    std::unique_ptr<juce::AudioFormatWriter> writer (
        wav.createWriterFor (stream.get(), kSampleRate,
                             (unsigned) buf.getNumChannels(), 24, {}, 0));
    if (writer == nullptr) return false;
    stream.release();   // writer owns it now
    return writer->writeFromAudioSampleBuffer (buf, 0, buf.getNumSamples());
}

// H7 (WF0908-P3): a short synthetic "impulse response" fixture -- an
// exponentially-decaying noise burst, deterministic per `seed` via a
// trivial LCG (no <random> dependency needed for a throwaway test WAV).
// Real spectral content is irrelevant here; this only needs to be a valid,
// non-empty, short stereo WAV so IRLibrary::importFile()/EffectChain
// actually accept it, and two different seeds must hash differently so the
// H7 mismatch scenario (§2.3 row 2) has genuinely different content to
// place at the same library path.
juce::AudioBuffer<float> makeImpulseFixture (int numSamples, uint32_t seed)
{
    juce::AudioBuffer<float> buf (2, numSamples);
    uint32_t state = seed == 0 ? 1u : seed;
    auto nextRand = [&state] () -> float
    {
        state = state * 1664525u + 1013904223u;
        return ((float) (state >> 8) / (float) (1u << 24)) * 2.0f - 1.0f;
    };
    for (int c = 0; c < 2; ++c)
    {
        auto* w = buf.getWritePointer (c);
        for (int i = 0; i < numSamples; ++i)
        {
            const float envelope = std::exp (-3.0f * (float) i / (float) numSamples);
            w[i] = nextRand() * envelope;
        }
    }
    return buf;
}

void setChoiceParam (juce::AudioPluginInstance& inst, const juce::String& nameContains,
                     int index, int numChoices)
{
    if (auto* p = findParam (inst, nameContains))
        p->setValue ((float) index / (float) juce::jmax (1, numChoices - 1));
}

// H2 evidence (WF0908-E10b GATE 5.5): dumps id|name|numSteps|defaultValue for
// the first `numProductParams` parameters to a plain text file. Run against
// the pre-refactor build\ VST3 and the post-refactor build-wf\ VST3 with the
// SAME literal `numProductParams` and diffed, this is the "pure move, not a
// rewrite" proof for src/ParameterLayout.h's createTsukiParameterLayout()
// (WF0908-E10b design doc §2.2: "參數 id/範圍/預設一字不改"). numProductParams
// is 60 (see the H7 comment block: a live name dump of a VST3-hosted
// instance's parameter indices 0-64 showed 0-59 are the product's own 60
// parameters in createTsukiParameterLayout()'s declaration order, then
// 60=Bypass, 61=Program, 62+="MIDI CC n|c" -- JUCE-VST3-wrapper-synthesised
// extras that are NOT part of the product layout this check is verifying).
void dumpParameterLayout (juce::AudioPluginInstance& inst, int numProductParams,
                          const juce::File& outFile)
{
    juce::StringArray lines;
    auto& params = inst.getParameters();
    for (int i = 0; i < numProductParams && i < params.size(); ++i)
    {
        auto* p = params[i];
        auto* hp = dynamic_cast<juce::HostedAudioProcessorParameter*> (p);
        lines.add ((hp != nullptr ? hp->getParameterID() : juce::String ("?"))
                   + "|" + p->getName (64) + "|"
                   + juce::String (p->getNumSteps()) + "|"
                   + juce::String (p->getDefaultValue(), 6));
    }
    outFile.replaceWithText (lines.joinIntoString ("\n") + "\n");
}

// H8 helper: independently-computed worst-case tail for the DEFAULT preset
// of each physics engine, mirroring the exact defaults declared in
// PluginProcessor.cpp::createParameterLayout() (cim_material=0/"steel",
// cim_strike_pos=0.3, cim_diameter=0.8mm, cim_num_strings=3,
// cim_detuning=5.0 cents; chr_material=0/"steel", chr_strike_pos=0.35,
// chr_thickness=3.0mm, chr_size=20.0mm; all macros default 0.5). If those
// defaults ever change in PluginProcessor.cpp, they must change here too --
// there is no programmatic way to read a VST3-hosted plugin's plain
// parameter defaults back through the generic AudioProcessorParameter
// interface (VST3 only exchanges normalised [0,1] values with the host).
double defaultCimbalomWorstCaseTail (MaterialDB& db)
{
    std::atomic<float> material { 0.0f }, strikePos { 0.3f }, diameter { 0.8f },
                        numStrings { 3.0f }, detuning { 5.0f },
                        mMaterial { 0.5f }, mTension { 0.5f }, mDamping { 0.5f },
                        mStrike { 0.5f }, mBody { 0.5f };
    CimbalomVoice voice;
    voice.setMaterialDB (&db);
    voice.pMaterial      = &material;
    voice.pStrikePos     = &strikePos;
    voice.pDiameter      = &diameter;
    voice.pNumStrings    = &numStrings;
    voice.pDetuning      = &detuning;
    voice.pMacroMaterial = &mMaterial;
    voice.pMacroTension  = &mTension;
    voice.pMacroDamping  = &mDamping;
    voice.pMacroStrike   = &mStrike;
    voice.pMacroBody     = &mBody;
    return voice.worstCaseTailSeconds();
}

double defaultChromaticWorstCaseTail (MaterialDB& db, int subEngine)
{
    std::atomic<float> sub { (float) subEngine }, material { 0.0f },
                        strikePos { 0.35f }, thickness { 3.0f }, size { 20.0f },
                        mMaterial { 0.5f }, mTension { 0.5f }, mDamping { 0.5f },
                        mStrike { 0.5f }, mBody { 0.5f };
    ChromaticVoice voice;
    voice.setCurrentPlaybackSampleRate (kSampleRate);
    voice.setMaterialDB (&db);
    voice.pSubEngine     = &sub;
    voice.pMaterial      = &material;
    voice.pStrikePos     = &strikePos;
    voice.pThickness     = &thickness;
    voice.pSize          = &size;
    voice.pMacroMaterial = &mMaterial;
    voice.pMacroTension  = &mTension;
    voice.pMacroDamping  = &mDamping;
    voice.pMacroStrike   = &mStrike;
    voice.pMacroBody     = &mBody;
    return voice.worstCaseTailSeconds();
}

// Renders a single struck note with NO note-off inside the render window --
// a physically struck string/beam/plate keeps ringing on its own after the
// strike; sending note-off would instead engage the damper
// (CimbalomVoice::applyDamp() / ChromaticVoice's resonator.damp(0.08f)),
// which accelerates decay and would defeat the "does the natural tail
// really last as long as advertised" check below.
juce::AudioBuffer<float> renderSustainedNote (juce::AudioPluginInstance& inst,
                                              int midiNote, float velocity,
                                              double lengthS)
{
    const int totalSamples = (int) (lengthS * kSampleRate);
    const int numBlocks = (totalSamples + kBlockSize - 1) / kBlockSize;
    inst.setNonRealtime (true);
    inst.prepareToPlay (kSampleRate, kBlockSize);
    const int chans = juce::jmax (2, inst.getTotalNumOutputChannels());
    juce::AudioBuffer<float> out (2, numBlocks * kBlockSize);
    out.clear();
    juce::AudioBuffer<float> block (chans, kBlockSize);
    juce::MidiBuffer midi;

    for (int b = 0; b < numBlocks; ++b)
    {
        midi.clear();
        if (b == 0)
            midi.addEvent (juce::MidiMessage::noteOn (1, midiNote, velocity), 0);
        block.clear();
        inst.processBlock (block, midi);
        for (int c = 0; c < 2; ++c)
            out.copyFrom (c, b * kBlockSize, block, juce::jmin (c, chans - 1), 0, kBlockSize);
    }
    inst.releaseResources();
    return out;
}

// WF0925-K2 (E16) helper: one note rendered with the instance's CURRENT
// parameters left exactly as loaded. Unlike renderNotes() -- which zeroes
// "Reverb Mix" because the sentinel fixture declares an FX-free render --
// E16 must render a factory preset as the preset defines it, reverb/delay
// included. Note-on at sample 0, note-off at noteOffS (so the release/damper
// path runs too, which renderSustainedNote() deliberately never reaches).
// The note/velocity/lengths are test-design choices, not pass/fail limits.
juce::AudioBuffer<float> renderNoteAsLoaded (juce::AudioPluginInstance& inst,
                                             int midiNote, float velocity,
                                             double noteOffS, double lengthS)
{
    const int totalSamples = (int) (lengthS * kSampleRate);
    const int numBlocks = (totalSamples + kBlockSize - 1) / kBlockSize;
    const int offSample = (int) std::llround (noteOffS * kSampleRate);
    inst.setNonRealtime (true);
    inst.prepareToPlay (kSampleRate, kBlockSize);
    const int chans = juce::jmax (2, inst.getTotalNumOutputChannels());
    juce::AudioBuffer<float> out (2, numBlocks * kBlockSize);
    out.clear();
    juce::AudioBuffer<float> block (chans, kBlockSize);
    juce::MidiBuffer midi;

    for (int b = 0; b < numBlocks; ++b)
    {
        const int blockStart = b * kBlockSize;
        midi.clear();
        if (b == 0)
            midi.addEvent (juce::MidiMessage::noteOn (1, midiNote, velocity), 0);
        if (offSample >= blockStart && offSample < blockStart + kBlockSize)
            midi.addEvent (juce::MidiMessage::noteOff (1, midiNote), offSample - blockStart);
        block.clear();
        inst.processBlock (block, midi);
        for (int c = 0; c < 2; ++c)
            out.copyFrom (c, blockStart, block, juce::jmin (c, chans - 1), 0, kBlockSize);
    }
    inst.releaseResources();
    return out;
}

// WF0925-K2 (09-25 live-gate finding 2): H8 used to look for
// data/materials.json ONLY relative to the current working directory, so
// running this probe from anywhere but the repo root produced 4 false H8
// FAILs (the 2026-09-25 live-gate run hit exactly that). Lookup order now:
//   1. <cwd>/data/materials.json -- first, so a run from the repo root (the
//      documented GATE command) resolves exactly the same file as before;
//   2. $TSUKI_REPO_ROOT/data/materials.json -- explicit override (an
//      absolute path, or relative to the cwd);
//   3. the nearest ancestor of this executable's own directory that contains
//      data/materials.json (e.g. build-wf/Release/ -> the repo root).
// The path finally used and how it was found are printed by the caller; a
// rejected TSUKI_REPO_ROOT is printed here. If nothing is found the cwd
// candidate is returned, so the H8 CHECK fails loudly naming that path,
// exactly as before this change.
struct MaterialsLookup { juce::File file; juce::String via; };

MaterialsLookup findMaterialsJson()
{
    const juce::String rel ("data/materials.json");
    const juce::File cwd = juce::File::getCurrentWorkingDirectory();
    const juce::File cwdCandidate = cwd.getChildFile (rel);
    if (cwdCandidate.existsAsFile())
        return { cwdCandidate, "found in the current working directory" };

    const juce::String envRoot =
        juce::SystemStats::getEnvironmentVariable ("TSUKI_REPO_ROOT", {});
    if (envRoot.isNotEmpty())
    {
        const juce::File envCandidate = cwd.getChildFile (envRoot).getChildFile (rel);
        if (envCandidate.existsAsFile())
            return { envCandidate, "found via TSUKI_REPO_ROOT" };
        std::cout << "  H8 materials.json: TSUKI_REPO_ROOT='" << envRoot
                  << "' has no " << rel << " -- ignored\n";
    }

    juce::File dir = juce::File::getSpecialLocation (juce::File::currentExecutableFile)
                         .getParentDirectory();
    while (dir.getFullPathName().isNotEmpty())
    {
        const juce::File candidate = dir.getChildFile (rel);
        if (candidate.existsAsFile())
            return { candidate, "found in an ancestor of the executable's directory" };
        const juce::File parent = dir.getParentDirectory();
        if (parent == dir)
            break;   // reached the filesystem root
        dir = parent;
    }
    return { cwdCandidate, "NOT FOUND in cwd / TSUKI_REPO_ROOT / the executable's ancestors;"
                           " falling back to the cwd path" };
}

// ── H7 user preset round-trip (WF0908-E10b, design doc §10.2 option B) ────
// A minimal, GUI-free juce::AudioProcessor used only to host a "shadow"
// AudioProcessorValueTreeState built from src/ParameterLayout.h's
// createTsukiParameterLayout() -- the REAL product parameter layout, moved
// there specifically so this GUI-free target can build one -- so that
// PresetManager (header-only, needs only an AudioProcessorValueTreeState&,
// src/PresetManager.h) can be attached to it for real and its real
// saveUserPreset() called for real. This is deliberately NOT
// TsukiSynthProcessor: it carries none of the product's DSP/engine members,
// and implements nothing beyond the pure-virtual juce::AudioProcessor
// contract, because H7's SAVE side only needs a working APVTS +
// PresetManager pair to exist (same architecture-conflict reasoning that
// blocked calling saveUserPreset() on the opaque VST3-loaded `inst` used
// everywhere else in this file -- see the H7 comment block at the top of
// this file).
class ShadowProcessor : public juce::AudioProcessor
{
public:
    ShadowProcessor()
        : juce::AudioProcessor (BusesProperties()
                                   .withOutput ("Output", juce::AudioChannelSet::stereo(), true)),
          apvts (*this, nullptr, "PARAMETERS", createTsukiParameterLayout())
    {}

    const juce::String getName() const override { return "TsukiSynthShadow"; }
    void prepareToPlay (double, int) override {}
    void releaseResources() override {}
    void processBlock (juce::AudioBuffer<float>&, juce::MidiBuffer&) override {}
    double getTailLengthSeconds() const override { return 0.0; }
    bool acceptsMidi() const override { return true; }
    bool producesMidi() const override { return false; }
    juce::AudioProcessorEditor* createEditor() override { return nullptr; }
    bool hasEditor() const override { return false; }
    int getNumPrograms() override { return 1; }
    int getCurrentProgram() override { return 0; }
    void setCurrentProgram (int) override {}
    const juce::String getProgramName (int) override { return {}; }
    void changeProgramName (int, const juce::String&) override {}
    void getStateInformation (juce::MemoryBlock&) override {}
    void setStateInformation (const void*, int) override {}

    // Declaration order matters: apvts must be fully constructed (via the
    // constructor's mem-initializer list above) before presetManager's
    // in-class initializer runs -- exactly mirroring
    // TsukiSynthProcessor.h's `apvts` / `presetManager` member order.
    juce::AudioProcessorValueTreeState apvts;
    PresetManager presetManager { apvts };
};

void setApvtsParamPlain (juce::AudioProcessorValueTreeState& vts,
                         const juce::String& paramID, float plainValue)
{
    if (auto* p = vts.getParameter (paramID))
        p->setValueNotifyingHost (p->convertTo0to1 (plainValue));
}


// H7 (WF0908-P3): AudioPluginInstance::getStateInformation() (the opaque
// VST3-ABI call every H-check in this file uses) does NOT return
// TsukiSynthProcessor::getStateInformation()'s bytes directly -- JUCE's VST3
// client wrapper (juce_VST3PluginFormatImpl.h's getStateInformation())
// wraps them in an outer <VST3PluginState><IComponent>BASE64...</IComponent>
// ...</VST3PluginState> XML (itself also AudioProcessor::copyXmlToBinary'd),
// where the <IComponent> text is the wrapped processor's own state,
// base64-encoded (confirmed by reading that header's appendStateFrom() /
// getStateInformation(), which calls component->getState() then
// info.toBase64Encoding() into that child element). A plain byte-substring
// search over the RAW block therefore never finds "reverb_ir" -- it exists,
// but only inside that base64 text, whose encoding does not preserve ASCII
// substrings. This decodes down to the actual TsukiSynthProcessor state
// bytes so memoryBlockContainsAscii() below is searching the right thing.
juce::MemoryBlock decodeVst3ProcessorState (const juce::MemoryBlock& outerBlock)
{
    juce::MemoryBlock inner;
    if (auto xml = juce::AudioProcessor::getXmlFromBinary (outerBlock.getData(),
                                                            (int) outerBlock.getSize()))
        if (auto* comp = xml->getChildByName ("IComponent"))
            inner.fromBase64Encoding (comp->getAllSubText());
    return inner;
}

// WF0925-K1 (E14): must mirror src/PluginProcessor.h's
// TsukiSynthProcessor::kStateVersion (this probe does not link
// PluginProcessor.cpp -- see the H7 comment block -- so it cannot read the
// constant; a version bump there must bump this too, which is the point).
constexpr int kExpectedStateVersion = 3;

// WF0925-K1 (E14): the "state_version" attribute of the TsukiSynthProcessor
// state inside an opaque VST3 state block (decodeVst3ProcessorState() above
// explains the wrapper shell). -1 = attribute absent, -2 = not decodable.
int readStateVersion (const juce::MemoryBlock& outerBlock)
{
    const auto inner = decodeVst3ProcessorState (outerBlock);
    if (auto xml = juce::AudioProcessor::getXmlFromBinary (inner.getData(),
                                                           (int) inner.getSize()))
        return xml->hasAttribute ("state_version")
                   ? xml->getIntAttribute ("state_version") : -1;
    return -2;
}

// Raw byte-pattern search over a MemoryBlock. Used on H7's IR checks instead
// of building a juce::String from the block: JUCE's copyXmlToBinary (used by
// TsukiSynthProcessor::getStateInformation()) prefixes the UTF-8 XML text
// with a small binary magic/size header, so a byte-level substring search is
// well-defined where a String reinterpretation of the header bytes would not
// be.
bool memoryBlockContainsAscii (const juce::MemoryBlock& block, const char* needle)
{
    const auto* data = static_cast<const char*> (block.getData());
    const size_t dataLen = block.getSize();
    const size_t needleLen = std::strlen (needle);
    if (needleLen == 0 || dataLen < needleLen) return false;
    for (size_t i = 0; i + needleLen <= dataLen; ++i)
        if (std::memcmp (data + i, needle, needleLen) == 0)
            return true;
    return false;
}

// WF0914-D12: builds a synthetic setStateInformation()-shaped blob carrying
// the pre-F-03 legacy "reverb_ir_path" property, so
// TsukiSynthProcessor::migrateLegacyReverbIRPath() (reached only through the
// opaque VST3 ABI here, same architectural reason as H7's comment block at
// the top of this file -- this probe holds no linked-in TsukiSynthProcessor)
// can be exercised without a GUI or a real pre-F-03 project file.
//
// Starts from `sourceInstance`'s OWN getStateInformation() output -- so
// every property real production code writes (presetIndex/engine_index/
// ir_missing/ir_mismatch/etc) round-trips unmodified, exactly the "bit
// pattern setStateInformation() actually receives" rather than a hand-typed
// XML guess -- and edits only the inner TsukiSynthProcessor-state XML nested
// inside the VST3 wrapper's <VST3PluginState><IComponent>BASE64...
// </IComponent></VST3PluginState> shell (see this file's
// decodeVst3ProcessorState() comment for why that shell exists and how the
// base64 IComponent text maps 1:1 to TsukiSynthProcessor::getStateInformation
// ()'s own bytes):
//   - `dropIRChild`: removes any existing "reverb_ir" child first (a fresh
//     instance's default state has none, but this keeps the helper correct
//     if called on an instance that already has one loaded).
//   - `injectIRRef`: when non-null, adds/replaces a "reverb_ir" child built
//     from that identity -- used to synthesize an "already on the new
//     schema" state without a GUI (scenario 3: new schema present, legacy
//     key must be ignored).
//   - `legacyPath`: always set as the "reverb_ir_path" property (the bare
//     pre-F-03 key). Empty string = no such property (not used by any of
//     this card's three scenarios, kept only for completeness).
//   - `stateVersionToWrite` (WF0925-K1 / E14): 0 (default) REMOVES the
//     "state_version" attribute the source instance now writes, so the blob
//     models what every state saved before WF0925-K1 looks like (pre-F-03
//     for scenarios 1/2, F-03-era for scenario 3 -- neither ever carried a
//     version); > 0 writes that number instead (the E14 "newer than this
//     build knows" scenario).
// No IEditController child is written: juce_VST3PluginFormatImpl.h's
// setStateInformation() reuses the IComponent stream for
// setComponentStateAndResetParameters() (the step that refreshes the
// host-exposed AudioProcessorParameter values findParam() reads below)
// unconditionally whenever an editController exists, regardless of whether
// an IEditController child is present -- confirmed by reading that
// function's body (juce_VST3PluginFormatImpl.h:2835-2869).
juce::MemoryBlock buildLegacyMigrationStateBlob (juce::AudioPluginInstance& sourceInstance,
                                                 const juce::String& legacyPath,
                                                 bool dropIRChild,
                                                 const IRLibrary::IRRef* injectIRRef,
                                                 int stateVersionToWrite = 0)
{
    juce::MemoryBlock outerRaw;
    sourceInstance.getStateInformation (outerRaw);

    auto outerXml = juce::AudioProcessor::getXmlFromBinary (outerRaw.getData(),
                                                             (int) outerRaw.getSize());
    if (outerXml == nullptr) return {};
    auto* comp = outerXml->getChildByName ("IComponent");
    if (comp == nullptr) return {};

    juce::MemoryBlock innerRaw;
    if (! innerRaw.fromBase64Encoding (comp->getAllSubText())) return {};
    auto innerXml = juce::AudioProcessor::getXmlFromBinary (innerRaw.getData(),
                                                             (int) innerRaw.getSize());
    if (innerXml == nullptr) return {};

    if (dropIRChild || injectIRRef != nullptr)
        if (auto* existing = innerXml->getChildByName ("reverb_ir"))
            innerXml->removeChildElement (existing, true);

    if (injectIRRef != nullptr)
    {
        auto* child = innerXml->createNewChildElement ("reverb_ir");
        child->setAttribute ("kind", injectIRRef->kind);
        child->setAttribute ("sha256", injectIRRef->sha256);
        child->setAttribute ("original_name", injectIRRef->originalName);
    }

    if (legacyPath.isNotEmpty())
        innerXml->setAttribute ("reverb_ir_path", legacyPath);

    if (stateVersionToWrite > 0)
        innerXml->setAttribute ("state_version", stateVersionToWrite);
    else
        innerXml->removeAttribute ("state_version");

    juce::MemoryBlock newInnerRaw;
    juce::AudioProcessor::copyXmlToBinary (*innerXml, newInnerRaw);

    juce::XmlElement outer ("VST3PluginState");
    outer.createNewChildElement ("IComponent")
         ->addTextElement (newInnerRaw.toBase64Encoding());

    juce::MemoryBlock newOuterRaw;
    juce::AudioProcessor::copyXmlToBinary (outer, newOuterRaw);
    return newOuterRaw;
}
} // namespace

int main (int argc, char** argv)
{
    if (argc < 3)
    {
        std::cout << "usage: TsukiSynthHostProbe <TsukiSynth.vst3> <out-dir>\n";
        return 2;
    }
    juce::ScopedJuceInitialiser_GUI juceInit;
    juce::MessageManager::getInstance()->setCurrentThreadAsMessageThread();

    const juce::File bundle (juce::File::getCurrentWorkingDirectory()
                                 .getChildFile (juce::String (argv[1])));
    const juce::File outDir (juce::File::getCurrentWorkingDirectory()
                                 .getChildFile (juce::String (argv[2])));
    outDir.createDirectory();

    // -- H1 scan ------------------------------------------------------------
    juce::VST3PluginFormat vst3;
    juce::OwnedArray<juce::PluginDescription> found;
    vst3.findAllTypesForFile (found, bundle.getFullPathName());
    CHECK (found.size() >= 1, "H1 scan: VST3 format finds the bundle ("
           << bundle.getFullPathName() << " -> " << found.size() << " type)");
    if (found.isEmpty()) return 1;
    const auto& desc = *found[0];
    CHECK (desc.name == "TsukiSynth" && desc.isInstrument,
           "H1 scan: described as instrument named TsukiSynth (got '"
           << desc.name << "', isInstrument=" << (desc.isInstrument ? 1 : 0)
           << ", version " << desc.version << ")");

    // -- H2 instantiate ------------------------------------------------------
    juce::AudioPluginFormatManager fm;
    fm.addFormat (new juce::VST3PluginFormat());
    juce::String err;
    auto inst = fm.createPluginInstance (desc, kSampleRate, kBlockSize, err);
    CHECK (inst != nullptr, "H2 instantiate: instance created"
           << (err.isEmpty() ? juce::String() : (" (error: " + err + ")")));
    if (inst == nullptr) return 1;

    // WF0908-E10b GATE 5.5 evidence (see dumpParameterLayout() comment):
    // written unconditionally so the SAME command, run against the
    // pre-refactor build\ VST3 and the post-refactor build-wf\ VST3, produces
    // a diffable pair of files proving createTsukiParameterLayout() is a pure
    // move.
    dumpParameterLayout (*inst, 60, outDir.getChildFile ("h2_parameter_layout.txt"));

    // -- H3 MIDI render ------------------------------------------------------
    auto render1 = renderMelody (*inst, nullptr);
    const auto mag = render1.getMagnitude (0, render1.getNumSamples());
    CHECK (mag > 0.001f && mag < 1.0f,
           "H3 MIDI render: non-silent, non-clipping output (peak "
           << mag << ") -- melody-position verdict follows via melody_verify.py");
    const auto wav1 = outDir.getChildFile ("hostprobe_render.wav");
    CHECK (writeWav (render1, wav1),
           "H3 MIDI render: WAV written: " << wav1.getFullPathName());

    // Determinism baseline: an identical second instance renders identical
    // bytes (prerequisite for the H5 byte-compare to be meaningful).
    {
        auto inst2 = fm.createPluginInstance (desc, kSampleRate, kBlockSize, err);
        CHECK (inst2 != nullptr, "H3 determinism: second instance created");
        if (inst2 != nullptr)
        {
            const auto r2 = renderMelody (*inst2, nullptr);
            CHECK (buffersEqual (r2, render1),
                   "H3 determinism: fresh-instance re-render is byte-identical");
        }
    }

    // -- H4 automation -------------------------------------------------------
    {
        auto instA = fm.createPluginInstance (desc, kSampleRate, kBlockSize, err);
        auto instB = fm.createPluginInstance (desc, kSampleRate, kBlockSize, err);
        CHECK (instA != nullptr && instB != nullptr,
               "H4 automation: instances created");
        if (instA != nullptr && instB != nullptr)
        {
            auto* gA = findParam (*instA, "EQ Shelf Gain");
            auto* gB = findParam (*instB, "EQ Shelf Gain");
            CHECK (gA != nullptr && gB != nullptr,
                   "H4 automation: 'EQ Shelf Gain (dB)' parameter exposed to host");
            if (gA != nullptr && gB != nullptr)
            {
                const auto rA = renderMelody (*instA, gA);
                const auto rB = renderMelody (*instB, gB);
                CHECK (buffersEqual (rA, rB),
                       "H4 automation: identically-automated renders are byte-identical");
                const double hiPlain = bandRmsDb (render1, 3000.0, 12000.0);
                const double hiAuto  = bandRmsDb (rA,      3000.0, 12000.0);
                const double delta = hiAuto - hiPlain;
                CHECK (delta >= 6.0,
                       "H4 automation: +12 dB shelf ramp lifts 3-12 kHz band by "
                       << juce::String (delta, 2) << " dB (require >= 6)");
                writeWav (rA, outDir.getChildFile ("hostprobe_automated.wav"));
            }
        }
    }

    // -- H5 state round-trip -------------------------------------------------
    {
        auto* strike = findParam (*inst, "Strike Position");
        CHECK (strike != nullptr, "H5 state: 'Strike Position' parameter found");
        if (strike != nullptr)
        {
            // The parameter has a 0.01 plain-value step, so setValue may
            // legitimately SNAP (first probe run: normalised 0.42 came back
            // 0.422222 = plain 0.43). The state contract is therefore
            // "restore returns what the plug-in itself settled on after the
            // set", i.e. compare against the post-set READBACK, never the
            // raw request.
            strike->setValue (0.42f);
            const float settled = strike->getValue();
            juce::MemoryBlock state;
            inst->getStateInformation (state);
            CHECK (state.getSize() > 0, "H5 state: non-empty state captured ("
                   << (int) state.getSize() << " bytes)");
            const int capturedStateVersion = readStateVersion (state);
            CHECK (capturedStateVersion == kExpectedStateVersion,
                   "E14 state_version: captured state carries state_version="
                   << capturedStateVersion << " (require " << kExpectedStateVersion
                   << " = PluginProcessor.h kStateVersion; -1 = absent)");

            // The byte-identity claim is FRESH-vs-FRESH: two new instances
            // restored from the same state must render identically -- the
            // DAW semantic ("reload the project, play from bar 1, get the
            // same audio every time"). It is deliberately NOT live-vs-fresh:
            // the exciter noise seed advances a per-noteOn event counter
            // (successive strikes vary by design), and that live history is
            // intentionally not part of the state -- a probe run comparing a
            // twice-rendered live instance against a fresh restore diffs on
            // exactly that counter (2026-08-22 A12 follow-up).
            auto freshA = fm.createPluginInstance (desc, kSampleRate, kBlockSize, err);
            auto freshB = fm.createPluginInstance (desc, kSampleRate, kBlockSize, err);
            CHECK (freshA != nullptr && freshB != nullptr,
                   "H5 state: two fresh instances created");
            if (freshA != nullptr && freshB != nullptr)
            {
                freshA->setStateInformation (state.getData(), (int) state.getSize());
                freshB->setStateInformation (state.getData(), (int) state.getSize());
                auto* strike2 = findParam (*freshA, "Strike Position");
                CHECK (strike2 != nullptr
                       && std::abs (strike2->getValue() - settled) < 1.0e-6f,
                       "H5 state: parameter survives round-trip exactly (requested 0.42,"
                       " settled " << settled << ", restored "
                       << (strike2 != nullptr ? strike2->getValue() : -1.0f) << ")");
                const auto ra = renderMelody (*freshA, nullptr);
                const auto rb = renderMelody (*freshB, nullptr);
                CHECK (buffersEqual (ra, rb),
                       "H5 state: two restores of the same state render byte-identically");
                // WF0925-K1 (E14): re-captured AFTER the render comparison so
                // it cannot influence the byte-identity check above.
                juce::MemoryBlock restoredState;
                freshA->getStateInformation (restoredState);
                const int roundTripStateVersion = readStateVersion (restoredState);
                CHECK (capturedStateVersion == kExpectedStateVersion
                       && roundTripStateVersion == capturedStateVersion,
                       "E14 state_version: survives restore -> re-capture unchanged ("
                       << capturedStateVersion << " -> " << roundTripStateVersion << ")");
            }
        }
    }

    // -- H6 variable block size (WF0907-E10) ---------------------------------
    {
        // 64 first: it is the baseline every other size is diffed against
        // (WF0907-E10 design 2.1).
        constexpr int kSizes[] = { 64, 256, kBlockSize, 1024, 4096 };
        juce::AudioBuffer<float> baseline;
        std::cout << "\n-- H6 variable block size (sentinel melody) --\n";
        for (int size : kSizes)
        {
            auto sInst = fm.createPluginInstance (desc, kSampleRate, size, err);
            CHECK (sInst != nullptr,
                   "H6: fresh instance created for block size " << size);
            if (sInst == nullptr) continue;
            auto rendered = renderMelody (*sInst, nullptr, size);
            const auto wavFile = outDir.getChildFile (
                "h6_block_" + juce::String (size) + ".wav");
            CHECK (writeWav (rendered, wavFile),
                   "H6: WAV written for block size " << size << ": "
                   << wavFile.getFullPathName()
                   << " -- judged by melody_verify.py (GATE step, not this"
                      " program's exit code)");
            if (size == kSizes[0])
                baseline = rendered;
            else
                printBlockSizeDelta (baseline, rendered, kSizes[0], size,
                                     kRenderLenS);
        }

        // Hardened CHECK (WF0908-E10b 2.3; was informational-only under
        // WF0907-E10 -- see the H6 header comment's history). ChromaticEngine.h's
        // glide phase now advances and re-scales the resonator ONE SAMPLE AT
        // A TIME (block-size independent by construction), so this water_gong
        // Pitch Glide=1.0 sweep is now judged by the SAME "byte identical"
        // bar the plain kMelody sweep above already reaches -- not a new
        // tolerance (R2).
        std::cout << "\n-- H6 water_gong Pitch Glide=1.0 (hardened to CHECK,"
                     " WF0908-E10b) --\n";
        {
            static constexpr NoteSpec glideNote[] = { { 0.0, 55, 4.4, 0.7f } };
            juce::AudioBuffer<float> glideBaseline;
            for (int size : kSizes)
            {
                auto gInst = fm.createPluginInstance (desc, kSampleRate, size, err);
                CHECK (gInst != nullptr,
                       "H6 glide: fresh instance created for block size " << size);
                if (gInst == nullptr) continue;
                setChoiceParam (*gInst, "Engine", 1, 4);       // Chromatic
                setChoiceParam (*gInst, "Sub-Engine", 1, 3);   // Water Gong
                if (auto* glide = findParam (*gInst, "Pitch Glide"))
                    glide->setValue (1.0f);
                auto rendered = renderNotes (*gInst, nullptr, glideNote, 1,
                                             kRenderLenS, size);
                writeWav (rendered, outDir.getChildFile (
                    "h6_glide_block_" + juce::String (size) + ".wav"));
                if (size == kSizes[0])
                {
                    glideBaseline = rendered;
                }
                else
                {
                    printBlockSizeDelta (glideBaseline, rendered, kSizes[0],
                                         size, kRenderLenS);
                    const double maxAbs = maxAbsDeltaOverCore (glideBaseline,
                                                               rendered, kRenderLenS);
                    CHECK (maxAbs == 0.0,
                           "H6 glide: block " << size << " vs " << kSizes[0]
                           << " water_gong Pitch Glide=1.0 render is byte-identical"
                              " (max|delta|="
                           << juce::String (maxAbs * 8388608.0, 6)
                           << " LSB@24bit, require 0)");
                }
            }
        }
        std::cout << "\n-- H6 supplementary (informational only, not"
                     " melody_verify-judged): FM Piano high note (MIDI 96) --\n";
        {
            static constexpr NoteSpec pianoNote[] = { { 0.0, 96, 1.5, 0.7f } };
            juce::AudioBuffer<float> pianoBaseline;
            constexpr double kPianoLenS = 2.0;
            for (int size : kSizes)
            {
                auto pInst = fm.createPluginInstance (desc, kSampleRate, size, err);
                if (pInst == nullptr) continue;
                setChoiceParam (*pInst, "Engine", 2, 4);       // FM Piano
                auto rendered = renderNotes (*pInst, nullptr, pianoNote, 1,
                                             kPianoLenS, size);
                writeWav (rendered, outDir.getChildFile (
                    "h6_piano_block_" + juce::String (size) + ".wav"));
                if (size == kSizes[0])
                    pianoBaseline = rendered;
                else
                    printBlockSizeDelta (pianoBaseline, rendered, kSizes[0],
                                         size, kPianoLenS);
            }
        }
    }

    // -- H7 user preset round-trip, IR three-state hardened (WF0908-P3) -----
    // See the H7 comment block at the top of this file for the full
    // architecture rationale (why SAVE goes through a shadow APVTS, why LOAD
    // goes through a real VST3 instance, and how the no-GUI mismatch
    // scenario is simulated).
    std::cout << "\n-- H7 user preset round-trip --\n";
    {
        ShadowProcessor shadow;

        // >=10 non-default parameters spread across several groups (global /
        // macro / cimbalom / chromatic / reverb / eq) so the round-trip
        // check below is not trivially satisfied by defaults surviving
        // untouched.
        struct ParamSet { const char* id; float plainValue; };
        static const ParamSet kNonDefaults[] = {
            { "engine",           1.0f },    // Chromatic         (default 0)
            { "macro_material",   0.20f },   //                   (default 0.5)
            { "macro_tension",    0.85f },   //                   (default 0.5)
            { "macro_damping",    0.15f },   //                   (default 0.5)
            { "cim_strike_pos",   0.62f },   //                   (default 0.3)
            { "cim_diameter",     1.40f },   //                   (default 0.8)
            { "cim_detuning",    11.50f },   //                   (default 5.0)
            { "chr_strike_pos",   0.90f },   //                   (default 0.35)
            { "chr_thickness",    6.50f },   //                   (default 3.0)
            { "chr_pitch_glide",  0.77f },   //                   (default 0.0)
            { "fx_reverb_mix",    0.55f },   //                   (default 0.2)
            { "fx_reverb_mode",   1.0f },    // Impulse Response  (default 0; see IR checks below)
            { "fx_eq_gain",       9.00f },   //                   (default 0.0)
        };
        for (const auto& p : kNonDefaults)
            setApvtsParamPlain (shadow.apvts, p.id, p.plainValue);

        // Import a real (synthesized) IR fixture into the managed library so
        // SAVE can reference a genuine content hash and LOAD (through a real
        // VST3 instance) can resolve it via IRLibrary.h -- header-only, no
        // GUI dependency, same as PresetManager.h.
        const juce::File irSource = outDir.getChildFile ("h7_ir_source.wav");
        writeWav (makeImpulseFixture (2400, 1), irSource);
        juce::String importErr;
        const auto irRef = IRLibrary::importFile (irSource, importErr);
        CHECK (! irRef.sha256.isEmpty(),
               "H7: IR fixture imported into managed library (" << importErr << ")");

        // SAVE side: PresetManager stays IR-agnostic (PresetManager.h's
        // getExtraStateBlock/applyExtraStateBlock comment, WF0908-P3 §2.5)
        // -- this probe supplies the "reverb_ir" extra block directly,
        // exactly what TsukiSynthProcessor::buildReverbIRBlock() constructs
        // in the real product for the same imported IRRef.
        shadow.presetManager.getExtraStateBlock = [&irRef] () -> juce::ValueTree
        {
            juce::ValueTree v ("reverb_ir");
            v.setProperty ("kind", irRef.kind, nullptr);
            v.setProperty ("sha256", irRef.sha256, nullptr);
            v.setProperty ("original_name", irRef.originalName, nullptr);
            return v;
        };

        const juce::File presetDir = juce::File::getSpecialLocation (
                                          juce::File::userApplicationDataDirectory)
                                          .getChildFile ("TsukiSynth")
                                          .getChildFile ("Presets");
        std::cout << "  [INFO] preset directory: "
                  << presetDir.getFullPathName() << '\n';
        std::cout << "  [INFO] IR library directory: "
                  << IRLibrary::getDirectory().getFullPathName() << '\n';

        // allowOverwrite=true: survive a leftover file from a previous
        // interrupted probe run without a manual cleanup step.
        const bool saved = shadow.presetManager.saveUserPreset ("wf0908_h7", true);
        CHECK (saved, "H7: shadow PresetManager::saveUserPreset(\"wf0908_h7\","
                      " true) succeeded");

        const juce::File presetFile = presetDir.getChildFile ("wf0908_h7.tsukipreset");
        CHECK (presetFile.existsAsFile(),
               "H7: preset file written: " << presetFile.getFullPathName());

        const juce::String presetXmlText = presetFile.loadFileAsString();
        CHECK (presetXmlText.contains ("reverb_ir") && presetXmlText.contains (irRef.sha256),
               "H7: saved user preset's reverb_ir block records the imported IR's sha256"
               " (fx_reverb_mode was saved as Impulse Response)");

        // WF0925-K1 (E14): the existing v2 file format is written and read
        // back as 2 (PresetManager::kPresetFormatVersion) -- read-only query,
        // does not move the current index the cleanup below relies on.
        const int h7FormatVersion = shadow.presetManager.getUserPresetFormatVersion (
                                        shadow.presetManager.getCurrentIndex());
        CHECK (h7FormatVersion == 2,
               "E14 preset format: saved \"wf0908_h7\" file reads back as format version "
               << h7FormatVersion << " (require 2 = PresetManager::kPresetFormatVersion)");

        // Fresh VST3 instance whose ctor-time PresetManager::scanUserPresets()
        // sees the file just saved above, finds "wf0908_h7" by name, and
        // loads it via the real TsukiSynthProcessor::setCurrentProgram() ->
        // presetManager.loadPreset() code path.
        auto loadIntoFreshInstance = [&] () -> std::unique_ptr<juce::AudioPluginInstance>
        {
            juce::String createErr;
            auto instL = fm.createPluginInstance (desc, kSampleRate, kBlockSize, createErr);
            CHECK (instL != nullptr, "H7: fresh real VST3 instance created for LOAD side");
            if (instL == nullptr)
                return nullptr;
            int foundIndex = -1;
            const int numPrograms = instL->getNumPrograms();
            for (int i = 0; i < numPrograms; ++i)
                if (instL->getProgramName (i) == "wf0908_h7") { foundIndex = i; break; }
            CHECK (foundIndex >= 0,
                   "H7: \"wf0908_h7\" user preset visible to a fresh real VST3"
                   " instance's getProgramName() (scanned " << numPrograms << " programs)");
            if (foundIndex >= 0)
                instL->setCurrentProgram (foundIndex);
            return instL;
        };

        // -- scenario 1: 吻合 (resolve succeeds, content hash matches) -------
        std::cout << "\n  -- H7 scenario 1: matched --\n";
        if (auto instMatch = loadIntoFreshInstance())
        {
            // Index-based comparison over the shadow's own parameter COUNT
            // only (not requiring the loaded side's count to match): a
            // VST3-hosted juce::AudioPluginInstance's getParameters() is NOT
            // just the product's 60 parameters -- JUCE's VST3 wrapper
            // appends a synthesised Bypass parameter, a Program parameter,
            // and (with MIDI-CC-as-parameter support enabled) 16 channels x
            // 128 CCs = 2048 more (a probe run measured exactly
            // 60 + 2 + 2080 = 2142 total). Index 0..59 on BOTH sides is
            // guaranteed to be the SAME 60 product parameters in the SAME
            // order, because both shadow.apvts and the real plugin's apvts
            // are built by the identical
            // src/ParameterLayout.h::createTsukiParameterLayout(). The name
            // check below additionally guards against silent reordering.
            auto& shadowParams = shadow.getParameters();
            auto& loadedParams = instMatch->getParameters();
            CHECK (loadedParams.size() >= shadowParams.size(),
                   "H7: loaded real instance exposes at least the shadow's"
                   " " << shadowParams.size() << " product parameters ("
                   << loadedParams.size() << " total, incl. VST3-wrapper"
                   " extras -- Bypass/Program/MIDI CC)");

            int mismatches = 0, nameMismatches = 0;
            const int n = shadowParams.size();
            for (int i = 0; i < n && i < loadedParams.size(); ++i)
            {
                if (shadowParams[i]->getName (64) != loadedParams[i]->getName (64))
                {
                    ++nameMismatches;
                    std::cout << "    [name-diff] index " << i << ": shadow='"
                              << shadowParams[i]->getName (64) << "' loaded='"
                              << loadedParams[i]->getName (64) << "'\n";
                }
                const float a = shadowParams[i]->getValue();
                const float b = loadedParams[i]->getValue();
                if (std::abs (a - b) > 1.0e-6f)
                {
                    ++mismatches;
                    std::cout << "    [diff] index " << i << " '"
                              << shadowParams[i]->getName (64)
                              << "': shadow=" << a << " loaded=" << b << '\n';
                }
            }
            CHECK (nameMismatches == 0 && mismatches == 0
                   && loadedParams.size() >= shadowParams.size(),
                   "H7: setCurrentProgram(\"wf0908_h7\") on a real VST3"
                   " instance restores every one of " << n
                   << " product parameters bit-identical to the shadow"
                   " APVTS that saved it (" << mismatches << " value"
                   " mismatches, " << nameMismatches << " name mismatches)");

            juce::MemoryBlock state1raw;
            instMatch->getStateInformation (state1raw);
            const auto state1 = decodeVst3ProcessorState (state1raw);
            CHECK (memoryBlockContainsAscii (state1, "reverb_ir")
                   && memoryBlockContainsAscii (state1, irRef.sha256.toRawUTF8())
                   && memoryBlockContainsAscii (state1, "ir_missing=\"0\"")
                   && memoryBlockContainsAscii (state1, "ir_mismatch=\"0\""),
                   "H7 scenario 1 (matched): getStateInformation() carries a reverb_ir"
                   " block with the imported sha256, ir_missing=0, ir_mismatch=0 --"
                   " getIRStatus().loaded == effectChain.hasImpulseResponse() by"
                   " construction (PluginProcessor.h's IRStatus comment: single field,"
                   " not a second independently-tracked bool)");
            instMatch->releaseResources();
        }

        // -- scenario 3: 缺檔，無 GUI (resolve fails: the library's
        // filename-addressed file is removed) -----------------------------
        std::cout << "\n  -- H7 scenario 3: missing (no GUI) --\n";
        const auto libFile = IRLibrary::resolve (irRef);
        CHECK (libFile.existsAsFile(),
               "H7: IR fixture present in library before missing simulation");
        const auto hiddenFile = libFile.getSiblingFile (
            libFile.getFileNameWithoutExtension() + "_hidden.wav");
        const bool movedAway = libFile.existsAsFile() && libFile.moveFileTo (hiddenFile);
        CHECK (movedAway, "H7: library IR file moved aside to simulate a missing file");

        if (auto instMissing = loadIntoFreshInstance())
        {
            auto* modeParam = findParam (*instMissing, "Reverb Mode");
            CHECK (modeParam != nullptr && modeParam->getValue() < 0.5f,
                   "H7 scenario 3: fx_reverb_mode forced back to Algorithmic (0) --"
                   " red line 1, never keeps the instance's previous IR");

            juce::MemoryBlock state3raw;
            instMissing->getStateInformation (state3raw);
            const auto state3 = decodeVst3ProcessorState (state3raw);
            CHECK (! memoryBlockContainsAscii (state3, "reverb_ir")
                   && memoryBlockContainsAscii (state3, "ir_missing=\"1\""),
                   "H7 scenario 3 (missing, no GUI): getStateInformation() carries NO"
                   " reverb_ir block (red line 1: nothing is remembered as loaded) and"
                   " ir_missing=1 -- UI shows \"not loaded\", never claims IR while"
                   " audio silently runs algorithmic (red line 2)");
            instMissing->releaseResources();
        }

        // -- scenario 2: 指了別的檔 / 庫被改寫 (resolve finds A file by that
        // name, but its content hash no longer matches -- this card's
        // documented no-GUI simulation of "使用者指了別的檔", §2.5) --------
        std::cout << "\n  -- H7 scenario 2: mismatch (library index rewritten) --\n";
        const juce::File otherSource = outDir.getChildFile ("h7_ir_other.wav");
        writeWav (makeImpulseFixture (3600, 2), otherSource);
        const bool rewrote = otherSource.copyFileTo (libFile);
        CHECK (rewrote, "H7: library index rewritten -- different IR content placed at"
                        " the sha-named path the preset expects (simulates \"使用者指了"
                        "別的檔\", behaviourally identical from the processor's point of"
                        " view: loaded content whose hash disagrees with the recorded"
                        " identity)");

        if (auto instMismatch = loadIntoFreshInstance())
        {
            auto* modeParam = findParam (*instMismatch, "Reverb Mode");
            CHECK (modeParam != nullptr && modeParam->getValue() >= 0.5f,
                   "H7 scenario 2: fx_reverb_mode stays Impulse Response -- loaded anyway"
                   " per §2.3 row 2, mismatch does not silently fall back to algorithmic");

            juce::MemoryBlock state2raw;
            instMismatch->getStateInformation (state2raw);
            const auto state2 = decodeVst3ProcessorState (state2raw);
            CHECK (memoryBlockContainsAscii (state2, "reverb_ir")
                   && memoryBlockContainsAscii (state2, "ir_mismatch=\"1\""),
                   "H7 scenario 2 (mismatch): getStateInformation() carries a reverb_ir"
                   " block (something IS loaded, audio truth == UI truth) and"
                   " ir_mismatch=1 (UI would flag \"not the same IR as the preset\")");
            instMismatch->releaseResources();
        }

        // -- cleanup: remove everything this run created --------------------
        hiddenFile.deleteFile();
        libFile.deleteFile();
        IRLibrary::sidecarForSha (irRef.sha256).deleteFile();
        irSource.deleteFile();
        otherSource.deleteFile();

        const int cleanupIndex = shadow.presetManager.getCurrentIndex();
        const bool deleted = cleanupIndex >= 0
                                 && shadow.presetManager.deleteUserPreset (cleanupIndex);
        CHECK (deleted, "H7: cleanup -- PresetManager::deleteUserPreset() removed"
                        " \"wf0908_h7\" (" << presetFile.getFullPathName() << ")");
        CHECK (! presetFile.existsAsFile(),
               "H7: cleanup -- preset file no longer on disk");
    }

    // -- E14 newer user-preset file format (WF0925-K1) -------------------------
    // A preset FILE claiming a format version newer than this build knows
    // (PresetManager::kPresetFormatVersion = 2). Contract under test (see
    // PresetManager.h): still listed and loaded -- parameters are read by ID,
    // as for v1/v2 -- but saveUserPreset() refuses to overwrite it, so a
    // newer build's file is never silently rewritten in the older format.
    // Own ShadowProcessor, separate from H7's, so H7's index-based cleanup
    // above is unaffected.
    std::cout << "\n-- E14 newer user-preset file format --\n";
    {
        ShadowProcessor shadowF;
        const juce::File futureFile = juce::File::getSpecialLocation (
                                           juce::File::userApplicationDataDirectory)
                                           .getChildFile ("TsukiSynth")
                                           .getChildFile ("Presets")
                                           .getChildFile ("wf0925_k1_future.tsukipreset");

        // Non-default value (default 0.3) so a successful load is observable.
        setApvtsParamPlain (shadowF.apvts, "cim_strike_pos", 0.62f);
        auto* strikeF = shadowF.apvts.getParameter ("cim_strike_pos");
        const float savedNorm = strikeF != nullptr ? strikeF->getValue() : -1.0f;

        juce::XmlElement root ("TsukiSynthPreset");
        root.setAttribute ("name", "wf0925_k1_future");
        root.setAttribute ("id", "wf0925-k1-future");
        root.setAttribute ("version", 99);
        root.addChildElement (shadowF.apvts.copyState().createXml().release());
        const bool wroteFuture = root.writeTo (futureFile);
        CHECK (wroteFuture, "E14 preset format: version=99 preset file written ("
                            << futureFile.getFullPathName() << ")");
        const juce::String futureTextBefore = futureFile.loadFileAsString();

        setApvtsParamPlain (shadowF.apvts, "cim_strike_pos", 0.3f);   // back to default
        shadowF.presetManager.scanUserPresets();
        int futureIndex = -1;
        for (int i = 0; i < shadowF.presetManager.getNumPresets(); ++i)
            if (shadowF.presetManager.getPresetName (i) == "wf0925_k1_future")
                { futureIndex = i; break; }
        CHECK (futureIndex >= 0
               && shadowF.presetManager.getUserPresetFormatVersion (futureIndex) == 99,
               "E14 preset format: newer-format file still listed after rescan, version read as "
               << shadowF.presetManager.getUserPresetFormatVersion (futureIndex));

        const bool loadedFuture = futureIndex >= 0
                                  && shadowF.presetManager.loadPreset (futureIndex);
        const float loadedNorm = strikeF != nullptr ? strikeF->getValue() : -2.0f;
        // 1e-6 on the normalised value: the same bar H7's shadow-vs-loaded
        // comparison above already uses (not a new tolerance, R2).
        CHECK (loadedFuture && std::abs (loadedNorm - savedNorm) < 1.0e-6f,
               "E14 preset format: newer-format preset loads and its parameters are read"
               " (cim_strike_pos normalised saved " << savedNorm << ", loaded "
               << loadedNorm << ")");

        const bool overwrote = shadowF.presetManager.saveUserPreset ("wf0925_k1_future", true);
        CHECK (! overwrote && futureFile.loadFileAsString() == futureTextBefore,
               "E14 preset format: saveUserPreset(allowOverwrite=true) refuses to overwrite"
               " the newer-format file (returned " << (overwrote ? "true" : "false")
               << ", file bytes unchanged)");

        futureFile.deleteFile();
        shadowF.presetManager.scanUserPresets();
        CHECK (! futureFile.existsAsFile(),
               "E14 preset format: cleanup -- newer-format test file removed");
    }

    // -- D12 legacy reverb_ir_path migration (WF0914-D12) --------------------
    // See docs/workcards/WF0914_D12_state_migration.md §1/§2 and this file's
    // buildLegacyMigrationStateBlob() comment for the full rationale.
    // Exercises TsukiSynthProcessor::migrateLegacyReverbIRPath() through the
    // same real VST3-ABI setStateInformation() path H7 already validates the
    // "reverb_ir" schema through, feeding it a synthetic pre-F-03 state blob
    // (bare "reverb_ir_path" property, no "reverb_ir" block) in place of a
    // real old project file -- no such file exists to load from disk.
    std::cout << "\n-- D12 legacy reverb_ir_path migration --\n";
    {
        // Template instance: its own getStateInformation() output is what
        // buildLegacyMigrationStateBlob() edits. A fresh default state has
        // no "reverb_ir" block, matching every pre-F-03 project (the new
        // schema did not exist yet when such a project was last saved).
        juce::String sourceErr;
        auto sourceInst = fm.createPluginInstance (desc, kSampleRate, kBlockSize, sourceErr);
        CHECK (sourceInst != nullptr, "D12: template instance created for building"
                                      " synthetic legacy state blobs");

        if (sourceInst != nullptr)
        {
            // -- scenario 1: 檔案存在 -> 正常 IRLibrary 匯入，等同使用者手動
            // 載入該 .wav (workcard §1 item 1) --------------------------------
            std::cout << "\n  -- D12 scenario 1: legacy path resolves to a file --\n";
            const juce::File legacySource = outDir.getChildFile ("d12_legacy_ir_source.wav");
            writeWav (makeImpulseFixture (2000, 3), legacySource);
            const auto expectedSha = IRLibrary::hashFile (legacySource);
            CHECK (expectedSha.isNotEmpty(),
                   "D12: legacy IR source fixture hashes ("
                   << legacySource.getFullPathName() << ")");

            IRLibrary::IRRef expectedRef;
            expectedRef.sha256 = expectedSha;
            CHECK (! IRLibrary::resolve (expectedRef).existsAsFile(),
                   "D12: legacy IR source not yet in the managed library"
                   " (migration must import it itself, not assume it's already there)");

            const auto blob1 = buildLegacyMigrationStateBlob (
                *sourceInst, legacySource.getFullPathName(), true, nullptr);
            CHECK (blob1.getSize() > 0, "D12 scenario 1: synthetic legacy state blob built");

            juce::String err1;
            auto inst1 = fm.createPluginInstance (desc, kSampleRate, kBlockSize, err1);
            CHECK (inst1 != nullptr, "D12 scenario 1: fresh real VST3 instance created");
            if (inst1 != nullptr)
            {
                inst1->setStateInformation (blob1.getData(), (int) blob1.getSize());

                // Audit fix (WF0914 D12 re-review): the synthetic source
                // state's own fx_reverb_mode is left at its default
                // (Algorithmic, ParameterLayout.cpp choice index 0) -- a
                // real achievable pre-F-03 project (user loaded an IR, then
                // switched back to Algorithmic, then saved; the old
                // reverb_ir_path key was written independently of the mode
                // parameter -- see `git show 31eb7ae^:src/PluginProcessor.cpp`
                // lines 699-700/743-745). Migration must import the file and
                // populate the new schema WITHOUT force-switching the mode
                // the saved state already carries -- that would silently
                // overwrite the user's own choice, matching neither the
                // pre-F-03 removed code (which passed
                // `/*switchModeToIR*/ false`) nor this card's own goal of
                // not silently discarding saved user state.
                auto* modeParam = findParam (*inst1, "Reverb Mode");
                CHECK (modeParam != nullptr && modeParam->getValue() < 0.5f,
                       "D12 scenario 1: fx_reverb_mode left as the saved state had it"
                       " (Algorithmic) -- migration imports the IR but does not"
                       " force-switch the mode (switchModeToIR=false), matching the"
                       " removed pre-F-03 code's own choice");

                juce::MemoryBlock state1raw;
                inst1->getStateInformation (state1raw);
                const auto state1 = decodeVst3ProcessorState (state1raw);
                CHECK (memoryBlockContainsAscii (state1, "<reverb_ir ")
                       && memoryBlockContainsAscii (state1, expectedSha.toRawUTF8())
                       && memoryBlockContainsAscii (state1, "ir_missing=\"0\""),
                       "D12 scenario 1: migrated state carries a reverb_ir block with the"
                       " legacy file's own content hash and ir_missing=0 -- resolved"
                       " through the managed library exactly like a fresh GUI import");
                CHECK (IRLibrary::resolve (expectedRef).existsAsFile(),
                       "D12 scenario 1: legacy IR now present in the managed library"
                       " under its content hash (hash/dedupe/kind=user, workcard §1 item 1)");
                // WF0925-K1 (staged-review:D12-legacykey): the consumed legacy
                // key must not linger in what this session saves next.
                CHECK (! memoryBlockContainsAscii (state1, "reverb_ir_path"),
                       "D12 scenario 1: migrated output state no longer carries"
                       " reverb_ir_path (consumed legacy key dropped, PluginProcessor.cpp"
                       " tree.removeProperty)");
                // WF0925-K1 (E14): the input had no state_version (pre-K1
                // state -> unchanged D12 path); what this build writes back
                // is tagged with its own format version.
                const int migratedVersion1 = readStateVersion (state1raw);
                CHECK (migratedVersion1 == kExpectedStateVersion,
                       "E14 state_version: an unversioned (pre-K1) state still migrates"
                       " and is re-saved as state_version=" << migratedVersion1
                       << " (require " << kExpectedStateVersion << ")");
                CHECK (memoryBlockContainsAscii (state1, "presetDirty=\"1\""),
                       "D12 scenario 1 (audit fix): migrated state is marked dirty --"
                       " a migration silently changes in-memory state (new reverb_ir"
                       " block) that no longer matches the bytes on disk, so it must"
                       " not come back as \"not dirty\" (setStateInformation() runs"
                       " presetManager.setDirty() after restoreDirty() when migration"
                       " ran, so restoreDirty()'s read of the OLD presetDirty=0 does"
                       " not silently survive)");

                inst1->releaseResources();
            }

            IRLibrary::fileForSha (expectedSha).deleteFile();
            IRLibrary::sidecarForSha (expectedSha).deleteFile();
            legacySource.deleteFile();

            // -- scenario 2: 檔案不存在 -> F-03 缺檔三態，不安靜留 algorithmic
            // (workcard §1 item 2) -------------------------------------------
            std::cout << "\n  -- D12 scenario 2: legacy path does not resolve --\n";
            const juce::File missingSource = outDir.getChildFile ("d12_legacy_ir_missing.wav");
            missingSource.deleteFile();   // guarantee it does not exist
            CHECK (! missingSource.existsAsFile(),
                   "D12: legacy IR source deliberately absent for scenario 2");

            const auto blob2 = buildLegacyMigrationStateBlob (
                *sourceInst, missingSource.getFullPathName(), true, nullptr);
            CHECK (blob2.getSize() > 0, "D12 scenario 2: synthetic legacy state blob built");

            juce::String err2;
            auto inst2 = fm.createPluginInstance (desc, kSampleRate, kBlockSize, err2);
            CHECK (inst2 != nullptr, "D12 scenario 2: fresh real VST3 instance created");
            if (inst2 != nullptr)
            {
                inst2->setStateInformation (blob2.getData(), (int) blob2.getSize());

                auto* modeParam = findParam (*inst2, "Reverb Mode");
                CHECK (modeParam != nullptr && modeParam->getValue() < 0.5f,
                       "D12 scenario 2: fx_reverb_mode forced to Algorithmic -- F-03's"
                       " normal missing-IR path (§2.3 row 3), not the silent"
                       " \"leave algorithmic without saying anything\" this card exists"
                       " to remove (workcard §1 item 2)");

                juce::MemoryBlock state2raw;
                inst2->getStateInformation (state2raw);
                const auto state2 = decodeVst3ProcessorState (state2raw);
                CHECK (! memoryBlockContainsAscii (state2, "<reverb_ir ")
                       && memoryBlockContainsAscii (state2, "ir_missing=\"1\""),
                       "D12 scenario 2: migrated state carries NO reverb_ir block (red"
                       " line 1: nothing remembered as loaded) and ir_missing=1 -- the"
                       " same three-state \"missing\" signature H7 scenario 3 validates"
                       " for the new schema, now also reached from the legacy key");
                // WF0925-K1 (staged-review:D12-legacykey): dropped on the
                // missing-file path too (recorded via expectedIRRef instead).
                CHECK (! memoryBlockContainsAscii (state2, "reverb_ir_path"),
                       "D12 scenario 2: migrated output state no longer carries"
                       " reverb_ir_path (consumed legacy key dropped even when the"
                       " file is missing)");
                CHECK (memoryBlockContainsAscii (state2, "presetDirty=\"1\""),
                       "D12 scenario 2 (audit fix): migrated state is marked dirty even"
                       " on the missing-file path -- fx_reverb_mode was force-changed to"
                       " Algorithmic and a warning raised, which also diverges from the"
                       " bytes on disk");

                inst2->releaseResources();
            }

            // -- scenario 3: 新 schema 已存在 -> 舊鍵忽略，不重複匯入
            // (workcard §1 item 3) --------------------------------------------
            std::cout << "\n  -- D12 scenario 3: reverb_ir already present, legacy key"
                         " ignored --\n";
            const juce::File irASource = outDir.getChildFile ("d12_irA_source.wav");
            writeWav (makeImpulseFixture (2200, 4), irASource);
            juce::String importErrA;
            const auto irRefA = IRLibrary::importFile (irASource, importErrA);
            CHECK (! irRefA.sha256.isEmpty(),
                   "D12: IR-A imported into managed library (" << importErrA << ")");

            const juce::File irBSource = outDir.getChildFile ("d12_irB_source.wav");
            writeWav (makeImpulseFixture (2600, 5), irBSource);
            const auto irBSha = IRLibrary::hashFile (irBSource);
            IRLibrary::IRRef irBRef;
            irBRef.sha256 = irBSha;
            CHECK (! IRLibrary::resolve (irBRef).existsAsFile(),
                   "D12: IR-B not in the managed library before scenario 3"
                   " (must stay that way -- migration must not run)");

            const auto blob3 = buildLegacyMigrationStateBlob (
                *sourceInst, irBSource.getFullPathName(), false, &irRefA);
            CHECK (blob3.getSize() > 0, "D12 scenario 3: synthetic state blob built"
                                        " (reverb_ir=IR-A + legacy reverb_ir_path=IR-B)");

            juce::String err3;
            auto inst3 = fm.createPluginInstance (desc, kSampleRate, kBlockSize, err3);
            CHECK (inst3 != nullptr, "D12 scenario 3: fresh real VST3 instance created");
            if (inst3 != nullptr)
            {
                inst3->setStateInformation (blob3.getData(), (int) blob3.getSize());

                juce::MemoryBlock state3raw;
                inst3->getStateInformation (state3raw);
                const auto state3 = decodeVst3ProcessorState (state3raw);
                CHECK (memoryBlockContainsAscii (state3, "<reverb_ir ")
                       && memoryBlockContainsAscii (state3, irRefA.sha256.toRawUTF8())
                       && ! memoryBlockContainsAscii (state3, irBSha.toRawUTF8())
                       && memoryBlockContainsAscii (state3, "ir_missing=\"0\""),
                       "D12 scenario 3: migrated state still carries IR-A's own sha256 (the"
                       " new schema's identity), never IR-B's -- legacy reverb_ir_path is"
                       " ignored once a reverb_ir block already exists (workcard §1 item 3)");
                CHECK (! IRLibrary::resolve (irBRef).existsAsFile(),
                       "D12 scenario 3: IR-B still absent from the managed library --"
                       " migrateLegacyReverbIRPath() never ran, no import happened");
                CHECK (memoryBlockContainsAscii (state3, "presetDirty=\"0\""),
                       "D12 scenario 3 (audit fix contrast): migration never ran, so"
                       " unlike scenarios 1/2 the dirty flag is untouched by D12 code --"
                       " confirms the setDirty() call in setStateInformation() is gated"
                       " on migratedLegacyIR actually having run, not unconditional");

                inst3->releaseResources();
            }

            IRLibrary::fileForSha (irRefA.sha256).deleteFile();
            IRLibrary::sidecarForSha (irRefA.sha256).deleteFile();
            irASource.deleteFile();
            irBSource.deleteFile();

            // -- E14 (WF0925-K1): state claiming a NEWER state_version --------
            // Contract (PluginProcessor.cpp setStateInformation()): no crash,
            // everything this build understands is read as usual, the D12
            // legacy migration is conservatively skipped, and the next save
            // is tagged with this build's own version (never echoes 99).
            std::cout << "\n  -- E14: state_version newer than this build knows --\n";
            auto* srcStrike = findParam (*sourceInst, "Strike Position");
            if (srcStrike != nullptr)
                srcStrike->setValue (0.55f);
            const float srcSettled = srcStrike != nullptr ? srcStrike->getValue() : -1.0f;

            const juce::File futureIRSource = outDir.getChildFile ("e14_future_state_ir.wav");
            writeWav (makeImpulseFixture (2400, 6), futureIRSource);
            IRLibrary::IRRef futureIRRef;
            futureIRRef.sha256 = IRLibrary::hashFile (futureIRSource);
            CHECK (futureIRRef.sha256.isNotEmpty()
                   && ! IRLibrary::resolve (futureIRRef).existsAsFile(),
                   "E14: legacy-key IR fixture exists on disk and is not yet in the managed"
                   " library (so a skipped migration is observable)");

            const auto blob4 = buildLegacyMigrationStateBlob (
                *sourceInst, futureIRSource.getFullPathName(), true, nullptr, 99);
            CHECK (blob4.getSize() > 0 && readStateVersion (blob4) == 99,
                   "E14: synthetic state blob built with state_version=99 + legacy"
                   " reverb_ir_path (read back " << readStateVersion (blob4) << ")");

            juce::String err4;
            auto inst4 = fm.createPluginInstance (desc, kSampleRate, kBlockSize, err4);
            CHECK (inst4 != nullptr, "E14: fresh real VST3 instance created");
            if (inst4 != nullptr)
            {
                inst4->setStateInformation (blob4.getData(), (int) blob4.getSize());

                auto* strike4 = findParam (*inst4, "Strike Position");
                CHECK (strike4 != nullptr
                       && std::abs (strike4->getValue() - srcSettled) < 1.0e-6f,
                       "E14: newer-version state loads without crashing and its parameters"
                       " are read (Strike Position settled " << srcSettled << ", restored "
                       << (strike4 != nullptr ? strike4->getValue() : -1.0f)
                       << "; same 1e-6 bar as H5)");

                juce::MemoryBlock state4raw;
                inst4->getStateInformation (state4raw);
                const auto state4 = decodeVst3ProcessorState (state4raw);
                const int resavedVersion = readStateVersion (state4raw);
                CHECK (state4.getSize() > 0 && resavedVersion == kExpectedStateVersion,
                       "E14: re-saved state is tagged with this build's own format version "
                       << resavedVersion << " (require " << kExpectedStateVersion
                       << ", never the loaded 99)");
                CHECK (! memoryBlockContainsAscii (state4, "<reverb_ir ")
                       && memoryBlockContainsAscii (state4, "ir_missing=\"0\"")
                       && ! IRLibrary::resolve (futureIRRef).existsAsFile(),
                       "E14: D12 legacy migration conservatively skipped for a newer-version"
                       " state -- no reverb_ir block, ir_missing=0 (no missing-IR path"
                       " either), IR not imported into the managed library");

                inst4->releaseResources();
            }

            IRLibrary::fileForSha (futureIRRef.sha256).deleteFile();   // only if a failure imported it
            IRLibrary::sidecarForSha (futureIRRef.sha256).deleteFile();
            futureIRSource.deleteFile();

            sourceInst->releaseResources();
        }
    }

    // -- H8 tail length (WF0907-E5) ------------------------------------------
    {
        MaterialDB matDB;
        // WF0925-K2: cwd first, then TSUKI_REPO_ROOT, then the executable's
        // ancestors -- see findMaterialsJson(). The path used is printed.
        const MaterialsLookup materialsLookup = findMaterialsJson();
        const juce::File materialsFile = materialsLookup.file;
        std::cout << "  H8 materials.json used: " << materialsFile.getFullPathName()
                  << " (" << materialsLookup.via << ")\n";
        const bool matLoaded = matDB.loadFromFile (materialsFile);
        CHECK (matLoaded, "H8 tail: MaterialDB loads " << materialsFile.getFullPathName());

        struct Preset { const char* label; int engineIdx; bool isChromatic; int subEngineIdx; };
        const Preset presets[] = {
            { "cimbalom",    0, false, 0 },
            { "tongue_drum", 1, true,  0 },
            { "water_gong",  1, true,  1 },
        };

        for (const auto& preset : presets)
        {
            auto pinst = fm.createPluginInstance (desc, kSampleRate, kBlockSize, err);
            CHECK (pinst != nullptr,
                   juce::String ("H8 tail: instance created for ") + preset.label);
            if (pinst == nullptr) continue;

            setChoiceParam (*pinst, "Engine", preset.engineIdx, 4);
            if (preset.isChromatic)
                setChoiceParam (*pinst, "Sub-Engine", preset.subEngineIdx, 3);
            pinst->prepareToPlay (kSampleRate, kBlockSize);

            const double hostTail = pinst->getTailLengthSeconds();
            const double engineWorst = matLoaded
                ? (preset.isChromatic
                       ? defaultChromaticWorstCaseTail (matDB, preset.subEngineIdx)
                       : defaultCimbalomWorstCaseTail (matDB))
                : -1.0;
            CHECK (matLoaded && hostTail >= engineWorst,
                   "H8 tail: " << preset.label << " getTailLengthSeconds()=" << hostTail
                   << "s >= engine worstCaseTailSeconds()=" << engineWorst << "s");
            pinst->releaseResources();
        }

        // Tongue Drum default preset measured T60 30.18 s
        // (docs/AUDIT_STRUCTURAL_FINDINGS_2026-08-31.zh-TW.md §1). Confirm a
        // held note (no note-off -- see renderSustainedNote()) is genuinely
        // still audible at 10 s AND that the host-facing number promises at
        // least that much, tying the two together rather than trusting
        // either in isolation.
        auto tdInst = fm.createPluginInstance (desc, kSampleRate, kBlockSize, err);
        CHECK (tdInst != nullptr, "H8 tail: tongue_drum sustain instance created");
        if (tdInst != nullptr)
        {
            setChoiceParam (*tdInst, "Engine", 1, 4);
            setChoiceParam (*tdInst, "Sub-Engine", 0, 3);

            const auto sustainRender = renderSustainedNote (*tdInst, 40, 0.7f, 11.0);
            const float peak = sustainRender.getMagnitude (0, sustainRender.getNumSamples());
            const int tailStartSample = (int) (10.0 * kSampleRate);
            const int tailLenSamples  = sustainRender.getNumSamples() - tailStartSample;
            double tailRms = 0.0;
            if (tailLenSamples > 0)
            {
                double acc = 0.0;
                for (int c = 0; c < sustainRender.getNumChannels(); ++c)
                {
                    const float* d = sustainRender.getReadPointer (c, tailStartSample);
                    for (int i = 0; i < tailLenSamples; ++i)
                        acc += (double) d[i] * d[i];
                }
                tailRms = std::sqrt (acc / (double) (tailLenSamples * sustainRender.getNumChannels()));
            }
            const double tailRelDb = 20.0 * std::log10 (juce::jmax (tailRms, 1e-12)
                                                        / juce::jmax ((double) peak, 1e-12));
            CHECK (tailRelDb > -60.0,
                   "H8 tail: tongue_drum MIDI 40 tail RMS at 10s = "
                   << juce::String (tailRelDb, 2)
                   << " dB relative to peak (require > -60, -60dB IS the T60 definition)");

            const double tdHostTail = tdInst->getTailLengthSeconds();
            CHECK (tdHostTail > 10.0,
                   "H8 tail: tongue_drum still audibly ringing at 10s -> "
                   "getTailLengthSeconds()=" << tdHostTail << "s (require > 10)");

            writeWav (sustainRender, outDir.getChildFile ("hostprobe_tail_tongue_drum.wav"));
            tdInst->releaseResources();
        }
    }

    // -- E16 factory presets (WF0925-K2, engineering-gaps:E16) --------------
    // PresetManager::loadFactoryPreset() silently SKIPS any paramID that
    // apvts.getParameter() cannot resolve (src/PresetManager.h, the
    // `if (auto* param = apvts.getParameter (entry.paramID))` loop), so a
    // typo in src/Presets.h would ship a preset that quietly ignores that
    // setting. For every factory preset this block:
    //   (a) resolves each of its paramIDs against a ShadowProcessor APVTS --
    //       built from the SAME createTsukiParameterLayout() the product's
    //       TsukiSynthProcessor uses (see ShadowProcessor above) -- and
    //       requires every one to resolve;
    //   (b) creates a FRESH real VST3 instance, requires program i to carry
    //       that preset's name and, after setCurrentProgram(i), to report i
    //       as current (exact integer/string equality, no tolerance);
    //   (c) renders C4 (MIDI 60, vel 0.7, note-off at 1.0 s, 2.0 s total)
    //       with the preset's parameters untouched and requires every output
    //       sample to be finite.
    // Per the 09-25 status check's E16 correction (查證修正), NO peak ceiling
    // and NO silence/RMS floor are asserted -- those would be new judgment
    // thresholds (R2/R4) awaiting 月月's decision. Peak and RMS are PRINTED
    // for each preset, descriptive only, not a GATE.
    {
        std::cout << "\n  -- E16 factory presets --\n";
        int factoryCount = 0;
        const FactoryPreset* factory = getFactoryPresetList (factoryCount);
        std::cout << "  E16: src/Presets.h registers " << factoryCount
                  << " factory presets\n";
        ShadowProcessor e16Shadow;
        // Negative control: the resolver used in (a) must be able to say
        // "no" -- an ID that is not in the layout must NOT resolve.
        CHECK (e16Shadow.apvts.getParameter ("wf0925_k2_no_such_param") == nullptr,
               "E16 negative control: a paramID absent from createTsukiParameterLayout()"
               " does not resolve");

        for (int i = 0; i < factoryCount; ++i)
        {
            const FactoryPreset& fp = factory[i];
            const juce::String presetLabel = "E16 factory preset " + juce::String (i)
                                           + " '" + juce::String (fp.name) + "'";

            juce::StringArray unresolved;
            for (int k = 0; k < fp.numParams; ++k)
                if (e16Shadow.apvts.getParameter (fp.params[k].paramID) == nullptr)
                    unresolved.add (fp.params[k].paramID);
            CHECK (unresolved.isEmpty(),
                   presetLabel << ": all " << fp.numParams
                   << " paramIDs resolve in createTsukiParameterLayout()"
                   << (unresolved.isEmpty()
                           ? juce::String()
                           : " (UNRESOLVED: " + unresolved.joinIntoString (", ") + ")"));

            auto pinst = fm.createPluginInstance (desc, kSampleRate, kBlockSize, err);
            CHECK (pinst != nullptr, presetLabel << ": fresh VST3 instance created");
            if (pinst == nullptr)
                continue;

            const juce::String vstName = i < pinst->getNumPrograms()
                                             ? pinst->getProgramName (i) : juce::String();
            pinst->setCurrentProgram (i);
            const int currentProgram = pinst->getCurrentProgram();
            CHECK (vstName == juce::String (fp.name) && currentProgram == i,
                   presetLabel << ": VST3 program " << i << " is named '" << vstName
                   << "' and setCurrentProgram(" << i << ") -> getCurrentProgram()="
                   << currentProgram);

            const auto render = renderNoteAsLoaded (*pinst, 60, 0.7f, 1.0, 2.0);
            long long nonFinite = 0;
            double peak = 0.0, sumSq = 0.0;
            long long finiteCount = 0;
            for (int c = 0; c < render.getNumChannels(); ++c)
            {
                const float* d = render.getReadPointer (c);
                for (int s = 0; s < render.getNumSamples(); ++s)
                {
                    if (! std::isfinite (d[s])) { ++nonFinite; continue; }
                    peak = juce::jmax (peak, (double) std::abs (d[s]));
                    sumSq += (double) d[s] * d[s];
                    ++finiteCount;
                }
            }
            const long long totalSamples = (long long) render.getNumChannels()
                                         * render.getNumSamples();
            CHECK (nonFinite == 0,
                   presetLabel << ": C4 render, all " << totalSamples
                   << " output samples finite (non-finite: " << nonFinite << ")");

            const double rms = finiteCount > 0 ? std::sqrt (sumSq / (double) finiteCount) : 0.0;
            std::cout << "    [info] " << presetLabel << ": peak "
                      << juce::String (20.0 * std::log10 (juce::jmax (peak, 1.0e-12)), 2)
                      << " dBFS, RMS "
                      << juce::String (20.0 * std::log10 (juce::jmax (rms, 1.0e-12)), 2)
                      << " dBFS (descriptive only, not a GATE; 1e-12 floor = -240 dB"
                         " printed for digital silence)\n";
        }
    }

    std::cout << (failures == 0 ? "PASS" : "FAIL") << " ("
              << failures << " failures)\n";
    return failures == 0 ? 0 : 1;
}
