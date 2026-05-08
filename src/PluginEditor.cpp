#include "PluginEditor.h"
#include "Presets.h"

namespace Clr
{
    static const juce::Colour bg          (0xff12121c);
    static const juce::Colour panelBg     (0xff1e1e2e);
    static const juce::Colour panelBorder (0xff2a2a40);
    static const juce::Colour accent      (0xffc8a2c8);
    static const juce::Colour accentDim   (0xff8b6f8b);
    static const juce::Colour text        (0xffe8e0f0);
    static const juce::Colour textDim     (0xff9090a8);
    static const juce::Colour knobTrack   (0xff3a3a52);
    static const juce::Colour knobFill    (0xff9478b8);
}

// ============================================================
TsukiSynthEditor::TsukiSynthEditor (TsukiSynthProcessor& p)
    : AudioProcessorEditor (&p),
      processorRef (p),
      keyboardComponent (keyboardState,
                         juce::MidiKeyboardComponent::horizontalKeyboard)
{
    // -- Keyboard --
    keyboardComponent.setColour (
        juce::MidiKeyboardComponent::keyDownOverlayColourId,
        Clr::accent.withAlpha (0.4f));
    keyboardComponent.setColour (
        juce::MidiKeyboardComponent::whiteNoteColourId,
        juce::Colour (0xfff0ecf4));
    keyboardComponent.setColour (
        juce::MidiKeyboardComponent::blackNoteColourId,
        juce::Colour (0xff2a2a3a));
    addAndMakeVisible (keyboardComponent);

    // -- Engine --
    setupCombo (engineCombo, "engine", "ENGINE");

    // -- Preset (manual) --
    presetLabel = std::make_unique<juce::Label>();
    presetLabel->setText ("PRESET", juce::dontSendNotification);
    presetLabel->setColour (juce::Label::textColourId, Clr::textDim);
    presetLabel->setFont (juce::FontOptions (11.0f));
    presetLabel->setJustificationType (juce::Justification::centred);
    addAndMakeVisible (*presetLabel);

    presetCombo = std::make_unique<juce::ComboBox>();
    presetCombo->setColour (juce::ComboBox::backgroundColourId, Clr::panelBg);
    presetCombo->setColour (juce::ComboBox::outlineColourId, Clr::panelBorder);
    presetCombo->setColour (juce::ComboBox::textColourId, Clr::text);
    int presetCount = 0;
    auto* presetList = getFactoryPresetList (presetCount);
    for (int i = 0; i < presetCount; ++i)
        presetCombo->addItem (presetList[i].name, i + 1);
    presetCombo->setSelectedId (processorRef.getCurrentProgram() + 1,
                                juce::dontSendNotification);
    presetCombo->onChange = [this]
    {
        processorRef.setCurrentProgram (presetCombo->getSelectedId() - 1);
    };
    addAndMakeVisible (*presetCombo);

    // -- Cimbalom --
    setupCombo  (cimMaterial, "cim_material", "MATERIAL");
    setupSlider (cimStrike,   "cim_strike_pos", "STRIKE");
    setupSlider (cimDiameter, "cim_diameter",   "DIA (mm)");
    setupCombo  (cimHammer,   "cim_hammer",     "HAMMER");
    setupSlider (cimStrings,  "cim_num_strings", "STRINGS");
    setupSlider (cimDetune,   "cim_detuning",   "DETUNE");

    // -- Chromatic --
    setupCombo  (chrSubEngine, "chr_sub_engine", "TYPE");
    setupCombo  (chrMaterial,  "chr_material",   "MATERIAL");
    setupSlider (chrStrike,    "chr_strike_pos", "STRIKE");
    setupSlider (chrThickness, "chr_thickness",  "THICK");
    setupSlider (chrSize,      "chr_size",       "SIZE");
    setupCombo  (chrExciter,   "chr_exciter",    "EXCITER");
    setupSlider (chrGlide,     "chr_pitch_glide","GLIDE");

    // -- FM Piano --
    setupCombo  (fmType,       "fm_type",       "TYPE");
    setupSlider (fmRatio,      "fm_ratio",      "RATIO");
    setupSlider (fmIndex,      "fm_index",      "INDEX");
    setupSlider (fmBrightness, "fm_brightness", "BRIGHT");
    setupSlider (fmFeedback,   "fm_feedback",   "FB");
    setupSlider (fmAttack,     "fm_attack",     "ATK");
    setupSlider (fmRelease,    "fm_release",    "REL");

    // -- Effects (rotary) --
    setupSlider (fxRevMix,     "fx_reverb_mix",      "REVERB",  true);
    setupSlider (fxRevSize,    "fx_reverb_size",      "ROOM",    true);
    setupSlider (fxDlyTime,    "fx_delay_time",       "DLY T",   true);
    setupSlider (fxDlyFeedback,"fx_delay_feedback",   "DLY FB",  true);
    setupSlider (fxDlyMix,     "fx_delay_mix",        "DLY MIX", true);
    setupSlider (fxCompThresh, "fx_comp_threshold",   "COMP",    true);
    setupSlider (fxCompRatio,  "fx_comp_ratio",       "RATIO",   true);

    // -- Distortion (rotary) --
    setupCombo  (distType,        "fx_dist_type",        "TYPE");
    setupSlider (distDrive,       "fx_dist_drive",       "DRIVE",    true);
    setupSlider (distInstability, "fx_dist_instability",  "UNSTABLE", true);
    setupSlider (distMix,         "fx_dist_mix",          "MIX",      true);

    // Listen for engine changes
    processorRef.apvts.addParameterListener ("engine", this);

    updateEngineVisibility();
    setSize (820, 640);
}

