#pragma once
#include <cmath>
#include <algorithm>

/**
 * 包絡產生器 — 兩種模式
 *   1. ADSR：傳統 Attack-Decay-Sustain-Release（FM Piano 用）
 *   2. Exponential Decay：單純指數衰減（Modal Synthesis 每個模態用）
 */
class Envelope
{
public:
    enum class State { Idle, Attack, Decay, Sustain, Release };

    // ── ADSR 參數（秒）──
    void setAttack  (float seconds) { attackTime  = std::max (0.001f, seconds); }
    void setDecay   (float seconds) { decayTime   = std::max (0.001f, seconds); }
    void setSustain (float level)   { sustainLevel = std::clamp (level, 0.0f, 1.0f); }
    void setRelease (float seconds) { releaseTime = std::max (0.001f, seconds); }

    void setSampleRate (double sr) { sampleRate = sr; }

    void noteOn()
    {
        state = State::Attack;
        currentLevel = 0.0f;
    }

    void noteOff()
    {
        if (state != State::Idle)
            state = State::Release;
    }

    bool isActive() const { return state != State::Idle; }
    State getState() const { return state; }

    float getNextSample()
    {
        float rate;

        switch (state)
        {
            case State::Idle:
                return 0.0f;

            case State::Attack:
                rate = 1.0f / (attackTime * (float) sampleRate);
                currentLevel += rate;
                if (currentLevel >= 1.0f)
                {
                    currentLevel = 1.0f;
                    state = State::Decay;
                }
                break;

            case State::Decay:
                rate = (1.0f - sustainLevel) / (decayTime * (float) sampleRate);
                currentLevel -= rate;
                if (currentLevel <= sustainLevel)
                {
                    currentLevel = sustainLevel;
                    state = State::Sustain;
                }
                break;

            case State::Sustain:
                break;

            case State::Release:
                rate = currentLevel / (releaseTime * (float) sampleRate);
                currentLevel -= rate;
                if (currentLevel <= 0.001f)
                {
                    currentLevel = 0.0f;
                    state = State::Idle;
                }
                break;
        }

        return currentLevel;
    }

    // ── Exponential Decay 模式（Modal Synthesis 用）──
    // decayTime 秒後衰減到 ~0.1% (-60dB)
    struct ExpDecay
    {
        float level      = 0.0f;
        float decayCoeff = 1.0f;  // 每 sample 的乘法因子

        void trigger (float velocity, float decayTimeSec, double sr)
        {
            level = velocity;
            // exp(-6.9/τ/sr) → 在 τ 秒後衰減到 ~0.1%
            if (decayTimeSec > 0.0f && sr > 0.0)
                decayCoeff = (float) std::exp (-6.9078 / (decayTimeSec * sr));
            else
                decayCoeff = 0.0f;
        }

        float process()
        {
            float out = level;
            level *= decayCoeff;
            return out;
        }

        bool isActive() const { return level > 0.0001f; }
    };

private:
    double sampleRate   = 44100.0;
    float attackTime    = 0.01f;
    float decayTime     = 0.1f;
    float sustainLevel  = 0.7f;
    float releaseTime   = 0.3f;
    float currentLevel  = 0.0f;
    State state         = State::Idle;
};
