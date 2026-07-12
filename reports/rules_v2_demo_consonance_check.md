# Consonance Compliance Check

Score: `scores\originals\rules_v2_demo\rules_v2_demo_001.score.json`

Method: every pair of events (across engines or within one engine) whose `[time, time+duration)` windows overlap is checked -- pitch-class interval (mod 1200 cents, octave-equivalence assumption) vs the nearest local minimum in the matching Sethares dissonance-curve table (tools/consonance.py, ROADMAP_PHYSICS.md M9-9a). PASS = within 10 cents of a registered minimum (same window tools/consonance.py itself uses for its 'recommended interval' definition). This checks the SCORE's declared sounding windows, not resonance ringing past note-off -- a note whose physical decay outlasts its declared `duration` may still overlap perceptually with the next note; that is a known scope limit, not silently assumed away.

**Summary: 13 simultaneous pairs checked — 13 PASS, 0 VIOLATION, 0 UNVALIDATED-DIRECTION.**

| lo event | lo engine/role | hi event | hi engine/role | cents (mod 1200) | table | nearest min | dist | verdict |
|---:|---|---:|---|---:|---|---:|---:|---|
| 0 (MIDI 55) | cimbalom/A_arrival | 1 (MIDI 62) | tongue_drum/A_mark | 700.0 | cimbalom->tongue_drum cross | 690 | 10.0 | PASS |
| 0 (MIDI 55) | cimbalom/A_arrival | 2 (MIDI 67) | water_gong/A_mark | 0.0 | cimbalom->water_gong cross | 0 | 0.0 | PASS |
| 22 (MIDI 55) | cimbalom/A2_arrival | 23 (MIDI 62) | tongue_drum/A2_mark | 700.0 | cimbalom->tongue_drum cross | 690 | 10.0 | PASS |
| 22 (MIDI 55) | cimbalom/A2_arrival | 24 (MIDI 67) | water_gong/A2_mark | 0.0 | cimbalom->water_gong cross | 0 | 0.0 | PASS |
| 44 (MIDI 60) | cimbalom/B_arrival | 45 (MIDI 67) | tongue_drum/B_mark | 700.0 | cimbalom->tongue_drum cross | 690 | 10.0 | PASS |
| 44 (MIDI 60) | cimbalom/B_arrival | 46 (MIDI 72) | water_gong/B_mark | 0.0 | cimbalom->water_gong cross | 0 | 0.0 | PASS |
| 57 (MIDI 60) | cimbalom/B_echo | 58 (MIDI 67) | tongue_drum/B_echo_mark | 700.0 | cimbalom->tongue_drum cross | 690 | 10.0 | PASS |
| 57 (MIDI 60) | cimbalom/B_echo | 59 (MIDI 72) | water_gong/B_echo_mark | 0.0 | cimbalom->water_gong cross | 0 | 0.0 | PASS |
| 73 (MIDI 55) | cimbalom/A3_arrival | 74 (MIDI 62) | tongue_drum/A3_mark | 700.0 | cimbalom->tongue_drum cross | 690 | 10.0 | PASS |
| 73 (MIDI 55) | cimbalom/A3_arrival | 75 (MIDI 67) | water_gong/A3_mark | 0.0 | cimbalom->water_gong cross | 0 | 0.0 | PASS |
| 73 (MIDI 55) | cimbalom/A3_arrival | 76 (MIDI 55) | cimbalom/A3_arpeggio | 0.0 | cimbalom self | 0 | 0.0 | PASS |
| 95 (MIDI 55) | cimbalom/final_cadence | 96 (MIDI 62) | tongue_drum/final_mark | 700.0 | cimbalom->tongue_drum cross | 690 | 10.0 | PASS |
| 95 (MIDI 55) | cimbalom/final_cadence | 97 (MIDI 67) | water_gong/final_mark | 0.0 | cimbalom->water_gong cross | 0 | 0.0 | PASS |
