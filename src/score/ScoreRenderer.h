#pragma once

#include "ScoreParser.h"
#include "WavWriter.h"
#include "../engines/CimbalomEngine.h"
#include "../engines/ChromaticEngine.h"
#include "../engines/FMPianoEngine.h"
#include "../physics/MaterialDB.h"
#include "../dsp/EffectsChain.h"
#include <algorithm>
#include <cmath>
#include <functional>
#include <memory>
#include <cstring>

/**
 * Offline score -> WAV renderer (the CLI / deaf + AI path).
 *
 * NOTE: this path drives the engine voices with EXPLICIT physical parameters
 * from the score JSON and does NOT apply the plugin's Macro "feel" layer
 * (Material/Tension/Damping... 0-1 knobs that the plugin's startNote() reads).
 * So CLI output is the pure physical model -- which is exactly what the
 * physics-verification harness (tools/physics_verify.py) checks.
 */
class ScoreRenderer
{
    using Material = MaterialDB::Material;

public:
    void setMaterialDB (MaterialDB* db) { materialDB = db; }
    void setBaseDir (const juce::File& dir) { baseDir = dir; }
    const std::vector<std::string>& getWarnings() const { return renderWarnings; }
    const WavWriter::Report& getWriteReport() const { return writeReport; }

    bool validateScore (const Score& score, bool clearMessages = true)
    {
        if (clearMessages) renderWarnings.clear();
        if (materialDB == nullptr)
        {
            renderWarnings.push_back ("Material database is not initialized");
            return false;
        }
        for (size_t i = 0; i < score.events.size(); ++i)
        {
            const auto& ev = score.events[i];
            if (noteNameToMidi (ev.note) < 0)
            {
                renderWarnings.push_back ("Event " + std::to_string (i) + ": invalid note");
                return false;
            }
            if (ev.engine != "fm")
            {
                if (materialDB->getMaterial (juce::String (ev.material)) == nullptr)
                {
                    renderWarnings.push_back ("Event " + std::to_string (i)
                        + ": unknown material \"" + ev.material + "\"");
                    return false;
                }
                if (! isKnownExciter (ev.exciter))
                {
                    renderWarnings.push_back ("Event " + std::to_string (i)
                        + ": unknown exciter \"" + ev.exciter + "\"");
                    return false;
                }
            }
        }
        return true;
    }

    /** Validate every layer reference before a batch starts writing outputs. */
    bool validateLayeredScore (const Score& score, bool clearMessages = true)
    {
        if (clearMessages) renderWarnings.clear();
        if (materialDB == nullptr)
        {
            renderWarnings.push_back ("Material database is not initialized");
            return false;
        }
        if (score.layers.empty())
        {
            renderWarnings.push_back ("Layered score has no layers");
            return false;
        }

        for (const auto& layer : score.layers)
        {
            const juce::File sourceFile = baseDir.getChildFile (
                juce::String (layer.source));
            const auto allowedRoot = layerAllowedRoot();
            if ((! sourceFile.isAChildOf (allowedRoot) && sourceFile != allowedRoot)
                || ! sourceFile.hasFileExtension (".score.json"))
            {
                renderWarnings.push_back ("Layer source must remain inside "
                    + allowedRoot.getFullPathName().toStdString()
                    + " and end in .score.json: " + layer.source);
                return false;
            }
            if (! sourceFile.existsAsFile())
            {
                renderWarnings.push_back ("Layer source does not exist: " + layer.source);
                return false;
            }

            Score subScore;
            if (! ScoreParser::parse (sourceFile, subScore))
            {
                for (const auto& error : subScore.errors)
                    renderWarnings.push_back ("Layer " + layer.source + ": " + error);
                return false;
            }
            if (subScore.hasLayers())
            {
                renderWarnings.push_back ("Nested layer scores are not supported by this renderer");
                return false;
            }
            if (subScore.global.sampleRate != score.global.sampleRate)
            {
                renderWarnings.push_back ("Layer sample rate differs from parent score");
                return false;
            }
            if (! validateScore (subScore, false))
            {
                renderWarnings.push_back ("Layer validation failed: " + layer.source);
                return false;
            }
        }
        return true;
    }