TsukiSynthEditor::~TsukiSynthEditor()
{
    processorRef.apvts.removeParameterListener ("engine", this);
}

// ============================================================
void TsukiSynthEditor::parameterChanged (const juce::String& id, float)
{
    if (id == "engine")
        juce::MessageManager::callAsync ([this] { updateEngineVisibility(); resized(); });
}

void TsukiSynthEditor::updateEngineVisibility()
{
    int eng = (int) processorRef.apvts.getRawParameterValue ("engine")->load();

    bool isCim = (eng == 0);
    bool isChr = (eng == 1);
    bool isFM  = (eng == 2);

    setVisible (cimMaterial, isCim);  setVisible (cimHammer, isCim);
    setVisible (cimStrike, isCim);    setVisible (cimDiameter, isCim);
    setVisible (cimStrings, isCim);   setVisible (cimDetune, isCim);

    setVisible (chrSubEngine, isChr); setVisible (chrMaterial, isChr);
    setVisible (chrStrike, isChr);    setVisible (chrThickness, isChr);
    setVisible (chrSize, isChr);      setVisible (chrExciter, isChr);
    setVisible (chrGlide, isChr);

    setVisible (fmType, isFM);        setVisible (fmRatio, isFM);
    setVisible (fmIndex, isFM);       setVisible (fmBrightness, isFM);
    setVisible (fmFeedback, isFM);    setVisible (fmAttack, isFM);
    setVisible (fmRelease, isFM);
}

// ============================================================
void TsukiSynthEditor::setupSlider (ParamSlider& ps, const juce::String& paramID,
                                     const juce::String& labelText, bool rotary)
{
    ps.slider = std::make_unique<juce::Slider>();
    ps.label  = std::make_unique<juce::Label>();

    if (rotary)
    {
        ps.slider->setSliderStyle (juce::Slider::RotaryVerticalDrag);
        ps.slider->setTextBoxStyle (juce::Slider::TextBoxBelow, false, 46, 14);
        ps.slider->setColour (juce::Slider::rotarySliderFillColourId, Clr::knobFill);
        ps.slider->setColour (juce::Slider::rotarySliderOutlineColourId, Clr::knobTrack);
        ps.slider->setColour (juce::Slider::thumbColourId, Clr::accent);
    }
    else
    {
        ps.slider->setTextBoxStyle (juce::Slider::TextBoxRight, false, 50, 18);
        ps.slider->setColour (juce::Slider::thumbColourId, Clr::accent);
        ps.slider->setColour (juce::Slider::trackColourId, Clr::knobTrack);
    }
    ps.slider->setColour (juce::Slider::textBoxTextColourId, Clr::textDim);
    ps.slider->setColour (juce::Slider::textBoxOutlineColourId,
                          juce::Colours::transparentBlack);
    addAndMakeVisible (*ps.slider);

    ps.label->setText (labelText, juce::dontSendNotification);
    ps.label->setColour (juce::Label::textColourId, Clr::textDim);
    ps.label->setFont (juce::FontOptions (11.0f));
    ps.label->setJustificationType (juce::Justification::centred);
    addAndMakeVisible (*ps.label);

    ps.attachment = std::make_unique<SliderAttachment> (
        processorRef.apvts, paramID, *ps.slider);
}

