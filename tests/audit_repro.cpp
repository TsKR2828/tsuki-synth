#include "dsp/AudioFIFO.h"
#include "dsp/Envelope.h"
#include "engines/ChromaticEngine.h"
#include "score/ScoreParser.h"
#include "score/ScoreRenderer.h"
#include "score/WavWriter.h"

#include <cmath>
#include <cstdio>
#include <limits>
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

bool readAudioFile (const juce::File& file, juce::AudioBuffer<float>& audio,
                    double* sampleRate = nullptr)
{
    auto reader = openAudioFile (file);
    if (reader == nullptr || reader->lengthInSamples <= 0
        || reader->lengthInSamples > std::numeric_limits<int>::max())
        return false;
    audio.setSize (2, (int) reader->lengthInSamples);
    if (sampleRate != nullptr) *sampleRate = reader->sampleRate;
    return reader->read (&audio, 0, audio.getNumSamples(), 0, true, true);
}

void loadTestMaterial (MaterialDB& materials)
{
    const auto json = R"json({"materials":{"steel":{"display_name":"Steel","density":7800,"youngs_modulus":200000000000,"poisson_ratio":0.29,"damping":{"eta":0.0002,"beta_air":0.00000012,"gamma_radiation":0.00002}}}})json";
    CHECK (materials.loadFromString (json), "Test material database loads");
}

void testMaterialDatabaseIsTransactional()
{
    MaterialDB materials;
    loadTestMaterial (materials);
    const int originalSize = materials.size();
    const auto invalid = R"json({"materials":{"bad":{"display_name":"Bad","density":0,"youngs_modulus":1,"poisson_ratio":0.6,"damping":{"eta":-1,"beta_air":0,"gamma_radiation":0}}}})json";
    CHECK (! materials.loadFromString (invalid),
           "MaterialDB rejects non-physical material constants");
    CHECK (materials.size() == originalSize
           && materials.getMaterial ("steel") != nullptr,
           "Failed material reload preserves the last known-good database");

    // Pre-2026-08-10 schema must FAIL CLOSED, not be reinterpreted: alpha and eta
    // differ by the 118.921 MIDI-60 anchor factor, so silently reading an alpha as
    // an eta would under-damp every material by ~5 orders of magnitude.
    const auto legacy = R"json({"materials":{"steel":{"display_name":"Steel","density":7800,"youngs_modulus":200000000000,"poisson_ratio":0.29,"damping":{"alpha":0.0238,"beta_air":0.00000012,"gamma_radiation":0.00002}}}})json";
    CHECK (! materials.loadFromString (legacy),
           "MaterialDB refuses the retired frequency-independent alpha schema");

    // Belt-and-braces: a file carrying BOTH keys is also refused, so a partially
    // migrated database can never render with an ambiguous damping source.
    const auto both = R"json({"materials":{"steel":{"display_name":"Steel","density":7800,"youngs_modulus":200000000000,"poisson_ratio":0.29,"damping":{"alpha":0.0238,"eta":0.0002,"beta_air":0.00000012,"gamma_radiation":0.00002}}}})json";
    CHECK (! materials.loadFromString (both),
           "MaterialDB refuses a damping block carrying both alpha and eta");
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
            "sample_rate": 192000,
            "master_volume": 0.8,
            "random_seed": 123456789,
            "effects": {
                "wall": { "distance_m": 12, "material": "stone" }
            }
        },
        "events": [{
            "event_id": "parser-g9",
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
    CHECK (score.global.sampleRate == 192000,
           "ScoreParser accepts the shared 192 kHz render contract");
    CHECK (score.events.size() == 1 && score.events[0].eventId == "parser-g9",
           "ScoreParser reads an optional stable event_id");
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

    const auto duplicateIdFile = juce::File::createTempFile (".score.json");
    duplicateIdFile.replaceWithText (R"json({
      "$schema":"TsukiSynth Score v1",
      "meta":{"title":"Duplicate IDs","id":"duplicate_ids"},
      "global":{"bpm":120,"sample_rate":48000,"master_volume":0.8},
      "events":[
        {"event_id":"same","time":0,"duration":0.1,"engine":"fm","note":60,"velocity":0.5},
        {"event_id":"same","time":1,"duration":0.1,"engine":"fm","note":61,"velocity":0.5}
      ],
      "export":{"filename":"duplicate_ids"}
    })json");
    Score duplicateIdScore;
    CHECK (! ScoreParser::parse (duplicateIdFile, duplicateIdScore)
           && ! duplicateIdScore.errors.empty(),
           "duplicate event_id");
    duplicateIdFile.deleteFile();

    const auto longIdFile = juce::File::createTempFile (".score.json");
    const auto longId = juce::String::repeatedString ("x", 129);
    longIdFile.replaceWithText (
        juce::String (R"json({
          "$schema":"TsukiSynth Score v1",
          "meta":{"title":"Long ID","id":"long_id"},
          "global":{"bpm":120,"sample_rate":48000,"master_volume":0.8},
          "events":[{"event_id":")json") + longId + R"json(","time":0,
            "duration":0.1,"engine":"fm","note":60,"velocity":0.5}],
          "export":{"filename":"long_id"}
        })json");
    Score longIdScore;
    CHECK (! ScoreParser::parse (longIdFile, longIdScore)
           && ! longIdScore.errors.empty(),
           "overlong event_id");
    longIdFile.deleteFile();
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
    auto silentEvent = event;
    silentEvent.velocity = 0.0f;
    silentEvent.time = 1.0;
    score.events.push_back (silentEvent);

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
    CHECK (root != nullptr
           && root->getProperty ("contract").toString() == "TsukiSynth Mode Dump v2"
           && (int) root->getProperty ("input_event_count") == 2
           && (int) root->getProperty ("dumped_event_count") == 1
           && dumped != nullptr && (int) dumped->getProperty ("source_index") == 0,
           "Mode dump v2 carries explicit observable and event identity metadata");
}

