cmake_minimum_required(VERSION 3.22)
project(TsukiSynth VERSION 0.1.0)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# MSVC: treat source files as UTF-8 (fixes codepage 950 parsing errors)
if(MSVC)
    add_compile_options(/utf-8)
endif()

add_subdirectory(libs/JUCE)

juce_add_plugin(TsukiSynth
    COMPANY_NAME "TsKR"
    IS_SYNTH TRUE
    NEEDS_MIDI_INPUT TRUE
    NEEDS_MIDI_OUTPUT FALSE
    PLUGIN_MANUFACTURER_CODE TsKR
    PLUGIN_CODE TkSy
    FORMATS VST3 Standalone
    PRODUCT_NAME "TsukiSynth"
)

juce_add_binary_data(TsukiSynthData SOURCES
    data/materials.json
)

target_sources(TsukiSynth PRIVATE
    src/PluginProcessor.cpp
    src/PluginEditor.cpp
)

target_include_directories(TsukiSynth PRIVATE src)

target_compile_definitions(TsukiSynth PUBLIC
    JUCE_WEB_BROWSER=0
    JUCE_USE_CURL=0
    JUCE_VST3_CAN_REPLACE_VST2=0
)

target_link_libraries(TsukiSynth
    PRIVATE
        TsukiSynthData
        juce::juce_audio_utils
    PUBLIC
        juce::juce_recommended_config_flags
        juce::juce_recommended_lto_flags
        juce::juce_recommended_warning_flags
)
