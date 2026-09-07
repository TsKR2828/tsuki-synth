#pragma once

#include <juce_audio_formats/juce_audio_formats.h>

class StandaloneRecorder
{
public:
    StandaloneRecorder()
        : writerThread ("TsukiSynth Recorder")
    {
    }

    ~StandaloneRecorder()
    {
        stop();
        writerThread.stopThread (1000);
    }

    void prepare (double newSampleRate)
    {
        sampleRate = newSampleRate;
    }

    bool start()
    {
        if (isRecording())
            return true;

        if (sampleRate <= 0.0)
        {
            setError ("Recorder unavailable");
            return false;
        }

        auto directory = getRecordingsDirectory();
        if (! directory.createDirectory())
        {
            setError ("Could not create recordings folder");
            return false;
        }

        auto destination = directory.getChildFile (
            "TsukiSynth_" + juce::Time::getCurrentTime().formatted ("%Y%m%d_%H%M%S") + ".wav");

        if (destination.existsAsFile())
            destination = destination.getNonexistentSibling();

        destination.deleteFile();
        std::unique_ptr<juce::OutputStream> stream (destination.createOutputStream().release());
        if (stream == nullptr)
        {
            setError ("Could not create WAV file");
            return false;
        }

        juce::WavAudioFormat wavFormat;
        auto writer = wavFormat.createWriterFor (
            stream,
            juce::AudioFormatWriter::Options()
                .withSampleRate (sampleRate)
                .withNumChannels (2)
                .withBitsPerSample (24));

        if (writer == nullptr)
        {
            setError ("Could not start WAV writer");
            return false;
        }

        writerThread.startThread();

        auto newThreadedWriter = std::make_unique<juce::AudioFormatWriter::ThreadedWriter> (
            writer.release(), writerThread, 32768);

        {
            const juce::ScopedLock sl (writerLock);
            threadedWriter = std::move (newThreadedWriter);
            activeWriter = threadedWriter.get();
        }

        {
            const juce::ScopedLock sl (stateLock);
            activeFile = destination;
            lastSavedFile = {};
            lastError.clear();
        }

        droppedBlocks.store (0);
        recording.store (true);
        return true;
    }

    juce::File stop()
    {
        if (! isRecording())
            return getLastSavedFile();

        juce::File savedFile;

        {
            const juce::ScopedLock sl (stateLock);
            savedFile = activeFile;
        }

        {
            const juce::ScopedLock sl (writerLock);
            activeWriter = nullptr;
        }

        threadedWriter.reset();
        writerThread.stopThread (1000);
        recording.store (false);

        {
            const juce::ScopedLock sl (stateLock);
            lastSavedFile = savedFile;
            activeFile = {};
        }

        return savedFile;
    }

    void recordBlock (const juce::AudioBuffer<float>& buffer)
    {
        if (! recording.load())
            return;

        const auto numSamples = buffer.getNumSamples();
        if (numSamples <= 0 || buffer.getNumChannels() <= 0)
            return;

        const float* channels[] {
            buffer.getReadPointer (0),
            buffer.getReadPointer (buffer.getNumChannels() > 1 ? 1 : 0)
        };

        const juce::ScopedLock sl (writerLock);
        if (activeWriter != nullptr && ! activeWriter->write (channels, numSamples))
            ++droppedBlocks;
    }

    bool isRecording() const
    {
        return recording.load();
    }

    juce::String getStatusText() const
    {
        if (isRecording())
            return "Recording...";

        const juce::ScopedLock sl (stateLock);

        if (lastError.isNotEmpty())
            return lastError;

        if (lastSavedFile.existsAsFile())
            return "Saved: " + lastSavedFile.getFileName();

        return {};
    }

    juce::File getLastSavedFile() const
    {
        const juce::ScopedLock sl (stateLock);
        return lastSavedFile;
    }

    int getDroppedBlockCount() const
    {
        return droppedBlocks.load();
    }

    static juce::File getRecordingsDirectory()
    {
        return juce::File::getSpecialLocation (juce::File::userDocumentsDirectory)
            .getChildFile ("TsukiSynth")
            .getChildFile ("Recordings");
    }

private:
    void setError (const juce::String& message)
    {
        const juce::ScopedLock sl (stateLock);
        lastError = message;
    }

    juce::TimeSliceThread writerThread;
    juce::CriticalSection writerLock;
    juce::CriticalSection stateLock;
    std::unique_ptr<juce::AudioFormatWriter::ThreadedWriter> threadedWriter;
    juce::AudioFormatWriter::ThreadedWriter* activeWriter = nullptr;
    juce::File activeFile;
    juce::File lastSavedFile;
    juce::String lastError;
    std::atomic<bool> recording { false };
    std::atomic<int> droppedBlocks { 0 };
    double sampleRate = 0.0;
};