    /// Dump each modal event's model-predicted partials as JSON (single source
    /// of truth for verification). Non-modal (fm) events are skipped.
    juce::String dumpModes (const Score& score)
    {
        // MemoryOutputStream: amortised O(1) append. juce::String's operator<<
        // reallocates + copies the whole accumulated buffer on every append,
        // which is O(total²) over a multi-MB dump — a 3000-event score's dump
        // took >600 s purely in string copies (the real cause of the Vivaldi
        // --dump-modes timeouts, not the modal math, which is milliseconds).
        juce::MemoryOutputStream out (1 << 20);
        out << "{\n  \"input_event_count\": " << static_cast<int> (score.events.size())
            << ",\n  \"events\": [\n";
        bool first = true;
        int sourceIndex = 0;
        int dumpedCount = 0;
        for (const auto& ev : score.events)
        {
            int midiNote = noteNameToMidi (ev.note);
            std::vector<std::vector<ModalResonator::Mode>> allStrings;
            // per-partial body-filter magnitude lookup, filled below (same
            // shape as allStrings) so each partial can carry its own
            // |dry+BodyResonance(dry)| value -- see BodyResonance::
            // magnitudeAt(). The function is identical for every partial of
            // a given voice (it's driven by the *summed* course output, not
            // per-string), but is looked up per-frequency so the JSON stays
            // self-contained (Python never has to know the filter's shape).
            std::function<float(float)> bodyMagFn = [] (float) { return 1.0f; };

            if (ev.engine == "string" || ev.engine == "cimbalom" || ev.engine == "piano")
            {
                const Material* mat = materialDB->getMaterial (juce::String (ev.material));
                if (mat == nullptr) mat = materialDB->getMaterial ("steel");
                if (mat == nullptr) continue;
                // 2026-07 (--amps GATE fix): mirror renderEvent()'s piano
                // branch EXACTLY -- piano's actual render overrides
                // strikePosition/exciter (wood_mallet+0.3 -> felt+0.125)
                // before exciting the string, but this dumpModes() branch
                // previously didn't, so the "theory" was computed for a
                // wood-mallet strike at 0.3 while the render used a felt
                // strike at 0.125 (root-cause report Experiment 4/5, "piano
                // theory/render parameter-mismatch bug", closes a further
                // -4..-26 dB of *diagnostic-only* apparent error once fixed).
                std::string strikeExciter = ev.exciter;
                double strikePos = ev.strikePosition;
                if (ev.engine == "piano")
                {
                    if (strikeExciter == "wood_mallet") strikeExciter = "felt";
                    if (strikePos == 0.3)               strikePos = 0.125;
                }
                CimbalomParams cp;
                cp.materialKey = ev.material;
                cp.strikePosition = strikePos;
                cp.diameterMm = ev.diameterMm;
                cp.numStrings = ev.numStrings;
                cp.detuningCents = ev.detuningCents;
                cp.tensionOverride = ev.tensionN;
                cp.dampingOverride = ev.dampingOverride;
                cp.exciter = cimbalomExciterFromString (strikeExciter);
                cp.tuneToMidi = ev.frequencyMode == "midi";
                cp.randomSeed = score.global.randomSeed;
                cp.eventIndex = static_cast<uint64_t> (sourceIndex);
                auto voice = std::make_shared<CimbalomVoice>();
                voice->prepare (score.global.sampleRate);
                voice->noteOn (midiNote, ev.velocity, *mat, cp);
                allStrings = voice->getAllStringModes();
                bodyMagFn = [voice] (float f) { return voice->getBodyMagnitudeAt (f); };
            }
            else if (ev.engine == "beam" || ev.engine == "tongue_drum"
                  || ev.engine == "plate" || ev.engine == "water_gong"
                  || ev.engine == "custom")
            {
                const Material* mat = materialDB->getMaterial (juce::String (ev.material));
                if (mat == nullptr) continue;
                ChromaticParams cp;
                cp.materialKey = ev.material;
                cp.subEngine = (ev.engine == "beam" || ev.engine == "tongue_drum")
                    ? ChromaticSubEngine::TongueDrum
                    : (ev.engine == "custom") ? ChromaticSubEngine::CustomHarmonics
                                              : ChromaticSubEngine::WaterGong;
                cp.strikePosition = ev.strikePosition;
                cp.plateRadius = ev.radiusMm / 1000.0;
                cp.plateThickness = ev.thicknessMm / 1000.0;
                cp.tongueLength = ev.lengthMm / 1000.0;
                cp.tongueWidth = ev.widthMm / 1000.0;
                cp.tongueThickness = ev.thicknessMm / 1000.0;
                cp.tongueBoundary = ev.beamBoundary == "free_free"
                    ? BeamModel::Boundary::FreeFree : BeamModel::Boundary::Cantilever;
                cp.plateFreeEdge = ev.plateFreeEdge;
                cp.exciterHardness = chromaticExciterHardness (ev.exciter);
                cp.tuneToMidi = ev.frequencyMode == "midi";
                cp.randomSeed = score.global.randomSeed;
                cp.eventIndex = static_cast<uint64_t> (sourceIndex);
                // Lifetime fix (2026-07-18): the custom-partial atoms used to be
                // stack locals whose ADDRESSES were wired into voice->pRatio/pAmp.
                // The voice itself outlives this block (the bodyMagFn lambda
                // below captures the shared_ptr), so once the block ended the
                // voice held dangling pointers -- only "safe" by accident
                // because nothing re-reads pRatio/pAmp after noteOn(). Bundling
                // the atoms into the same heap allocation as the voice (and
                // handing out an aliasing shared_ptr) makes the atoms' lifetime
                // cover the voice's by construction. Pure lifetime refactor:
                // the values stored/loaded are identical, so neither the dump
                // output nor any rendered audio changes.
                struct VoiceWithCustomAtoms
                {
                    std::atomic<float> ratioAtoms[8];
                    std::atomic<float> ampAtoms[8];
                    ChromaticVoice voice;
                };
                auto bundle = std::make_shared<VoiceWithCustomAtoms>();
                // Aliasing shared_ptr: shares ownership of the whole bundle but
                // points at the voice member, so existing capture sites keep
                // the entire bundle (voice + atoms) alive together.
                std::shared_ptr<ChromaticVoice> voice (bundle, &bundle->voice);
                voice->prepare (score.global.sampleRate);

                // Custom partials must be wired before noteOn(), exactly as in
                // renderChromatic().  The dump is a contract, not a second set
                // of defaults.
                if (cp.subEngine == ChromaticSubEngine::CustomHarmonics)
                {
                    for (int ci = 0; ci < 8; ++ci)
                    {
                        if (ev.customRatios[ci] >= 0.0f)
                        {
                            bundle->ratioAtoms[ci].store (ev.customRatios[ci]);
                            voice->pRatio[ci] = &bundle->ratioAtoms[ci];
                        }
                        if (ev.customAmps[ci] >= 0.0f)
                        {
                            bundle->ampAtoms[ci].store (ev.customAmps[ci]);
                            voice->pAmp[ci] = &bundle->ampAtoms[ci];
                        }
                    }
                }
                voice->noteOn (midiNote, ev.velocity, *mat, cp);
                allStrings.push_back (voice->getModes());
                bodyMagFn = [voice] (float f) { return voice->getBodyMagnitudeAt (f); };
            }
            else
            {
                ++sourceIndex;
                continue;   // fm = non-modal synthesis
            }

            if (! first) out << ",\n";
            first = false;
            auto jsonEsc = [] (const juce::String& s) { return s.replace ("\\", "\\\\").replace ("\"", "\\\""); };
            auto modeToJson = [&] (const ModalResonator::Mode& m)
            {
                juce::String s;
                // decay uses scientific notation (not fixed 4dp): high-frequency
                // beam/plate partials can have genuinely positive decayTime well
                // under 1e-4 s (e.g. a small tongue_drum tine's upper partials,
                // whose raw physical fundamental is far above the MIDI-tuned
                // target -- see BeamModel.h -- so the damping law 1/(2a+b*f^2+g*f)
                // evaluated at that high raw f yields a small-but-real decay).
                // Fixed-point %.4f silently rounds anything below 5e-5 s to the
                // string "0.0000", which is byte-identical to a true zero once
                // re-parsed as JSON -- verify_score.py's "decay must be > 0"
                // check (tools/verify_score.py bad_decay, d <= 0.0) then flags a
                // physically-valid positive decay as a bug. This is a dump
                // (diagnostic/verification) precision fix only: it does not touch
                // BeamModel/PlateModel/ModalResonator or the render() audio path,
                // so no rendered score's audio output changes (Sec.1 rule 10 does
                // not apply here -- the underlying decayTime numeric value driving
                // synthesis is unchanged, only how --dump-modes prints it).
                //
                // "body_mag" (2026-07, --amps GATE fix): |dry+BodyResonance(dry)|
                // at this mode's frequency, read from the SAME BodyResonance
                // object noteOn() configured for the real render (amount=0.5,
                // 120/280/500 Hz filters) -- see BodyResonance::magnitudeAt().
                // Theory-only: a function of the model's own linear filter
                // state, never of rendered audio.
                s << "{\"freq\": " << juce::String (m.frequency, 3)
                  << ", \"amp\": " << juce::String (m.amplitude, 5)
                  << ", \"decay\": " << juce::String (m.decayTime, 4, true)
                  << ", \"body_mag\": " << juce::String (bodyMagFn (m.frequency), 5) << "}";
                return s;
            };

            out << "    { \"source_index\": " << sourceIndex
                << ", \"engine\": \"" << jsonEsc (juce::String (ev.engine))
                << "\", \"note\": \"" << jsonEsc (juce::String (ev.note))
                << "\", \"midi\": " << midiNote
                << ", \"frequency_mode\": \"" << jsonEsc (juce::String (ev.frequencyMode))
                << "\", \"partials\": [";
            if (! allStrings.empty())
                for (size_t i = 0; i < allStrings[0].size(); ++i)
                {
                    if (i) out << ", ";
                    out << modeToJson (allStrings[0][i]);
                }
            out << "], \"strings\": [";
            for (size_t s = 0; s < allStrings.size(); ++s)
            {
                if (s) out << ", ";
                out << "[";
                for (size_t i = 0; i < allStrings[s].size(); ++i)
                {
                    if (i) out << ", ";
                    out << modeToJson (allStrings[s][i]);
                }
                out << "]";
            }
            out << "] }";
            ++sourceIndex;
            ++dumpedCount;
        }
        out << "\n  ],\n  \"dumped_event_count\": " << dumpedCount << "\n}\n";
        return out.toString();
    }

