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

    // FM Piano controls
    setupCombo  (fmTypeCombo,         "fm_type",         "Type");
    setupSlider (fmRatioSlider,       "fm_ratio",        "Ratio");
    setupSlider (fmIndexSlider,       "fm_index",        "Mod Index");
    setupSlider (fmBrightnessSlider,  "fm_brightness",   "Brightness");
    setupSlider (fmFeedbackSlider,    "fm_feedback",     "Feedback");
    setupSlider (fmAttackSlider,      "fm_attack",       "Attack",    "ms");
    setupSlider (fmReleaseSlider,     "fm_release",      "Release",   "ms");

    // Effect chain controls (always visible)
    setupSlider (fxReverbMixSlider,   "fx_reverb_mix",      "Reverb");
    setupSlider (fxReverbSizeSlider,  "fx_reverb_size",     "Room Size");
    setupSlider (fxDelayTimeSlider,   "fx_delay_time",      "Delay",     "ms");
    setupSlider (fxDelayFbSlider,     "fx_delay_feedback",  "Dly FB");
    setupSlider (fxDelayMixSlider,    "fx_delay_mix",       "Dly Mix");
    setupSlider (fxCompThreshSlider,  "fx_comp_threshold",  "Comp",      "dB");
    setupSlider (fxCompRatioSlider,   "fx_comp_ratio",      "Ratio");

    // Listen for engine changes
    processorRef.apvts.addParameterListener ("engine", this);

    updateEngineVisibility();
    setSize (520, 580);
}

TsukiSynthEditor::~TsukiSynthEditor()
{
    processorRef.apvts.removeParameterListener ("engine", this);
}

void TsukiSynthEditor::parameterChanged (const juce::String& parameterID, float)
{
    if (parameterID == "engine")
    {
        juce::MessageManager::callAsync ([this]() {
            updateEngineVisibility();
            resized();
        });
    }
}

void TsukiSynthEditor::updateEngineVisibility()
{
    int engine = (int) processorRef.apvts.getRawParameterValue ("engine")->load();
    bool isCim = (engine == 0);
    bool isChr = (engine == 1);
    bool isFM  = (engine == 2);

    // Cimbalom
    setComponentVisible (cimMaterialCombo,    isCim);
    setComponentVisible (cimHammerCombo,      isCim);
    setComponentVisible (cimStrikePosSlider,  isCim);
    setComponentVisible (cimDiameterSlider,   isCim);
    setComponentVisible (cimNumStringsSlider, isCim);
    setComponentVisible (cimDetuningSlider,   isCim);

    // Chromatic
    setComponentVisible (chrSubEngineCombo,   isChr);
    setComponentVisible (chrMaterialCombo,    isChr);
    setComponentVisible (chrStrikePosSlider,  isChr);
    setComponentVisible (chrThicknessSlider,  isChr);
    setComponentVisible (chrSizeSlider,       isChr);
    setComponentVisible (chrExciterCombo,     isChr);
    setComponentVisible (chrPitchGlideSlider, isChr);

    // FM Piano
    setComponentVisible (fmTypeCombo,        isFM);
    setComponentVisible (fmRatioSlider,      isFM);
    setComponentVisible (fmIndexSlider,      isFM);
    setComponentVisible (fmBrightnessSlider, isFM);
    setComponentVisible (fmFeedbackSlider,   isFM);
    setComponentVisible (fmAttackSlider,     isFM);
    setComponentVisible (fmReleaseSlider,    isFM);

    // Effects are always visible
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
    juce::String subtitle;
    switch (engine)
    {
        case 0: subtitle = "Cimbalom Engine  |  Physical Modeling String"; break;
        case 1: subtitle = "Chromatic Engine  |  Beam / Plate / Custom"; break;
        case 2: subtitle = "FM Piano Engine  |  Frequency Modulation Synthesis"; break;
        default: subtitle = "TsukiSynth"; break;
    }
    g.drawFittedText (subtitle, 0, 34, getWidth(), 18,
                      juce::Justification::centred, 1);

    // Divider after engine subtitle
    g.setColour (juce::Colour (0xff333355));
    g.drawHorizontalLine (56, 20.0f, (float) getWidth() - 20.0f);

    // Divider before effects section
    int fxDividerY = getHeight() - 155;
    g.setColour (juce::Colour (0xff333355));
    g.drawHorizontalLine (fxDividerY, 20.0f, (float) getWidth() - 20.0f);

    // Effects section label
    g.setColour (juce::Colour (0xff7788aa));
    g.setFont (juce::FontOptions (11.0f));
    g.drawFittedText ("EFFECTS", 20, fxDividerY + 2, 60, 14,
                      juce::Justification::centredLeft, 1);
}

