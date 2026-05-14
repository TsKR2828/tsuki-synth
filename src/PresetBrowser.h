#pragma once
#include <juce_gui_basics/juce_gui_basics.h>
#include "TsukiLookAndFeel.h"
#include "PresetManager.h"

class PresetBrowser : public juce::Component
{
public:
    enum Category { All = 0, Cimbalom, Chromatic, FMPiano, User };

    PresetBrowser (PresetManager& pm) : presetManager (pm)
    {
        for (int i = 0; i < 5; ++i)
        {
            auto* btn = catButtons.add (new juce::TextButton());
            btn->setRadioGroupId (9001);
            btn->setClickingTogglesState (true);
            btn->setColour (juce::TextButton::buttonColourId, Clr::comboBg);
            btn->setColour (juce::TextButton::buttonOnColourId, Clr::gold.withAlpha (0.25f));
            btn->setColour (juce::TextButton::textColourOffId, Clr::textDim);
            btn->setColour (juce::TextButton::textColourOnId, Clr::goldLight);
            btn->onClick = [this, i] { selectedCategory = i; rebuild(); };
            addAndMakeVisible (btn);
        }
        catButtons[0]->setButtonText ("All");
        catButtons[1]->setButtonText ("Cimbalom");
        catButtons[2]->setButtonText ("Chromatic");
        catButtons[3]->setButtonText ("FM");
        catButtons[4]->setButtonText ("User");
        catButtons[0]->setToggleState (true, juce::dontSendNotification);

        viewport.setViewedComponent (&listContainer, false);
        viewport.setScrollBarsShown (true, false);
        viewport.setColour (juce::ScrollBar::thumbColourId, Clr::gold.withAlpha (0.3f));
        addAndMakeVisible (viewport);

        rebuild();
    }

    std::function<void (int)> onPresetSelected;

    void rebuild()
    {
        listContainer.removeAllChildren();
        itemButtons.clear();

        auto& pm = presetManager;
        int nFactory = pm.getNumFactoryPresets();
        int total    = pm.getNumPresets();
        int current  = pm.getCurrentIndex();

        for (int i = 0; i < total; ++i)
        {
            int cat = categoryOf (i, nFactory);
            if (selectedCategory != All && cat != selectedCategory)
                continue;

            auto* btn = itemButtons.add (new juce::TextButton());
            btn->setButtonText (pm.getPresetName (i));
            btn->setComponentID (juce::String (i));

            bool isCurrent = (i == current);
            btn->setColour (juce::TextButton::buttonColourId,
                            isCurrent ? Clr::gold.withAlpha (0.18f) : Clr::panelBg);
            btn->setColour (juce::TextButton::textColourOffId,
                            isCurrent ? Clr::goldLight : Clr::text);

            if (i >= nFactory)
                btn->setColour (juce::TextButton::textColourOffId,
                                isCurrent ? Clr::goldLight : Clr::gold.withAlpha (0.7f));

            btn->onClick = [this, i]
            {
                if (onPresetSelected)
                    onPresetSelected (i);
            };

            listContainer.addAndMakeVisible (btn);
        }

        layoutList();
    }

    void paint (juce::Graphics& g) override
    {
        g.fillAll (Clr::panelBg);
        g.setColour (Clr::effectBorder);
        g.drawRect (getLocalBounds(), 1);
    }

    void resized() override
    {
        auto area = getLocalBounds().reduced (4);
        auto catRow = area.removeFromTop (24);
        area.removeFromTop (4);

        int bw = catRow.getWidth() / 5;
        for (auto* btn : catButtons)
            btn->setBounds (catRow.removeFromLeft (bw));

        viewport.setBounds (area);
        layoutList();
    }

private:
    PresetManager& presetManager;
    int selectedCategory = All;

    juce::OwnedArray<juce::TextButton> catButtons;
    juce::Viewport viewport;
    juce::Component listContainer;
    juce::OwnedArray<juce::TextButton> itemButtons;

    static int categoryOf (int index, int nFactory)
    {
        if (index >= nFactory) return User;
        if (index < 4)  return Cimbalom;
        if (index < 8)  return Chromatic;
        return FMPiano;
    }

    void layoutList()
    {
        int itemH = 28;
        int y = 0;
        int w = viewport.getWidth() - (viewport.isVerticalScrollBarShown() ? 10 : 0);
        w = juce::jmax (w, 100);

        for (auto* btn : itemButtons)
        {
            btn->setBounds (0, y, w, itemH);
            y += itemH;
        }

        listContainer.setSize (w, juce::jmax (y, viewport.getHeight()));
    }

    JUCE_DECLARE_NON_COPYABLE_WITH_LEAK_DETECTOR (PresetBrowser)
};

class PresetNameButton : public juce::Component
{
public:
    PresetNameButton()
    {
        setInterceptsMouseClicks (true, false);
    }

    void setName (const juce::String& n)
    {
        displayName = n;
        repaint();
    }

    void paint (juce::Graphics& g) override
    {
        auto b = getLocalBounds().toFloat();

        g.setColour (Clr::comboBg);
        g.fillRoundedRectangle (b, 3.0f);
        g.setColour (isHovered ? Clr::gold.withAlpha (0.5f) : Clr::comboBorder);
        g.drawRoundedRectangle (b.reduced (0.5f), 3.0f, 0.5f);

        g.setColour (Clr::goldLight);
        g.setFont (juce::FontOptions (12.0f));
        g.drawText (displayName, b.reduced (8, 0), juce::Justification::centredLeft);

        float arrowX = b.getRight() - 16.0f;
        float arrowY = b.getCentreY();
        juce::Path arrow;
        arrow.addTriangle (arrowX - 3, arrowY - 2, arrowX + 3, arrowY - 2, arrowX, arrowY + 2);
        g.setColour (Clr::textDim);
        g.fillPath (arrow);
    }

    void mouseEnter (const juce::MouseEvent&) override { isHovered = true;  repaint(); }
    void mouseExit  (const juce::MouseEvent&) override { isHovered = false; repaint(); }

    std::function<void()> onClick;
    void mouseUp (const juce::MouseEvent& e) override
    {
        if (e.mouseWasClicked() && onClick)
            onClick();
    }

private:
    juce::String displayName;
    bool isHovered = false;
};