    bool render (const Score& score, const juce::File& outputFile)
    {
        renderWarnings.clear();
        writeReport = {};
        if (score.events.empty() || ! validateScore (score, false))
            return false;

        double sr = score.global.sampleRate;
        if (! isValidSampleRate (sr))
            return false;

        double totalDuration = 0.0;
        for (size_t i = 0; i < score.events.size(); ++i)
            totalDuration = std::max (totalDuration, eventEndTime (
                score.events[i], sr, score.global.randomSeed, i));

        totalDuration += wallDelaySeconds (score.global.effects);
        totalDuration += effectTailSeconds (score.global.effects);
        totalDuration += score.exportSettings.tailSilenceMs / 1000.0;
        int64_t totalSamples64 = static_cast<int64_t> (std::ceil (totalDuration * sr)) + 1;
        if (! validateBufferBudget (totalSamples64, "render output"))
            return false;
        int totalSamples = static_cast<int> (totalSamples64);

        juce::AudioBuffer<float> buffer (2, totalSamples);
        buffer.clear();

        for (size_t i = 0; i < score.events.size(); ++i)
            renderEvent (score.events[i], buffer, sr, score.global.randomSeed, i);

        applyEffects (buffer, score.global, sr);
        if (! trimBuffer (buffer, score.exportSettings))
            return false;

        return WavWriter::write (outputFile, buffer, sr,
                                 score.exportSettings.bitDepth,
                                 score.exportSettings.normalize,
                                 &writeReport);
    }

