#include "PluginEditor.h"

TsukiSynthEditor::TsukiSynthEditor (TsukiSynthProcessor& p)
    : AudioProcessorEditor (&p), processorRef (p)
{
    setupCombo  (materialCombo,    "cim_material",    "Material");
    setupCombo  (hammerCombo,      "cim_hammer",      "Hammer");
    setupSlider (strikePosSlider,  "cim_strike_pos",  "Strike Pos");
    setupSlider (diameterSlider,   "cim_diameter",    "Diameter",     "mm");
    setupSlider (numStringsSlider, "cim_num_strings", "Strings");
    setupSlider (detuningSlider,   "cim_detuning",    "Detuning",    "ct");

    setSize (520, 380);
}

TsukiSynthEditor::~TsukiSynthEditor() {}

void TsukiSynthEditor::paint (juce::Graphics& g)
{
    g.fillAll (juce::Colour (0xff1a1a2e));

    // 標題
    g.setColour (juce::Colour (0xffe0e0e0));
    g.setFont (juce::FontOptions (24.0f));
    g.drawFittedText ("TsukiSynth", 0, 8, getWidth(), 30,
                      juce::Justification::centred, 1);

    // 副標
    g.setColour (juce::Colour (0xff888888));
    g.setFont (juce::FontOptions (12.0f));
    g.drawFittedText ("Cimbalom Engine  |  Physical Modeling String",
                      0, 34, getWidth(), 18,
                      juce::Justification::centred, 1);

    // 分隔線
    g.setColour (juce::Colour (0xff333355));
    g.drawHorizontalLine (56, 20.0f, (float) getWidth() - 20.0f);
}

void TsukiSynthEditor::resized()
{
    auto area = getLocalBounds().reduced (20).withTrimmedTop (50);
    int rowH = 50;

    // Row 1: Material + Hammer
    auto row1 = area.removeFromTop (rowH);
    auto half = row1.getWidth() / 2;
    materialCombo.label->setBounds (row1.removeFromLeft (70));
    materialCombo.combo->setBounds (row1.removeFromLeft (half - 80).reduced (2));
    row1.removeFromLeft (20);
    hammerCombo.label->setBounds (row1.removeFromLeft (60));
    hammerCombo.combo->setBounds (row1.reduced (2));

    area.removeFromTop (8);

    // Row 2: Strike Position
    auto row2 = area.removeFromTop (rowH);
    strikePosSlider.label->setBounds (row2.removeFromLeft (80));
    strikePosSlider.slider->setBounds (row2.reduced (2));

    area.removeFromTop (4);

    // Row 3: Diameter
    auto row3 = area.removeFromTop (rowH);
    diameterSlider.label->setBounds (row3.removeFromLeft (80));
    diameterSlider.slider->setBounds (row3.reduced (2));

    area.removeFromTop (4);

    // Row 4: Strings + Detuning
    auto row4 = area.removeFromTop (rowH);
    auto r4left = row4.removeFromLeft (row4.getWidth() / 2);
    numStringsSlider.label->setBounds (r4left.removeFromLeft (80));
    numStringsSlider.slider->setBounds (r4left.reduced (2));
    detuningSlider.label->setBounds (row4.removeFromLeft (80));
    detuningSlider.slider->setBounds (row4.reduced (2));
}

void TsukiSynthEditor::setupCombo (ParamCombo& pc, const juce::String& paramID,
                                    const juce::String& labelText)
{
    pc.combo = std::make_unique<juce::ComboBox>();
    pc.label = std::make_unique<juce::Label> ("", labelText);

    // 從 APVTS 取得選項
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
