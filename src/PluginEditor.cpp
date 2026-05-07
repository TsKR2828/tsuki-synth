#include "PluginEditor.h"

TsukiSynthEditor::TsukiSynthEditor (TsukiSynthProcessor& p)
    : AudioProcessorEditor (&p), processorRef (p)
{
    // Engine selector
    setupCombo (engineCombo, "engine", "Engine");

    // Cimbalom controls
    setupCombo  (cimMaterialCombo,    "cim_material",    "Material");
    setupCombo  (cimHammerCombo,      "cim_hammer",      "Hammer");
    setupSlider (cimStrikePosSlider,  "cim_strike_pos",  "Strike Pos");
    setupSlider (cimDiameterSlider,   "cim_diameter",    "Diameter",  "mm");
    setupSlider (cimNumStringsSlider, "cim_num_strings", "Strings");
    setupSlider (cimDetuningSlider,   "cim_detuning",    "Detuning",  "ct");

    // Chromatic controls
    setupCombo  (chrSubEngineCombo,   "chr_sub_engine",  "Type");
    setupCombo  (chrMaterialCombo,    "chr_material",    "Material");
    setupSlider (chrStrikePosSlider,  "chr_strike_pos",  "Strike Pos");
    setupSlider (chrThicknessSlider,  "chr_thickness",   "Thickness", "mm");
    setupSlider (chrSizeSlider,       "chr_size",        "Size",      "mm");
    setupCombo  (chrExciterCombo,     "chr_exciter",     "Exciter");
    setupSlider (chrPitchGlideSlider, "chr_pitch_glide", "Pitch Glide");

    // Listen for engine changes
    processorRef.apvts.addParameterListener ("engine", this);

    updateEngineVisibility();
    setSize (520, 440);
}

TsukiSynthEditor::~TsukiSynthEditor()
{
    processorRef.apvts.removeParameterListener ("engine", this);
}

void TsukiSynthEditor::parameterChanged (const juce::String& parameterID, float)
{
    if (parameterID == "engine")
    {
        // Must be called on message thread
        juce::MessageManager::callAsync ([this]() { updateEngineVisibility(); });
    }
}

void TsukiSynthEditor::updateEngineVisibility()
{
    int engine = (int) processorRef.apvts.getRawParameterValue ("engine")->load();
    bool isCim = (engine == 0);
    bool isChr = (engine == 1);

    setComponentVisible (cimMaterialCombo,    isCim);
    setComponentVisible (cimHammerCombo,      isCim);
    setComponentVisible (cimStrikePosSlider,  isCim);
    setComponentVisible (cimDiameterSlider,   isCim);
    setComponentVisible (cimNumStringsSlider, isCim);
    setComponentVisible (cimDetuningSlider,   isCim);

    setComponentVisible (chrSubEngineCombo,   isChr);
    setComponentVisible (chrMaterialCombo,    isChr);
    setComponentVisible (chrStrikePosSlider,  isChr);
    setComponentVisible (chrThicknessSlider,  isChr);
    setComponentVisible (chrSizeSlider,       isChr);
    setComponentVisible (chrExciterCombo,     isChr);
    setComponentVisible (chrPitchGlideSlider, isChr);

    repaint();
}

void TsukiSynthEditor::setComponentVisible (ParamCombo& pc, bool visible)
{
    pc.combo->setVisible (visible);
    pc.label->setVisible (visible);
}

void TsukiSynthEditor::setComponentVisible (ParamSlider& ps, bool visible)
{
    ps.slider->setVisible (visible);
    ps.label->setVisible (visible);
}

void TsukiSynthEditor::paint (juce::Graphics& g)
{
    g.fillAll (juce::Colour (0xff1a1a2e));

    // Title
    g.setColour (juce::Colour (0xffe0e0e0));
    g.setFont (juce::FontOptions (24.0f));
    g.drawFittedText ("TsukiSynth", 0, 8, getWidth(), 30,
                      juce::Justification::centred, 1);

    // Subtitle changes with engine
    int engine = (int) processorRef.apvts.getRawParameterValue ("engine")->load();
    g.setColour (juce::Colour (0xff888888));
    g.setFont (juce::FontOptions (12.0f));
    juce::String subtitle = (engine == 0)
        ? "Cimbalom Engine  |  Physical Modeling String"
        : "Chromatic Engine  |  Beam / Plate / Custom";
    g.drawFittedText (subtitle, 0, 34, getWidth(), 18,
                      juce::Justification::centred, 1);

    // Divider
    g.setColour (juce::Colour (0xff333355));
    g.drawHorizontalLine (56, 20.0f, (float) getWidth() - 20.0f);
}