void testRendererRejectsAttackOnlyModalEvent()
{
    MaterialDB materials;
    loadTestMaterial (materials);

    Score score;
    score.global.sampleRate = 48000;
    score.global.effects.reverbWet = 0.0;
    score.exportSettings.normalize = false;
    ScoreEvent event;
    event.engine = "tongue_drum";
    event.note = "C4";
    event.velocity = 0.8f;
    event.material = "steel";
    event.frequencyMode = "geometry";
    event.lengthMm = 10000.0;
    event.widthMm = 1.0;
    event.thicknessMm = 0.1;
    score.events.push_back (event);

    ScoreRenderer renderer;
    renderer.setMaterialDB (&materials);
    const auto output = juce::File::createTempFile (".wav");
    CHECK (! renderer.render (score, output),
           "Renderer refuses a modal event whose geometry is entirely below 20 Hz");
    const auto& warnings = renderer.getWarnings();
    CHECK (! warnings.empty()
           && warnings.back().find ("no render-active modal energy") != std::string::npos,
           "Attack-only refusal reports the renderable-frequency reason");
    output.deleteFile();
}

void testSemanticEventOrderIsBitExact()
{
    MaterialDB materials;
    loadTestMaterial (materials);

    ScoreEvent cimbalom;
    cimbalom.time = 0.0;
    cimbalom.duration = 0.2;
    cimbalom.engine = "cimbalom";
    cimbalom.note = "C4";
    cimbalom.velocity = 0.8f;
    cimbalom.material = "steel";

    ScoreEvent tongue = cimbalom;
    tongue.engine = "tongue_drum";
    tongue.note = "G4";
    tongue.lengthMm = 100.0;
    tongue.widthMm = 25.0;
    tongue.thicknessMm = 3.0;

    auto makeScore = []
    {
        Score score;
        score.global.sampleRate = 48000;
        score.global.masterVolume = 1.0;
        score.global.randomSeed = 987654321;
        score.global.effects.reverbWet = 0.0;
        score.global.effects.delayWet = 0.0;
        score.global.effects.distortionWet = 0.0;
        score.exportSettings.normalize = false;
        score.exportSettings.tailSilenceMs = 0.0;
        return score;
    };

    auto ordered = makeScore();
    ordered.events = { cimbalom, tongue };
    auto permuted = makeScore();
    permuted.events = { tongue, cimbalom };
    auto withSilent = makeScore();
    ScoreEvent silent = tongue;
    silent.time = 0.0;
    silent.duration = 10.0;
    silent.velocity = 0.0f;
    withSilent.events = { silent, cimbalom, tongue };

    const auto fileA = juce::File::createTempFile (".wav");
    const auto fileB = juce::File::createTempFile (".wav");
    const auto fileC = juce::File::createTempFile (".wav");
    ScoreRenderer renderer;
    renderer.setMaterialDB (&materials);
    const bool rendered = renderer.render (ordered, fileA)
        && renderer.render (permuted, fileB)
        && renderer.render (withSilent, fileC);
    CHECK (rendered, "Semantic-order regression fixtures render successfully");

    juce::MemoryBlock bytesA, bytesB, bytesC;
    const bool loaded = fileA.loadFileAsData (bytesA)
        && fileB.loadFileAsData (bytesB)
        && fileC.loadFileAsData (bytesC);
    CHECK (loaded && bytesA == bytesB,
           "Permuting simultaneous events preserves the exact WAV bytes");
    CHECK (loaded && bytesA == bytesC,
           "Inserting a zero-velocity event preserves the exact WAV bytes");

    fileA.deleteFile();
    fileB.deleteFile();
    fileC.deleteFile();
}

