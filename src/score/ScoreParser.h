#pragma once

#include <juce_core/juce_core.h>
#include <algorithm>
#include <cmath>
#include <initializer_list>
#include <limits>
#include <cstdint>
#include <regex>
#include <vector>
#include <string>

struct ScoreMeta
{
    std::string title;
    std::string id;
    std::string author;
    std::string description;
};

struct ScoreEffects
{
    double reverbDecay = 2.0;
    double reverbWet   = 0.0;
    double delayTimeMs = 0.0;
    double delayFeedback = 0.0;
    double delayWet    = 0.0;
    double wallDistanceM = 0.0;
    std::string wallMaterial;

    std::string distortionType = "overdrive";
    double distortionDrive       = 0.0;
    double distortionInstability = 0.0;
    double distortionWet         = 0.0;
};

struct ScoreGlobal
{
    double bpm          = 120.0;
    int    sampleRate   = 48000;
    double masterVolume = 0.8;
    uint64_t randomSeed = 0x5453554B4953594Eull;
    ScoreEffects effects;
};

struct ScoreEvent
{
    double      time     = 0.0;
    double      duration = 1.0;
    std::string engine;
    std::string note;
    // velocity in [0,1] -- see the "velocity law" comment block at its parse
    // site below (ROADMAP_PHYSICS.md M6-6a) for the physical semantics.
    float       velocity = 0.8f;
    std::string material = "steel";
    double      strikePosition = 0.3;
    double      thicknessMm    = 2.0;
    double      radiusMm       = 120.0;
    double      lengthMm       = 100.0;
    double      widthMm        = 25.0;
    std::string beamBoundary   = "cantilever";
    std::string frequencyMode  = "midi";
    std::string exciter = "wood_mallet";
    double      diameterMm     = 0.8;
    int         numStrings     = 3;
    float       detuningCents  = 5.0f;
    double      tensionN       = 0.0;
    double      dampingOverride = -1.0;  // <0 = use material default
    int         fmPreset       = 0;
    float       fmRatio        = -1.0f;   // <0 = use FMParams default
    float       fmIndex        = -1.0f;
    float       fmBrightness   = -1.0f;
    float       fmFeedback     = -1.0f;
    float       fmAttackMs     = -1.0f;
    float       fmReleaseMs    = -1.0f;

    bool        plateFreeEdge  = true;   // water_gong: hung plate, edges free (physical default)

    float       customRatios[8] = { -1, -1, -1, -1, -1, -1, -1, -1 };
    float       customAmps[8]   = { -1, -1, -1, -1, -1, -1, -1, -1 };

    bool        hasGlide       = false;
    std::string glideFromNote;
    double      glideDurationMs = 0.0;
    std::string glideCurve     = "linear";
};

struct ScoreExport
{
    std::string filename;
    std::string exportFilename;
    std::string format = "wav";
    int    bitDepth       = 24;
    bool   normalize      = true;
    double tailSilenceMs  = 500.0;
    double startPosition  = 0.0;
    double endPosition    = 1.0;
};

struct ScoreLayer
{
    std::string source;
    double regionStart = 0.0;
    double regionEnd   = 1.0;
    double gain        = 1.0;
};

struct Score
{
    ScoreMeta   meta;
    ScoreGlobal global;
    std::vector<ScoreEvent> events;
    ScoreExport exportSettings;
    std::vector<ScoreLayer> layers;
    int crossfadeMs = 0;

    bool hasLayers() const { return ! layers.empty(); }
    std::vector<std::string> warnings;
    std::vector<std::string> errors;
};

inline bool tryNoteNameToMidi (const std::string& name, int& midi)
{
    if (name.empty()) return false;

    static const std::regex numericPattern (R"(^[0-9]{1,3}$)");
    static const std::regex notePattern (R"(^([A-Ga-g])([#b]?)(-?[0-9]+)$)");
    std::smatch match;

    if (std::regex_match (name, numericPattern))
    {
        try
        {
            const int value = std::stoi (name);
            if (value < 0 || value > 127) return false;
            midi = value;
            return true;
        }
        catch (...) { return false; }
    }

    if (! std::regex_match (name, match, notePattern))
        return false;

    char letter = match[1].str()[0];
    if (letter >= 'a' && letter <= 'g')
        letter = static_cast<char> (letter - ('a' - 'A'));

    static const int noteMap[] = { 9, 11, 0, 2, 4, 5, 7 }; // A..G
    int semitone = noteMap[letter - 'A'];
    const auto accidental = match[2].str();
    if (accidental == "#") ++semitone;
    else if (accidental == "b") --semitone;

    int octave = 0;
    try { octave = std::stoi (match[3].str()); }
    catch (...) { return false; }

    const int value = (octave + 1) * 12 + semitone;
    if (value < 0 || value > 127) return false;
    midi = value;
    return true;
}

inline bool isValidNoteName (const std::string& name)
{
    int midi = -1;
    return tryNoteNameToMidi (name, midi);
}

inline int noteNameToMidi (const std::string& name)
{
    int midi = -1;
    return tryNoteNameToMidi (name, midi) ? midi : -1;
}

