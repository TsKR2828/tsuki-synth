#include "PluginEditor.h"
#include "Presets.h"
#include "BinaryData.h"

#include <array>

namespace
{
    constexpr int kW = 620;
    constexpr int kH = 920;

    constexpr float kUiFontScale = 1.2f;
    constexpr float fontSize (float base) { return base * kUiFontScale; }

    constexpr float kRotaryStart = juce::MathConstants<float>::pi * 1.25f;
    constexpr float kRotaryEnd   = juce::MathConstants<float>::pi * 2.75f;

    constexpr int kTitleH    = 64;
    constexpr int kPresetH   = 50;
    constexpr int kTabH      = 42;
    constexpr int kMacroH    = 104;
    constexpr int kEffectsH  = 126;
    constexpr int kDistH     = 82;
    constexpr int kAnalyzerH = 86;
    constexpr int kKeyboardH = 84;
    constexpr int kSidePad   = 16;

    constexpr int kKnobLabelH  = 18;
    constexpr int kFxLabelH    = 15;
    constexpr int kComboLabelH = 18;
    constexpr int kComboBoxH   = 30;
    constexpr int kPanelTitleH = 20;

#if JucePlugin_Build_Standalone
    constexpr bool kStandaloneBuild = true;
#else
    constexpr bool kStandaloneBuild = false;
#endif
}

