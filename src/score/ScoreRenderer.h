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

    /// Dump each modal event's model-predicted partials as JSON (single source
    /// of truth for verification). Non-modal (fm) events are skipped.
    juce::String dumpModes (const Score& score)
    {
        juce::String out;
        out << "{\n  \"events\": [\n";
        bool first = true;
        for (const auto& ev : score.events)
        {
            int midiNote = noteNameToMidi (ev.note);
            std::vector<ModalResonator::Mode> modes;

            if (ev.engine == "string" || ev.engine == "cimbalom")
            {
                const Material* mat = materialDB->getMaterial (juce::String (ev.material));
                if (mat == nullptr) mat = materialDB->getMaterial ("steel");
                if (mat == nullptr) continue;
                CimbalomParams cp;
                cp.materialKey = ev.material;
                cp.strikePosition = ev.strikePosition;
                cp.diameterMm = ev.diameterMm;
                cp.tensionOverride = ev.tensionN;
                cp.dampingOverride = ev.dampingOverride;
                CimbalomVoice voice;
                voice.prepare (score.global.sampleRate);
                voice.noteOn (midiNote, ev.velocity, *mat, cp);
                modes = voice.getModes();
            }
            else if (ev.engine == "beam" || ev.engine == "tongue_drum"
                  || ev.engine == "plate" || ev.engine == "water_gong"
                  || ev.engine == "membrane" || ev.engine == "custom")
            {
                const Material* mat = materialDB->getMaterial (juce::String (ev.material));
                if (mat == nullptr) mat = materialDB->getMaterial ("steel");
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
                ChromaticVoice voice;
                voice.prepare (score.global.sampleRate);
                voice.noteOn (midiNote, ev.velocity, *mat, cp);
                modes = voice.getModes();
            }
            else
            {
                continue;   // fm = non-modal synthesis
            }

            if (! first) out << ",\n";
            first = false;
            out << "    { \"engine\": \"" << juce::String (ev.engine)
                << "\", \"note\": \"" << juce::String (ev.note)
                << "\", \"midi\": " << midiNote << ", \"partials\": [";
            for (size_t i = 0; i < modes.size(); ++i)
            {
                if (i) out << ", ";
                out << "{\"freq\": " << juce::String (modes[i].frequency, 3)
                    << ", \"amp\": " << juce::String (modes[i].amplitude, 5)
                    << ", \"decay\": " << juce::String (modes[i].decayTime, 4) << "}";
            }
            out << "] }";
        }
        out << "\n  ]\n}\n";
        return out;
    }

    bool render (const Score& score, const juce::File& outputFile)
    {
        if (materialDB == nullptr || score.events.empty())
            return false;

        double sr = score.global.sampleRate;
        if (! isValidSampleRate (sr))
            return false;

        double totalDuration = 0.0;
        for (const auto& ev : score.events)
            totalDuration = std::max (totalDuration, eventEndTime (ev));

        totalDuration += wallDelaySeconds (score.global.effects);
        totalDuration += score.exportSettings.tailSilenceMs / 1000.0;
        int totalSamples = static_cast<int> (totalDuration * sr) + 1;
        if (totalSamples <= 0)
            return false;

        juce::AudioBuffer<float> buffer (2, totalSamples);
        buffer.clear();

        for (const auto& ev : score.events)
            renderEvent (ev, buffer, sr);

        applyEffects (buffer, score.global, sr);
        if (! trimBuffer (buffer, score.exportSettings))
            return false;

        return WavWriter::write (outputFile, buffer, sr,
                                 score.exportSettings.bitDepth,
                                 score.exportSettings.normalize);
    }

    bool renderLayered (const Score& score, const juce::File& outputFile)
    {
        if (materialDB == nullptr || score.layers.empty())
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

        for (const auto& layer : score.layers)
        {
            juce::File sourceFile = baseDir.getChildFile (juce::String (layer.source));
            if (! sourceFile.existsAsFile())
                return false;

            Score subScore;
            if (! ScoreParser::parse (sourceFile, subScore))
                return false;
            if (subScore.hasLayers()
                || subScore.global.sampleRate != score.global.sampleRate)
                return false;

            double subDuration = 0.0;
            for (const auto& ev : subScore.events)
                subDuration = std::max (subDuration, eventEndTime (ev));
            subDuration += wallDelaySeconds (subScore.global.effects);
            subDuration += subScore.exportSettings.tailSilenceMs / 1000.0;

            int subTotalSamples = static_cast<int> (subDuration * sr) + 1;
            if (subTotalSamples <= 0)
                return false;

            juce::AudioBuffer<float> subBuffer (2, subTotalSamples);
            subBuffer.clear();

            for (const auto& ev : subScore.events)
                renderEvent (ev, subBuffer, sr);

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
            rl.buffer.setSize (2, regionLen);
            rl.buffer.copyFrom (0, 0, subBuffer, 0, regionStart, regionLen);
            rl.buffer.copyFrom (1, 0, subBuffer, 1, regionStart, regionLen);
            rl.buffer.applyGain (static_cast<float> (layer.gain));
            rl.numSamples = regionLen;
            renderedLayers.push_back (std::move (rl));
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

        juce::AudioBuffer<float> output (2, totalOut);
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

        const int wallSamples = static_cast<int> (
            wallDelaySeconds (score.global.effects) * sr);
        int tailSamples = static_cast<int> (score.exportSettings.tailSilenceMs / 1000.0 * sr);
        output.setSize (2, totalOut + wallSamples + tailSamples, true, true, true);
        applyEffects (output, score.global, sr);

        if (! trimBuffer (output, score.exportSettings))
            return false;

        return WavWriter::write (outputFile, output, sr,
                                 score.exportSettings.bitDepth,
                                 score.exportSettings.normalize);
    }

private:
    void renderEvent (const ScoreEvent& ev, juce::AudioBuffer<float>& buffer, double sr)
    {
        int startSample = juce::jlimit (0, buffer.getNumSamples(),
                                        static_cast<int> (std::max (0.0, ev.time) * sr));
        // Let voice ring into tail region — isActive() stops the loop naturally
        int endSample = buffer.getNumSamples();
        if (startSample >= endSample)
            return;

        int midiNote = noteNameToMidi (ev.note);
        const Material* mat = materialDB->getMaterial (juce::String (ev.material));
        if (mat == nullptr)
            mat = materialDB->getMaterial ("steel");

        if (ev.engine == "string" || ev.engine == "cimbalom")
        {
            renderCimbalom (ev, mat, midiNote, startSample, endSample, buffer, sr);
        }
        else if (ev.engine == "beam" || ev.engine == "tongue_drum")
        {
            renderChromatic (ev, mat, midiNote, ChromaticSubEngine::TongueDrum,
                             startSample, endSample, buffer, sr);
        }
        else if (ev.engine == "plate" || ev.engine == "water_gong")
        {
            renderChromatic (ev, mat, midiNote, ChromaticSubEngine::WaterGong,
                             startSample, endSample, buffer, sr);
        }
        else if (ev.engine == "fm")
        {
            renderFM (ev, midiNote, startSample, endSample, buffer, sr);
        }
        else if (ev.engine == "custom")
        {
            renderChromatic (ev, mat, midiNote, ChromaticSubEngine::CustomHarmonics,
                             startSample, endSample, buffer, sr);
        }
        else if (ev.engine == "membrane")
        {
            renderChromatic (ev, mat, midiNote, ChromaticSubEngine::WaterGong,
                             startSample, endSample, buffer, sr);
        }
    }

    void renderCimbalom (const ScoreEvent& ev, const Material* mat, int midiNote,
                          int start, int end, juce::AudioBuffer<float>& buf, double sr)
    {
        if (mat == nullptr) return;

        CimbalomParams cp;
        cp.materialKey = ev.material;
        cp.strikePosition = ev.strikePosition;
        cp.diameterMm = ev.diameterMm;
        cp.tensionOverride = ev.tensionN;
        cp.dampingOverride = ev.dampingOverride;

        if (ev.exciter == "cotton" || ev.exciter == "cotton_mallet") cp.exciter = ExciterType::Cotton;
        else if (ev.exciter == "felt" || ev.exciter == "felt_mallet") cp.exciter = ExciterType::Felt;
        else if (ev.exciter == "metal" || ev.exciter == "metal_mallet"
                 || ev.exciter == "metal_hammer") cp.exciter = ExciterType::Metal;
        else if (ev.exciter == "hard_plastic" || ev.exciter == "wood"
                 || ev.exciter == "wood_mallet") cp.exciter = ExciterType::Wood;
        else cp.exciter = ExciterType::Wood;

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
                           juce::AudioBuffer<float>& buf, double sr)
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
        cp.exciterHardness = chromaticExciterHardness (ev.exciter);

        ChromaticVoice voice;
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

    void renderFM (const ScoreEvent& ev, int midiNote,
                    int start, int end,
                    juce::AudioBuffer<float>& buf, double sr)
    {
        FMParams fp;
        fp.preset = static_cast<FMPreset> (ev.fmPreset);

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

    static float chromaticExciterHardness (const std::string& exciter)
    {
        if (exciter == "cotton" || exciter == "cotton_mallet"
            || exciter == "finger" || exciter == "finger_tap"
            || exciter == "bow")
            return 0.0f;
        if (exciter == "felt" || exciter == "felt_mallet"
            || exciter == "medium")
            return 1.0f;
        if (exciter == "metal" || exciter == "metal_mallet"
            || exciter == "metal_hammer" || exciter == "metal_tip"
            || exciter == "sharp")
            return 3.0f;
        return 2.0f;
    }

    static double eventEndTime (const ScoreEvent& ev)
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

        return end;
    }

    static double wallDelaySeconds (const ScoreEffects& effects)
    {
        return effects.wallDistanceM > 0.0
            ? (2.0 * effects.wallDistanceM / 343.0)
            : 0.0;
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
        fxp.reverbRoomSize = static_cast<float> (
            std::min (global.effects.reverbDecay / 10.0, 1.0));
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

        juce::AudioBuffer<float> trimmed (buffer.getNumChannels(), trimLength);
        for (int channel = 0; channel < buffer.getNumChannels(); ++channel)
            trimmed.copyFrom (
                channel, 0, buffer, channel, trimStart, trimLength);
        buffer = std::move (trimmed);
        return true;
    }

    static bool isValidSampleRate (double sr)
    {
        return sr == 44100.0 || sr == 48000.0 || sr == 88200.0 || sr == 96000.0;
    }
};
