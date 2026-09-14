#pragma once
#include <juce_audio_processors/juce_audio_processors.h>

// WF0908-E10b (design doc §10.2, option B): `createParameterLayout()` was a
// private static member of TsukiSynthProcessor, defined in
// PluginProcessor.cpp -- a translation unit that also includes
// "PluginEditor.h" and therefore the full GUI module chain. Extracted here,
// as a free function with NO GUI include, so that a GUI-free target (the L2
// HostProbe, tests/host_probe.cpp) can build a real
// juce::AudioProcessorValueTreeState against the product's real parameter
// layout -- needed for H7's shadow-APVTS PresetManager::saveUserPreset()
// test -- without linking PluginEditor.cpp / juce_gui_basics / juce_gui_extra.
//
// This is a PURE MOVE: parameter ids, ranges, and defaults are byte-for-byte
// what TsukiSynthProcessor::createParameterLayout() used to build (verified
// by an H2 parameter-list dump taken before and after this refactor --
// see the WF0908-E10b evidence file). TsukiSynthProcessor::apvts now
// constructs from createTsukiParameterLayout() instead of its own private
// method.
juce::AudioProcessorValueTreeState::ParameterLayout createTsukiParameterLayout();