// ========================================================================
//  Constructor
// ========================================================================
TsukiSynthEditor::TsukiSynthEditor (TsukiSynthProcessor& p)
    : AudioProcessorEditor (&p),
      proc (p),
      keyboard (p.keyboardState, juce::MidiKeyboardComponent::horizontalKeyboard),
      analyzerPanel (p.analyzerFifo, p.analyzerDryFifo)
{
    setLookAndFeel (&lnf);

    // -- Brand assets (SVG moon + embedded font) -------------------------
    moonPath = juce::Drawable::parseSVGPath (
        "M14 3 a8 8 0 1 0 0 14 a6 6 0 0 1 0 -14 z");
    wordmarkTypeface = juce::Typeface::createSystemTypefaceFor (
        BinaryData::IBMPlexSansSemiBold_ttf,
        BinaryData::IBMPlexSansSemiBold_ttfSize);

    // -- Keyboard --------------------------------------------------------
    keyboard.setColour (juce::MidiKeyboardComponent::whiteNoteColourId,     Clr::whiteKey);
    keyboard.setColour (juce::MidiKeyboardComponent::blackNoteColourId,     Clr::blackKey);
    keyboard.setColour (juce::MidiKeyboardComponent::keySeparatorLineColourId, juce::Colour (0x28000000));
    keyboard.setColour (juce::MidiKeyboardComponent::shadowColourId,        juce::Colour (0x30000000));
    keyboard.setColour (juce::MidiKeyboardComponent::keyDownOverlayColourId, Clr::gold.withAlpha (0.35f));
    // Use scientific pitch notation: middle C = MIDI 60 = "C4" (matches tuner display)
    keyboard.setOctaveForMiddleC (4);
    addAndMakeVisible (keyboard);

    // -- Tab buttons -----------------------------------------------------
    auto initTab = [this] (juce::TextButton& btn, int idx)
    {
        btn.setComponentID ("tab");
        btn.setClickingTogglesState (true);
        btn.setRadioGroupId (1001);
        btn.onClick = [this, idx]
        {
            auto* param = proc.apvts.getParameter ("engine");
            param->beginChangeGesture();
            param->setValueNotifyingHost (param->convertTo0to1 ((float) idx));
            param->endChangeGesture();
        };
        addAndMakeVisible (btn);
    };
    initTab (tabCim, 0);
    initTab (tabChr, 1);
    initTab (tabFM,  2);

    // -- Language toggle -------------------------------------------------
    langToggle.setComponentID ("step");
    langToggle.setButtonText (UiLocale::toggleLabel());
    langToggle.onClick = [this]
    {
        if (UiLocale::isChinese())
            UiLocale::setLanguage (UiLanguage::English);
        else
            UiLocale::setLanguage (UiLanguage::Chinese);
        langToggle.setButtonText (UiLocale::toggleLabel());
        refreshLocalizedText();
        repaint();
    };
    addAndMakeVisible (langToggle);

    // -- Standalone recorder --------------------------------------------
    recordButton.setComponentID ("step");
    recordButton.onClick = [this]
    {
        if (proc.isRecording())
        {
            proc.stopRecording();
            auto file = proc.getLastRecordingFile();
            auto prefix = UiLocale::isChinese()
                            ? juce::String (juce::CharPointer_UTF8 ("存檔位置：\n"))
                            : juce::String ("Saved to:\n");

            if (file.existsAsFile())
                juce::AlertWindow::showMessageBoxAsync (
                    juce::AlertWindow::InfoIcon,
                    UiLocale::label ("ui_record_saved"),
                    prefix + file.getFullPathName(),
                    UiLocale::isChinese() ? juce::String (juce::CharPointer_UTF8 ("好")) : juce::String ("OK"),
                    this);
        }
        else
        {
            if (! proc.startRecording())
            {
                auto detail = proc.getRecordingStatus();
                juce::AlertWindow::showMessageBoxAsync (
                    juce::AlertWindow::WarningIcon,
                    UiLocale::label ("ui_record_failed"),
                    detail.isNotEmpty() ? detail : UiLocale::label ("ui_record_failed"),
                    UiLocale::isChinese() ? juce::String (juce::CharPointer_UTF8 ("好")) : juce::String ("OK"),
                    this);
            }
        }

        refreshRecorderText();
    };
    recordButton.setVisible (kStandaloneBuild);
    if (kStandaloneBuild)
        addAndMakeVisible (recordButton);

    // -- Preset ----------------------------------------------------------
    presetCombo.setColour (juce::ComboBox::backgroundColourId, Clr::comboBg);
    presetCombo.setColour (juce::ComboBox::outlineColourId,    Clr::comboBorder);
    presetCombo.setColour (juce::ComboBox::textColourId,       Clr::goldLight);
    rebuildPresetCombo();
    presetCombo.onChange = [this]
    {
        int id = presetCombo.getSelectedId();
        if (id > 0 && id <= (int) presetIdToIndex.size())
            proc.setCurrentProgram (presetIdToIndex[(size_t) (id - 1)]);
        updateDirtyIndicator();
    };
    addAndMakeVisible (presetCombo);

    presetPrev.setComponentID ("step");
    presetPrev.setButtonText ("<");
    presetPrev.onClick = [this]
    {
        int cur = presetCombo.getSelectedId();
        int n   = presetCombo.getNumItems();
        presetCombo.setSelectedId (cur > 1 ? cur - 1 : n);
    };
    addAndMakeVisible (presetPrev);

    presetNext.setComponentID ("step");
    presetNext.setButtonText (">");
    presetNext.onClick = [this]
    {
        int cur = presetCombo.getSelectedId();
        int n   = presetCombo.getNumItems();
        presetCombo.setSelectedId (cur < n ? cur + 1 : 1);
    };
    addAndMakeVisible (presetNext);

    presetSave.setComponentID ("step");
    presetSave.onClick = [this] { promptSavePreset(); };
    addAndMakeVisible (presetSave);

    presetInit.setComponentID ("step");
    presetInit.onClick = [this]
    {
        proc.presetManager.initPreset();
        rebuildPresetCombo();
        updateDirtyIndicator();
    };
    addAndMakeVisible (presetInit);

    dirtyLabel.setText ("", juce::dontSendNotification);
    dirtyLabel.setFont (juce::Font (juce::FontOptions (fontSize (14.0f))).boldened());
    dirtyLabel.setColour (juce::Label::textColourId, Clr::gold);
    dirtyLabel.setJustificationType (juce::Justification::centred);
    addAndMakeVisible (dirtyLabel);

    // -- Cimbalom --------------------------------------------------------
    setupCombo (cimMaterial, "cim_material");
    setupCombo (cimHammer,   "cim_hammer");
    setupKnob  (cimStrike,   "cim_strike_pos");
    setupKnob  (cimDiameter, "cim_diameter");
    setupKnob  (cimStrings,  "cim_num_strings");
    setupKnob  (cimDetune,   "cim_detuning");

    // -- Chromatic -------------------------------------------------------
    setupCombo (chrSubEngine, "chr_sub_engine");
    setupCombo (chrMaterial,  "chr_material");
    setupCombo (chrExciter,   "chr_exciter");
    setupKnob  (chrStrike,    "chr_strike_pos");
    setupKnob  (chrThickness, "chr_thickness");
    setupKnob  (chrSize,      "chr_size");
    setupKnob  (chrGlide,     "chr_pitch_glide");

    // -- FM Piano --------------------------------------------------------
    setupCombo (fmType,       "fm_type");
    setupKnob  (fmRatio,      "fm_ratio");
    setupKnob  (fmIndex,      "fm_index");
    setupKnob  (fmBrightness, "fm_brightness");
    setupKnob  (fmFeedback,   "fm_feedback");
    setupKnob  (fmAttack,     "fm_attack");
    setupKnob  (fmRelease,    "fm_release");

    // -- Effects ---------------------------------------------------------
    setupKnob (fxRevMix,      "fx_reverb_mix",      true);
    setupKnob (fxRevSize,     "fx_reverb_size",     true);
    setupKnob (fxDlyTime,     "fx_delay_time",      true);
    setupKnob (fxDlyFeedback, "fx_delay_feedback",  true);
    setupKnob (fxDlyMix,      "fx_delay_mix",       true);
    setupKnob (fxCompThresh,  "fx_comp_threshold",  true);
    setupKnob (fxCompRatio,   "fx_comp_ratio",      true);

    // -- Distortion ------------------------------------------------------
    setupCombo (distType,        "fx_dist_type");
    setupKnob  (distDrive,       "fx_dist_drive",        true);
    setupKnob  (distInstability, "fx_dist_instability",   true);
    setupKnob  (distMix,         "fx_dist_mix",           true);

    // -- Macro -----------------------------------------------------------
    setupKnob (macroMaterial,   "macro_material",   true);
    setupKnob (macroTension,    "macro_tension",    true);
    setupKnob (macroDamping,    "macro_damping",    true);
    setupKnob (macroStrike,     "macro_strike",     true);
    setupKnob (macroBrightness, "macro_brightness", true);
    setupKnob (macroBody,       "macro_body",       true);
    setupKnob (macroNoise,      "macro_noise",      true);
    setupKnob (macroOutput,     "macro_output",     true);

    // -- Analyzer --------------------------------------------------------
    addAndMakeVisible (analyzerPanel);
    analyzerPanel.setActive (true);
    analyzerPanel.setSampleRate (proc.getSampleRate() > 0.0 ? proc.getSampleRate() : 44100.0);
    analyzerPanel.refreshText();

    // -- Engine listener + initial state ---------------------------------
    proc.apvts.addParameterListener ("engine", this);
    updateEngine();
    refreshLocalizedText();
    updateDirtyIndicator();
    // 20Hz matches analyzer/tuner tick rate so sample-rate sync is never more
    // than one tuner tick stale even if host changes SR mid-session
    startTimerHz (20);
    setResizable (true, true);
    setResizeLimits (540, 820, 1100, 1400);
    setSize (kW, kH);
}