void TsukiSynthEditor::setupCombo (ParamCombo& pc, const juce::String& paramID,
                                    const juce::String& labelText)
{
    pc.combo = std::make_unique<juce::ComboBox>();
    pc.label = std::make_unique<juce::Label>();

    pc.combo->setColour (juce::ComboBox::backgroundColourId, Clr::panelBg);
    pc.combo->setColour (juce::ComboBox::outlineColourId, Clr::panelBorder);
    pc.combo->setColour (juce::ComboBox::textColourId, Clr::text);

    if (auto* choiceParam = dynamic_cast<juce::AudioParameterChoice*> (
            processorRef.apvts.getParameter (paramID)))
    {
        int id = 1;
        for (const auto& choice : choiceParam->choices)
            pc.combo->addItem (choice, id++);
    }
    addAndMakeVisible (*pc.combo);

    pc.label->setText (labelText, juce::dontSendNotification);
    pc.label->setColour (juce::Label::textColourId, Clr::textDim);
    pc.label->setFont (juce::FontOptions (11.0f));
    pc.label->setJustificationType (juce::Justification::centred);
    addAndMakeVisible (*pc.label);

    pc.attachment = std::make_unique<ComboAttachment> (
        processorRef.apvts, paramID, *pc.combo);
}

void TsukiSynthEditor::setVisible (ParamSlider& ps, bool v)
{
    ps.slider->setVisible (v);
    ps.label->setVisible (v);
}

void TsukiSynthEditor::setVisible (ParamCombo& pc, bool v)
{
    pc.combo->setVisible (v);
    pc.label->setVisible (v);
}

// ============================================================
void TsukiSynthEditor::paintPanel (juce::Graphics& g,
                                    juce::Rectangle<int> bounds,
                                    const juce::String& title)
{
    g.setColour (Clr::panelBg);
    g.fillRoundedRectangle (bounds.toFloat(), 6.0f);
    g.setColour (Clr::panelBorder);
    g.drawRoundedRectangle (bounds.toFloat().reduced (0.5f), 6.0f, 1.0f);

    if (title.isNotEmpty())
    {
        g.setColour (Clr::accentDim);
        g.setFont (juce::FontOptions (10.0f));
        g.drawText (title, bounds.getX() + 10, bounds.getY() + 4,
                    120, 14, juce::Justification::centredLeft);
    }
}

// ============================================================
void TsukiSynthEditor::paint (juce::Graphics& g)
{
    g.fillAll (Clr::bg);

    // Header
    auto header = getLocalBounds().removeFromTop (50);
    g.setColour (Clr::accent);
    g.setFont (juce::FontOptions (20.0f));
    g.drawText (juce::CharPointer_UTF8 (
                    "\xe6\x9c\x88\xe5\x85\x89\xe5\x90\x88\xe6\x88\x90\xe5\x99\xa8"),
                header.removeFromLeft (140).withTrimmedLeft (16),
                juce::Justification::centredLeft);
    g.setColour (Clr::text);
    g.setFont (juce::FontOptions (18.0f));
    g.drawText ("TsukiSynth", header.removeFromLeft (130),
                juce::Justification::centredLeft);
    g.setColour (Clr::textDim);
    g.setFont (juce::FontOptions (10.0f));
    g.drawText ("Physical Modeling Multi-Engine", header,
                juce::Justification::centredLeft);

    // Section panels
    paintPanel (g, enginePanelBounds,     "ENGINE");
    paintPanel (g, effectsPanelBounds,    "EFFECTS");
    paintPanel (g, distortionPanelBounds, "DISTORTION");
}