void TsukiSynthEditor::resized()
{
    auto area = getLocalBounds().reduced (20).withTrimmedTop (50);
    int rowH = 44;
    int labelW = 80;
    int gap = 6;

    // Row 0: Engine selector
    auto row0 = area.removeFromTop (rowH);
    engineCombo.label->setBounds (row0.removeFromLeft (labelW));
    engineCombo.combo->setBounds (row0.reduced (2));
    area.removeFromTop (gap);

    // ===== Cimbalom layout =====
    int engine = (int) processorRef.apvts.getRawParameterValue ("engine")->load();

    if (engine == 0)
    {
        // Row 1: Material + Hammer
        auto row1 = area.removeFromTop (rowH);
        int half = row1.getWidth() / 2;
        cimMaterialCombo.label->setBounds (row1.removeFromLeft (labelW));
        cimMaterialCombo.combo->setBounds (row1.removeFromLeft (half - labelW - 10).reduced (2));
        row1.removeFromLeft (20);
        cimHammerCombo.label->setBounds (row1.removeFromLeft (60));
        cimHammerCombo.combo->setBounds (row1.reduced (2));
        area.removeFromTop (gap);

        // Row 2: Strike Position
        auto row2 = area.removeFromTop (rowH);
        cimStrikePosSlider.label->setBounds (row2.removeFromLeft (labelW));
        cimStrikePosSlider.slider->setBounds (row2.reduced (2));
        area.removeFromTop (gap);

        // Row 3: Diameter
        auto row3 = area.removeFromTop (rowH);
        cimDiameterSlider.label->setBounds (row3.removeFromLeft (labelW));
        cimDiameterSlider.slider->setBounds (row3.reduced (2));
        area.removeFromTop (gap);

        // Row 4: Strings + Detuning
        auto row4 = area.removeFromTop (rowH);
        auto r4left = row4.removeFromLeft (row4.getWidth() / 2);
        cimNumStringsSlider.label->setBounds (r4left.removeFromLeft (labelW));
        cimNumStringsSlider.slider->setBounds (r4left.reduced (2));
        cimDetuningSlider.label->setBounds (row4.removeFromLeft (labelW));
        cimDetuningSlider.slider->setBounds (row4.reduced (2));
    }
    else
    {
        // ===== Chromatic layout =====

        // Row 1: Sub-engine + Material
        auto row1 = area.removeFromTop (rowH);
        int half = row1.getWidth() / 2;
        chrSubEngineCombo.label->setBounds (row1.removeFromLeft (60));
        chrSubEngineCombo.combo->setBounds (row1.removeFromLeft (half - 70).reduced (2));
        row1.removeFromLeft (20);
        chrMaterialCombo.label->setBounds (row1.removeFromLeft (60));
        chrMaterialCombo.combo->setBounds (row1.reduced (2));
        area.removeFromTop (gap);

        // Row 2: Strike Position
        auto row2 = area.removeFromTop (rowH);
        chrStrikePosSlider.label->setBounds (row2.removeFromLeft (labelW));
        chrStrikePosSlider.slider->setBounds (row2.reduced (2));
        area.removeFromTop (gap);

        // Row 3: Thickness + Size
        auto row3 = area.removeFromTop (rowH);
        auto r3left = row3.removeFromLeft (row3.getWidth() / 2);
        chrThicknessSlider.label->setBounds (r3left.removeFromLeft (labelW));
        chrThicknessSlider.slider->setBounds (r3left.reduced (2));
        chrSizeSlider.label->setBounds (row3.removeFromLeft (labelW));
        chrSizeSlider.slider->setBounds (row3.reduced (2));
        area.removeFromTop (gap);

        // Row 4: Exciter + Pitch Glide
        auto row4 = area.removeFromTop (rowH);
        auto r4left = row4.removeFromLeft (row4.getWidth() / 2);
        chrExciterCombo.label->setBounds (r4left.removeFromLeft (60));
        chrExciterCombo.combo->setBounds (r4left.reduced (2));
        chrPitchGlideSlider.label->setBounds (row4.removeFromLeft (labelW));
        chrPitchGlideSlider.slider->setBounds (row4.reduced (2));
    }
}

void TsukiSynthEditor::setupCombo (ParamCombo& pc, const juce::String& paramID,
                                    const juce::String& labelText)
{
    pc.combo = std::make_unique<juce::ComboBox>();
    pc.label = std::make_unique<juce::Label> ("", labelText);

    if (auto* param = dynamic_cast<juce::AudioParameterChoice*> (
            processorRef.apvts.getParameter (paramID)))
    {
        int id = 1;
        for (auto& choice : param->choices)
            pc.combo->addItem (choice, id++);
    }

    pc.label->setColour (juce::Label::textColourId, juce::Colour (0xffcccccc));
    pc.label->setFont (juce::FontOptions (13.0f));

    addAndMakeVisible (*pc.combo);
    addAndMakeVisible (*pc.label);

    pc.attachment = std::make_unique<juce::AudioProcessorValueTreeState::ComboBoxAttachment> (
        processorRef.apvts, paramID, *pc.combo);
}

void TsukiSynthEditor::setupSlider (ParamSlider& ps, const juce::String& paramID,
                                     const juce::String& labelText,
                                     const juce::String& suffix)
{
    ps.slider = std::make_unique<juce::Slider> (juce::Slider::LinearHorizontal,
                                                 juce::Slider::TextBoxRight);
    ps.label  = std::make_unique<juce::Label> ("", labelText);

    ps.slider->setTextBoxStyle (juce::Slider::TextBoxRight, false, 60, 24);
    if (suffix.isNotEmpty())
        ps.slider->setTextValueSuffix (" " + suffix);

    ps.label->setColour (juce::Label::textColourId, juce::Colour (0xffcccccc));
    ps.label->setFont (juce::FontOptions (13.0f));

    addAndMakeVisible (*ps.slider);
    addAndMakeVisible (*ps.label);

    ps.attachment = std::make_unique<juce::AudioProcessorValueTreeState::SliderAttachment> (
        processorRef.apvts, paramID, *ps.slider);
}
