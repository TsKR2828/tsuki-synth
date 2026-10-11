#pragma once

// Voice pool size per engine for the PLUG-IN (one juce::Synthesiser per engine
// in TsukiSynthProcessor; Piano and Cimbalom share the Cimbalom synth).
// The CLI renderer does NOT use this header or any pool: it creates one voice
// per event (src/cli/RenderApp.cpp; CMakeLists.txt compiles PluginProcessor.cpp
// only into the plug-in targets).
//
// Provenance (R4: every constant traced):
//   Cimbalom/Piano 16 and FM 16 -- the long-standing pool size. WF1003-V
//     (reports/wf1003_v_voice_pool.zh-TW.md) measured 32 Piano voices held at
//     once at 7.3 ms mean / 20.5 ms p99 per 512-sample block against a 10.67 ms
//     real-time budget (about 30% of blocks late), so Piano stays 16. FM has no
//     measurement at any size, so it is not changed.
//   Chromatic 32 -- month-month ruling 2026-10-07 ("照 Fable 建議", evidence-
//     threshold rule) on WF1003-V's data: 32 Chromatic (Tongue Drum) voices held
//     at once cost 0.44 ms mean / 1.3 ms p99 and the moonlight tongue-drum score
//     (demand 20 voices) went from 64 steals to 0. Adoption was conditional on
//     the pre-registered criteria in reports/gate_outputs/wf1004_P_criteria_
//     preregistered.txt; result in reports/wf1004_p_per_engine_pool.zh-TW.md.
//
// The TSUKI_VOICE_POOL_* macros are compile-time overrides that exist only so the
// before/after evidence can be re-run with a baseline build (method:
// reports/gate_outputs/wf1004_P_method.txt). TSUKI_VOICE_POOL_SIZE (WF1003-V's
// uniform override) still forces all three engines to one value.
#ifdef TSUKI_VOICE_POOL_SIZE
 #ifndef TSUKI_VOICE_POOL_CIMBALOM
  #define TSUKI_VOICE_POOL_CIMBALOM TSUKI_VOICE_POOL_SIZE
 #endif
 #ifndef TSUKI_VOICE_POOL_CHROMATIC
  #define TSUKI_VOICE_POOL_CHROMATIC TSUKI_VOICE_POOL_SIZE
 #endif
 #ifndef TSUKI_VOICE_POOL_FM
  #define TSUKI_VOICE_POOL_FM TSUKI_VOICE_POOL_SIZE
 #endif
#endif
#ifndef TSUKI_VOICE_POOL_CIMBALOM
 #define TSUKI_VOICE_POOL_CIMBALOM 16
#endif
#ifndef TSUKI_VOICE_POOL_CHROMATIC
 #define TSUKI_VOICE_POOL_CHROMATIC 32
#endif
#ifndef TSUKI_VOICE_POOL_FM
 #define TSUKI_VOICE_POOL_FM 16
#endif

namespace TsukiVoicePool
{
    inline constexpr int kCimbalom  = TSUKI_VOICE_POOL_CIMBALOM;   // engines 0 (Cimbalom) and 3 (Piano)
    inline constexpr int kChromatic = TSUKI_VOICE_POOL_CHROMATIC;  // engine 1 (Tongue Drum / Water Gong / Custom Harmonics)
    inline constexpr int kFMPiano   = TSUKI_VOICE_POOL_FM;         // engine 2 (FM Piano)
}