class ScoreParser
{
public:
    static bool parse (const juce::File& file, Score& score)
    {
        score = Score();

        auto text = file.loadFileAsString();
        if (text.isEmpty())
            return fail (score, "Score file is empty or unreadable");

        juce::var json;
        const auto parseResult = juce::JSON::parse (text, json);
        if (parseResult.failed())
            return fail (score, "Invalid JSON: " + parseResult.getErrorMessage().toStdString());
        if (! json.isObject())
            return fail (score, "Top-level JSON value must be an object");

        auto* obj = json.getDynamicObject();
        if (obj == nullptr)
            return fail (score, "Top-level JSON object is unavailable");

        if (! validateDocument (*obj, score))
            return false;

        const auto* validatedEvents = obj->getProperty ("events").getArray();
        const size_t validatedEventCount = validatedEvents != nullptr
            ? static_cast<size_t> (validatedEvents->size()) : 0;

        if (auto* meta = obj->getProperty ("meta").getDynamicObject())
        {
            readString (*meta, "title", score.meta.title, true);
            readString (*meta, "id", score.meta.id, true);
            readString (*meta, "author", score.meta.author, true);
            readString (*meta, "description", score.meta.description, true);
        }

        if (auto* g = obj->getProperty ("global").getDynamicObject())
        {
            readNumber (*g, "bpm", score.global.bpm, 1.0, 999.0);
            readNumber (*g, "master_volume", score.global.masterVolume, 0.0, 1.0);
            if (g->hasProperty ("random_seed"))
                score.global.randomSeed = static_cast<uint64_t> ((double) g->getProperty ("random_seed"));

            int parsedSR = score.global.sampleRate;
            if (readInt (*g, "sample_rate", parsedSR, 1, 192000))
            {
                if (! isSupportedSampleRate (parsedSR))
                    return false;
                score.global.sampleRate = parsedSR;
            }

            if (auto* fx = g->getProperty ("effects").getDynamicObject())
            {
                if (auto* rev = fx->getProperty ("reverb").getDynamicObject())
                {
                    readNumber (*rev, "decay", score.global.effects.reverbDecay, 0.0, 30.0);
                    readNumber (*rev, "wet", score.global.effects.reverbWet, 0.0, 1.0);
                }
                if (auto* del = fx->getProperty ("delay").getDynamicObject())
                {
                    readNumber (*del, "time_ms", score.global.effects.delayTimeMs, 0.0, 5000.0);
                    readNumber (*del, "feedback", score.global.effects.delayFeedback, 0.0, 0.95);
                    readNumber (*del, "wet", score.global.effects.delayWet, 0.0, 1.0);
                }
                if (auto* wall = fx->getProperty ("wall").getDynamicObject())
                {
                    readNumber (*wall, "distance_m", score.global.effects.wallDistanceM, 0.0, 100.0);
                    readString (*wall, "material", score.global.effects.wallMaterial, true);
                }
                if (auto* dist = fx->getProperty ("distortion").getDynamicObject())
                {
                    readString (*dist, "type", score.global.effects.distortionType);
                    readNumber (*dist, "drive", score.global.effects.distortionDrive, 0.0, 1.0);
                    readNumber (*dist, "instability", score.global.effects.distortionInstability, 0.0, 1.0);
                    readNumber (*dist, "wet", score.global.effects.distortionWet, 0.0, 1.0);
                }
            }
        }

        if (auto* evts = obj->getProperty ("events").getArray())
        {
            int srcIndex = 0;
            for (const auto& ev : *evts)
            {
                if (auto* e = ev.getDynamicObject())
                {
                    ScoreEvent se;
                    double velocity = se.velocity;

                    // ── velocity law (ROADMAP_PHYSICS.md M6-6a, comment only --
                    //    no logic change here; this documents what happens
                    //    downstream once `velocity` leaves this parser) ────────
                    //    `velocity` in [0,1] is read here as a plain number and
                    //    carried unchanged into ScoreEvent::velocity. It is used
                    //    as the LINEAR excitation-force scale for the modal
                    //    engines: ModalResonator::excite() sets
                    //        currentAmp = baseAmp * velocity
                    //    (src/dsp/ModalResonator.h) -- no curve, no lookup
                    //    table. Amplitude is proportional to velocity, so
                    //    doubling velocity doubles the waveform amplitude and
                    //    therefore raises the rendered level by
                    //        20 * log10(2) = +6.0206 dB.
                    //    This is not just a design intent -- it is machine-
                    //    verified: tools/physics_verify.py's velocity judgment
                    //    (ROADMAP_PHYSICS.md Sec.6 "velocity ×2 電平", M1-1d)
                    //    renders the same note at velocity and 2*velocity and
                    //    checks the measured level difference against
                    //    +6.0 +/- 1.0 dB for every modal engine (cimbalom /
                    //    tongue_drum / water_gong / water_gong_free / piano);
                    //    FM is exempted there as a non-modal, non-physical
                    //    engine (see ROADMAP_PHYSICS.md Sec.0 domain table).
                    //    See docs/AI_PHYSICAL_COMPOSITION_GUIDE.zh-TW.md Sec.4.6
                    //    for the deaf-reader-facing "velocity -> dB" table.
                    if (! readNumber (*e, "time", se.time, 0.0, 24.0 * 60.0 * 60.0)
                        || ! readNumber (*e, "duration", se.duration, 0.0, 24.0 * 60.0 * 60.0)
                        || ! readString (*e, "engine", se.engine)
                        || ! readNote (*e, "note", se.note)
                        || ! readNumber (*e, "velocity", velocity, 0.0, 1.0)
                        || ! isKnownEngine (se.engine))
                    {
                        return fail (score, "Event " + std::to_string (srcIndex)
                            + ": required field could not be parsed");
                    }

                    if (! isValidNoteName (se.note))
                    {
                        return fail (score, "Event " + std::to_string (srcIndex)
                            + ": invalid note \"" + se.note + "\"");
                    }

                    se.velocity = static_cast<float> (velocity);

                    if (auto* p = e->getProperty ("params").getDynamicObject())
                    {
                        readString (*p, "material", se.material);
                        readNumber (*p, "strike_position", se.strikePosition, 0.0, 1.0);
                        readNumber (*p, "thickness_mm", se.thicknessMm, 0.1, 1000.0);
                        readNumber (*p, "radius_mm", se.radiusMm, 1.0, 10000.0);
                        readNumber (*p, "length_mm", se.lengthMm, 1.0, 10000.0);
                        readNumber (*p, "width_mm", se.widthMm, 1.0, 10000.0);
                        readString (*p, "beam_boundary", se.beamBoundary);
                        readString (*p, "frequency_mode", se.frequencyMode);
                        readString (*p, "exciter", se.exciter);
                        readNumber (*p, "diameter_mm", se.diameterMm, 0.1, 50.0);
                        {
                            int ns = se.numStrings;
                            if (readInt (*p, "num_strings", ns, 1, 5))
                                se.numStrings = ns;
                            double dc = se.detuningCents;
                            if (readNumber (*p, "detuning_cents", dc, 0.0, 50.0))
                                se.detuningCents = static_cast<float> (dc);
                        }
                        readNumber (*p, "tension_n", se.tensionN, 0.0, 100000.0);
                        if (p->hasProperty ("damping_override"))
                        {
                            auto dv = p->getProperty ("damping_override");
                            double damping = -1.0;
                            if (varToFiniteNumber (dv, damping))
                                se.dampingOverride = std::clamp (damping, 0.0, 10000.0);
                        }

                        int fmPreset = se.fmPreset;
                        if (readInt (*p, "fm_preset", fmPreset, 0, 7))
                            se.fmPreset = fmPreset;

                        double value = 0.0;
                        if (readNumber (*p, "fm_ratio", value, 0.25, 16.0))
                            se.fmRatio = static_cast<float> (value);
                        if (readNumber (*p, "fm_index", value, 0.0, 25.0))
                            se.fmIndex = static_cast<float> (value);
                        if (readNumber (*p, "fm_brightness", value, 0.0, 1.0))
                            se.fmBrightness = static_cast<float> (value);
                        if (readNumber (*p, "fm_feedback", value, 0.0, 1.0))
                            se.fmFeedback = static_cast<float> (value);
                        if (readNumber (*p, "fm_attack", value, 1.0, 5000.0))
                            se.fmAttackMs = static_cast<float> (value);
                        if (readNumber (*p, "fm_release", value, 10.0, 10000.0))
                            se.fmReleaseMs = static_cast<float> (value);

                        readBool (*p, "plate_free_edge", se.plateFreeEdge);

                        for (int ci = 0; ci < 8; ++ci)
                        {
                            std::string rk = "ratio_" + std::to_string (ci);
                            std::string ak = "amp_" + std::to_string (ci);
                            double rv = -1.0, av = -1.0;
                            if (readNumber (*p, rk.c_str(), rv, 0.1, 100.0))
                                se.customRatios[ci] = static_cast<float> (rv);
                            if (readNumber (*p, ak.c_str(), av, 0.0, 1.0))
                                se.customAmps[ci] = static_cast<float> (av);
                        }
                    }

                    if (auto* gl = e->getProperty ("glide").getDynamicObject())
                    {
                        std::string fromNote;
                        double durationMs = 0.0;
                        if (readNote (*gl, "from_note", fromNote)
                            && readNumber (*gl, "duration_ms", durationMs, 1.0, 5000.0))
                        {
                            se.hasGlide = true;
                            se.glideFromNote = fromNote;
                            se.glideDurationMs = durationMs;
                        }
                        if (gl->hasProperty ("curve"))
                            readString (*gl, "curve", se.glideCurve);
                    }

                    score.events.push_back (se);
                }
                ++srcIndex;
            }
        }

        if (auto* exp = obj->getProperty ("export").getDynamicObject())
        {
            readString (*exp, "filename", score.exportSettings.filename, true);
            readString (*exp, "export_filename", score.exportSettings.exportFilename, true);
            readString (*exp, "format", score.exportSettings.format);
            if (! score.exportSettings.format.empty()
                && score.exportSettings.format != "wav"
                && score.exportSettings.format != "flac")
            {
                return fail (score, "Unsupported export format \""
                    + score.exportSettings.format + "\"");
            }

            int bitDepth = score.exportSettings.bitDepth;
            if (readInt (*exp, "bit_depth", bitDepth, 1, 64)
                && (bitDepth == 16 || bitDepth == 24 || bitDepth == 32))
                score.exportSettings.bitDepth = bitDepth;

            readBool (*exp, "normalize", score.exportSettings.normalize);
            readNumber (*exp, "tail_silence_ms", score.exportSettings.tailSilenceMs, 0.0, 60000.0);
            readNumber (*exp, "start_position", score.exportSettings.startPosition, 0.0, 1.0);
            readNumber (*exp, "end_position", score.exportSettings.endPosition, 0.0, 1.0);

            if (score.exportSettings.startPosition >= score.exportSettings.endPosition)
                return false;

            if (score.exportSettings.format == "flac" && score.exportSettings.bitDepth == 32)
                score.warnings.push_back ("FLAC does not support 32-bit; output will be 24-bit");
        }

        if (auto* layersArr = obj->getProperty ("layers").getArray())
        {
            for (const auto& lv : *layersArr)
            {
                if (auto* l = lv.getDynamicObject())
                {
                    ScoreLayer layer;
                    if (! readString (*l, "source", layer.source))
                        continue;

                    readNumber (*l, "gain", layer.gain, 0.0, 2.0);
                    if (auto* region = l->getProperty ("region").getArray())
                    {
                        if (region->size() >= 2)
                        {
                            double rs = layer.regionStart;
                            double re = layer.regionEnd;
                            if (varToFiniteNumber ((*region)[0], rs)
                                && varToFiniteNumber ((*region)[1], re))
                            {
                                layer.regionStart = std::clamp (rs, 0.0, 1.0);
                                layer.regionEnd   = std::clamp (re, 0.0, 1.0);
                            }
                        }
                    }
                    score.layers.push_back (layer);
                }
            }
        }

        int crossfade = score.crossfadeMs;
        if (readInt (*obj, "crossfade_ms", crossfade, 0, 60000))
            score.crossfadeMs = crossfade;

        if (score.events.size() != validatedEventCount)
            return fail (score, "Internal event-count mismatch: validated "
                + std::to_string (validatedEventCount) + ", parsed "
                + std::to_string (score.events.size()));

        return ! score.events.empty() || score.hasLayers();
    }

private:
    static bool fail (Score& score, const std::string& message)
    {
        score.errors.push_back (message);
        return false;
    }

