cmake_minimum_required(VERSION 3.22)
project(TsukiSynth VERSION 0.3.0)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

if(MSVC)
    add_compile_options(/utf-8)
endif()

add_subdirectory(libs/JUCE)

# --- AAX / AU support ---
option(TSUKI_AAX "Build AAX format (requires Avid AAX SDK)" OFF)
option(TSUKI_AU  "Build AU format (macOS only)" OFF)

set(PLUGIN_FORMATS VST3 Standalone)

if(TSUKI_AU AND APPLE)
    list(APPEND PLUGIN_FORMATS AU)
    message(STATUS "AU (Audio Unit) enabled")
endif()

if(TSUKI_AAX)
    if(NOT DEFINED AAX_SDK_PATH)
        message(FATAL_ERROR "TSUKI_AAX=ON but AAX_SDK_PATH not set.")
    endif()
    juce_set_aax_sdk_path("${AAX_SDK_PATH}")
    list(APPEND PLUGIN_FORMATS AAX)
    message(STATUS "AAX enabled: SDK at ${AAX_SDK_PATH}")
endif()

juce_add_plugin(TsukiSynth
    COMPANY_NAME "TsKR"
    IS_SYNTH TRUE
    NEEDS_MIDI_INPUT TRUE
    NEEDS_MIDI_OUTPUT FALSE
    PLUGIN_MANUFACTURER_CODE TsKR
    PLUGIN_CODE TkSy
    FORMATS ${PLUGIN_FORMATS}
    PRODUCT_NAME "TsukiSynth"
    AAX_CATEGORY AAX_ePlugInCategory_SWGenerators
)

juce_add_binary_data(TsukiSynthData SOURCES
    data/materials.json
    data/fonts/IBMPlexSans-SemiBold.ttf
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
        juce::juce_audio_formats
        juce::juce_audio_utils
        juce::juce_dsp
    PUBLIC
        juce::juce_recommended_config_flags
        juce::juce_recommended_lto_flags
        juce::juce_recommended_warning_flags
)

# --- CLI Score Renderer ---
juce_add_console_app(TsukiSynthCLI
    PRODUCT_NAME "tsukisynth-cli"
)

target_sources(TsukiSynthCLI PRIVATE
    src/cli/RenderApp.cpp
)

target_include_directories(TsukiSynthCLI PRIVATE src)

target_compile_definitions(TsukiSynthCLI PRIVATE
    JUCE_WEB_BROWSER=0
    JUCE_USE_CURL=0
)

target_link_libraries(TsukiSynthCLI
    PRIVATE
        TsukiSynthData
        juce::juce_core
        juce::juce_audio_formats
        juce::juce_audio_processors
    PUBLIC
        juce::juce_recommended_config_flags
        juce::juce_recommended_lto_flags
)

# --- Regression tests ---
option(TSUKI_BUILD_TESTS "Build regression tests" ON)
if(TSUKI_BUILD_TESTS)
    enable_testing()
    add_executable(TsukiSynthAuditTest tests/audit_repro.cpp)
    target_include_directories(TsukiSynthAuditTest PRIVATE src)
    target_compile_definitions(TsukiSynthAuditTest PRIVATE
        JUCE_WEB_BROWSER=0
        JUCE_USE_CURL=0
    )
    target_link_libraries(TsukiSynthAuditTest
        PRIVATE
            juce::juce_audio_formats
            juce::juce_audio_processors
        PUBLIC
            juce::juce_recommended_config_flags
    )
    add_test(NAME audit_repro COMMAND TsukiSynthAuditTest)

    add_executable(TsukiSynthTunerTest tests/tuner_repro.cpp)
    target_include_directories(TsukiSynthTunerTest PRIVATE src)
    # Kept consistent with the other two test targets. tuner_repro.cpp's
    # current includes (PitchDetector/AudioFIFO/MidiNoteTracker) are std-only,
    # but parity here means a future JUCE-touching include cannot silently
    # build this target with different definitions/flags than its siblings.
    target_compile_definitions(TsukiSynthTunerTest PRIVATE
        JUCE_WEB_BROWSER=0
        JUCE_USE_CURL=0
    )
    target_link_libraries(TsukiSynthTunerTest
        PRIVATE
            juce::juce_audio_formats
            juce::juce_audio_processors
        PUBLIC
            juce::juce_recommended_config_flags
    )
    add_test(NAME tuner_repro COMMAND TsukiSynthTunerTest)

    add_executable(TsukiSynthPhysicsModelsTest tests/physics_models_repro.cpp)
    target_include_directories(TsukiSynthPhysicsModelsTest PRIVATE src)
    target_compile_definitions(TsukiSynthPhysicsModelsTest PRIVATE
        JUCE_WEB_BROWSER=0
        JUCE_USE_CURL=0
    )
    target_link_libraries(TsukiSynthPhysicsModelsTest
        PRIVATE
            juce::juce_audio_formats
            juce::juce_audio_processors
        PUBLIC
            juce::juce_recommended_config_flags
    )
    add_test(NAME physics_models_repro COMMAND TsukiSynthPhysicsModelsTest)
endif()
