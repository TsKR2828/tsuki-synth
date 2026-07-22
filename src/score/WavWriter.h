#pragma once

#include <juce_audio_formats/juce_audio_formats.h>
#include <cmath>
#include <cstdint>

class WavWriter
{
public:
    struct Report
    {
        float preNormalizePeak = 0.0f;
        float appliedGain = 1.0f;
        int64_t samplesAtOrAboveFullScale = 0;
    };

    static bool write (const juce::File& file,
                       juce::AudioBuffer<float>& buffer,
                       double sampleRate,
                       int bitDepth = 24,
                       bool normalize = true,
                       Report* report = nullptr)
    {
        Report measured;
        for (int ch = 0; ch < buffer.getNumChannels(); ++ch)
        {
            measured.preNormalizePeak = juce::jmax (
                measured.preNormalizePeak,
                buffer.getMagnitude (ch, 0, buffer.getNumSamples()));
            const float* samples = buffer.getReadPointer (ch);
            for (int i = 0; i < buffer.getNumSamples(); ++i)
                if (std::abs (samples[i]) >= 1.0f)
                    ++measured.samplesAtOrAboveFullScale;
        }

        if (normalize)
        {
            if (measured.preNormalizePeak > 0.0001f)
            {
                measured.appliedGain = 0.95f / measured.preNormalizePeak;
                for (int ch = 0; ch < buffer.getNumChannels(); ++ch)
                    buffer.applyGain (ch, 0, buffer.getNumSamples(), measured.appliedGain);
            }
        }
        if (report != nullptr) *report = measured;

        const bool writeFlac = file.hasFileExtension ("flac");
        int safeBitDepth = writeFlac
            ? ((bitDepth == 16 || bitDepth == 24) ? bitDepth : 24)
            : ((bitDepth == 16 || bitDepth == 24 || bitDepth == 32)
                ? bitDepth : 24);

        juce::TemporaryFile tempFile (file);
        std::unique_ptr<juce::OutputStream> stream (
            tempFile.getFile().createOutputStream());
        if (stream == nullptr) return false;

        std::unique_ptr<juce::AudioFormat> format;
        if (writeFlac)
            format = std::make_unique<juce::FlacAudioFormat>();
        else
            format = std::make_unique<juce::WavAudioFormat>();

        const auto options = juce::AudioFormatWriterOptions()
            .withSampleRate (sampleRate)
            .withNumChannels (buffer.getNumChannels())
            .withBitsPerSample (safeBitDepth)
            .withQualityOptionIndex (writeFlac ? 5 : 0);
        auto writer = format->createWriterFor (stream, options);

        if (writer == nullptr)
        {
            tempFile.deleteTemporaryFile();
            return false;
        }

        bool wrote = writer->writeFromAudioSampleBuffer (buffer, 0, buffer.getNumSamples());
        writer.reset();

        if (! wrote)
        {
            tempFile.deleteTemporaryFile();
            return false;
        }

        return tempFile.overwriteTargetFileWithTemporary();
    }
};