// ============================================================
void TsukiSynthEditor::resized()
{
    auto area = getLocalBounds();

    // Keyboard
    keyboardComponent.setBounds (area.removeFromBottom (90).reduced (8, 4));

    // Header
    area.removeFromTop (54);
    auto content = area.reduced (10, 0);

    // ---- Engine panel ----
    enginePanelBounds = content.removeFromTop (160);
    {
        auto inner = enginePanelBounds.reduced (12, 20);
        inner.removeFromTop (2);

        const int rH = 26, labelW = 60, gap = 4;

        // Row 0: Engine + Preset
        auto row = inner.removeFromTop (rH);
        engineCombo.label->setBounds (row.removeFromLeft (labelW));
        engineCombo.combo->setBounds (row.removeFromLeft (120));
        row.removeFromLeft (12);
        presetLabel->setBounds (row.removeFromLeft (50));
        presetCombo->setBounds (row.removeFromLeft (180));

        inner.removeFromTop (gap);

        int eng = (int) processorRef.apvts.getRawParameterValue ("engine")->load();

        if (eng == 0) // Cimbalom
        {
            row = inner.removeFromTop (rH);
            cimMaterial.label->setBounds (row.removeFromLeft (labelW));
            cimMaterial.combo->setBounds (row.removeFromLeft (130));
            row.removeFromLeft (12);
            cimHammer.label->setBounds (row.removeFromLeft (55));
            cimHammer.combo->setBounds (row.removeFromLeft (100));

            inner.removeFromTop (gap);
            row = inner.removeFromTop (rH);
            cimStrike.label->setBounds (row.removeFromLeft (labelW));
            cimStrike.slider->setBounds (row.removeFromLeft (160));
            row.removeFromLeft (12);
            cimDiameter.label->setBounds (row.removeFromLeft (55));
            cimDiameter.slider->setBounds (row.removeFromLeft (160));

            inner.removeFromTop (gap);
            row = inner.removeFromTop (rH);
            cimStrings.label->setBounds (row.removeFromLeft (labelW));
            cimStrings.slider->setBounds (row.removeFromLeft (120));
            row.removeFromLeft (12);
            cimDetune.label->setBounds (row.removeFromLeft (55));
            cimDetune.slider->setBounds (row.removeFromLeft (160));
        }
        else if (eng == 1) // Chromatic
        {
            row = inner.removeFromTop (rH);
            chrSubEngine.label->setBounds (row.removeFromLeft (labelW));
            chrSubEngine.combo->setBounds (row.removeFromLeft (130));
            row.removeFromLeft (12);
            chrMaterial.label->setBounds (row.removeFromLeft (55));
            chrMaterial.combo->setBounds (row.removeFromLeft (130));

            inner.removeFromTop (gap);
            row = inner.removeFromTop (rH);
            chrStrike.label->setBounds (row.removeFromLeft (labelW));
            chrStrike.slider->setBounds (row.removeFromLeft (140));
            row.removeFromLeft (12);
            chrExciter.label->setBounds (row.removeFromLeft (55));
            chrExciter.combo->setBounds (row.removeFromLeft (100));

            inner.removeFromTop (gap);
            row = inner.removeFromTop (rH);
            chrThickness.label->setBounds (row.removeFromLeft (labelW));
            chrThickness.slider->setBounds (row.removeFromLeft (110));
            row.removeFromLeft (8);
            chrSize.label->setBounds (row.removeFromLeft (40));
            chrSize.slider->setBounds (row.removeFromLeft (110));
            row.removeFromLeft (8);
            chrGlide.label->setBounds (row.removeFromLeft (40));
            chrGlide.slider->setBounds (row.removeFromLeft (110));
        }
        else // FM Piano
        {
            row = inner.removeFromTop (rH);
            fmType.label->setBounds (row.removeFromLeft (labelW));
            fmType.combo->setBounds (row.removeFromLeft (130));
            row.removeFromLeft (12);
            fmRatio.label->setBounds (row.removeFromLeft (45));
            fmRatio.slider->setBounds (row.removeFromLeft (160));

            inner.removeFromTop (gap);
            row = inner.removeFromTop (rH);
            fmIndex.label->setBounds (row.removeFromLeft (labelW));
            fmIndex.slider->setBounds (row.removeFromLeft (130));
            row.removeFromLeft (12);
            fmBrightness.label->setBounds (row.removeFromLeft (50));
            fmBrightness.slider->setBounds (row.removeFromLeft (130));

            inner.removeFromTop (gap);
            row = inner.removeFromTop (rH);
            fmFeedback.label->setBounds (row.removeFromLeft (labelW));
            fmFeedback.slider->setBounds (row.removeFromLeft (100));
            row.removeFromLeft (8);
            fmAttack.label->setBounds (row.removeFromLeft (35));
            fmAttack.slider->setBounds (row.removeFromLeft (110));
            row.removeFromLeft (8);
            fmRelease.label->setBounds (row.removeFromLeft (35));
            fmRelease.slider->setBounds (row.removeFromLeft (110));
        }
    }

    content.removeFromTop (8);

    // ---- Bottom panels ----
    auto bottomPanels = content.removeFromTop (190);

    // Effects (left ~60%)
    effectsPanelBounds = bottomPanels.removeFromLeft (
        bottomPanels.getWidth() * 3 / 5 - 4);
    {
        auto inner = effectsPanelBounds.reduced (10, 22);
        const int kW = 62, kH = 80, gap = 6;

        auto knobRow = inner.removeFromTop (kH);
        auto slot = knobRow.removeFromLeft (kW);
        fxRevMix.label->setBounds (slot.removeFromTop (14));
        fxRevMix.slider->setBounds (slot);
        knobRow.removeFromLeft (gap);

        slot = knobRow.removeFromLeft (kW);
        fxRevSize.label->setBounds (slot.removeFromTop (14));
        fxRevSize.slider->setBounds (slot);
        knobRow.removeFromLeft (gap);

        slot = knobRow.removeFromLeft (kW);
        fxDlyMix.label->setBounds (slot.removeFromTop (14));
        fxDlyMix.slider->setBounds (slot);
        knobRow.removeFromLeft (gap);

        slot = knobRow.removeFromLeft (kW);
        fxDlyTime.label->setBounds (slot.removeFromTop (14));
        fxDlyTime.slider->setBounds (slot);
        knobRow.removeFromLeft (gap);

        slot = knobRow.removeFromLeft (kW);
        fxDlyFeedback.label->setBounds (slot.removeFromTop (14));
        fxDlyFeedback.slider->setBounds (slot);

        inner.removeFromTop (gap);
        knobRow = inner.removeFromTop (kH);

        slot = knobRow.removeFromLeft (kW);
        fxCompThresh.label->setBounds (slot.removeFromTop (14));
        fxCompThresh.slider->setBounds (slot);
        knobRow.removeFromLeft (gap);

        slot = knobRow.removeFromLeft (kW);
        fxCompRatio.label->setBounds (slot.removeFromTop (14));
        fxCompRatio.slider->setBounds (slot);
    }

    bottomPanels.removeFromLeft (8);

    // Distortion (right)
    distortionPanelBounds = bottomPanels;
    {
        auto inner = distortionPanelBounds.reduced (10, 22);

        auto typeRow = inner.removeFromTop (24);
        distType.label->setBounds (typeRow.removeFromLeft (34));
        distType.combo->setBounds (typeRow.removeFromLeft (110));

        inner.removeFromTop (8);
        const int kW = 64, kH = 80, gap = 6;
        auto knobRow = inner.removeFromTop (kH);

        auto slot = knobRow.removeFromLeft (kW);
        distDrive.label->setBounds (slot.removeFromTop (14));
        distDrive.slider->setBounds (slot);
        knobRow.removeFromLeft (gap);

        slot = knobRow.removeFromLeft (kW);
        distInstability.label->setBounds (slot.removeFromTop (14));
        distInstability.slider->setBounds (slot);
        knobRow.removeFromLeft (gap);

        slot = knobRow.removeFromLeft (kW);
        distMix.label->setBounds (slot.removeFromTop (14));
        distMix.slider->setBounds (slot);
    }
}