    static bool validateKeys (juce::DynamicObject& obj,
                              std::initializer_list<const char*> allowed,
                              const std::string& path, Score& score)
    {
        const auto& props = obj.getProperties();
        for (int i = 0; i < props.size(); ++i)
        {
            const auto key = props.getName (i).toString().toStdString();
            bool found = false;
            for (const auto* candidate : allowed)
                if (key == candidate) { found = true; break; }
            if (! found)
                return fail (score, path + ": unknown property \"" + key + "\"");
        }
        return true;
    }

    static bool validateString (juce::DynamicObject& obj, const char* name,
                                const std::string& path, Score& score,
                                bool required = false, bool allowEmpty = false)
    {
        if (! obj.hasProperty (name))
            return required ? fail (score, path + "." + name + " is required") : true;
        const auto value = obj.getProperty (name);
        if (! value.isString())
            return fail (score, path + "." + name + " must be a string");
        if (! allowEmpty && value.toString().trim().isEmpty())
            return fail (score, path + "." + name + " must not be empty");
        return true;
    }

    static bool validateNumber (juce::DynamicObject& obj, const char* name,
                                double minValue, double maxValue,
                                const std::string& path, Score& score,
                                bool required = false, bool integer = false)
    {
        if (! obj.hasProperty (name))
            return required ? fail (score, path + "." + name + " is required") : true;
        double value = 0.0;
        if (! varToFiniteNumber (obj.getProperty (name), value))
            return fail (score, path + "." + name + " must be a finite number");
        if (integer && std::floor (value) != value)
            return fail (score, path + "." + name + " must be an integer");
        if (value < minValue || value > maxValue)
            return fail (score, path + "." + name + " is outside ["
                + std::to_string (minValue) + ", " + std::to_string (maxValue) + "]");
        return true;
    }

