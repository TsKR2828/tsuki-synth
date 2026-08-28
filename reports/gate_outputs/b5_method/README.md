# B5 baseline: bit-exact sampling of wood_* scores (pre-work)

Captured at HEAD=`53e6c76` (branch `fix/deep-physics-audit-20260716`), working
tree clean, **before** any B5 code changes. Purpose: freeze the exact WAV
bytes for every corpus score that touches a `wood_` field, so B5's damping
work can be checked for bit-exact-or-not against this baseline.

## Discrepancy vs. the original task wording -- flagged, not silently fixed

The task asked for the clean-list to include "at least one wood_spruce
tongue_drum or water_gong piece." That constraint **cannot be satisfied**
from the actual repo contents at this commit:

- `grep -rl "wood_" scores/ --include="*.score.json"` matches 13 files (listed
  below), but every one of those hits is either the resonator `"material"`
  field (`wood_oak`, `wood_birch`, `wood_maple`, or the literal `"wood"` used
  once in `akashic_opening_bell_001.score.json`, which the plain-`wood_`
  grep pattern does NOT match and so isn't in the 13) or the exciter field
  `"exciter": "wood_mallet"` (mallet material, not resonator material --
  `wood_mallet` is not even a key in `data/materials.json`).
- `grep -rl "wood_spruce" scores/ --include="*.score.json"` returns **zero**
  files. `wood_spruce` is a defined material in `data/materials.json` but no
  score under `scores/` currently uses it as a resonator material.
- `grep -rl "tongue_drum\|water_gong" scores/ --include="*.score.json"` finds
  10 files, but none of them use a `wood_*` material -- the tongue_drum
  pieces use `aluminum`/`steel`, the water_gong pieces use `bronze`.

So there is no file in the repo, at this commit, that is simultaneously (a)
matched by the `wood_` grep and (b) a tongue_drum/water_gong piece using
`wood_spruce`. Rather than substitute a piece that doesn't actually meet the
stated constraint and call it compliant, this baseline renders **all 13**
files the `wood_` grep actually found (the list has >8 entries, so per the
task's own fallback rule "if the list has more than 8, rendering all is
better" -- this also removes the "pick which 4" ambiguity). If a
wood_spruce/tongue_drum-or-water_gong sample is specifically needed, it does
not exist yet and a new score would have to be authored first.

## Piece list (13 files -- full result of the grep, verified at HEAD=53e6c76)

| # | score path | wood_ field(s) found |
|---|---|---|
| 1 | `scores/examples/moonlight_sonata_movement1_yangqin.score.json` | exciter `wood_mallet` |
| 2 | `scores/examples/moonlight_sonata_movement1_yangqin_tongue_mix.score.json` | exciter `wood_mallet` |
| 3 | `scores/library/akashic/akashic_notify_001.score.json` | exciter `wood_mallet` |
| 4 | `scores/library/forest/forest_action_001.score.json` | material `wood_oak` |
| 5 | `scores/library/forest/forest_notify_001.score.json` | exciter `wood_mallet` |
| 6 | `scores/library/forest/forest_transition_001.score.json` | material `wood_birch` |
| 7 | `scores/library/forest/forest_ui_001.score.json` | material `wood_oak` + exciter `wood_mallet` |
| 8 | `scores/library/rabbit/rabbit_notify_001.score.json` | exciter `wood_mallet` |
| 9 | `scores/library/rabbit/rabbit_ui_001.score.json` | material `wood_maple` + exciter `wood_mallet` |
| 10 | `scores/originals/ai_radiance/ai_radiance_m1.score.json` | exciter `wood_mallet` |
| 11 | `scores/originals/rules_v2_demo/rules_v2_demo_001.score.json` | exciter `wood_mallet` |
| 12 | `scores/tests/melody_sentinel.score.json` | exciter `wood_mallet` |
| 13 | `scores/tests/test_glide.score.json` | exciter `wood_mallet` |

## How to rerun

From the repo root, with the three test targets already built (per X4
regulation; not needed for this script itself, only the CLI target is
required):

```bash
python reports/gate_outputs/b5_method/render_wood_scores.py --label before --workdir "$TEMP/b5_render_before"
python reports/gate_outputs/b5_method/render_wood_scores.py --label after  --workdir "$TEMP/b5_render_after"
```

- `--workdir` MUST be outside the repo (the script refuses otherwise).
- Each run renders all 13 pieces via
  `build/TsukiSynthCLI_artefacts/Release/TsukiSynthCLI.exe <score> --output <piece_dir>`
  (same invocation shape as `reports/gate_outputs/b4_method/render_affected_pieces.py`).
- Outputs land in this directory: `render_<label>.csv` (piece, score_path,
  wav filename, length_s, RMS dBFS, spectral centroid Hz, sha256) and
  `sha256_<label>.txt` (one line per WAV: `<sha256>  <piece>/<wavname>`,
  sorted in the same order as `PIECES` in the script).
- To check bit-exactness after a B5 change, diff the two sha256 files:
  `diff reports/gate_outputs/b5_method/sha256_before.txt reports/gate_outputs/b5_method/sha256_after.txt`.
  Any line that differs is a piece whose rendered WAV bytes changed.

## Files in this directory

- `render_wood_scores.py` -- the render/hash script (rerunnable with
  `--label before|after`).
- `sha256_before.txt` -- SHA256 of all 13 baseline WAVs, captured at
  HEAD=53e6c76 (this commit, working tree clean, pre-B5).
- `render_before.csv` -- same 13 rows plus length/RMS/centroid, for
  human-readable sanity context (SHA256 column is authoritative for
  bit-exactness; RMS/centroid are informational only).
- `README.md` -- this file.
