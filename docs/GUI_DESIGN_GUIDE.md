# TsukiSynth GUI Design Guide

> Phase 7 Visual Design Brief — for designer reference
> Last updated: 2026-05-08

---

## 1. Product Overview

**TsukiSynth** is a physical modeling + FM synthesis VST3/Standalone plugin built with C++/JUCE.

It contains **3 synthesis engines** that the user switches between:
1. **Cimbalom** — hammered string (physical modeling)
2. **Chromatic** — tongue drum / water gong / custom harmonics (physical modeling)
3. **FM Piano** — frequency modulation synthesis (DX7-style)

Plus a **global effect chain** (Reverb, Delay, Compressor) that applies to all engines.

**Window size**: approximately 520 x 580 px (resizable is optional but not required).

---

## 2. Design Direction

### Mood & Atmosphere
- **Dark, warm, tactile** — like holding a handcrafted wooden instrument in a dimly lit studio
- Inspired by premium acoustic instruments: rosewood, ebony, aged brass hardware
- NOT cold/clinical/futuristic — this is NOT a wavetable synth
- NOT skeuomorphic (don't draw literal wood planks) — use **abstract warmth** through color and texture

### Keywords
`warm` `organic` `handcrafted` `intimate` `twilight` `moon` `japanese aesthetic`

### Name meaning
Tsuki (月) = Moon in Japanese. The brand identity leans into **lunar / night / quiet elegance**.

---

## 3. Color Palette

### Background layers
| Role | Hex | Description |
|------|-----|-------------|
| Deep background | `#0f0f1a` | Near-black with blue undertone (night sky) |
| Panel background | `#1a1a2e` | Current base — dark indigo |
| Raised surface | `#232340` | Cards, grouped sections |
| Subtle border | `#2a2a4a` | Section dividers, panel edges |

### Accent colors
| Role | Hex | Usage |
|------|-----|-------|
| Primary accent | `#c49a6c` | Warm gold/amber — active knob rings, selected tabs, value text |
| Secondary accent | `#7b8ea8` | Cool steel blue — labels, inactive elements |
| Highlight | `#e8c88a` | Bright gold — hover states, peak indicators |
| Engine: Cimbalom | `#c49a6c` | Warm brass (matches hammered metal) |
| Engine: Chromatic | `#8bb8a8` | Jade green (crystal/nature) |
| Engine: FM Piano | `#a88bc4` | Soft purple (electronic/synth) |

### Text
| Role | Hex |
|------|-----|
| Title | `#e0e0e0` |
| Value readout | `#d4b896` (warm white) |
| Label | `#8899aa` (muted blue-grey) |
| Disabled | `#444466` |

### Functional
| Role | Hex |
|------|-----|
| Positive / active | `#6aaa7a` |
| Warning / clip | `#cc7744` |
| Error / overload | `#cc4444` |

---

## 4. Typography

JUCE uses system fonts. Recommended stack:

| Role | Font | Size | Weight | Tracking |
|------|------|------|--------|----------|
| Plugin title "TsukiSynth" | Default sans | 22-26px | Bold | +1px |
| Engine subtitle | Default sans | 11-12px | Regular | +0.5px (uppercase) |
| Section header (ENGINE / EFFECTS) | Default sans | 10-11px | Bold | +2px (uppercase) |
| Parameter label | Default sans | 11-12px | Regular | normal |
| Value readout | Default sans or mono | 11-12px | Regular | normal |
| Preset name | Default sans | 12px | Medium | normal |

---

## 5. Layout Structure

```
+----------------------------------------------------------+
|                      TsukiSynth                          |  <- Title bar
|          Chromatic Engine | Beam / Plate / Custom         |  <- Subtitle (changes per engine)
+----------------------------------------------------------+
| [Preset: ▼ Crystal Tongue Drum]                          |  <- Preset selector (full width)
+----------------------------------------------------------+
|  [ Cimbalom ]  [ Chromatic ]  [ FM Piano ]               |  <- Engine tabs (3 buttons)
+----------------------------------------------------------+
|                                                          |
|  ┌─ ENGINE PARAMETERS ─────────────────────────────┐    |
|  │                                                  │    |  <- Dynamic content area
|  │   (6-7 parameters per engine)                    │    |     switches with engine tabs
|  │   arranged in 2-column grid of rotary knobs      │    |
|  │   + combo boxes for categorical params           │    |
|  │                                                  │    |
|  └──────────────────────────────────────────────────┘    |
|                                                          |
+--- EFFECTS ─────────────────────────────────────────────+
|                                                          |
|  ┌─ REVERB ──┐  ┌─ DELAY ───┐  ┌─ COMPRESSOR ─┐       |  <- 3 effect groups
|  │ Mix  Size │  │ Time FB Mix│  │ Thresh  Ratio │       |     always visible
|  └───────────┘  └───────────┘  └───────────────┘       |
|                                                          |
+----------------------------------------------------------+
```

### Engine Tab Buttons
- 3 toggle buttons, only one active at a time
- Active tab: filled with engine accent color + white text
- Inactive tab: outlined border + muted text
- Each tab has a subtle icon or symbol (optional):
  - Cimbalom: a small string/hammer icon
  - Chromatic: a bell or wave icon
  - FM Piano: a sine wave icon

### Content Area
- Parameters displayed as **rotary knobs** (not horizontal sliders)
- 2 columns, 3-4 rows
- ComboBox parameters (Material, Hammer, Type, etc.) use styled dropdown menus
- Each knob has: label above, value readout below

### Effects Section
- Fixed at bottom, always visible regardless of engine
- 3 grouped panels side by side
- Smaller knobs than engine parameters (compact layout)
- Subtle background color difference to separate from engine area

---

## 6. Component Styles

### Rotary Knob (primary control)
```
        Label
      ┌───────┐
      │  ╭─╮  │
      │ ╱   ╲ │     Arc: 270-degree sweep
      │|  ●  | │     Filled arc = current value (accent color)
      │ ╲   ╱ │     Unfilled arc = remaining range (dark)
      │  ╰─╯  │     Center dot = grab point
      └───────┘
       Value
```
- **Size**: 48-56px diameter for engine params, 36-42px for effect params
- **Arc style**: 270-degree sweep, starting from 7 o'clock to 5 o'clock
- **Filled portion**: accent color gradient (slightly brighter at the indicator end)
- **Track (unfilled)**: `#1a1a2e` with subtle inner shadow
- **Indicator**: small bright dot or line at the current position
- **Center**: engine accent color circle or dark circle with subtle gradient
- **Hover**: indicator brightens, subtle glow around arc
- **Label**: above the knob, `#8899aa`, uppercase, 10px
- **Value**: below the knob, `#d4b896`, 11px, shows current value + unit

### ComboBox (dropdown selector)
- Dark background (`#1e1e36`) with subtle border (`#333355`)
- Text: `#cccccc`
- Arrow indicator: small triangle, accent color
- Dropdown popup: slightly lighter background, hover highlight with accent color
- Selected item: accent color text or left-side color bar

### Engine Tab Button
- **Inactive**: transparent background, `#666688` text, thin border `#333355`
- **Active**: engine accent color background (15% opacity), engine accent text, bottom border highlight (2px solid accent)
- **Hover**: background lightens slightly
- Corner radius: 4-6px (top corners only, connecting to panel below)

### Section Divider
- Thin horizontal line: `#2a2a4a`
- Optional section label: uppercase, `#556677`, 9-10px, tracking +2px
- Label sits on the line with small padding (pill style or left-aligned)

### Preset ComboBox
- Full-width or wide (>60% of window width)
- Slightly larger text than parameter combos
- Left: "PRESET" label in small caps
- Preset name in brighter text (`#d4b896`)

---

## 7. Engine-Specific Parameter Layout

### Cimbalom (6 params)
```
Row 1:  [Material ▼]            [Hammer ▼]
Row 2:  (Strike Position knob)  (Diameter knob)
Row 3:  (Strings knob)          (Detuning knob)
```

### Chromatic (7 params)
```
Row 1:  [Sub-engine ▼]          [Material ▼]
Row 2:  (Strike Pos knob)       (Thickness knob)
Row 3:  (Size knob)             [Exciter ▼]
Row 4:  (Pitch Glide knob)      ---
```
- Pitch Glide knob: only visually prominent when Water Gong sub-engine selected (otherwise greyed/dimmed)

### FM Piano (7 params)
```
Row 1:  [Sound Type ▼]          ---
Row 2:  (Ratio knob)            (Mod Index knob)
Row 3:  (Brightness knob)       (Feedback knob)
Row 4:  (Attack knob)           (Release knob)
```

---

## 8. Effects Section Detail

```
┌── REVERB ──────┐  ┌── DELAY ──────────┐  ┌── COMPRESSOR ────┐
│  (Mix)  (Room)  │  │ (Time) (FB) (Mix) │  │ (Thresh) (Ratio) │
└─────────────────┘  └──────────────────┘  └──────────────────┘
```

- 3 panels with subtle raised background (`#1e1e30`)
- Each panel has a section title in small caps: `REVERB` / `DELAY` / `COMPRESSOR`
- Smaller knobs (36-42px)
- Compact spacing
- When a section is effectively bypassed (mix=0 or ratio=1), the panel dims slightly

---

## 9. Visual Polish Details

### Subtle Texture
- Very faint noise texture overlaid on the deep background (2-3% opacity)
- Gives a warm, organic feel without being literal wood grain
- Alternative: very subtle radial gradient from center (slightly lighter) to edges

### Shadows & Depth
- Panels have subtle drop shadow (2-4px blur, `#000000` 20%)
- Knobs have slight inner shadow on the track for depth
- Active tab has a subtle glow (engine accent color, 10% opacity, 8px blur)

### Animations (if implemented)
- Knob rotation: smooth interpolation (not jumpy)
- Engine tab switch: crossfade content (150ms)
- Preset change: brief flash on the preset name

### Hover & Interaction States
- Knob hover: value readout becomes brighter, knob indicator glows
- Knob drag: indicator becomes a bright line (from dot)
- ComboBox hover: border brightens to accent color
- Tab hover: background lightens 5%

---

## 10. Logo & Title Treatment

### "TsukiSynth" wordmark
- Clean sans-serif, 22-26px
- Subtle letter-spacing (+1px)
- Color: `#e0e0e0` with optional subtle gradient (white to warm gold)
- Optional: a small crescent moon icon (2-3px stroke) to the left of "Tsuki"

### Subtitle
- Changes dynamically per engine:
  - `CIMBALOM ENGINE  |  Physical Modeling String`
  - `CHROMATIC ENGINE  |  Beam / Plate / Custom`
  - `FM PIANO ENGINE  |  Frequency Modulation Synthesis`
- 11px, uppercase, `#667788`, tracking +1px
- The pipe `|` separator in slightly darker color

---

## 11. Current Implementation Reference

The current editor uses basic JUCE components:
- `juce::Slider` (LinearHorizontal) — to be replaced with **rotary knobs**
- `juce::ComboBox` — to be **styled** (custom LookAndFeel)
- `juce::Label` — styling via color/font changes
- Background: flat `#1a1a2e` — to gain **texture and depth**

The switch to rotary knobs is the biggest visual change. All parameter wiring (APVTS attachments) stays the same; only the Slider style changes from `LinearHorizontal` to `RotaryHorizontalVerticalDrag`.

### JUCE Technical Notes
- Custom styling via `juce::LookAndFeel_V4` subclass
- Knob appearance: override `drawRotarySlider()`
- ComboBox appearance: override `drawComboBox()` + `drawPopupMenuItem()`
- Tab buttons: custom `juce::TextButton` with state-dependent colors
- Background texture: `juce::Image` or procedural in `paint()`
- All colors defined in a central theme struct for easy adjustment

---

## 12. Deliverables Expected

1. **Full plugin window mockup** (520x580 or adjusted size) showing one engine active
2. **All 3 engine states** (Cimbalom / Chromatic / FM Piano tab selected)
3. **Component close-ups**: knob states (default / hover / active), ComboBox, tab buttons
4. **Color/token sheet**: final hex values for all roles
5. **Effects section** detail view

---

## 13. Reference & Inspiration

Instruments and aesthetics to draw from:
- Hammered dulcimer (warm wood + brass strings)
- Japanese moon viewing (tsukimi) — serene, minimal, dark
- Premium VST plugins with dark themes: FabFilter, Arturia, u-he Diva
- Avoid: neon colors, sharp corners, overly complex textures

The design should feel like **opening a lacquered wooden instrument case at night** — dark, warm, revealing something precious inside.
