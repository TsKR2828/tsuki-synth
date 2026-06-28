# TsukiSynth Score JSON — Writing Guide

> A physics-based music synthesizer where you compose by writing JSON.
> No audio knowledge required — describe physical objects, and the engine simulates how they sound.

## Quick Start — Minimal Score

```json
{
  "$schema": "TsukiSynth Score v1",
  "meta": {
    "title": "My First Score",
    "id": "my_first_score"
  },
  "global": {
    "bpm": 120,
    "sample_rate": 48000,
    "master_volume": 0.8
  },
  "events": [
    {
      "time": 0.0,
      "duration": 1.0,
      "engine": "string",
      "note": "C4",
      "velocity": 0.7,
      "params": {
        "material": "steel",
        "diameter_mm": 0.8,
        "exciter": "pluck"
      }
    }
  ],
  "export": {
    "filename": "my_first_score",
    "format": "wav",
    "bit_depth": 24,
    "normalize": true,
    "tail_silence_ms": 500
  }
}
```

Render: `TsukiSynthCLI.exe my_first_score.score.json --output .`

That's it. One steel string, plucked at C4. Now let's learn everything.

---

## Core Concept

Every sound is a **physical simulation**. You pick:
1. **Engine** — what shape of object vibrates (string, beam, plate, or FM)
2. **Material** — what it's made of (steel, glass, bamboo...)
3. **Exciter** — how you hit/bow/pluck it
4. **Dimensions** — how big it is (diameter, length, thickness, radius)

The synthesizer solves the physics equations and produces the audio. Pitch comes from `note`, loudness from `velocity`, timbre from everything else.

> The `fm` and `custom` engines use FM synthesis and user-defined harmonics respectively — they are **not** physical models. They share the score format for convenience but their output is not physically verifiable in the same way as modal engines.

---

## File Structure

```
{
  "$schema": "TsukiSynth Score v1",   // Always this string
  "meta": { ... },                     // Title, author, tags
  "global": { ... },                   // BPM, sample rate, effects
  "events": [ ... ],                   // The notes (sorted by time)
  "export": { ... },                   // Output filename & format

  // Optional:
  "track_profiles": { ... },          // Named instrument presets (documentation only)
  "layers": [ ... ],                  // Composite from other .score.json files
  "crossfade_ms": 0                   // Crossfade between layers
}
```

---

## meta (Required)

| Field | Required | Example |
|-------|----------|---------|
| `title` | YES | `"Moonlit Waltz"` |
| `id` | YES | `"moonlit_waltz"` (lowercase, `a-z0-9_` only) |
| `author` | no | `"Claude"` |
| `description` | no | Free text |
| `created` | no | `"2026-06-22"` |
| `tags` | no | `["ambient", "piano"]` |
| `key` | no | `"C minor"` |
| `mood` | no | `sacred` / `mystical` / `tense` / `ominous` / `playful` / `calm` / `epic` / `melancholic` |

---

## global (Required)

```json
"global": {
  "bpm": 120,
  "sample_rate": 48000,
  "master_volume": 0.8,
  "effects": { ... }
}
```

| Field | Range | Note |
|-------|-------|------|
| `bpm` | 1–999 | **Informational only.** The renderer uses absolute seconds. |
| `sample_rate` | 44100 / 48000 / 88200 / 96000 | Only these 4 values are valid. |
| `master_volume` | 0–1 | Overall output gain. |

---

## Events — The Notes

Each event is one note. Events are in an array, **sorted by `time`**.

```json
{
  "time": 0.0,         // Start time in SECONDS (absolute, not beats)
  "duration": 1.5,     // Duration in SECONDS
  "engine": "string",  // Which physics model
  "note": "C4",        // Pitch (note name OR MIDI 0–127)
  "velocity": 0.7,     // Loudness 0–1
  "params": { ... }    // Engine-specific physical parameters
}
```

### Required Fields Per Event

All five fields (`time`, `duration`, `engine`, `note`, `velocity`) are required. Events missing any are skipped with a warning.

### Note Format

Both formats work:
- Note name: `"C4"`, `"G#5"`, `"Bb3"`, `"F#2"`
- MIDI number: `60` (= C4), `69` (= A4 = 440 Hz)

### Polyphony

Multiple events can share the same `time` — they play simultaneously. This is how you make chords:

