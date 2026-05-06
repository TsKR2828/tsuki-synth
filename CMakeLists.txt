cmake_minimum_required(VERSION 3.22)
project(TsukiSynth VERSION 0.1.0 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

include(FetchContent)

FetchContent_Declare(
    JUCE
    GIT_REPOSITORY https://github.com/juce-framework/JUCE.git
    GIT_TAG        8.0.1
    GIT_SHALLOW    TRUE
    GIT_PROGRESS   TRUE
)

FetchContent_MakeAvailable(JUCE)

juce_add_plugin(TsukiSynth
    COMPANY_NAME        "TsKR"
    PLUGIN_MANUFACTURER_CODE TsKR
    PLUGIN_CODE         TkSy
    FORMATS             VST3 Standalone
    PRODUCT_NAME        "TsukiSynth"
    IS_SYNTH            TRUE
    NEEDS_MIDI_INPUT    TRUE
    NEEDS_MIDI_OUTPUT   FALSE
    IS_MIDI_EFFECT      FALSE
    COPY_PLUGIN_AFTER_BUILD FALSE
)

juce_add_binary_data(TsukiSynthData
    SOURCES
        data/materials.json
)

target_sources(TsukiSynth
    PRIVATE
        src/PluginProcessor.cpp
        src/PluginEditor.cpp
)

target_include_directories(TsukiSynth
    PRIVATE
        src
)

target_compile_definitions(TsukiSynth
    PUBLIC
        JUCE_WEB_BROWSER=0
        JUCE_USE_CURL=0
        JUCE_VST3_CAN_REPLACE_VST2=0
)

target_link_libraries(TsukiSynth
    PRIVATE
        TsukiSynthData
        juce::juce_audio_utils
        juce::juce_dsp
    PUBLIC
        juce::juce_recommended_config_flags
        juce::juce_recommended_lto_flags
        juce::juce_recommended_warning_flags
)

# --- CLI Renderer ---
juce_add_console_app(TsukiSynthCLI
    PRODUCT_NAME "tsukisynth-cli"
)

target_sources(TsukiSynthCLI
    PRIVATE
        src/cli/RenderApp.cpp
)

target_include_directories(TsukiSynthCLI
    PRIVATE
        src
)

target_compile_definitions(TsukiSynthCLI
    PRIVATE
        JUCE_WEB_BROWSER=0
        JUCE_USE_CURL=0
)

target_link_libraries(TsukiSynthCLI
    PRIVATE
        TsukiSynthData
        juce::juce_core
        juce::juce_audio_formats
    PUBLIC
        juce::juce_recommended_config_flags
        juce::juce_recommended_lto_flags
)
