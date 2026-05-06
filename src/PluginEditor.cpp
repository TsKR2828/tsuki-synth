#include "PluginEditor.h"

static juce::Label& setupLabel (juce::Label& label, const juce::String& text,
                                 juce::Component* parent)
{
    label.setText (text, juce::dontSendNotification);
    label.setColour (juce::Label::textColourId, juce::Colour (0xffaaaaaa));
    label.setFont (juce::FontOptions (12.0f));
    parent->addAndMakeVisible (label);
    return label;
}

static juce::Slider& setupSlider (juce::Slider& slider, double min, double max,
                                   double step, double val, juce::Component* parent)
{
    slider.setRange (min, max, step);
    slider.setValue (val, juce::dontSendNotification);
    slider.setTextBoxStyle (juce::Slider::TextBoxRight, false, 48, 20);
    slider.setColour (juce::Slider::thumbColourId, juce::Colour (0xffe0d6c8));
    slider.setColour (juce::Slider::trackColourId, juce::Colour (0xff444466));
    parent->addAndMakeVisible (slider);
    return slider;
}

TsukiSynthEditor::TsukiSynthEditor (TsukiSynthProcessor& p)
    : AudioProcessorEditor (&p),
      processorRef (p),
      keyboardComponent (keyboardState, juce::MidiKeyboardComponent::horizontalKeyboard)
{
    keyboardState.addListener (this);
    addAndMakeVisible (keyboardComponent);

    // Material
    setupLabel (materialLabel, "Material", this);
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

    // Exciter
    setupLabel (exciterLabel, "Exciter", this);
    exciterBox.addItem ("Cotton", 1);
    exciterBox.addItem ("Felt", 2);
    exciterBox.addItem ("Wood", 3);
    exciterBox.addItem ("Metal", 4);
    exciterBox.setSelectedId (3, juce::dontSendNotification);
    exciterBox.onChange = [this]
    {
        auto& params = processorRef.getCimbalomParams();
        switch (exciterBox.getSelectedId())
        {
            case 1: params.exciter = ExciterType::Cotton; break;
            case 2: params.exciter = ExciterType::Felt;   break;
            case 3: params.exciter = ExciterType::Wood;   break;
            case 4: params.exciter = ExciterType::Metal;  break;
        }
        processorRef.updateVoiceParams();
    };
    addAndMakeVisible (exciterBox);

    // Strike position
    setupLabel (strikeLabel, "Strike Pos", this);
    setupSlider (strikeSlider, 0.05, 0.95, 0.01, 0.3, this);
    strikeSlider.onValueChange = [this]
    {
        processorRef.getCimbalomParams().strikePosition = strikeSlider.getValue();
        processorRef.updateVoiceParams();
    };

    // Strings per course
    setupLabel (stringsLabel, "Strings", this);
    setupSlider (stringsSlider, 1, 5, 1, 3, this);
    stringsSlider.onValueChange = [this]
    {
        processorRef.getCimbalomParams().stringsPerCourse =
            static_cast<int> (stringsSlider.getValue());
        processorRef.updateVoiceParams();
    };

    // Detune
    setupLabel (detuneLabel, "Detune (ct)", this);
    setupSlider (detuneSlider, 0.0, 15.0, 0.5, 3.0, this);
    detuneSlider.onValueChange = [this]
    {
        processorRef.getCimbalomParams().detuneAmount = detuneSlider.getValue();
        processorRef.updateVoiceParams();
    };

    // Soundboard coupling
    setupLabel (soundboardLabel, "Soundboard", this);
    setupSlider (soundboardSlider, 0.0, 1.0, 0.01, 0.3, this);
    soundboardSlider.onValueChange = [this]
    {
        processorRef.getCimbalomParams().soundboardAmount = soundboardSlider.getValue();
        processorRef.updateVoiceParams();
    };

    setSize (760, 480);
}

TsukiSynthEditor::~TsukiSynthEditor()
{
    keyboardState.removeListener (this);
}

void TsukiSynthEditor::paint (juce::Graphics& g)
{
    g.fillAll (juce::Colour (0xff1a1a2e));

    // Title
    g.setColour (juce::Colour (0xffe0d6c8));
    g.setFont (juce::FontOptions (22.0f));
    g.drawText ("TsukiSynth - Cimbalom",
                getLocalBounds().removeFromTop (42),
                juce::Justification::centred);

    // Subtitle
    g.setFont (juce::FontOptions (11.0f));
    g.setColour (juce::Colour (0xff666666));
    g.drawText ("Physical Modeling String Synthesis",
                getLocalBounds().removeFromTop (58),
                juce::Justification::centred);

    // Separator line
    g.setColour (juce::Colour (0xff333355));
    g.drawHorizontalLine (62, 20.0f, static_cast<float> (getWidth() - 20));
}

void TsukiSynthEditor::resized()
{
    auto area = getLocalBounds();
    auto keyboard = area.removeFromBottom (120).reduced (10, 0);
    keyboardComponent.setBounds (keyboard);

    area.removeFromTop (68);
    auto controls = area.reduced (20, 0);

    const int rowH = 30;
    const int labelW = 90;
    const int gap = 6;

    // Row 1: Material + Exciter
    auto row = controls.removeFromTop (rowH);
    materialLabel.setBounds (row.removeFromLeft (labelW));
    materialBox.setBounds (row.removeFromLeft (180));
    row.removeFromLeft (20);
    exciterLabel.setBounds (row.removeFromLeft (60));
    exciterBox.setBounds (row.removeFromLeft (120));

    controls.removeFromTop (gap);

    // Row 2: Strike + Strings
    row = controls.removeFromTop (rowH);
    strikeLabel.setBounds (row.removeFromLeft (labelW));
    strikeSlider.setBounds (row.removeFromLeft (200));
    row.removeFromLeft (20);
    stringsLabel.setBounds (row.removeFromLeft (60));
    stringsSlider.setBounds (row.removeFromLeft (140));

    controls.removeFromTop (gap);

    // Row 3: Detune + Soundboard
    row = controls.removeFromTop (rowH);
    detuneLabel.setBounds (row.removeFromLeft (labelW));
    detuneSlider.setBounds (row.removeFromLeft (200));
    row.removeFromLeft (20);
    soundboardLabel.setBounds (row.removeFromLeft (80));
    soundboardSlider.setBounds (row.removeFromLeft (140));
}

void TsukiSynthEditor::populateMaterialBox()
{
    materialBox.clear();
    auto keys = processorRef.getMaterialDB().getMaterialKeys();

    int id = 1;
    int selectedId = 1;
    for (const auto& key : keys)
    {
        juce::String name (key);
        if (const auto* mat = processorRef.getMaterialDB().getMaterial (key))
            name = juce::String (mat->displayName);
        materialBox.addItem (name, id);
        if (key == processorRef.getCimbalomParams().materialKey)
            selectedId = id;
        ++id;
    }
    materialBox.setSelectedId (selectedId, juce::dontSendNotification);
}

void TsukiSynthEditor::handleNoteOn (juce::MidiKeyboardState*, int midiChannel,
                                      int midiNoteNumber, float velocity)
{
    processorRef.addMidiMessage (
        juce::MidiMessage::noteOn (midiChannel, midiNoteNumber, velocity));
}

void TsukiSynthEditor::handleNoteOff (juce::MidiKeyboardState*, int midiChannel,
                                       int midiNoteNumber, float velocity)
{
    processorRef.addMidiMessage (
        juce::MidiMessage::noteOff (midiChannel, midiNoteNumber, velocity));
}
