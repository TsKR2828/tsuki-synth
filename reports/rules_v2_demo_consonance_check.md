# Consonance Compliance Check

Score: `scores\originals\rules_v2_demo\rules_v2_demo_001.score.json`

Score SHA256: `c59cb720510289d706d84ecdcf28d741e335451560b0d70e6f83f471b48f0006`

Checker SHA256: `810a3ac87a5dc2db5e467e05ec9484697fc92b38dccb244d4973cdad48a5d81a`

Sethares implementation SHA256: `a4f13d06faa0b1d0f6ad9f4e7b679fa0e14e1bb5faed8cc430aed74c4733e516`

CLI: `C:\Users\admin\Desktop\Claude\tsuki-synth\build\TsukiSynthCLI_artefacts\Release\TsukiSynthCLI.exe`

CLI SHA256: `f87037d6fcb8bd14e7037b8c62848ff8c0e16c4684e1da8c57f42f31a6f1845f`

Method: every pair of events (across engines or within one engine) whose `[time, time+duration)` windows overlap is checked -- pitch-class interval (mod 1200 cents, octave-equivalence assumption) vs the nearest local minimum in an event-specific Sethares roughness curve built from this score's real C++ `--dump-modes` spectra (all active strings, material, geometry, boundary, strike and velocity-dependent hammer spectrum; tools/consonance.py formula, ROADMAP_PHYSICS.md M9-9a). PASS = within 10 cents of a local minimum. FM and Custom Harmonics are explicitly UNVERIFIED-DOMAIN. This checks the SCORE's declared sounding windows, not resonance ringing past note-off -- a note whose physical decay outlasts its declared `duration` may still overlap perceptually with the next note; that is a known scope limit, not silently assumed away.

**Summary: 13 simultaneous pairs checked — 13 PASS, 0 VIOLATION, 0 UNVERIFIED.**

| lo event | lo engine/role | hi event | hi engine/role | cents (mod 1200) | table | nearest min | dist | verdict |
|---:|---|---:|---|---:|---|---:|---:|---|
| 0 (MIDI 55) | cimbalom/A_arrival | 1 (MIDI 57) | tongue_drum/A_mark | 200.0 | event-specific cimbalom->tongue_drum/cantilever | 200 | 0.0 | PASS |
| 0 (MIDI 55) | cimbalom/A_arrival | 2 (MIDI 67) | water_gong/A_mark | 1200.0 | event-specific cimbalom->water_gong/clamped | 1200 | 0.0 | PASS |
| 22 (MIDI 55) | cimbalom/A2_arrival | 23 (MIDI 57) | tongue_drum/A2_mark | 200.0 | event-specific cimbalom->tongue_drum/cantilever | 200 | 0.0 | PASS |
| 22 (MIDI 55) | cimbalom/A2_arrival | 24 (MIDI 67) | water_gong/A2_mark | 1200.0 | event-specific cimbalom->water_gong/clamped | 1200 | 0.0 | PASS |
| 44 (MIDI 60) | cimbalom/B_arrival | 45 (MIDI 67) | tongue_drum/B_mark | 700.0 | event-specific cimbalom->tongue_drum/cantilever | 705 | 5.0 | PASS |
| 44 (MIDI 60) | cimbalom/B_arrival | 46 (MIDI 72) | water_gong/B_mark | 1200.0 | event-specific cimbalom->water_gong/clamped | 0 | 0.0 | PASS |
| 57 (MIDI 60) | cimbalom/B_echo | 58 (MIDI 67) | tongue_drum/B_echo_mark | 700.0 | event-specific cimbalom->tongue_drum/cantilever | 700 | 0.0 | PASS |
| 57 (MIDI 60) | cimbalom/B_echo | 59 (MIDI 72) | water_gong/B_echo_mark | 1200.0 | event-specific cimbalom->water_gong/clamped | 0 | 0.0 | PASS |
| 73 (MIDI 55) | cimbalom/A3_arrival | 74 (MIDI 57) | tongue_drum/A3_mark | 200.0 | event-specific cimbalom->tongue_drum/cantilever | 200 | 0.0 | PASS |
| 73 (MIDI 55) | cimbalom/A3_arrival | 75 (MIDI 67) | water_gong/A3_mark | 1200.0 | event-specific cimbalom->water_gong/clamped | 0 | 0.0 | PASS |
| 73 (MIDI 55) | cimbalom/A3_arrival | 76 (MIDI 55) | cimbalom/A3_arpeggio | 0.0 | event-specific cimbalom->cimbalom | 0 | 0.0 | PASS |
| 95 (MIDI 55) | cimbalom/final_cadence | 96 (MIDI 57) | tongue_drum/final_mark | 200.0 | event-specific cimbalom->tongue_drum/cantilever | 200 | 0.0 | PASS |
| 95 (MIDI 55) | cimbalom/final_cadence | 97 (MIDI 67) | water_gong/final_mark | 1200.0 | event-specific cimbalom->water_gong/clamped | 0 | 0.0 | PASS |
