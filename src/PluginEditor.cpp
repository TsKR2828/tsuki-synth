#include "PluginEditor.h"
#include "Presets.h"
#include "BinaryData.h"

namespace
{
    constexpr int kW = 540;
    constexpr int kH = 850;

    constexpr float kRotaryStart = juce::MathConstants<float>::pi * 1.25f;
    constexpr float kRotaryEnd   = juce::MathConstants<float>::pi * 2.75f;

    constexpr int kTitleH    = 64;
    constexpr int kPresetH   = 44;
    constexpr int kTabH      = 36;
    constexpr int kMacroH    = 90;
    constexpr int kEffectsH  = 108;
    constexpr int kDistH      = 70;
    constexpr int kAnalyzerH  = 80;
    constexpr int kKeyboardH  = 80;
    constexpr int kSidePad   = 16;
}

// ========================================================================
//  Constructor
// ========================================================================
TsukiSynthEditor::TsukiSynthEditor (TsukiSynthProcessor& p)
    : AudioProcessorEditor (&p),
      proc (p),
      keyboard (p.keyboardState, juce::MidiKeyboardComponent::horizontalKeyboard),
      presetBrowser (p.presetManager),
      harmonicEditor (p.apvts),
      analyzerPanel (p.analyzerFifo)
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

    // -- Preset ----------------------------------------------------------
    presetNameBtn.onClick = [this] { showPresetBrowser(); };
    updatePresetName();
    addAndMakeVisible (presetNameBtn);

    presetBrowser.onPresetSelected = [this] (int index)
    {
        proc.setCurrentProgram (index);
        updatePresetName();
        updateDirtyIndicator();
        hidePresetBrowser();
    };
    addChildComponent (presetBrowser);

    presetPrev.setComponentID ("step");
    presetPrev.setButtonText ("<");
    presetPrev.onClick = [this]
    {
        auto& pm = proc.presetManager;
        int cur = pm.getCurrentIndex();
        int n   = pm.getNumPresets();
        proc.setCurrentProgram (cur > 0 ? cur - 1 : n - 1);
        updatePresetName();
        updateDirtyIndicator();
    };
    addAndMakeVisible (presetPrev);

    presetNext.setComponentID ("step");
    presetNext.setButtonText (">");
    presetNext.onClick = [this]
    {
        auto& pm = proc.presetManager;
        int cur = pm.getCurrentIndex();
        int n   = pm.getNumPresets();
        proc.setCurrentProgram (cur < n - 1 ? cur + 1 : 0);
        updatePresetName();
        updateDirtyIndicator();
    };
    addAndMakeVisible (presetNext);

    presetSave.setComponentID ("step");
    presetSave.onClick = [this] { promptSavePreset(); };
    addAndMakeVisible (presetSave);

    presetInit.setComponentID ("step");
    presetInit.onClick = [this]
    {
        proc.presetManager.initPreset();
        updatePresetName();
        updateDirtyIndicator();
    };
    addAndMakeVisible (presetInit);

    dirtyLabel.setText ("", juce::dontSendNotification);
    dirtyLabel.setFont (juce::Font (juce::FontOptions (14.0f)).boldened());
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
    analyzerPanel.setSampleRate (proc.getSampleRate());

    // -- Engine listener + initial state ---------------------------------
    addChildComponent (harmonicEditor);
    proc.apvts.addParameterListener ("engine", this);
    proc.apvts.addParameterListener ("chr_sub_engine", this);
    updateEngine();
    updateDirtyIndicator();
    startTimerHz (5);
    setResizable (true, true);
    setResizeLimits (420, 700, 900, 1200);
    setSize (kW, kH);
}

TsukiSynthEditor::~TsukiSynthEditor()
{
    stopTimer();
    setLookAndFeel (nullptr);
    proc.apvts.removeParameterListener ("engine", this);
    proc.apvts.removeParameterListener ("chr_sub_engine", this);
}

