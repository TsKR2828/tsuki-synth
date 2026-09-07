#include "PluginEditor.h"
#include "BinaryData.h"
#include "Presets.h"

namespace
{
    constexpr int kW = 540;
    constexpr int kH = 850;

    constexpr float kRotaryStart = juce::MathConstants<float>::pi * 1.25f;
    constexpr float kRotaryEnd   = juce::MathConstants<float>::pi * 2.75f;

    constexpr int kTitleH    = 56;
    constexpr int kPresetH   = 44;
    constexpr int kTabH      = 36;
    constexpr int kMacroH    = 90;
    constexpr int kEffectsH  = 108;
    constexpr int kDistH      = 70;
    constexpr int kAnalyzerH  = 80;
    constexpr int kKeyboardH  = 80;
    constexpr int kSidePad   = 16;
    constexpr int kMaxScale   = 2;
}

// ========================================================================
//  Constructor
// ========================================================================
TsukiSynthEditor::TsukiSynthEditor (TsukiSynthProcessor& p)
    : AudioProcessorEditor (&p),
      proc (p),
      keyboard (p.keyboardState, juce::MidiKeyboardComponent::horizontalKeyboard),
      analyzerPanel (p.analyzerFifo)
{
    setLookAndFeel (&lnf);

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
        refreshLocalizedText();
        if (auto* topLevel = getTopLevelComponent())
            topLevel->resized();
        repaint();
    };
    addAndMakeVisible (langToggle);

    // -- Standalone recorder --------------------------------------------
    recordButton.setComponentID ("step");
    recordButton.onClick = [this]
    {
        if (proc.isRecording())
            proc.stopRecording();
        else
            proc.startRecording();

        updateRecordingUi();
    };
    recordButton.setVisible (proc.isStandalone());
    addAndMakeVisible (recordButton);

    recordStatus.setFont (juce::Font (juce::FontOptions (10.0f)));
    recordStatus.setJustificationType (juce::Justification::centredRight);
    recordStatus.setColour (juce::Label::textColourId, Clr::textDim);
    recordStatus.setVisible (proc.isStandalone());
    addAndMakeVisible (recordStatus);

    // -- Preset ----------------------------------------------------------
    presetCombo.setColour (juce::ComboBox::backgroundColourId, Clr::comboBg);
    presetCombo.setColour (juce::ComboBox::outlineColourId,    Clr::comboBorder);
    presetCombo.setColour (juce::ComboBox::textColourId,       Clr::goldLight);
    rebuildPresetCombo();
    presetCombo.onChange = [this]
    {
        int id = presetCombo.getSelectedId();
        if (id > 0)
            proc.setCurrentProgram (id - 1);
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

    // -- Engine listener + initial state ---------------------------------
    proc.apvts.addParameterListener ("engine", this);
    refreshLocalizedText();
    updateEngine();
    updateDirtyIndicator();
    updateRecordingUi();
    startTimerHz (5);
    setSize (kW, kH);
    setResizable (true, true);
    setResizeLimits (kW, kH, kW * kMaxScale, kH * kMaxScale);

    if (auto* boundsConstrainer = getConstrainer())
        boundsConstrainer->setFixedAspectRatio ((double) kW / (double) kH);
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
        juce::MessageManager::callAsync ([this] { updateEngine(); resized(); repaint(); });
}

void TsukiSynthEditor::timerCallback()
{
    updateDirtyIndicator();
    updateRecordingUi();
    updateStandaloneWindowTitle();
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
}

void TsukiSynthEditor::updateStandaloneWindowTitle()
{
    auto* window = findParentComponentOfClass<juce::DocumentWindow>();
    if (window == nullptr)
        return;

    window->setName (UiLocale::text ("appTitle"));
}

void TsukiSynthEditor::updateRecordingUi()
{
    const auto standalone = proc.isStandalone();
    recordButton.setVisible (standalone);
    recordStatus.setVisible (standalone);

    if (! standalone)
        return;

    const auto recording = proc.isRecording();
    const auto status = proc.getRecordingStatusText();
    recordButton.setButtonText (recording ? "STOP" : "REC");
    recordStatus.setText (status, juce::dontSendNotification);
    recordStatus.setTooltip (status);
    recordStatus.setColour (juce::Label::textColourId,
                            recording ? Clr::goldBright : Clr::textDim);
}