    bool renderLayered (const Score& score, const juce::File& outputFile)
    {
        writeReport = {};
        if (! validateLayeredScore (score))
            return false;

        double sr = score.global.sampleRate;
        if (! isValidSampleRate (sr))
            return false;

        int crossfadeSamples = static_cast<int> (score.crossfadeMs / 1000.0 * sr);

        struct RenderedLayer
        {
            juce::AudioBuffer<float> buffer;
            int numSamples = 0;
        };

        std::vector<RenderedLayer> renderedLayers;
        renderedLayers.reserve (score.layers.size());
        int64_t retainedLayerSamples = 0;

        for (const auto& layer : score.layers)
        {
            juce::File sourceFile = baseDir.getChildFile (juce::String (layer.source));
            const auto allowedRoot = layerAllowedRoot();
            if ((! sourceFile.isAChildOf (allowedRoot) && sourceFile != allowedRoot)
                || ! sourceFile.hasFileExtension (".score.json"))
            {
                renderWarnings.push_back ("Layer source must remain inside "
                    + allowedRoot.getFullPathName().toStdString()
                    + " and end in .score.json: " + layer.source);
                return false;
            }
            if (! sourceFile.existsAsFile())
            {
                renderWarnings.push_back ("Layer source does not exist: " + layer.source);
                return false;
            }

            Score subScore;
            if (! ScoreParser::parse (sourceFile, subScore))
            {
                for (const auto& error : subScore.errors)
                    renderWarnings.push_back ("Layer " + layer.source + ": " + error);
                return false;
            }
            if (subScore.hasLayers()
                || subScore.global.sampleRate != score.global.sampleRate)
            {
                renderWarnings.push_back (subScore.hasLayers()
                    ? "Nested layer scores are not supported by this renderer"
                    : "Layer sample rate differs from parent score");
                return false;
            }
            if (! validateScore (subScore, false)) return false;

            double subDuration = 0.0;
            for (size_t i = 0; i < subScore.events.size(); ++i)
                subDuration = std::max (subDuration, eventEndTime (
                    subScore.events[i], sr, subScore.global.randomSeed, i));
            subDuration += wallDelaySeconds (subScore.global.effects);
            subDuration += effectTailSeconds (subScore.global.effects);
            subDuration += subScore.exportSettings.tailSilenceMs / 1000.0;

            int64_t subTotalSamples64 = static_cast<int64_t> (std::ceil (subDuration * sr)) + 1;
            if (! validateBufferBudget (subTotalSamples64, "layer source " + layer.source)
                || ! validateBufferBudget (retainedLayerSamples + subTotalSamples64,
                                            "layered render working set while loading "
                                                + layer.source))
                return false;
            int subTotalSamples = static_cast<int> (subTotalSamples64);

            juce::AudioBuffer<float> subBuffer (2, subTotalSamples);
            subBuffer.clear();

            for (size_t i = 0; i < subScore.events.size(); ++i)
                renderEvent (subScore.events[i], subBuffer, sr,
                             subScore.global.randomSeed, i);

            applyEffects (subBuffer, subScore.global, sr);
            if (! trimBuffer (subBuffer, subScore.exportSettings))
                return false;
            subTotalSamples = subBuffer.getNumSamples();

            double rs = std::clamp (layer.regionStart, 0.0, 1.0);
            double re = std::clamp (layer.regionEnd, 0.0, 1.0);
            if (re < rs) std::swap (rs, re);
            int regionStart = std::clamp (static_cast<int> (rs * subTotalSamples), 0, subTotalSamples - 1);
            int regionEnd   = std::clamp (static_cast<int> (re * subTotalSamples), regionStart + 1, subTotalSamples);
            int regionLen   = regionEnd - regionStart;

            RenderedLayer rl;
            for (int channel = 0; channel < subBuffer.getNumChannels(); ++channel)
                std::memmove (subBuffer.getWritePointer (channel),
                              subBuffer.getReadPointer (channel, regionStart),
                              static_cast<size_t> (regionLen) * sizeof (float));
            subBuffer.setSize (subBuffer.getNumChannels(), regionLen,
                               true, false, true);
            rl.buffer = std::move (subBuffer);
            rl.buffer.applyGain (static_cast<float> (layer.gain));
            rl.numSamples = regionLen;
            renderedLayers.push_back (std::move (rl));
            retainedLayerSamples += regionLen;
        }

        // Clamp crossfade to shortest layer to prevent negative offsets
        int minLayerLen = renderedLayers[0].numSamples;
        for (const auto& rl : renderedLayers)
            minLayerLen = std::min (minLayerLen, rl.numSamples);
        crossfadeSamples = std::min (crossfadeSamples, minLayerLen - 1);
        crossfadeSamples = std::max (crossfadeSamples, 0);

        int totalOut = 0;
        for (size_t i = 0; i < renderedLayers.size(); ++i)
        {
            if (i == 0)
                totalOut = renderedLayers[i].numSamples;
            else
                totalOut += renderedLayers[i].numSamples - crossfadeSamples;
        }
        totalOut = std::max (totalOut, 1);

        const int wallSamples = static_cast<int> (
            wallDelaySeconds (score.global.effects) * sr);
        const int effectSamples = static_cast<int> (
            effectTailSeconds (score.global.effects) * sr);
        const int tailSamples = static_cast<int> (
            score.exportSettings.tailSilenceMs / 1000.0 * sr);
        const int64_t finalSamples = static_cast<int64_t> (totalOut) + wallSamples
            + effectSamples + tailSamples;
        if (! validateBufferBudget (finalSamples + retainedLayerSamples,
                                    "layered render working set")) return false;

        juce::AudioBuffer<float> output (2, static_cast<int> (finalSamples));
        output.clear();

        int writePos = 0;
        for (size_t i = 0; i < renderedLayers.size(); ++i)
        {
            const auto& rl = renderedLayers[i];

            for (int s = 0; s < rl.numSamples; ++s)
            {
                int outIdx = writePos + s;
                if (outIdx < 0 || outIdx >= totalOut) continue;

                float sampleL = rl.buffer.getSample (0, s);
                float sampleR = rl.buffer.getSample (1, s);

                // Crossfade: fade in at start of layer (except first)
                if (i > 0 && s < crossfadeSamples && crossfadeSamples > 0)
                {
                    float fadeIn = static_cast<float> (s) / crossfadeSamples;
                    sampleL *= fadeIn;
                    sampleR *= fadeIn;
                }
                // Crossfade: fade out at end of layer (except last)
                if (i < renderedLayers.size() - 1)
                {
                    int fadeOutStart = rl.numSamples - crossfadeSamples;
                    if (s >= fadeOutStart && crossfadeSamples > 0)
                    {
                        float fadeOut = static_cast<float> (rl.numSamples - s) / crossfadeSamples;
                        sampleL *= fadeOut;
                        sampleR *= fadeOut;
                    }
                }

                output.addSample (0, outIdx, sampleL);
                output.addSample (1, outIdx, sampleR);
            }

            if (i < renderedLayers.size() - 1)
                writePos += rl.numSamples - crossfadeSamples;
        }

        applyEffects (output, score.global, sr);

        if (! trimBuffer (output, score.exportSettings))
            return false;

        return WavWriter::write (outputFile, output, sr,
                                 score.exportSettings.bitDepth,
                                 score.exportSettings.normalize,
                                 &writeReport);
    }

private:
    void renderEvent (const ScoreEvent& ev, juce::AudioBuffer<float>& buffer, double sr,
                      uint64_t randomSeed, uint64_t eventIndex)
    {
        int startSample = juce::jlimit (0, buffer.getNumSamples(),
                                        static_cast<int> (std::max (0.0, ev.time) * sr));
        // Let voice ring into tail region — isActive() stops the loop naturally
        int endSample = buffer.getNumSamples();
        if (startSample >= endSample)
            return;

        int midiNote = noteNameToMidi (ev.note);
        const Material* mat = materialDB->getMaterial (juce::String (ev.material));

        if (ev.engine == "string" || ev.engine == "cimbalom")
        {
            renderCimbalom (ev, mat, midiNote, startSample, endSample, buffer, sr,
                            randomSeed, eventIndex);
        }
        else if (ev.engine == "beam" || ev.engine == "tongue_drum")
        {
            renderChromatic (ev, mat, midiNote, ChromaticSubEngine::TongueDrum,
                             startSample, endSample, buffer, sr, randomSeed, eventIndex);
        }
        else if (ev.engine == "plate" || ev.engine == "water_gong")
        {
            renderChromatic (ev, mat, midiNote, ChromaticSubEngine::WaterGong,
                             startSample, endSample, buffer, sr, randomSeed, eventIndex);
        }
        else if (ev.engine == "fm")
        {
            renderFM (ev, midiNote, startSample, endSample, buffer, sr,
                      randomSeed, eventIndex);
        }
        else if (ev.engine == "custom")
        {
            renderChromatic (ev, mat, midiNote, ChromaticSubEngine::CustomHarmonics,
                             startSample, endSample, buffer, sr, randomSeed, eventIndex);
        }
        else if (ev.engine == "piano")
        {
            // Physical piano = struck stiff steel string (StringModel), calibrated:
            // felt hammer + strike near 1/8 of the string. Only override the
            // ScoreEvent defaults so explicit scores still win.
            ScoreEvent pev = ev;
            if (pev.exciter == "wood_mallet") pev.exciter = "felt";
            if (pev.strikePosition == 0.3)    pev.strikePosition = 0.125;
            renderCimbalom (pev, mat, midiNote, startSample, endSample, buffer, sr,
                            randomSeed, eventIndex);
        }
    }

