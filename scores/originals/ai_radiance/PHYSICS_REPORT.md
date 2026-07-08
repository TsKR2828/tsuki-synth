# AI Radiance / 光之驗算 — Physics and Render Report

Generated and validated on 2026-06-22.

## Composition

| Item | Result |
|---|---:|
| Movements | 4 |
| Total duration | 98.529 s |
| Score events | 308 |
| Explicit rests | 248 |
| Phrase regions | 126 |
| MIDI range | 31–90 |
| Frequency range | 48.999–1479.978 Hz |

## Engine allocation

| Engine | Events | Function |
|---|---:|---|
| Cimbalom / yangqin | 136 | discrete attack, pulse, melodic memory |
| Tongue drum | 64 | non-harmonic beam decay and ethereal echo |
| FM | 48 | exact spectral body, beacon and pad |
| Custom harmonics | 36 | spectral flashes and final crown |
| Water gong | 24 | low-frequency horizon, pressure and glide |

## Material allocation

| Material | Events |
|---|---:|
| Steel | 144 |
| Glass | 70 |
| Bamboo | 16 |
| Bronze | 15 |
| Aluminum | 9 |
| Copper | 6 |

FM events do not use a physical material.

## Modal verification

The C++ `ScoreRenderer::dumpModes()` path was run on all four movement scores.

| Check | Result |
|---|---:|
| Modal events checked | 260 |
| Individual modes checked | 5,083 |
| Empty mode sets | 0 |
| NaN / infinite values | 0 |
| Frequencies ≤ 0 Hz | 0 |
| Frequencies > 20 kHz | 0 |
| Invalid decay constants | 0 |
| Maximum fundamental deviation | 5.002 cents |

The approximately five-cent maximum deviation is expected from the cimbalom engine's multi-string detuning and beating model.

The remaining 48 events use FM synthesis. Their carrier pitch is still derived exactly from:

```text
f = 440 × 2 ^ ((midi_note - 69) / 12)
```

## Render verification

| Output | Duration | Peak | RMS | Stereo correlation |
|---|---:|---:|---:|---:|
| Complete suite | 98.529 s | −0.446 dBFS | −21.085 dBFS | 0.97419 |
| Movement 1 | 28.364 s | −0.446 dBFS | −22.627 dBFS | 0.98979 |
| Movement 2 | 20.448 s | −0.446 dBFS | −16.342 dBFS | 0.97436 |
| Movement 3 | 24.970 s | −0.446 dBFS | −19.669 dBFS | 0.98200 |
| Movement 4 | 27.148 s | −0.446 dBFS | −19.624 dBFS | 0.97105 |

All files are stereo, 48 kHz, 24-bit WAV. No output reaches 0 dBFS.

## Timing verification

- Every event is sorted by absolute seconds.
- Every note includes MIDI number and target frequency.
- Renderer note-off compensation uses:

```text
event.duration = intended_sounding_duration / 0.9
```

- Every semantic voice has explicit rests and phrase regions.
- The complete suite concatenates four movement renders with 1.4-second crossfades.

## Creative premise

This work deliberately does not ask whether a patch resembles a familiar acoustic instrument.

It asks:

1. Which body owns the attack?
2. Which body owns the decay?
3. Which damping constant defines the phrase boundary?
4. Which non-harmonic modes may remain after the tonal event ends?

The resulting orchestration is therefore based on measurable transfer of energy between string, beam, plate and deterministic FM spectra.