float TsukiSynthEditor::currentUiScale() const
{
    auto widthScale  = (float) getWidth()  / (float) kW;
    auto heightScale = (float) getHeight() / (float) kH;
    return juce::jlimit (1.0f, (float) kMaxScale, juce::jmin (widthScale, heightScale));
}

juce::AffineTransform TsukiSynthEditor::contentTransform() const
{
    const auto scale = currentUiScale();
    const auto contentW = (float) kW * scale;
    const auto contentH = (float) kH * scale;
    const auto x = ((float) getWidth()  - contentW) * 0.5f;
    const auto y = ((float) getHeight() - contentH) * 0.5f;

    return juce::AffineTransform::scale (scale)
        .followedBy (juce::AffineTransform::translation (x, y));
}

void TsukiSynthEditor::updateScaledChildTransforms()
{
    const auto transform = contentTransform();

    auto apply = [&] (juce::Component& component)
    {
        component.setTransform (transform);
    };

    auto applyKnob = [&] (KnobParam& k)
    {
        apply (k.slider);
        apply (k.label);
    };

    auto applyCombo = [&] (ComboParam& c)
    {
        apply (c.combo);
        apply (c.label);
    };

    apply (keyboard);
    apply (tabCim);
    apply (tabChr);
    apply (tabFM);
    apply (langToggle);
    apply (recordButton);
    apply (recordStatus);
    apply (presetCombo);
    apply (presetPrev);
    apply (presetNext);
    apply (presetSave);
    apply (presetInit);
    apply (dirtyLabel);

    applyCombo (cimMaterial);
    applyCombo (cimHammer);
    applyKnob  (cimStrike);
    applyKnob  (cimDiameter);
    applyKnob  (cimStrings);
    applyKnob  (cimDetune);

    applyCombo (chrSubEngine);
    applyCombo (chrMaterial);
    applyCombo (chrExciter);
    applyKnob  (chrStrike);
    applyKnob  (chrThickness);
    applyKnob  (chrSize);
    applyKnob  (chrGlide);

    applyCombo (fmType);
    applyKnob  (fmRatio);
    applyKnob  (fmIndex);
    applyKnob  (fmBrightness);
    applyKnob  (fmFeedback);
    applyKnob  (fmAttack);
    applyKnob  (fmRelease);

    applyKnob (macroMaterial);
    applyKnob (macroTension);
    applyKnob (macroDamping);
    applyKnob (macroStrike);
    applyKnob (macroBrightness);
    applyKnob (macroBody);
    applyKnob (macroNoise);
    applyKnob (macroOutput);

    applyKnob (fxRevMix);
    applyKnob (fxRevSize);
    applyKnob (fxDlyTime);
    applyKnob (fxDlyFeedback);
    applyKnob (fxDlyMix);
    applyKnob (fxCompThresh);
    applyKnob (fxCompRatio);

    applyCombo (distType);
    applyKnob  (distDrive);
    applyKnob  (distInstability);
    applyKnob  (distMix);

    apply (analyzerPanel);
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
    langToggle.setButtonText (UiLocale::toggleLabel());
    presetSave.setButtonText (UiLocale::text ("save"));
    presetInit.setButtonText (UiLocale::text ("init"));
    tabCim.setButtonText (UiLocale::tabName (0));
    tabChr.setButtonText (UiLocale::tabName (1));
    tabFM.setButtonText  (UiLocale::tabName (2));
    rebuildPresetCombo();

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

    keyboard.repaint();
    analyzerPanel.repaint();
    analyzerPanel.oscilloscope.repaint();
    updateStandaloneWindowTitle();
}

