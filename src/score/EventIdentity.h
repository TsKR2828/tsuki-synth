#pragma once

#include "ScoreParser.h"
#include "../dsp/NoiseGen.h"

#include <algorithm>
#include <cmath>
#include <cstdint>
#include <cstring>
#include <limits>
#include <string>
#include <vector>

/** Stable, semantic identity for offline score events.

    Array position is deliberately absent. Reordering simultaneous JSON events
    or inserting a zero-velocity event must not reseed unrelated attacks. The
    byte encoding is explicitly little-endian and field-ordered, so it does not
    depend on locale, JSON formatting, std::hash, or host endianness.
*/
namespace TsukiEventIdentity
{
inline void appendU64 (std::string& out, uint64_t value)
{
    for (int shift = 0; shift < 64; shift += 8)
        out.push_back ((char) ((value >> shift) & 0xffu));
}

inline void appendU32 (std::string& out, uint32_t value)
{
    for (int shift = 0; shift < 32; shift += 8)
        out.push_back ((char) ((value >> shift) & 0xffu));
}

inline void appendBool (std::string& out, bool value)
{
    out.push_back (value ? '\x01' : '\x00');
}

inline void appendDouble (std::string& out, double value)
{
    if (value == 0.0) value = 0.0; // canonicalise negative zero
    uint64_t bits = 0;
    static_assert (sizeof (bits) == sizeof (value)
                   && std::numeric_limits<double>::is_iec559,
                   "64-bit IEEE double required");
    std::memcpy (&bits, &value, sizeof (bits));
    appendU64 (out, bits);
}

inline void appendFloat (std::string& out, float value)
{
    if (value == 0.0f) value = 0.0f; // canonicalise negative zero
    uint32_t bits = 0;
    static_assert (sizeof (bits) == sizeof (value)
                   && std::numeric_limits<float>::is_iec559,
                   "32-bit IEEE float required");
    std::memcpy (&bits, &value, sizeof (bits));
    appendU32 (out, bits);
}

inline void appendString (std::string& out, const std::string& value)
{
    appendU64 (out, (uint64_t) value.size());
    out.append (value);
}

inline std::string canonicalEventBytes (const ScoreEvent& event)
{
    std::string out;
    out.reserve (384);
    appendString (out, event.eventId);
    appendDouble (out, event.time);
    appendDouble (out, event.duration);
    appendString (out, event.engine);
    appendString (out, event.note);
    appendFloat (out, event.velocity);
    appendString (out, event.material);
    appendDouble (out, event.strikePosition);
    appendDouble (out, event.thicknessMm);
    appendDouble (out, event.radiusMm);
    appendDouble (out, event.lengthMm);
    appendDouble (out, event.widthMm);
    appendString (out, event.beamBoundary);
    appendString (out, event.frequencyMode);
    appendString (out, event.exciter);
    appendDouble (out, event.diameterMm);
    appendU32 (out, (uint32_t) event.numStrings);
    appendFloat (out, event.detuningCents);
    appendDouble (out, event.tensionN);
    appendDouble (out, event.dampingOverride);
    appendU32 (out, (uint32_t) event.fmPreset);
    appendFloat (out, event.fmRatio);
    appendFloat (out, event.fmIndex);
    appendFloat (out, event.fmBrightness);
    appendFloat (out, event.fmFeedback);
    appendFloat (out, event.fmAttackMs);
    appendFloat (out, event.fmReleaseMs);
    appendBool (out, event.plateFreeEdge);
    for (int i = 0; i < 8; ++i) appendFloat (out, event.customRatios[i]);
    for (int i = 0; i < 8; ++i) appendFloat (out, event.customAmps[i]);
    appendBool (out, event.hasGlide);
    appendString (out, event.glideFromNote);
    appendDouble (out, event.glideDurationMs);
    appendString (out, event.glideCurve);
    return out;
}

inline uint64_t stableHash (const std::string& bytes) noexcept
{
    uint64_t hash = 14695981039346656037ull; // FNV-1a 64 offset basis
    for (const unsigned char byte : bytes)
    {
        hash ^= byte;
        hash *= 1099511628211ull;
    }
    return hash;
}

struct PlannedEvent
{
    const ScoreEvent* event = nullptr;
    size_t sourceIndex = 0;
    std::string canonicalBytes;
    uint64_t identity = 0;
};

inline std::vector<PlannedEvent> buildPlan (
    const std::vector<ScoreEvent>& events, bool includeZeroVelocity = false)
{
    std::vector<PlannedEvent> plan;
    plan.reserve (events.size());
    for (size_t i = 0; i < events.size(); ++i)
    {
        if (! includeZeroVelocity && events[i].velocity <= 0.0f)
            continue;
        plan.push_back ({ &events[i], i, canonicalEventBytes (events[i]), 0 });
    }

    std::sort (plan.begin(), plan.end(), [] (const auto& a, const auto& b)
    {
        if (a.canonicalBytes != b.canonicalBytes)
            return a.canonicalBytes < b.canonicalBytes;
        // Exact duplicates are physically indistinguishable. This final tie
        // break only gives their deterministic stream multiset an order.
        return a.sourceIndex < b.sourceIndex;
    });

    size_t groupStart = 0;
    while (groupStart < plan.size())
    {
        size_t groupEnd = groupStart + 1;
        while (groupEnd < plan.size()
               && plan[groupEnd].canonicalBytes == plan[groupStart].canonicalBytes)
            ++groupEnd;

        const auto& event = *plan[groupStart].event;
        std::string identityMaterial;
        if (! event.eventId.empty())
        {
            identityMaterial = "event_id";
            identityMaterial.push_back ('\0');
            identityMaterial.append (event.eventId);
        }
        else
        {
            identityMaterial = "semantic";
            identityMaterial.push_back ('\0');
            identityMaterial.append (plan[groupStart].canonicalBytes);
        }
        const uint64_t base = stableHash (identityMaterial);
        for (size_t i = groupStart; i < groupEnd; ++i)
        {
            const uint64_t duplicateRank = (uint64_t) (i - groupStart);
            plan[i].identity = NoiseGen::mixSeed (
                base, duplicateRank,
                (uint32_t) noteNameToMidi (plan[i].event->note),
                (uint32_t) std::llround (plan[i].event->velocity * 1000000.0f));
        }
        groupStart = groupEnd;
    }
    return plan;
}

inline std::vector<uint64_t> identitiesBySourceIndex (
    const std::vector<ScoreEvent>& events)
{
    std::vector<uint64_t> identities (events.size(), 0);
    for (const auto& planned : buildPlan (events, true))
        identities[planned.sourceIndex] = planned.identity;
    return identities;
}
} // namespace TsukiEventIdentity
