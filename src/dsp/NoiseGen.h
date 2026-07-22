#pragma once
#include <cmath>
#include <cstdint>

/**
 * 噪音產生器 — White / Pink
 * 用途：Exciter 的瞬態噪音成分（模擬槌頭衝擊）
 */
class NoiseGen
{
public:
    enum class Type { White, Pink };

    void setType (Type t) { type = t; }

    /** Reseed the white-noise RNG for deterministic, reproducible output.
     *
     *  PCG32 and the integer-to-float mapping below are specified here rather
     *  than delegated to std::uniform_real_distribution, whose sequence is not
     *  portable across standard-library implementations. */
    void setSeed (uint64_t seed)
    {
        state = 0u;
        nextUInt();
        state += seed;
        nextUInt();
    }

    /** Stable mixer for a score seed, event index and note metadata. */
    static uint64_t mixSeed (uint64_t scoreSeed, uint64_t eventIndex,
                             uint32_t midiNote, uint32_t velocityCode) noexcept
    {
        uint64_t x = scoreSeed ^ (eventIndex + 0x9E3779B97F4A7C15ull);
        x ^= (uint64_t) midiNote << 32;
        x ^= velocityCode;
        x += 0x9E3779B97F4A7C15ull;
        x = (x ^ (x >> 30)) * 0xBF58476D1CE4E5B9ull;
        x = (x ^ (x >> 27)) * 0x94D049BB133111EBull;
        return x ^ (x >> 31);
    }

    float processSample()
    {
        // Use the upper 24 bits so every integer is represented exactly by a
        // float.  The result is the portable half-open interval [-1, 1).
        const float unit = (float) (nextUInt() >> 8) * (1.0f / 16777216.0f);
        float white = unit * 2.0f - 1.0f;

        if (type == Type::White)
            return white;

        // Pink noise — Paul Kellet 的經典 IIR 近似
        //
        // SAMPLE-RATE DEPENDENCE: these filter coefficients are Paul
        // Kellett's published values designed for fs = 44.1 kHz (the
        // classic music-dsp.org "refined" pink filter). The class has no
        // sample-rate input, so at other rates the pole/zero frequencies
        // shift proportionally and the -3 dB/oct approximation band edges
        // move (e.g. at 96 kHz everything sits ~2.2x higher; the spectral
        // SLOPE stays ~-3 dB/oct over the design band, but the band's
        // placement and the total RMS change slightly). Current impact is
        // effectively zero: every engine sets Type::White (see
        // setupExciter() in CimbalomEngine.h / ChromaticEngine.h), so the
        // Pink branch is dormant. If Pink is ever enabled at a non-44.1k
        // rate, either accept the shifted approximation band or add a
        // sample-rate-aware redesign -- do so consciously, not by accident.
        b0 = 0.99886f * b0 + white * 0.0555179f;
        b1 = 0.99332f * b1 + white * 0.0750759f;
        b2 = 0.96900f * b2 + white * 0.1538520f;
        b3 = 0.86650f * b3 + white * 0.3104856f;
        b4 = 0.55000f * b4 + white * 0.5329522f;
        b5 = -0.7616f * b5 - white * 0.0168980f;
        float pink = (b0 + b1 + b2 + b3 + b4 + b5 + b6 + white * 0.5362f) * 0.11f;
        b6 = white * 0.115926f;

        return pink;
    }

    void reset()
    {
        b0 = b1 = b2 = b3 = b4 = b5 = b6 = 0.0f;
    }

private:
    uint32_t nextUInt() noexcept
    {
        const uint64_t oldState = state;
        state = oldState * 6364136223846793005ull + stream;
        const uint32_t xorshifted = (uint32_t) (((oldState >> 18u) ^ oldState) >> 27u);
        const uint32_t rot = (uint32_t) (oldState >> 59u);
        return (xorshifted >> rot) | (xorshifted << ((0u - rot) & 31u));
    }

    Type type = Type::White;
    uint64_t state = 0x853C49E6748FEA9Bull;
    static constexpr uint64_t stream = 0xDA3E39CB94B95BDBull;

    // Pink noise filter state
    float b0 = 0, b1 = 0, b2 = 0, b3 = 0, b4 = 0, b5 = 0, b6 = 0;
};
