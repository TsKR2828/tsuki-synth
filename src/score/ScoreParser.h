#pragma once

#include <juce_core/juce_core.h>
#include <algorithm>
#include <cmath>
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
    double reverbWet   = 0.3;
    double delayTimeMs = 0.0;
    double delayFeedback = 0.0;
    double delayWet    = 0.0;

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
    ScoreEffects effects;
};

struct ScoreEvent
{
    double      time     = 0.0;
    double      duration = 1.0;
    std::string engine;
    std::string note;
    float       velocity = 0.8f;
    std::string material = "steel";
    double      strikePosition = 0.3;
    double      thicknessMm    = 2.0;
    double      radiusMm       = 120.0;
    double      lengthMm       = 100.0;
    double      widthMm        = 25.0;
    std::string exciter = "wood_mallet";
    double      diameterMm     = 0.8;
    double      tensionN       = 0.0;
    double      dampingOverride = -1.0;  // <0 = use material default
    int         fmPreset       = 0;
    float       fmRatio        = -1.0f;   // <0 = use FMParams default
    float       fmIndex        = -1.0f;
    float       fmBrightness   = -1.0f;
    float       fmFeedback     = -1.0f;
    float       fmAttackMs     = -1.0f;
    float       fmReleaseMs    = -1.0f;

    bool        hasGlide       = false;
    std::string glideFromNote;
    double      glideDurationMs = 0.0;
    std::string glideCurve     = "linear";
};

struct ScoreExport
{
    std::string filename;
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
};

inline int noteNameToMidi (const std::string& name)
{
    if (name.empty()) return 60;

    // Pure numeric → MIDI number
    if (name[0] >= '0' && name[0] <= '9')
    {
        try { return std::stoi (name); }
        catch (...) { return 60; }
    }

    // Accept uppercase and lowercase note letters (A-G / a-g)
    char letter = name[0];
    if (letter >= 'a' && letter <= 'g')
        letter = static_cast<char> (letter - 32);  // to uppercase

    if (letter < 'A' || letter > 'G')
        return 60;  // unknown letter → default C4

    static const int noteMap[] = { 9, 11, 0, 2, 4, 5, 7 };  // A..G
    int base = noteMap[letter - 'A'];
    int pos = 1;
    if (pos < static_cast<int> (name.size()) && name[static_cast<size_t> (pos)] == '#')
        { base++; pos++; }
    else if (pos < static_cast<int> (name.size()) && name[static_cast<size_t> (pos)] == 'b')
        { base--; pos++; }

    int octave = 4;
    if (pos < static_cast<int> (name.size()))
    {
        char c = name[static_cast<size_t> (pos)];
        if (c >= '0' && c <= '9')
            octave = c - '0';
    }

    return (octave + 1) * 12 + base;
}

class ScoreParser
{
public:
    static bool parse (const juce::File& file, Score& score)
    {
        score = Score();

        auto text = file.loadFileAsString();
        if (text.isEmpty()) return false;

        auto json = juce::JSON::parse (text);
        if (! json.isObject()) return false;

        auto* obj = json.getDynamicObject();
        if (obj == nullptr) return false;

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
            for (const auto& ev : *evts)
            {
                if (auto* e = ev.getDynamicObject())
                {
                    ScoreEvent se;
                    double velocity = se.velocity;

                    if (! readNumber (*e, "time", se.time, 0.0, 24.0 * 60.0 * 60.0)
                        || ! readNumber (*e, "duration", se.duration, 0.0, 24.0 * 60.0 * 60.0)
                        || ! readString (*e, "engine", se.engine)
                        || ! readString (*e, "note", se.note)
                        || ! readNumber (*e, "velocity", velocity, 0.0, 1.0)
                        || ! isKnownEngine (se.engine))
                    {
                        continue;
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
                        readString (*p, "exciter", se.exciter);
                        readNumber (*p, "diameter_mm", se.diameterMm, 0.1, 50.0);
                        readNumber (*p, "tension_n", se.tensionN, 0.0, 100000.0);
                        if (p->hasProperty ("damping_override"))
                        {
                            auto dv = p->getProperty ("damping_override");
                            double damping = -1.0;
                            if (varToFiniteNumber (dv, damping))
                                se.dampingOverride = std::max (0.0, damping);
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
                    }

                    if (auto* gl = e->getProperty ("glide").getDynamicObject())
                    {
                        std::string fromNote;
                        double durationMs = 0.0;
                        if (readString (*gl, "from_note", fromNote)
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
            }
        }

        if (auto* exp = obj->getProperty ("export").getDynamicObject())
        {
            readString (*exp, "filename", score.exportSettings.filename, true);
            readString (*exp, "format", score.exportSettings.format);

            int bitDepth = score.exportSettings.bitDepth;
            if (readInt (*exp, "bit_depth", bitDepth, 1, 64)
                && (bitDepth == 16 || bitDepth == 24 || bitDepth == 32))
                score.exportSettings.bitDepth = bitDepth;

            readBool (*exp, "normalize", score.exportSettings.normalize);
            readNumber (*exp, "tail_silence_ms", score.exportSettings.tailSilenceMs, 0.0, 60000.0);
            readNumber (*exp, "start_position", score.exportSettings.startPosition, 0.0, 1.0);
            readNumber (*exp, "end_position", score.exportSettings.endPosition, 0.0, 1.0);
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

        return ! score.events.empty() || score.hasLayers();
    }

private:
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
            || engine == "membrane" || engine == "custom"
            || engine == "fm";
    }

    static bool isSupportedSampleRate (int sr)
    {
        return sr == 44100 || sr == 48000 || sr == 88200 || sr == 96000;
    }
};