    static bool validateBool (juce::DynamicObject& obj, const char* name,
                              const std::string& path, Score& score)
    {
        if (! obj.hasProperty (name)) return true;
        if (! obj.getProperty (name).isBool())
            return fail (score, path + "." + name + " must be boolean");
        return true;
    }

    static bool validateEnum (juce::DynamicObject& obj, const char* name,
                              std::initializer_list<const char*> values,
                              const std::string& path, Score& score,
                              bool required = false)
    {
        if (! validateString (obj, name, path, score, required)) return false;
        if (! obj.hasProperty (name)) return true;
        const auto value = obj.getProperty (name).toString().toStdString();
        for (const auto* candidate : values)
            if (value == candidate) return true;
        return fail (score, path + "." + name + " has unsupported value \""
            + value + "\"");
    }

    static bool validateStringArray (juce::DynamicObject& obj, const char* name,
                                     const std::string& path, Score& score)
    {
        if (! obj.hasProperty (name)) return true;
        auto* values = obj.getProperty (name).getArray();
        if (values == nullptr)
            return fail (score, path + "." + name + " must be an array");
        for (int i = 0; i < values->size(); ++i)
            if (! (*values)[i].isString())
                return fail (score, path + "." + name + "[" + std::to_string (i)
                    + "] must be a string");
        return true;
    }

    static bool validateNoteValue (const juce::var& value,
                                   const std::string& path, Score& score)
    {
        int midi = -1;
        if (value.isString())
        {
            if (! tryNoteNameToMidi (value.toString().toStdString(), midi))
                return fail (score, path + " must exactly match MIDI 0..127 or note form C#4/Bb3");
            return true;
        }
        double numeric = 0.0;
        if (! varToFiniteNumber (value, numeric) || std::floor (numeric) != numeric
            || numeric < 0.0 || numeric > 127.0)
            return fail (score, path + " must be an integer MIDI value 0..127 or a note string");
        return true;
    }

    static bool validateMeta (juce::DynamicObject& meta, Score& score)
    {
        if (! validateKeys (meta, { "title", "id", "author", "composer", "work",
            "catalogue", "opus_number", "movement_number", "movement_name", "key",
            "description", "created", "tags", "mood", "use_case", "category",
            "worldview", "variation_of", "primary_type", "sound_type", "family_id",
            "character", "loop_bpm", "loop_bars" }, "meta", score)) return false;
        if (! validateString (meta, "title", "meta", score, true)
            || ! validateString (meta, "id", "meta", score, true)) return false;
        const auto id = meta.getProperty ("id").toString().toStdString();
        if (! std::regex_match (id, std::regex (R"(^[a-z0-9_]+$)")))
            return fail (score, "meta.id must use snake_case [a-z0-9_]");
        for (const auto* name : { "author", "composer", "work", "catalogue", "opus_number",
                                  "movement_name", "key", "description", "created", "use_case",
                                  "category", "worldview", "family_id" })
            if (! validateString (meta, name, "meta", score, false, true)) return false;
        if (meta.hasProperty ("variation_of") && ! meta.getProperty ("variation_of").isVoid()
            && ! validateString (meta, "variation_of", "meta", score, false, true)) return false;
        if (meta.hasProperty ("family_id"))
        {
            const auto family = meta.getProperty ("family_id").toString().toStdString();
            if (! std::regex_match (family, std::regex (R"(^[a-z0-9_]+$)")))
                return fail (score, "meta.family_id must use snake_case [a-z0-9_]");
        }
        if (auto* characters = meta.getProperty ("character").getArray())
        {
            for (int i = 0; i < characters->size(); ++i)
            {
                const auto value = (*characters)[i].toString().toStdString();
                bool known = false;
                for (const auto* candidate : { "punch", "soft", "dark", "bright",
                                               "pulse", "stomp", "airy", "metallic",
                                               "glitch" })
                    if (value == candidate) { known = true; break; }
                if (! known)
                    return fail (score, "meta.character[" + std::to_string (i)
                        + "] has unsupported value \"" + value + "\"");
            }
        }
        return validateNumber (meta, "movement_number", 1, 100000, "meta", score, false, true)
            && validateNumber (meta, "loop_bpm", 1, 999, "meta", score)
            && validateNumber (meta, "loop_bars", 1, 100000, "meta", score, false, true)
            && validateStringArray (meta, "tags", "meta", score)
            && validateStringArray (meta, "character", "meta", score)
            && validateEnum (meta, "mood", { "sacred", "mystical", "tense", "ominous",
                "playful", "calm", "epic", "melancholic", "neutral", "aggressive",
                "oppressive" }, "meta", score)
            && validateEnum (meta, "primary_type", { "ambience", "creature", "magic", "ui",
                "whoosh", "impact", "foley", "mechanical" }, "meta", score)
            && validateEnum (meta, "sound_type", { "oneshot", "loop", "variant" }, "meta", score);
    }

