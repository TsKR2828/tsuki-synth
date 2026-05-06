#include "PluginEditor.h"

static void initLabel (juce::Label& l, const juce::String& t, juce::Component* p)
{
    l.setText (t, juce::dontSendNotification);
    l.setColour (juce::Label::textColourId, juce::Colour (0xffaaaaaa));
    l.setFont (juce::FontOptions (12.0f));
    p->addAndMakeVisible (l);
}

static void initSlider (juce::Slider& s, double lo, double hi, double step,
                         double val, juce::Component* p)
{
    s.setRange (lo, hi, step);
    s.setValue (val, juce::dontSendNotification);
    s.setTextBoxStyle (juce::Slider::TextBoxRight, false, 48, 20);
    s.setColour (juce::Slider::thumbColourId, juce::Colour (0xffe0d6c8));
    s.setColour (juce::Slider::trackColourId, juce::Colour (0xff444466));
    p->addAndMakeVisible (s);
}

TsukiSynthEditor::TsukiSynthEditor (TsukiSynthProcessor& p)
    : AudioProcessorEditor (&p),
      processorRef (p),
      keyboardComponent (keyboardState, juce::MidiKeyboardComponent::horizontalKeyboard)
{
    keyboardState.addListener (this);
    addAndMakeVisible (keyboardComponent);

    // Engine selector
    initLabel (engineLabel, "Engine", this);
    engineBox.addItem ("Cimbalom", 1);
    engineBox.addItem ("Chromatic", 2);
    engineBox.setSelectedId (1, juce::dontSendNotification);
    engineBox.onChange = [this]
    {
        processorRef.setEngineType (
            engineBox.getSelectedId() == 1 ? EngineType::Cimbalom
                                           : EngineType::Chromatic);
        showEngineControls();
    };
    addAndMakeVisible (engineBox);

    // Material
    initLabel (materialLabel, "Material", this);
    populateMaterialBox();
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
    initLabel (strikeLabel, "Strike Pos", this);
    initSlider (strikeSlider, 0.05, 0.95, 0.01, 0.3, this);
    strikeSlider.onValueChange = [this]
    {
        processorRef.getCimbalomParams().strikePosition = strikeSlider.getValue();
        processorRef.getChromaticParams().strikePosition = strikeSlider.getValue();
        processorRef.updateVoiceParams();
    };

    // --- Cimbalom controls ---
    initLabel (exciterLabel, "Exciter", this);
    exciterBox.addItem ("Cotton", 1);
    exciterBox.addItem ("Felt", 2);
    exciterBox.addItem ("Wood", 3);
    exciterBox.addItem ("Metal", 4);
    exciterBox.setSelectedId (3, juce::dontSendNotification);
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

    initLabel (stringsLabel, "Strings", this);
    initSlider (stringsSlider, 1, 5, 1, 3, this);
    stringsSlider.onValueChange = [this]
    {
        processorRef.getCimbalomParams().stringsPerCourse =
            static_cast<int> (stringsSlider.getValue());
        processorRef.updateVoiceParams();
    };

    initLabel (detuneLabel, "Detune", this);
    initSlider (detuneSlider, 0.0, 15.0, 0.5, 3.0, this);
    detuneSlider.onValueChange = [this]
    {
        processorRef.getCimbalomParams().detuneAmount = detuneSlider.getValue();
        processorRef.updateVoiceParams();
    };

    initLabel (soundboardLabel, "Soundboard", this);
    initSlider (soundboardSlider, 0.0, 1.0, 0.01, 0.3, this);
    soundboardSlider.onValueChange = [this]
    {
        processorRef.getCimbalomParams().soundboardAmount = soundboardSlider.getValue();
        processorRef.updateVoiceParams();
    };

    // --- Chromatic controls ---
    initLabel (subEngineLabel, "Type", this);
    subEngineBox.addItem ("Tongue Drum", 1);
    subEngineBox.addItem ("Water Gong", 2);
    subEngineBox.addItem ("Custom Harmonics", 3);
    subEngineBox.setSelectedId (1, juce::dontSendNotification);
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

    initLabel (waterLabel, "Water Level", this);
    initSlider (waterSlider, 0.0, 1.0, 0.01, 0.0, this);
    waterSlider.onValueChange = [this]
    {
        processorRef.getChromaticParams().waterLevel = waterSlider.getValue();
        processorRef.updateVoiceParams();
    };

    showEngineControls();
    setSize (760, 500);
}

