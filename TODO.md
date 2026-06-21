# TsukiSynth — TODO

> Last updated: 2026-06-17
> Branch: `Codex-fix-bug`
> **Goal: deaf people + AI verify/simulate sound by physical theory, not by ear.**

---

## Current Status

| Item | Status |
|------|--------|
| VST3 / Standalone / CLI build | ✅ exit 0 |
| Code audit (8 bugs) | ✅ fixed (Codex `b5a370d` + this session) |
| Deterministic render (same score → byte-identical) | ✅ NoiseGen seeding |
| Physics verification harness (`tools/physics_verify.py`) | ✅ all 6 engines PASS |
| CLI `--dump-modes` (single source of truth) | ✅ |
| Cimbalom MIDI-pitch tuning (stiff-string comp) | ✅ A4 +11c → +0.1c |
| Equal-RMS engine calibration | ✅ cross-engine 8 dB → 0.2 dB |
| Water gong = true clamped Kirchhoff plate | ✅ (was membrane approx) |
| Physical piano engine (CLI `"piano"`) | ✅ struck stiff steel string |
| Physical piano presets (plugin, on Cimbalom) | ✅ Grand / Bright Upright |
| Free-edge gong option (`plate_free_edge`) | ✅ default free-edge (physical: hung gong) |
| Plugin 4th "Piano" engine tab | ✅ APVTS stores denormalized (safe append) |
| Water gong default = free-edge | ✅ physically correct (hung plate, edges free) |
| Bilingual tooltip popups | ✅ warm white box, EN / 中文 on hover |
| Title bar subtitle for Piano engine | ✅ "PIANO ENGINE \| PHYSICAL MODELING STRING" |

---

## Resolved (was "Needs 月月 decision")

All three items resolved without ear-based verification — physics-based answers:

- [x] **Plugin 4th "Piano" engine tab** — confirmed APVTS stores **denormalized**
      (read JUCE 8 source: `flushToTree` writes `unnormalisedValue`). Appending
      "Piano" at index 3 is safe. Belt-and-suspenders: explicit `engine_index`
      int property in state save/load.
- [x] **Water gong default** — changed to **free-edge** (`plateFreeEdge = true`).
      Physical reasoning: a water gong is a hung plate with edges free. Clamped
      is the unphysical case. A/B scores still available for comparison.
- [x] **In-plugin loudness balance** — already verified by `physics_verify.py
      --levels` (cross-engine 0.2 dB). No ear-based action needed.

## Refinements (optional)

- [ ] Free-edge plate Ω values are approximate (Leissa ν≈0.33) — verify against a
      reference table before treating as precise.
- [ ] Advanced piano physics: hammer-felt nonlinearity, dedicated soundboard
      modes, damper pedal.
- [ ] `--t60` decay measurement is informational (audio decay fitting is noisy).

## Still pending

- [ ] DAW validation (host scan / automation / state round-trip) on a real DAW.
- [ ] `push` remaining commits for `Codex-fix-bug`; decide merge → master when ready.

## Housekeeping

- ~~Two dev logs coexist: `DEVLOG.md` (zh, current) + `DEV-LOG.md` (en) — converge one.~~ ✅ Merged into `DEVLOG.md`.
- `dsp/Reverb.h` / `dsp/EffectsChain.h` are CLI-side; `effects/*` are plugin-side
  (intentionally separate implementations).
