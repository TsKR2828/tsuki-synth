#include <juce_core/juce_core.h>
#include <juce_audio_formats/juce_audio_formats.h>

// juce::SHA256 (used by writeRenderManifest() for the v2 manifest's
// wav_sha256 field) lives in the juce_cryptography module, which is NOT in
// this target's link list (CMakeLists.txt links juce_core /
// juce_audio_formats / juce_audio_processors only, and CMakeLists.txt is
// outside this fix line's file scope). The class depends only on juce_core,
// so its single self-contained implementation file is compiled into this
// translation unit directly -- the same mechanism as JUCE's own generated
// include_juce_cryptography.cpp unity file, narrowed to just SHA256. If the
// module is ever added to target_link_libraries, drop the .cpp include
// below (duplicate symbols) and keep only the header.
#include <juce_cryptography/juce_cryptography.h>
#include <juce_cryptography/hashing/juce_SHA256.cpp>

#include "../score/ScoreParser.h"
#include "../score/ScoreRenderer.h"
#include "../physics/MaterialDB.h"
#include "../dsp/DiagnosticOverrides.h"
#include "BinaryData.h"

#include <iostream>
#include <algorithm>
#include <cmath>
#include <set>
#include <vector>

static MaterialDB globalMaterialDB;
static std::vector<std::string> argumentErrors;

// DIAGNOSTIC-ONLY (2026-07-09, M2 option b, 月月-authorized): strip
// --body-amount / --no-exciter-noise / --num-strings out of argv, setting
// DiagnosticOverrides accordingly, and return everything else untouched.
// These flags exist only so tools/physics_verify.py can isolate a single
// signal-path stage via differential renders -- they are NOT part of the
// verified render contract (ROADMAP_PHYSICS.md §1) and are filtered out
// here so the remaining dispatch logic below (which mimics the pre-existing
// argc/argv shape) never has to know about them. When none of these three
// flags are present, `remaining` is byte-for-byte the original argument
// list and every DiagnosticOverrides value stays at its "no override"
// sentinel -- i.e. render behavior is provably unchanged (see the
// SHA256 no-flags proof recorded alongside this change).
static juce::StringArray extractDiagnosticOverrides (int argc, char* argv[])
{
    juce::StringArray remaining;
    for (int i = 0; i < argc; ++i)
    {
        juce::String arg (argv[i]);
        if (arg == "--body-amount" && i + 1 < argc)
        {
            try
            {
                size_t used = 0;
                const std::string raw (argv[i + 1]);
                const float value = std::stof (raw, &used);
                if (used != raw.size() || ! std::isfinite (value) || value < 0.0f || value > 1.0f)
                    throw std::invalid_argument ("range");
                DiagnosticOverrides::bodyAmountOverride = value;
            }
            catch (...) { argumentErrors.push_back ("--body-amount requires a finite value in [0,1]"); }
            ++i;
        }
        else if (arg == "--body-amount")
        {
            argumentErrors.push_back ("--body-amount requires a value");
        }
        else if (arg == "--no-exciter-noise")
        {
            DiagnosticOverrides::disableExciterNoise = true;
        }
        else if (arg == "--num-strings" && i + 1 < argc)
        {
            try
            {
                size_t used = 0;
                const std::string raw (argv[i + 1]);
                const int value = std::stoi (raw, &used);
                if (used != raw.size() || value < 1 || value > 5)
                    throw std::invalid_argument ("range");
                DiagnosticOverrides::numStringsOverride = value;
            }
            catch (...) { argumentErrors.push_back ("--num-strings requires an integer in [1,5]"); }
            ++i;
        }
        else if (arg == "--num-strings")
        {
            argumentErrors.push_back ("--num-strings requires a value");
        }
        else
        {
            remaining.add (arg);
        }
    }
    return remaining;
}

static void ensureMaterialDB()
{
    if (globalMaterialDB.size() == 0)
    {
        globalMaterialDB.loadFromString (juce::String::fromUTF8 (
            BinaryData::materials_json,
            static_cast<int> (BinaryData::materials_jsonSize)));
    }
}

