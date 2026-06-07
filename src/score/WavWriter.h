#pragma once

#include <juce_audio_formats/juce_audio_formats.h>

class WavWriter
{
public:
    static bool write (const juce::File& file,
                       const juce::AudioBuffer<float>& buffer,
                       double sampleRate,
                       int bitDepth = 24,
                       bool normalize = true)
    {
        juce::AudioBuffer<float> outBuf;
        outBuf.makeCopyOf (buffer);

        if (normalize)
        {
            float peak = 0.0f;
            for (int ch = 0; ch < outBuf.getNumChannels(); ++ch)
                peak = juce::jmax (peak, outBuf.getMagnitude (ch, 0, outBuf.getNumSamples()));

            if (peak > 0.0001f)
            {
                float gain = 0.95f / peak;
                for (int ch = 0; ch < outBuf.getNumChannels(); ++ch)
                    outBuf.applyGain (ch, 0, outBuf.getNumSamples(), gain);
            }
        }

        int safeBitDepth = (bitDepth == 16 || bitDepth == 24 || bitDepth == 32)
                               ? bitDepth : 24;

        juce::TemporaryFile tempFile (file);
        auto stream = tempFile.getFile().createOutputStream();
        if (stream == nullptr) return false;

        juce::WavAudioFormat wav;
        std::unique_ptr<juce::AudioFormatWriter> writer (
            wav.createWriterFor (stream.release(), sampleRate,
                                 static_cast<unsigned int> (outBuf.getNumChannels()),
                                 safeBitDepth, {}, 0));

        if (writer == nullptr)
        {
            tempFile.deleteTemporaryFile();
            return false;
        }

        bool wrote = writer->writeFromAudioSampleBuffer (outBuf, 0, outBuf.getNumSamples());
        writer.reset();

        if (! wrote)
        {
            tempFile.deleteTemporaryFile();
            return false;
        }

        return tempFile.overwriteTargetFileWithTemporary();
    }
};
