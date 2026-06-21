#pragma once
#include <juce_gui_basics/juce_gui_basics.h>

// ═══════════════════════════════════════════════════════════════════════
//  Colour palette — matches uiux/TsukiSynth.html CSS exactly
// ═══════════════════════════════════════════════════════════════════════
namespace Clr
{
    inline const juce::Colour bg             (0xff07070d);
    inline const juce::Colour pluginTop      (0xff1a1a2e);
    inline const juce::Colour pluginBot      (0xff16162a);
    inline const juce::Colour presetBg       (0xff14142a);
    inline const juce::Colour engineTop      (0xff16162a);
    inline const juce::Colour engineBot      (0xff131326);
    inline const juce::Colour effectsBg      (0xff11111e);
    inline const juce::Colour panelBg        (0xff1a1a30);
    inline const juce::Colour kbFooter       (0xff0c0c18);

    inline const juce::Colour border         (0xff2a2a4a);
    inline const juce::Colour borderLight    (0xff232340);
    inline const juce::Colour borderFocus    (0xff3a3a5a);
    inline const juce::Colour effectBorder   (0xff232342);

    inline const juce::Colour text           (0xffe0e0e0);
    inline const juce::Colour textDim        (0xff667788);
    inline const juce::Colour textMid        (0xff8899aa);
    inline const juce::Colour label          (0xff8899aa);
    inline const juce::Colour valueText      (0xffd4b896);
    inline const juce::Colour fxTitle        (0xff6a7a8a);
    inline const juce::Colour divLabel       (0xff556677);

    inline const juce::Colour comboBg        (0xff1e1e36);
    inline const juce::Colour comboBorder    (0xff333355);
    inline const juce::Colour comboText      (0xffcccccc);

    inline const juce::Colour gold           (0xffc49a6c);
    inline const juce::Colour goldBright     (0xffd4b896);
    inline const juce::Colour goldLight      (0xffe0d2b8);

    inline const juce::Colour cimbalom       (0xffc49a6c);
    inline const juce::Colour chromatic      (0xff8bb8a8);
    inline const juce::Colour fm             (0xffa88bc4);
    inline const juce::Colour piano          (0xff8ba0c4);

    inline const juce::Colour knobTrack      (0xff10101c);
    inline const juce::Colour knobFaceA      (0xff2a2a44);
    inline const juce::Colour knobFaceB      (0xff1d1d33);
    inline const juce::Colour knobFaceC      (0xff11111e);

    inline const juce::Colour whiteKey       (0xffd8cdb6);
    inline const juce::Colour blackKey       (0xff2a2535);
    inline const juce::Colour tabInactive    (0xff667788);
}

// ═══════════════════════════════════════════════════════════════════════
//  TsukiLookAndFeel — custom drawing for the synth plugin
// ═══════════════════════════════════════════════════════════════════════
class TsukiLookAndFeel : public juce::LookAndFeel_V4
{
public:
    juce::Colour accent { Clr::gold };

    static constexpr float fontScale = 1.2f;

    static juce::Font scaledFont (float baseSize)
    {
        return juce::FontOptions (baseSize * fontScale);
    }

    TsukiLookAndFeel()
    {
        // CJK-capable font — required for Traditional Chinese UI labels.
        // Microsoft JhengHei is bundled with all Chinese Windows editions
        // and has good ASCII coverage. Falls back to system default if absent.
        setDefaultSansSerifTypefaceName ("Microsoft JhengHei");

        setColour (juce::PopupMenu::backgroundColourId,            juce::Colour (0xff20203a));
        setColour (juce::PopupMenu::highlightedBackgroundColourId, Clr::gold.withAlpha (0.10f));
        setColour (juce::PopupMenu::textColourId,                  Clr::comboText);
        setColour (juce::PopupMenu::highlightedTextColourId,       Clr::goldLight);

        setColour (juce::ComboBox::backgroundColourId,  Clr::comboBg);
        setColour (juce::ComboBox::outlineColourId,     Clr::comboBorder);
        setColour (juce::ComboBox::textColourId,        Clr::comboText);
        setColour (juce::ComboBox::arrowColourId,       accent);

        setColour (juce::Slider::textBoxTextColourId,       Clr::valueText);
        setColour (juce::Slider::textBoxBackgroundColourId, juce::Colours::transparentBlack);
        setColour (juce::Slider::textBoxOutlineColourId,    juce::Colours::transparentBlack);

        setColour (juce::Label::textColourId, Clr::label);
    }

