#pragma once
#include <random>
#include <cmath>

/**
 * 噪音產生器 — White / Pink
 * 用途：Exciter 的瞬態噪音成分（模擬槌頭衝擊）
 */
class NoiseGen
{
public:
    enum class Type { White, Pink };

    void setType (Type t) { type = t; }

    float processSample()
    {
        float white = dist (rng);

        if (type == Type::White)
            return white;

        // Pink noise — Paul Kellet 的經典 IIR 近似
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
    Type type = Type::White;
    std::mt19937 rng { std::random_device{}() };
    std::uniform_real_distribution<float> dist { -1.0f, 1.0f };

    // Pink noise filter state
    float b0 = 0, b1 = 0, b2 = 0, b3 = 0, b4 = 0, b5 = 0, b6 = 0;
};
