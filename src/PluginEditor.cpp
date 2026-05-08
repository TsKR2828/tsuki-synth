#include "PluginEditor.h"
#include "Presets.h"

namespace
{
    constexpr int kW = 540;
    constexpr int kH = 680;

    constexpr float kRotaryStart = juce::MathConstants<float>::pi * 1.25f;
    constexpr float kRotaryEnd   = juce::MathConstants<float>::pi * 2.75f;

    constexpr int kTitleH    = 56;
    constexpr int kPresetH   = 44;
    constexpr int kTabH      = 36;
    constexpr int kEffectsH  = 108;
    constexpr int kDistH     = 70;
    constexpr int kKeyboardH = 80;
    constexpr int kSidePad   = 16;
}

// ════════════════════════════════════════════════════════════════════════
//  Constructor
// ════════════════════════════════════════════════════════════════════════
TsukiSynthEditor::TsukiSynthEditor (TsukiSynthProcessor& p)
    : AudioProcessorEditor (&p),
      proc (p),
      keyboard (p.keyboardState, juce::MidiKeyboardComponent::horizontalKeyboard)
{
    setLookAndFeel (&lnf);

    // ── Keyboard ────────────────────────────────────────────────
    keyboard.setColour (juce::MidiKeyboardComponent::whiteNoteColourId,     Clr::whiteKey);
    keyboard.setColour (juce::MidiKeyboardComponent::blackNoteColourId,     Clr::blackKey);
    keyboard.setColour (juce::MidiKeyboardComponent::keySeparatorLineColourId, juce::Colour (0x28000000));
    keyboard.setColour (juce::MidiKeyboardComponent::shadowColourId,        juce::Colour (0x30000000));
    keyboard.setColour (juce::MidiKeyboardComponent::keyDownOverlayColourId, Clr::gold.withAlpha (0.35f));
    addAndMakeVisible (keyboard);

    // ── Tab buttons ─────────────────────────────────────────────
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

    // ── Preset ──────────────────────────────────────────────────
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

    // ── Cimbalom ────────────────────────────────────────────────
    setupCombo (cimMaterial, "cim_material",    "MATERIAL");
    setupCombo (cimHammer,   "cim_hammer",      "HAMMER");
    setupKnob  (cimStrike,   "cim_strike_pos",  "STRIKE POS");
    setupKnob  (cimDiameter, "cim_diameter",    "DIAMETER");
    setupKnob  (cimStrings,  "cim_num_strings", "STRINGS");
    setupKnob  (cimDetune,   "cim_detuning",    "DETUNING");

    // ── Chromatic ───────────────────────────────────────────────
    setupCombo (chrSubEngine, "chr_sub_engine", "SUB-ENGINE");
    setupCombo (chrMaterial,  "chr_material",   "MATERIAL");
    setupCombo (chrExciter,   "chr_exciter",    "EXCITER");
    setupKnob  (chrStrike,    "chr_strike_pos", "STRIKE POS");
    setupKnob  (chrThickness, "chr_thickness",  "THICKNESS");
    setupKnob  (chrSize,      "chr_size",       "SIZE");
    setupKnob  (chrGlide,     "chr_pitch_glide","PITCH GLIDE");

    // ── FM Piano ────────────────────────────────────────────────
    setupCombo (fmType,       "fm_type",       "SOUND TYPE");
    setupKnob  (fmRatio,      "fm_ratio",      "RATIO");
    setupKnob  (fmIndex,      "fm_index",      "MOD INDEX");
    setupKnob  (fmBrightness, "fm_brightness", "BRIGHTNESS");
    setupKnob  (fmFeedback,   "fm_feedback",   "FEEDBACK");
    setupKnob  (fmAttack,     "fm_attack",     "ATTACK");
    setupKnob  (fmRelease,    "fm_release",    "RELEASE");

    // ── Effects ─────────────────────────────────────────────────
    setupKnob (fxRevMix,      "fx_reverb_mix",      "MIX",    true);
    setupKnob (fxRevSize,     "fx_reverb_size",      "SIZE",   true);
    setupKnob (fxDlyTime,     "fx_delay_time",       "TIME",   true);
    setupKnob (fxDlyFeedback, "fx_delay_feedback",   "FB",     true);
    setupKnob (fxDlyMix,      "fx_delay_mix",        "MIX",    true);
    setupKnob (fxCompThresh,  "fx_comp_threshold",   "THRESH", true);
    setupKnob (fxCompRatio,   "fx_comp_ratio",       "RATIO",  true);

    // ── Distortion ──────────────────────────────────────────────
    setupCombo (distType,        "fx_dist_type",        "TYPE");
    setupKnob  (distDrive,       "fx_dist_drive",       "DRIVE",       true);
    setupKnob  (distInstability, "fx_dist_instability",  "INSTABILITY", true);
    setupKnob  (distMix,         "fx_dist_mix",          "MIX",         true);

    // ── Engine listener ─────────────────────────────────────────
    proc.apvts.addParameterListener ("engine", this);
    updateEngine();
    startTimerHz (5);
    setSize (kW, kH);
}

