#include "dsp/AudioFIFO.h"
#include "dsp/Envelope.h"
#include "engines/ChromaticEngine.h"
#include "score/ScoreParser.h"
#include "score/ScoreRenderer.h"
#include "score/WavWriter.h"

#include <cmath>
#include <cstdio>
#include <memory>
#include <string>
#include <utility>
#include <vector>

namespace
{
int failures = 0;

#define CHECK(condition, message)                                      \
    do                                                                 \
    {                                                                  \
        if (condition)                                                 \
            std::printf ("[PASS] %s\n", message);                      \
        else                                                           \
        {                                                              \
            std::printf ("[FAIL] %s\n", message);                      \
            ++failures;                                                \
        }                                                              \
    } while (false)

std::unique_ptr<juce::AudioFormatReader> openAudioFile (
    const juce::File& file)
{
    juce::AudioFormatManager manager;
    manager.registerBasicFormats();
    return std::unique_ptr<juce::AudioFormatReader> (
        manager.createReaderFor (file));
}

void loadTestMaterial (MaterialDB& materials)
{
    const auto json = R"json({"materials":{"steel":{"display_name":"Steel","density":7800,"youngs_modulus":200000000000,"poisson_ratio":0.29,"damping":{"alpha":0.0238,"beta_air":0.00000012,"gamma_radiation":0.00002}}}})json";
    CHECK (materials.loadFromString (json), "Test material database loads");
}

void testMaterialDatabaseIsTransactional()
{
    MaterialDB materials;
    loadTestMaterial (materials);
    const int originalSize = materials.size();
    const auto invalid = R"json({"materials":{"bad":{"display_name":"Bad","density":0,"youngs_modulus":1,"poisson_ratio":0.6,"damping":{"alpha":-1,"beta_air":0,"gamma_radiation":0}}}})json";
    CHECK (! materials.loadFromString (invalid),
           "MaterialDB rejects non-physical material constants");
    CHECK (materials.size() == originalSize
           && materials.getMaterial ("steel") != nullptr,
           "Failed material reload preserves the last known-good database");
}

void testEnvelopeRelease()
{
    Envelope env;
    env.setSampleRate (1000.0);
    env.setAttack (0.001f);
    env.setDecay (0.001f);
    env.setSustain (1.0f);
    env.setRelease (0.5f);
    env.noteOn();
    env.getNextSample();
    env.noteOff();

    for (int i = 0; i < 499; ++i)
        env.getNextSample();

    CHECK (env.isActive(), "Envelope remains active before release time");
    env.getNextSample();
    CHECK (! env.isActive(), "Envelope ends at the configured release time");
}

void testAudioFifoKeepsNewestUnreadData()
{
    AudioFIFO fifo (4);
    const float first[] = { 1.0f, 2.0f, 3.0f, 4.0f };
    const float overflow[] = { 5.0f, 6.0f };
    float output[4] = {};

    fifo.push (first, 4);
    fifo.push (overflow, 2);
    const int pulled = fifo.pull (output, 4);

    CHECK (pulled == 4, "AudioFIFO reports the readable sample count");
    CHECK (output[0] == 3.0f && output[1] == 4.0f
           && output[2] == 5.0f && output[3] == 6.0f,
           "AudioFIFO overwrites stale samples and keeps newest history");
}

void testChromaticMidiTuning()
{
    std::vector<ModalResonator::Mode> modes {
        { 1084.0f, 1.0f, 1.0f },
        { 2168.0f, 0.5f, 1.0f },
        { 60000.0f, 0.2f, 1.0f }
    };

    tuneChromaticModesToMidi (modes, 69);

    CHECK (! modes.empty() && std::abs (modes[0].frequency - 440.0f) < 0.01f,
           "Chromatic fundamental is tuned to the requested MIDI note");
    CHECK (modes.size() == 2 && std::abs (modes[1].frequency - 880.0f) < 0.02f,
           "Chromatic mode ratios are preserved and ultrasonic modes removed");
}

void testScoreParserFields()
{
    const auto file = juce::File::createTempFile (".score.json");
    const auto json = R"json({
        "$schema": "TsukiSynth Score v1",
        "meta": { "title": "Parser Test", "id": "parser_test" },
        "global": {
            "bpm": 120,
            "sample_rate": 48000,
            "master_volume": 0.8,
            "random_seed": 123456789,
            "effects": {
                "wall": { "distance_m": 12, "material": "stone" }
            }
        },
        "events": [{
            "time": 0,
            "duration": 0.1,
            "engine": "fm",
            "note": "G9",
            "velocity": 0.5
        }],
        "export": {
            "filename": "parser_test",
            "export_filename": "Parser_Test",
            "format": "flac"
        }
    })json";

    CHECK (file.replaceWithText (json), "Temporary score file is writable");

    Score score;
    CHECK (ScoreParser::parse (file, score), "ScoreParser accepts a valid score");
    CHECK (score.exportSettings.exportFilename == "Parser_Test"
           && score.exportSettings.format == "flac",
           "ScoreParser reads export filename and format");
    CHECK (score.global.effects.wallDistanceM == 12.0
           && score.global.effects.wallMaterial == "stone",
           "ScoreParser reads wall reflection settings");
    CHECK (score.global.randomSeed == 123456789ull,
           "ScoreParser reads an exact deterministic random seed");
    CHECK (noteNameToMidi ("G9") == 127 && noteNameToMidi ("A9") == -1,
           "Note names are exact and out-of-range notes are rejected");

    file.deleteFile();
}

