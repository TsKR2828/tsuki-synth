#include "PluginEditor.h"

namespace Colours
{
    static const juce::Colour bg         (0xff12121c);
    static const juce::Colour panelBg    (0xff1e1e2e);
    static const juce::Colour panelBorder (0xff2a2a40);
    static const juce::Colour accent     (0xffc8a2c8);
    static const juce::Colour accentDim  (0xff8b6f8b);
    static const juce::Colour text       (0xffe8e0f0);
    static const juce::Colour textDim    (0xff9090a8);
    static const juce::Colour knobTrack  (0xff3a3a52);
    static const juce::Colour knobFill   (0xff9478b8);
}

static void initLabel (juce::Label& l, const juce::String& t, juce::Component* p)
{
    l.setText (t, juce::dontSendNotification);
    l.setColour (juce::Label::textColourId, Colours::textDim);
    l.setFont (juce::FontOptions (11.5f));
    l.setJustificationType (juce::Justification::centred);
    p->addAndMakeVisible (l);
}

static void initRotary (juce::Slider& s, double lo, double hi, double step,
                         double val, juce::Component* p)
{
    s.setSliderStyle (juce::Slider::RotaryVerticalDrag);
    s.setRange (lo, hi, step);
    s.setValue (val, juce::dontSendNotification);
    s.setTextBoxStyle (juce::Slider::TextBoxBelow, false, 46, 14);
    s.setColour (juce::Slider::rotarySliderFillColourId, Colours::knobFill);
    s.setColour (juce::Slider::rotarySliderOutlineColourId, Colours::knobTrack);
    s.setColour (juce::Slider::thumbColourId, Colours::accent);
    s.setColour (juce::Slider::textBoxTextColourId, Colours::textDim);
    s.setColour (juce::Slider::textBoxOutlineColourId, juce::Colours::transparentBlack);
    p->addAndMakeVisible (s);
}

static void initLinear (juce::Slider& s, double lo, double hi, double step,
                         double val, juce::Component* p)
{
    s.setRange (lo, hi, step);
    s.setValue (val, juce::dontSendNotification);
    s.setTextBoxStyle (juce::Slider::TextBoxRight, false, 44, 18);
    s.setColour (juce::Slider::thumbColourId, Colours::accent);
    s.setColour (juce::Slider::trackColourId, Colours::knobTrack);
    s.setColour (juce::Slider::textBoxTextColourId, Colours::textDim);
    s.setColour (juce::Slider::textBoxOutlineColourId, juce::Colours::transparentBlack);
    p->addAndMakeVisible (s);
}

