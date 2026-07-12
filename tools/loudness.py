#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
loudness.py -- ITU-R BS.1770-4 integrated loudness (LUFS) measurement.

ROADMAP_PHYSICS.md Milestone M6-6c: "verify_score.py 報告加整曲 LUFS
(integrated) 與逐樂句 RMS，讓響度成為可讀數字。"

This module is deliberately import-free of verify_score.py AND
report_html.py (same reasoning as report_html.py's own module docstring:
verify_score.py imports report_html.py, so anything both of them need has
to live in a third, standalone module to avoid a circular import). Both
files import THIS module.

INFORMATIONAL ONLY -- ROADMAP_PHYSICS.md Sec.6 (容差登記表) does not
register a LUFS tolerance ("待 M2 實測後檢討" pattern was used for other
rows, but LUFS was never given a target value at all), so nothing computed
here feeds a pass/fail Check anywhere. verify_score.py prints it as a plain
info line; report_html.py prints it in the banner-stats line and the
per-phrase RMS numbers on the phrases timeline. Do not invent a tolerance
for it (task instruction: "no tolerance exists for LUFS in Sec.6, do not
invent one").

── K-weighting filter design (cited) ───────────────────────────────────────
ITU-R BS.1770-4 (10/2015), Annex 1, "Filter definitions" (also reproduced,
with the same parametrisation, in EBU Tech 3341 and in widely-used
open-source loudness meters such as pyloudnorm and ffmpeg's `ebur128`
filter): K-weighting is the cascade of

  * Stage 1 -- a high-frequency shelf (models the acoustic effect of an
    average human head), analogue-prototype parameters f0, gain G, Q.
  * Stage 2 -- the "RLB" (Revised Low-frequency B-weighting) high-pass,
    analogue-prototype parameters f0, Q (0 dB gain).

The Annex gives these analogue-prototype parameters plus a bilinear-
transform recipe that turns them into digital biquad coefficients AT ANY
SAMPLE RATE. We implement that general recipe (so this works whether
TsukiSynthCLI renders at 44100/48000/96000 Hz -- ScoreParser.h's
ScoreGlobal::sampleRate defaults to 48000, see src/score/ScoreParser.h)
rather than hardcoding only the specific 48 kHz numbers the standard
happens to publish as a worked example. _BS1770_48K_STAGE{1,2} below are
those literal published 48 kHz numbers, quoted directly from Annex 1 Table
1, kept ONLY as a citation / cross-check target -- see the self-test at
the bottom of this file, which confirms the general formula reproduces
them to ~9 significant digits at fs=48000.
"""

import math

import numpy as np
from scipy.signal import lfilter

# ── K-weighting analogue-prototype parameters (ITU-R BS.1770-4 Annex 1) ────
_STAGE1_F0 = 1681.9744509555319   # Hz -- high-frequency shelf centre freq
_STAGE1_G = 3.99984385397         # dB -- shelf gain
_STAGE1_Q = 0.7071752369554193

_STAGE2_F0 = 38.13547087613982    # Hz -- RLB high-pass centre freq
_STAGE2_Q = 0.5003270373238773

# Literal 48 kHz coefficients published in ITU-R BS.1770-4 Annex 1 Table 1
# (quoted directly from the standard) -- citation / self-test target only,
# never used at runtime (see module docstring).
_BS1770_48K_STAGE1 = dict(b0=1.53512485958697, b1=-2.69169618940638,
                          b2=1.19839281085285, a1=-1.69065929318241,
                          a2=0.73248077421585)
_BS1770_48K_STAGE2 = dict(b0=1.0, b1=-2.0, b2=1.0,
                          a1=-1.99004745483398, a2=0.99007225036621)

# ── block-based measurement constants (ITU-R BS.1770-4 Sec.5 / Annex 1) ────
BLOCK_S = 0.400          # 400 ms measurement blocks (task 6c)
OVERLAP = 0.75           # 75% overlap -> 100 ms hop
ABS_GATE_LUFS = -70.0    # absolute gate (task 6c)
REL_GATE_LU = -10.0      # relative gate, applied after absolute gating


def _stage1_coeffs(sr):
    """High-frequency shelf biquad at sample rate `sr` (bilinear transform
    of the analogue prototype f0/G/Q above -- ITU-R BS.1770-4 Annex 1)."""
    f0, G, Q = _STAGE1_F0, _STAGE1_G, _STAGE1_Q
    K = math.tan(math.pi * f0 / sr)
    Vh = 10.0 ** (G / 20.0)
    Vb = Vh ** 0.499666774155
    a0 = 1.0 + K / Q + K * K
    b0 = (Vh + Vb * K / Q + K * K) / a0
    b1 = 2.0 * (K * K - Vh) / a0
    b2 = (Vh - Vb * K / Q + K * K) / a0
    a1 = 2.0 * (K * K - 1.0) / a0
    a2 = (1.0 - K / Q + K * K) / a0
    return b0, b1, b2, a1, a2


def _stage2_coeffs(sr):
    """RLB high-pass biquad at sample rate `sr` (bilinear transform of the
    analogue prototype f0/Q above -- ITU-R BS.1770-4 Annex 1)."""
    f0, Q = _STAGE2_F0, _STAGE2_Q
    K = math.tan(math.pi * f0 / sr)
    a0 = 1.0 + K / Q + K * K
    b0 = 1.0
    b1 = -2.0
    b2 = 1.0
    a1 = 2.0 * (K * K - 1.0) / a0
    a2 = (1.0 - K / Q + K * K) / a0
    return b0, b1, b2, a1, a2


def k_weighting_coeffs(sr):
    """Returns (stage1, stage2), each a (b0, b1, b2, a1, a2) tuple, at
    sample rate `sr` (Hz)."""
    return _stage1_coeffs(sr), _stage2_coeffs(sr)


def apply_k_weighting(mono, sr):
    """Applies the two-stage K-weighting filter (ITU-R BS.1770-4 Annex 1)
    to a mono float array. This is a CAUSAL IIR cascade (matches the
    standard's own block diagram) -- deliberately NOT zero-phase. This is
    unlike the T60 decay-envelope measurement elsewhere in this repo
    (tools/physics_verify.py's measure_t60(), which uses zero-phase
    sosfiltfilt for an unbiased envelope shape); loudness is defined by the
    standard on the causally-filtered signal, phase response included."""
    (b0_1, b1_1, b2_1, a1_1, a2_1), (b0_2, b1_2, b2_2, a1_2, a2_2) = k_weighting_coeffs(sr)
    stage1 = lfilter([b0_1, b1_1, b2_1], [1.0, a1_1, a2_1], mono)
    stage2 = lfilter([b0_2, b1_2, b2_2], [1.0, a1_2, a2_2], stage1)
    return stage2


def _block_mean_squares(weighted, sr, block_s=BLOCK_S, overlap=OVERLAP):
    """Mean square per 400 ms block, hopped at 100 ms (75% overlap). Returns
    an empty array if the signal is shorter than one block."""
    hop_s = block_s * (1.0 - overlap)
    block_n = int(round(block_s * sr))
    hop_n = max(1, int(round(hop_s * sr)))
    if block_n <= 0 or len(weighted) < block_n:
        return np.array([])
    n_blocks = 1 + (len(weighted) - block_n) // hop_n
    zs = np.empty(n_blocks, dtype=np.float64)
    w = weighted.astype(np.float64)
    for i in range(n_blocks):
        s = i * hop_n
        seg = w[s:s + block_n]
        zs[i] = np.mean(seg ** 2)
    return zs


def _loudness_from_z(z):
    """L = -0.691 + 10*log10(z) -- ITU-R BS.1770-4 Eq.(2)/(4), single
    channel (channel weighting G_i = 1.0 for the mono signals this repo
    measures; verify_score.py/report_html.py both already mix down to mono
    via read_wav_mono() before calling this)."""
    if z <= 0.0:
        return float("-inf")
    return -0.691 + 10.0 * math.log10(z)


def integrated_lufs(mono, sr):
    """Whole-signal integrated loudness (LUFS), ITU-R BS.1770-4: K-weight,
    split into 400ms/75%-overlap blocks, absolute-gate at -70 LUFS, then
    relative-gate at (that gated mean - 10 LU). Returns None if the signal
    is shorter than one block, or if every block is gated out (e.g. total
    silence) -- callers must treat None as "not measurable", never as 0 or
    -inf LUFS."""
    if mono is None or sr is None or len(mono) < int(round(BLOCK_S * sr)):
        return None
    weighted = apply_k_weighting(np.asarray(mono, dtype=np.float64), sr)
    zs = _block_mean_squares(weighted, sr)
    if zs.size == 0:
        return None

    abs_gate_z = 10.0 ** ((ABS_GATE_LUFS + 0.691) / 10.0)
    kept_abs = zs[zs > abs_gate_z]
    if kept_abs.size == 0:
        return None
    gamma_abs = _loudness_from_z(float(np.mean(kept_abs)))

    rel_threshold_lufs = gamma_abs + REL_GATE_LU
    rel_gate_z = 10.0 ** ((rel_threshold_lufs + 0.691) / 10.0)
    kept_rel = kept_abs[kept_abs > rel_gate_z]
    if kept_rel.size == 0:
        return None
    return _loudness_from_z(float(np.mean(kept_rel)))


def resolve_phrase_segments(score, events):
    """Returns a list of segment dicts {start, end, track, label, source}
    for "per-phrase RMS" (task 6c): one segment per entry in the score's
    "phrases" array when present (source="phrase"), otherwise the merged
    event-activity timeline (source="activity") -- the same fallback
    report_html.py's phrase/rest section (render_phrases_section) already
    draws when a score has no "phrases" field, so the RMS numbers line up
    with what the HTML timeline actually shows."""
    phrases = (score or {}).get("phrases")
    if phrases:
        out = []
        for p in phrases:
            if not isinstance(p, dict):
                continue
            start, end = p.get("start"), p.get("end")
            if start is None or end is None:
                continue
            out.append({
                "start": float(start), "end": float(end),
                "track": p.get("track") or p.get("role") or "?",
                "label": f"phrase #{p.get('number', '?')}",
                "source": "phrase",
            })
        if out:
            return out

    spans = []
    for ev in (events or []):
        if not isinstance(ev, dict):
            continue
        t, d = ev.get("time"), ev.get("duration")
        if t is None or d is None:
            continue
        spans.append((float(t), float(t) + max(float(d), 0.0)))
    spans.sort()
    merged = []
    for s, e in spans:
        if merged and s <= merged[-1][1]:
            merged[-1] = (merged[-1][0], max(merged[-1][1], e))
        else:
            merged.append((s, e))
    return [{"start": s, "end": e, "track": "events",
             "label": f"segment {i + 1}", "source": "activity"}
            for i, (s, e) in enumerate(merged)]


def compute_segment_rms_table(score, events, mono, sr):
    """resolve_phrase_segments() with an "rms_dbfs" key attached to each
    segment (task 6c "Per-phrase RMS: RMS dBFS over each phrase span (or
    over merged activity segments when no phrases)")."""
    segs = resolve_phrase_segments(score, events)
    out = []
    for seg in segs:
        rms = segment_rms_dbfs(mono, sr, seg["start"], seg["end"])
        out.append({**seg, "rms_dbfs": rms})
    return out


def segment_rms_dbfs(mono, sr, start_s, end_s):
    """Plain (non-K-weighted) RMS in dBFS over [start_s, end_s) of `mono`
    -- used for the "per-phrase RMS" numbers (task 6c), which the task
    brief specifies as plain RMS dBFS, not LUFS (LUFS is the whole-file
    figure; per-phrase is a simpler, faster-to-read loudness-over-time
    number). Returns None if the window is empty/out of range."""
    if mono is None or sr is None:
        return None
    n = len(mono)
    start_i = max(0, int(round(start_s * sr)))
    end_i = min(n, int(round(end_s * sr)))
    if end_i <= start_i:
        return None
    seg = mono[start_i:end_i].astype(np.float64)
    if seg.size == 0:
        return None
    rms = float(np.sqrt(np.mean(seg ** 2)))
    return 20.0 * math.log10(rms) if rms > 1e-12 else -120.0


# ── self-test (task 6c, mandatory) ──────────────────────────────────────────
def _selftest():
    """A 997 Hz full-scale sine must measure -3.01 LUFS +/- 0.1 (a
    well-known BS.1770 property: full-scale RMS is -3.01 dBFS by
    peak-to-RMS ratio of a sine, sqrt(2), and K-weighting is close to unity
    gain at 997 Hz), and a -18 dBFS 997 Hz sine -> -21.01 LUFS +/- 0.1
    (same signal, 18 dB quieter, purely additive since the meter is
    linear in level). Also cross-checks the general biquad-coefficient
    formula against the literal 48 kHz coefficients ITU-R BS.1770-4 Annex 1
    Table 1 publishes. Returns a dict of the actual measured numbers (never
    silently rounds/fudges -- see ROADMAP_PHYSICS.md Rule 2)."""
    sr = 48000
    dur_s = 5.0
    t = np.arange(int(dur_s * sr)) / sr
    sine_fs = np.sin(2.0 * np.pi * 997.0 * t)  # full-scale (peak = 1.0)
    sine_m18 = sine_fs * (10.0 ** (-18.0 / 20.0))

    lufs_fs = integrated_lufs(sine_fs, sr)
    lufs_m18 = integrated_lufs(sine_m18, sr)

    s1 = _stage1_coeffs(sr)
    s2 = _stage2_coeffs(sr)
    s1_pub = (_BS1770_48K_STAGE1["b0"], _BS1770_48K_STAGE1["b1"], _BS1770_48K_STAGE1["b2"],
              _BS1770_48K_STAGE1["a1"], _BS1770_48K_STAGE1["a2"])
    s2_pub = (_BS1770_48K_STAGE2["b0"], _BS1770_48K_STAGE2["b1"], _BS1770_48K_STAGE2["b2"],
              _BS1770_48K_STAGE2["a1"], _BS1770_48K_STAGE2["a2"])
    stage1_max_err = max(abs(a - b) for a, b in zip(s1, s1_pub))
    stage2_max_err = max(abs(a - b) for a, b in zip(s2, s2_pub))

    ok = (lufs_fs is not None and abs(lufs_fs - (-3.01)) <= 0.1
          and lufs_m18 is not None and abs(lufs_m18 - (-21.01)) <= 0.1
          and stage1_max_err < 1e-6 and stage2_max_err < 1e-6)

    return {
        "ok": ok,
        "lufs_997hz_fullscale": lufs_fs,
        "lufs_997hz_minus18dbfs": lufs_m18,
        "stage1_coeff_max_abs_err_vs_published_48k": stage1_max_err,
        "stage2_coeff_max_abs_err_vs_published_48k": stage2_max_err,
    }


if __name__ == "__main__":
    import sys
    result = _selftest()
    print("LUFS self-test (ITU-R BS.1770-4):")
    print(f"  997 Hz full-scale sine   : {result['lufs_997hz_fullscale']:.4f} LUFS "
          f"(target -3.01 +/- 0.1)")
    print(f"  997 Hz sine @ -18 dBFS   : {result['lufs_997hz_minus18dbfs']:.4f} LUFS "
          f"(target -21.01 +/- 0.1)")
    print(f"  stage1 coeff max abs err vs published 48kHz table: "
          f"{result['stage1_coeff_max_abs_err_vs_published_48k']:.3e}")
    print(f"  stage2 coeff max abs err vs published 48kHz table: "
          f"{result['stage2_coeff_max_abs_err_vs_published_48k']:.3e}")
    print(f"RESULT: {'PASS' if result['ok'] else 'FAIL'}")
    sys.exit(0 if result["ok"] else 1)
