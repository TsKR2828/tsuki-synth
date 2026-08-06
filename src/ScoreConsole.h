#pragma once

#include <juce_gui_basics/juce_gui_basics.h>
#include "TsukiLookAndFeel.h"

/**
 * Standalone-only score console: a small control panel that turns the
 * Standalone build into a self-contained tool (2026-08-06 月月 request --
 * "AI can render WAV without Cubase, a human should get one click too").
 *
 * It deliberately does NOT re-implement rendering. All rendering goes
 * through the same TsukiSynthCLI.exe that the verified render contract
 * (manifest v4, determinism SHA) lives in -- this panel is a launcher, so
 * there is exactly one render path in the project.
 *
 * Capabilities:
 *   - pick a score.json and render it (child process, log streamed)
 *   - open the output folder (Desktop/TsukiSynth_Renders)
 *   - open the score's <name>.report.html if it exists
 *   - generate that report via `python tools/verify_score.py --html`
 *     when the score lives inside a repo checkout (walks up to find
 *     tools/verify_score.py; disabled otherwise, stated in the log)
 */
class ScoreConsole : public juce::Component, private juce::Thread
{
public:
    ScoreConsole() : juce::Thread ("TsukiScoreConsole")
    {
        auto initButton = [this] (juce::TextButton& b, const juce::String& text)
        {
            b.setButtonText (text);
            addAndMakeVisible (b);
        };
        initButton (renderButton,  juce::String::fromUTF8 ("載入 score 並渲染"));   // 載入 score 並渲染
        initButton (folderButton,  juce::String::fromUTF8 ("開輸出資料夾"));       // 開輸出資料夾
        initButton (reportButton,  juce::String::fromUTF8 ("開 HTML 報告"));                    // 開 HTML 報告
        initButton (genReportButton, juce::String::fromUTF8 ("產生報告 (Python)"));         // 產生報告 (Python)

        renderButton.onClick  = [this] { chooseAndRender(); };
        folderButton.onClick  = [this]
        {
            outputDir().createDirectory();
            outputDir().revealToUser();
        };
        reportButton.onClick  = [this] { openReport(); };
        genReportButton.onClick = [this] { generateReport(); };

        statusLabel.setText (juce::String::fromUTF8 (
            "選一份 score.json 開始。輸出：桌面\\TsukiSynth_Renders"),
            juce::dontSendNotification);   // 選一份 score.json 開始。輸出：桌面\TsukiSynth_Renders
        statusLabel.setFont (TsukiLookAndFeel::scaledFont (13.0f));
        addAndMakeVisible (statusLabel);

        log.setMultiLine (true);
        log.setReadOnly (true);
        log.setCaretVisible (false);
        log.setFont (juce::Font (juce::FontOptions ("Consolas", 13.0f,
                                                    juce::Font::plain)));
        addAndMakeVisible (log);

        setSize (640, 420);
    }

    ~ScoreConsole() override { stopThread (8000); }

    void resized() override
    {
        auto area = getLocalBounds().reduced (12);
        auto row = area.removeFromTop (30);
        renderButton.setBounds (row.removeFromLeft (150));
        row.removeFromLeft (8);
        folderButton.setBounds (row.removeFromLeft (120));
        row.removeFromLeft (8);
        reportButton.setBounds (row.removeFromLeft (120));
        row.removeFromLeft (8);
        genReportButton.setBounds (row.removeFromLeft (150));
        area.removeFromTop (8);
        statusLabel.setBounds (area.removeFromTop (22));
        area.removeFromTop (6);
        log.setBounds (area);
    }

private:
    // ── paths ──────────────────────────────────────────────────────────────
    static juce::File outputDir()
    {
        return juce::File::getSpecialLocation (juce::File::userDesktopDirectory)
                   .getChildFile ("TsukiSynth_Renders");
    }