TsukiSynthEditor::~TsukiSynthEditor()
{
    stopTimer();
    setLookAndFeel (nullptr);
    proc.apvts.removeParameterListener ("engine", this);
}

// ========================================================================
//  Engine switching
// ========================================================================
void TsukiSynthEditor::parameterChanged (const juce::String& id, float)
{
    if (id == "engine")
    {
        auto safeThis = juce::Component::SafePointer<TsukiSynthEditor> (this);
        juce::MessageManager::callAsync ([safeThis]
        {
            if (safeThis != nullptr)
            {
                safeThis->updateEngine();
                safeThis->resized();
                safeThis->repaint();
            }
        });
    }
}

void TsukiSynthEditor::timerCallback()
{
    updateDirtyIndicator();
    refreshRecorderText();

    double sr = proc.getSampleRate();
    if (sr > 0.0)
        analyzerPanel.setSampleRate (sr);
}

int TsukiSynthEditor::currentEngine() const
{
    return (int) proc.apvts.getRawParameterValue ("engine")->load();
}

juce::Colour TsukiSynthEditor::accentForEngine (int eng) const
{
    switch (eng)
    {
        case 0:  return Clr::cimbalom;
        case 1:  return Clr::chromatic;
        case 2:  return Clr::fm;
        default: return Clr::gold;
    }
}

void TsukiSynthEditor::updateEngine()
{
    int eng = currentEngine();
    lnf.accent = accentForEngine (eng);

    tabCim.setToggleState (eng == 0, juce::dontSendNotification);
    tabChr.setToggleState (eng == 1, juce::dontSendNotification);
    tabFM.setToggleState  (eng == 2, juce::dontSendNotification);

    bool isCim = (eng == 0), isChr = (eng == 1), isFM = (eng == 2);

    setVisible (cimMaterial, isCim);  setVisible (cimHammer,   isCim);
    setVisible (cimStrike,   isCim);  setVisible (cimDiameter, isCim);
    setVisible (cimStrings,  isCim);  setVisible (cimDetune,   isCim);

    setVisible (chrSubEngine, isChr); setVisible (chrMaterial,  isChr);
    setVisible (chrExciter,   isChr); setVisible (chrStrike,    isChr);
    setVisible (chrThickness, isChr); setVisible (chrSize,      isChr);
    setVisible (chrGlide,     isChr);

    setVisible (fmType,       isFM);  setVisible (fmRatio,      isFM);
    setVisible (fmIndex,      isFM);  setVisible (fmBrightness, isFM);
    setVisible (fmFeedback,   isFM);  setVisible (fmAttack,     isFM);
    setVisible (fmRelease,    isFM);

    keyboard.setColour (juce::MidiKeyboardComponent::keyDownOverlayColourId,
                        lnf.accent.withAlpha (0.35f));
    analyzerPanel.setAccent (lnf.accent);

    // Keyboard range indicator — highlight each engine's "sweet spot"
    switch (eng)
    {
        case 0:  keyboard.setRangeIndicator (36, 96, Clr::cimbalom);  break;  // C2–C7
        case 1:  keyboard.setRangeIndicator (48, 84, Clr::chromatic); break;  // C3–C6
        case 2:  keyboard.setRangeIndicator (24, 96, Clr::fm);       break;  // C1–C7
        default: break;
    }

    rebuildPresetCombo();
}

// ========================================================================
//  Setup helpers
// ========================================================================
void TsukiSynthEditor::setupKnob (KnobParam& k, const juce::String& paramID,
                                    bool small)
{
    k.paramID = paramID;

    auto& s = k.slider;
    s.setSliderStyle (juce::Slider::RotaryVerticalDrag);
    s.setTextBoxStyle (juce::Slider::TextBoxBelow, true,
                       small ? 54 : 70, small ? 18 : 21);
    s.setRotaryParameters ({ kRotaryStart, kRotaryEnd, true });
    s.setColour (juce::Slider::textBoxTextColourId,       Clr::valueText);
    s.setColour (juce::Slider::textBoxBackgroundColourId, juce::Colours::transparentBlack);
    s.setColour (juce::Slider::textBoxOutlineColourId,    juce::Colours::transparentBlack);
    addAndMakeVisible (s);

    auto& l = k.label;
    l.setText (UiLocale::label (paramID), juce::dontSendNotification);
    l.setFont (juce::Font (juce::FontOptions (fontSize (small ? 8.0f : 9.5f))).boldened());
    l.setJustificationType (juce::Justification::centred);
    l.setColour (juce::Label::textColourId, small ? Clr::fxTitle : Clr::label);
    addAndMakeVisible (l);

    k.attachment = std::make_unique<SliderAttachment> (proc.apvts, paramID, s);
}

