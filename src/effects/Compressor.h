#pragma once
#include <cmath>
#include <algorithm>

/**
 * Simple stereo peak compressor
 *
 * Linked stereo detection (max of L/R) to prevent image shift.
 * Fixed attack (5ms) and release (100ms) for simplicity.
 * Auto makeup gain based on threshold and ratio.
 */
class Compressor
{
public:
    void prepare (double sr)
    {
        sampleRate = sr;
        attackCoeff  = (float) std::exp (-1.0 / (0.005 * sr));   // 5 ms
        releaseCoeff = (float) std::exp (-1.0 / (0.100 * sr));   // 100 ms
        envFollower  = 0.0f;
    }

    void setThreshold (float dB) { thresholdDB = std::clamp (dB, -60.0f, 0.0f); }
    void setRatio     (float r)  { ratio       = std::clamp (r,   1.0f, 20.0f); }

    void reset() { envFollower = 0.0f; }

    void processStereo (float& left, float& right)
    {
        if (ratio <= 1.01f)
            return;  // bypass if ratio ~1

        // Linked peak detection
        float peak = std::max (std::abs (left), std::abs (right));

        // Envelope follower
        if (peak > envFollower)
            envFollower = attackCoeff * envFollower + (1.0f - attackCoeff) * peak;
        else
            envFollower = releaseCoeff * envFollower + (1.0f - releaseCoeff) * peak;

        // Convert to dB
        float envDB = 20.0f * std::log10 (envFollower + 1e-10f);

        // Gain computation
        float gainDB = 0.0f;
        if (envDB > thresholdDB)
            gainDB = (thresholdDB + (envDB - thresholdDB) / ratio) - envDB;

        // Auto makeup gain (compensate for average reduction)
        float makeupDB = -(thresholdDB * (1.0f - 1.0f / ratio)) * 0.5f;

        float totalGain = std::pow (10.0f, (gainDB + makeupDB) / 20.0f);

        left  *= totalGain;
        right *= totalGain;
    }

private:
    double sampleRate   = 44100.0;
    float thresholdDB   = -12.0f;
    float ratio         = 4.0f;
    float envFollower   = 0.0f;
    float attackCoeff   = 0.0f;
    float releaseCoeff  = 0.0f;
};
