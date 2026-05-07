#pragma once
#include <vector>
#include <cmath>

/**
 * 延遲線 — 環狀緩衝 + 線性插值 + feedback
 * 用途：Delay 效果、Wall Reflection、Karplus-Strong
 */
class DelayLine
{
public:
    void prepare (double sr, float maxDelaySec = 2.0f)
    {
        sampleRate = sr;
        int maxSamples = (int) (maxDelaySec * sr) + 1;
        buffer.assign ((size_t) maxSamples, 0.0f);
        writePos = 0;
    }

    void setDelay (float delaySec)
    {
        delaySamples = (float) (delaySec * sampleRate);
        if (delaySamples >= (float) buffer.size())
            delaySamples = (float) buffer.size() - 1.0f;
        if (delaySamples < 0.0f)
            delaySamples = 0.0f;
    }

    void setFeedback (float fb) { feedback = std::clamp (fb, 0.0f, 0.95f); }
    void setWetDry   (float w)  { wet = std::clamp (w, 0.0f, 1.0f); }

    void reset()
    {
        std::fill (buffer.begin(), buffer.end(), 0.0f);
        writePos = 0;
    }

    float processSample (float input)
    {
        float delayed = readSample();
        float toWrite = input + delayed * feedback;

        buffer[(size_t) writePos] = toWrite;
        writePos = (writePos + 1) % (int) buffer.size();

        return input * (1.0f - wet) + delayed * wet;
    }

    // 直接讀寫（給 Karplus-Strong 等演算法用）
    void  pushSample (float s) { buffer[(size_t) writePos] = s; writePos = (writePos + 1) % (int) buffer.size(); }
    float popSample() const    { return readSample(); }

private:
    float readSample() const
    {
        float readPos = (float) writePos - delaySamples;
        if (readPos < 0.0f)
            readPos += (float) buffer.size();

        int   idx0 = (int) readPos;
        int   idx1 = (idx0 + 1) % (int) buffer.size();
        float frac = readPos - (float) idx0;

        return buffer[(size_t) idx0] * (1.0f - frac) + buffer[(size_t) idx1] * frac;
    }

    double sampleRate    = 44100.0;
    std::vector<float> buffer;
    int   writePos       = 0;
    float delaySamples   = 0.0f;
    float feedback       = 0.0f;
    float wet            = 0.5f;
};