    void renderCimbalom (const ScoreEvent& ev, const Material* mat, int midiNote,
                          int start, int end, juce::AudioBuffer<float>& buf, double sr,
                          uint64_t randomSeed, uint64_t eventIndex)
    {
        if (mat == nullptr) return;

        CimbalomParams cp;
        cp.materialKey = ev.material;
        cp.strikePosition = ev.strikePosition;
        cp.diameterMm = ev.diameterMm;
        cp.numStrings = ev.numStrings;
        cp.detuningCents = ev.detuningCents;
        cp.tensionOverride = ev.tensionN;
        cp.dampingOverride = ev.dampingOverride;
        cp.exciter = cimbalomExciterFromString (ev.exciter);
        cp.tuneToMidi = ev.frequencyMode == "midi";
        cp.randomSeed = randomSeed;
        cp.eventIndex = eventIndex;

        CimbalomVoice voice;
        voice.prepare (sr);
        voice.noteOn (midiNote, ev.velocity, *mat, cp);

        int noteOffSample = juce::jlimit (start, end,
            start + static_cast<int> (std::max (0.0, ev.duration) * sr * 0.9));

        int glideSamples = 0;
        double glideStartRatio = 1.0;
        bool useExpCurve = false;
        if (ev.hasGlide)
        {
            int fromMidi = noteNameToMidi (ev.glideFromNote);
            double fromFreq = juce::MidiMessage::getMidiNoteInHertz (fromMidi);
            double toFreq   = juce::MidiMessage::getMidiNoteInHertz (midiNote);
            glideStartRatio = fromFreq / toFreq;
            glideSamples = static_cast<int> (ev.glideDurationMs / 1000.0 * sr);
            useExpCurve = (ev.glideCurve == "exponential");
        }

        for (int i = start; i < end && voice.isActive(); ++i)
        {
            if (i == noteOffSample) voice.noteOff();

            if (ev.hasGlide && (i - start) < glideSamples)
            {
                double t = static_cast<double> (i - start) / glideSamples;
                double factor = useExpCurve
                    ? glideStartRatio * std::exp (std::log (1.0 / glideStartRatio) * t)
                    : glideStartRatio + (1.0 - glideStartRatio) * t;
                voice.scaleFrequencies (factor);
            }
            else if (ev.hasGlide && (i - start) == glideSamples)
            {
                voice.scaleFrequencies (1.0);
            }

            float v = voice.getNextSample();   // engine getNextSample() now applies its own output gain
            buf.addSample (0, i, v);
            buf.addSample (1, i, v);
        }
    }

    void renderChromatic (const ScoreEvent& ev, const Material* mat, int midiNote,
                           ChromaticSubEngine sub, int start, int end,
                           juce::AudioBuffer<float>& buf, double sr,
                           uint64_t randomSeed, uint64_t eventIndex)
    {
        if (mat == nullptr) return;

        ChromaticParams cp;
        cp.materialKey = ev.material;
        cp.subEngine = sub;
        cp.strikePosition = ev.strikePosition;
        cp.plateRadius = ev.radiusMm / 1000.0;
        cp.plateThickness = ev.thicknessMm / 1000.0;
        cp.tongueLength = ev.lengthMm / 1000.0;
        cp.tongueWidth = ev.widthMm / 1000.0;
        cp.tongueThickness = ev.thicknessMm / 1000.0;
        cp.tongueBoundary = ev.beamBoundary == "free_free"
            ? BeamModel::Boundary::FreeFree : BeamModel::Boundary::Cantilever;
        cp.plateFreeEdge = ev.plateFreeEdge;
        cp.exciterHardness = chromaticExciterHardness (ev.exciter);
        cp.tuneToMidi = ev.frequencyMode == "midi";
        cp.randomSeed = randomSeed;
        cp.eventIndex = eventIndex;

        ChromaticVoice voice;
        voice.prepare (sr);

        std::atomic<float> ratioAtoms[8];
        std::atomic<float> ampAtoms[8];
        if (sub == ChromaticSubEngine::CustomHarmonics)
        {
            for (int ci = 0; ci < 8; ++ci)
            {
                if (ev.customRatios[ci] >= 0.0f)
                {
                    ratioAtoms[ci].store (ev.customRatios[ci]);
                    voice.pRatio[ci] = &ratioAtoms[ci];
                }
                if (ev.customAmps[ci] >= 0.0f)
                {
                    ampAtoms[ci].store (ev.customAmps[ci]);
                    voice.pAmp[ci] = &ampAtoms[ci];
                }
            }
        }

        voice.noteOn (midiNote, ev.velocity, *mat, cp);

        int noteOffSample = juce::jlimit (start, end,
            start + static_cast<int> (std::max (0.0, ev.duration) * sr * 0.9));

        int glideSamples = 0;
        double glideStartRatio = 1.0;
        bool useExpCurve = false;
        if (ev.hasGlide)
        {
            int fromMidi = noteNameToMidi (ev.glideFromNote);
            double fromFreq = juce::MidiMessage::getMidiNoteInHertz (fromMidi);
            double toFreq   = juce::MidiMessage::getMidiNoteInHertz (midiNote);
            glideStartRatio = fromFreq / toFreq;
            glideSamples = static_cast<int> (ev.glideDurationMs / 1000.0 * sr);
            useExpCurve = (ev.glideCurve == "exponential");
        }

        for (int i = start; i < end && voice.isActive(); ++i)
        {
            if (i == noteOffSample) voice.noteOff();

            if (ev.hasGlide && (i - start) < glideSamples)
            {
                double t = static_cast<double> (i - start) / glideSamples;
                double factor = useExpCurve
                    ? glideStartRatio * std::exp (std::log (1.0 / glideStartRatio) * t)
                    : glideStartRatio + (1.0 - glideStartRatio) * t;
                voice.scaleFrequencies (factor);
            }
            else if (ev.hasGlide && (i - start) == glideSamples)
            {
                voice.scaleFrequencies (1.0);
            }

            float v = voice.getNextSample();   // engine getNextSample() now applies its own output gain
            buf.addSample (0, i, v);
            buf.addSample (1, i, v);
        }
    }