    static bool validateEffects (juce::DynamicObject& effects, Score& score)
    {
        if (! validateKeys (effects, { "reverb", "delay", "wall", "distortion" },
                            "global.effects", score)) return false;
        auto validateObject = [&] (const char* name, auto fn)
        {
            if (! effects.hasProperty (name)) return true;
            auto* object = effects.getProperty (name).getDynamicObject();
            if (object == nullptr)
                return fail (score, std::string ("global.effects.") + name + " must be an object");
            return fn (*object);
        };
        return validateObject ("reverb", [&] (juce::DynamicObject& o) {
                return validateKeys (o, { "decay", "wet" }, "global.effects.reverb", score)
                    && validateNumber (o, "decay", 0, 30, "global.effects.reverb", score)
                    && validateNumber (o, "wet", 0, 1, "global.effects.reverb", score); })
            && validateObject ("delay", [&] (juce::DynamicObject& o) {
                return validateKeys (o, { "time_ms", "feedback", "wet" }, "global.effects.delay", score)
                    && validateNumber (o, "time_ms", 0, 5000, "global.effects.delay", score)
                    && validateNumber (o, "feedback", 0, 0.95, "global.effects.delay", score)
                    && validateNumber (o, "wet", 0, 1, "global.effects.delay", score); })
            && validateObject ("wall", [&] (juce::DynamicObject& o) {
                return validateKeys (o, { "distance_m", "material" }, "global.effects.wall", score)
                    && validateNumber (o, "distance_m", 0, 100, "global.effects.wall", score)
                    && validateEnum (o, "material", { "stone", "concrete", "glass", "metal",
                        "wood", "fabric", "curtain" }, "global.effects.wall", score); })
            && validateObject ("distortion", [&] (juce::DynamicObject& o) {
                return validateKeys (o, { "type", "drive", "instability", "wet" },
                                    "global.effects.distortion", score)
                    && validateEnum (o, "type", { "overdrive", "bitcrush", "wavefold" },
                                     "global.effects.distortion", score)
                    && validateNumber (o, "drive", 0, 1, "global.effects.distortion", score)
                    && validateNumber (o, "instability", 0, 1, "global.effects.distortion", score)
                    && validateNumber (o, "wet", 0, 1, "global.effects.distortion", score); });
    }

    static bool validateGlobal (juce::DynamicObject& global, Score& score)
    {
        if (! validateKeys (global, { "bpm", "sample_rate", "master_volume", "random_seed", "effects" },
                            "global", score)
            || ! validateNumber (global, "bpm", 1, 999, "global", score, true)
            || ! validateNumber (global, "sample_rate", 44100, 96000, "global", score, true, true)
            || ! validateNumber (global, "master_volume", 0, 1, "global", score, true)
            || ! validateNumber (global, "random_seed", 0, 9007199254740991.0,
                                 "global", score, false, true)) return false;
        const int sr = static_cast<int> ((double) global.getProperty ("sample_rate"));
        if (! isSupportedSampleRate (sr))
            return fail (score, "global.sample_rate must be one of 44100, 48000, 88200, 96000");
        if (! global.hasProperty ("effects")) return true;
        auto* effects = global.getProperty ("effects").getDynamicObject();
        return effects != nullptr ? validateEffects (*effects, score)
                                  : fail (score, "global.effects must be an object");
    }

    static bool isKnownExciterName (const std::string& value)
    {
        static const std::initializer_list<const char*> values = { "cotton", "cotton_mallet",
            "felt", "felt_mallet", "wood", "wood_mallet", "metal", "metal_mallet",
            "metal_hammer", "metal_tip", "hard_plastic", "hard_strike", "finger",
            "finger_tap", "bow", "bow_slow", "brush", "rubber_mallet", "metal_scrape",
            "pluck", "medium", "sharp" };
        for (const auto* candidate : values) if (value == candidate) return true;
        return false;
    }

    static bool parameterIsRelevant (const std::string& engine, const std::string& key)
    {
        if (key == "material" || key == "strike_position" || key == "exciter"
            || key == "damping_override") return engine != "fm";
        if (key.rfind ("fm_", 0) == 0) return engine == "fm";
        if (key.rfind ("ratio_", 0) == 0 || key.rfind ("amp_", 0) == 0)
            return engine == "custom";
        if (key == "diameter_mm" || key == "num_strings" || key == "detuning_cents"
            || key == "tension_n")
            return engine == "string" || engine == "cimbalom" || engine == "piano";
        if (key == "length_mm" || key == "width_mm" || key == "beam_boundary")
            return engine == "beam" || engine == "tongue_drum";
        if (key == "frequency_mode")
            return engine == "string" || engine == "cimbalom" || engine == "piano"
                || engine == "beam" || engine == "tongue_drum"
                || engine == "plate" || engine == "water_gong";
        if (key == "radius_mm" || key == "plate_free_edge")
            return engine == "plate" || engine == "water_gong";
        if (key == "thickness_mm")
            return engine == "beam" || engine == "tongue_drum"
                || engine == "plate" || engine == "water_gong";
        return false;
    }