void TsukiSynthEditor::setupCombo (ComboParam& c, const juce::String& paramID)
{
    c.paramID = paramID;

    // Populate items: use UiLocale if available, else APVTS choices
    auto localizedItems = UiLocale::comboItems (paramID);

    if (localizedItems.isEmpty())
    {
        if (auto* cp = dynamic_cast<juce::AudioParameterChoice*> (
                proc.apvts.getParameter (paramID)))
        {
            int id = 1;
            for (const auto& choice : cp->choices)
                c.combo.addItem (choice, id++);
        }
    }
    else
    {
        int id = 1;
        for (const auto& item : localizedItems)
            c.combo.addItem (item, id++);
    }

    addAndMakeVisible (c.combo);

    c.label.setText (UiLocale::label (paramID), juce::dontSendNotification);
    c.label.setFont (juce::Font (juce::FontOptions (fontSize (9.0f))).boldened());
    c.label.setJustificationType (juce::Justification::centred);
    c.label.setColour (juce::Label::textColourId, Clr::label);
    addAndMakeVisible (c.label);

    c.attachment = std::make_unique<ComboAttachment> (proc.apvts, paramID, c.combo);
}

void TsukiSynthEditor::setVisible (KnobParam& k, bool v)
{
    k.slider.setVisible (v);
    k.label.setVisible (v);
}

void TsukiSynthEditor::setVisible (ComboParam& c, bool v)
{
    c.combo.setVisible (v);
    c.label.setVisible (v);
}

// ========================================================================
//  Localization
// ========================================================================
void TsukiSynthEditor::refreshComboItems (ComboParam& cp)
{
    auto items = UiLocale::comboItems (cp.paramID);

    // If UiLocale has no items for this param, use APVTS choices
    if (items.isEmpty())
    {
        if (auto* p = dynamic_cast<juce::AudioParameterChoice*> (
                proc.apvts.getParameter (cp.paramID)))
            items = p->choices;
    }

    if (items.isEmpty())
        return;

    int currentId = cp.combo.getSelectedId();
    cp.combo.clear (juce::dontSendNotification);

    int id = 1;
    for (const auto& item : items)
        cp.combo.addItem (item, id++);

    if (currentId > 0 && currentId <= items.size())
        cp.combo.setSelectedId (currentId, juce::dontSendNotification);
}

void TsukiSynthEditor::refreshLocalizedText()
{
    // Helper lambdas
    auto refreshKnobLabel = [] (KnobParam& k)
    {
        k.label.setText (UiLocale::label (k.paramID), juce::dontSendNotification);
    };
    auto refreshComboLabel = [this] (ComboParam& c)
    {
        c.label.setText (UiLocale::label (c.paramID), juce::dontSendNotification);
        refreshComboItems (c);
    };

    // -- Macro knobs --
    refreshKnobLabel (macroMaterial);
    refreshKnobLabel (macroTension);
    refreshKnobLabel (macroDamping);
    refreshKnobLabel (macroStrike);
    refreshKnobLabel (macroBrightness);
    refreshKnobLabel (macroBody);
    refreshKnobLabel (macroNoise);
    refreshKnobLabel (macroOutput);

    // -- Cimbalom --
    refreshComboLabel (cimMaterial);
    refreshComboLabel (cimHammer);
    refreshKnobLabel  (cimStrike);
    refreshKnobLabel  (cimDiameter);
    refreshKnobLabel  (cimStrings);
    refreshKnobLabel  (cimDetune);

    // -- Chromatic --
    refreshComboLabel (chrSubEngine);
    refreshComboLabel (chrMaterial);
    refreshComboLabel (chrExciter);
    refreshKnobLabel  (chrStrike);
    refreshKnobLabel  (chrThickness);
    refreshKnobLabel  (chrSize);
    refreshKnobLabel  (chrGlide);

    // -- FM Piano --
    refreshComboLabel (fmType);
    refreshKnobLabel  (fmRatio);
    refreshKnobLabel  (fmIndex);
    refreshKnobLabel  (fmBrightness);
    refreshKnobLabel  (fmFeedback);
    refreshKnobLabel  (fmAttack);
    refreshKnobLabel  (fmRelease);

    // -- Effects --
    refreshKnobLabel (fxRevMix);
    refreshKnobLabel (fxRevSize);
    refreshKnobLabel (fxDlyTime);
    refreshKnobLabel (fxDlyFeedback);
    refreshKnobLabel (fxDlyMix);
    refreshKnobLabel (fxCompThresh);
    refreshKnobLabel (fxCompRatio);

    // -- Distortion --
    refreshComboLabel (distType);
    refreshKnobLabel  (distDrive);
    refreshKnobLabel  (distInstability);
    refreshKnobLabel  (distMix);

    // -- Tabs / buttons / presets --
    tabCim.setButtonText (UiLocale::label ("ui_tab_cimbalom"));
    tabChr.setButtonText (UiLocale::label ("ui_tab_chromatic"));
    tabFM .setButtonText (UiLocale::label ("ui_tab_fm"));
    presetSave.setButtonText (UiLocale::label ("ui_btn_save"));
    presetInit.setButtonText (UiLocale::label ("ui_btn_init"));
    langToggle.setButtonText (UiLocale::toggleLabel());
    refreshRecorderText();
    rebuildPresetCombo();
    analyzerPanel.refreshText();
    keyboard.repaint();

    repaint();
}

void TsukiSynthEditor::refreshRecorderText()
{
    if (! kStandaloneBuild)
        return;

    recordButton.setButtonText (UiLocale::label (proc.isRecording() ? "ui_btn_stop" : "ui_btn_rec"));
    auto status = proc.getRecordingStatus();
    if (status.isNotEmpty())
        recordButton.setTooltip (status);
}

