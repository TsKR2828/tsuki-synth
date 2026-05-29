#pragma once

#include "ScoreParser.h"
#include "WavWriter.h"
#include "../engines/CimbalomEngine.h"
#include "../engines/ChromaticEngine.h"
#include "../engines/FMPianoEngine.h"
#include "../physics/MaterialDB.h"
#include "../dsp/EffectsChain.h"

class ScoreRenderer
{
    using Material = MaterialDB::Material;

public:
    void setMaterialDB (MaterialDB* db) { materialDB = db; }
    void setBaseDir (const juce::File& dir) { baseDir = dir; }

    bool render (const Score& score, const juce::File& outputFile)
    {
        if (materialDB == nullptr || score.events.empty())
            return false;

        double sr = score.global.sampleRate;
        double totalDuration = 0.0;
        for (const auto& ev : score.events)
            totalDuration = std::max (totalDuration, ev.time + ev.duration);

        totalDuration += score.exportSettings.tailSilenceMs / 1000.0;
        int totalSamples = static_cast<int> (totalDuration * sr) + 1;

        juce::AudioBuffer<float> buffer (2, totalSamples);
        buffer.clear();

        for (const auto& ev : score.events)
            renderEvent (ev, buffer, sr);

        EffectsChain fx;
        fx.prepare (sr);
        EffectsParams fxp;
        fxp.reverbEnabled = score.global.effects.reverbWet > 0.001;
        fxp.reverbWet = static_cast<float> (score.global.effects.reverbWet);
        fxp.reverbRoomSize = static_cast<float> (std::min (score.global.effects.reverbDecay / 10.0, 1.0));
        fxp.delayEnabled = score.global.effects.delayWet > 0.001;
        fxp.delayWet = static_cast<float> (score.global.effects.delayWet);
        fxp.delayTime = score.global.effects.delayTimeMs / 1000.0;
        fxp.delayFeedback = static_cast<float> (score.global.effects.delayFeedback);

        fxp.distortionEnabled = score.global.effects.distortionWet > 0.001;
        fxp.distortionDrive = static_cast<float> (score.global.effects.distortionDrive);
        fxp.distortionInstability = static_cast<float> (score.global.effects.distortionInstability);
        fxp.distortionWet = static_cast<float> (score.global.effects.distortionWet);
        if (score.global.effects.distortionType == "bitcrush")
            fxp.distortionType = DistortionType::Bitcrush;
        else if (score.global.effects.distortionType == "wavefold")
            fxp.distortionType = DistortionType::Wavefold;
        else
            fxp.distortionType = DistortionType::Overdrive;

        fxp.masterVolume = static_cast<float> (score.global.masterVolume);
        fx.setParameters (fxp);

        float* left  = buffer.getWritePointer (0);
        float* right = buffer.getWritePointer (1);
        for (int i = 0; i < totalSamples; ++i)
            fx.processStereo (left[i], right[i]);

        double sp = std::clamp (score.exportSettings.startPosition, 0.0, 1.0);
        double ep = std::clamp (score.exportSettings.endPosition, sp, 1.0);
        if (sp > 0.0 || ep < 1.0)
        {
            int trimStart = static_cast<int> (sp * totalSamples);
            int trimEnd   = static_cast<int> (ep * totalSamples);
            int trimLen   = trimEnd - trimStart;
            if (trimLen > 0 && trimLen < totalSamples)
            {
                juce::AudioBuffer<float> trimmed (2, trimLen);
                trimmed.copyFrom (0, 0, buffer, 0, trimStart, trimLen);
                trimmed.copyFrom (1, 0, buffer, 1, trimStart, trimLen);
                return WavWriter::write (outputFile, trimmed, sr,
                                         score.exportSettings.bitDepth,
                                         score.exportSettings.normalize);
            }
        }

        return WavWriter::write (outputFile, buffer, sr,
                                 score.exportSettings.bitDepth,
                                 score.exportSettings.normalize);
    }

