#pragma once

#include <array>
#include <algorithm>

/** Single source of truth for score rendering and analysis sample rates. */
namespace TsukiSampleRates
{
inline constexpr std::array<int, 6> supported {
    44100, 48000, 88200, 96000, 176400, 192000
};

inline bool isSupported (double sampleRate)
{
    return std::any_of (supported.begin(), supported.end(),
                        [sampleRate] (int value)
                        { return sampleRate == (double) value; });
}

inline constexpr const char* description =
    "44100, 48000, 88200, 96000, 176400, 192000";
} // namespace TsukiSampleRates