// ========================================================================
//  Preset helpers
// ========================================================================
void TsukiSynthEditor::rebuildPresetCombo()
{
    presetCombo.clear (juce::dontSendNotification);
    presetIdToIndex.clear();

    int eng = currentEngine();
    auto& pm = proc.presetManager;

    int nFactory = pm.getNumFactoryPresets();
    int nUser    = pm.getNumUserPresets();
    int fc = 0;
    auto* factoryList = getFactoryPresetList (fc);

    int comboId = 1;
    for (int i = 0; i < nFactory; ++i)
    {
        if (getPresetEngine (factoryList[i]) != eng)
            continue;
        presetCombo.addItem (UiLocale::presetName (pm.getPresetName (i)), comboId);
        presetIdToIndex.push_back (i);
        ++comboId;
    }

    if (nUser > 0)
    {
        presetCombo.addSeparator();
        for (int i = 0; i < nUser; ++i)
        {
            presetCombo.addItem (pm.getPresetName (nFactory + i), comboId);
            presetIdToIndex.push_back (nFactory + i);
            ++comboId;
        }
    }

    int cur = pm.getCurrentIndex();
    for (int c = 0; c < (int) presetIdToIndex.size(); ++c)
    {
        if (presetIdToIndex[(size_t) c] == cur)
        {
            presetCombo.setSelectedId (c + 1, juce::dontSendNotification);
            break;
        }
    }
}

void TsukiSynthEditor::updateDirtyIndicator()
{
    dirtyLabel.setText (proc.presetManager.isDirty() ? "*" : "",
                        juce::dontSendNotification);
}

void TsukiSynthEditor::promptSavePreset()
{
    auto* aw = new juce::AlertWindow (UiLocale::label ("ui_save_title"),
                                       UiLocale::label ("ui_save_prompt"),
                                       juce::AlertWindow::NoIcon, this);
    aw->addTextEditor ("name", "My Preset", UiLocale::label ("ui_save_field"));
    aw->addButton (UiLocale::label ("ui_btn_save"),   1);
    aw->addButton (UiLocale::label ("ui_btn_cancel"), 0);

    aw->enterModalState (true, juce::ModalCallbackFunction::create (
        [this, aw] (int result)
        {
            if (result == 1)
            {
                auto name = aw->getTextEditorContents ("name").trim();
                if (name.isNotEmpty())
                {
                    proc.presetManager.saveUserPreset (name);
                    rebuildPresetCombo();
                    updateDirtyIndicator();
                }
            }
            delete aw;
        }));
}

// ========================================================================
//  Layout helpers
// ========================================================================
void TsukiSynthEditor::layoutKnobCell (juce::Rectangle<int> cell, KnobParam& k)
{
    auto c = cell.reduced (0, 1);
    k.label.setBounds (c.removeFromTop (kKnobLabelH));
    k.slider.setBounds (c.withSizeKeepingCentre (juce::jmin (58, c.getWidth()), c.getHeight()));
}

void TsukiSynthEditor::layoutComboCell (juce::Rectangle<int> cell, ComboParam& p)
{
    auto c = cell.reduced (10, 1);
    p.label.setBounds (c.removeFromTop (kComboLabelH));
    c.removeFromTop (4);
    p.combo.setBounds (c.removeFromTop (kComboBoxH));
}

void TsukiSynthEditor::layoutFxKnob (juce::Rectangle<int> cell, KnobParam& k)
{
    auto c = cell.reduced (2, 0);
    k.label.setBounds (c.removeFromTop (kFxLabelH));
    k.slider.setBounds (c.withSizeKeepingCentre (juce::jmin (44, c.getWidth()), c.getHeight()));
}

// ========================================================================
//  Paint
// ========================================================================
void TsukiSynthEditor::paintPanel (juce::Graphics& g, juce::Rectangle<int> bounds,
                                     const juce::String& title)
{
    g.setColour (Clr::panelBg);
    g.fillRoundedRectangle (bounds.toFloat(), 5.0f);
    g.setColour (Clr::effectBorder);
    g.drawRoundedRectangle (bounds.toFloat().reduced (0.5f), 5.0f, 0.5f);

    g.setColour (Clr::fxTitle);
    g.setFont (juce::Font (juce::FontOptions (fontSize (9.0f))).boldened());
    g.drawText (title, bounds.getX() + 8, bounds.getY() + 6,
                bounds.getWidth() - 16, kPanelTitleH, juce::Justification::centredLeft);
}