    bool renderLayered (const Score& score, const juce::File& outputFile)
    {
        if (materialDB == nullptr || score.layers.empty())
            return false;

        double sr = score.global.sampleRate;
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

            double subDuration = 0.0;
            for (const auto& ev : subScore.events)
                subDuration = std::max (subDuration, ev.time + ev.duration);
            subDuration += subScore.exportSettings.tailSilenceMs / 1000.0;

            int subTotalSamples = static_cast<int> (subDuration * sr) + 1;
            juce::AudioBuffer<float> subBuffer (2, subTotalSamples);
            subBuffer.clear();

            for (const auto& ev : subScore.events)
                renderEvent (ev, subBuffer, sr);

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

        // Apply effects + master volume (same as render())
        EffectsChain fx;
        fx.prepare (sr);
        EffectsParams fxp;
        fxp.reverbEnabled = score.global.effects.reverbWet > 0.001;
        fxp.reverbWet = static_cast<float> (score.global.effects.reverbWet);
        fxp.reverbRoomSize = static_cast<float> (std::min (score.global.effects.reverbDecay / 10.0, 1.0));
        fxp.delayEnabled = score.global.effects.delayWet > 0.001;
        fxp.delayWet = static_cast<float> (score.global.effects.delayWet);
        fxp.delayTime = score.global.effects.delayTimeMs / 1000.0;
        fxp.delayFeedback = static_cast<float> (score.global.effects.delayFeedback);
        fxp.distortionEnabled = score.global.effects.distortionWet > 0.001;
        fxp.distortionDrive = static_cast<float> (score.global.effects.distortionDrive);
        fxp.distortionInstability = static_cast<float> (score.global.effects.distortionInstability);
        fxp.distortionWet = static_cast<float> (score.global.effects.distortionWet);
        if (score.global.effects.distortionType == "bitcrush")
            fxp.distortionType = DistortionType::Bitcrush;
        else if (score.global.effects.distortionType == "wavefold")
            fxp.distortionType = DistortionType::Wavefold;
        else
            fxp.distortionType = DistortionType::Overdrive;
        fxp.masterVolume = static_cast<float> (score.global.masterVolume);
        fx.setParameters (fxp);

        float* left  = output.getWritePointer (0);
        float* right = output.getWritePointer (1);
        for (int i = 0; i < totalOut; ++i)
            fx.processStereo (left[i], right[i]);

        // Append tail silence
        int tailSamples = static_cast<int> (score.exportSettings.tailSilenceMs / 1000.0 * sr);
        if (tailSamples > 0)
        {
            output.setSize (2, totalOut + tailSamples, true);
            for (int i = totalOut; i < totalOut + tailSamples; ++i)
            {
                float tl = 0.0f, tr = 0.0f;
                fx.processStereo (tl, tr);
                output.setSample (0, i, tl);
                output.setSample (1, i, tr);
            }
        }

        return WavWriter::write (outputFile, output, sr,
                                 score.exportSettings.bitDepth,
                                 score.exportSettings.normalize);
    }

private:
    void renderEvent (const ScoreEvent& ev, juce::AudioBuffer<float>& buffer, double sr)
    {
        int startSample = static_cast<int> (ev.time * sr);
        // Let voice ring into tail region — isActive() stops the loop naturally
        int endSample = buffer.getNumSamples();

        int midiNote = noteNameToMidi (ev.note);
        const Material* mat = materialDB->getMaterial (ev.material);

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

        int noteOffSample = start + static_cast<int> (ev.duration * sr * 0.9);

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

            float v = voice.getNextSample() * 0.15f;
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

        ChromaticVoice voice;
        voice.prepare (sr);
        voice.noteOn (midiNote, ev.velocity, *mat, cp);

        int noteOffSample = start + static_cast<int> (ev.duration * sr * 0.9);

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

            float v = voice.getNextSample() * 0.15f;
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

        int noteOffSample = start + static_cast<int> (ev.duration * sr * 0.9);

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

            float v = voice.getNextSample() * 0.15f;
            buf.addSample (0, i, v);
            buf.addSample (1, i, v);
        }
    }

    MaterialDB* materialDB = nullptr;
    juce::File  baseDir;
};
