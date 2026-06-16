# TsukiSynth — TODO

> Last updated: 2026-06-16
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
| Free-edge gong option (`plate_free_edge`) | ✅ default off, A/B scores |

---

## Needs 月月 decision / ear

- [ ] **Plugin 4th "Piano" engine tab** — needs APVTS state-compat check first:
      confirm APVTS stores the `engine` choice **denormalized** (then appending
      "Piano" at index 3 is safe for old DAW projects). If normalized → old saved
      states would remap to the wrong engine. *Physical piano already shipped via
      Cimbalom preset + CLI `"piano"`; this is just the dedicated UI tab.*
- [ ] **Water gong character** — listen to clamped (default) vs free-edge
      (`scores/examples/water_gong_{clamped,free}.score.json`) and decide which.
- [ ] **In-plugin loudness balance** — FM vs modal engines at equal velocity
      (CLI is equal-RMS; confirm the plugin balance by ear if desired).

## Refinements (optional)

- [ ] Free-edge plate Ω values are approximate (Leissa ν≈0.33) — verify against a
      reference table before treating as precise.
- [ ] Advanced piano physics: hammer-felt nonlinearity, dedicated soundboard
      modes, damper pedal.
- [ ] `--t60` decay measurement is informational (audio decay fitting is noisy).

## Still pending from before

- [ ] DAW validation (host scan / automation / state round-trip) on a real DAW.
- [ ] `push` is done for `Codex-fix-bug`; decide merge → master when ready.

## Housekeeping

- Two dev logs coexist: `DEVLOG.md` (zh, current) + `DEV-LOG.md` (en) — converge one.
- `dsp/Reverb.h` / `dsp/EffectsChain.h` are CLI-side; `effects/*` are plugin-side
  (intentionally separate implementations).
