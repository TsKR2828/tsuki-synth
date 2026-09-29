#include "IRLibrary.h"
#include "dsp/AudioFIFO.h"
#include "dsp/DiagnosticOverrides.h"
#include "dsp/Envelope.h"
#include "effects/EffectChain.h"
#include "engines/ChromaticEngine.h"
#include "score/ScoreParser.h"
#include "score/ScoreRenderer.h"
#include "score/WavWriter.h"

#include <atomic>
#include <cmath>
#include <cstdio>
#include <cstdlib>
#include <limits>
#include <memory>
#include <random>
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

// The minimal database these repro tests render against. It carries TWO
// materials, for two different reasons:
//
//   steel        -- the string material every cimbalom/string event below
//                   names explicitly.
//   wood_spruce  -- the bridge/soundboard reference material that
//                   CimbalomEngine.h::kBridgeSoundboardMaterialKey looks up
//                   for StringModel::bridgeLossRate() (2026-08-16 B1). That
//                   lookup is fail-closed at four call sites
//                   (CimbalomEngine.h:133 -> return, ScoreRenderer.h:183 ->
//                   continue, :704 -> return false, :999 -> return 0.0), so a
//                   database WITHOUT it makes every string render abort --
//                   which is exactly what it should do, because a database
//                   with no soundboard material is an incomplete database.
//                   Production data/materials.json always contains it; this
//                   fixture simply had not caught up (TODO.md X1).
//
// Both entries are verbatim copies of their data/materials.json values so the
// fixture stays traceable (Rule 4) and cannot drift into a second, divergent
// source of physical constants. display_name is ASCII here only to keep this
// source file free of non-ASCII literals; it is not read by the physics.
void loadTestMaterial (MaterialDB& materials)
{
    const auto json = R"json({"materials":{)json"
        R"json("steel":{"display_name":"Steel","density":7800,"youngs_modulus":200000000000,"poisson_ratio":0.29,"damping":{"eta":0.0002,"beam_plate_beta_air":0.00000012,"beam_plate_gamma_radiation":0.00002}},)json"
        R"json("wood_spruce":{"display_name":"Spruce","density":450,"youngs_modulus":12000000000,"poisson_ratio":0.37,"damping":{"eta":0.007,"beam_plate_beta_air":0.0000003,"beam_plate_gamma_radiation":0.00005}})json"
        R"json(}})json";
    CHECK (materials.loadFromString (json), "Test material database loads");
}

void testMaterialDatabaseIsTransactional()
{
    MaterialDB materials;
    loadTestMaterial (materials);
    const int originalSize = materials.size();
    const auto invalid = R"json({"materials":{"bad":{"display_name":"Bad","density":0,"youngs_modulus":1,"poisson_ratio":0.6,"damping":{"eta":-1,"beam_plate_beta_air":0,"beam_plate_gamma_radiation":0}}}})json";
    CHECK (! materials.loadFromString (invalid),
           "MaterialDB rejects non-physical material constants");
    CHECK (materials.size() == originalSize
           && materials.getMaterial ("steel") != nullptr,
           "Failed material reload preserves the last known-good database");

    // Pre-2026-08-10 schema must FAIL CLOSED, not be reinterpreted: alpha and eta
    // differ by the 118.921 MIDI-60 anchor factor, so silently reading an alpha as
    // an eta would under-damp every material by ~5 orders of magnitude.
    const auto legacy = R"json({"materials":{"steel":{"display_name":"Steel","density":7800,"youngs_modulus":200000000000,"poisson_ratio":0.29,"damping":{"alpha":0.0238,"beam_plate_beta_air":0.00000012,"beam_plate_gamma_radiation":0.00002}}}})json";
    CHECK (! materials.loadFromString (legacy),
           "MaterialDB refuses the retired frequency-independent alpha schema");

    // Belt-and-braces: a file carrying BOTH keys is also refused, so a partially
    // migrated database can never render with an ambiguous damping source.
    const auto both = R"json({"materials":{"steel":{"display_name":"Steel","density":7800,"youngs_modulus":200000000000,"poisson_ratio":0.29,"damping":{"alpha":0.0238,"eta":0.0002,"beam_plate_beta_air":0.00000012,"beam_plate_gamma_radiation":0.00002}}}})json";
    CHECK (! materials.loadFromString (both),
           "MaterialDB refuses a damping block carrying both alpha and eta");

    // Pre-B3 (2026-08-24) schema must also FAIL CLOSED: bare
    // beta_air/gamma_radiation were renamed to beam_plate_* because they no
    // longer feed StringModel at all (Beam/Plate-only) -- a file written for
    // the old schema must not silently load with the new semantics.
    // Positive control FIRST (required by docs/workcards/B3.md §7-1): the very
    // same material block with the NEW key names must load, proving the two
    // rejection checks below discriminate old vs new schema rather than
    // rejecting everything.
    MaterialDB b3Schema;
    const auto newKeys = R"json({"materials":{"steel":{"display_name":"Steel","density":7800,"youngs_modulus":200000000000,"poisson_ratio":0.29,"damping":{"eta":0.0002,"beam_plate_beta_air":0.00000012,"beam_plate_gamma_radiation":0.00002}}}})json";
    CHECK (b3Schema.loadFromString (newKeys),
           "MaterialDB accepts the renamed beam_plate_* schema (positive control)");
    // Each rejection case carries the COMPLETE new schema PLUS one retired
    // key, so the ONLY possible failure trigger is the retired key itself
    // (not a missing beam_plate_* field) -- same isolation discipline as the
    // alpha "both" case above. A file with only the old keys (missing the
    // new ones) is rejected a fortiori by the finiteNumber() reads.
    const auto bareBeta = R"json({"materials":{"steel":{"display_name":"Steel","density":7800,"youngs_modulus":200000000000,"poisson_ratio":0.29,"damping":{"eta":0.0002,"beta_air":0.00000012,"beam_plate_beta_air":0.00000012,"beam_plate_gamma_radiation":0.00002}}}})json";
    CHECK (! b3Schema.loadFromString (bareBeta),
           "MaterialDB refuses the retired bare beta_air/gamma_radiation schema (beta_air)");
    const auto bareGamma = R"json({"materials":{"steel":{"display_name":"Steel","density":7800,"youngs_modulus":200000000000,"poisson_ratio":0.29,"damping":{"eta":0.0002,"gamma_radiation":0.00002,"beam_plate_beta_air":0.00000012,"beam_plate_gamma_radiation":0.00002}}}})json";
    CHECK (! b3Schema.loadFromString (bareGamma),
           "MaterialDB refuses the retired bare beta_air/gamma_radiation schema (gamma_radiation)");
    CHECK (b3Schema.getMaterial ("steel") != nullptr,
           "Rejected legacy reloads keep the last known-good beam_plate_* database");
}

