#pragma once

#include <juce_gui_basics/juce_gui_basics.h>
#include "TsukiLookAndFeel.h"

/**
 * Accessibility hover magnifier: while the mouse rests over any small text
 * control (Label / TextButton / ComboBox), a floating bubble repeats that
 * control's visible text at a large, readable size.
 *
 * One instance serves the whole editor: the editor registers itself as a
 * global mouse listener target (addMouseListener with
 * wantsEventsForAllNestedChildComponents = true) and forwards events here.
 * The bubble never intercepts mouse events, so it cannot steal hover or
 * clicks from the control underneath.
 */
class HoverMagnifier : public juce::Component
{
public:
    HoverMagnifier()
    {
        setInterceptsMouseClicks (false, false);
        setAlwaysOnTop (true);
        setVisible (false);
    }

    /** The component the bubble positions itself inside (the editor). */
    void setOwner (juce::Component* ownerComponent) { owner = ownerComponent; }

    void mouseMove (const juce::MouseEvent& e) override  { refreshFrom (e); }
    void mouseEnter (const juce::MouseEvent& e) override { refreshFrom (e); }
    void mouseExit (const juce::MouseEvent&) override    { hideBubble(); }

    void paint (juce::Graphics& g) override
    {
        auto bounds = getLocalBounds().toFloat();

        g.setColour (juce::Colour (0xfff5f0e8));
        g.fillRoundedRectangle (bounds, 6.0f);
        g.setColour (juce::Colour (0x40000000));
        g.drawRoundedRectangle (bounds.reduced (0.5f), 6.0f, 1.0f);

        g.setColour (juce::Colour (0xff1a1a2e));
        g.setFont (TsukiLookAndFeel::scaledFont (magnifiedFontSize).boldened());
        g.drawText (text, getLocalBounds().reduced (10, 2),
                    juce::Justification::centred, true);
    }

private:
    static constexpr float magnifiedFontSize = 22.0f;

    juce::Component* owner = nullptr;
    juce::Component* currentSource = nullptr;
    juce::String text;

    static juce::String textOf (juce::Component* c)
    {
        if (auto* label = dynamic_cast<juce::Label*> (c))
            return label->getText();
        if (auto* button = dynamic_cast<juce::TextButton*> (c))
            return button->getButtonText();
        if (auto* combo = dynamic_cast<juce::ComboBox*> (c))
            return combo->getText();
        return {};
    }

    void refreshFrom (const juce::MouseEvent& e)
    {
        auto* source = e.eventComponent;
        if (owner == nullptr || source == nullptr || source == this)
            return;

        const auto sourceText = textOf (source);
        if (sourceText.isEmpty())
        {
            // Mouse is over a non-text component (knob, keyboard, panel).
            if (source != currentSource)
                hideBubble();
            return;
        }

        currentSource = source;
        text = sourceText;

        // Size the bubble to the magnified text.
        const auto font = TsukiLookAndFeel::scaledFont (magnifiedFontSize)
                              .boldened();
        const int textW = (int) juce::GlyphArrangement::getStringWidth (font,
                                                                        text)
                        + 1;
        const int w = juce::jmin (owner->getWidth() - 8,
                                  juce::jmax (48, textW + 24));
        const int h = 36;

        // Place above the source control (below if there is no room),
        // horizontally centred on it, kept inside the editor.
        const auto sourceInOwner = owner->getLocalArea (source,
                                                        source->getLocalBounds());
        int x = sourceInOwner.getCentreX() - w / 2;
        int y = sourceInOwner.getY() - h - 6;
        if (y < 0)
            y = sourceInOwner.getBottom() + 6;

        setBounds (juce::Rectangle<int> (x, y, w, h)
                       .constrainedWithin (owner->getLocalBounds()));
        setVisible (true);
        toFront (false);
        repaint();
    }

    void hideBubble()
    {
        currentSource = nullptr;
        setVisible (false);
    }

    JUCE_DECLARE_NON_COPYABLE_WITH_LEAK_DETECTOR (HoverMagnifier)
};