static juce::File getOutputDir (const juce::StringArray& args)
{
    for (int i = 1; i < args.size() - 1; ++i)
    {
        if (args[i] == "--output" || args[i] == "-o")
            return juce::File (args[i + 1]);
    }
    return juce::File::getCurrentWorkingDirectory()
               .getChildFile ("exports").getChildFile ("wav");
}

static bool hasExactOutputOption (const juce::StringArray& args, int start)
{
    if (args.size() == start) return true;
    return args.size() == start + 2
        && (args[start] == "--output" || args[start] == "-o")
        && args[start + 1].isNotEmpty();
}

static void printParseErrors (const Score& score, std::ostream& stream = std::cout)
{
    for (const auto& error : score.errors)
        stream << "  ERROR: " << error << std::endl;
    for (const auto& warning : score.warnings)
        stream << "  WARNING: " << warning << std::endl;
}

static void printRendererMessages (const ScoreRenderer& renderer)
{
    for (const auto& warning : renderer.getWarnings())
        std::cout << "  ERROR: " << warning << std::endl;
}

// Manifest contract v2 (2026-07-18), consumed by tools/verify_score.py:
//   * wav_sha256: SHA256 of the written output file's bytes, hashed from
//     disk AFTER the renderer has finished writing it -- the artifact
//     carries its own verifiability (a verifier needs nothing but the WAV
//     and its manifest to prove they belong together). Read-only: the
//     audio bytes and the render order are untouched by this change.
//   * score: stored relative to the manifest's own directory (falling back
//     to the bare file name when no relative path exists, e.g. the score
//     sits on a different drive) instead of v1's machine-specific absolute
//     path, so the output directory is relocatable.
static bool writeRenderManifest (const juce::File& scoreFile,
                                 const juce::File& outputFile,
                                 const Score& score,
                                 const ScoreRenderer& renderer)
{
    const auto& report = renderer.getWriteReport();

    // Hash exactly what is on disk. Opening the stream explicitly (instead
    // of the juce::SHA256(File) convenience constructor) lets a failed open
    // be reported as an error rather than silently hashing to all-zeros.
    juce::FileInputStream wavStream (outputFile);
    if (! wavStream.openedOk())
    {
        std::cout << "  ERROR: failed to re-open output for hashing: "
                  << outputFile.getFullPathName() << std::endl;
        outputFile.deleteFile();
        return false;
    }
    const juce::SHA256 wavHash (wavStream);

    // Score path relative to where this manifest lands. JUCE's
    // getRelativePathFrom() returns the untouched absolute path when no
    // relative path exists -- detect that and fall back to the file name.
    // Separators are normalised to '/' (also valid on Windows) so the
    // manifest bytes do not depend on the platform's native separator.
    const auto manifestDir = outputFile.getParentDirectory();
    juce::String scoreRef = scoreFile.getRelativePathFrom (manifestDir);
    if (juce::File::isAbsolutePath (scoreRef))
        scoreRef = scoreFile.getFileName();
    scoreRef = scoreRef.replaceCharacter ('\\', '/');

    juce::DynamicObject::Ptr root (new juce::DynamicObject());
    root->setProperty ("contract", "TsukiSynth Render Manifest v2");
    root->setProperty ("score", scoreRef);
    root->setProperty ("output", outputFile.getFileName());
    root->setProperty ("wav_sha256", wavHash.toHexString());
    root->setProperty ("sample_rate", score.global.sampleRate);
    root->setProperty ("random_seed", static_cast<juce::int64> (score.global.randomSeed));
    root->setProperty ("input_event_count", static_cast<int> (score.events.size()));
    root->setProperty ("input_layer_count", static_cast<int> (score.layers.size()));
    root->setProperty ("normalize", score.exportSettings.normalize);
    root->setProperty ("pre_normalize_peak", report.preNormalizePeak);
    root->setProperty ("applied_gain", report.appliedGain);
    root->setProperty ("samples_at_or_above_full_scale",
                       static_cast<juce::int64> (report.samplesAtOrAboveFullScale));
    const auto manifest = outputFile.getSiblingFile (outputFile.getFileName() + ".render.json");
    if (! manifest.replaceWithText (juce::JSON::toString (juce::var (root.get()), true)))
    {
        std::cout << "  ERROR: failed to write render manifest: "
                  << manifest.getFullPathName() << std::endl;
        outputFile.deleteFile();
        return false;
    }
    return true;
}