void TsukiSynthEditor::paint (juce::Graphics& g)
{
    // -- plugin background gradient --------------------------------------
    g.setGradientFill (juce::ColourGradient (
        Clr::pluginTop, 0.0f, 0.0f,
        Clr::pluginBot, 0.0f, (float) getHeight(), false));
    g.fillAll();

    int w = getWidth();

    // -- title bar -------------------------------------------------------
    {
        constexpr int padT = 16;
        constexpr int padL = 20;
        constexpr int moonSize = 18;
        constexpr int moonDy = 2;
        constexpr int moonToWord = 8;
        constexpr int wordToSub = 4;
        constexpr int wordH = 22;
        constexpr int subH = 18;
        constexpr int wordX = padL + moonSize + moonToWord;
        constexpr int subY = padT + wordH + wordToSub;

        g.setGradientFill (juce::ColourGradient (
            juce::Colour (0x04ffffff), 0.0f, 0.0f,
            juce::Colours::transparentBlack, 0.0f, (float) kTitleH, false));
        g.fillRect (0, 0, w, kTitleH);

        {
            auto scaled = moonPath;
            scaled.applyTransform (juce::AffineTransform::scale ((float) moonSize / 20.0f)
                                       .translated ((float) padL, (float) (padT + moonDy)));
            g.setColour (juce::Colour (0xffd4b896).withAlpha (0.95f));
            g.fillPath (scaled);
        }

        {
            auto wmFont = juce::Font (juce::FontOptions ((float) wordH).withTypeface (wordmarkTypeface))
                              .withExtraKerningFactor (0.04f);
            juce::GlyphArrangement glyphs;
            float baseline = (float) padT + wmFont.getAscent();
            glyphs.addLineOfText (wmFont, "TsukiSynth", (float) wordX, baseline);

            juce::Path textPath;
            glyphs.createPath (textPath);
            g.setGradientFill (juce::ColourGradient (
                juce::Colour (0xfff0e8d8), 0.0f, (float) padT,
                juce::Colour (0xffc49a6c), 0.0f, (float) (padT + wordH), false));
            g.fillPath (textPath);
        }

        int eng = currentEngine();
        auto eName = eng == 0 ? juce::String ("CIMBALOM")
                   : eng == 1 ? juce::String ("CHROMATIC")
                   :            juce::String ("FM PIANO");
        auto eType = eng == 0 ? juce::String ("PHYSICAL MODELING STRING")
                   : eng == 1 ? juce::String ("BEAM / PLATE / CUSTOM")
                   :            juce::String ("FREQUENCY MODULATION");
        auto subFont = juce::Font (juce::FontOptions (fontSize (10.0f)).withTypeface (wordmarkTypeface))
                           .withExtraKerningFactor (0.12f);
        g.setFont (subFont);

        auto nameStr = eName + " ENGINE";
        int nameW = (int) juce::GlyphArrangement::getStringWidth (subFont, nameStr);

        g.setColour (juce::Colour (0xff8899aa));
        g.drawText (nameStr, padL, subY, nameW + 4, subH, juce::Justification::centredLeft);
        g.setColour (juce::Colour (0xff3a3a5a));
        g.drawText ("|", padL + nameW + 7, subY, 10, subH, juce::Justification::centred);
        g.setColour (juce::Colour (0xff667788));
        g.drawText (eType, padL + nameW + 24, subY, 300, subH, juce::Justification::centredLeft);

        // version number (right-aligned in title bar)
        auto verFont = juce::Font (juce::FontOptions (fontSize (8.5f)))
                           .withExtraKerningFactor (0.08f);
        g.setFont (verFont);
        g.setColour (juce::Colour (0xff556677));
        g.drawText ("v" JucePlugin_VersionString,
                     w - 70, subY, 60, subH, juce::Justification::centredRight);

        g.setColour (Clr::borderLight);
        g.drawHorizontalLine (kTitleH - 1, 0.0f, (float) w);
    }

    // -- preset row background -------------------------------------------
    {
        int y = kTitleH;
        g.setColour (Clr::presetBg);
        g.fillRect (0, y, w, kPresetH);
        g.setColour (Clr::borderLight);
        g.drawHorizontalLine (y + kPresetH - 1, 0.0f, (float) w);
    }

    // -- tabs background -------------------------------------------------
    {
        int y = kTitleH + kPresetH;
        g.setColour (Clr::presetBg);
        g.fillRect (0, y, w, kTabH);
    }

    // -- macro section ---------------------------------------------------
    {
        int y = macroArea_.getY();
        int h = macroArea_.getHeight();
        g.setGradientFill (juce::ColourGradient (
            Clr::engineTop, 0.0f, (float) y,
            Clr::engineBot, 0.0f, (float) (y + h), false));
        g.fillRect (0, y, w, h);
        g.setColour (Clr::borderLight);
        g.drawHorizontalLine (y, 0.0f, (float) w);

        g.setColour (Clr::divLabel);
        g.setFont (juce::Font (juce::FontOptions (fontSize (9.0f))).boldened()
                       .withExtraKerningFactor (0.2f));
        g.drawText (UiLocale::label ("ui_section_macro"), kSidePad, y + 4, 96, 20, juce::Justification::centredLeft);

        g.setColour (juce::Colour (0xff334455));
        g.setFont (juce::FontOptions (fontSize (9.0f)));
        g.drawText (UiLocale::paramCountText (8), kSidePad + 92, y + 4,
                    90, 20, juce::Justification::centredLeft);

        g.setColour (Clr::border.withAlpha (0.5f));
        g.fillRect (kSidePad + 184, y + 14, w - kSidePad * 2 - 184, 1);
    }

    // -- engine section --------------------------------------------------
    {
        int y = engineArea_.getY();
        int h = engineArea_.getHeight();
        g.setGradientFill (juce::ColourGradient (
            Clr::engineTop, 0.0f, (float) y,
            Clr::engineBot, 0.0f, (float) (y + h), false));
        g.fillRect (0, y, w, h);
        g.setColour (Clr::borderLight);
        g.drawHorizontalLine (y, 0.0f, (float) w);

        // divider label
        g.setColour (Clr::divLabel);
        g.setFont (juce::Font (juce::FontOptions (fontSize (9.0f))).boldened()
                       .withExtraKerningFactor (0.2f));
        g.drawText (UiLocale::label ("ui_section_engine"), kSidePad, y + 4, 104, 20, juce::Justification::centredLeft);

        int eng = currentEngine();
        int pc  = (eng == 0) ? 6 : 7;
        g.setColour (juce::Colour (0xff334455));
        g.setFont (juce::FontOptions (fontSize (9.0f)));
        g.drawText (UiLocale::paramCountText (pc), kSidePad + 112, y + 4,
                    90, 20, juce::Justification::centredLeft);

        // divider line
        g.setColour (Clr::border.withAlpha (0.5f));
        g.fillRect (kSidePad + 204, y + 14, w - kSidePad * 2 - 204, 1);
    }

    // -- effects section -------------------------------------------------
    {
        int y = effectsRow_.getY();
        int h = effectsRow_.getHeight();
        g.setColour (Clr::effectsBg);
        g.fillRect (0, y, w, h);
        g.setColour (Clr::borderLight);
        g.drawHorizontalLine (y, 0.0f, (float) w);

        g.setColour (Clr::divLabel);
        g.setFont (juce::Font (juce::FontOptions (fontSize (9.0f))).boldened()
                       .withExtraKerningFactor (0.2f));
        g.drawText (UiLocale::label ("ui_section_effects"), kSidePad, y + 4, 96, 20, juce::Justification::centredLeft);
        g.setColour (Clr::border.withAlpha (0.5f));
        g.fillRect (kSidePad + 104, y + 14, w - kSidePad * 2 - 104, 1);

        paintPanel (g, reverbBounds_, UiLocale::label ("ui_panel_reverb"));
        paintPanel (g, delayBounds_,  UiLocale::label ("ui_panel_delay"));
        paintPanel (g, compBounds_,   UiLocale::label ("ui_panel_compressor"));
    }

    // -- distortion row --------------------------------------------------
    {
        int y = distRow_.getY();
        g.setColour (Clr::effectsBg);
        g.fillRect (0, y, w, distRow_.getHeight());
        paintPanel (g, distPanelBounds_, UiLocale::label ("ui_panel_distortion"));
    }

    // -- analyzer row ----------------------------------------------------
    {
        int y = analyzerRow_.getY();
        g.setColour (Clr::effectsBg);
        g.fillRect (0, y, w, analyzerRow_.getHeight());
        g.setColour (Clr::borderLight);
        g.drawHorizontalLine (y, 0.0f, (float) w);
    }

    // -- keyboard footer -------------------------------------------------
    {
        int y = analyzerRow_.getBottom();
        g.setColour (Clr::kbFooter);
        g.fillRect (0, y, w, getHeight() - y);
        g.setColour (Clr::borderLight);
        g.drawHorizontalLine (y, 0.0f, (float) w);
    }
}