```json
{"time": 0.0, "duration": 2.0, "engine": "fm", "note": "C4", "velocity": 0.6, "params": {"fm_preset": 0}},
{"time": 0.0, "duration": 2.0, "engine": "fm", "note": "E4", "velocity": 0.6, "params": {"fm_preset": 0}},
{"time": 0.0, "duration": 2.0, "engine": "fm", "note": "G4", "velocity": 0.6, "params": {"fm_preset": 0}}
```

---

## Engines

### Physical Engines (simulate real vibrating objects)

| Engine | Aliases | What It Is | Required Params |
|--------|---------|------------|-----------------|
| `string` | `cimbalom` | Vibrating wire/string | `material`, `diameter_mm` |
| `beam` | `tongue_drum` | Vibrating bar/rod | `material`, `thickness_mm`, `length_mm`, `width_mm` |
| `plate` | `water_gong`, `membrane` | Vibrating disc/sheet | `material`, `radius_mm`, `thickness_mm` |

### FM Engine (classic FM synthesis)

| Engine | What It Is | Key Param |
|--------|------------|-----------|
| `fm` | 2-operator FM synthesizer | `fm_preset` (0–7) |
| `piano` | Piano variant of string engine | `material`, `diameter_mm` |

### Custom Engine

| Engine | What It Is |
|--------|------------|
| `custom` | User-editable harmonics |

---

## Engine Parameters

### String / Cimbalom

```json
"params": {
  "material": "steel",        // See Materials table
  "diameter_mm": 0.8,         // Wire diameter: 0.1–50 mm
  "strike_position": 0.3,     // 0=edge, 0.5=center, 1=far edge
  "exciter": "pluck",         // See Exciters table
  "damping_override": -1      // -1 = use material default
}
```

Thin strings (0.1–0.5mm) → bright, high. Thick strings (2–5mm) → deep, bass.

### Beam / Tongue Drum

```json
"params": {
  "material": "bamboo",
  "thickness_mm": 2,           // 0.1–1000
  "length_mm": 100,            // 1–10000
  "width_mm": 25,              // 1–10000
  "strike_position": 0.4,
  "exciter": "wood_mallet"
}
```

Long thin beams → low pitch. Short thick beams → high pitch, percussive.

> **Note:** Modal engines compute natural frequencies from physical dimensions, then retune all modes to the MIDI note pitch via chromatic scaling. Dimensions primarily affect **timbre** (harmonic ratios, decay rates) rather than fundamental pitch. The score's `note` field determines the sounding pitch.

### Plate / Water Gong

```json
"params": {
  "material": "bronze",
  "radius_mm": 120,            // 1–10000
  "thickness_mm": 2,           // 0.1–1000
  "plate_free_edge": true,     // true=hung gong, false=clamped
  "strike_position": 0.3,
  "exciter": "felt_mallet"
}
```

`plate_free_edge: true` → gong/cymbal (free to ring). `false` → clamped drum.

### FM Synthesis

```json
"params": {
  "fm_preset": 0,              // 0–7, see FM Presets table
  "fm_ratio": 1.0,             // Modulator ratio: 0.25–16
  "fm_index": 4.5,             // Modulation depth: 0–25
  "fm_brightness": 0.6,        // Decay speed: 0=sustained, 1=fast
  "fm_feedback": 0.02,         // Self-feedback: 0–1
  "fm_attack": 5,              // Attack in ms: 1–5000
  "fm_release": 500            // Release in ms: 10–10000
}
```

You can use just `fm_preset` and omit the rest — the preset provides all defaults.

---

## FM Presets

| Preset | Name | Best For |
|--------|------|----------|
| 0 | **Piano** | Acoustic piano, natural hammer sound |
| 1 | **E.Piano** | Electric piano (3-layer: body + tine + shimmer) |
| 2 | **Vibraphone** | Vibraphone with vibrato modulation |
| 3 | **Bell** | Bright bell/chime strikes |
| 4 | **Organ** | Sustained organ tone, minimal transient |
| 5 | **Pad** | Soft, warm, slow-attack pad |
| 6 | **Bass** | Punchy bass, low-register emphasis |
| 7 | **Brass** | Metallic brass, trumpet-like |

---

## Materials (14 Available)