// ========================================================================
//  Preset helpers
// ========================================================================
void TsukiSynthEditor::rebuildPresetCombo()
{
    presetCombo.clear (juce::dontSendNotification);

    auto& pm = proc.presetManager;
    int nFactory = pm.getNumFactoryPresets();
    int nUser    = pm.getNumUserPresets();

    for (int i = 0; i < nFactory; ++i)
        presetCombo.addItem (UiLocale::factoryPresetName (pm.getPresetName (i)), i + 1);

    if (nUser > 0)
    {
        presetCombo.addSeparator();
        for (int i = 0; i < nUser; ++i)
            presetCombo.addItem (pm.getPresetName (nFactory + i), nFactory + i + 1);
    }

    int cur = pm.getCurrentIndex();
    if (cur >= 0 && cur < pm.getNumPresets())
        presetCombo.setSelectedId (cur + 1, juce::dontSendNotification);
}

void TsukiSynthEditor::updateDirtyIndicator()
{
    dirtyLabel.setText (proc.presetManager.isDirty() ? "*" : "",
                        juce::dontSendNotification);
}

void TsukiSynthEditor::promptSavePreset()
{
    auto* aw = new juce::AlertWindow (UiLocale::text ("presetSaveTitle"),
                                       UiLocale::text ("presetSaveMessage"),
                                       juce::AlertWindow::NoIcon, this);
    aw->addTextEditor ("name",
                       UiLocale::text ("presetDefaultName"),
                       UiLocale::text ("presetNameLabel"));
    aw->addButton (UiLocale::text ("save"),   1);
    aw->addButton (UiLocale::text ("cancel"), 0);

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

    juce::Graphics::ScopedSaveState scaledState (g);
    g.addTransform (contentTransform());

    int w = kW;

    // -- title bar -------------------------------------------------------
    {
        g.setGradientFill (juce::ColourGradient (
            juce::Colour (0x04ffffff), 0.0f, 0.0f,
            juce::Colours::transparentBlack, 0.0f, (float) kTitleH, false));
        g.fillRect (0, 0, w, kTitleH);

        // MoonIcon crescent from uiux/components.jsx, viewBox 0 0 20 20.
        static const auto sourceMoonPath = [] {
            return juce::Drawable::parseSVGPath ("M14 3 a8 8 0 1 0 0 14 a6 6 0 0 1 0 -14 z");
        }();

        auto moonPath = sourceMoonPath;
        moonPath.applyTransform (
            juce::AffineTransform::scale (18.0f / 20.0f)
                .followedBy (juce::AffineTransform::translation (20.0f, 16.0f)));
        g.setColour (Clr::goldBright.withAlpha (0.95f));
        g.fillPath (moonPath);

        // wordmark
        static const auto wordmarkTypeface = []() -> juce::Typeface::Ptr
        {
            return juce::Typeface::createSystemTypefaceFor (
                BinaryData::IBMPlexSansSemiBold_ttf,
                BinaryData::IBMPlexSansSemiBold_ttfSize);
        }();

        auto wordmarkOptions = wordmarkTypeface != nullptr
            ? juce::FontOptions (wordmarkTypeface).withHeight (22.0f)
            : juce::FontOptions ("Segoe UI", "Semibold", 22.0f);

        auto wordmarkFont = juce::Font (
            wordmarkOptions
                .withFallbacks (std::vector<juce::String> { "Segoe UI", "Arial", "Microsoft JhengHei" })
                .withKerningFactor (0.04f));
        g.setGradientFill (juce::ColourGradient (
            juce::Colour (0xfff0e8d8), 46.0f, 12.0f,
            juce::Colour (0xffc49a6c), 46.0f, 36.0f, false));
        g.setFont (wordmarkFont);
        g.drawText (UiLocale::text ("appTitle"), 46, 12, 180, 24,
                    juce::Justification::centredLeft);

        // subtitle
        int eng = currentEngine();
        auto eName = eng == 0 ? juce::String ("CIMBALOM ENGINE")
                   : eng == 1 ? juce::String ("CHROMATIC ENGINE")
                   :            juce::String ("FM PIANO ENGINE");
        auto eType = eng == 0 ? juce::String ("PHYSICAL MODELING STRING")
                   : eng == 1 ? juce::String ("BEAM / PLATE / CUSTOM")
                   :            juce::String ("FREQUENCY MODULATION");
        auto subFont = juce::Font (
            juce::FontOptions ("IBM Plex Sans", "Medium", 10.0f)
                .withFallbacks (std::vector<juce::String> { "Segoe UI", "Arial", "Microsoft JhengHei" })
                .withKerningFactor (0.12f));
        g.setFont (subFont);
        g.setColour (Clr::textMid);
        auto nameStr = eName;
        auto typeStr = eType;
        constexpr int subtitleX = 20;
        g.drawText (nameStr, subtitleX, 36, 200, 14, juce::Justification::centredLeft);
        int nameW = (int) juce::GlyphArrangement::getStringWidth (subFont, nameStr);
        g.setColour (juce::Colour (0xff3a3a5a));
        g.drawText ("|", subtitleX + nameW + 7, 36, 8, 14, juce::Justification::centred);
        g.setColour (Clr::textDim);
        g.drawText (typeStr, subtitleX + nameW + 22, 36, 300, 14, juce::Justification::centredLeft);

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
        g.drawText (UiLocale::text ("macro"), kSidePad, y + 6, 56, 14,
                    juce::Justification::centredLeft);

        g.setColour (juce::Colour (0xff334455));
        g.setFont (juce::FontOptions (9.0f));
        g.drawText (UiLocale::paramCount (8), kSidePad + 52, y + 6,
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
        g.drawText (UiLocale::text ("engine"), kSidePad, y + 6, 64, 14,
                    juce::Justification::centredLeft);

        int eng = currentEngine();
        int pc  = (eng == 0) ? 6 : 7;
        g.setColour (juce::Colour (0xff334455));
        g.setFont (juce::FontOptions (9.0f));
        g.drawText (UiLocale::paramCount (pc), kSidePad + 68, y + 6,
                    60, 14, juce::Justification::centredLeft);

        // divider line
        g.setColour (Clr::border.withAlpha (0.5f));
        g.fillRect (kSidePad + 130, y + 12, w - kSidePad * 2 - 130, 1);
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
        g.drawText (UiLocale::text ("effects"), kSidePad, y + 6, 60, 14,
                    juce::Justification::centredLeft);
        g.setColour (Clr::border.withAlpha (0.5f));
        g.fillRect (kSidePad + 64, y + 12, w - kSidePad * 2 - 64, 1);

        paintPanel (g, reverbBounds_, UiLocale::text ("reverb"));
        paintPanel (g, delayBounds_,  UiLocale::text ("delay"));
        paintPanel (g, compBounds_,   UiLocale::text ("compressor"));
    }

    // -- distortion row --------------------------------------------------
    {
        int y = distRow_.getY();
        g.setColour (Clr::effectsBg);
        g.fillRect (0, y, w, distRow_.getHeight());
        paintPanel (g, distPanelBounds_, UiLocale::text ("distortion"));
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
        g.fillRect (0, y, w, kH - y);
        g.setColour (Clr::borderLight);
        g.drawHorizontalLine (y, 0.0f, (float) w);
    }
}

// ========================================================================
//  Resized -- top-to-bottom layout
// ========================================================================
void TsukiSynthEditor::resized()
{
    auto area = juce::Rectangle<int> (0, 0, kW, kH);
    int w = area.getWidth();

    // -- title (paint only) + language toggle in title bar ----------------
    area.removeFromTop (kTitleH);
    recordStatus.setBounds (230, 20, 188, 18);
    recordButton.setBounds (w - 112, 20, 48, 18);
    langToggle.setBounds (w - 60, 20, 44, 18);

    // -- preset row ------------------------------------------------------
    {
        auto row   = area.removeFromTop (kPresetH);
        auto inner = row.reduced (kSidePad, 8);

        presetPrev.setBounds (inner.removeFromLeft (20).reduced (0, 1));
        inner.removeFromLeft (2);
        presetNext.setBounds (inner.removeFromLeft (20).reduced (0, 1));
        inner.removeFromLeft (6);

        presetInit.setBounds (inner.removeFromRight (46).reduced (0, 1));
        inner.removeFromRight (4);
        presetSave.setBounds (inner.removeFromRight (42).reduced (0, 1));
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

    updateScaledChildTransforms();
}