    static bool validateParams (juce::DynamicObject& params, const std::string& engine,
                                const std::string& path, Score& score)
    {
        if (! validateKeys (params, { "material", "strike_position", "thickness_mm",
            "radius_mm", "length_mm", "width_mm", "beam_boundary", "frequency_mode", "exciter", "diameter_mm",
            "num_strings", "detuning_cents", "tension_n", "damping_override",
            "fm_preset", "fm_ratio", "fm_index", "fm_brightness", "fm_feedback",
            "fm_attack", "fm_release", "plate_free_edge",
            "ratio_0", "ratio_1", "ratio_2", "ratio_3", "ratio_4", "ratio_5",
            "ratio_6", "ratio_7", "amp_0", "amp_1", "amp_2", "amp_3", "amp_4",
            "amp_5", "amp_6", "amp_7" }, path, score)) return false;
        const auto& properties = params.getProperties();
        for (int i = 0; i < properties.size(); ++i)
        {
            const auto key = properties.getName (i).toString().toStdString();
            if (! parameterIsRelevant (engine, key))
                return fail (score, path + "." + key + " is not used by engine \""
                    + engine + "\"; no-op parameters are rejected");
        }
        if (! validateString (params, "material", path, score)
            || ! validateString (params, "exciter", path, score)
            || ! validateNumber (params, "strike_position", 0, 1, path, score)
            || ! validateNumber (params, "thickness_mm", 0.1, 1000, path, score)
            || ! validateNumber (params, "radius_mm", 1, 10000, path, score)
            || ! validateNumber (params, "length_mm", 1, 10000, path, score)
            || ! validateNumber (params, "width_mm", 1, 10000, path, score)
            || ! validateNumber (params, "diameter_mm", 0.1, 50, path, score)
            || ! validateNumber (params, "num_strings", 1, 5, path, score, false, true)
            || ! validateNumber (params, "detuning_cents", 0, 50, path, score)
            || ! validateNumber (params, "tension_n", 1, 100000, path, score)
            || ! validateNumber (params, "fm_preset", 0, 7, path, score, false, true)
            || ! validateNumber (params, "fm_ratio", 0.25, 16, path, score)
            || ! validateNumber (params, "fm_index", 0, 25, path, score)
            || ! validateNumber (params, "fm_brightness", 0, 1, path, score)
            || ! validateNumber (params, "fm_feedback", 0, 1, path, score)
            || ! validateNumber (params, "fm_attack", 1, 5000, path, score)
            || ! validateNumber (params, "fm_release", 10, 10000, path, score)
            || ! validateBool (params, "plate_free_edge", path, score)) return false;
        if (params.hasProperty ("exciter")
            && ! isKnownExciterName (params.getProperty ("exciter").toString().toStdString()))
            return fail (score, path + ".exciter is not a supported exciter");
        if (! validateEnum (params, "beam_boundary", { "cantilever", "free_free" }, path, score))
            return false;
        if (! validateEnum (params, "frequency_mode", { "midi", "geometry" }, path, score))
            return false;
        if (params.hasProperty ("damping_override")
            && ! params.getProperty ("damping_override").isVoid()
            && ! validateNumber (params, "damping_override", 0, 10000, path, score)) return false;
        for (int i = 0; i < 8; ++i)
        {
            const auto ratio = "ratio_" + std::to_string (i);
            const auto amp = "amp_" + std::to_string (i);
            if (! validateNumber (params, ratio.c_str(), 0.1, 100, path, score)
                || ! validateNumber (params, amp.c_str(), 0, 1, path, score)) return false;
        }
        return true;
    }

    static bool validatePerformance (juce::DynamicObject& perf, const std::string& path,
                                     Score& score)
    {
        if (! validateKeys (perf, { "track", "role", "midi_note", "frequency_hz",
            "source_duration_sec", "intended_release_time", "articulation",
            "articulation_gap_ms", "phrase_end", "breath_after_ms" }, path, score)) return false;
        for (const auto* name : { "track", "role", "articulation" })
            if (! validateString (perf, name, path, score)) return false;
        return validateNumber (perf, "midi_note", 0, 127, path, score, false, true)
            && validateNumber (perf, "frequency_hz", std::numeric_limits<double>::min(),
                               std::numeric_limits<double>::max(), path, score)
            && validateNumber (perf, "source_duration_sec", 0, 86400, path, score)
            && validateNumber (perf, "intended_release_time", 0, 86400, path, score)
            && validateNumber (perf, "articulation_gap_ms", 0, 86400000, path, score)
            && validateNumber (perf, "breath_after_ms", 0, 86400000, path, score)
            && validateBool (perf, "phrase_end", path, score);
    }

    static bool validateEvent (juce::DynamicObject& event, int index, Score& score)
    {
        const auto path = "events[" + std::to_string (index) + "]";
        if (! validateKeys (event, { "time", "duration", "engine", "note", "velocity",
                                    "params", "glide", "performance", "comment" }, path, score)
            || ! validateNumber (event, "time", 0, 86400, path, score, true)
            || ! validateNumber (event, "duration", 0, 86400, path, score, true)
            || ! validateEnum (event, "engine", { "string", "cimbalom", "beam",
                "tongue_drum", "plate", "water_gong", "custom", "fm", "piano" },
                path, score, true)
            || ! validateNumber (event, "velocity", 0, 1, path, score, true)
            || ! validateString (event, "comment", path, score, false, true)) return false;
        if (! event.hasProperty ("note")) return fail (score, path + ".note is required");
        if (! validateNoteValue (event.getProperty ("note"), path + ".note", score)) return false;
        const auto engine = event.getProperty ("engine").toString().toStdString();
        if (event.hasProperty ("params"))
        {
            auto* params = event.getProperty ("params").getDynamicObject();
            if (params == nullptr) return fail (score, path + ".params must be an object");
            if (! validateParams (*params, engine, path + ".params", score)) return false;
        }
        if (event.hasProperty ("glide"))
        {
            auto* glide = event.getProperty ("glide").getDynamicObject();
            if (glide == nullptr) return fail (score, path + ".glide must be an object");
            const auto glidePath = path + ".glide";
            if (! validateKeys (*glide, { "from_note", "duration_ms", "curve" }, glidePath, score)
                || ! glide->hasProperty ("from_note")
                || ! validateNoteValue (glide->getProperty ("from_note"), glidePath + ".from_note", score)
                || ! validateNumber (*glide, "duration_ms", 1, 5000, glidePath, score, true)
                || ! validateEnum (*glide, "curve", { "linear", "exponential" }, glidePath, score))
                return false;
        }
        if (event.hasProperty ("performance"))
        {
            auto* perf = event.getProperty ("performance").getDynamicObject();
            if (perf == nullptr) return fail (score, path + ".performance must be an object");
            if (! validatePerformance (*perf, path + ".performance", score)) return false;
        }
        return true;
    }

