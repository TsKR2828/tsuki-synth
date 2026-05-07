#include "PluginEditor.h"

TsukiSynthEditor::TsukiSynthEditor (TsukiSynthProcessor& p)
    : AudioProcessorEditor (&p), processorRef (p)
{
    setSize (480, 320);
}

TsukiSynthEditor::~TsukiSynthEditor() {}

void TsukiSynthEditor::paint (juce::Graphics& g)
{
    g.fillAll (juce::Colour (0xff1a1a2e));

    g.setColour (juce::Colour (0xffe0e0e0));
    g.setFont (juce::FontOptions (28.0f));
    g.drawFittedText ("TsukiSynth", getLocalBounds().removeFromTop (80),
                      juce::Justification::centred, 1);

    g.setColour (juce::Colour (0xff888888));
    g.setFont (juce::FontOptions (14.0f));
    g.drawFittedText ("Phase 1 — Sine Wave Test\nPlay MIDI to hear sound",
                      getLocalBounds().reduced (20),
                      juce::Justification::centred, 2);
}

void TsukiSynthEditor::resized() {}