TsukiSynthEditor::~TsukiSynthEditor()
{
    keyboardState.removeListener (this);
}

void TsukiSynthEditor::showEngineControls()
{
    bool isCim = processorRef.getEngineType() == EngineType::Cimbalom;
    bool isWaterGong = processorRef.getChromaticParams().subEngine
                    == ChromaticSubEngine::WaterGong;

    exciterLabel.setVisible (isCim);
    exciterBox.setVisible (isCim);
    stringsLabel.setVisible (isCim);
    stringsSlider.setVisible (isCim);
    detuneLabel.setVisible (isCim);
    detuneSlider.setVisible (isCim);
    soundboardLabel.setVisible (isCim);
    soundboardSlider.setVisible (isCim);

    subEngineLabel.setVisible (! isCim);
    subEngineBox.setVisible (! isCim);
    waterLabel.setVisible (! isCim && isWaterGong);
    waterSlider.setVisible (! isCim && isWaterGong);
}

void TsukiSynthEditor::paint (juce::Graphics& g)
{
    g.fillAll (juce::Colour (0xff1a1a2e));

    g.setColour (juce::Colour (0xffe0d6c8));
    g.setFont (juce::FontOptions (22.0f));
    g.drawText ("TsukiSynth",
                getLocalBounds().removeFromTop (40),
                juce::Justification::centred);

    g.setFont (juce::FontOptions (11.0f));
    g.setColour (juce::Colour (0xff666666));
    g.drawText ("Physical Modeling Multi-Engine Synthesizer",
                getLocalBounds().removeFromTop (55),
                juce::Justification::centred);

    g.setColour (juce::Colour (0xff333355));
    g.drawHorizontalLine (58, 20.0f, static_cast<float> (getWidth() - 20));
}

void TsukiSynthEditor::resized()
{
    auto area = getLocalBounds();
    keyboardComponent.setBounds (area.removeFromBottom (120).reduced (10, 0));

    area.removeFromTop (64);
    auto ctrl = area.reduced (20, 0);

    const int rH = 28, labelW = 80, gap = 5;

    // Row 0: Engine + Material
    auto row = ctrl.removeFromTop (rH);
    engineLabel.setBounds (row.removeFromLeft (labelW));
    engineBox.setBounds (row.removeFromLeft (140));
    row.removeFromLeft (20);
    materialLabel.setBounds (row.removeFromLeft (65));
    materialBox.setBounds (row.removeFromLeft (180));

    ctrl.removeFromTop (gap);

    // Row 1: Strike + engine-specific
    row = ctrl.removeFromTop (rH);
    strikeLabel.setBounds (row.removeFromLeft (labelW));
    strikeSlider.setBounds (row.removeFromLeft (190));
    row.removeFromLeft (20);

    if (processorRef.getEngineType() == EngineType::Cimbalom)
    {
        exciterLabel.setBounds (row.removeFromLeft (55));
        exciterBox.setBounds (row.removeFromLeft (100));
    }
    else
    {
        subEngineLabel.setBounds (row.removeFromLeft (40));
        subEngineBox.setBounds (row.removeFromLeft (150));
    }

    ctrl.removeFromTop (gap);

    // Row 2
    row = ctrl.removeFromTop (rH);
    if (processorRef.getEngineType() == EngineType::Cimbalom)
    {
        stringsLabel.setBounds (row.removeFromLeft (labelW));
        stringsSlider.setBounds (row.removeFromLeft (140));
        row.removeFromLeft (20);
        detuneLabel.setBounds (row.removeFromLeft (55));
        detuneSlider.setBounds (row.removeFromLeft (160));
    }
    else
    {
        waterLabel.setBounds (row.removeFromLeft (labelW));
        waterSlider.setBounds (row.removeFromLeft (200));
    }

    ctrl.removeFromTop (gap);

    // Row 3 (Cimbalom only)
    row = ctrl.removeFromTop (rH);
    if (processorRef.getEngineType() == EngineType::Cimbalom)
    {
        soundboardLabel.setBounds (row.removeFromLeft (labelW));
        soundboardSlider.setBounds (row.removeFromLeft (200));
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