| Key | Sound Character | Damping | Best For |
|-----|----------------|---------|----------|
| `steel` | Bright, sustained, clear | Very low | Strings, wires, sustained tones |
| `copper` | Warm, slightly muted | Low-medium | Warm strings, mellow tones |
| `bronze` | Rich, complex partials | Low-medium | Gongs, bells, cymbals |
| `aluminum` | Bright, dry, light | Very low | Crisp percussion, hi-hats |
| `brass` | Warm-bright metallic | Medium | Warm metallic sounds |
| `iron` | Dark, heavy | Medium | Anvils, heavy percussion |
| `glass` | Crystal-clear, pure | Extremely low | Bells, chimes, sonar pings |
| `wood_spruce` | Soft, warm | High | Gentle woody sounds |
| `wood_maple` | Rich, woody | Medium-high | Snare drums, marimba |
| `wood_birch` | Bright wood | Medium-high | Percussive wood |
| `wood_oak` | Dark, deep wood | High | Deep earth tones |
| `bamboo` | Bright, woody | Medium | Raindrops, wind chimes |
| `nylon` | Very dull, muted | Very high | Deep drones, bass |
| `rubber` | Thick, damped | High | Muted sounds, whale song |

**Rule of thumb:** Low damping = long sustain. High damping = quick decay.

---

## Exciters (21 Available)

| Exciter | Hardness | Best For |
|---------|----------|----------|
| `cotton` | Soft | Gentle touches, wind chimes |
| `cotton_mallet` | Soft | Soft mallet strikes |
| `felt` | Medium | Timpani, warm strikes |
| `felt_mallet` | Medium | Piano hammers, warm percussion |
| `finger` | Soft | Fingertip plucks |
| `finger_tap` | Soft | Light taps, raindrops |
| `bow` | Soft | Bowed strings (sustained) |
| `bow_slow` | Soft | Slow, deep bowing (drones) |
| `brush` | Soft | Brushed textures |
| `wood` | Medium-hard | Wooden stick strikes |
| `wood_mallet` | Medium-hard | Xylophone/marimba mallets |
| `hard_plastic` | Medium-hard | Crisp strikes |
| `rubber_mallet` | Medium-hard | Rubber mallet (warm but defined) |
| `medium` | Medium | General-purpose |
| `pluck` | Medium-hard | String plucks (guitar-like) |
| `metal` | Hard | Metal beater strikes |
| `metal_mallet` | Hard | Metal mallet, bright |
| `metal_hammer` | Hard | Heavy metal impact |
| `metal_tip` | Hard | Precise metallic ping |
| `metal_scrape` | Medium-hard | Scraping texture |
| `hard_strike` | Hard | Maximum attack, snare-like |
| `sharp` | Hard | Sharpest transient |

**Soft** exciters emphasize fundamentals. **Hard** exciters bring out overtones.

---

## Effects

All effects are in `global.effects` and apply to the entire score.

### Reverb
```json
"reverb": { "decay": 2.0, "wet": 0.3 }
```
| Field | Range | Default |
|-------|-------|---------|
| `decay` | 0–30 seconds | 2.0 |
| `wet` | 0–1 | 0.3 |

Small room: decay 0.5–1.5. Concert hall: 2–4. Cathedral: 5–8. Underwater: 10+.

### Delay
```json
"delay": { "time_ms": 300, "feedback": 0.3, "wet": 0.15 }
```
| Field | Range | Default |
|-------|-------|---------|
| `time_ms` | 0–5000 | 0 |
| `feedback` | 0–0.95 | 0 |
| `wet` | 0–1 | 0 |

Sync delay to tempo: `delay_ms = 60000 / bpm` (quarter note) or half/double.

### Distortion
```json
"distortion": { "type": "overdrive", "drive": 0.3, "instability": 0.1, "wet": 0.2 }
```
| Field | Values |
|-------|--------|
| `type` | `overdrive` / `bitcrush` / `wavefold` |
| `drive` | 0–1 (intensity) |
| `instability` | 0–1 (LFO wobble) |
| `wet` | 0–1 |

### Wall Reflection
```json
"wall": { "distance_m": 5, "material": "stone" }
```
Simulates sound bouncing off a wall. Materials: `stone`, `glass`, `metal`, `wood`, `fabric`.

---

