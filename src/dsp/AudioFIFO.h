#pragma once
#include <atomic>
#include <cstdint>
#include <vector>
#include <algorithm>

// Lock-free SPSC ring buffer for audio thread → GUI data transfer.
// Capacity must be a power of two.
// Producer (processBlock) calls push(). Consumer (GUI timer) calls pull().
// If producer laps the consumer, oldest unread data is silently dropped.
class AudioFIFO
{
public:
    explicit AudioFIFO (int capacityPow2 = 4096)
        : buffer (static_cast<size_t> (capacityPow2), 0.0f),
          mask (capacityPow2 - 1)
    {
    }

    void push (const float* data, int numSamples)
    {
        auto w = writePos.load (std::memory_order_relaxed);
        for (int i = 0; i < numSamples; ++i)
            buffer[static_cast<size_t> ((w + (uint64_t) i) & (uint64_t) mask)] = data[i];
        writePos.store (w + (uint64_t) numSamples, std::memory_order_release);
    }

    int pull (float* dest, int maxSamples)
    {
        auto w = writePos.load (std::memory_order_acquire);
        auto r = readPos.load (std::memory_order_relaxed);
        uint64_t available = w - r;
        const auto cap = static_cast<uint64_t> (capacity());

        if (available > cap)
        {
            r = w - cap;
            available = cap;
        }

        int n = std::min ((int) available, maxSamples);
        for (int i = 0; i < n; ++i)
            dest[i] = buffer[static_cast<size_t> ((r + (uint64_t) i) & (uint64_t) mask)];
        readPos.store (r + (uint64_t) n, std::memory_order_release);
        return n;
    }

    int getAvailable() const
    {
        auto a = writePos.load (std::memory_order_acquire)
               - readPos.load (std::memory_order_relaxed);
        return static_cast<int> (std::min (a, static_cast<uint64_t> (capacity())));
    }

    int capacity() const { return mask + 1; }

    void reset()
    {
        writePos.store (0, std::memory_order_relaxed);
        readPos.store  (0, std::memory_order_relaxed);
    }

private:
    std::vector<float> buffer;
    int mask;
    std::atomic<uint64_t> writePos { 0 };
    std::atomic<uint64_t> readPos  { 0 };
};