TsukiSynthEditor::~TsukiSynthEditor()
{
    stopTimer();
    setLookAndFeel (nullptr);
    proc.apvts.removeParameterListener ("engine", this);
}

// ════════════════════════════════════════════════════════════════════════
//  Engine switching
// ════════════════════════════════════════════════════════════════════════
void TsukiSynthEditor::parameterChanged (const juce::String& id, float)
{
    if (id == "engine")
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

    setVisible (fmType,       isFM);  setVisible (fmRatio,      isFM);
    setVisible (fmIndex,      isFM);  setVisible (fmBrightness, isFM);
    setVisible (fmFeedback,   isFM);  setVisible (fmAttack,     isFM);
    setVisible (fmRelease,    isFM);

    keyboard.setColour (juce::MidiKeyboardComponent::keyDownOverlayColourId,
                        lnf.accent.withAlpha (0.35f));
}

// ════════════════════════════════════════════════════════════════════════
//  Setup helpers
// ════════════════════════════════════════════════════════════════════════
void TsukiSynthEditor::setupKnob (KnobParam& k, const juce::String& paramID,
                                    const juce::String& text, bool small)
{
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
    l.setText (text, juce::dontSendNotification);
    l.setFont (juce::Font (juce::FontOptions (small ? 8.0f : 9.5f)).boldened());
    l.setJustificationType (juce::Justification::centred);
    l.setColour (juce::Label::textColourId, small ? Clr::fxTitle : Clr::label);
    addAndMakeVisible (l);

    k.attachment = std::make_unique<SliderAttachment> (proc.apvts, paramID, s);
}

void TsukiSynthEditor::setupCombo (ComboParam& c, const juce::String& paramID,
                                     const juce::String& text)
{
    if (auto* cp = dynamic_cast<juce::AudioParameterChoice*> (
            proc.apvts.getParameter (paramID)))
    {
        int id = 1;
        for (const auto& choice : cp->choices)
            c.combo.addItem (choice, id++);
    }
    addAndMakeVisible (c.combo);

    c.label.setText (text, juce::dontSendNotification);
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

// ════════════════════════════════════════════════════════════════════════
//  Preset helpers
// ════════════════════════════════════════════════════════════════════════
void TsukiSynthEditor::rebuildPresetCombo()
{
    presetCombo.clear (juce::dontSendNotification);

    auto& pm = proc.presetManager;
    int nFactory = pm.getNumFactoryPresets();
    int nUser    = pm.getNumUserPresets();

    for (int i = 0; i < nFactory; ++i)
        presetCombo.addItem (pm.getPresetName (i), i + 1);

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
                    rebuildPresetCombo();
                    updateDirtyIndicator();
                }
            }
            delete aw;
        }));
}

// ════════════════════════════════════════════════════════════════════════
//  Layout helpers
// ════════════════════════════════════════════════════════════════════════
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