## Timing — CRITICAL RULES

### 1. All Times Are Absolute Seconds

`time` and `duration` are in **seconds**, not beats or ticks. BPM is metadata only.

To convert from musical notation:
```
beat_duration = 60 / bpm
bar_duration  = beat_duration × beats_per_bar

Example: BPM 120, 4/4 time
  beat = 0.5 seconds
  bar  = 2.0 seconds
  beat 1 of bar 3 = 2 × 2.0 = 4.0 seconds
```

### 2. The 90% Note-Off Rule

**The renderer releases each note at 90% of its stated duration.**

```
actual_release = time + duration × 0.9
```

This means a note with `"duration": 1.0` actually sustains for 0.9 seconds, then the remaining 0.1 seconds is the natural decay tail.

**If you need a note to sustain exactly N seconds:**
```
duration = desired_sustain / 0.9
```

Example: need exactly 2 seconds of sustain → `"duration": 2.222`

### 3. Events Must Be Sorted by Time

The `events` array should be sorted by ascending `time`. Events at the same time are allowed (polyphony).

---

## Glide / Portamento

Slides the pitch from one note to another at the start of an event.

```json
{
  "time": 5.0,
  "duration": 3.0,
  "engine": "string",
  "note": "A4",
  "velocity": 0.6,
  "params": { "material": "rubber", "diameter_mm": 2.0, "exciter": "bow" },
  "glide": {
    "from_note": "E4",
    "duration_ms": 800,
    "curve": "exponential"
  }
}
```

| Field | Range | Note |
|-------|-------|------|
| `from_note` | note name or MIDI | Starting pitch |
| `duration_ms` | 1–5000 | How long the slide takes |
| `curve` | `linear` / `exponential` | Exponential sounds more natural |

The note starts at `from_note` and glides to `note` over `duration_ms`, then holds at `note` for the rest of the event.

---

## Export Settings

```json
"export": {
  "filename": "my_song",
  "format": "wav",
  "bit_depth": 24,
  "normalize": true,
  "tail_silence_ms": 500
}
```

| Field | Values | Default | Note |
|-------|--------|---------|------|
| `filename` | string | (required) | Output filename, no extension |
| `format` | `wav` / `flac` | `wav` | |
| `bit_depth` | 16 / 24 / 32 | 24 | |
| `normalize` | bool | true | Peak normalize to -3 dB |
| `tail_silence_ms` | 0–60000 | 300 | Silence after last note |

---

## Layers (Advanced)

Instead of `events`, you can composite multiple .score.json files:

```json
{
  "events": [],
  "layers": [
    { "source": "bell.score.json", "region": [0.0, 0.6], "gain": 1.0 },
    { "source": "drone.score.json", "region": [0.0, 1.0], "gain": 0.8 }
  ],
  "crossfade_ms": 80
}
```

`region` clips the source: `[0.0, 0.6]` = first 60% of the rendered audio.

---

## track_profiles (Optional, Documentation Only)

Name your instruments for readability. The renderer ignores this — it's for humans and AI reading the score.

```json
"track_profiles": {
  "melody": {
    "role": "melody",
    "label": "Steel violin",
    "engine": "string",
    "material": "steel",
    "exciter": "bow"
  },
  "bass": {
    "role": "bass",
    "label": "Copper bass",
    "engine": "string",
    "material": "copper",
    "exciter": "pluck"
  }
}
```

---

## Common Patterns & Recipes

### Drum Kit
```json
// Kick drum — large clamped plate
{"engine":"plate","note":"C2","params":{"material":"rubber","radius_mm":200,"thickness_mm":4,"plate_free_edge":false,"exciter":"felt_mallet"}}

// Snare — wood beam
{"engine":"beam","note":"E4","params":{"material":"wood_maple","thickness_mm":2,"length_mm":30,"width_mm":20,"exciter":"hard_strike"}}

// Hi-hat — small aluminum plate
{"engine":"plate","note":"F#5","params":{"material":"aluminum","thickness_mm":0.5,"radius_mm":30,"plate_free_edge":true,"exciter":"metal_tip"}}

// Cymbal crash — bronze plate
{"engine":"plate","note":"C5","params":{"material":"bronze","thickness_mm":1,"radius_mm":100,"plate_free_edge":true,"exciter":"metal_mallet"}}
```