// ========================================================================
//  Resized -- top-to-bottom layout
// ========================================================================
void TsukiSynthEditor::resized()
{
    auto area = getLocalBounds();
    int w = area.getWidth();

    // -- title (paint only) + language toggle in title bar ----------------
    area.removeFromTop (kTitleH);
    langToggle.setBounds (w - 72, 20, 56, 24);
    if (kStandaloneBuild)
        recordButton.setBounds (w - 136, 20, 56, 24);

    // -- preset row ------------------------------------------------------
    {
        auto row   = area.removeFromTop (kPresetH);
        auto inner = row.reduced (kSidePad, 8);

        presetPrev.setBounds (inner.removeFromLeft (24).reduced (0, 1));
        inner.removeFromLeft (2);
        presetNext.setBounds (inner.removeFromLeft (24).reduced (0, 1));
        inner.removeFromLeft (6);

        presetInit.setBounds (inner.removeFromRight (58).reduced (0, 1));
        inner.removeFromRight (4);
        presetSave.setBounds (inner.removeFromRight (58).reduced (0, 1));
        inner.removeFromRight (4);
        dirtyLabel.setBounds (inner.removeFromRight (14));

        presetCombo.setBounds (inner);
    }

    // -- engine tabs -----------------------------------------------------
    {
        auto row   = area.removeFromTop (kTabH);
        auto inner = row.reduced (kSidePad, 0).withTrimmedTop (4);
        int tw = inner.getWidth() / 3;
        tabCim.setBounds (inner.removeFromLeft (tw));
        tabChr.setBounds (inner.removeFromLeft (tw));
        tabFM.setBounds  (inner);
    }

    // -- macro row -------------------------------------------------------
    macroArea_ = area.removeFromTop (kMacroH);
    {
        auto inner = macroArea_.reduced (kSidePad, 0).withTrimmedTop (26);
        int knobW = inner.getWidth() / 8;
        layoutFxKnob (inner.removeFromLeft (knobW), macroMaterial);
        layoutFxKnob (inner.removeFromLeft (knobW), macroTension);
        layoutFxKnob (inner.removeFromLeft (knobW), macroDamping);
        layoutFxKnob (inner.removeFromLeft (knobW), macroStrike);
        layoutFxKnob (inner.removeFromLeft (knobW), macroBrightness);
        layoutFxKnob (inner.removeFromLeft (knobW), macroBody);
        layoutFxKnob (inner.removeFromLeft (knobW), macroNoise);
        layoutFxKnob (inner, macroOutput);
    }

    // -- bottom sections (fixed sizes, from bottom up) -------------------
    auto kbArea = area.removeFromBottom (kKeyboardH);
    keyboard.setBounds (kbArea.reduced (14, 10));

    analyzerRow_ = area.removeFromBottom (kAnalyzerH);
    analyzerPanel.setBounds (analyzerRow_.reduced (kSidePad, 4));

    distRow_ = area.removeFromBottom (kDistH);
    {
        distPanelBounds_ = distRow_.reduced (kSidePad, 4);
        auto inner = distPanelBounds_.reduced (8, 0).withTrimmedTop (28);

        auto typeArea = inner.removeFromLeft (inner.getWidth() * 2 / 7);
        distType.label.setBounds (typeArea.removeFromTop (kComboLabelH));
        typeArea.removeFromTop (4);
        distType.combo.setBounds (typeArea.removeFromTop (kComboBoxH));

        inner.removeFromLeft (10);
        int knobW = inner.getWidth() / 3;
        layoutFxKnob (inner.removeFromLeft (knobW), distDrive);
        layoutFxKnob (inner.removeFromLeft (knobW), distInstability);
        layoutFxKnob (inner, distMix);
    }

    effectsRow_ = area.removeFromBottom (kEffectsH);
    {
        auto inner = effectsRow_.reduced (kSidePad, 0).withTrimmedTop (30);
        int gap   = 8;
        int avail = inner.getWidth() - gap * 2;
        int revW  = avail * 29 / 100;
        int dlyW  = avail * 40 / 100;
        int cmpW  = avail - revW - dlyW;

        reverbBounds_ = inner.removeFromLeft (revW);
        inner.removeFromLeft (gap);
        delayBounds_ = inner.removeFromLeft (dlyW);
        inner.removeFromLeft (gap);
        compBounds_ = inner.withWidth (cmpW);

        // reverb knobs
        {
            auto p = reverbBounds_.reduced (6, 0).withTrimmedTop (28);
            int kw = p.getWidth() / 2;
            layoutFxKnob (p.removeFromLeft (kw), fxRevMix);
            layoutFxKnob (p, fxRevSize);
        }
        // delay knobs
        {
            auto p = delayBounds_.reduced (6, 0).withTrimmedTop (28);
            int kw = p.getWidth() / 3;
            layoutFxKnob (p.removeFromLeft (kw), fxDlyTime);
            layoutFxKnob (p.removeFromLeft (kw), fxDlyFeedback);
            layoutFxKnob (p, fxDlyMix);
        }
        // compressor knobs
        {
            auto p = compBounds_.reduced (6, 0).withTrimmedTop (28);
            int kw = p.getWidth() / 2;
            layoutFxKnob (p.removeFromLeft (kw), fxCompThresh);
            layoutFxKnob (p, fxCompRatio);
        }
    }

    // -- engine section (remaining space) --------------------------------
    engineArea_ = area;
    {
        auto inner = engineArea_.reduced (kSidePad, 0).withTrimmedTop (30);
        int eng = currentEngine();

        int numRows = 3;
        int gap     = 8;
        int rowH    = (inner.getHeight() - (numRows - 1) * gap) / numRows;
        int colGap  = 16;

        auto takeRow = [&]() -> juce::Rectangle<int>
        {
            auto row  = inner.removeFromTop (rowH);
            inner.removeFromTop (gap);
            return row;
        };

        auto splitTwo = [colGap] (juce::Rectangle<int> row)
            -> std::pair<juce::Rectangle<int>, juce::Rectangle<int>>
        {
            int colW = (row.getWidth() - colGap) / 2;
            auto left = row.removeFromLeft (colW);
            row.removeFromLeft (colGap);
            auto right = row.withWidth (colW);
            return { left, right };
        };

        auto splitThree = [] (juce::Rectangle<int> row)
            -> std::array<juce::Rectangle<int>, 3>
        {
            constexpr int threeGap = 12;
            int colW = (row.getWidth() - threeGap * 2) / 3;
            auto left = row.removeFromLeft (colW);
            row.removeFromLeft (threeGap);
            auto mid = row.removeFromLeft (colW);
            row.removeFromLeft (threeGap);
            auto right = row.withWidth (colW);
            return { left, mid, right };
        };

        if (eng == 0)
        {
            auto [l0, r0] = splitTwo (takeRow());
            layoutComboCell (l0, cimMaterial);
            layoutComboCell (r0, cimHammer);

            auto [l1, r1] = splitTwo (takeRow());
            layoutKnobCell (l1, cimStrike);
            layoutKnobCell (r1, cimDiameter);

            auto [l2, r2] = splitTwo (takeRow());
            layoutKnobCell (l2, cimStrings);
            layoutKnobCell (r2, cimDetune);
        }
        else if (eng == 1)
        {
            auto [l0, r0] = splitTwo (takeRow());
            layoutComboCell (l0, chrMaterial);
            layoutComboCell (r0, chrSubEngine);

            auto [c0, c1, c2] = splitThree (takeRow());
            layoutKnobCell (c0, chrThickness);
            layoutKnobCell (c1, chrSize);
            layoutKnobCell (c2, chrGlide);

            auto [l2, r2] = splitTwo (takeRow());
            layoutKnobCell (l2, chrStrike);
            layoutComboCell (r2, chrExciter);
        }
        else
        {
            layoutComboCell (takeRow(), fmType);

            auto [c0, c1, c2] = splitThree (takeRow());
            layoutKnobCell (c0, fmRatio);
            layoutKnobCell (c1, fmIndex);
            layoutKnobCell (c2, fmBrightness);

            auto [c3, c4, c5] = splitThree (takeRow());
            layoutKnobCell (c3, fmFeedback);
            layoutKnobCell (c4, fmAttack);
            layoutKnobCell (c5, fmRelease);
        }
    }
}