// ════════════════════════════════════════════════════════════════════════
//  Paint
// ════════════════════════════════════════════════════════════════════════
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
    // ── plugin background gradient ──────────────────────────────
    g.setGradientFill (juce::ColourGradient (
        Clr::pluginTop, 0.0f, 0.0f,
        Clr::pluginBot, 0.0f, (float) getHeight(), false));
    g.fillAll();

    int w = getWidth();

    // ── title bar ───────────────────────────────────────────────
    {
        g.setGradientFill (juce::ColourGradient (
            juce::Colour (0x04ffffff), 0.0f, 0.0f,
            juce::Colours::transparentBlack, 0.0f, (float) kTitleH, false));
        g.fillRect (0, 0, w, kTitleH);

        // moon crescent (two overlapping circles)
        g.setColour (Clr::goldBright.withAlpha (0.92f));
        g.fillEllipse (18.0f, 16.0f, 15.0f, 15.0f);
        g.setColour (juce::Colour (0xff1a1a2d));
        g.fillEllipse (23.0f, 13.0f, 14.0f, 14.0f);

        // wordmark
        g.setFont (juce::Font (juce::FontOptions (20.0f)).boldened()
                       .withExtraKerningFactor (0.04f));
        g.setColour (Clr::goldBright);
        g.drawText ("TsukiSynth", 38, 14, 150, 22, juce::Justification::centredLeft);

        // subtitle
        int eng = currentEngine();
        auto eName = eng == 0 ? juce::String ("CIMBALOM")
                   : eng == 1 ? juce::String ("CHROMATIC")
                   :            juce::String ("FM PIANO");
        auto eType = eng == 0 ? juce::String ("PHYSICAL MODELING STRING")
                   : eng == 1 ? juce::String ("BEAM / PLATE / CUSTOM")
                   :            juce::String ("FREQUENCY MODULATION");
        auto subFont = juce::Font (juce::FontOptions (10.0f)).withExtraKerningFactor (0.1f);
        g.setFont (subFont);
        g.setColour (Clr::textMid);
        auto nameStr = eName + " ENGINE";
        g.drawText (nameStr, 40, 36, 200, 14, juce::Justification::centredLeft);
        int nameW = (int) subFont.getStringWidthFloat (nameStr);
        g.setColour (juce::Colour (0xff3a3a5a));
        g.drawText ("|", 40 + nameW + 4, 36, 10, 14, juce::Justification::centred);
        g.setColour (Clr::textDim);
        g.drawText (eType, 40 + nameW + 16, 36, 300, 14, juce::Justification::centredLeft);

        g.setColour (Clr::borderLight);
        g.drawHorizontalLine (kTitleH - 1, 0.0f, (float) w);
    }

    // ── preset row background ───────────────────────────────────
    {
        int y = kTitleH;
        g.setColour (Clr::presetBg);
        g.fillRect (0, y, w, kPresetH);
        g.setColour (Clr::borderLight);
        g.drawHorizontalLine (y + kPresetH - 1, 0.0f, (float) w);
    }

    // ── tabs background ─────────────────────────────────────────
    {
        int y = kTitleH + kPresetH;
        g.setColour (Clr::presetBg);
        g.fillRect (0, y, w, kTabH);
    }

    // ── engine section ──────────────────────────────────────────
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

    // ── effects section ─────────────────────────────────────────
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

    // ── distortion row ──────────────────────────────────────────
    {
        int y = distRow_.getY();
        g.setColour (Clr::effectsBg);
        g.fillRect (0, y, w, distRow_.getHeight());
        paintPanel (g, distPanelBounds_, "DISTORTION");
    }

    // ── keyboard footer ─────────────────────────────────────────
    {
        int y = distRow_.getBottom();
        g.setColour (Clr::kbFooter);
        g.fillRect (0, y, w, getHeight() - y);
        g.setColour (Clr::borderLight);
        g.drawHorizontalLine (y, 0.0f, (float) w);
    }
}

// ════════════════════════════════════════════════════════════════════════
//  Resized — top-to-bottom layout
// ════════════════════════════════════════════════════════════════════════
void TsukiSynthEditor::resized()
{
    auto area = getLocalBounds();

    // ── title (paint only) ──────────────────────────────────────
    area.removeFromTop (kTitleH);

    // ── preset row ──────────────────────────────────────────────
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

        presetCombo.setBounds (inner);
    }

    // ── engine tabs ─────────────────────────────────────────────
    {
        auto row   = area.removeFromTop (kTabH);
        auto inner = row.reduced (kSidePad, 0).withTrimmedTop (4);
        int tw = inner.getWidth() / 3;
        tabCim.setBounds (inner.removeFromLeft (tw));
        tabChr.setBounds (inner.removeFromLeft (tw));
        tabFM.setBounds  (inner);
    }

    // ── bottom sections (fixed sizes, from bottom up) ───────────
    auto kbArea = area.removeFromBottom (kKeyboardH);
    keyboard.setBounds (kbArea.reduced (14, 10));

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

    // ── engine section (remaining space) ────────────────────────
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
            layoutComboCell (l0, chrSubEngine);
            layoutComboCell (r0, chrMaterial);

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
}