void TsukiSynthEditor::resized()
{
    auto area = getLocalBounds().reduced (20).withTrimmedTop (50);
    int rowH = 40;
    int labelW = 80;
    int gap = 4;

    // Row 0: Engine selector
    auto row0 = area.removeFromTop (rowH);
    engineCombo.label->setBounds (row0.removeFromLeft (labelW));
    engineCombo.combo->setBounds (row0.reduced (2));
    area.removeFromTop (gap);

    int engine = (int) processorRef.apvts.getRawParameterValue ("engine")->load();

    if (engine == 0)
    {
        // ===== Cimbalom layout =====
        auto row1 = area.removeFromTop (rowH);
        int half = row1.getWidth() / 2;
        cimMaterialCombo.label->setBounds (row1.removeFromLeft (labelW));
        cimMaterialCombo.combo->setBounds (row1.removeFromLeft (half - labelW - 10).reduced (2));
        row1.removeFromLeft (20);
        cimHammerCombo.label->setBounds (row1.removeFromLeft (60));
        cimHammerCombo.combo->setBounds (row1.reduced (2));
        area.removeFromTop (gap);

        auto row2 = area.removeFromTop (rowH);
        cimStrikePosSlider.label->setBounds (row2.removeFromLeft (labelW));
        cimStrikePosSlider.slider->setBounds (row2.reduced (2));
        area.removeFromTop (gap);

        auto row3 = area.removeFromTop (rowH);
        cimDiameterSlider.label->setBounds (row3.removeFromLeft (labelW));
        cimDiameterSlider.slider->setBounds (row3.reduced (2));
        area.removeFromTop (gap);

        auto row4 = area.removeFromTop (rowH);
        auto r4left = row4.removeFromLeft (row4.getWidth() / 2);
        cimNumStringsSlider.label->setBounds (r4left.removeFromLeft (labelW));
        cimNumStringsSlider.slider->setBounds (r4left.reduced (2));
        cimDetuningSlider.label->setBounds (row4.removeFromLeft (labelW));
        cimDetuningSlider.slider->setBounds (row4.reduced (2));
    }
    else if (engine == 1)
    {
        // ===== Chromatic layout =====
        auto row1 = area.removeFromTop (rowH);
        int half = row1.getWidth() / 2;
        chrSubEngineCombo.label->setBounds (row1.removeFromLeft (60));
        chrSubEngineCombo.combo->setBounds (row1.removeFromLeft (half - 70).reduced (2));
        row1.removeFromLeft (20);
        chrMaterialCombo.label->setBounds (row1.removeFromLeft (60));
        chrMaterialCombo.combo->setBounds (row1.reduced (2));
        area.removeFromTop (gap);

        auto row2 = area.removeFromTop (rowH);
        chrStrikePosSlider.label->setBounds (row2.removeFromLeft (labelW));
        chrStrikePosSlider.slider->setBounds (row2.reduced (2));
        area.removeFromTop (gap);

        auto row3 = area.removeFromTop (rowH);
        auto r3left = row3.removeFromLeft (row3.getWidth() / 2);
        chrThicknessSlider.label->setBounds (r3left.removeFromLeft (labelW));
        chrThicknessSlider.slider->setBounds (r3left.reduced (2));
        chrSizeSlider.label->setBounds (row3.removeFromLeft (labelW));
        chrSizeSlider.slider->setBounds (row3.reduced (2));
        area.removeFromTop (gap);

        auto row4 = area.removeFromTop (rowH);
        auto r4left = row4.removeFromLeft (row4.getWidth() / 2);
        chrExciterCombo.label->setBounds (r4left.removeFromLeft (60));
        chrExciterCombo.combo->setBounds (r4left.reduced (2));
        chrPitchGlideSlider.label->setBounds (row4.removeFromLeft (labelW));
        chrPitchGlideSlider.slider->setBounds (row4.reduced (2));
    }
    else
    {
        // ===== FM Piano layout =====
        auto row1 = area.removeFromTop (rowH);
        fmTypeCombo.label->setBounds (row1.removeFromLeft (labelW));
        fmTypeCombo.combo->setBounds (row1.reduced (2));
        area.removeFromTop (gap);

        auto row2 = area.removeFromTop (rowH);
        auto r2left = row2.removeFromLeft (row2.getWidth() / 2);
        fmRatioSlider.label->setBounds (r2left.removeFromLeft (labelW));
        fmRatioSlider.slider->setBounds (r2left.reduced (2));
        fmIndexSlider.label->setBounds (row2.removeFromLeft (labelW));
        fmIndexSlider.slider->setBounds (row2.reduced (2));
        area.removeFromTop (gap);

        auto row3 = area.removeFromTop (rowH);
        auto r3left = row3.removeFromLeft (row3.getWidth() / 2);
        fmBrightnessSlider.label->setBounds (r3left.removeFromLeft (labelW));
        fmBrightnessSlider.slider->setBounds (r3left.reduced (2));
        fmFeedbackSlider.label->setBounds (row3.removeFromLeft (labelW));
        fmFeedbackSlider.slider->setBounds (row3.reduced (2));
        area.removeFromTop (gap);

        auto row4 = area.removeFromTop (rowH);
        auto r4left = row4.removeFromLeft (row4.getWidth() / 2);
        fmAttackSlider.label->setBounds (r4left.removeFromLeft (labelW));
        fmAttackSlider.slider->setBounds (r4left.reduced (2));
        fmReleaseSlider.label->setBounds (row4.removeFromLeft (labelW));
        fmReleaseSlider.slider->setBounds (row4.reduced (2));
    }

    // ===== Effects section (always visible, bottom area) =====
    int fxLabelW = 70;
    auto fxArea = getLocalBounds().reduced (20);
    fxArea = fxArea.withTop (getHeight() - 140);

    // FX Row 1: Reverb Mix + Room Size
    auto fxRow1 = fxArea.removeFromTop (36);
    auto fx1left = fxRow1.removeFromLeft (fxRow1.getWidth() / 2);
    fxReverbMixSlider.label->setBounds (fx1left.removeFromLeft (fxLabelW));
    fxReverbMixSlider.slider->setBounds (fx1left.reduced (2));
    fxReverbSizeSlider.label->setBounds (fxRow1.removeFromLeft (fxLabelW));
    fxReverbSizeSlider.slider->setBounds (fxRow1.reduced (2));
    fxArea.removeFromTop (2);

    // FX Row 2: Delay Time + Delay Feedback + Delay Mix
    auto fxRow2 = fxArea.removeFromTop (36);
    int thirdW = fxRow2.getWidth() / 3;
    auto fx2a = fxRow2.removeFromLeft (thirdW);
    auto fx2b = fxRow2.removeFromLeft (thirdW);
    fxDelayTimeSlider.label->setBounds (fx2a.removeFromLeft (fxLabelW));
    fxDelayTimeSlider.slider->setBounds (fx2a.reduced (2));
    fxDelayFbSlider.label->setBounds (fx2b.removeFromLeft (50));
    fxDelayFbSlider.slider->setBounds (fx2b.reduced (2));
    fxDelayMixSlider.label->setBounds (fxRow2.removeFromLeft (55));
    fxDelayMixSlider.slider->setBounds (fxRow2.reduced (2));
    fxArea.removeFromTop (2);

    // FX Row 3: Compressor Threshold + Ratio
    auto fxRow3 = fxArea.removeFromTop (36);
    auto fx3left = fxRow3.removeFromLeft (fxRow3.getWidth() / 2);
    fxCompThreshSlider.label->setBounds (fx3left.removeFromLeft (fxLabelW));
    fxCompThreshSlider.slider->setBounds (fx3left.reduced (2));
    fxCompRatioSlider.label->setBounds (fxRow3.removeFromLeft (fxLabelW));
    fxCompRatioSlider.slider->setBounds (fxRow3.reduced (2));
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

    ps.slider->setTextBoxStyle (juce::Slider::TextBoxRight, false, 55, 22);
    if (suffix.isNotEmpty())
        ps.slider->setTextValueSuffix (" " + suffix);

    ps.label->setColour (juce::Label::textColourId, juce::Colour (0xffcccccc));
    ps.label->setFont (juce::FontOptions (12.0f));

    addAndMakeVisible (*ps.slider);
    addAndMakeVisible (*ps.label);

    ps.attachment = std::make_unique<juce::AudioProcessorValueTreeState::SliderAttachment> (
        processorRef.apvts, paramID, *ps.slider);
}