    // ── Rotary knob: arc track + gradient face + indicator ─────────
    void drawRotarySlider (juce::Graphics& g, int x, int y, int w, int h,
                           float sliderPos, float startAng, float endAng,
                           juce::Slider&) override
    {
        auto area = juce::Rectangle<float> ((float) x, (float) y, (float) w, (float) h)
                        .reduced (2.0f);
        float cx     = area.getCentreX();
        float cy     = area.getCentreY();
        float radius = juce::jmin (area.getWidth(), area.getHeight()) * 0.5f;
        float trackR = radius * 0.88f;
        float faceR  = radius * 0.68f;
        float indR   = radius * 0.62f;
        float angle  = startAng + sliderPos * (endAng - startAng);
        constexpr float halfPi = juce::MathConstants<float>::halfPi;

        // subtle outer ring
        g.setColour (juce::Colour (0x06ffffff));
        float outerR = trackR + 3.5f;
        g.drawEllipse (cx - outerR, cy - outerR, outerR * 2.0f, outerR * 2.0f, 0.8f);

        // background track arc
        {
            juce::Path bg;
            bg.addCentredArc (cx, cy, trackR, trackR, 0.0f, startAng, endAng, true);
            g.setColour (Clr::knobTrack);
            g.strokePath (bg, juce::PathStrokeType (3.0f, juce::PathStrokeType::curved,
                                                     juce::PathStrokeType::rounded));
        }

        // filled value arc
        if (sliderPos > 0.005f)
        {
            juce::Path fill;
            fill.addCentredArc (cx, cy, trackR, trackR, 0.0f, startAng, angle, true);
            g.setColour (accent);
            g.strokePath (fill, juce::PathStrokeType (3.0f, juce::PathStrokeType::curved,
                                                       juce::PathStrokeType::rounded));
        }

        // face circle with radial gradient
        {
            juce::ColourGradient grad (Clr::knobFaceA, cx - faceR * 0.3f, cy - faceR * 0.4f,
                                       Clr::knobFaceC, cx + faceR * 0.5f, cy + faceR * 0.7f, true);
            grad.addColour (0.55, Clr::knobFaceB);
            g.setGradientFill (grad);
            g.fillEllipse (cx - faceR, cy - faceR, faceR * 2.0f, faceR * 2.0f);

            g.setColour (juce::Colour (0x80000000));
            g.drawEllipse (cx - faceR, cy - faceR, faceR * 2.0f, faceR * 2.0f, 0.5f);

            g.setColour (juce::Colour (0x0dffffff));
            g.drawEllipse (cx - faceR, cy - faceR - 0.5f, faceR * 2.0f, faceR * 2.0f, 0.5f);
        }

        // indicator line + dot
        float tipX = cx + indR * std::cos (angle - halfPi);
        float tipY = cy + indR * std::sin (angle - halfPi);
        g.setColour (accent);
        g.drawLine (cx, cy, tipX, tipY, 1.6f);
        g.fillEllipse (tipX - 1.8f, tipY - 1.8f, 3.6f, 3.6f);
    }

    // ── ComboBox trigger ───────────────────────────────────────────
    void drawComboBox (juce::Graphics& g, int w, int h, bool,
                       int, int, int, int, juce::ComboBox&) override
    {
        auto area = juce::Rectangle<float> (0.0f, 0.0f, (float) w, (float) h);
        g.setColour (Clr::comboBg);
        g.fillRoundedRectangle (area, 4.0f);
        g.setColour (Clr::comboBorder);
        g.drawRoundedRectangle (area.reduced (0.5f), 4.0f, 0.5f);

        float chX = (float) w - 16.0f;
        float chY = (float) h * 0.5f - 2.5f;
        juce::Path chev;
        chev.addTriangle (chX, chY, chX + 7.0f, chY, chX + 3.5f, chY + 5.0f);
        g.setColour (accent);
        g.fillPath (chev);
    }

    // ── Popup menu ─────────────────────────────────────────────────
    void drawPopupMenuBackground (juce::Graphics& g, int w, int h) override
    {
        g.setColour (juce::Colour (0xff20203a));
        g.fillRoundedRectangle (0.0f, 0.0f, (float) w, (float) h, 5.0f);
        g.setColour (Clr::borderFocus);
        g.drawRoundedRectangle (0.5f, 0.5f, (float) w - 1.0f, (float) h - 1.0f, 5.0f, 0.5f);
    }

    void drawPopupMenuItem (juce::Graphics& g, const juce::Rectangle<int>& area,
                            bool, bool isActive, bool isHighlighted,
                            bool isTicked, bool,
                            const juce::String& text, const juce::String&,
                            const juce::Drawable*, const juce::Colour*) override
    {
        if (isHighlighted && isActive)
        {
            g.setColour (Clr::gold.withAlpha (0.10f));
            g.fillRoundedRectangle (area.toFloat().reduced (3.0f, 0.5f), 3.0f);
        }

        if (isTicked)
        {
            g.setColour (accent);
            g.fillRoundedRectangle ((float) area.getX() + 4.0f,
                                    (float) area.getY() + 6.0f,
                                    2.0f,
                                    (float) area.getHeight() - 12.0f, 1.0f);
        }

        g.setColour (isTicked ? accent : (isHighlighted ? Clr::goldLight : Clr::comboText));
        g.setFont (scaledFont (11.0f));
        g.drawText (text, area.reduced (14, 0), juce::Justification::centredLeft);
    }

