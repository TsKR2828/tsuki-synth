#pragma once

#include <algorithm>
#include <atomic>
#include <cstdint>
#include <memory>
#include <stdexcept>

// Lock-free, allocation-free-after-construction SPSC sample history.
//
// The producer always publishes every incoming sample. If the consumer falls
// more than one capacity behind, the oldest samples are overwritten and the
// consumer resumes at the oldest sample that is still present. Each slot is
// atomic so an overwrite can never create a C++ data race with the GUI reader.
// This "newest data wins" policy is intentional for live analysers: displaying
// stale audio after a GUI stall is worse than dropping old history.
class AudioFIFO
{
public:
    explicit AudioFIFO (int capacityPow2 = 4096)
        : capacityValue (checkedCapacity (capacityPow2)),
          mask (capacityValue - 1),
          buffer (std::make_unique<std::atomic<float>[]> (
              static_cast<size_t> (capacityValue)))
    {
        for (int i = 0; i < capacityValue; ++i)
            buffer[static_cast<size_t> (i)].store (0.0f,
                                                   std::memory_order_relaxed);
    }

    /** Audio-thread producer. Never allocates or waits. */
    void push (const float* data, int numSamples) noexcept
    {
        if (data == nullptr || numSamples <= 0)
            return;

        const auto w = writePos.load (std::memory_order_relaxed);
        // A single oversized block can only leave its final capacity samples
        // readable, but sequence positions still advance by the full block.
        const int first = std::max (0, numSamples - capacityValue);
        for (int i = first; i < numSamples; ++i)
            buffer[static_cast<size_t> ((w + static_cast<uint64_t> (i))
                                        & static_cast<uint64_t> (mask))]
                .store (data[i], std::memory_order_relaxed);

        writePos.store (w + static_cast<uint64_t> (numSamples),
                        std::memory_order_release);
    }

    /** Pull unread samples in chronological order, skipping overwritten data. */
    int pull (float* dest, int maxSamples) noexcept
    {
        if (dest == nullptr || maxSamples <= 0)
            return 0;

        const auto w = writePos.load (std::memory_order_acquire);
        const auto requested = readPos.load (std::memory_order_relaxed);
        const auto oldest = w > static_cast<uint64_t> (capacityValue)
                                ? w - static_cast<uint64_t> (capacityValue)
                                : 0;
        const auto start = std::max (requested, oldest);
        const int n = static_cast<int> (std::min<uint64_t> (
            w - start, static_cast<uint64_t> (maxSamples)));

        copyFromSequence (dest, start, n);
        readPos.store (start + static_cast<uint64_t> (n),
                       std::memory_order_release);
        return n;
    }

    /**
     * Return at most maxSamples of the newest unread history and discard all
     * older unread samples. This is the preferred live-analyser operation.
     */
    int pullLatest (float* dest, int maxSamples) noexcept
    {
        if (dest == nullptr || maxSamples <= 0)
            return 0;

        const auto w = writePos.load (std::memory_order_acquire);
        const auto requested = readPos.load (std::memory_order_relaxed);
        const auto oldest = w > static_cast<uint64_t> (capacityValue)
                                ? w - static_cast<uint64_t> (capacityValue)
                                : 0;
        const auto unreadStart = std::max (requested, oldest);
        const auto available = w - unreadStart;
        const int n = static_cast<int> (std::min<uint64_t> (
            available, static_cast<uint64_t> (maxSamples)));
        const auto start = w - static_cast<uint64_t> (n);

        copyFromSequence (dest, start, n);
        // Consume the snapshot. New samples published after w remain unread.
        readPos.store (w, std::memory_order_release);
        return n;
    }

    int getAvailable() const noexcept
    {
        const auto w = writePos.load (std::memory_order_acquire);
        const auto r = readPos.load (std::memory_order_relaxed);
        return static_cast<int> (std::min<uint64_t> (
            w - std::min (r, w), static_cast<uint64_t> (capacityValue)));
    }

    int capacity() const noexcept { return capacityValue; }

    /** Discard queued audio without rewinding producer sequence numbers. */
    void clear() noexcept
    {
        readPos.store (writePos.load (std::memory_order_acquire),
                       std::memory_order_release);
    }

    // Backwards-compatible name. A live reset is a discard, not a counter
    // rewind, because the producer may be running concurrently.
    void reset() noexcept { clear(); }

private:
    static int checkedCapacity (int value)
    {
        if (value <= 0 || (value & (value - 1)) != 0)
            throw std::invalid_argument (
                "AudioFIFO capacity must be a positive power of two");
        return value;
    }

    void copyFromSequence (float* dest, uint64_t start, int n) const noexcept
    {
        for (int i = 0; i < n; ++i)
            dest[i] = buffer[static_cast<size_t> (
                (start + static_cast<uint64_t> (i))
                & static_cast<uint64_t> (mask))]
                .load (std::memory_order_relaxed);
    }

    const int capacityValue;
    const int mask;
    std::unique_ptr<std::atomic<float>[]> buffer;
    std::atomic<uint64_t> writePos { 0 };
    std::atomic<uint64_t> readPos  { 0 };
};