// ========================================================================
//  Engine switching
// ========================================================================
void TsukiSynthEditor::parameterChanged (const juce::String& id, float)
{
    if (id == "engine" || id == "chr_sub_engine")
        juce::MessageManager::callAsync ([this] { updateEngine(); resized(); repaint(); });
}

void TsukiSynthEditor::timerCallback()
{
    updateDirtyIndicator();
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

    bool showHarmonic = isChr && (int) proc.apvts.getRawParameterValue ("chr_sub_engine")->load() == 2;
    harmonicEditor.setVisible (showHarmonic);

    setVisible (fmType,       isFM);  setVisible (fmRatio,      isFM);
    setVisible (fmIndex,      isFM);  setVisible (fmBrightness, isFM);
    setVisible (fmFeedback,   isFM);  setVisible (fmAttack,     isFM);
    setVisible (fmRelease,    isFM);

    keyboard.setColour (juce::MidiKeyboardComponent::keyDownOverlayColourId,
                        lnf.accent.withAlpha (0.35f));
    analyzerPanel.setAccent (lnf.accent);
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
                       small ? 42 : 54, small ? 11 : 14);
    s.setRotaryParameters ({ kRotaryStart, kRotaryEnd, true });
    s.setColour (juce::Slider::textBoxTextColourId,       Clr::valueText);
    s.setColour (juce::Slider::textBoxBackgroundColourId, juce::Colours::transparentBlack);
    s.setColour (juce::Slider::textBoxOutlineColourId,    juce::Colours::transparentBlack);
    addAndMakeVisible (s);

    auto& l = k.label;
    l.setText (UiLocale::label (paramID), juce::dontSendNotification);
    l.setFont (juce::Font (juce::FontOptions (small ? 8.0f : 9.5f)).boldened());
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
    c.label.setFont (juce::Font (juce::FontOptions (9.0f)).boldened());
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
}

// ========================================================================
//  Preset helpers
// ========================================================================
void TsukiSynthEditor::updatePresetName()
{
    auto& pm = proc.presetManager;
    int cur = pm.getCurrentIndex();
    if (cur >= 0 && cur < pm.getNumPresets())
        presetNameBtn.setName (pm.getPresetName (cur));
    else
        presetNameBtn.setName ("Init");
}

void TsukiSynthEditor::showPresetBrowser()
{
    presetBrowser.rebuild();
    auto nameBounds = presetNameBtn.getBoundsInParent();
    int browserH = juce::jmin (300, getHeight() - nameBounds.getBottom() - 10);
    presetBrowser.setBounds (nameBounds.getX(), nameBounds.getBottom() + 2,
                             nameBounds.getWidth(), browserH);
    presetBrowser.setVisible (true);
    presetBrowser.toFront (true);
}

void TsukiSynthEditor::hidePresetBrowser()
{
    presetBrowser.setVisible (false);
}

void TsukiSynthEditor::updateDirtyIndicator()
{
    dirtyLabel.setText (proc.presetManager.isDirty() ? "*" : "",
                        juce::dontSendNotification);
}