### Bass Line (FM)
```json
{"engine":"fm","note":"E2","params":{"fm_preset":6}}
```

### Piano Chord (FM)
```json
{"engine":"fm","note":"C4","velocity":0.65,"params":{"fm_preset":0}},
{"engine":"fm","note":"E4","velocity":0.60,"params":{"fm_preset":0}},
{"engine":"fm","note":"G4","velocity":0.55,"params":{"fm_preset":0}}
```

### Bowed String Melody
```json
{"engine":"string","note":"A4","params":{"material":"steel","diameter_mm":0.55,"exciter":"bow","damping_override":0.4}}
```

### Deep Drone
```json
{"engine":"string","note":"C2","duration":15.0,"velocity":0.3,"params":{"material":"nylon","diameter_mm":3.0,"exciter":"bow_slow"}}
```

### Bell / Chime
```json
{"engine":"beam","note":"C6","params":{"material":"glass","thickness_mm":0.5,"length_mm":15,"width_mm":3,"exciter":"cotton"}}
```

### Gong Hit
```json
{"engine":"plate","note":"C3","params":{"material":"bronze","thickness_mm":3,"radius_mm":180,"plate_free_edge":true,"exciter":"felt_mallet"}}
```

### Whale Song (Glide)
```json
{
  "engine":"string","note":"A3","duration":4.0,"velocity":0.25,
  "params":{"material":"rubber","diameter_mm":2.0,"exciter":"bow"},
  "glide":{"from_note":"E3","duration_ms":1200,"curve":"exponential"}
}
```

---

## Composition Checklist

Before rendering, verify:

- [ ] All `time` values are in seconds, sorted ascending
- [ ] `sample_rate` is exactly 44100, 48000, 88200, or 96000
- [ ] `velocity` is 0–1 (not 0–127)
- [ ] `meta.id` matches `^[a-z0-9_]+$`
- [ ] Every event has all 5 required fields: `time`, `duration`, `engine`, `note`, `velocity`
- [ ] Physical dimensions are positive numbers within range
- [ ] `fm_preset` is 0–7 if using FM engine
- [ ] `export.filename` is set
- [ ] `bit_depth` is 16, 24, or 32
- [ ] The 90% rule is accounted for in timing-critical passages
- [ ] Events at the same time are intentional (chords/polyphony)

---

## Common Mistakes

| Mistake | Fix |
|---------|-----|
| Using beats instead of seconds | Convert: `time_sec = beat_number × (60 / bpm)` |
| velocity > 1 (using MIDI 0–127) | Scale to 0–1: `velocity = midi_velocity / 127` |
| Forgetting `params` for physical engines | Every physical engine needs at least `material` + dimensions |
| Omitting beam/plate dimensions | When a required dimension is omitted, the parser uses default values (e.g. length_mm=100, radius_mm=120). For reproducible physical verification, specify all dimensions explicitly. |
| Setting `sample_rate` to 22050 or other values | Only 44100 / 48000 / 88200 / 96000 are valid |
| Notes too short, no sound | Duration < 0.05 may be inaudible. 90% rule makes it even shorter. |
| All notes at same velocity | Vary velocity 0.4–0.9 for natural feel |
| No effects | Even minimal reverb (decay 1.5, wet 0.15) adds life |

---

## Rendering

### Single File
```
TsukiSynthCLI.exe score.score.json --output ./output
```

### Batch (All .score.json in a Directory)
```
TsukiSynthCLI.exe --batch ./scores --output ./output
```

Batch mode is non-recursive. It skips files whose WAV already exists in the output directory.

The CLI is at: `build/TsukiSynthCLI_artefacts/Release/TsukiSynthCLI.exe`

---

## Full Example — 8-Bar Pop Song

