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
//
// HONEST SCOPE: this is a JUCE host, not Cubase. It proves VST3-contract
// behaviour of the shipped binary; Cubase-specific behaviour is L3
// (tools/cubase_scan_verify.py = scan; AI-driven export = playback).
//
// Usage: TsukiSynthHostProbe <path-to-TsukiSynth.vst3> <out-dir>
// Exit 0 = all checks pass.

#include <juce_audio_processors/juce_audio_processors.h>
#include <juce_audio_formats/juce_audio_formats.h>
#include <juce_events/juce_events.h>
#include <juce_dsp/juce_dsp.h>
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

// Renders kMelody through `inst`. If eqGain != nullptr, ramps it linearly
// 0 -> 1 (normalised) across the render, one step per block, BEFORE each
// processBlock -- a deterministic stand-in for a DAW automation lane.
juce::AudioBuffer<float> renderMelody (juce::AudioPluginInstance& inst,
                                       juce::AudioProcessorParameter* eqGain)
{
    // The sentinel score declares an FX-FREE render (reverb/delay wet 0),
    // but the plug-in's APVTS default is fx_reverb_mix = 0.2 -- a creative
    // default, not part of the melody-position claim. Left on, its build-up
    // registered phantom band rises ~80 ms after strikes (first probe run,
    // 2026-08-20). Zero it so host renders match the fixture's declaration,
    // exactly as a DAW project for this test would.
    if (auto* rev = findParam (inst, "Reverb Mix"))
        rev->setValue (0.0f);
    const int totalSamples = (int) (kRenderLenS * kSampleRate);
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
        const int blockStart = b * kBlockSize;
        midi.clear();
        for (const auto& n : kMelody)
        {
            const int on  = (int) std::llround (n.time * kSampleRate);
            const int off = (int) std::llround ((n.time + n.durS) * kSampleRate);
            if (on >= blockStart && on < blockStart + kBlockSize)
                midi.addEvent (juce::MidiMessage::noteOn  (1, n.midi, n.vel),
                               on - blockStart);
            if (off >= blockStart && off < blockStart + kBlockSize)
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
                          juce::jmin (c, chans - 1), 0, kBlockSize);
    }
    inst.releaseResources();
    return out;
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
            }
        }
    }

    std::cout << (failures == 0 ? "PASS" : "FAIL") << " ("
              << failures << " failures)\n";
    return failures == 0 ? 0 : 1;
}