TsukiSynthEditor::TsukiSynthEditor (TsukiSynthProcessor& p)
    : AudioProcessorEditor (&p),
      processorRef (p),
      keyboardComponent (keyboardState, juce::MidiKeyboardComponent::horizontalKeyboard)
{
    keyboardState.addListener (this);
    keyboardComponent.setColour (juce::MidiKeyboardComponent::keyDownOverlayColourId,
                                 Colours::accent.withAlpha (0.4f));
    keyboardComponent.setColour (juce::MidiKeyboardComponent::whiteNoteColourId,
                                 juce::Colour (0xfff0ecf4));
    keyboardComponent.setColour (juce::MidiKeyboardComponent::blackNoteColourId,
                                 juce::Colour (0xff2a2a3a));
    addAndMakeVisible (keyboardComponent);

    // Engine selector
    initLabel (engineLabel, "ENGINE", this);
    engineBox.addItem ("Cimbalom", 1);
    engineBox.addItem ("Chromatic", 2);
    engineBox.addItem ("FM Piano", 3);
    engineBox.setSelectedId (1, juce::dontSendNotification);
    engineBox.setColour (juce::ComboBox::backgroundColourId, Colours::panelBg);
    engineBox.setColour (juce::ComboBox::outlineColourId, Colours::panelBorder);
    engineBox.setColour (juce::ComboBox::textColourId, Colours::text);
    engineBox.onChange = [this]
    {
        int id = engineBox.getSelectedId();
        EngineType e = id == 1 ? EngineType::Cimbalom
                     : id == 2 ? EngineType::Chromatic
                               : EngineType::FMPiano;
        processorRef.setEngineType (e);
        showEngineControls();
        resized();
    };
    addAndMakeVisible (engineBox);

    // Material
    initLabel (materialLabel, "MATERIAL", this);
    populateMaterialBox();
    materialBox.setColour (juce::ComboBox::backgroundColourId, Colours::panelBg);
    materialBox.setColour (juce::ComboBox::outlineColourId, Colours::panelBorder);
    materialBox.setColour (juce::ComboBox::textColourId, Colours::text);
    materialBox.onChange = [this]
    {
        int idx = materialBox.getSelectedId() - 1;
        auto keys = processorRef.getMaterialDB().getMaterialKeys();
        if (idx >= 0 && idx < static_cast<int> (keys.size()))
        {
            processorRef.setMaterial (keys[static_cast<size_t> (idx)]);
            processorRef.updateVoiceParams();
        }
    };
    addAndMakeVisible (materialBox);

    // Strike position
    initLabel (strikeLabel, "STRIKE", this);
    initLinear (strikeSlider, 0.05, 0.95, 0.01, 0.3, this);
    strikeSlider.onValueChange = [this]
    {
        processorRef.getCimbalomParams().strikePosition = strikeSlider.getValue();
        processorRef.getChromaticParams().strikePosition = strikeSlider.getValue();
        processorRef.updateVoiceParams();
    };

    // --- Cimbalom controls ---
    initLabel (exciterLabel, "EXCITER", this);
    exciterBox.addItem ("Cotton", 1);
    exciterBox.addItem ("Felt", 2);
    exciterBox.addItem ("Wood", 3);
    exciterBox.addItem ("Metal", 4);
    exciterBox.setSelectedId (3, juce::dontSendNotification);
    exciterBox.setColour (juce::ComboBox::backgroundColourId, Colours::panelBg);
    exciterBox.setColour (juce::ComboBox::outlineColourId, Colours::panelBorder);
    exciterBox.setColour (juce::ComboBox::textColourId, Colours::text);
    exciterBox.onChange = [this]
    {
        static const ExciterType types[] = {
            ExciterType::Cotton, ExciterType::Felt,
            ExciterType::Wood, ExciterType::Metal };
        int idx = exciterBox.getSelectedId() - 1;
        if (idx >= 0 && idx < 4)
            processorRef.getCimbalomParams().exciter = types[idx];
        processorRef.updateVoiceParams();
    };
    addAndMakeVisible (exciterBox);

    initLabel (stringsLabel, "STRINGS", this);
    initLinear (stringsSlider, 1, 5, 1, 3, this);
    stringsSlider.onValueChange = [this]
    {
        processorRef.getCimbalomParams().stringsPerCourse =
            static_cast<int> (stringsSlider.getValue());
        processorRef.updateVoiceParams();
    };

    initLabel (detuneLabel, "DETUNE", this);
    initLinear (detuneSlider, 0.0, 15.0, 0.5, 3.0, this);
    detuneSlider.onValueChange = [this]
    {
        processorRef.getCimbalomParams().detuneAmount = detuneSlider.getValue();
        processorRef.updateVoiceParams();
    };

    initLabel (soundboardLabel, "BOARD", this);
    initLinear (soundboardSlider, 0.0, 1.0, 0.01, 0.3, this);
    soundboardSlider.onValueChange = [this]
    {
        processorRef.getCimbalomParams().soundboardAmount = soundboardSlider.getValue();
        processorRef.updateVoiceParams();
    };

    // --- Chromatic controls ---
    initLabel (subEngineLabel, "TYPE", this);
    subEngineBox.addItem ("Tongue Drum", 1);
    subEngineBox.addItem ("Water Gong", 2);
    subEngineBox.addItem ("Custom Harmonics", 3);
    subEngineBox.setSelectedId (1, juce::dontSendNotification);
    subEngineBox.setColour (juce::ComboBox::backgroundColourId, Colours::panelBg);
    subEngineBox.setColour (juce::ComboBox::outlineColourId, Colours::panelBorder);
    subEngineBox.setColour (juce::ComboBox::textColourId, Colours::text);
    subEngineBox.onChange = [this]
    {
        static const ChromaticSubEngine subs[] = {
            ChromaticSubEngine::TongueDrum,
            ChromaticSubEngine::WaterGong,
            ChromaticSubEngine::CustomHarmonics };
        int idx = subEngineBox.getSelectedId() - 1;
        if (idx >= 0 && idx < 3)
            processorRef.getChromaticParams().subEngine = subs[idx];
        processorRef.updateVoiceParams();
        showEngineControls();
    };
    addAndMakeVisible (subEngineBox);

    initLabel (waterLabel, "WATER", this);
    initLinear (waterSlider, 0.0, 1.0, 0.01, 0.0, this);
    waterSlider.onValueChange = [this]
    {
        processorRef.getChromaticParams().waterLevel = waterSlider.getValue();
        processorRef.updateVoiceParams();
    };

    // --- FM Piano controls ---
    initLabel (fmPresetLabel, "PRESET", this);
    fmPresetBox.addItem ("Piano", 1);
    fmPresetBox.addItem ("Electric Piano", 2);
    fmPresetBox.addItem ("Vibraphone", 3);
    fmPresetBox.addItem ("Bell", 4);
    fmPresetBox.addItem ("Organ", 5);
    fmPresetBox.addItem ("Bass", 6);
    fmPresetBox.addItem ("Strings", 7);
    fmPresetBox.addItem ("Brass", 8);
    fmPresetBox.setSelectedId (1, juce::dontSendNotification);
    fmPresetBox.setColour (juce::ComboBox::backgroundColourId, Colours::panelBg);
    fmPresetBox.setColour (juce::ComboBox::outlineColourId, Colours::panelBorder);
    fmPresetBox.setColour (juce::ComboBox::textColourId, Colours::text);
    fmPresetBox.onChange = [this]
    {
        static const FMPreset presets[] = {
            FMPreset::Piano, FMPreset::ElectricPiano,
            FMPreset::Vibraphone, FMPreset::Bell,
            FMPreset::Organ, FMPreset::Bass,
            FMPreset::Strings, FMPreset::Brass };
        int idx = fmPresetBox.getSelectedId() - 1;
        if (idx >= 0 && idx < 8)
            processorRef.getFMParams().preset = presets[idx];
        processorRef.updateVoiceParams();
    };
    addAndMakeVisible (fmPresetBox);

    initLabel (fmDetuneLabel, "DETUNE", this);
    initLinear (fmDetuneSlider, -5.0, 5.0, 0.1, 0.0, this);
    fmDetuneSlider.onValueChange = [this]
    {
        processorRef.getFMParams().detune = fmDetuneSlider.getValue();
        processorRef.updateVoiceParams();
    };

    initLabel (fmVolumeLabel, "VOLUME", this);
    initLinear (fmVolumeSlider, 0.0, 1.0, 0.01, 0.8, this);
    fmVolumeSlider.onValueChange = [this]
    {
        processorRef.getFMParams().masterVolume = fmVolumeSlider.getValue();
        processorRef.updateVoiceParams();
    };

    // --- Effects section (rotary knobs) ---
    initLabel (reverbLabel, "REVERB", this);
    initRotary (reverbSlider, 0.0, 1.0, 0.01, 0.25, this);
    reverbSlider.onValueChange = [this]
    {
        processorRef.getEffectsParams().reverbWet = static_cast<float> (reverbSlider.getValue());
        processorRef.getEffectsParams().reverbEnabled = reverbSlider.getValue() > 0.001;
        processorRef.getEffectsChain().setParameters (processorRef.getEffectsParams());
    };

    initLabel (delayLabel, "DELAY", this);
    initRotary (delaySlider, 0.0, 1.0, 0.01, 0.0, this);
    delaySlider.onValueChange = [this]
    {
        float wet = static_cast<float> (delaySlider.getValue());
        processorRef.getEffectsParams().delayWet = wet;
        processorRef.getEffectsParams().delayEnabled = wet > 0.001;
        processorRef.getEffectsChain().setParameters (processorRef.getEffectsParams());
    };

    initLabel (compLabel, "COMP", this);
    initRotary (compSlider, 0.0, 1.0, 0.01, 0.0, this);
    compSlider.onValueChange = [this]
    {
        float v = static_cast<float> (compSlider.getValue());
        processorRef.getEffectsParams().compressorEnabled = v > 0.001f;
        processorRef.getEffectsParams().compThreshold = -6.0f - v * 18.0f;
        processorRef.getEffectsParams().compRatio = 1.0f + v * 7.0f;
        processorRef.getEffectsParams().compMakeup = v * 6.0f;
        processorRef.getEffectsChain().setParameters (processorRef.getEffectsParams());
    };

    initLabel (masterLabel, "MASTER", this);
    initRotary (masterSlider, 0.0, 2.0, 0.01, 1.0, this);
    masterSlider.onValueChange = [this]
    {
        processorRef.getEffectsParams().masterVolume = static_cast<float> (masterSlider.getValue());
        processorRef.getEffectsChain().setParameters (processorRef.getEffectsParams());
    };

    // --- Distortion section ---
    initLabel (distTypeLabel, "TYPE", this);
    distTypeBox.addItem ("Overdrive", 1);
    distTypeBox.addItem ("Bitcrush", 2);
    distTypeBox.addItem ("Wavefold", 3);
    distTypeBox.setSelectedId (1, juce::dontSendNotification);
    distTypeBox.setColour (juce::ComboBox::backgroundColourId, Colours::panelBg);
    distTypeBox.setColour (juce::ComboBox::outlineColourId, Colours::panelBorder);
    distTypeBox.setColour (juce::ComboBox::textColourId, Colours::text);
    distTypeBox.onChange = [this]
    {
        static const DistortionType types[] = {
            DistortionType::Overdrive,
            DistortionType::Bitcrush,
            DistortionType::Wavefold };
        int idx = distTypeBox.getSelectedId() - 1;
        if (idx >= 0 && idx < 3)
        {
            processorRef.getEffectsParams().distortionType = types[idx];
            processorRef.getEffectsChain().setParameters (processorRef.getEffectsParams());
        }
    };
    addAndMakeVisible (distTypeBox);

    initLabel (distDriveLabel, "DRIVE", this);
    initRotary (distDriveSlider, 0.0, 1.0, 0.01, 0.0, this);
    distDriveSlider.onValueChange = [this]
    {
        float v = static_cast<float> (distDriveSlider.getValue());
        processorRef.getEffectsParams().distortionDrive = v;
        processorRef.getEffectsParams().distortionEnabled = v > 0.001f;
        processorRef.getEffectsChain().setParameters (processorRef.getEffectsParams());
    };

    initLabel (distInstLabel, "UNSTABLE", this);
    initRotary (distInstSlider, 0.0, 1.0, 0.01, 0.0, this);
    distInstSlider.onValueChange = [this]
    {
        processorRef.getEffectsParams().distortionInstability =
            static_cast<float> (distInstSlider.getValue());
        processorRef.getEffectsChain().setParameters (processorRef.getEffectsParams());
    };

    initLabel (distWetLabel, "MIX", this);
    initRotary (distWetSlider, 0.0, 1.0, 0.01, 0.5, this);
    distWetSlider.onValueChange = [this]
    {
        processorRef.getEffectsParams().distortionWet =
            static_cast<float> (distWetSlider.getValue());
        processorRef.getEffectsChain().setParameters (processorRef.getEffectsParams());
    };

    showEngineControls();
    syncFromProcessor();
    setSize (820, 620);
    startTimerHz (10);
}