    /** The one true renderer. Search order: next to this executable
        (packaged layout), then the build-tree layout relative to the
        Standalone artefact. */
    static juce::File findCli()
    {
        const auto exe = juce::File::getSpecialLocation (
            juce::File::currentExecutableFile);
        auto sibling = exe.getSiblingFile ("TsukiSynthCLI.exe");
        if (sibling.existsAsFile())
            return sibling;
        // build tree: .../build/TsukiSynth_artefacts/Release/Standalone/x.exe
        //          -> .../build/TsukiSynthCLI_artefacts/Release/TsukiSynthCLI.exe
        auto buildTree = exe.getParentDirectory()   // Standalone
                             .getParentDirectory()  // Release
                             .getParentDirectory()  // TsukiSynth_artefacts
                             .getParentDirectory()  // build
                             .getChildFile ("TsukiSynthCLI_artefacts")
                             .getChildFile ("Release")
                             .getChildFile ("TsukiSynthCLI.exe");
        return buildTree;   // may not exist; caller checks
    }

    /** Walk up from the score to a repo checkout containing
        tools/verify_score.py; invalid File if not found. */
    static juce::File findRepoRoot (const juce::File& score)
    {
        auto dir = score.getParentDirectory();
        for (int depth = 0; depth < 12 && dir.isDirectory(); ++depth)
        {
            if (dir.getChildFile ("tools")
                    .getChildFile ("verify_score.py").existsAsFile())
                return dir;
            dir = dir.getParentDirectory();
        }
        return {};
    }

    juce::File reportFileFor (const juce::File& score) const
    {
        auto name = score.getFileName();
        if (name.endsWith (".score.json"))
            name = name.dropLastCharacters (11) + ".report.html";
        else
            name = score.getFileNameWithoutExtension() + ".report.html";
        return score.getSiblingFile (name);
    }

    // ── actions ────────────────────────────────────────────────────────────
    void chooseAndRender()
    {
        if (isThreadRunning())
        {
            appendLog (juce::String::fromUTF8 (
                "[已有工作執行中，請稍候]"));   // 已有工作執行中
            return;
        }
        chooser = std::make_unique<juce::FileChooser> (
            juce::String::fromUTF8 ("選擇 score.json"),
            lastScore.existsAsFile() ? lastScore.getParentDirectory()
                                     : juce::File(),
            "*.json");
        chooser->launchAsync (juce::FileBrowserComponent::openMode
                                  | juce::FileBrowserComponent::canSelectFiles,
                              [this] (const juce::FileChooser& fc)
        {
            const auto f = fc.getResult();
            if (f == juce::File())
                return;
            lastScore = f;
            pendingMode = Mode::render;
            startThread();
        });
    }

    void openReport()
    {
        if (! lastScore.existsAsFile())
        {
            appendLog (juce::String::fromUTF8 (
                "[尚未選擇 score，先渲染一次或產生報告]"));
            return;
        }
        const auto report = reportFileFor (lastScore);
        if (report.existsAsFile())
        {
            report.startAsProcess();
        }
        else
        {
            appendLog (juce::String::fromUTF8 (
                "[找不到報告檔：") + report.getFullPathName()
                + juce::String::fromUTF8 ("，可先按「產生報告」]"));
        }
    }

    void generateReport()
    {
        if (isThreadRunning())
        {
            appendLog (juce::String::fromUTF8 (
                "[已有工作執行中，請稍候]"));
            return;
        }
        if (! lastScore.existsAsFile())
        {
            appendLog (juce::String::fromUTF8 (
                "[尚未選擇 score，先按「載入 score 並渲染」]"));
            return;
        }
        pendingMode = Mode::report;
        startThread();
    }

    // ── worker ─────────────────────────────────────────────────────────────
    enum class Mode { render, report };
    Mode pendingMode = Mode::render;

