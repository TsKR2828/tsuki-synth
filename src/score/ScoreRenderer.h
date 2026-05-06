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
public:
    void setMaterialDB (MaterialDB* db) { materialDB = db; }

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
        fxp.masterVolume = static_cast<float> (score.global.masterVolume);
        fx.setParameters (fxp);

        float* left  = buffer.getWritePointer (0);
        float* right = buffer.getWritePointer (1);
        for (int i = 0; i < totalSamples; ++i)
            fx.processStereo (left[i], right[i]);

        return WavWriter::write (outputFile, buffer, sr,
                                 score.exportSettings.bitDepth,
                                 score.exportSettings.normalize);
    }

private:
    void renderEvent (const ScoreEvent& ev, juce::AudioBuffer<float>& buffer, double sr)
    {
        int startSample = static_cast<int> (ev.time * sr);
        int durationSamples = static_cast<int> (ev.duration * sr);
        int endSample = std::min (startSample + durationSamples, buffer.getNumSamples());

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
            auto sub = (ev.engine == "water_gong") ? ChromaticSubEngine::WaterGong
                                                   : ChromaticSubEngine::TongueDrum;
            if (ev.engine == "plate") sub = ChromaticSubEngine::TongueDrum;
            renderChromatic (ev, mat, midiNote, sub, startSample, endSample, buffer, sr);
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
    }

    void renderCimbalom (const ScoreEvent& ev, const Material* mat, int midiNote,
                          int start, int end, juce::AudioBuffer<float>& buf, double sr)
    {
        if (mat == nullptr) return;

        CimbalomParams cp;
        cp.materialKey = ev.material;
        cp.strikePosition = ev.strikePosition;

        if (ev.exciter == "cotton") cp.exciter = ExciterType::Cotton;
        else if (ev.exciter == "felt") cp.exciter = ExciterType::Felt;
        else if (ev.exciter == "metal" || ev.exciter == "metal_mallet") cp.exciter = ExciterType::Metal;
        else cp.exciter = ExciterType::Wood;

        CimbalomVoice voice;
        voice.prepare (sr);
        voice.noteOn (midiNote, ev.velocity, *mat, cp);

        int noteOffSample = start + static_cast<int> (ev.duration * sr * 0.9);

        for (int i = start; i < end && voice.isActive(); ++i)
        {
            if (i == noteOffSample) voice.noteOff();
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

        for (int i = start; i < end && voice.isActive(); ++i)
        {
            if (i == noteOffSample) voice.noteOff();
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

        FMVoice voice;
        voice.prepare (sr);
        voice.noteOn (midiNote, ev.velocity, fp);

        int noteOffSample = start + static_cast<int> (ev.duration * sr * 0.9);

        for (int i = start; i < end && voice.isActive(); ++i)
        {
            if (i == noteOffSample) voice.noteOff();
            float v = voice.getNextSample() * 0.15f;
            buf.addSample (0, i, v);
            buf.addSample (1, i, v);
        }
    }

    MaterialDB* materialDB = nullptr;
};
