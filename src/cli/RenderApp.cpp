#include <juce_core/juce_core.h>
#include <juce_audio_formats/juce_audio_formats.h>
#include "../score/ScoreParser.h"
#include "../score/ScoreRenderer.h"
#include "../physics/MaterialDB.h"
#include "../dsp/DiagnosticOverrides.h"
#include "BinaryData.h"

#include <iostream>

static MaterialDB globalMaterialDB;

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
            DiagnosticOverrides::bodyAmountOverride = juce::String (argv[i + 1]).getFloatValue();
            ++i;
        }
        else if (arg == "--no-exciter-noise")
        {
            DiagnosticOverrides::disableExciterNoise = true;
        }
        else if (arg == "--num-strings" && i + 1 < argc)
        {
            DiagnosticOverrides::numStringsOverride = juce::String (argv[i + 1]).getIntValue();
            ++i;
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
        return false;
    }

    for (const auto& w : score.warnings)
        std::cout << "  WARNING: " << w << std::endl;

    outputDir.createDirectory();

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
    juce::File outFile = outputDir.getChildFile (outName + extension);

    if (! isSafeOutputName (outName))
    {
        std::cout << "  REJECTED unsafe filename: " << outName << std::endl;
        return false;
    }

    if (outFile.existsAsFile())
    {
        std::cout << "  SKIPPED (already exists): " << outFile.getFullPathName() << std::endl;
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
            for (const auto& w : renderer.getWarnings())
                std::cout << "  WARNING: " << w << std::endl;
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
            for (const auto& w : renderer.getWarnings())
                std::cout << "  WARNING: " << w << std::endl;
            std::cout << "  -> " << outFile.getFullPathName() << std::endl;
            return true;
        }
    }

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

    if (args.size() < 2)
    {
        std::cout << "TsukiSynth CLI Renderer" << std::endl;
        std::cout << "Usage:" << std::endl;
        std::cout << "  tsukisynth-cli <score.json> [--output <dir>]" << std::endl;
        std::cout << "  tsukisynth-cli --batch <dir> [--output <dir>]" << std::endl;
        return 0;
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
        return 0;
    }

    if (firstArg == "--dump-modes")
    {
        if (args.size() < 3)
        {
            std::cout << "Usage: tsukisynth-cli --dump-modes <score.json>" << std::endl;
            return 1;
        }
        juce::File scoreFile { args[2] };
        Score score;
        if (! ScoreParser::parse (scoreFile, score))
        {
            std::cout << "FAILED to parse: " << scoreFile.getFileName() << std::endl;
            return 1;
        }
        ScoreRenderer renderer;
        renderer.setMaterialDB (&globalMaterialDB);
        renderer.setBaseDir (scoreFile.getParentDirectory());
        std::cout << renderer.dumpModes (score).toStdString();
        return 0;
    }

    if (firstArg == "--batch" || firstArg == "-b")
    {
        if (args.size() < 3)
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

        std::cout << "Batch rendering " << files.size() << " scores..." << std::endl;
        int ok = 0;
        for (const auto& f : files)
            if (renderScore (f, outputDir))
                ++ok;

        std::cout << "Done: " << ok << "/" << files.size() << " rendered." << std::endl;
        return (ok == files.size()) ? 0 : 1;
    }

    juce::File scoreFile { firstArg };
    if (! scoreFile.existsAsFile())
    {
        std::cout << "File not found: " << scoreFile.getFullPathName() << std::endl;
        return 1;
    }

    return renderScore (scoreFile, outputDir) ? 0 : 1;
}
