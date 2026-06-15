#include <juce_core/juce_core.h>
#include <juce_audio_formats/juce_audio_formats.h>
#include "../score/ScoreParser.h"
#include "../score/ScoreRenderer.h"
#include "../physics/MaterialDB.h"
#include "BinaryData.h"

#include <iostream>

static MaterialDB globalMaterialDB;

static void ensureMaterialDB()
{
    if (globalMaterialDB.size() == 0)
    {
        globalMaterialDB.loadFromString (juce::String::fromUTF8 (
            BinaryData::materials_json,
            static_cast<int> (BinaryData::materials_jsonSize)));
    }
}

static juce::File getOutputDir (int argc, char* argv[])
{
    for (int i = 1; i < argc - 1; ++i)
    {
        juce::String arg (argv[i]);
        if (arg == "--output" || arg == "-o")
            return juce::File (juce::String (argv[i + 1]));
    }
    return juce::File::getCurrentWorkingDirectory()
               .getChildFile ("exports").getChildFile ("wav");
}

static bool renderScore (const juce::File& scoreFile, const juce::File& outputDir)
{
    Score score;
    if (! ScoreParser::parse (scoreFile, score))
    {
        std::cout << "  FAILED to parse: " << scoreFile.getFileName() << std::endl;
        return false;
    }

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

    ScoreRenderer renderer;
    renderer.setMaterialDB (&globalMaterialDB);
    renderer.setBaseDir (scoreFile.getParentDirectory());

    if (score.hasLayers())
    {
        std::cout << "  Layering: " << score.meta.title
                  << " (" << score.layers.size() << " layers)" << std::endl;

        if (renderer.renderLayered (score, outFile))
        {
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

    if (argc < 2)
    {
        std::cout << "TsukiSynth CLI Renderer" << std::endl;
        std::cout << "Usage:" << std::endl;
        std::cout << "  tsukisynth-cli <score.json> [--output <dir>]" << std::endl;
        std::cout << "  tsukisynth-cli --batch <dir> [--output <dir>]" << std::endl;
        return 0;
    }

    ensureMaterialDB();
    auto outputDir = getOutputDir (argc, argv);

    juce::String firstArg (argv[1]);

    if (firstArg == "--dump-modes")
    {
        if (argc < 3)
        {
            std::cout << "Usage: tsukisynth-cli --dump-modes <score.json>" << std::endl;
            return 1;
        }
        juce::File scoreFile { juce::String (argv[2]) };
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
        if (argc < 3)
        {
            std::cout << "Usage: tsukisynth-cli --batch <dir> [--output <dir>]" << std::endl;
            return 1;
        }

        juce::String dirPath { argv[2] };
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