TsukiSynthEditor::~TsukiSynthEditor()
{
    stopTimer();
    keyboardState.removeListener (this);
}

void TsukiSynthEditor::timerCallback()
{
    int engId = 0;
    switch (processorRef.getEngineType())
    {
        case EngineType::Cimbalom: engId = 1; break;
        case EngineType::Chromatic: engId = 2; break;
        case EngineType::FMPiano: engId = 3; break;
    }
    if (engineBox.getSelectedId() != engId)
        syncFromProcessor();
}

void TsukiSynthEditor::syncFromProcessor()
{
    int engId = 1;
    switch (processorRef.getEngineType())
    {
        case EngineType::Cimbalom: engId = 1; break;
        case EngineType::Chromatic: engId = 2; break;
        case EngineType::FMPiano: engId = 3; break;
    }
    engineBox.setSelectedId (engId, juce::dontSendNotification);

    auto& cim = processorRef.getCimbalomParams();
    strikeSlider.setValue (cim.strikePosition, juce::dontSendNotification);
    exciterBox.setSelectedId (static_cast<int> (cim.exciter) + 1, juce::dontSendNotification);
    stringsSlider.setValue (cim.stringsPerCourse, juce::dontSendNotification);
    detuneSlider.setValue (cim.detuneAmount, juce::dontSendNotification);
    soundboardSlider.setValue (cim.soundboardAmount, juce::dontSendNotification);

    auto& chr = processorRef.getChromaticParams();
    subEngineBox.setSelectedId (static_cast<int> (chr.subEngine) + 1, juce::dontSendNotification);
    waterSlider.setValue (chr.waterLevel, juce::dontSendNotification);

    auto& fm = processorRef.getFMParams();
    fmPresetBox.setSelectedId (static_cast<int> (fm.preset) + 1, juce::dontSendNotification);
    fmDetuneSlider.setValue (fm.detune, juce::dontSendNotification);
    fmVolumeSlider.setValue (fm.masterVolume, juce::dontSendNotification);

    auto& fx = processorRef.getEffectsParams();
    reverbSlider.setValue (fx.reverbWet, juce::dontSendNotification);
    delaySlider.setValue (fx.delayWet, juce::dontSendNotification);
    masterSlider.setValue (fx.masterVolume, juce::dontSendNotification);
    distDriveSlider.setValue (fx.distortionDrive, juce::dontSendNotification);
    distInstSlider.setValue (fx.distortionInstability, juce::dontSendNotification);
    distWetSlider.setValue (fx.distortionWet, juce::dontSendNotification);

    int distId = 1;
    switch (fx.distortionType)
    {
        case DistortionType::Overdrive: distId = 1; break;
        case DistortionType::Bitcrush:  distId = 2; break;
        case DistortionType::Wavefold:  distId = 3; break;
    }
    distTypeBox.setSelectedId (distId, juce::dontSendNotification);

    populateMaterialBox();
    showEngineControls();
    resized();
}