void testScoreParserRejectsInvalidContract()
{
    const std::vector<std::pair<const char*, const char*>> invalidCases {
        { "unknown engine", R"json({"time":0,"duration":0.1,"engine":"tongue_durm","note":"C4","velocity":0.5})json" },
        { "trailing note junk", R"json({"time":0,"duration":0.1,"engine":"fm","note":"60junk","velocity":0.5})json" },
        { "fractional MIDI", R"json({"time":0,"duration":0.1,"engine":"fm","note":60.9,"velocity":0.5})json" },
        { "out-of-range velocity", R"json({"time":0,"duration":0.1,"engine":"fm","note":60,"velocity":2})json" },
        { "unknown event field", R"json({"time":0,"duration":0.1,"engine":"fm","note":60,"velocity":0.5,"velocty":0.5})json" },
        { "unimplemented membrane", R"json({"time":0,"duration":0.1,"engine":"membrane","note":60,"velocity":0.5})json" },
        { "rejected no-op parameter", R"json({"time":0,"duration":0.1,"engine":"plate","note":60,"velocity":0.5,"params":{"height_mm":100}})json" },
        { "wrong scalar type", R"json({"time":0,"duration":0.1,"engine":"fm","note":60,"velocity":"0.5"})json" },
        { "irrelevant engine parameter", R"json({"time":0,"duration":0.1,"engine":"fm","note":60,"velocity":0.5,"params":{"radius_mm":100}})json" },
        { "irrelevant frequency mode", R"json({"time":0,"duration":0.1,"engine":"fm","note":60,"velocity":0.5,"params":{"frequency_mode":"geometry"}})json" },
        { "unknown beam boundary", R"json({"time":0,"duration":0.1,"engine":"beam","note":60,"velocity":0.5,"params":{"beam_boundary":"floating"}})json" }
    };

    for (const auto& [label, eventJson] : invalidCases)
    {
        const auto file = juce::File::createTempFile (".score.json");
        const juce::String json = juce::String (R"json({
          "$schema":"TsukiSynth Score v1",
          "meta":{"title":"Negative","id":"negative"},
          "global":{"bpm":120,"sample_rate":48000,"master_volume":0.8},
          "events":[)json") + eventJson + R"json(],
          "export":{"filename":"negative"}
        })json";
        file.replaceWithText (json);
        Score score;
        const bool accepted = ScoreParser::parse (file, score);
        CHECK (! accepted && ! score.errors.empty(), label);
        file.deleteFile();
    }
}