    static bool validateExport (juce::DynamicObject& settings, Score& score)
    {
        if (! validateKeys (settings, { "filename", "export_filename", "format", "bit_depth",
            "normalize", "tail_silence_ms", "start_position", "end_position" }, "export", score)
            || ! validateString (settings, "filename", "export", score, true)
            || ! validateString (settings, "export_filename", "export", score)
            || ! validateEnum (settings, "format", { "wav", "flac" }, "export", score)
            || ! validateNumber (settings, "bit_depth", 16, 32, "export", score, false, true)
            || ! validateBool (settings, "normalize", "export", score)
            || ! validateNumber (settings, "tail_silence_ms", 0, 60000, "export", score, false, true)
            || ! validateNumber (settings, "start_position", 0, 1, "export", score)
            || ! validateNumber (settings, "end_position", 0, 1, "export", score)) return false;
        for (const auto* name : { "filename", "export_filename" })
        {
            if (! settings.hasProperty (name)) continue;
            const auto value = settings.getProperty (name).toString();
            if (value.containsChar ('/') || value.containsChar ('\\')
                || value.contains ("..") || juce::File::isAbsolutePath (value))
                return fail (score, std::string ("export.") + name
                    + " must be a safe filename stem, not a path");
        }
        if (settings.hasProperty ("bit_depth"))
        {
            const int bits = static_cast<int> ((double) settings.getProperty ("bit_depth"));
            if (bits != 16 && bits != 24 && bits != 32)
                return fail (score, "export.bit_depth must be 16, 24, or 32");
        }
        const double start = settings.hasProperty ("start_position")
            ? (double) settings.getProperty ("start_position") : 0.0;
        const double end = settings.hasProperty ("end_position")
            ? (double) settings.getProperty ("end_position") : 1.0;
        return start < end ? true : fail (score, "export.start_position must be less than end_position");
    }

    static bool validateSimpleObjectArray (juce::DynamicObject& root, const char* name,
                                           std::initializer_list<const char*> keys,
                                           std::initializer_list<const char*> required,
                                           Score& score)
    {
        if (! root.hasProperty (name)) return true;
        auto* array = root.getProperty (name).getArray();
        if (array == nullptr) return fail (score, std::string (name) + " must be an array");
        for (int i = 0; i < array->size(); ++i)
        {
            auto* object = (*array)[i].getDynamicObject();
            const auto path = std::string (name) + "[" + std::to_string (i) + "]";
            if (object == nullptr || ! validateKeys (*object, keys, path, score))
                return object != nullptr ? false : fail (score, path + " must be an object");
            for (const auto* key : required)
                if (! object->hasProperty (key)) return fail (score, path + "." + key + " is required");
            const auto& props = object->getProperties();
            for (int p = 0; p < props.size(); ++p)
            {
                const auto key = props.getName (p).toString().toStdString();
                const auto value = props.getValueAt (p);
                const bool expectsString = key == "track" || key == "role" || key == "kind";
                if (expectsString ? ! value.isString() : ! (value.isInt() || value.isInt64() || value.isDouble()))
                    return fail (score, path + "." + key + " has wrong type");
            }
        }
        return true;
    }

    static bool validateAnnotations (juce::DynamicObject& root, Score& score)
    {
        if (root.hasProperty ("composition_thesis")
            && ! validateString (root, "composition_thesis", "score", score, false, true)) return false;
        if (root.hasProperty ("source"))
        {
            auto* source = root.getProperty ("source").getDynamicObject();
            if (source == nullptr || ! validateKeys (*source, { "score_source", "source_url",
                "source_midi_file", "source_format", "license", "license_url", "attribution",
                "editorial_note" }, "source", score))
                return source != nullptr ? false : fail (score, "source must be an object");
            const auto& props = source->getProperties();
            for (int i = 0; i < props.size(); ++i)
                if (! props.getValueAt (i).isString())
                    return fail (score, "source fields must be strings");
        }
        if (! validateSimpleObjectArray (root, "tempo_map",
                { "time", "tick", "quarter_bpm", "microseconds_per_quarter" },
                { "time", "quarter_bpm" }, score)
            || ! validateSimpleObjectArray (root, "time_signatures",
                { "time", "tick", "numerator", "denominator" },
                { "time", "numerator", "denominator" }, score)
            || ! validateSimpleObjectArray (root, "rests",
                { "track", "role", "time", "duration", "approx_quarter_beats", "kind" },
                { "track", "time", "duration", "kind" }, score)
            || ! validateSimpleObjectArray (root, "phrases",
                { "track", "role", "number", "start", "end", "breath_after_ms" },
                { "track", "number", "start", "end" }, score)) return false;
        if (root.hasProperty ("timing_policy"))
        {
            auto* policy = root.getProperty ("timing_policy").getDynamicObject();
            if (policy == nullptr || ! validateKeys (*policy, { "time_unit", "renderer_note_off_ratio",
                "duration_compensation", "silence_representation", "source_timing",
                "articulation_policy" }, "timing_policy", score))
                return policy != nullptr ? false : fail (score, "timing_policy must be an object");
            const auto& props = policy->getProperties();
            for (int i = 0; i < props.size(); ++i)
            {
                const auto key = props.getName (i).toString();
                const auto value = props.getValueAt (i);
                if (key == "renderer_note_off_ratio")
                {
                    double n = 0.0;
                    if (! varToFiniteNumber (value, n) || n < 0 || n > 1)
                        return fail (score, "timing_policy.renderer_note_off_ratio must be in [0,1]");
                }
                else if (! value.isString()) return fail (score, "timing_policy text fields must be strings");
            }
        }
        if (root.hasProperty ("track_profiles"))
        {
            auto* profiles = root.getProperty ("track_profiles").getDynamicObject();
            if (profiles == nullptr) return fail (score, "track_profiles must be an object");
            const auto& properties = profiles->getProperties();
            for (int i = 0; i < properties.size(); ++i)
            {
                auto* profile = properties.getValueAt (i).getDynamicObject();
                const auto path = "track_profiles." + properties.getName (i).toString().toStdString();
                if (profile == nullptr || ! validateKeys (*profile, { "role", "label", "engine",
                    "material", "diameter_mm", "strike_position", "exciter", "damping_override",
                    "base_velocity" }, path, score))
                    return profile != nullptr ? false : fail (score, path + " must be an object");
                for (const auto* field : { "role", "label", "engine", "material", "exciter" })
                    if (! validateString (*profile, field, path, score)) return false;
                if (! validateNumber (*profile, "diameter_mm", 0.1, 50, path, score)
                    || ! validateNumber (*profile, "strike_position", 0, 1, path, score)
                    || ! validateNumber (*profile, "damping_override", 0, 10000, path, score)
                    || ! validateNumber (*profile, "base_velocity", 0, 1, path, score)) return false;
            }
        }
        return true;
    }