void TsukiSynthEditor::showEngineControls()
{
    auto eng = processorRef.getEngineType();
    bool isCim = eng == EngineType::Cimbalom;
    bool isChr = eng == EngineType::Chromatic;
    bool isFM  = eng == EngineType::FMPiano;
    bool isWaterGong = processorRef.getChromaticParams().subEngine
                    == ChromaticSubEngine::WaterGong;

    materialLabel.setVisible (! isFM);
    materialBox.setVisible (! isFM);
    strikeLabel.setVisible (! isFM);
    strikeSlider.setVisible (! isFM);

    exciterLabel.setVisible (isCim);
    exciterBox.setVisible (isCim);
    stringsLabel.setVisible (isCim);
    stringsSlider.setVisible (isCim);
    detuneLabel.setVisible (isCim);
    detuneSlider.setVisible (isCim);
    soundboardLabel.setVisible (isCim);
    soundboardSlider.setVisible (isCim);

    subEngineLabel.setVisible (isChr);
    subEngineBox.setVisible (isChr);
    waterLabel.setVisible (isChr && isWaterGong);
    waterSlider.setVisible (isChr && isWaterGong);

    fmPresetLabel.setVisible (isFM);
    fmPresetBox.setVisible (isFM);
    fmDetuneLabel.setVisible (isFM);
    fmDetuneSlider.setVisible (isFM);
    fmVolumeLabel.setVisible (isFM);
    fmVolumeSlider.setVisible (isFM);
}