static bool isSafeOutputName (const juce::String& name)
{
    if (name.isEmpty()) return false;
    if (name.containsChar ('/') || name.containsChar ('\\')) return false;
    if (name.contains ("..")) return false;
    if (juce::File::isAbsolutePath (name)) return false;
    return true;
}

static bool renderScore (const juce::File& scoreFile, const juce::File& outputDir)
{
    Score score;
    if (! ScoreParser::parse (scoreFile, score))
    {
        std::cout << "  FAILED to parse: " << scoreFile.getFileName() << std::endl;
        printParseErrors (score);
        return false;
    }

    for (const auto& w : score.warnings)
        std::cout << "  WARNING: " << w << std::endl;

    if (! outputDir.createDirectory())
    {
        std::cout << "  FAILED to create output directory: "
                  << outputDir.getFullPathName() << std::endl;
        return false;
    }

    juce::String outName;
    if (! score.exportSettings.exportFilename.empty())
        outName = juce::String (score.exportSettings.exportFilename);
    else if (! score.exportSettings.filename.empty())
        outName = juce::String (score.exportSettings.filename);
    else
        outName = scoreFile.getFileNameWithoutExtension();

    const juce::String extension = score.exportSettings.format == "flac"
        ? ".flac"
        : ".wav";

    if (! isSafeOutputName (outName))
    {
        std::cout << "  REJECTED unsafe filename: " << outName << std::endl;
        return false;
    }
    juce::File outFile = outputDir.getChildFile (outName + extension);
    const auto manifestFile = outFile.getSiblingFile (
        outFile.getFileName() + ".render.json");

    if (outFile.existsAsFile() || manifestFile.existsAsFile())
    {
        std::cout << "  SKIPPED (output or manifest already exists): "
                  << (outFile.existsAsFile() ? outFile.getFullPathName()
                                             : manifestFile.getFullPathName())
                  << std::endl;
        return false;
    }

    ScoreRenderer renderer;
    renderer.setMaterialDB (&globalMaterialDB);
    renderer.setBaseDir (scoreFile.getParentDirectory());

    if (score.hasLayers())
    {
        std::cout << "  Layering: " << score.meta.title
                  << " (" << score.layers.size() << " layers)" << std::endl;

        if (renderer.renderLayered (score, outFile))
        {
            printRendererMessages (renderer);
            if (! writeRenderManifest (scoreFile, outFile, score, renderer)) return false;
            std::cout << "  -> " << outFile.getFullPathName() << std::endl;
            return true;
        }
    }
    else
    {
        std::cout << "  Rendering: " << score.meta.title
                  << " (" << score.events.size() << " events)" << std::endl;

        if (renderer.render (score, outFile))
        {
            printRendererMessages (renderer);
            if (! writeRenderManifest (scoreFile, outFile, score, renderer)) return false;
            std::cout << "  -> " << outFile.getFullPathName() << std::endl;
            return true;
        }
    }

    printRendererMessages (renderer);
    std::cout << "  FAILED to render: " << scoreFile.getFileName() << std::endl;
    return false;
}