    void renderFM (const ScoreEvent& ev, int midiNote,
                    int start, int end,
                    juce::AudioBuffer<float>& buf, double sr,
                    uint64_t randomSeed, uint64_t eventIndex)
    {
        FMParams fp;
        fp.preset = static_cast<FMPreset> (ev.fmPreset);
        fp.randomSeed = randomSeed;
        fp.eventIndex = eventIndex;

        // Forward detailed FM params if specified in JSON (>=0 means explicitly set)
        if (ev.fmRatio      >= 0.0f) fp.ratio      = ev.fmRatio;
        if (ev.fmIndex      >= 0.0f) fp.index       = ev.fmIndex;
        if (ev.fmBrightness >= 0.0f) fp.brightness  = ev.fmBrightness;
        if (ev.fmFeedback   >= 0.0f) fp.feedback    = ev.fmFeedback;
        if (ev.fmAttackMs   >= 0.0f) fp.attackMs    = ev.fmAttackMs;
        if (ev.fmReleaseMs  >= 0.0f) fp.releaseMs   = ev.fmReleaseMs;

        FMVoice voice;
        voice.prepare (sr);
        voice.noteOn (midiNote, ev.velocity, fp);

        int noteOffSample = juce::jlimit (start, end,
            start + static_cast<int> (std::max (0.0, ev.duration) * sr * 0.9));

        int glideSamples = 0;
        double glideStartRatio = 1.0;
        bool useExpCurve = false;
        if (ev.hasGlide)
        {
            int fromMidi = noteNameToMidi (ev.glideFromNote);
            double fromFreq = juce::MidiMessage::getMidiNoteInHertz (fromMidi);
            double toFreq   = juce::MidiMessage::getMidiNoteInHertz (midiNote);
            glideStartRatio = fromFreq / toFreq;
            glideSamples = static_cast<int> (ev.glideDurationMs / 1000.0 * sr);
            useExpCurve = (ev.glideCurve == "exponential");
        }

        for (int i = start; i < end && voice.isActive(); ++i)
        {
            if (i == noteOffSample) voice.noteOff();

            if (ev.hasGlide && (i - start) < glideSamples)
            {
                double t = static_cast<double> (i - start) / glideSamples;
                double factor = useExpCurve
                    ? glideStartRatio * std::exp (std::log (1.0 / glideStartRatio) * t)
                    : glideStartRatio + (1.0 - glideStartRatio) * t;
                voice.scaleFrequency (factor);
            }
            else if (ev.hasGlide && (i - start) == glideSamples)
            {
                voice.scaleFrequency (1.0);
            }

            float v = voice.getNextSample();   // engine getNextSample() now applies its own output gain
            buf.addSample (0, i, v);
            buf.addSample (1, i, v);
        }
    }

    MaterialDB* materialDB = nullptr;
    juce::File  baseDir;
    std::vector<std::string> renderWarnings;
    WavWriter::Report writeReport;

    static bool isKnownExciter (const std::string& exciter)
    {
        return exciter == "cotton" || exciter == "cotton_mallet"
            || exciter == "felt" || exciter == "felt_mallet"
            || exciter == "wood" || exciter == "wood_mallet"
            || exciter == "metal" || exciter == "metal_mallet"
            || exciter == "metal_hammer" || exciter == "metal_tip"
            || exciter == "hard_plastic" || exciter == "hard_strike"
            || exciter == "finger" || exciter == "finger_tap"
            || exciter == "bow" || exciter == "bow_slow" || exciter == "brush"
            || exciter == "rubber_mallet" || exciter == "metal_scrape"
            || exciter == "pluck" || exciter == "medium" || exciter == "sharp";
    }

    /// Exciter string -> CimbalomEngine::ExciterType, shared by renderCimbalom()
    /// and dumpModes() so the diagnostic (--dump-modes) path and the render
    /// path always agree on which hammer the score asked for (single source
    /// of truth, ROADMAP_PHYSICS.md §2c).
    static ExciterType cimbalomExciterFromString (const std::string& exciter)
    {
        if (exciter == "cotton" || exciter == "cotton_mallet") return ExciterType::Cotton;
        if (exciter == "felt" || exciter == "felt_mallet") return ExciterType::Felt;
        if (exciter == "metal" || exciter == "metal_mallet"
            || exciter == "metal_hammer") return ExciterType::Metal;
        if (exciter == "finger" || exciter == "finger_tap") return ExciterType::Felt;
        if (exciter == "bow") return ExciterType::Cotton;
        if (exciter == "hard_plastic" || exciter == "wood"
            || exciter == "wood_mallet" || exciter == "pluck") return ExciterType::Wood;
        if (exciter == "rubber_mallet") return ExciterType::Felt;
        if (exciter == "metal_scrape") return ExciterType::Metal;
        if (exciter == "bow_slow" || exciter == "brush") return ExciterType::Cotton;
        return ExciterType::Wood;
    }