void TsukiSynthEditor::paintSectionPanel (juce::Graphics& g,
                                            juce::Rectangle<int> bounds,
                                            const juce::String& title)
{
    g.setColour (Colours::panelBg);
    g.fillRoundedRectangle (bounds.toFloat(), 6.0f);
    g.setColour (Colours::panelBorder);
    g.drawRoundedRectangle (bounds.toFloat().reduced (0.5f), 6.0f, 1.0f);

    if (title.isNotEmpty())
    {
        g.setColour (Colours::accentDim);
        g.setFont (juce::FontOptions (10.0f));
        g.drawText (title, bounds.getX() + 10, bounds.getY() + 4, 120, 14,
                    juce::Justification::centredLeft);
    }
}

void TsukiSynthEditor::paint (juce::Graphics& g)
{
    g.fillAll (Colours::bg);

    // Header
    auto headerArea = getLocalBounds().removeFromTop (50);
    g.setColour (Colours::accent);
    g.setFont (juce::FontOptions (20.0f));
    g.drawText (juce::CharPointer_UTF8 ("\xe6\x9c\x88\xe5\x85\x89\xe5\x90\x88\xe6\x88\x90\xe5\x99\xa8"),
                headerArea.removeFromLeft (140).withTrimmedLeft (16),
                juce::Justification::centredLeft);
    g.setColour (Colours::text);
    g.setFont (juce::FontOptions (18.0f));
    g.drawText ("TsukiSynth", headerArea.removeFromLeft (130),
                juce::Justification::centredLeft);

    g.setColour (Colours::textDim);
    g.setFont (juce::FontOptions (10.0f));
    g.drawText ("Physical Modeling Multi-Engine",
                headerArea, juce::Justification::centredLeft);

    // Section panels
    paintSectionPanel (g, enginePanelBounds, "ENGINE");
    paintSectionPanel (g, effectsPanelBounds, "EFFECTS");
    paintSectionPanel (g, distortionPanelBounds, "DISTORTION");
}