    int getPopupMenuBorderSize() override { return 3; }
    juce::Font getPopupMenuFont() override { return scaledFont (11.0f); }
    juce::Font getComboBoxFont (juce::ComboBox&) override { return scaledFont (11.0f); }

    // ── Label ──────────────────────────────────────────────────────
    void drawLabel (juce::Graphics& g, juce::Label& lbl) override
    {
        g.setColour (lbl.findColour (juce::Label::textColourId));
        g.setFont (lbl.getFont());
        g.drawText (lbl.getText(), lbl.getLocalBounds(),
                    lbl.getJustificationType(), false);
    }

    // ── Slider text box (monospace value display) ──────────────────
    juce::Label* createSliderTextBox (juce::Slider& s) override
    {
        auto* l = juce::LookAndFeel_V4::createSliderTextBox (s);
        l->setColour (juce::Label::textColourId, Clr::valueText);
        l->setColour (juce::Label::backgroundColourId, juce::Colours::transparentBlack);
        l->setColour (juce::Label::outlineColourId, juce::Colours::transparentBlack);
        l->setJustificationType (juce::Justification::centred);
        l->setFont (scaledFont (10.5f));
        return l;
    }

    // ── Button (tab / step / icon) ────────────────────────────────
    void drawButtonBackground (juce::Graphics& g, juce::Button& btn,
                               const juce::Colour&, bool isOver, bool) override
    {
        auto area = btn.getLocalBounds().toFloat();
        auto id   = btn.getComponentID();

        if (id == "tab")
        {
            if (btn.getToggleState())
            {
                g.setColour (accent.withAlpha (0.15f));
                g.fillRoundedRectangle (area.withTrimmedBottom (-2.0f), 5.0f);
                g.setColour (accent);
                g.fillRect (area.getX() + 4.0f, area.getBottom() - 2.0f,
                            area.getWidth() - 8.0f, 2.0f);
            }
            else if (isOver)
            {
                g.setColour (juce::Colour (0x06ffffff));
                g.fillRoundedRectangle (area, 5.0f);
            }
        }
        else if (id == "step")
        {
            g.setColour (Clr::comboBg);
            g.fillRoundedRectangle (area, 3.0f);
            g.setColour (isOver ? accent : Clr::border);
            g.drawRoundedRectangle (area.reduced (0.5f), 3.0f, 0.5f);
        }
    }

    void drawButtonText (juce::Graphics& g, juce::TextButton& btn,
                         bool isOver, bool) override
    {
        auto id = btn.getComponentID();

        if (id == "tab")
        {
            g.setFont (scaledFont (11.0f));
            g.setColour (btn.getToggleState() ? accent
                                              : (isOver ? juce::Colour (0xffaaaacc) : Clr::tabInactive));
            g.drawText (btn.getButtonText(), btn.getLocalBounds(),
                        juce::Justification::centred);
        }
        else if (id == "step")
        {
            g.setFont (scaledFont (13.0f));
            g.setColour (isOver ? accent : Clr::textMid);
            g.drawText (btn.getButtonText(), btn.getLocalBounds(),
                        juce::Justification::centred);
        }
        else
        {
            g.setFont (scaledFont (11.0f));
            g.setColour (btn.findColour (juce::TextButton::textColourOffId));
            g.drawText (btn.getButtonText(), btn.getLocalBounds(),
                        juce::Justification::centred);
        }
    }

    // ── Tooltip (白框 bilingual popup) ────────────────────────────
    juce::Rectangle<int> getTooltipBounds (const juce::String& tipText,
                                            juce::Point<int> screenPos,
                                            juce::Rectangle<int> parentArea) override
    {
        auto font = scaledFont (12.0f);
        int textW = (int) juce::GlyphArrangement::getStringWidth (font, tipText) + 1;
        int w = juce::jmin (400, juce::jmax (80, textW + 28));
        int h = 34;

        int x = screenPos.x > parentArea.getCentreX()
                    ? screenPos.x - w - 8
                    : screenPos.x + 12;
        int y = screenPos.y > parentArea.getCentreY()
                    ? screenPos.y - h - 8
                    : screenPos.y + 20;

        return juce::Rectangle<int> (x, y, w, h).constrainedWithin (parentArea);
    }

    void drawTooltip (juce::Graphics& g, const juce::String& text,
                      int width, int height) override
    {
        auto bounds = juce::Rectangle<float> (0.0f, 0.0f, (float) width, (float) height);

        g.setColour (juce::Colour (0xfff5f0e8));
        g.fillRoundedRectangle (bounds, 5.0f);

        g.setColour (juce::Colour (0x30000000));
        g.drawRoundedRectangle (bounds.reduced (0.5f), 5.0f, 1.0f);

        g.setColour (juce::Colour (0xff1a1a2e));
        g.setFont (scaledFont (12.0f));
        g.drawText (text, bounds.toNearestInt().reduced (12, 0),
                    juce::Justification::centred, true);
    }
};