void testRendererSupportsContractSampleRates()
{
    MaterialDB materials;
    loadTestMaterial (materials);
    bool allRendered = true;

    for (const int sampleRate : TsukiSampleRates::supported)
    {
        Score score;
        score.global.sampleRate = sampleRate;
        score.global.masterVolume = 1.0;
        score.global.effects.reverbWet = 0.0;
        score.exportSettings.normalize = false;
        score.exportSettings.tailSilenceMs = 0.0;
        ScoreEvent event;
        event.time = 0.0;
        event.duration = 0.01;
        event.engine = "tongue_drum";
        event.note = "A4";
        event.velocity = 0.5f;
        event.material = "steel";
        event.dampingOverride = 100.0;
        score.events.push_back (event);

        ScoreRenderer renderer;
        renderer.setMaterialDB (&materials);
        const auto output = juce::File::createTempFile (".wav");
        const bool rendered = renderer.render (score, output);
        auto reader = rendered ? openAudioFile (output) : nullptr;
        allRendered = allRendered && reader != nullptr
            && (int) reader->sampleRate == sampleRate
            && reader->lengthInSamples > 0;
        output.deleteFile();
    }

    CHECK (allRendered,
           "Physical renderer writes valid audio at every shared sample rate through 192 kHz");
}

void testCausalityLocalityAndLinearSuperposition()
{
    MaterialDB materials;
    loadTestMaterial (materials);

    auto baseScore = []
    {
        Score score;
        score.global.sampleRate = 48000;
        score.global.masterVolume = 0.5;
        score.global.randomSeed = 424242;
        score.global.effects.reverbWet = 0.0;
        score.global.effects.delayWet = 0.0;
        score.global.effects.distortionWet = 0.0;
        score.exportSettings.normalize = false;
        score.exportSettings.bitDepth = 32;
        score.exportSettings.tailSilenceMs = 0.0;
        return score;
    };
    auto event = [] (const char* id, double time, double strike)
    {
        ScoreEvent value;
        value.eventId = id;
        value.time = time;
        value.duration = 0.1;
        value.engine = "tongue_drum";
        value.note = "C4";
        value.velocity = 0.2f;
        value.material = "steel";
        value.strikePosition = strike;
        value.dampingOverride = 100.0;
        return value;
    };
    auto renderToAudio = [&materials] (const Score& score,
                                       juce::AudioBuffer<float>& audio)
    {
        ScoreRenderer renderer;
        renderer.setMaterialDB (&materials);
        const auto output = juce::File::createTempFile (".wav");
        const bool ok = renderer.render (score, output)
            && readAudioFile (output, audio);
        output.deleteFile();
        return ok;
    };

    auto delayed = baseScore();
    delayed.events = { event ("delayed", 0.2, 0.3) };
    juce::AudioBuffer<float> delayedAudio;
    const bool delayedOk = renderToAudio (delayed, delayedAudio);
    const int causalPrefix = std::min (delayedAudio.getNumSamples(), 9600);
    CHECK (delayedOk && causalPrefix == 9600
           && delayedAudio.getMagnitude (0, 0, causalPrefix) == 0.0f
           && delayedAudio.getMagnitude (1, 0, causalPrefix) == 0.0f,
           "Renderer is causal: an event produces no samples before its authored time");

    auto present = baseScore();
    present.exportSettings.tailSilenceMs = 1000.0;
    present.events = { event ("present", 0.0, 0.3) };
    auto withFuture = present;
    withFuture.events.push_back (event ("future", 0.5, 0.6));
    juce::AudioBuffer<float> presentAudio, futureAudio;
    bool locality = renderToAudio (present, presentAudio)
        && renderToAudio (withFuture, futureAudio);
    const int futureStart = 24000;
    locality = locality && presentAudio.getNumSamples() >= futureStart
        && futureAudio.getNumSamples() >= futureStart;
    for (int ch = 0; locality && ch < 2; ++ch)
        for (int i = 0; i < futureStart; ++i)
            locality = locality
                && presentAudio.getSample (ch, i) == futureAudio.getSample (ch, i);
    CHECK (locality,
           "Adding a future event leaves every earlier rendered sample bit-exact");

    const auto a = event ("linear-a", 0.0, 0.25);
    const auto b = event ("linear-b", 0.0, 0.65);
    auto scoreA = baseScore(); scoreA.events = { a };
    auto scoreB = baseScore(); scoreB.events = { b };
    auto scoreAB = baseScore(); scoreAB.events = { a, b };
    juce::AudioBuffer<float> audioA, audioB, audioAB;
    bool linear = renderToAudio (scoreA, audioA)
        && renderToAudio (scoreB, audioB)
        && renderToAudio (scoreAB, audioAB)
        && audioA.getNumSamples() == audioB.getNumSamples()
        && audioA.getNumSamples() == audioAB.getNumSamples();
    float maxLinearError = 0.0f;
    for (int ch = 0; linear && ch < 2; ++ch)
        for (int i = 0; i < audioAB.getNumSamples(); ++i)
            maxLinearError = std::max (maxLinearError, std::abs (
                audioAB.getSample (ch, i)
                - audioA.getSample (ch, i) - audioB.getSample (ch, i)));
    CHECK (linear && maxLinearError < 2.0e-6f,
           "FX-off renderer obeys linear superposition within PCM quantization error");

    auto oversized = baseScore();
    oversized.global.sampleRate = 192000;
    oversized.events = { event ("oversized", 86400.0, 0.3) };
    ScoreRenderer budgetRenderer;
    budgetRenderer.setMaterialDB (&materials);
    const auto oversizedOutput = juce::File::createTempFile (".wav");
    CHECK (! budgetRenderer.render (oversized, oversizedOutput),
           "Extreme valid-duration input is rejected by the 1 GiB buffer budget");
    oversizedOutput.deleteFile();
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
    testRendererRejectsAttackOnlyModalEvent();
    testSemanticEventOrderIsBitExact();
    testRendererSupportsContractSampleRates();
    testCausalityLocalityAndLinearSuperposition();
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
