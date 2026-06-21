#include "dsp/AudioFIFO.h"
#include "dsp/Envelope.h"
#include "engines/ChromaticEngine.h"
#include "score/ScoreParser.h"
#include "score/ScoreRenderer.h"
#include "score/WavWriter.h"

#include <cmath>
#include <cstdio>
#include <memory>

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

void testAudioFifoDoesNotOverwriteUnreadData()
{
    AudioFIFO fifo (4);
    const float first[] = { 1.0f, 2.0f, 3.0f, 4.0f };
    const float overflow[] = { 5.0f, 6.0f };
    float output[4] = {};

    fifo.push (first, 4);
    fifo.push (overflow, 2);
    const int pulled = fifo.pull (output, 4);

    CHECK (pulled == 4, "AudioFIFO reports the readable sample count");
    CHECK (output[0] == 1.0f && output[1] == 2.0f
           && output[2] == 3.0f && output[3] == 4.0f,
           "AudioFIFO never overwrites unread samples");
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
        "global": {
            "sample_rate": 48000,
            "effects": {
                "wall": { "distance_m": 12, "material": "stone" }
            }
        },
        "events": [{
            "time": 0,
            "duration": 0.1,
            "engine": "fm",
            "note": "A9",
            "velocity": 0.5
        }],
        "export": {
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
    CHECK (noteNameToMidi ("A9") == 127,
           "Note names are clamped to the MIDI range");

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
        "global": {
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
    testAudioFifoDoesNotOverwriteUnreadData();
    testChromaticMidiTuning();
    testScoreParserFields();
    testFlacWriter();
    testFmRenderTailAndWall();
    testLayerSourceMasterAndTrim();

    std::printf ("%s (%d failure%s)\n",
                 failures == 0 ? "PASS" : "FAIL",
                 failures,
                 failures == 1 ? "" : "s");
    return failures == 0 ? 0 : 1;
}
