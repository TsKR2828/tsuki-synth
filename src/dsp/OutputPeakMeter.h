#pragma once
#include <juce_audio_basics/juce_audio_basics.h>
#include <atomic>
#include <cmath>
#include <limits>

/**
 * WF1002-C1（月月 2026-10-02 裁決 Q05=C）：外掛最後輸出的峰值記錄，給 editor
 * 的削波指示燈用。只「讀」輸出 buffer，從不寫回——聲音不變（輸出端仍然沒有
 * limiter / soft clip，見 docs/uiux/UI_FUNCTIONAL_SPEC.zh-TW.md §4.14）。
 *
 * 執行緒契約：
 *  - pushBlock()：音訊執行緒，每個 processBlock 結尾呼叫一次。不配置記憶體、
 *    不上鎖：只有一個逐樣本取 |x| 最大值的迴圈（NaN／inf 另外記成「超標」），
 *    加一個 lock-free 的 std::atomic<float> compare-exchange「取最大值」迴圈。
 *  - takePeak()：message 執行緒（editor timer）。回傳「上次 take 之後」所有
 *    block 的最大 |sample| 並歸零，所以 editor 20 Hz 輪詢之間的短暫超標不會
 *    被下一個 block 蓋掉。
 *
 * 判準 kFullScale = 1.0f：0 dBFS 的定義（浮點滿刻度），不是調出來的容差；
 * 「超過 0 dBFS」＝峰值 > 1.0f（剛好等於 1.0 不算削波）。
 */
class OutputPeakMeter
{
public:
    static constexpr float kFullScale = 1.0f;   // 0 dBFS by definition

    static_assert (std::atomic<float>::is_always_lock_free,
                   "OutputPeakMeter requires a lock-free std::atomic<float>");

    void pushBlock (const juce::AudioBuffer<float>& buffer) noexcept
    {
        const int n = buffer.getNumSamples();
        constexpr float kMaxFinite = std::numeric_limits<float>::max();
        float blockPeak = 0.0f;
        bool nonFinite = false;
        for (int ch = 0; ch < buffer.getNumChannels(); ++ch)
        {
            const float* d = buffer.getReadPointer (ch);
            for (int i = 0; i < n; ++i)
            {
                const float a = std::abs (d[i]);
                if (! (a <= kMaxFinite))      // NaN or +-inf
                    nonFinite = true;
                else if (a > blockPeak)
                    blockPeak = a;
            }
        }
        // A non-finite output sample is not a valid in-range sample either;
        // record it as over full scale so the indicator lights instead of the
        // NaN silently comparing false everywhere.
        noteBlockPeak (nonFinite ? kMaxFinite : blockPeak);
    }

    void noteBlockPeak (float blockPeak) noexcept
    {
        float current = peakSinceLastTake.load (std::memory_order_relaxed);
        while (blockPeak > current
               && ! peakSinceLastTake.compare_exchange_weak (current, blockPeak,
                                                             std::memory_order_relaxed))
        {
        }
    }

    float takePeak() noexcept
    {
        return peakSinceLastTake.exchange (0.0f, std::memory_order_relaxed);
    }

    static bool isOverFullScale (float peak) noexcept { return peak > kFullScale; }

private:
    std::atomic<float> peakSinceLastTake { 0.0f };
};