    static bool validateDocument (juce::DynamicObject& root, Score& score)
    {
        if (! validateKeys (root, { "$schema", "meta", "global", "events", "export",
            "layers", "crossfade_ms", "source", "tempo_map", "time_signatures",
            "track_profiles", "timing_policy", "rests", "phrases", "composition_thesis" },
            "score", score)
            || ! validateString (root, "$schema", "score", score, true)) return false;
        if (root.getProperty ("$schema").toString() != "TsukiSynth Score v1")
            return fail (score, "Unsupported score version; expected $schema=\"TsukiSynth Score v1\"");
        auto getRequiredObject = [&] (const char* name) -> juce::DynamicObject*
        {
            if (! root.hasProperty (name)) { fail (score, std::string (name) + " is required"); return nullptr; }
            auto* value = root.getProperty (name).getDynamicObject();
            if (value == nullptr) fail (score, std::string (name) + " must be an object");
            return value;
        };
        auto* meta = getRequiredObject ("meta"); if (meta == nullptr || ! validateMeta (*meta, score)) return false;
        auto* global = getRequiredObject ("global"); if (global == nullptr || ! validateGlobal (*global, score)) return false;
        auto* exportSettings = getRequiredObject ("export");
        if (exportSettings == nullptr || ! validateExport (*exportSettings, score)) return false;

        const bool hasEvents = root.hasProperty ("events");
        const bool hasLayers = root.hasProperty ("layers");
        if (hasEvents == hasLayers)
            return fail (score, "Exactly one of events or layers is required");
        if (hasEvents)
        {
            auto* events = root.getProperty ("events").getArray();
            if (events == nullptr || events->isEmpty())
                return fail (score, "events must be a non-empty array");
            double previousTime = -1.0;
            for (int i = 0; i < events->size(); ++i)
            {
                auto* event = (*events)[i].getDynamicObject();
                if (event == nullptr) return fail (score, "events[" + std::to_string (i) + "] must be an object");
                if (! validateEvent (*event, i, score)) return false;
                const double time = (double) event->getProperty ("time");
                if (time < previousTime) return fail (score, "events must be sorted by ascending time");
                previousTime = time;
            }
        }
        else
        {
            auto* layers = root.getProperty ("layers").getArray();
            if (layers == nullptr || layers->isEmpty()) return fail (score, "layers must be a non-empty array");
            for (int i = 0; i < layers->size(); ++i)
            {
                auto* layer = (*layers)[i].getDynamicObject();
                const auto path = "layers[" + std::to_string (i) + "]";
                if (layer == nullptr || ! validateKeys (*layer, { "source", "region", "gain" }, path, score))
                    return layer != nullptr ? false : fail (score, path + " must be an object");
                if (! validateString (*layer, "source", path, score, true)
                    || ! validateNumber (*layer, "gain", 0, 2, path, score)) return false;
                if (layer->hasProperty ("region"))
                {
                    auto* region = layer->getProperty ("region").getArray();
                    if (region == nullptr || region->size() != 2)
                        return fail (score, path + ".region must contain exactly two numbers");
                    double begin = 0.0, end = 0.0;
                    if (! varToFiniteNumber ((*region)[0], begin) || ! varToFiniteNumber ((*region)[1], end)
                        || begin < 0 || end > 1 || begin >= end)
                        return fail (score, path + ".region must satisfy 0 <= start < end <= 1");
                }
            }
        }
        return validateNumber (root, "crossfade_ms", 0, 60000, "score", score, false, true)
            && validateAnnotations (root, score);
    }

    static bool varToFiniteNumber (const juce::var& v, double& out)
    {
        if (v.isVoid() || v.isUndefined()
            || (! v.isInt() && ! v.isInt64() && ! v.isDouble()))
            return false;

        double value = (double) v;
        if (! std::isfinite (value))
            return false;

        out = value;
        return true;
    }

    static bool readNumber (juce::DynamicObject& obj, const char* name,
                            double& target, double minValue, double maxValue)
    {
        if (! obj.hasProperty (name))
            return false;

        double value = target;
        if (! varToFiniteNumber (obj.getProperty (name), value))
            return false;

        target = std::clamp (value, minValue, maxValue);
        return true;
    }

    static bool readInt (juce::DynamicObject& obj, const char* name,
                         int& target, int minValue, int maxValue)
    {
        double value = (double) target;
        if (! readNumber (obj, name, value, (double) minValue, (double) maxValue))
            return false;

        target = (int) std::round (value);
        return true;
    }

    static bool readBool (juce::DynamicObject& obj, const char* name, bool& target)
    {
        if (! obj.hasProperty (name))
            return false;

        auto value = obj.getProperty (name);
        if (! value.isBool())
            return false;

        target = (bool) value;
        return true;
    }

    static bool readNote (juce::DynamicObject& obj, const char* name,
                          std::string& target)
    {
        if (! obj.hasProperty (name)) return false;
        const auto value = obj.getProperty (name);
        int midi = -1;
        if (value.isString())
        {
            const auto text = value.toString().toStdString();
            if (! tryNoteNameToMidi (text, midi)) return false;
            target = text;
            return true;
        }
        double numeric = 0.0;
        if (! varToFiniteNumber (value, numeric) || std::floor (numeric) != numeric
            || numeric < 0 || numeric > 127) return false;
        target = std::to_string (static_cast<int> (numeric));
        return true;
    }

    static bool readString (juce::DynamicObject& obj, const char* name,
                            std::string& target, bool allowEmpty = false)
    {
        if (! obj.hasProperty (name))
            return false;

        auto text = obj.getProperty (name).toString().trim();
        if (! allowEmpty && text.isEmpty())
            return false;

        target = text.toStdString();
        return true;
    }

    static bool isKnownEngine (const std::string& engine)
    {
        return engine == "string" || engine == "cimbalom"
            || engine == "beam" || engine == "tongue_drum"
            || engine == "plate" || engine == "water_gong"
            || engine == "custom"
            || engine == "fm" || engine == "piano";
    }

    static bool isSupportedSampleRate (int sr)
    {
        return sr == 44100 || sr == 48000 || sr == 88200 || sr == 96000;
    }
};