void testCustomDumpUsesEffectiveParameters()
{
    MaterialDB materials;
    loadTestMaterial (materials);
    Score score;
    score.global.sampleRate = 48000;
    ScoreEvent event;
    event.engine = "custom";
    event.note = "A4";
    event.velocity = 0.8f;
    event.customRatios[0] = 1.0f;
    event.customRatios[1] = 1.5f;
    event.customRatios[2] = 2.25f;
    event.customAmps[0] = 1.0f;
    event.customAmps[1] = 0.9f;
    event.customAmps[2] = 0.8f;
    score.events.push_back (event);

    ScoreRenderer renderer;
    renderer.setMaterialDB (&materials);
    CHECK (renderer.validateScore (score), "Custom score passes renderer preflight");
    const auto parsed = juce::JSON::parse (renderer.dumpModes (score));
    auto* root = parsed.getDynamicObject();
    auto* events = root != nullptr ? root->getProperty ("events").getArray() : nullptr;
    auto* dumped = events != nullptr && ! events->isEmpty()
        ? (*events)[0].getDynamicObject() : nullptr;
    auto* partials = dumped != nullptr ? dumped->getProperty ("partials").getArray() : nullptr;
    const bool frequenciesMatch = partials != nullptr && partials->size() >= 3
        && std::abs ((double) (*partials)[0].getDynamicObject()->getProperty ("freq") - 440.0) < 0.1
        && std::abs ((double) (*partials)[1].getDynamicObject()->getProperty ("freq") - 660.0) < 0.1
        && std::abs ((double) (*partials)[2].getDynamicObject()->getProperty ("freq") - 990.0) < 0.1;
    CHECK (frequenciesMatch, "Custom dump reports authored 1:1.5:2.25 ratios");
    CHECK (root != nullptr && (int) root->getProperty ("input_event_count") == 1
           && (int) root->getProperty ("dumped_event_count") == 1
           && dumped != nullptr && (int) dumped->getProperty ("source_index") == 0,
           "Mode dump carries input/dumped event-count identity");
}

void testFullWetShortReverbHasAudibleTail()
{
    Score score;
    score.global.sampleRate = 44100;
    score.global.masterVolume = 1.0;
    score.global.effects.reverbWet = 1.0;
    score.global.effects.reverbDecay = 0.0;
    score.exportSettings.normalize = false;
    score.exportSettings.tailSilenceMs = 0.0;
    ScoreEvent event;
    event.time = 0.0;
    event.duration = 0.01;
    event.engine = "fm";
    event.note = "A4";
    event.velocity = 0.8f;
    event.fmAttackMs = 1.0f;
    event.fmReleaseMs = 10.0f;
    score.events.push_back (event);

    MaterialDB materials;
    ScoreRenderer renderer;
    renderer.setMaterialDB (&materials);
    const auto file = juce::File::createTempFile (".wav");
    CHECK (renderer.render (score, file), "Full-wet short reverb renders successfully");
    auto reader = openAudioFile (file);
    bool nonSilent = false;
    if (reader != nullptr)
    {
        juce::AudioBuffer<float> audio (2, static_cast<int> (reader->lengthInSamples));
        reader->read (&audio, 0, audio.getNumSamples(), 0, true, true);
        nonSilent = audio.getMagnitude (0, 0, audio.getNumSamples()) > 0.000001f
            && reader->lengthInSamples > 3000;
    }
    CHECK (nonSilent, "Full-wet reverb includes its delayed response instead of all-zero output");
    file.deleteFile();
}

void testFlacWriter()
{
    const auto file = juce::File::createTempFile (".flac");
    juce::AudioBuffer<float> buffer (2, 480);
    buffer.clear();
    buffer.setSample (0, 0, 0.5f);
    buffer.setSample (1, 0, -0.5f);

    CHECK (WavWriter::write (file, buffer, 48000.0, 24, false),
           "FLAC writer creates an output file");

    auto reader = openAudioFile (file);
    CHECK (reader != nullptr && reader->lengthInSamples == 480
           && reader->bitsPerSample == 24,
           "FLAC output can be read back with the requested format");

    file.deleteFile();
}