    void run() override
    {
        const auto score = lastScore;
        juce::StringArray args;

        if (pendingMode == Mode::render)
        {
            const auto cli = findCli();
            if (! cli.existsAsFile())
            {
                appendLog (juce::String::fromUTF8 (
                    "[錯誤] 找不到 TsukiSynthCLI.exe（應與 Standalone 同資料夾）"));
                setStatus (juce::String::fromUTF8 ("渲染失敗"));
                return;
            }
            outputDir().createDirectory();
            args = { cli.getFullPathName(), score.getFullPathName(),
                     "--output", outputDir().getFullPathName() };
            setStatus (juce::String::fromUTF8 ("渲染中… ")
                       + score.getFileName());
        }
        else
        {
            const auto repo = findRepoRoot (score);
            if (repo == juce::File())
            {
                appendLog (juce::String::fromUTF8 (
                    "[錯誤] 此 score 不在 repo 內（找不到 tools/verify_score.py），無法產報告"));
                setStatus (juce::String::fromUTF8 ("產報告失敗"));
                return;
            }
            args = { "python",
                     repo.getChildFile ("tools")
                         .getChildFile ("verify_score.py").getFullPathName(),
                     "--html", score.getFullPathName() };
            setStatus (juce::String::fromUTF8 (
                "產生報告中…（含完整驗證，會花幾分鐘）"));
        }

        appendLog ("$ " + args.joinIntoString (" "));

        juce::ChildProcess child;
        if (! child.start (args))
        {
            appendLog (juce::String::fromUTF8 (
                "[錯誤] 無法啟動子程序（python 不在 PATH？）"));
            setStatus (juce::String::fromUTF8 ("失敗"));
            return;
        }

        char buf[2048];
        juce::String pendingText;
        while (child.isRunning() && ! threadShouldExit())
        {
            const int n = child.readProcessOutput (buf, sizeof (buf));
            if (n > 0)
                appendLog (juce::String::fromUTF8 (buf, n), false);
            else
                wait (100);
        }
        // drain what is left after exit
        for (int n = child.readProcessOutput (buf, sizeof (buf)); n > 0;
             n = child.readProcessOutput (buf, sizeof (buf)))
            appendLog (juce::String::fromUTF8 (buf, n), false);

        if (threadShouldExit())
        {
            child.kill();
            setStatus (juce::String::fromUTF8 ("已中斷"));
            return;
        }

        const auto exitCode = child.getExitCode();
        if (pendingMode == Mode::render)
        {
            setStatus (exitCode == 0
                ? juce::String::fromUTF8 ("渲染完成 → 桌面\\TsukiSynth_Renders")
                : juce::String::fromUTF8 ("渲染失敗 (exit ")
                    + juce::String (exitCode) + ")");
        }
        else
        {
            setStatus (exitCode == 0
                ? juce::String::fromUTF8 ("報告完成，按「開 HTML 報告」檢視")
                : juce::String::fromUTF8 ("產報告失敗 (exit ")
                    + juce::String (exitCode) + ")");
        }
    }

    // ── UI plumbing (all UI touches hop to the message thread) ────────────
    void appendLog (const juce::String& text, bool newline = true)
    {
        auto safeThis = juce::Component::SafePointer<ScoreConsole> (this);
        juce::MessageManager::callAsync ([safeThis, text, newline]
        {
            if (safeThis == nullptr)
                return;
            safeThis->log.moveCaretToEnd();
            safeThis->log.insertTextAtCaret (text + (newline ? "\n" : ""));
        });
    }

    void setStatus (const juce::String& text)
    {
        auto safeThis = juce::Component::SafePointer<ScoreConsole> (this);
        juce::MessageManager::callAsync ([safeThis, text]
        {
            if (safeThis != nullptr)
                safeThis->statusLabel.setText (text,
                                               juce::dontSendNotification);
        });
    }

    juce::TextButton renderButton, folderButton, reportButton, genReportButton;
    juce::Label statusLabel;
    juce::TextEditor log;
    std::unique_ptr<juce::FileChooser> chooser;
    juce::File lastScore;

    JUCE_DECLARE_NON_COPYABLE_WITH_LEAK_DETECTOR (ScoreConsole)
};