void TsukiSynthEditor::resized()
{
    auto area = getLocalBounds();

    // Keyboard at bottom
    keyboardComponent.setBounds (area.removeFromBottom (90).reduced (8, 4));

    // Header
    area.removeFromTop (54);

    auto content = area.reduced (10, 0);

    // Engine panel (top section)
    enginePanelBounds = content.removeFromTop (150);
    {
        auto inner = enginePanelBounds.reduced (12, 20);
        inner.removeFromTop (2);

        const int rH = 26, labelW = 70, gap = 4;

        // Row 0: Engine selector + Material
        auto row = inner.removeFromTop (rH);
        engineLabel.setBounds (row.removeFromLeft (labelW));
        engineBox.setBounds (row.removeFromLeft (130));
        row.removeFromLeft (16);
        if (materialBox.isVisible())
        {
            materialLabel.setBounds (row.removeFromLeft (65));
            materialBox.setBounds (row.removeFromLeft (180));
        }

        inner.removeFromTop (gap);
        auto eng = processorRef.getEngineType();

        if (eng == EngineType::FMPiano)
        {
            row = inner.removeFromTop (rH);
            fmPresetLabel.setBounds (row.removeFromLeft (labelW));
            fmPresetBox.setBounds (row.removeFromLeft (160));
            row.removeFromLeft (16);
            fmDetuneLabel.setBounds (row.removeFromLeft (55));
            fmDetuneSlider.setBounds (row.removeFromLeft (180));

            inner.removeFromTop (gap);
            row = inner.removeFromTop (rH);
            fmVolumeLabel.setBounds (row.removeFromLeft (labelW));
            fmVolumeSlider.setBounds (row.removeFromLeft (200));
        }
        else
        {
            row = inner.removeFromTop (rH);
            strikeLabel.setBounds (row.removeFromLeft (labelW));
            strikeSlider.setBounds (row.removeFromLeft (180));
            row.removeFromLeft (16);

            if (eng == EngineType::Cimbalom)
            {
                exciterLabel.setBounds (row.removeFromLeft (55));
                exciterBox.setBounds (row.removeFromLeft (100));
            }
            else
            {
                subEngineLabel.setBounds (row.removeFromLeft (40));
                subEngineBox.setBounds (row.removeFromLeft (150));
            }

            inner.removeFromTop (gap);
            row = inner.removeFromTop (rH);
            if (eng == EngineType::Cimbalom)
            {
                stringsLabel.setBounds (row.removeFromLeft (labelW));
                stringsSlider.setBounds (row.removeFromLeft (130));
                row.removeFromLeft (16);
                detuneLabel.setBounds (row.removeFromLeft (55));
                detuneSlider.setBounds (row.removeFromLeft (160));
            }
            else
            {
                waterLabel.setBounds (row.removeFromLeft (labelW));
                waterSlider.setBounds (row.removeFromLeft (200));
            }

            inner.removeFromTop (gap);
            row = inner.removeFromTop (rH);
            if (eng == EngineType::Cimbalom)
            {
                soundboardLabel.setBounds (row.removeFromLeft (labelW));
                soundboardSlider.setBounds (row.removeFromLeft (200));
            }
        }
    }

    content.removeFromTop (8);

    // Bottom area: Effects left, Distortion right
    auto bottomPanels = content.removeFromTop (180);

    // Effects panel (left)
    effectsPanelBounds = bottomPanels.removeFromLeft (bottomPanels.getWidth() * 3 / 5 - 4);
    {
        auto inner = effectsPanelBounds.reduced (10, 22);
        const int knobW = 70, knobH = 80;
        auto knobRow = inner.removeFromTop (knobH);

        auto slot = knobRow.removeFromLeft (knobW);
        reverbLabel.setBounds (slot.removeFromTop (14));
        reverbSlider.setBounds (slot);

        knobRow.removeFromLeft (8);
        slot = knobRow.removeFromLeft (knobW);
        delayLabel.setBounds (slot.removeFromTop (14));
        delaySlider.setBounds (slot);

        knobRow.removeFromLeft (8);
        slot = knobRow.removeFromLeft (knobW);
        compLabel.setBounds (slot.removeFromTop (14));
        compSlider.setBounds (slot);

        knobRow.removeFromLeft (8);
        slot = knobRow.removeFromLeft (knobW);
        masterLabel.setBounds (slot.removeFromTop (14));
        masterSlider.setBounds (slot);
    }

    bottomPanels.removeFromLeft (8);

    // Distortion panel (right)
    distortionPanelBounds = bottomPanels;
    {
        auto inner = distortionPanelBounds.reduced (10, 22);

        // Type selector row
        auto typeRow = inner.removeFromTop (24);
        distTypeLabel.setBounds (typeRow.removeFromLeft (34));
        distTypeBox.setBounds (typeRow.removeFromLeft (110));

        inner.removeFromTop (8);

        const int knobW = 64, knobH = 80;
        auto knobRow = inner.removeFromTop (knobH);

        auto slot = knobRow.removeFromLeft (knobW);
        distDriveLabel.setBounds (slot.removeFromTop (14));
        distDriveSlider.setBounds (slot);

        knobRow.removeFromLeft (6);
        slot = knobRow.removeFromLeft (knobW);
        distInstLabel.setBounds (slot.removeFromTop (14));
        distInstSlider.setBounds (slot);

        knobRow.removeFromLeft (6);
        slot = knobRow.removeFromLeft (knobW);
        distWetLabel.setBounds (slot.removeFromTop (14));
        distWetSlider.setBounds (slot);
    }
}

void TsukiSynthEditor::populateMaterialBox()
{
    materialBox.clear();
    auto keys = processorRef.getMaterialDB().getMaterialKeys();
    int id = 1, sel = 1;
    auto& activeKey = processorRef.getEngineType() == EngineType::Cimbalom
                    ? processorRef.getCimbalomParams().materialKey
                    : processorRef.getChromaticParams().materialKey;
    for (const auto& key : keys)
    {
        juce::String name (key);
        if (const auto* mat = processorRef.getMaterialDB().getMaterial (key))
            name = juce::String (mat->displayName);
        materialBox.addItem (name, id);
        if (key == activeKey) sel = id;
        ++id;
    }
    materialBox.setSelectedId (sel, juce::dontSendNotification);
}

void TsukiSynthEditor::handleNoteOn (juce::MidiKeyboardState*, int ch, int note, float vel)
{
    processorRef.addMidiMessage (juce::MidiMessage::noteOn (ch, note, vel));
}

void TsukiSynthEditor::handleNoteOff (juce::MidiKeyboardState*, int ch, int note, float vel)
{
    processorRef.addMidiMessage (juce::MidiMessage::noteOff (ch, note, vel));
}
