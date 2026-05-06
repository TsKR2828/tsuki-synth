#include "PluginEditor.h"

TsukiSynthEditor::TsukiSynthEditor (TsukiSynthProcessor& p)
    : AudioProcessorEditor (&p),
      processorRef (p),
      keyboardComponent (keyboardState, juce::MidiKeyboardComponent::horizontalKeyboard)
{
    keyboardState.addListener (this);
    addAndMakeVisible (keyboardComponent);

    materialLabel.setText ("Material", juce::dontSendNotification);
    materialLabel.setColour (juce::Label::textColourId, juce::Colour (0xffaaaaaa));
    addAndMakeVisible (materialLabel);

    populateMaterialBox();
    materialBox.setSelectedId (1, juce::dontSendNotification);
    materialBox.onChange = [this]
    {
        int idx = materialBox.getSelectedId() - 1;
        auto keys = processorRef.getMaterialDB().getMaterialKeys();
        if (idx >= 0 && idx < static_cast<int> (keys.size()))
            processorRef.setMaterial (keys[static_cast<size_t> (idx)]);
    };
    addAndMakeVisible (materialBox);

    strikeLabel.setText ("Strike Position", juce::dontSendNotification);
    strikeLabel.setColour (juce::Label::textColourId, juce::Colour (0xffaaaaaa));
    addAndMakeVisible (strikeLabel);

    strikeSlider.setRange (0.05, 0.95, 0.01);
    strikeSlider.setValue (0.3, juce::dontSendNotification);
    strikeSlider.setTextBoxStyle (juce::Slider::TextBoxRight, false, 50, 20);
    strikeSlider.setColour (juce::Slider::thumbColourId, juce::Colour (0xffe0d6c8));
    strikeSlider.onValueChange = [this]
    {
        processorRef.setStrikePosition (strikeSlider.getValue());
    };
    addAndMakeVisible (strikeSlider);

    setSize (720, 340);
}

TsukiSynthEditor::~TsukiSynthEditor()
{
    keyboardState.removeListener (this);
}

void TsukiSynthEditor::paint (juce::Graphics& g)
{
    g.fillAll (juce::Colour (0xff1a1a2e));

    g.setColour (juce::Colour (0xffe0d6c8));
    g.setFont (juce::FontOptions (24.0f));
    g.drawText ("TsukiSynth",
                getLocalBounds().removeFromTop (50),
                juce::Justification::centred);

    g.setFont (juce::FontOptions (11.0f));
    g.setColour (juce::Colour (0xff666666));
    g.drawText ("Phase 2 - Modal Synthesis String Model",
                getLocalBounds().removeFromTop (68),
                juce::Justification::centred);
}

void TsukiSynthEditor::resized()
{
    auto area = getLocalBounds();
    auto keyboard = area.removeFromBottom (120).reduced (10, 0);
    keyboardComponent.setBounds (keyboard);

    area.removeFromTop (75);
    auto controlArea = area.removeFromTop (80).reduced (20, 0);

    auto row1 = controlArea.removeFromTop (35);
    materialLabel.setBounds (row1.removeFromLeft (80));
    materialBox.setBounds (row1.removeFromLeft (200));

    controlArea.removeFromTop (10);
    auto row2 = controlArea.removeFromTop (35);
    strikeLabel.setBounds (row2.removeFromLeft (110));
    strikeSlider.setBounds (row2.removeFromLeft (250));
}

void TsukiSynthEditor::populateMaterialBox()
{
    materialBox.clear();
    auto keys = processorRef.getMaterialDB().getMaterialKeys();
    int id = 1;
    for (const auto& key : keys)
    {
        if (const auto* mat = processorRef.getMaterialDB().getMaterial (key))
            materialBox.addItem (juce::String (mat->displayName), id++);
        else
            materialBox.addItem (juce::String (key), id++);
    }
}

void TsukiSynthEditor::handleNoteOn (juce::MidiKeyboardState*, int midiChannel,
                                      int midiNoteNumber, float velocity)
{
    auto message = juce::MidiMessage::noteOn (midiChannel, midiNoteNumber, velocity);
    processorRef.addMidiMessage (message);
}

void TsukiSynthEditor::handleNoteOff (juce::MidiKeyboardState*, int midiChannel,
                                       int midiNoteNumber, float velocity)
{
    auto message = juce::MidiMessage::noteOff (midiChannel, midiNoteNumber, velocity);
    processorRef.addMidiMessage (message);
}