    static float chromaticExciterHardness (const std::string& exciter)
    {
        if (exciter == "cotton" || exciter == "cotton_mallet"
            || exciter == "finger" || exciter == "finger_tap"
            || exciter == "bow" || exciter == "bow_slow" || exciter == "brush")
            return 0.0f;
        if (exciter == "felt" || exciter == "felt_mallet"
            || exciter == "medium" || exciter == "rubber_mallet")
            return 1.0f;
        if (exciter == "metal" || exciter == "metal_mallet"
            || exciter == "metal_hammer" || exciter == "metal_tip"
            || exciter == "sharp" || exciter == "metal_scrape")
            return 3.0f;
        return 2.0f;
    }

    double eventMaxT60 (const ScoreEvent& ev, double sr,
                        uint64_t randomSeed, uint64_t eventIndex) const
    {
        if (ev.engine == "fm") return 0.0;
        const Material* mat = materialDB != nullptr
            ? materialDB->getMaterial (juce::String (ev.material)) : nullptr;
        if (mat == nullptr) return 0.0;

        std::vector<std::vector<ModalResonator::Mode>> modeSets;
        if (ev.engine == "string" || ev.engine == "cimbalom" || ev.engine == "piano")
        {
            ScoreEvent effective = ev;
            if (effective.engine == "piano")
            {
                if (effective.exciter == "wood_mallet") effective.exciter = "felt";
                if (effective.strikePosition == 0.3) effective.strikePosition = 0.125;
            }
            CimbalomParams cp;
            cp.materialKey = effective.material;
            cp.strikePosition = effective.strikePosition;
            cp.diameterMm = effective.diameterMm;
            cp.numStrings = effective.numStrings;
            cp.detuningCents = effective.detuningCents;
            cp.tensionOverride = effective.tensionN;
            cp.dampingOverride = effective.dampingOverride;
            cp.exciter = cimbalomExciterFromString (effective.exciter);
            cp.tuneToMidi = effective.frequencyMode == "midi";
            cp.randomSeed = randomSeed;
            cp.eventIndex = eventIndex;
            CimbalomVoice voice;
            voice.prepare (sr);
            voice.noteOn (noteNameToMidi (effective.note), effective.velocity, *mat, cp);
            modeSets = voice.getAllStringModes();
        }
        else
        {
            ChromaticParams cp;
            cp.materialKey = ev.material;
            cp.subEngine = (ev.engine == "beam" || ev.engine == "tongue_drum")
                ? ChromaticSubEngine::TongueDrum
                : ev.engine == "custom" ? ChromaticSubEngine::CustomHarmonics
                                          : ChromaticSubEngine::WaterGong;
            cp.strikePosition = ev.strikePosition;
            cp.plateRadius = ev.radiusMm / 1000.0;
            cp.plateThickness = ev.thicknessMm / 1000.0;
            cp.tongueLength = ev.lengthMm / 1000.0;
            cp.tongueWidth = ev.widthMm / 1000.0;
            cp.tongueThickness = ev.thicknessMm / 1000.0;
            cp.tongueBoundary = ev.beamBoundary == "free_free"
                ? BeamModel::Boundary::FreeFree : BeamModel::Boundary::Cantilever;
            cp.plateFreeEdge = ev.plateFreeEdge;
            cp.exciterHardness = chromaticExciterHardness (ev.exciter);
            cp.tuneToMidi = ev.frequencyMode == "midi";
            cp.randomSeed = randomSeed;
            cp.eventIndex = eventIndex;
            ChromaticVoice voice;
            voice.prepare (sr);
            std::atomic<float> ratios[8];
            std::atomic<float> amps[8];
            if (cp.subEngine == ChromaticSubEngine::CustomHarmonics)
            {
                for (int i = 0; i < 8; ++i)
                {
                    if (ev.customRatios[i] >= 0.0f)
                    {
                        ratios[i].store (ev.customRatios[i]);
                        voice.pRatio[i] = &ratios[i];
                    }
                    if (ev.customAmps[i] >= 0.0f)
                    {
                        amps[i].store (ev.customAmps[i]);
                        voice.pAmp[i] = &amps[i];
                    }
                }
            }
            voice.noteOn (noteNameToMidi (ev.note), ev.velocity, *mat, cp);
            modeSets.push_back (voice.getModes());
        }

        double maxT60 = 0.0;
        for (const auto& modes : modeSets)
            for (const auto& mode : modes)
                if (std::isfinite (mode.decayTime) && mode.decayTime > maxT60)
                    maxT60 = mode.decayTime;
        return maxT60;
    }

    double eventEndTime (const ScoreEvent& ev, double sr,
                         uint64_t randomSeed, uint64_t eventIndex) const
    {
        const double start = std::max (0.0, ev.time);
        const double duration = std::max (0.0, ev.duration);
        double end = start + duration;

        if (ev.engine == "fm")
        {
            const double releaseMs = ev.fmReleaseMs >= 0.0f
                ? ev.fmReleaseMs
                : FMParams().releaseMs;
            const double noteOff = start + duration * 0.9;
            end = std::max (end, noteOff + releaseMs * 0.001);
        }
        else
        {
            // ModalResonator reaches -60 dB at T60. noteOff occurs at 90%
            // of the authored duration and changes the remaining decay time
            // to 5%, so allocate the exact worst-mode active interval rather
            // than a fixed five-second tail.
            const double maxT60 = eventMaxT60 (ev, sr, randomSeed, eventIndex);
            const double noteOff = duration * 0.9;
            const double active = maxT60 <= noteOff
                ? maxT60 : noteOff + (maxT60 - noteOff) * 0.05;
            end = std::max (end, start + active);
        }

        return end;
    }

    static double wallDelaySeconds (const ScoreEffects& effects)
    {
        return effects.wallDistanceM > 0.0
            ? (2.0 * effects.wallDistanceM / 343.0)
            : 0.0;
    }