void testFmRenderTailAndWall()
{
    Score score;
    score.global.sampleRate = 44100;
    score.global.masterVolume = 1.0;
    score.global.effects.reverbWet = 0.0;
    score.global.effects.wallDistanceM = 34.3;
    score.global.effects.wallMaterial = "concrete";
    score.exportSettings.normalize = false;
    score.exportSettings.tailSilenceMs = 0.0;

    ScoreEvent event;
    event.time = 0.0;
    event.duration = 0.2;
    event.engine = "fm";
    event.note = "A4";
    event.velocity = 0.8f;
    event.fmAttackMs = 1.0f;
    event.fmReleaseMs = 1000.0f;
    score.events.push_back (event);

    MaterialDB materials;
    ScoreRenderer renderer;
    renderer.setMaterialDB (&materials);

    const auto file = juce::File::createTempFile (".wav");
    CHECK (renderer.render (score, file),
           "ScoreRenderer renders an FM event with no material database entry");

    auto reader = openAudioFile (file);
    const auto minimumSamples = static_cast<juce::int64> (1.37 * 44100.0);
    CHECK (reader != nullptr && reader->lengthInSamples >= minimumSamples,
           "FM release and wall reflection are included in output duration");

    file.deleteFile();
}

void testLayerSourceMasterAndTrim()
{
    const auto directory = juce::File::getSpecialLocation (
        juce::File::tempDirectory)
        .getNonexistentChildFile ("tsuki-layer-test", {}, false);
    CHECK (directory.createDirectory(),
           "Temporary layer test directory is writable");

    const auto source = directory.getChildFile ("source.score.json");
    const auto sourceJson = R"json({
        "$schema": "TsukiSynth Score v1",
        "meta": { "title": "Layer Source", "id": "layer_source" },
        "global": {
            "bpm": 120,
            "sample_rate": 44100,
            "master_volume": 0,
            "effects": { "reverb": { "decay": 0, "wet": 0 } }
        },
        "events": [{
            "time": 0,
            "duration": 0.2,
            "engine": "fm",
            "note": "A4",
            "velocity": 0.8,
            "params": { "fm_attack": 1, "fm_release": 100 }
        }],
        "export": {
            "filename": "layer_source",
            "normalize": false,
            "tail_silence_ms": 0,
            "start_position": 0,
            "end_position": 0.5
        }
    })json";
    CHECK (source.replaceWithText (sourceJson),
           "Layer source score is writable");

    Score parent;
    parent.global.sampleRate = 44100;
    parent.global.masterVolume = 1.0;
    parent.global.effects.reverbWet = 0.0;
    parent.exportSettings.normalize = false;
    parent.exportSettings.tailSilenceMs = 0.0;
    parent.layers.push_back ({ source.getFileName().toStdString(), 0.0, 1.0, 1.0 });

    MaterialDB materials;
    ScoreRenderer renderer;
    renderer.setMaterialDB (&materials);
    renderer.setBaseDir (directory);

    const auto output = directory.getChildFile ("layer.wav");
    CHECK (renderer.renderLayered (parent, output),
           "Layered renderer accepts a valid source score");

    auto reader = openAudioFile (output);
    CHECK (reader != nullptr
           && reader->lengthInSamples > 6000
           && reader->lengthInSamples < 6300,
           "Layer source trim controls the mixed region length");

    if (reader != nullptr)
    {
        juce::AudioBuffer<float> rendered (
            2, static_cast<int> (reader->lengthInSamples));
        reader->read (&rendered, 0, rendered.getNumSamples(), 0, true, true);
        CHECK (rendered.getMagnitude (
                   0, 0, rendered.getNumSamples()) < 0.000001f,
               "Layer source master volume is applied before mixing");
    }

    directory.deleteRecursively();
}
}

int main()
{
    std::printf ("TsukiSynth regression tests\n");
    testEnvelopeRelease();
    testAudioFifoKeepsNewestUnreadData();
    testMaterialDatabaseIsTransactional();
    testChromaticMidiTuning();
    testScoreParserFields();
    testScoreParserRejectsInvalidContract();
    testCustomDumpUsesEffectiveParameters();
    testFullWetShortReverbHasAudibleTail();
    testFlacWriter();
    testFmRenderTailAndWall();
    testLayerSourceMasterAndTrim();

    std::printf ("%s (%d failure%s)\n",
                 failures == 0 ? "PASS" : "FAIL",
                 failures,
                 failures == 1 ? "" : "s");
    return failures == 0 ? 0 : 1;
}
