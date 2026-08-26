#pragma once

#include <array>
#include <cstdint>
#include <limits>

/**
 * Allocation-free MIDI key/sustain state used by the tuner target display.
 * Channels are zero-based [0, 15]. Retriggers are reference-counted and the
 * selected note is the most recently struck note that is still held or held by
 * sustain.
 */
class MidiNoteTracker
{
public:
    void noteOn (int channel, int note) noexcept
    {
        if (! valid (channel, note))
            return;

        auto& state = notes[index (channel, note)];
        if (state.heldCount < std::numeric_limits<uint16_t>::max())
            ++state.heldCount;
        state.sustained = false;
        state.order = nextOrder();
    }

    void noteOff (int channel, int note) noexcept
    {
        if (! valid (channel, note))
            return;

        auto& state = notes[index (channel, note)];
        if (state.heldCount > 0)
            --state.heldCount;

        if (state.heldCount == 0)
            state.sustained = sustain[static_cast<size_t> (channel)]
                              && state.order != 0;
    }

    void sustainPedal (int channel, bool down) noexcept
    {
        if (channel < 0 || channel >= channelCount)
            return;

        const auto c = static_cast<size_t> (channel);
        if (sustain[c] == down)
            return;

        sustain[c] = down;
        if (! down)
            releaseUnheldSustained (channel);
    }

    /** MIDI CC123: release all keys on one channel, respecting sustain. */
    void allNotesOff (int channel) noexcept
    {
        if (channel < 0 || channel >= channelCount)
            return;

        for (int note = 0; note < noteCount; ++note)
        {
            auto& state = notes[index (channel, note)];
            state.heldCount = 0;
            state.sustained = sustain[static_cast<size_t> (channel)]
                              && state.order != 0;
        }
    }

    /** MIDI CC120: sound must stop immediately, regardless of sustain. */
    void allSoundOff (int channel) noexcept
    {
        if (channel < 0 || channel >= channelCount)
            return;

        for (int note = 0; note < noteCount; ++note)
            notes[index (channel, note)] = {};
    }

    /** MIDI CC121: reset sustain and release notes that are no longer held. */
    void resetControllers (int channel) noexcept
    {
        if (channel < 0 || channel >= channelCount)
            return;
        sustain[static_cast<size_t> (channel)] = false;
        releaseUnheldSustained (channel);
    }

    void clear() noexcept
    {
        notes.fill ({});
        sustain.fill (false);
        sequence = 0;
    }

    int selectedNote() const noexcept
    {
        uint64_t newest = 0;
        int selected = -1;
        for (int channel = 0; channel < channelCount; ++channel)
        {
            for (int note = 0; note < noteCount; ++note)
            {
                const auto& state = notes[index (channel, note)];
                if ((state.heldCount > 0 || state.sustained)
                    && state.order >= newest)
                {
                    newest = state.order;
                    selected = note;
                }
            }
        }
        return selected;
    }

    bool isActive (int channel, int note) const noexcept
    {
        if (! valid (channel, note))
            return false;
        const auto& state = notes[index (channel, note)];
        return state.heldCount > 0 || state.sustained;
    }

private:
    static constexpr int channelCount = 16;
    static constexpr int noteCount = 128;

    struct NoteState
    {
        uint16_t heldCount = 0;
        bool sustained = false;
        uint64_t order = 0;
    };

    static constexpr bool valid (int channel, int note) noexcept
    {
        return channel >= 0 && channel < channelCount
            && note >= 0 && note < noteCount;
    }

    static constexpr size_t index (int channel, int note) noexcept
    {
        return static_cast<size_t> (channel * noteCount + note);
    }

    uint64_t nextOrder() noexcept
    {
        ++sequence;
        if (sequence == 0) // practically unreachable, but preserve ordering
        {
            uint64_t order = 1;
            for (auto& state : notes)
                if (state.heldCount > 0 || state.sustained)
                    state.order = order++;
            sequence = order;
        }
        return sequence;
    }

    void releaseUnheldSustained (int channel) noexcept
    {
        for (int note = 0; note < noteCount; ++note)
        {
            auto& state = notes[index (channel, note)];
            if (state.heldCount == 0)
            {
                state.sustained = false;
                state.order = 0;
            }
        }
    }

    std::array<NoteState, channelCount * noteCount> notes {};
    std::array<bool, channelCount> sustain {};
    uint64_t sequence = 0;
};