    static double effectTailSeconds (const ScoreEffects& fx)
    {
        double tail = 0.0;
        if (fx.reverbWet > 0.001)
        {
            // SimpleReverb::setDecayTime() makes decay an authored T60.
            // Even T60=0 retains the first comb + serial-allpass response.
            const double longestComb = (1617.0 + 23.0) / 44100.0;
            const double allPassLatency = (556.0 + 441.0 + 341.0 + 225.0
                                           + 4.0 * 23.0) / 44100.0;
            tail += longestComb + fx.reverbDecay + allPassLatency;
        }
        if (fx.delayWet > 0.001 && fx.delayTimeMs > 0.0)
        {
            const double repeats = fx.delayFeedback > 0.0
                ? std::ceil (std::log (0.001) / std::log (fx.delayFeedback)) : 1.0;
            // StereoDelay's right channel is intentionally 10% longer.
            tail += std::max (1.0, repeats) * fx.delayTimeMs * 0.001 * 1.10;
        }
        return tail;
    }

    bool validateBufferBudget (int64_t samples, const std::string& label)
    {
        static constexpr int64_t maxBytes = int64_t (1) << 30; // 1 GiB per stereo buffer
        if (samples <= 0 || samples > std::numeric_limits<int>::max())
        {
            renderWarnings.push_back (label + ": invalid or address-space-exceeding sample count "
                + std::to_string (samples));
            return false;
        }
        const int64_t bytes = samples * 2 * static_cast<int64_t> (sizeof (float));
        if (bytes > maxBytes)
        {
            renderWarnings.push_back (label + " requires " + std::to_string (bytes)
                + " bytes, exceeding the explicit 1 GiB render-buffer budget");
            return false;
        }
        return true;
    }

    juce::File layerAllowedRoot() const
    {
        juce::File current = baseDir;
        for (;;)
        {
            if (current.getFileName().equalsIgnoreCase ("scores"))
                return current;
            const auto parent = current.getParentDirectory();
            if (parent == current) break;
            current = parent;
        }
        return baseDir;
    }

    static float wallReflectionGain (const std::string& material)
    {
        if (material == "stone" || material == "concrete")
            return 0.65f;
        if (material == "glass" || material == "metal")
            return 0.55f;
        if (material == "wood")
            return 0.35f;
        if (material == "fabric" || material == "curtain")
            return 0.15f;
        return 0.4f;
    }

    static void applyWallReflection (
        juce::AudioBuffer<float>& buffer, const ScoreEffects& effects, double sr)
    {
        const int delaySamples = static_cast<int> (
            std::round (wallDelaySeconds (effects) * sr));
        if (delaySamples <= 0 || delaySamples >= buffer.getNumSamples())
            return;

        const float gain = wallReflectionGain (effects.wallMaterial);
        for (int channel = 0; channel < buffer.getNumChannels(); ++channel)
        {
            float* samples = buffer.getWritePointer (channel);
            for (int i = buffer.getNumSamples() - 1; i >= delaySamples; --i)
                samples[i] += samples[i - delaySamples] * gain;
        }
    }

    static void configureEffects (
        EffectsChain& fx, const ScoreGlobal& global, double sr)
    {
        fx.prepare (sr);
        EffectsParams fxp;
        fxp.reverbEnabled = global.effects.reverbWet > 0.001;
        fxp.reverbWet = static_cast<float> (global.effects.reverbWet);
        fxp.reverbDecaySeconds = static_cast<float> (global.effects.reverbDecay);
        fxp.delayEnabled = global.effects.delayWet > 0.001;
        fxp.delayWet = static_cast<float> (global.effects.delayWet);
        fxp.delayTime = global.effects.delayTimeMs / 1000.0;
        fxp.delayFeedback = static_cast<float> (global.effects.delayFeedback);
        fxp.distortionEnabled = global.effects.distortionWet > 0.001;
        fxp.distortionDrive = static_cast<float> (global.effects.distortionDrive);
        fxp.distortionInstability = static_cast<float> (
            global.effects.distortionInstability);
        fxp.distortionWet = static_cast<float> (global.effects.distortionWet);
        if (global.effects.distortionType == "bitcrush")
            fxp.distortionType = DistortionType::Bitcrush;
        else if (global.effects.distortionType == "wavefold")
            fxp.distortionType = DistortionType::Wavefold;
        else
            fxp.distortionType = DistortionType::Overdrive;
        fxp.masterVolume = static_cast<float> (global.masterVolume);
        fx.setParameters (fxp);
    }

    static void processEffects (
        juce::AudioBuffer<float>& buffer, EffectsChain& fx)
    {
        float* left = buffer.getWritePointer (0);
        float* right = buffer.getWritePointer (1);
        for (int i = 0; i < buffer.getNumSamples(); ++i)
            fx.processStereo (left[i], right[i]);
    }

    static void applyEffects (
        juce::AudioBuffer<float>& buffer, const ScoreGlobal& global, double sr)
    {
        applyWallReflection (buffer, global.effects, sr);
        EffectsChain fx;
        configureEffects (fx, global, sr);
        processEffects (buffer, fx);
    }

    static bool trimBuffer (
        juce::AudioBuffer<float>& buffer, const ScoreExport& settings)
    {
        const int totalSamples = buffer.getNumSamples();
        const double start = std::clamp (settings.startPosition, 0.0, 1.0);
        const double end = std::clamp (settings.endPosition, start, 1.0);
        const int trimStart = static_cast<int> (start * totalSamples);
        const int trimEnd = static_cast<int> (end * totalSamples);
        const int trimLength = trimEnd - trimStart;

        if (trimLength <= 0)
            return false;
        if (trimLength >= totalSamples && trimStart == 0)
            return true;

        for (int channel = 0; channel < buffer.getNumChannels(); ++channel)
            std::memmove (buffer.getWritePointer (channel),
                          buffer.getReadPointer (channel, trimStart),
                          static_cast<size_t> (trimLength) * sizeof (float));
        buffer.setSize (buffer.getNumChannels(), trimLength, true, false, true);
        return true;
    }

    static bool isValidSampleRate (double sr)
    {
        return sr == 44100.0 || sr == 48000.0 || sr == 88200.0 || sr == 96000.0;
    }
};
