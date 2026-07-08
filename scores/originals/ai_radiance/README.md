# AI Radiance / 光之驗算

An original four-movement physical-synthesis suite composed by Codex for TsukiSynth.

The work treats engines as mathematical bodies rather than acoustic imitations:

1. **Dew Lattice** — cimbalom attacks interwoven with tongue-drum decay, grounded by free-edge bronze plates.
2. **Storm of Equations** — gliding water gongs against asymmetric metal-hammer bursts and custom harmonic flashes.
3. **Memory Orchard** — stable FM electric-piano spectra remembered imperfectly by cimbalom and bamboo beams.
4. **Crown at Absolute Zero** — glass tongue drums become a clock while steel strings, plates and pads dissolve into a spectral crown.

Every event includes:

- MIDI note and frequency
- intended physical release time
- renderer 90% note-off compensation
- semantic role and articulation
- explicit rests and phrase regions

See [`PHYSICS_REPORT.md`](PHYSICS_REPORT.md) for modal and WAV validation results.

Generate deterministically:

```powershell
python tools\compose_ai_radiance.py
```

Render all movements and the complete suite:

```powershell
build\TsukiSynthCLI_artefacts\Release\TsukiSynthCLI.exe `
  --batch scores\originals\ai_radiance `
  --output exports\wav\ai_radiance
```
