#pragma once

#include <juce_core/juce_core.h>
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
    std::string material;
    double      strikePosition = 0.3;
    double      thicknessMm    = 2.0;
    double      radiusMm       = 120.0;
    double      lengthMm       = 100.0;
    double      widthMm        = 25.0;
    std::string exciter;
    double      diameterMm     = 0.8;
    double      tensionN       = 0.0;
    double      dampingOverride = -1.0;  // <0 = use material default
    int         fmPreset       = 0;

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

    if (name[0] >= '0' && name[0] <= '9')
        return std::stoi (name);

    static const int noteMap[] = { 9, 11, 0, 2, 4, 5, 7 };
    int base = noteMap[name[0] - 'A'];
    int pos = 1;
    if (pos < static_cast<int> (name.size()) && name[static_cast<size_t> (pos)] == '#')
        { base++; pos++; }
    else if (pos < static_cast<int> (name.size()) && name[static_cast<size_t> (pos)] == 'b')
        { base--; pos++; }

    int octave = 4;
    if (pos < static_cast<int> (name.size()))
        octave = name[static_cast<size_t> (pos)] - '0';

    return (octave + 1) * 12 + base;
}

class ScoreParser
{
public:
    static bool parse (const juce::File& file, Score& score)
    {
        auto text = file.loadFileAsString();
        if (text.isEmpty()) return false;

        auto json = juce::JSON::parse (text);
        if (! json.isObject()) return false;

        auto* obj = json.getDynamicObject();
        if (obj == nullptr) return false;

        if (auto* meta = obj->getProperty ("meta").getDynamicObject())
        {
            score.meta.title = meta->getProperty ("title").toString().toStdString();
            score.meta.id = meta->getProperty ("id").toString().toStdString();
            score.meta.author = meta->getProperty ("author").toString().toStdString();
            score.meta.description = meta->getProperty ("description").toString().toStdString();
        }

        if (auto* g = obj->getProperty ("global").getDynamicObject())
        {
            score.global.bpm = g->getProperty ("bpm");
            score.global.sampleRate = static_cast<int> ((int) g->getProperty ("sample_rate"));
            score.global.masterVolume = g->getProperty ("master_volume");

            if (auto* fx = g->getProperty ("effects").getDynamicObject())
            {
                if (auto* rev = fx->getProperty ("reverb").getDynamicObject())
                {
                    score.global.effects.reverbDecay = rev->getProperty ("decay");
                    score.global.effects.reverbWet = rev->getProperty ("wet");
                }
                if (auto* del = fx->getProperty ("delay").getDynamicObject())
                {
                    score.global.effects.delayTimeMs = del->getProperty ("time_ms");
                    score.global.effects.delayFeedback = del->getProperty ("feedback");
                    score.global.effects.delayWet = del->getProperty ("wet");
                }
                if (auto* dist = fx->getProperty ("distortion").getDynamicObject())
                {
                    score.global.effects.distortionType = dist->getProperty ("type").toString().toStdString();
                    score.global.effects.distortionDrive = dist->getProperty ("drive");
                    score.global.effects.distortionInstability = dist->getProperty ("instability");
                    score.global.effects.distortionWet = dist->getProperty ("wet");
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
                    se.time = e->getProperty ("time");
                    se.duration = e->getProperty ("duration");
                    se.engine = e->getProperty ("engine").toString().toStdString();
                    se.note = e->getProperty ("note").toString().toStdString();
                    se.velocity = static_cast<float> ((double) e->getProperty ("velocity"));

                    if (auto* p = e->getProperty ("params").getDynamicObject())
                    {
                        se.material = p->getProperty ("material").toString().toStdString();
                        se.strikePosition = p->getProperty ("strike_position");
                        se.thicknessMm = p->getProperty ("thickness_mm");
                        se.radiusMm = p->getProperty ("radius_mm");
                        se.lengthMm = p->getProperty ("length_mm");
                        se.widthMm = p->getProperty ("width_mm");
                        se.exciter = p->getProperty ("exciter").toString().toStdString();
                        if (p->hasProperty ("diameter_mm"))
                            se.diameterMm = p->getProperty ("diameter_mm");
                        if (p->hasProperty ("tension_n"))
                            se.tensionN = p->getProperty ("tension_n");
                        if (p->hasProperty ("damping_override"))
                        {
                            auto dv = p->getProperty ("damping_override");
                            se.dampingOverride = dv.isVoid() ? -1.0 : (double) dv;
                        }
                        if (p->hasProperty ("fm_preset"))
                            se.fmPreset = static_cast<int> ((int) p->getProperty ("fm_preset"));
                    }

                    if (auto* gl = e->getProperty ("glide").getDynamicObject())
                    {
                        se.hasGlide = true;
                        se.glideFromNote = gl->getProperty ("from_note").toString().toStdString();
                        se.glideDurationMs = gl->getProperty ("duration_ms");
                        if (gl->hasProperty ("curve"))
                            se.glideCurve = gl->getProperty ("curve").toString().toStdString();
                    }

                    score.events.push_back (se);
                }
            }
        }

        if (auto* exp = obj->getProperty ("export").getDynamicObject())
        {
            score.exportSettings.filename = exp->getProperty ("filename").toString().toStdString();
            if (exp->hasProperty ("format"))
                score.exportSettings.format = exp->getProperty ("format").toString().toStdString();
            if (exp->hasProperty ("bit_depth"))
                score.exportSettings.bitDepth = static_cast<int> ((int) exp->getProperty ("bit_depth"));
            if (exp->hasProperty ("normalize"))
                score.exportSettings.normalize = (bool) exp->getProperty ("normalize");
            if (exp->hasProperty ("tail_silence_ms"))
                score.exportSettings.tailSilenceMs = exp->getProperty ("tail_silence_ms");
            if (exp->hasProperty ("start_position"))
                score.exportSettings.startPosition = exp->getProperty ("start_position");
            if (exp->hasProperty ("end_position"))
                score.exportSettings.endPosition = exp->getProperty ("end_position");
        }

        if (auto* layersArr = obj->getProperty ("layers").getArray())
        {
            for (const auto& lv : *layersArr)
            {
                if (auto* l = lv.getDynamicObject())
                {
                    ScoreLayer layer;
                    layer.source = l->getProperty ("source").toString().toStdString();
                    if (l->hasProperty ("gain"))
                        layer.gain = l->getProperty ("gain");
                    if (auto* region = l->getProperty ("region").getArray())
                    {
                        if (region->size() >= 2)
                        {
                            layer.regionStart = (*region)[0];
                            layer.regionEnd   = (*region)[1];
                        }
                    }
                    score.layers.push_back (layer);
                }
            }
        }
        if (obj->hasProperty ("crossfade_ms"))
            score.crossfadeMs = static_cast<int> ((int) obj->getProperty ("crossfade_ms"));

        return ! score.events.empty() || score.hasLayers();
    }
};