void TsukiSynthEditor::promptSavePreset()
{
    auto* aw = new juce::AlertWindow ("Save Preset",
                                       "Enter a name for the preset:",
                                       juce::AlertWindow::NoIcon, this);
    aw->addTextEditor ("name", "My Preset", "Preset Name:");
    aw->addButton ("Save",   1);
    aw->addButton ("Cancel", 0);

    aw->enterModalState (true, juce::ModalCallbackFunction::create (
        [this, aw] (int result)
        {
            if (result == 1)
            {
                auto name = aw->getTextEditorContents ("name").trim();
                if (name.isNotEmpty())
                {
                    proc.presetManager.saveUserPreset (name);
                    updatePresetName();
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
    k.label.setBounds (c.removeFromTop (12));
    k.slider.setBounds (c.withSizeKeepingCentre (juce::jmin (58, c.getWidth()), c.getHeight()));
}

void TsukiSynthEditor::layoutComboCell (juce::Rectangle<int> cell, ComboParam& p)
{
    auto c = cell.reduced (10, 1);
    p.label.setBounds (c.removeFromTop (12));
    c.removeFromTop (4);
    p.combo.setBounds (c.removeFromTop (26));
}

void TsukiSynthEditor::layoutFxKnob (juce::Rectangle<int> cell, KnobParam& k)
{
    auto c = cell.reduced (2, 0);
    k.label.setBounds (c.removeFromTop (10));
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
    g.setFont (juce::Font (juce::FontOptions (9.0f)).boldened());
    g.drawText (title, bounds.getX() + 8, bounds.getY() + 6,
                bounds.getWidth() - 16, 12, juce::Justification::centredLeft);
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
    //  All values from uiux/TsukiSynth.html CSS + uiux/app.jsx + uiux/components.jsx
    //  .title-bar  { padding: 16px 20px 10px }        → padT=16, padL=20
    //  .title-left { gap: 8px; margin-bottom: 4px }   → moonToWord=8, wordToSub=4
    //  .title-moon { transform: translateY(2px) }      → moonDy=2
    //  MoonIcon    size=18 color="#d4b896" opacity=0.95
    //  .wordmark   font-size:22px letter-spacing:0.04em gradient:#f0e8d8→#c49a6c
    //  .title-sub  font-size:10px letter-spacing:0.12em gap:7px
    //              .sub-engine=#8899aa  .sub-pipe=#3a3a5a  .sub-tag=#667788
    {
        constexpr int   padT = 16, padL = 20;
        constexpr int   moonSize = 18, moonDy = 2, moonToWord = 8, wordToSub = 4;
        constexpr int   wordH = 22, subH = 12;
        constexpr int   wordX = padL + moonSize + moonToWord;   // 46
        constexpr int   subY  = padT + wordH + wordToSub;       // 42

        g.setGradientFill (juce::ColourGradient (
            juce::Colour (0x04ffffff), 0.0f, 0.0f,
            juce::Colours::transparentBlack, 0.0f, (float) kTitleH, false));
        g.fillRect (0, 0, w, kTitleH);

        // moon — parseSVGPath 原始路徑, viewBox 20→18px, 位置 (padL, padT+moonDy)
        {
            auto scaled = moonPath;
            scaled.applyTransform (juce::AffineTransform::scale ((float) moonSize / 20.0f)
                                       .translated ((float) padL, (float)(padT + moonDy)));
            g.setColour (juce::Colour (0xffd4b896).withAlpha (0.95f));
            g.fillPath (scaled);
        }

        // wordmark — IBM Plex Sans SemiBold 22px, gradient #f0e8d8→#c49a6c
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
                juce::Colour (0xffc49a6c), 0.0f, (float)(padT + wordH), false));
            g.fillPath (textPath);
        }

        // subtitle — 10px, gap 7px between spans
        int eng = currentEngine();
        auto eName = eng == 0 ? juce::String ("CIMBALOM")
                   : eng == 1 ? juce::String ("CHROMATIC")
                   :            juce::String ("FM PIANO");
        auto eType = eng == 0 ? juce::String ("PHYSICAL MODELING STRING")
                   : eng == 1 ? juce::String ("BEAM / PLATE / CUSTOM")
                   :            juce::String ("FREQUENCY MODULATION");
        auto subFont = juce::Font (juce::FontOptions (10.0f).withTypeface (wordmarkTypeface))
                           .withExtraKerningFactor (0.12f);
        g.setFont (subFont);
        auto nameStr = eName + " ENGINE";
        int nameW = (int) juce::GlyphArrangement::getStringWidth (subFont, nameStr);

        g.setColour (juce::Colour (0xff8899aa));
        g.drawText (nameStr, padL, subY, nameW + 4, subH, juce::Justification::centredLeft);
        g.setColour (juce::Colour (0xff3a3a5a));
        g.drawText ("|", padL + nameW + 7, subY, 10, subH, juce::Justification::centred);
        g.setColour (juce::Colour (0xff667788));
        g.drawText (eType, padL + nameW + 7 + 10 + 7, subY, 300, subH, juce::Justification::centredLeft);

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
        g.setFont (juce::Font (juce::FontOptions (9.0f)).boldened()
                       .withExtraKerningFactor (0.2f));
        g.drawText ("MACRO", kSidePad, y + 6, 56, 14, juce::Justification::centredLeft);

        g.setColour (juce::Colour (0xff334455));
        g.setFont (juce::FontOptions (9.0f));
        g.drawText ("8 params", kSidePad + 52, y + 6,
                    60, 14, juce::Justification::centredLeft);

        g.setColour (Clr::border.withAlpha (0.5f));
        g.fillRect (kSidePad + 114, y + 12, w - kSidePad * 2 - 114, 1);
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
        g.setFont (juce::Font (juce::FontOptions (9.0f)).boldened()
                       .withExtraKerningFactor (0.2f));
        g.drawText ("ENGINE", kSidePad, y + 6, 56, 14, juce::Justification::centredLeft);

        int eng = currentEngine();
        int pc  = (eng == 0) ? 6 : 7;
        g.setColour (juce::Colour (0xff334455));
        g.setFont (juce::FontOptions (9.0f));
        g.drawText (juce::String (pc) + " params", kSidePad + 58, y + 6,
                    60, 14, juce::Justification::centredLeft);

        // divider line
        g.setColour (Clr::border.withAlpha (0.5f));
        g.fillRect (kSidePad + 120, y + 12, w - kSidePad * 2 - 120, 1);
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
        g.setFont (juce::Font (juce::FontOptions (9.0f)).boldened()
                       .withExtraKerningFactor (0.2f));
        g.drawText ("EFFECTS", kSidePad, y + 6, 60, 14, juce::Justification::centredLeft);
        g.setColour (Clr::border.withAlpha (0.5f));
        g.fillRect (kSidePad + 64, y + 12, w - kSidePad * 2 - 64, 1);

        paintPanel (g, reverbBounds_, "REVERB");
        paintPanel (g, delayBounds_,  "DELAY");
        paintPanel (g, compBounds_,   "COMPRESSOR");
    }

    // -- distortion row --------------------------------------------------
    {
        int y = distRow_.getY();
        g.setColour (Clr::effectsBg);
        g.fillRect (0, y, w, distRow_.getHeight());
        paintPanel (g, distPanelBounds_, "DISTORTION");
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
    langToggle.setBounds (w - 60, 22, 44, 18);

    // -- preset row ------------------------------------------------------
    {
        auto row   = area.removeFromTop (kPresetH);
        auto inner = row.reduced (kSidePad, 8);

        presetPrev.setBounds (inner.removeFromLeft (20).reduced (0, 1));
        inner.removeFromLeft (2);
        presetNext.setBounds (inner.removeFromLeft (20).reduced (0, 1));
        inner.removeFromLeft (6);

        presetInit.setBounds (inner.removeFromRight (30).reduced (0, 1));
        inner.removeFromRight (4);
        presetSave.setBounds (inner.removeFromRight (36).reduced (0, 1));
        inner.removeFromRight (4);
        dirtyLabel.setBounds (inner.removeFromRight (14));

        presetNameBtn.setBounds (inner);
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
        auto inner = macroArea_.reduced (kSidePad, 0).withTrimmedTop (22);
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
        auto inner = distPanelBounds_.reduced (8, 0).withTrimmedTop (22);

        auto typeArea = inner.removeFromLeft (inner.getWidth() * 2 / 7);
        distType.label.setBounds (typeArea.removeFromTop (12));
        typeArea.removeFromTop (4);
        distType.combo.setBounds (typeArea.removeFromTop (26));

        inner.removeFromLeft (10);
        int knobW = inner.getWidth() / 3;
        layoutFxKnob (inner.removeFromLeft (knobW), distDrive);
        layoutFxKnob (inner.removeFromLeft (knobW), distInstability);
        layoutFxKnob (inner, distMix);
    }

    effectsRow_ = area.removeFromBottom (kEffectsH);
    {
        auto inner = effectsRow_.reduced (kSidePad, 0).withTrimmedTop (24);
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
            auto p = reverbBounds_.reduced (6, 0).withTrimmedTop (22);
            int kw = p.getWidth() / 2;
            layoutFxKnob (p.removeFromLeft (kw), fxRevMix);
            layoutFxKnob (p, fxRevSize);
        }
        // delay knobs
        {
            auto p = delayBounds_.reduced (6, 0).withTrimmedTop (22);
            int kw = p.getWidth() / 3;
            layoutFxKnob (p.removeFromLeft (kw), fxDlyTime);
            layoutFxKnob (p.removeFromLeft (kw), fxDlyFeedback);
            layoutFxKnob (p, fxDlyMix);
        }
        // compressor knobs
        {
            auto p = compBounds_.reduced (6, 0).withTrimmedTop (22);
            int kw = p.getWidth() / 2;
            layoutFxKnob (p.removeFromLeft (kw), fxCompThresh);
            layoutFxKnob (p, fxCompRatio);
        }
    }

    // -- engine section (remaining space) --------------------------------
    engineArea_ = area;
    {
        auto inner = engineArea_.reduced (kSidePad, 0).withTrimmedTop (24);
        int eng = currentEngine();

        int numRows = (eng == 0) ? 3 : 4;
        int gap     = 6;
        int rowH    = (inner.getHeight() - (numRows - 1) * gap) / numRows;
        int colGap  = 14;
        int colW    = (inner.getWidth() - colGap) / 2;

        auto takeRow = [&]() -> std::pair<juce::Rectangle<int>, juce::Rectangle<int>>
        {
            auto row  = inner.removeFromTop (rowH);
            inner.removeFromTop (gap);
            auto left = row.removeFromLeft (colW);
            row.removeFromLeft (colGap);
            auto right = row.withWidth (colW);
            return { left, right };
        };

        if (eng == 0)
        {
            auto [l0, r0] = takeRow();
            layoutComboCell (l0, cimMaterial);
            layoutComboCell (r0, cimHammer);

            auto [l1, r1] = takeRow();
            layoutKnobCell (l1, cimStrike);
            layoutKnobCell (r1, cimDiameter);

            auto [l2, r2] = takeRow();
            layoutKnobCell (l2, cimStrings);
            layoutKnobCell (r2, cimDetune);
        }
        else if (eng == 1)
        {
            auto [l0, r0] = takeRow();
            layoutComboCell (l0, chrMaterial);
            layoutComboCell (r0, chrSubEngine);

            auto [l1, r1] = takeRow();
            layoutKnobCell (l1, chrStrike);
            layoutKnobCell (r1, chrThickness);

            auto [l2, r2] = takeRow();
            layoutKnobCell (l2, chrSize);
            layoutComboCell (r2, chrExciter);

            auto [l3, r3] = takeRow();
            layoutKnobCell (l3, chrGlide);
            (void) r3;

            if (harmonicEditor.isVisible())
            {
                auto hArea = inner.withHeight (juce::jmin (inner.getHeight(), 90));
                harmonicEditor.setBounds (hArea);
            }
        }
        else
        {
            auto [l0, r0] = takeRow();
            layoutComboCell (l0, fmType);
            (void) r0;

            auto [l1, r1] = takeRow();
            layoutKnobCell (l1, fmRatio);
            layoutKnobCell (r1, fmIndex);

            auto [l2, r2] = takeRow();
            layoutKnobCell (l2, fmBrightness);
            layoutKnobCell (r2, fmFeedback);

            auto [l3, r3] = takeRow();
            layoutKnobCell (l3, fmAttack);
            layoutKnobCell (r3, fmRelease);
        }
    }
}