// B5 (2026-08-28, draft stage): `orthotropic` is an OPTIONAL, wood-only,
// fail-closed schema block. Nothing in the engine consumes it yet
// (docs/workcards/B5.md §0) -- these tests only prove the schema parser is
// correct, not that any audio changes. Positive cases first (present/absent/
// non-wood-allowed), then the required negative controls (§7 of the
// workcard), each isolating exactly one invalid field so the failure trigger
// is unambiguous.
void testOrthotropicSchemaFailClosed()
{
    // ---- Positive 1: full valid block, ratio_GRT_EL explicit null (wood_maple
    // literature values -- Table 5-1 has no measured RT shear ratio for maple).
    {
        MaterialDB materials;
        const auto json = R"json({"materials":{"wood_maple":{"display_name":"Maple","density":650,"youngs_modulus":12500000000,"poisson_ratio":0.38,"damping":{"eta":0.012,"beam_plate_beta_air":0.00000025,"beam_plate_gamma_radiation":0.000045},"orthotropic":{"source_species":"Maple, sugar","moisture_content_pct":12,"mp_percent":25,"ratio_ET_EL":0.065,"ratio_ER_EL":0.132,"ratio_GLR_EL":0.111,"ratio_GLT_EL":0.063,"ratio_GRT_EL":null,"poisson_LR":0.424,"poisson_LT":0.476,"poisson_RT":0.774,"poisson_TR":0.349,"poisson_RL":0.065,"poisson_TL":0.037}}}})json";
        CHECK (materials.loadFromString (json),
               "Orthotropic: full valid block with explicit-null ratio_GRT_EL loads");
        auto* mat = materials.getMaterial ("wood_maple");
        CHECK (mat != nullptr && mat->orthotropic.present,
               "Orthotropic: present == true after a valid block loads");
        CHECK (mat != nullptr && ! mat->orthotropic.hasGRT,
               "Orthotropic: explicit null ratio_GRT_EL yields hasGRT == false");
        CHECK (mat != nullptr && mat->orthotropic.sourceSpecies == juce::String ("Maple, sugar"),
               "Orthotropic: source_species read back verbatim");
        CHECK (mat != nullptr && std::abs ((double) mat->orthotropic.moistureContentPct - 12.0) < 1e-6,
               "Orthotropic: moisture_content_pct read back (±1e-6)");
        CHECK (mat != nullptr && std::abs ((double) mat->orthotropic.mpPercent - 25.0) < 1e-6,
               "Orthotropic: mp_percent read back (±1e-6)");
        CHECK (mat != nullptr && std::abs ((double) mat->orthotropic.ratioET_EL - 0.065) < 1e-6,
               "Orthotropic: ratio_ET_EL read back (±1e-6)");
        CHECK (mat != nullptr && std::abs ((double) mat->orthotropic.ratioER_EL - 0.132) < 1e-6,
               "Orthotropic: ratio_ER_EL read back (±1e-6)");
        CHECK (mat != nullptr && std::abs ((double) mat->orthotropic.ratioGLR_EL - 0.111) < 1e-6,
               "Orthotropic: ratio_GLR_EL read back (±1e-6)");
        CHECK (mat != nullptr && std::abs ((double) mat->orthotropic.ratioGLT_EL - 0.063) < 1e-6,
               "Orthotropic: ratio_GLT_EL read back (±1e-6)");
        CHECK (mat != nullptr && std::abs ((double) mat->orthotropic.poissonLR - 0.424) < 1e-6
               && std::abs ((double) mat->orthotropic.poissonLT - 0.476) < 1e-6
               && std::abs ((double) mat->orthotropic.poissonRT - 0.774) < 1e-6
               && std::abs ((double) mat->orthotropic.poissonTR - 0.349) < 1e-6
               && std::abs ((double) mat->orthotropic.poissonRL - 0.065) < 1e-6
               && std::abs ((double) mat->orthotropic.poissonTL - 0.037) < 1e-6,
               "Orthotropic: all 6 poisson ratios read back (±1e-6)");
    }

    // ---- Positive 2: a material with no "orthotropic" key at all -> present == false.
    {
        MaterialDB materials;
        loadTestMaterial (materials);
        auto* mat = materials.getMaterial ("steel");
        CHECK (mat != nullptr && ! mat->orthotropic.present,
               "Orthotropic: absent key yields present == false (legal, not an error)");
    }

    // ---- Positive 3: schema does not forbid a non-wood material from carrying
    // an orthotropic block (docs/workcards/B5.md §7 point 3) -- not the core
    // concern of this card, just confirming it is not accidentally rejected.
    {
        MaterialDB materials;
        const auto json = R"json({"materials":{"steel":{"display_name":"Steel","density":7800,"youngs_modulus":200000000000,"poisson_ratio":0.29,"damping":{"eta":0.0002,"beam_plate_beta_air":0.00000012,"beam_plate_gamma_radiation":0.00002},"orthotropic":{"source_species":"Spruce, Sitka","moisture_content_pct":12,"mp_percent":27,"ratio_ET_EL":0.043,"ratio_ER_EL":0.078,"ratio_GLR_EL":0.064,"ratio_GLT_EL":0.061,"ratio_GRT_EL":0.003,"poisson_LR":0.372,"poisson_LT":0.467,"poisson_RT":0.435,"poisson_TR":0.245,"poisson_RL":0.040,"poisson_TL":0.025}}}})json";
        CHECK (materials.loadFromString (json),
               "Orthotropic: non-wood material (steel) with a valid block loads (schema allows it)");
        auto* mat = materials.getMaterial ("steel");
        CHECK (mat != nullptr && mat->orthotropic.present && mat->orthotropic.hasGRT
               && std::abs ((double) mat->orthotropic.ratioGRT_EL - 0.003) < 1e-6,
               "Orthotropic: non-null ratio_GRT_EL yields hasGRT == true with correct value");
    }

    // ---- Negative controls. Each swaps exactly ONE field of an otherwise-valid
    // block, so the ONLY possible failure trigger is that field (same isolation
    // discipline as the alpha/beta_air checks above).

    // Negative 1: ratio_ET_EL = 1.5 (violates the open interval (0,1); cross-grain
    // stiffness cannot exceed longitudinal stiffness for orthotropic wood).
    // This line, if relaxed to accept ratios >= 1, should turn this test FAIL.
    {
        MaterialDB materials;
        const auto bad = R"json({"materials":{"wood_spruce":{"display_name":"Spruce","density":450,"youngs_modulus":12000000000,"poisson_ratio":0.37,"damping":{"eta":0.007,"beam_plate_beta_air":0.0000003,"beam_plate_gamma_radiation":0.00005},"orthotropic":{"source_species":"Spruce, Sitka","moisture_content_pct":12,"mp_percent":27,"ratio_ET_EL":1.5,"ratio_ER_EL":0.078,"ratio_GLR_EL":0.064,"ratio_GLT_EL":0.061,"ratio_GRT_EL":0.003,"poisson_LR":0.372,"poisson_LT":0.467,"poisson_RT":0.435,"poisson_TR":0.245,"poisson_RL":0.040,"poisson_TL":0.025}}}})json";
        CHECK (! materials.loadFromString (bad),
               "Orthotropic: ratio_ET_EL = 1.5 (out of (0,1)) is rejected -- whole file fails closed");
    }

    // Negative 2: ratio_ET_EL = 0 (boundary itself excluded -- open interval, not [0,1)).
    // This line, if relaxed to accept 0, should turn this test FAIL.
    {
        MaterialDB materials;
        const auto bad = R"json({"materials":{"wood_spruce":{"display_name":"Spruce","density":450,"youngs_modulus":12000000000,"poisson_ratio":0.37,"damping":{"eta":0.007,"beam_plate_beta_air":0.0000003,"beam_plate_gamma_radiation":0.00005},"orthotropic":{"source_species":"Spruce, Sitka","moisture_content_pct":12,"mp_percent":27,"ratio_ET_EL":0,"ratio_ER_EL":0.078,"ratio_GLR_EL":0.064,"ratio_GLT_EL":0.061,"ratio_GRT_EL":0.003,"poisson_LR":0.372,"poisson_LT":0.467,"poisson_RT":0.435,"poisson_TR":0.245,"poisson_RL":0.040,"poisson_TL":0.025}}}})json";
        CHECK (! materials.loadFromString (bad),
               "Orthotropic: ratio_ET_EL = 0 (excluded boundary) is rejected -- whole file fails closed");
    }

    // Negative 3: poisson_LR = -0.1 (poisson ratios are [0,1), never negative).
    // This line, if relaxed to accept negative values, should turn this test FAIL.
    {
        MaterialDB materials;
        const auto bad = R"json({"materials":{"wood_spruce":{"display_name":"Spruce","density":450,"youngs_modulus":12000000000,"poisson_ratio":0.37,"damping":{"eta":0.007,"beam_plate_beta_air":0.0000003,"beam_plate_gamma_radiation":0.00005},"orthotropic":{"source_species":"Spruce, Sitka","moisture_content_pct":12,"mp_percent":27,"ratio_ET_EL":0.043,"ratio_ER_EL":0.078,"ratio_GLR_EL":0.064,"ratio_GLT_EL":0.061,"ratio_GRT_EL":0.003,"poisson_LR":-0.1,"poisson_LT":0.467,"poisson_RT":0.435,"poisson_TR":0.245,"poisson_RL":0.040,"poisson_TL":0.025}}}})json";
        CHECK (! materials.loadFromString (bad),
               "Orthotropic: poisson_LR = -0.1 (negative) is rejected -- whole file fails closed");
    }

    // Negative 4: ratio_GRT_EL given as the STRING "n/a" -- a type error, not the
    // legal explicit-null representation of "literature table lists no value".
    // This is the specific trap §11 of B5.md calls out: if this check is ever
    // loosened to coerce non-null/non-number values into hasGRT=false, a future
    // consumer could silently read a physically-nonsensical zero shear modulus.
    // This line, if relaxed to accept non-null/non-number types, should turn
    // this test FAIL.
    {
        MaterialDB materials;
        const auto bad = R"json({"materials":{"wood_maple":{"display_name":"Maple","density":650,"youngs_modulus":12500000000,"poisson_ratio":0.38,"damping":{"eta":0.012,"beam_plate_beta_air":0.00000025,"beam_plate_gamma_radiation":0.000045},"orthotropic":{"source_species":"Maple, sugar","moisture_content_pct":12,"mp_percent":25,"ratio_ET_EL":0.065,"ratio_ER_EL":0.132,"ratio_GLR_EL":0.111,"ratio_GLT_EL":0.063,"ratio_GRT_EL":"n/a","poisson_LR":0.424,"poisson_LT":0.476,"poisson_RT":0.774,"poisson_TR":0.349,"poisson_RL":0.065,"poisson_TL":0.037}}}})json";
        CHECK (! materials.loadFromString (bad),
               "Orthotropic: ratio_GRT_EL = \"n/a\" (string, not a legal null) is rejected");
    }

    // Negative 5: source_species = "" (empty string; must be one of the four
    // transcribed species names).
    // This line, if relaxed to accept an empty/unlisted species, should turn
    // this test FAIL.
    {
        MaterialDB materials;
        const auto bad = R"json({"materials":{"wood_spruce":{"display_name":"Spruce","density":450,"youngs_modulus":12000000000,"poisson_ratio":0.37,"damping":{"eta":0.007,"beam_plate_beta_air":0.0000003,"beam_plate_gamma_radiation":0.00005},"orthotropic":{"source_species":"","moisture_content_pct":12,"mp_percent":27,"ratio_ET_EL":0.043,"ratio_ER_EL":0.078,"ratio_GLR_EL":0.064,"ratio_GLT_EL":0.061,"ratio_GRT_EL":0.003,"poisson_LR":0.372,"poisson_LT":0.467,"poisson_RT":0.435,"poisson_TR":0.245,"poisson_RL":0.040,"poisson_TL":0.025}}}})json";
        CHECK (! materials.loadFromString (bad),
               "Orthotropic: source_species = \"\" (empty) is rejected -- whole file fails closed");
    }

    // Negative 6 (transactional): a failed orthotropic block must NOT destroy an
    // already-loaded, otherwise-good database -- same guarantee
    // testMaterialDatabaseIsTransactional() proves for the existing fields.
    // This line, if relaxed so a bad block partially commits or wipes the
    // database, should turn this test FAIL.
    {
        MaterialDB materials;
        loadTestMaterial (materials);
        const int originalSize = materials.size();
        const auto bad = R"json({"materials":{"wood_spruce":{"display_name":"Spruce","density":450,"youngs_modulus":12000000000,"poisson_ratio":0.37,"damping":{"eta":0.007,"beam_plate_beta_air":0.0000003,"beam_plate_gamma_radiation":0.00005},"orthotropic":{"source_species":"Spruce, Sitka","moisture_content_pct":12,"mp_percent":27,"ratio_ET_EL":1.5,"ratio_ER_EL":0.078,"ratio_GLR_EL":0.064,"ratio_GLT_EL":0.061,"ratio_GRT_EL":0.003,"poisson_LR":0.372,"poisson_LT":0.467,"poisson_RT":0.435,"poisson_TR":0.245,"poisson_RL":0.040,"poisson_TL":0.025}}}})json";
        CHECK (! materials.loadFromString (bad),
               "Orthotropic: (setup for transactional check) bad block is rejected");
        CHECK (materials.size() == originalSize
               && materials.getMaterial ("steel") != nullptr
               && materials.getMaterial ("wood_spruce") != nullptr,
               "Orthotropic: a failed reload preserves the last known-good database intact");
    }
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

// B6 Phase 3/4 audit fix (2026-08-28, adversarial-audit finding #1):
// dumpModes() sets DiagnosticOverrides::capturePhysicsOnlyModes = true so it
// can read CimbalomVoice's physics-only per-partial amplitudes. The
// surrounding comment used to argue this could never leak into a render
// because RenderApp.cpp's --dump-modes and normal-render CLI branches are
// mutually exclusive within one process -- but THIS binary (audit_repro.cpp)
// is exactly the counter-example that argument didn't cover: it calls
// dumpModes() and then render() on the SAME process, sometimes the SAME
// ScoreRenderer instance (see testCustomDumpUsesEffectiveParameters() just
// above, which dumps a "custom" score without ever rendering it). Before the
// fix, dumpModes() left the flag permanently true, so any render() call in
// this binary AFTER a dumpModes() call would run noteOn() with the
// physics-only capture bookkeeping still enabled -- not audible (the capture
// is additive bookkeeping, per testPhysicsOnlyCaptureDoesNotAffectRender()),
// but a violated invariant nonetheless (the doc comment's claim that
// "render()/renderEvent() never set this" was contradicted by dumpModes()
// leaving it set behind them). This test proves the ACTUAL enforced
// invariant end-to-end: dump-then-render produces byte-identical WAV output
// to a render that never called dumpModes() at all, and the flag reads back
// false immediately after dumpModes() returns.
void testDumpModesDoesNotLeakPhysicsOnlyFlagIntoRender()
{
    MaterialDB materials;
    loadTestMaterial (materials);

    Score score;
    score.global.sampleRate = 48000;
    score.global.masterVolume = 1.0;
    score.global.randomSeed = 424242;
    score.global.effects.reverbWet = 0.0;
    score.global.effects.delayWet = 0.0;
    score.global.effects.distortionWet = 0.0;
    score.exportSettings.normalize = false;
    score.exportSettings.tailSilenceMs = 0.0;

    ScoreEvent cimbalom;
    cimbalom.time = 0.0;
    cimbalom.duration = 0.2;
    cimbalom.engine = "cimbalom";
    cimbalom.note = "C4";
    cimbalom.velocity = 0.8f;
    cimbalom.material = "steel";
    score.events.push_back (cimbalom);

    DiagnosticOverrides::capturePhysicsOnlyModes = false;   // clean starting
        // state regardless of what earlier tests in this binary left behind

    // Baseline: a renderer that NEVER calls dumpModes() at all.
    const auto baselineFile = juce::File::createTempFile (".wav");
    ScoreRenderer baselineRenderer;
    baselineRenderer.setMaterialDB (&materials);
    CHECK (baselineRenderer.render (score, baselineFile),
           "Dump-leak repro: never-dumped baseline renders successfully");

    // Same score, same ScoreRenderer instance, dumpModes() called FIRST --
    // this is the exact sequence tests/audit_repro.cpp itself already
    // exercises across different test functions in one process.
    const auto dumpedThenRenderedFile = juce::File::createTempFile (".wav");
    ScoreRenderer dumpingRenderer;
    dumpingRenderer.setMaterialDB (&materials);
    const auto dumpJson = dumpingRenderer.dumpModes (score);
    CHECK (! dumpJson.isEmpty(), "Dump-leak repro: dumpModes() produced output");
    CHECK (! DiagnosticOverrides::capturePhysicsOnlyModes,
           "capturePhysicsOnlyModes reads back false immediately after "
           "dumpModes() returns (RAII guard restored it, not left permanently true)");
    CHECK (dumpingRenderer.render (score, dumpedThenRenderedFile),
           "Dump-leak repro: post-dump render on the same instance succeeds");

    juce::MemoryBlock baselineBytes, dumpedThenRenderedBytes;
    const bool loaded = baselineFile.loadFileAsData (baselineBytes)
        && dumpedThenRenderedFile.loadFileAsData (dumpedThenRenderedBytes);
    CHECK (loaded && baselineBytes == dumpedThenRenderedBytes,
           "Calling dumpModes() before render() produces byte-identical WAV "
           "output to a render that never called dumpModes() at all -- "
           "capturePhysicsOnlyModes does not leak from the diagnostic dump "
           "path into a subsequent render in the same process");

    baselineFile.deleteFile();
    dumpedThenRenderedFile.deleteFile();
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

// ---------------------------------------------------------------------------
// WF0907-E7 helpers (K-03 oversized-block chunking, K-02 wet-gain quantifier)
// ---------------------------------------------------------------------------

// Deterministic fixed-seed white noise. std::mt19937 (not JUCE's Random) so
// the sequence is portable and traceable to a documented standard PRNG
// rather than an internal, undocumented algorithm.
juce::AudioBuffer<float> generateWhiteNoise (int numSamples, int numChannels,
                                             unsigned seed)
{
    juce::AudioBuffer<float> buffer (numChannels, numSamples);
    std::mt19937 rng (seed);
    std::uniform_real_distribution<float> dist (-1.0f, 1.0f);
    for (int ch = 0; ch < numChannels; ++ch)
    {
        float* data = buffer.getWritePointer (ch);
        for (int i = 0; i < numSamples; ++i)
            data[i] = dist (rng);
    }
    return buffer;
}

// Synthetic exponential-decay white-noise impulse response, written to a
// temp WAV file for EffectChain::loadImpulseResponse(). Purely a test
// fixture (no physical measurement backs this shape); t60Seconds only
// controls where the envelope crosses -60 dB: env(t) = 10^(-3 t / t60).
juce::File writeExponentialDecayIr (double sampleRate, double t60Seconds,
                                    double lengthSeconds, unsigned seed)
{
    const int numSamples = std::max (1, (int) std::lround (sampleRate * lengthSeconds));
    auto ir = generateWhiteNoise (numSamples, 2, seed);
    for (int ch = 0; ch < 2; ++ch)
    {
        float* data = ir.getWritePointer (ch);
        for (int i = 0; i < numSamples; ++i)
        {
            const double t = (double) i / sampleRate;
            const double env = std::pow (10.0, -3.0 * t / t60Seconds);
            data[i] = (float) (data[i] * env);
        }
    }
    auto file = juce::File::createTempFile (".wav");
    WavWriter::write (file, ir, sampleRate, 32, false);
    return file;
}

// WF0925-K1 (engineering-gaps:E15), two parts:
// (a) Known-answer vectors for IRLibrary's self-contained SHA-256 (until now
//     only hand-checked once, wf0908_P3_f03.txt:41). The expected digests
//     were re-computed independently with Python's hashlib on 2026-09-25
//     (command + output in reports/gate_outputs/wf0925_K1_*.txt) -- not
//     typed from memory. "" and "abc" cover the one-block padding path; the
//     56-byte message forces the padding into a SECOND block.
//     Source note (WF0925-K2): the "abc" and 56-byte (448-bit) digests are
//     also FIPS 180-2 Appendix B.1 / B.2 (printed pp. 35 / 39 of
//     https://csrc.nist.gov/publications/fips/fips180-2/fips180-2.pdf,
//     fetched 2026-09-25; both match word for word, extract in
//     reports/gate_outputs/wf0925_K2_e15_sources.txt). The empty-message
//     digest does NOT appear in FIPS 180-2; its only source here is Python
//     hashlib.
// (b) Corrupted library entry repair: import an IR, damage the managed copy
//     (truncate to half, then a 0-byte file), re-import the SAME source,
//     and require the entry's content hash to be correct again and no
//     ".tmp-*" leftover. Before WF0925-K1, importFile() reused any existing
//     file of that name without re-hashing, so the damage was permanent.
//     Uses the real IRLibrary::getDirectory() (the same user library H7 in
//     tests/host_probe.cpp uses); the fixture is fresh seeded noise, so its
//     sha-named entry cannot collide with a real user IR, and it is removed
//     at the end.
void testIRLibrarySha256AndCorruptEntryRepair()
{
    CHECK (IRLibrary::detail::sha256Hex ("", 0)
               == "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
           "E15: IRLibrary SHA-256 known answer, empty message");
    CHECK (IRLibrary::detail::sha256Hex ("abc", 3)
               == "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad",
           "E15: IRLibrary SHA-256 known answer, \"abc\"");
    static const char twoBlockMsg[] =
        "abcdbcdecdefdefgefghfghighijhijkijkljklmklmnlmnomnopnopq";
    CHECK (IRLibrary::detail::sha256Hex (twoBlockMsg, sizeof (twoBlockMsg) - 1)
               == "248d6a61d20638b8e5c026930c3e6039a33ce45964ff2167f6ecedd419db06c1",
           "E15: IRLibrary SHA-256 known answer, 56-byte two-block message");

    const auto source = writeExponentialDecayIr (48000.0, 0.2, 0.05, 925u);
    const auto sourceSha = IRLibrary::hashFile (source);
    juce::String err;
    const auto ref = IRLibrary::importFile (source, err);
    CHECK (sourceSha.isNotEmpty() && ref.sha256 == sourceSha,
           "E15: fixture IR imported into the managed library under its content hash");
    const auto libFile = IRLibrary::fileForSha (sourceSha);
    CHECK (libFile.existsAsFile() && IRLibrary::hashFile (libFile) == sourceSha,
           "E15: fresh library entry's bytes hash to its own name");

    auto noTempLeft = [&libFile] ()
    {
        return libFile.getParentDirectory()
                   .findChildFiles (juce::File::findFiles, false,
                                    libFile.getFileName() + ".tmp-*")
                   .isEmpty();
    };

    // Damage 1: truncated to half (a half-written copy).
    juce::MemoryBlock bytes;
    libFile.loadFileAsData (bytes);
    {
        juce::FileOutputStream out (libFile);
        if (out.openedOk())
        {
            out.setPosition (0);
            out.truncate();
            out.write (bytes.getData(), bytes.getSize() / 2);
        }
    }
    CHECK (libFile.existsAsFile() && IRLibrary::hashFile (libFile) != sourceSha,
           "E15: precondition -- truncated library entry no longer matches its name");
    const auto ref2 = IRLibrary::importFile (source, err);
    CHECK (ref2.sha256 == sourceSha && IRLibrary::hashFile (libFile) == sourceSha,
           "E15: re-importing the original file repairs a truncated library entry");
    CHECK (noTempLeft(), "E15: no .tmp-* file left next to the repaired entry");

    // Damage 2: a 0-byte file (hashFile() returns "" for it).
    {
        juce::FileOutputStream out (libFile);
        if (out.openedOk())
        {
            out.setPosition (0);
            out.truncate();
        }
    }
    CHECK (libFile.existsAsFile() && libFile.getSize() == 0,
           "E15: precondition -- library entry emptied to 0 bytes");
    const auto ref3 = IRLibrary::importFile (source, err);
    CHECK (ref3.sha256 == sourceSha && IRLibrary::hashFile (libFile) == sourceSha,
           "E15: re-importing the original file repairs a 0-byte library entry");
    CHECK (noTempLeft(), "E15: no .tmp-* file left after the second repair");

    // Intact entry: re-import returns the same identity and leaves the entry
    // correct. (Whether it was skipped or rewritten is not observable here --
    // CopyFile preserves the source's mtime -- so no such claim is made.)
    const auto ref4 = IRLibrary::importFile (source, err);
    CHECK (ref4.sha256 == sourceSha && IRLibrary::hashFile (libFile) == sourceSha
               && noTempLeft(),
           "E15: re-importing onto an intact entry keeps identity and content");

    libFile.deleteFile();
    IRLibrary::sidecarForSha (sourceSha).deleteFile();
    source.deleteFile();
}

// Wires the reverb-mode/mix pointers, prepares the chain, and -- when an IR
// file is supplied -- loads it and prepares a SECOND time. juce_Convolution.h
// documents that prepare() blocks until the IR from the most recent
// loadImpulseResponse() call is fully initialised, so the second prepare()
// is the synchronisation point that makes the background-thread IR load
// deterministic for a bit-exact comparison; without it, process() could run
// against a not-yet-ready convolution engine depending on thread timing.
void prepareChainWithOptionalIr (EffectChain& chain, double sampleRate,
                                 int maxBlockSize, std::atomic<float>* modePtr,
                                 std::atomic<float>* mixPtr, const juce::File* irFile)
{
    chain.pReverbMode = modePtr;
    chain.pReverbMix  = mixPtr;
    chain.prepare (sampleRate, maxBlockSize);
    if (irFile != nullptr)
    {
        chain.loadImpulseResponse (*irFile);
        chain.prepare (sampleRate, maxBlockSize);
    }
}

// Runs `chain.processBlock` once per (startSample, count) range in `ranges`,
// each range copied out of `source` into its own sub-buffer and processed
// independently, then concatenated into the returned buffer. Passing a
// single range spanning the whole signal exercises EffectChain's internal
// oversized-block chunking; passing several smaller ranges simulates a host
// calling processBlock once per host-sized callback.
juce::AudioBuffer<float> processInChunks (
    EffectChain& chain, const juce::AudioBuffer<float>& source,
    const std::vector<std::pair<int, int>>& ranges)
{
    int total = 0;
    for (auto& r : ranges) total += r.second;
    juce::AudioBuffer<float> out (source.getNumChannels(), total);
    int dstPos = 0;
    for (auto& r : ranges)
    {
        juce::AudioBuffer<float> sub (source.getNumChannels(), r.second);
        for (int ch = 0; ch < source.getNumChannels(); ++ch)
            sub.copyFrom (ch, 0, source, ch, r.first, r.second);
        chain.processBlock (sub);
        for (int ch = 0; ch < source.getNumChannels(); ++ch)
            out.copyFrom (ch, dstPos, sub, ch, 0, r.second);
        dstPos += r.second;
    }
    return out;
}

bool buffersBitExact (const juce::AudioBuffer<float>& a,
                      const juce::AudioBuffer<float>& b, int numSamples)
{
    if (a.getNumChannels() != b.getNumChannels()) return false;
    for (int ch = 0; ch < a.getNumChannels(); ++ch)
    {
        const float* da = a.getReadPointer (ch);
        const float* db = b.getReadPointer (ch);
        for (int i = 0; i < numSamples; ++i)
            if (da[i] != db[i])
                return false;
    }
    return true;
}

int countMismatches (const juce::AudioBuffer<float>& a,
                     const juce::AudioBuffer<float>& b, int startSample,
                     int numSamples)
{
    int mismatches = 0;
    for (int ch = 0; ch < a.getNumChannels(); ++ch)
    {
        const float* da = a.getReadPointer (ch);
        const float* db = b.getReadPointer (ch);
        for (int i = startSample; i < startSample + numSamples; ++i)
            if (da[i] != db[i])
                ++mismatches;
    }
    return mismatches;
}

// K-03: EffectChain::processBlock() called once with a block larger than the
// maxBlock negotiated in prepare() must produce output bit-identical to a
// host that instead calls processBlock() once per <=maxBlock chunk. Before
// this workcard's fix, EffectChain silently fell back to the algorithmic
// reverb whenever numSamples > maxBlock even in IR mode (EffectChain.h's
// irMode guard), which this test would have caught as a mismatch between
// once-call and chunked-call output.
void testEffectChainOversizedBlockMatchesExternalChunking()
{
    const double sampleRate = 48000.0;
    const int maxBlock = 512;
    const int totalSamples = 1537; // 512 + 512 + 513, per the workcard spec

    const auto irFile = writeExponentialDecayIr (sampleRate, 0.3, 1.0, 909090);
    const auto noise = generateWhiteNoise (totalSamples, 2, 12345);

    std::atomic<float> irModeOn { 1.0f };
    std::atomic<float> wetMix { 1.0f };

    // (a) IR mode: one 1537-sample call (internal auto-chunking) vs three
    // externally chunked 512+512+513 calls, from identically prepared
    // fresh chain instances (same initial state).
    EffectChain onceIr;
    prepareChainWithOptionalIr (onceIr, sampleRate, maxBlock, &irModeOn, &wetMix, &irFile);
    const auto onceIrOut = processInChunks (onceIr, noise, { { 0, totalSamples } });

    EffectChain chunkedIr;
    prepareChainWithOptionalIr (chunkedIr, sampleRate, maxBlock, &irModeOn, &wetMix, &irFile);
    const auto chunkedIrOut = processInChunks (
        chunkedIr, noise, { { 0, 512 }, { 512, 512 }, { 1024, 513 } });

    CHECK (buffersBitExact (onceIrOut, chunkedIrOut, totalSamples),
          "K-03(a): IR-mode EffectChain::processBlock on one 1537-sample call is "
          "bit-identical to three externally chunked 512+512+513 calls");

    // (c) Mutant: silently drop the input sample at global index 511 (the
    // last sample the first 512-sample chunk should have processed) by
    // feeding only 511 samples for that chunk, then resuming at the correct
    // source offset for the remaining chunks. This is exactly the failure
    // mode "chunk boundary drops the last sample" -- if the comparison in
    // (a) could not detect a missing sample, it would be meaningless.
    EffectChain mutantIr;
    prepareChainWithOptionalIr (mutantIr, sampleRate, maxBlock, &irModeOn, &wetMix, &irFile);
    const auto mutantOut = processInChunks (
        mutantIr, noise, { { 0, 511 }, { 512, 512 }, { 1024, 513 } });
    const int overlap = std::min (onceIrOut.getNumSamples(), mutantOut.getNumSamples());
    const int mismatches = countMismatches (onceIrOut, mutantOut, 0, overlap);
    CHECK (mismatches > 0,
          "K-03(c): a mutant chunking that drops one input sample at a chunk "
          "boundary is NOT bit-identical to the correct reference -- proving "
          "the bit-exact comparison in (a)/(b) has teeth");

    // (b) Same one-call-vs-external-chunking check in ALGO mode (no IR
    // pointer, so EffectChain's irMode guard is false regardless of size).
    EffectChain onceAlgo;
    prepareChainWithOptionalIr (onceAlgo, sampleRate, maxBlock, nullptr, &wetMix, nullptr);
    const auto onceAlgoOut = processInChunks (onceAlgo, noise, { { 0, totalSamples } });

    EffectChain chunkedAlgo;
    prepareChainWithOptionalIr (chunkedAlgo, sampleRate, maxBlock, nullptr, &wetMix, nullptr);
    const auto chunkedAlgoOut = processInChunks (
        chunkedAlgo, noise, { { 0, 512 }, { 512, 512 }, { 1024, 513 } });

    CHECK (buffersBitExact (onceAlgoOut, chunkedAlgoOut, totalSamples),
          "K-03(b): ALGO-mode EffectChain::processBlock on one 1537-sample call is "
          "bit-identical to three externally chunked 512+512+513 calls");

    irFile.deleteFile();
}

// K-02: quantifies (does not PASS/FAIL) how many dB louder EffectChain's IR
// wet path is than its ALGO wet path for a matched-T60 reverb, because
// SimpleReverb.h:155-156 multiplies wet output by an extra 0.15 that the
// convolution path (EffectChain.h) does not. Numbers originally fed
// reports/decision_packets/K02_reverb_wet_scale.zh-TW.md; this function
// asserts nothing.
//
// WF0914-D9c (月月 2026-09-16 裁決 D9 選項 A;
// reports/decision_packets/D9_ir_loudness_alignment.zh-TW.md): EffectChain
// now applies a fixed makeup gain (EffectChain::kIrWetMakeupGain = 26.9f,
// +28.58 dB) to the IR wet signal to compensate this structural gap, so the
// "[K-02] RMS difference (IR - ALGO)" this function prints is expected to
// land near 0 dB now (0 +/- 0.25 dB per the D9c workcard, citing the 0.24 dB
// spread already measured across the 4 real/synthetic IR samples in
// reports/gate_outputs/wf0914_D9b_ir_injection.txt) instead of the
// pre-D9c -28.483 dB. The measurement method itself is unchanged -- only
// EffectChain's product-code behaviour changed, which this quantifier is
// designed to observe.
struct DecayMeasurement { double referenceDb; double t60Seconds; bool measured; };

DecayMeasurement measureNoiseBurstDecay (const juce::AudioBuffer<float>& buffer,
                                         int burstSamples, double sampleRate)
{
    const int win = 512;
    auto windowRmsDb = [&] (int start) -> double
    {
        double sumSq = 0.0;
        int count = 0;
        for (int ch = 0; ch < buffer.getNumChannels(); ++ch)
        {
            const float* data = buffer.getReadPointer (ch);
            for (int i = start; i < start + win && i < buffer.getNumSamples(); ++i)
            {
                sumSq += (double) data[i] * (double) data[i];
                ++count;
            }
        }
        if (count == 0) return -300.0;
        const double rms = std::sqrt (sumSq / (double) count);
        return rms > 1.0e-12 ? 20.0 * std::log10 (rms) : -300.0;
    };

    // Reference level: average windowed RMS (dB) over the steady-state
    // portion just before the burst ends.
    const int refStart = std::max (0, burstSamples - win * 8);
    double refSum = 0.0;
    int refCount = 0;
    for (int s = refStart; s + win <= burstSamples; s += win)
    {
        refSum += windowRmsDb (s);
        ++refCount;
    }
    const double referenceDb = refCount > 0
        ? refSum / (double) refCount
        : windowRmsDb (std::max (0, burstSamples - win));

    // Walk forward from the burst's end until the level falls 60 dB below
    // the reference (interrupted-noise T60 method).
    const double target = referenceDb - 60.0;
    for (int s = burstSamples; s + win <= buffer.getNumSamples(); s += win)
    {
        if (windowRmsDb (s) <= target)
            return { referenceDb, (double) (s - burstSamples) / sampleRate, true };
    }
    return { referenceDb, -1.0, false };
}

void reportReverbWetGainQuantification()
{
    const double sampleRate = 48000.0;
    const int burstSamples = (int) std::lround (sampleRate * 2.0);   // 2 s noise
    const int tailSamples  = (int) std::lround (sampleRate * 12.0);  // 12 s decay tail
    const int totalSamples = burstSamples + tailSamples;

    juce::AudioBuffer<float> input (2, totalSamples);
    input.clear();
    {
        const auto burst = generateWhiteNoise (burstSamples, 2, 271828);
        for (int ch = 0; ch < 2; ++ch)
            input.copyFrom (ch, 0, burst, ch, 0, burstSamples);
    }

    std::atomic<float> wetMix { 1.0f };

    // ALGO, reverb defaults (pReverbSize/pReverbDecay left null -> roomSize
    // 0.5, no authored decay -- SimpleReverb.h's default emergent T60).
    EffectChain algoChain;
    prepareChainWithOptionalIr (algoChain, sampleRate, 2048, nullptr, &wetMix, nullptr);
    juce::AudioBuffer<float> algoOut = input;
    algoChain.processBlock (algoOut);
    const auto algoDecay = measureNoiseBurstDecay (algoOut, burstSamples, sampleRate);

    std::printf ("[K-02] ALGO wet output: steady-state RMS = %.3f dBFS, "
                "measured T60 = %s\n", algoDecay.referenceDb,
                algoDecay.measured
                    ? (std::to_string (algoDecay.t60Seconds) + " s").c_str()
                    : "NOT FOUND within 12 s tail");

    const double algoT60 = algoDecay.measured ? algoDecay.t60Seconds : 1.0;
    if (! algoDecay.measured)
        std::printf ("[K-02] WARNING: falling back to an assumed 1.0 s T60 for "
                    "the IR match step because measurement did not converge.\n");

    // IR: synthetic exponential-decay IR whose T60 is reverse-engineered
    // from the ALGO measurement above, so the only intended difference
    // between the two wet outputs is the 0.15 scale factor (and whatever
    // residual spectral/diffusion differences the two algorithms carry).
    const double irLengthSeconds = std::max (1.0, algoT60 * 1.5);
    const auto irFile = writeExponentialDecayIr (sampleRate, algoT60, irLengthSeconds, 555111);

    std::atomic<float> irModeOn { 1.0f };
    EffectChain irChain;
    prepareChainWithOptionalIr (irChain, sampleRate, 2048, &irModeOn, &wetMix, &irFile);
    juce::AudioBuffer<float> irOut = input;
    irChain.processBlock (irOut);
    const auto irDecay = measureNoiseBurstDecay (irOut, burstSamples, sampleRate);

    std::printf ("[K-02] IR   wet output (matched-T60 IR = %.3f s): steady-state RMS = "
                "%.3f dBFS, measured T60 = %s\n", algoT60, irDecay.referenceDb,
                irDecay.measured
                    ? (std::to_string (irDecay.t60Seconds) + " s").c_str()
                    : "NOT FOUND within 12 s tail");

    const double rmsDiffDb = irDecay.referenceDb - algoDecay.referenceDb;
    const double theoreticalDb = 20.0 * std::log10 (1.0 / 0.15);
    std::printf ("[K-02] RMS difference (IR - ALGO) = %.3f dB\n", rmsDiffDb);
    std::printf ("[K-02] Theoretical difference if ALGO's 0.15 factor were absent "
                "(20*log10(1/0.15)) = %.3f dB\n", theoreticalDb);

    irFile.deleteFile();
}

// WF0914-D9b: external-IR variant of K-02
// (docs/workcards/WF0914_D9b_ir_injection.md). Reproduces the exact method
// of reportReverbWetGainQuantification() above verbatim (same seed 271828,
// same 2s-burst/12s-tail geometry, same ALGO reference measurement, same
// -60dB-crossing T60 measurement, same wetMix=1.0) but loads a real WAV file
// named by the caller into the IR chain instead of
// writeExponentialDecayIr()'s synthetic fixture. This function is only
// reached from main() when TSUKI_K02_EXTERNAL_IR is set (see below); the
// unconditional reportReverbWetGainQuantification() call above it is
// untouched, so default (env var unset) behaviour is byte-for-byte
// unchanged -- WF0914_D9b GATE 3.
//
// WF0914-D9c: since EffectChain now applies kIrWetMakeupGain (see
// EffectChain.h), the "[K-02-EXT] RMS difference" this function prints for
// each external IR is expected to land near 0 dB (0 +/- 0.25 dB, per the
// D9c workcard) instead of the pre-D9c ~-28.5 dB this function originally
// measured for the 3 EchoThief IRs.
//
// Fails closed: validates the path opens as a readable audio file via
// JUCE's AudioFormatManager (the same openAudioFile() helper this file
// already uses for its own fixtures) BEFORE handing it to
// EffectChain::loadImpulseResponse(). This matters because
// juce::dsp::Convolution's own file loader does NOT fail closed on an
// unreadable file: juce_Convolution.cpp's loadStreamToBuffer() returns an
// empty, zero-sample-rate buffer when AudioFormatManager::createReaderFor()
// returns nullptr, and Convolution silently proceeds with that empty IR
// (near-silent wet output) rather than raising an error. Pre-validating
// here means an unreadable path is reported explicitly instead of silently
// producing a near-silent-but-plausible-looking measurement.
//
// Sample-rate mismatch is NOT treated as a fail-closed condition: JUCE's
// juce::dsp::Convolution always resamples a loaded IR to the current
// ProcessSpec sample rate before it becomes active, regardless of the
// source file's native rate -- traced to
// libs/JUCE/modules/juce_dsp/frequency/juce_Convolution.cpp,
// ConvolutionEngine::makeEngine(): `resampleImpulseResponse (impulseResponse,
// originalSampleRate, processSpec.sampleRate)` runs unconditionally (not
// gated on a rate-equality check), followed by
// `normaliseImpulseResponse (resampled)` because
// EffectChain::loadImpulseResponse() (src/effects/EffectChain.h) calls
// `convolution.loadImpulseResponse (file, Stereo::yes, Trim::yes, 0)` and
// leaves the trailing `Normalise` parameter at its declared default
// (`Normalise::yes`, juce_Convolution.h). So a 44.1kHz EchoThief WAV loaded
// while this function renders at 48kHz is resampled and energy-normalised
// by JUCE itself, not rejected -- this is the actual product code path
// (EffectChain), not an approximation of it.
bool reportReverbWetGainQuantificationExternalIr (const juce::String& irPathArg)
{
    const juce::File irFile (irPathArg);
    if (openAudioFile (irFile) == nullptr)
    {
        std::printf ("[K-02-EXT] ERROR: TSUKI_K02_EXTERNAL_IR does not name a "
                    "readable audio file (missing, or format not recognised "
                    "by JUCE's AudioFormatManager): %s\n",
                    irPathArg.toRawUTF8());
        return false;
    }

    const double sampleRate = 48000.0;
    const int burstSamples = (int) std::lround (sampleRate * 2.0);   // 2 s noise
    const int tailSamples  = (int) std::lround (sampleRate * 12.0);  // 12 s decay tail
    const int totalSamples = burstSamples + tailSamples;

    juce::AudioBuffer<float> input (2, totalSamples);
    input.clear();
    {
        const auto burst = generateWhiteNoise (burstSamples, 2, 271828);
        for (int ch = 0; ch < 2; ++ch)
            input.copyFrom (ch, 0, burst, ch, 0, burstSamples);
    }

    std::atomic<float> wetMix { 1.0f };

    // ALGO reference, identical setup to reportReverbWetGainQuantification()
    // above (this is a separate process invocation each time
    // TSUKI_K02_EXTERNAL_IR changes, so the ALGO reference is re-measured
    // rather than reused).
    EffectChain algoChain;
    prepareChainWithOptionalIr (algoChain, sampleRate, 2048, nullptr, &wetMix, nullptr);
    juce::AudioBuffer<float> algoOut = input;
    algoChain.processBlock (algoOut);
    const auto algoDecay = measureNoiseBurstDecay (algoOut, burstSamples, sampleRate);

    std::printf ("[K-02-EXT] ALGO wet output: steady-state RMS = %.3f dBFS, "
                "measured T60 = %s\n", algoDecay.referenceDb,
                algoDecay.measured
                    ? (std::to_string (algoDecay.t60Seconds) + " s").c_str()
                    : "NOT FOUND within 12 s tail");

    std::atomic<float> irModeOn { 1.0f };
    EffectChain irChain;
    prepareChainWithOptionalIr (irChain, sampleRate, 2048, &irModeOn, &wetMix, &irFile);
    juce::AudioBuffer<float> irOut = input;
    irChain.processBlock (irOut);
    const auto irDecay = measureNoiseBurstDecay (irOut, burstSamples, sampleRate);

    std::printf ("[K-02-EXT] IR   wet output (external IR file = %s): "
                "steady-state RMS = %.3f dBFS, measured T60 = %s\n",
                irPathArg.toRawUTF8(), irDecay.referenceDb,
                irDecay.measured
                    ? (std::to_string (irDecay.t60Seconds) + " s").c_str()
                    : "NOT FOUND within 12 s tail");

    const double rmsDiffDb = irDecay.referenceDb - algoDecay.referenceDb;
    const double theoreticalDb = 20.0 * std::log10 (1.0 / 0.15);
    std::printf ("[K-02-EXT] RMS difference (IR - ALGO) = %.3f dB\n", rmsDiffDb);
    std::printf ("[K-02-EXT] Theoretical difference if ALGO's 0.15 factor were absent "
                "(20*log10(1/0.15)) = %.3f dB\n", theoreticalDb);

    return true;
}

// WF0925-K2 (09-25 status check, staged-review:D9c-guard): pins
// EffectChain::kIrWetMakeupGain to the value 月月 decided on 2026-09-16
// (D9 option A, DECIDED CONVENTION: x26.9 = +28.58 dB; see the 裁決記錄
// section of reports/decision_packets/D9_ir_loudness_alignment.zh-TW.md,
// landed by docs/workcards/WF0914_D9c_ir_makeup_gain.md). Before this CHECK
// nothing turned red if the constant was edited or deleted: K-02 below only
// prints, HostProbe has no IR-loudness scenario, and the CLI / 8-score
// bit-identity renders never go through EffectChain.
//
// Deliberately NOT asserted here: |IR - ALGO| <= 0.25 dB on the K-02
// measurement. That 0.25 dB figure comes from the D9c workcard, not from
// 月月's decision, so making it a pass/fail limit would be a new tolerance
// (R2); it is left for a decision packet. K-02 / K-02-EXT stay
// informational, unchanged.
//
// Access: kIrWetMakeupGain is a PRIVATE static constexpr member and this
// card may not touch src/. C++'s explicit-instantiation access rule
// ([temp.spec.general]/6 in the current working draft,
// https://eel.is/c++draft/temp.spec.general: "The usual access checking
// rules do not apply to names in a declaration of an explicit
// instantiation ...") lets the explicit instantiation below name
// &EffectChain::kIrWetMakeupGain; the friend function it defines hands that
// address to the test. Only the constant is read; no product code runs.
const float* effectChainIrWetMakeupGainAddress();

template <const float* Member>
struct EffectChainIrWetMakeupGainAccess
{
    friend const float* effectChainIrWetMakeupGainAddress() { return Member; }
};

template struct EffectChainIrWetMakeupGainAccess<&EffectChain::kIrWetMakeupGain>;

void testIrWetMakeupGainPinnedToDecision()
{
    const float gain = *effectChainIrWetMakeupGainAddress();
    std::printf ("[D9c-guard] EffectChain::kIrWetMakeupGain = %.9g\n", (double) gain);
    CHECK (gain == 26.9f,
           "D9c-guard: EffectChain::kIrWetMakeupGain == 26.9f (decision 2026-09-16, "
           "D9 option A, DECIDED CONVENTION; "
           "reports/decision_packets/D9_ir_loudness_alignment.zh-TW.md)");
}
}

int main()
{
    std::printf ("TsukiSynth regression tests\n");
    testEnvelopeRelease();
    testAudioFifoKeepsNewestUnreadData();
    testMaterialDatabaseIsTransactional();
    testOrthotropicSchemaFailClosed();
    testChromaticMidiTuning();
    testScoreParserFields();
    testScoreParserRejectsInvalidContract();
    testCustomDumpUsesEffectiveParameters();
    testDumpModesDoesNotLeakPhysicsOnlyFlagIntoRender();
    testRendererRejectsAttackOnlyModalEvent();
    testSemanticEventOrderIsBitExact();
    testRendererSupportsContractSampleRates();
    testCausalityLocalityAndLinearSuperposition();
    testFullWetShortReverbHasAudibleTail();
    testFlacWriter();
    testFmRenderTailAndWall();
    testLayerSourceMasterAndTrim();
    testEffectChainOversizedBlockMatchesExternalChunking();
    testIRLibrarySha256AndCorruptEntryRepair();
    testIrWetMakeupGainPinnedToDecision();

    std::printf ("%s (%d failure%s)\n",
                 failures == 0 ? "PASS" : "FAIL",
                 failures,
                 failures == 1 ? "" : "s");

    std::printf ("\nWF0907-E7 K-02 quantification (informational, no PASS/FAIL):\n");
    reportReverbWetGainQuantification();

    // WF0914-D9b: external-IR K-02 variant. Only runs when this env var is
    // explicitly set; when unset (ctest's default invocation, GATE 2/3),
    // this entire block is skipped and everything above is unchanged --
    // default behaviour is byte-for-byte identical to before this workcard.
    if (const char* externalIrPath = std::getenv ("TSUKI_K02_EXTERNAL_IR"))
    {
        std::printf ("\nWF0914-D9b K-02 external-IR quantification "
                    "(informational, no PASS/FAIL):\n");
        if (! reportReverbWetGainQuantificationExternalIr (juce::String (externalIrPath)))
        {
            std::printf ("WF0914-D9b: TSUKI_K02_EXTERNAL_IR was set but the IR "
                        "could not be loaded -- failing closed (see error "
                        "above); no fallback to the synthetic IR.\n");
            return 1;
        }
    }

    return failures == 0 ? 0 : 1;
}
