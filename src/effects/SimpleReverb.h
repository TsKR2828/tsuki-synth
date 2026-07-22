#pragma once
#include <vector>
#include <cmath>
#include <algorithm>

/**
 * Freeverb-style reverb (Schroeder-Moorer)
 *
 * Architecture:
 *   Input → 8 parallel comb filters (LP in feedback) → 4 serial allpass → Output
 *   Stereo spread via offset delay lengths between L/R channels.
 *
 * Based on Jezar's Freeverb with original tuning constants.
 */
class SimpleReverb
{
public:
    void prepare (double sr)
    {
        sampleRate = sr;
        float scale = (float) (sr / 44100.0);

        for (int i = 0; i < numCombs; ++i)
        {
            int lenL = std::max (1, (int) (combTunings[i] * scale));
            int lenR = std::max (1, (int) ((combTunings[i] + stereoSpread) * scale));
            combBufL[i].assign ((size_t) lenL, 0.0f);
            combBufR[i].assign ((size_t) lenR, 0.0f);
            combPosL[i] = 0;
            combPosR[i] = 0;
            combFilterL[i] = 0.0f;
            combFilterR[i] = 0.0f;
        }

        for (int i = 0; i < numAllpass; ++i)
        {
            int lenL = std::max (1, (int) (allpassTunings[i] * scale));
            int lenR = std::max (1, (int) ((allpassTunings[i] + stereoSpread) * scale));
            allpassBufL[i].assign ((size_t) lenL, 0.0f);
            allpassBufR[i].assign ((size_t) lenR, 0.0f);
            allpassPosL[i] = 0;
            allpassPosR[i] = 0;
        }
    }

    void setRoomSize (float size)
    {
        roomSize = std::clamp (size, 0.0f, 1.0f);
        decayTimeSeconds = -1.0f;
    }
    /// Set a measurable T60 for offline/score rendering. A value of zero keeps
    /// the first delayed response but removes recirculating comb feedback.
    void setDecayTime (float seconds)
    {
        decayTimeSeconds = std::max (0.0f, seconds);
    }
    void setDamping  (float damp) { damping  = std::clamp (damp, 0.0f, 1.0f); }
    void setMix      (float m)    { mix      = std::clamp (m,    0.0f, 1.0f); }

    void reset()
    {
        for (int i = 0; i < numCombs; ++i)
        {
            std::fill (combBufL[i].begin(), combBufL[i].end(), 0.0f);
            std::fill (combBufR[i].begin(), combBufR[i].end(), 0.0f);
            combFilterL[i] = 0.0f;
            combFilterR[i] = 0.0f;
        }
        for (int i = 0; i < numAllpass; ++i)
        {
            std::fill (allpassBufL[i].begin(), allpassBufL[i].end(), 0.0f);
            std::fill (allpassBufR[i].begin(), allpassBufR[i].end(), 0.0f);
        }
    }

    void processStereo (float& left, float& right)
    {
        float inL = left;
        float inR = right;

        const float roomFeedback = roomSize * 0.28f + 0.7f;
        const auto feedbackForLength = [this, roomFeedback] (size_t samples)
        {
            if (decayTimeSeconds < 0.0f)
                return roomFeedback;
            if (decayTimeSeconds == 0.0f)
                return 0.0f;

            // Every comb, including the stereo-spread right channel, reaches
            // -60 dB after the authored T60.  A single shared feedback value
            // made T60 proportional to each comb length and therefore gave
            // eight different decay times (and a left/right mismatch).
            const double delaySeconds = (double) samples / sampleRate;
            return std::clamp ((float) std::pow (
                0.001, delaySeconds / (double) decayTimeSeconds),
                0.0f, 0.9995f);
        };
        float damp1 = damping * 0.4f;
        float damp2 = 1.0f - damp1;

        float outL = 0.0f;
        float outR = 0.0f;

        // Parallel comb filters
        for (int i = 0; i < numCombs; ++i)
        {
            // Left channel
            {
                auto& buf = combBufL[i];
                int& pos = combPosL[i];
                float output = buf[(size_t) pos];
                combFilterL[i] = output * damp2 + combFilterL[i] * damp1;
                buf[(size_t) pos] = inL + combFilterL[i]
                    * feedbackForLength (buf.size());
                pos = (pos + 1) % (int) buf.size();
                outL += output;
            }
            // Right channel
            {
                auto& buf = combBufR[i];
                int& pos = combPosR[i];
                float output = buf[(size_t) pos];
                combFilterR[i] = output * damp2 + combFilterR[i] * damp1;
                buf[(size_t) pos] = inR + combFilterR[i]
                    * feedbackForLength (buf.size());
                pos = (pos + 1) % (int) buf.size();
                outR += output;
            }
        }

        // Serial allpass filters
        for (int i = 0; i < numAllpass; ++i)
        {
            // Left
            {
                auto& buf = allpassBufL[i];
                int& pos = allpassPosL[i];
                float bufOut = buf[(size_t) pos];
                buf[(size_t) pos] = outL + bufOut * allpassFeedback;
                pos = (pos + 1) % (int) buf.size();
                outL = bufOut - outL;
            }
            // Right
            {
                auto& buf = allpassBufR[i];
                int& pos = allpassPosR[i];
                float bufOut = buf[(size_t) pos];
                buf[(size_t) pos] = outR + bufOut * allpassFeedback;
                pos = (pos + 1) % (int) buf.size();
                outR = bufOut - outR;
            }
        }

        float dry = 1.0f - mix;
        left  = inL * dry + outL * mix * 0.15f;
        right = inR * dry + outR * mix * 0.15f;
    }

private:
    static constexpr int numCombs   = 8;
    static constexpr int numAllpass = 4;
    static constexpr int stereoSpread = 23;
    static constexpr float allpassFeedback = 0.5f;

    // Freeverb comb tunings (samples at 44100 Hz)
    static constexpr int combTunings[8]    = { 1116, 1188, 1277, 1356, 1422, 1491, 1557, 1617 };
    static constexpr int allpassTunings[4] = { 556, 441, 341, 225 };

    // Comb filter state
    std::vector<float> combBufL[8], combBufR[8];
    int   combPosL[8] = {};
    int   combPosR[8] = {};
    float combFilterL[8] = {};
    float combFilterR[8] = {};

    // Allpass filter state
    std::vector<float> allpassBufL[4], allpassBufR[4];
    int allpassPosL[4] = {};
    int allpassPosR[4] = {};

    // Parameters
    float roomSize = 0.5f;
    float decayTimeSeconds = -1.0f;
    float damping  = 0.5f;
    float mix      = 0.3f;

    double sampleRate = 44100.0;
};