```json
{
  "$schema": "TsukiSynth Score v1",
  "meta": {
    "title": "Tiny Pop",
    "id": "tiny_pop",
    "author": "AI",
    "key": "C major",
    "mood": "playful"
  },
  "global": {
    "bpm": 120,
    "sample_rate": 48000,
    "master_volume": 0.85,
    "effects": {
      "reverb": { "decay": 1.8, "wet": 0.20 },
      "delay": { "time_ms": 250, "feedback": 0.15, "wet": 0.08 }
    }
  },
  "track_profiles": {
    "piano": { "label": "FM Piano", "engine": "fm", "role": "harmony" },
    "bass": { "label": "FM Bass", "engine": "fm", "role": "bass" },
    "snare": { "label": "Maple Snare", "engine": "beam", "role": "percussion" },
    "hihat": { "label": "Aluminum Hi-hat", "engine": "plate", "role": "percussion" }
  },
  "events": [
    {"time":0.0, "duration":1.8, "engine":"fm", "note":"C3", "velocity":0.70, "params":{"fm_preset":6}, "comment":"Bass — C"},
    {"time":0.0, "duration":1.8, "engine":"fm", "note":"C4", "velocity":0.55, "params":{"fm_preset":0}, "comment":"Piano chord C"},
    {"time":0.0, "duration":1.8, "engine":"fm", "note":"E4", "velocity":0.50, "params":{"fm_preset":0}},
    {"time":0.0, "duration":1.8, "engine":"fm", "note":"G4", "velocity":0.48, "params":{"fm_preset":0}},

    {"time":0.5, "duration":0.10,"engine":"beam","note":"E5", "velocity":0.50, "params":{"material":"wood_maple","thickness_mm":2,"length_mm":30,"width_mm":20,"exciter":"hard_strike"}, "comment":"Snare on beat 2"},
    {"time":0.5, "duration":0.08,"engine":"plate","note":"F#6","velocity":0.35, "params":{"material":"aluminum","thickness_mm":0.5,"radius_mm":30,"plate_free_edge":true,"exciter":"metal_tip"}, "comment":"Hi-hat"},

    {"time":1.0, "duration":0.08,"engine":"plate","note":"F#6","velocity":0.30, "params":{"material":"aluminum","thickness_mm":0.5,"radius_mm":30,"plate_free_edge":true,"exciter":"metal_tip"}},
    {"time":1.5, "duration":0.10,"engine":"beam","note":"E5", "velocity":0.52, "params":{"material":"wood_maple","thickness_mm":2,"length_mm":30,"width_mm":20,"exciter":"hard_strike"}},
    {"time":1.5, "duration":0.08,"engine":"plate","note":"F#6","velocity":0.35, "params":{"material":"aluminum","thickness_mm":0.5,"radius_mm":30,"plate_free_edge":true,"exciter":"metal_tip"}},

    {"time":2.0, "duration":1.8, "engine":"fm", "note":"F3", "velocity":0.68, "params":{"fm_preset":6}, "comment":"Bass — F"},
    {"time":2.0, "duration":1.8, "engine":"fm", "note":"F4", "velocity":0.55, "params":{"fm_preset":0}, "comment":"Piano chord F"},
    {"time":2.0, "duration":1.8, "engine":"fm", "note":"A4", "velocity":0.50, "params":{"fm_preset":0}},
    {"time":2.0, "duration":1.8, "engine":"fm", "note":"C5", "velocity":0.48, "params":{"fm_preset":0}},

    {"time":2.5, "duration":0.10,"engine":"beam","note":"E5", "velocity":0.50, "params":{"material":"wood_maple","thickness_mm":2,"length_mm":30,"width_mm":20,"exciter":"hard_strike"}},
    {"time":3.0, "duration":0.08,"engine":"plate","note":"F#6","velocity":0.30, "params":{"material":"aluminum","thickness_mm":0.5,"radius_mm":30,"plate_free_edge":true,"exciter":"metal_tip"}},
    {"time":3.5, "duration":0.10,"engine":"beam","note":"E5", "velocity":0.52, "params":{"material":"wood_maple","thickness_mm":2,"length_mm":30,"width_mm":20,"exciter":"hard_strike"}}
  ],
  "export": {
    "filename": "tiny_pop",
    "format": "wav",
    "bit_depth": 24,
    "normalize": true,
    "tail_silence_ms": 500
  }
}
```

---

## Design Philosophy

TsukiSynth exists so that **deaf people and AI** can create music through physics. You don't need to hear — you need to understand:

- A **thin steel string** plucked = bright guitar-like tone
- A **thick nylon string** bowed slowly = deep rumbling drone
- A **glass beam** tapped = crystal chime
- A **bronze plate** struck = gong
- **FM preset 0** = piano

Describe the physical world. The engine does the rest.