int main (int argc, char* argv[])
{
    // No GUI init needed - pure offline rendering

    // Strip diagnostic-only overrides out of the argument list first (see
    // extractDiagnosticOverrides() above) so everything below sees the same
    // argv shape it always has. `args` mirrors the original argv indexing
    // (args[0] = program name, args[1] = first real argument, ...).
    juce::StringArray args = extractDiagnosticOverrides (argc, argv);

    if (! argumentErrors.empty())
    {
        for (const auto& error : argumentErrors)
            std::cerr << "ERROR: " << error << std::endl;
        return 2;
    }

    if (args.size() < 2)
    {
        std::cout << "TsukiSynth CLI Renderer" << std::endl;
        std::cout << "Usage:" << std::endl;
        std::cout << "  tsukisynth-cli <score.json> [--output <dir>]" << std::endl;
        std::cout << "  tsukisynth-cli --batch <dir> [--output <dir>]" << std::endl;
        return args.size() == 1 ? 0 : 2;
    }

    ensureMaterialDB();
    auto outputDir = getOutputDir (args);

    juce::String firstArg = args[1];

    if (firstArg == "--help" || firstArg == "-h")
    {
        std::cout << "TsukiSynth CLI Renderer" << std::endl;
        std::cout << "Usage:" << std::endl;
        std::cout << "  tsukisynth-cli <score.json> [--output <dir>]" << std::endl;
        std::cout << "  tsukisynth-cli --batch <dir> [--output <dir>]" << std::endl;
        std::cout << "  tsukisynth-cli --dump-modes <score.json>" << std::endl;
        std::cout << std::endl;
        std::cout << "Diagnostic-only flags (NOT part of the verified render" << std::endl;
        std::cout << "contract, ROADMAP_PHYSICS.md Sec.1 -- for isolating" << std::endl;
        std::cout << "signal-path stages via differential renders only):" << std::endl;
        std::cout << "  --body-amount <float>   override BodyResonance mix (0 = bypass)" << std::endl;
        std::cout << "  --no-exciter-noise      disable the exciter noise-burst transient" << std::endl;
        std::cout << "  --num-strings <int>     override cimbalom/piano string count" << std::endl;
        return args.size() == 2 ? 0 : 2;
    }

    if (firstArg == "--dump-modes")
    {
        if (args.size() != 3)
        {
            std::cout << "Usage: tsukisynth-cli --dump-modes <score.json>" << std::endl;
            return 1;
        }
        juce::File scoreFile { args[2] };
        Score score;
        if (! ScoreParser::parse (scoreFile, score))
        {
            std::cerr << "FAILED to parse: " << scoreFile.getFileName() << std::endl;
            printParseErrors (score, std::cerr);
            return 1;
        }
        ScoreRenderer renderer;
        renderer.setMaterialDB (&globalMaterialDB);
        renderer.setBaseDir (scoreFile.getParentDirectory());
        if (score.hasLayers())
        {
            std::cerr << "ERROR: --dump-modes requires an event score; "
                         "layer expansion is not implemented" << std::endl;
            return 1;
        }
        if (! renderer.validateScore (score))
        {
            for (const auto& error : renderer.getWarnings())
                std::cerr << "ERROR: " << error << std::endl;
            return 1;
        }
        std::cout << renderer.dumpModes (score).toStdString();
        return 0;
    }

    if (firstArg == "--validate")
    {
        if (args.size() != 3)
        {
            std::cerr << "Usage: tsukisynth-cli --validate <score.json>" << std::endl;
            return 2;
        }
        const juce::File scoreFile { args[2] };
        Score score;
        if (! ScoreParser::parse (scoreFile, score))
        {
            printParseErrors (score, std::cerr);
            return 1;
        }
        ScoreRenderer renderer;
        renderer.setMaterialDB (&globalMaterialDB);
        renderer.setBaseDir (scoreFile.getParentDirectory());
        const bool valid = score.hasLayers()
            ? renderer.validateLayeredScore (score)
            : renderer.validateScore (score);
        if (! valid)
        {
            for (const auto& error : renderer.getWarnings())
                std::cerr << "ERROR: " << error << std::endl;
            return 1;
        }
        std::cout << "VALID: " << score.events.size() << " events, "
                  << score.layers.size() << " layers" << std::endl;
        return 0;
    }

    if (firstArg == "--batch" || firstArg == "-b")
    {
        if (args.size() < 3 || ! hasExactOutputOption (args, 3))
        {
            std::cout << "Usage: tsukisynth-cli --batch <dir> [--output <dir>]" << std::endl;
            return 1;
        }

        juce::String dirPath = args[2];
        juce::File dir { dirPath };
        juce::Array<juce::File> files;

        if (dir.isDirectory())
            dir.findChildFiles (files, juce::File::findFiles, false, "*.score.json");
        else
            files.add (juce::File { dirPath });

        if (files.isEmpty())
        {
            std::cout << "No .score.json files found." << std::endl;
            return 1;
        }

        std::sort (files.begin(), files.end(), [] (const juce::File& a, const juce::File& b)
        {
            return a.getFullPathName().compareNatural (b.getFullPathName()) < 0;
        });

        std::set<std::string> outputNames;
        std::set<std::string> existingOutputNames;
        if (outputDir.isDirectory())
        {
            juce::Array<juce::File> existingFiles;
            outputDir.findChildFiles (existingFiles, juce::File::findFiles,
                                      false, "*");
            for (const auto& existing : existingFiles)
                existingOutputNames.insert (
                    existing.getFileName().toLowerCase().toStdString());
        }
        for (const auto& file : files)
        {
            Score score;
            if (! ScoreParser::parse (file, score))
            {
                std::cout << "Batch preflight parse failed: " << file.getFileName() << std::endl;
                printParseErrors (score);
                return 1;
            }
            const auto stem = ! score.exportSettings.exportFilename.empty()
                ? score.exportSettings.exportFilename
                : ! score.exportSettings.filename.empty() ? score.exportSettings.filename
                                                           : file.getFileNameWithoutExtension().toStdString();
            if (! isSafeOutputName (juce::String (stem)))
            {
                std::cout << "Batch preflight rejected unsafe filename: "
                          << stem << std::endl;
                return 1;
            }
            const auto key = juce::String (stem
                + (score.exportSettings.format == "flac" ? ".flac" : ".wav"))
                .toLowerCase().toStdString();
            if (! outputNames.insert (key).second)
            {
                std::cout << "Batch output collision: " << key << std::endl;
                return 1;
            }

            if (existingOutputNames.count (key) != 0)
            {
                std::cout << "Batch preflight found existing output: "
                          << key << std::endl;
                return 1;
            }
            if (existingOutputNames.count (key + ".render.json") != 0)
            {
                std::cout << "Batch preflight found existing manifest: "
                          << key << ".render.json" << std::endl;
                return 1;
            }

            ScoreRenderer renderer;
            renderer.setMaterialDB (&globalMaterialDB);
            renderer.setBaseDir (file.getParentDirectory());
            const bool valid = score.hasLayers()
                ? renderer.validateLayeredScore (score)
                : renderer.validateScore (score);
            if (! valid)
            {
                std::cout << "Batch preflight validation failed: "
                          << file.getFileName() << std::endl;
                printRendererMessages (renderer);
                return 1;
            }
        }

        std::cout << "Batch rendering " << files.size() << " scores..." << std::endl;
        int ok = 0;
        for (const auto& f : files)
            if (renderScore (f, outputDir))
                ++ok;

        std::cout << "Done: " << ok << "/" << files.size() << " rendered." << std::endl;
        return (ok == files.size()) ? 0 : 1;
    }

    juce::File scoreFile { firstArg };
    if (! hasExactOutputOption (args, 2))
    {
        std::cerr << "ERROR: unexpected or incomplete command-line arguments" << std::endl;
        return 2;
    }
    if (! scoreFile.existsAsFile())
    {
        std::cout << "File not found: " << scoreFile.getFullPathName() << std::endl;
        return 1;
    }

    return renderScore (scoreFile, outputDir) ? 0 : 1;
}
