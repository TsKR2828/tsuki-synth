#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tools/consonance.py — M9-9a/9b: ear-free consonance + duration rules for
TsukiSynth's modal (inharmonic) engines.

This is a PURE-COMPUTATION harness (like physics_verify.py): every number in
its report is derived from the model's own --dump-modes partial spectrum
(freq / amp / decay / body_mag — the SAME theory-only fields that M2's
windowed-synthesis amplitude gate already validated against rendered audio to
+/-3.0 dB, ROADMAP_PHYSICS.md §6) run through a published psychoacoustic
formula (Sethares 1993). Nothing here is fit or tuned by listening
(ROADMAP_PHYSICS.md §0 "驗收哲學" — no-circularity rule).

── 9a: Sethares dissonance-curve method ────────────────────────────────────
Source: W.A. Sethares, "Local consonance and the relationship between timbre
and scale", J. Acoust. Soc. Am. 94(3), 1993, and the same closed-form curve
as republished on the author's reference page (sethares.engr.wisc.edu/
consemi.html). Pairwise roughness of two partials (f1,a1) and (f2,a2):

    fmin  = min(f1, f2)
    fdif  = |f2 - f1|
    amin  = min(a1, a2)
    s     = d* / (s1 * fmin + s2)
    d(f1,f2,a1,a2) = amin * ( exp(-b1*s*fdif) - exp(-b2*s*fdif) )

Fitted constants (Sethares 1993, cited above — NOT re-derived or tuned here):
    d*  = 0.24
    s1  = 0.0207
    s2  = 18.96
    b1  = 3.51
    b2  = 5.75

Total dissonance of an interval between tone A (partials {f_i,a_i}) and tone
B (A's own partial set transposed by the interval ratio) is the sum of
d(...) over every cross pair (i in A, j in B). Self-pairs (i,i within the
same tone) are NOT included: they are interval-independent (a constant
offset that would not move any minimum/maximum), so the dissonance CURVE
swept over interval is exactly the cross-tone sum.

── 9b: duration rules ──────────────────────────────────────────────────────
--dump-modes reports each mode's `decay` field, which src/dsp/ModalResonator.h
(ModalResonator::excite(): `decayCoeff = exp(-6.9078f/(decayTime*sampleRate))`)
defines as T60 (time to fall 60 dB), confirmed in M5 (ROADMAP_PHYSICS.md §6,
"T60 比值" — measured/model ratio 1.00-1.28 at MIDI 60/72, all 5 modal
engines). Because dB decays LINEARLY in time for a single exponential decay,
the time to fall 20 dB is exactly T60/3:
    -60 dB at t=T60   =>   -20 dB at t = T60 * (20/60) = T60/3
This is the "let the previous strike decay 20 dB before re-striking the same
pitch" spacing floor requested by ROADMAP_PHYSICS.md M9-9b, and it is an
exact algebraic consequence of the (already-validated) T60 field — not a new
constant.

Usage:
    python tools/consonance.py                 # writes reports/consonance_tables.md
    python tools/consonance.py --cli <path>
"""
import argparse, json, math, sys, tempfile
from pathlib import Path
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from physics_verify import find_cli, render_probe, dump_modes_event, model_fundamental_decay

# ── Sethares 1993 dissonance-curve constants (cited above; DO NOT tune) ─────
DSTAR = 0.24
S1 = 0.0207
S2 = 18.96
B1 = 3.51
B2 = 5.75


def sethares_d(f1, f2, a1, a2):
    """Pairwise roughness of two sinusoidal partials (Sethares 1993)."""
    fmin = f1 if f1 < f2 else f2
    fdif = abs(f2 - f1)
    amin = a1 if a1 < a2 else a2
    s = DSTAR / (S1 * fmin + S2)
    return amin * (math.exp(-B1 * s * fdif) - math.exp(-B2 * s * fdif))


def total_dissonance(spec_a, spec_b):
    """Sum of sethares_d over every (partial of A) x (partial of B) pair."""
    total = 0.0
    for (f1, a1) in spec_a:
        for (f2, a2) in spec_b:
            total += sethares_d(f1, f2, a1, a2)
    return total


# ── partial-spectrum extraction (theory-only, via --dump-modes) ────────────
CONSONANCE_ENGINES = ["cimbalom", "tongue_drum", "water_gong", "water_gong_free", "piano"]
CONSONANCE_MIDI = 60      # C4 probe note (matches M2-2d's --amps probe note)
CONSONANCE_NPART = 8      # "first ~8 partials" per ROADMAP_PHYSICS.md M9-9a


def get_spectrum(cli, eng, outdir, midi=CONSONANCE_MIDI, npart=CONSONANCE_NPART):
    """Returns a list of (freq_hz, amp_normalized) for the first `npart`
    partials (ascending frequency, as --dump-modes already orders them) of
    `eng` at MIDI `midi`. amp_normalized = amp*body_mag (the model's own
    theory-only per-partial level -- same quantity M2's --amps gate measures
    against rendered audio) divided by that spectrum's own max, so every
    engine's loudest partial = 1.0. This is a documented per-instrument
    normalization choice (relative partial balance within one instrument's
    own timbre), not a physical constant -- it does not move where the
    dissonance curve's minima/maxima fall for a SINGLE spectrum swept against
    itself; it only sets the relative scale between two DIFFERENT engines in
    the cross-engine sweep, which is scale-arbitrary by construction (loudness
    matching between different instruments is a mix decision, not physics)."""
    wav, sf = render_probe(cli, eng, midi, outdir)
    event = dump_modes_event(cli, sf)
    if not event:
        raise RuntimeError(f"--dump-modes returned nothing for {eng} @ MIDI {midi}")
    partials = event["partials"][:npart]
    raw = [(p["freq"], p["amp"] * p.get("body_mag", 1.0)) for p in partials]
    peak = max(a for _, a in raw) or 1.0
    return [(f, a / peak) for f, a in raw]


# ── 9a: dissonance-curve sweep + extrema ────────────────────────────────────
SWEEP_STEP_CENTS = 5
SWEEP_MAX_CENTS = 1200
MIN_WINDOW_CENTS = 10   # "within 10 cents of a minimum" (task spec, 9a)
MAX_BAND_CENTS = 15     # discouraged-band half-width around a local maximum;
                         # an authored reporting choice (NOT a Sethares
                         # constant) -- maxima in these inharmonic curves are
                         # broader plateaus than the minima, so a slightly
                         # wider window than the 10-cent minimum window avoids
                         # under-reporting the discouraged region. Documented,
                         # not fitted to any audio.


def sweep_curve(spec_a, spec_b_base):
    cents_axis = list(range(0, SWEEP_MAX_CENTS + 1, SWEEP_STEP_CENTS))
    vals = []
    for c in cents_axis:
        ratio = 2.0 ** (c / 1200.0)
        spec_b = [(f * ratio, a) for f, a in spec_b_base]
        vals.append(total_dissonance(spec_a, spec_b))
    return cents_axis, vals


def find_extrema(cents_axis, vals):
    """Simple discrete local-minimum/maximum finder (the curve is a smooth
    deterministic sum of exponentials -- no measurement noise, so a plain
    neighbour comparison is sufficient; no smoothing/denoising needed)."""
    minima, maxima = [], []
    n = len(vals)
    for i in range(1, n - 1):
        if vals[i] < vals[i - 1] and vals[i] < vals[i + 1]:
            minima.append((cents_axis[i], vals[i]))
        elif vals[i] > vals[i - 1] and vals[i] > vals[i + 1]:
            maxima.append((cents_axis[i], vals[i]))
    # boundary points (0 and 1200 cents, i.e. unison/octave-of-self): include
    # if they are lower/higher than their single neighbour, since a sweep
    # boundary has no "other side" to compare against.
    if vals[0] < vals[1]:
        minima.insert(0, (cents_axis[0], vals[0]))
    elif vals[0] > vals[1]:
        maxima.insert(0, (cents_axis[0], vals[0]))
    if vals[-1] < vals[-2]:
        minima.append((cents_axis[-1], vals[-1]))
    elif vals[-1] > vals[-2]:
        maxima.append((cents_axis[-1], vals[-1]))
    return minima, maxima


INTERVAL_NAMES = [
    (0, "unison"), (100, "m2"), (200, "M2"), (300, "m3"), (400, "M3"),
    (500, "P4"), (600, "TT"), (700, "P5"), (800, "m6"), (900, "M6"),
    (1000, "m7"), (1100, "M7"), (1200, "octave"),
]


def nearest_name(cents):
    best = min(INTERVAL_NAMES, key=lambda p: abs(p[0] - cents))
    delta = cents - best[0]
    return f"{best[1]}{'+' if delta >= 0 else ''}{delta:.0f}c" if delta else best[1]


# ── 9b: duration rules (T60/3 = time to fall 20 dB) ─────────────────────────
DURATION_ENGINES = ["cimbalom", "tongue_drum", "water_gong", "water_gong_free", "piano"]
DURATION_MIDI_NOTES = [48, 60, 72]   # C3 / C4 / C5 registers


def duration_rules(cli, outdir):
    rows = []
    for eng in DURATION_ENGINES:
        for midi in DURATION_MIDI_NOTES:
            _, sf = render_probe(cli, eng, midi, outdir)
            t60 = model_fundamental_decay(cli, sf)
            if not t60:
                continue
            min_spacing = t60 / 3.0     # time to fall 20 dB, exact for a single exponential
            density_ceiling = 1.0 / min_spacing   # notes/sec, same-pitch re-strike
            rows.append(dict(engine=eng, midi=midi, t60=t60,
                              min_spacing=min_spacing, density_ceiling=density_ceiling))
    return rows


# ── report writer ────────────────────────────────────────────────────────
def fmt_curve_table(cents_axis, vals, step=25):
    lines = ["| cents | dissonance |", "|---:|---:|"]
    for c, v in zip(cents_axis, vals):
        if c % step == 0:
            lines.append(f"| {c} | {v:.4f} |")
    return "\n".join(lines)


def fmt_spectrum_table(spec):
    lines = ["| partial | freq (Hz) | rel. amp |", "|---:|---:|---:|"]
    for i, (f, a) in enumerate(spec, 1):
        lines.append(f"| {i} | {f:.2f} | {a:.4f} |")
    return "\n".join(lines)


def build_report(cli, outdir, duration_outdir=None):
    duration_outdir = duration_outdir if duration_outdir is not None else outdir
    out = []
    out.append("# TsukiSynth 協和度與時值表（Consonance & Duration Tables）\n")
    out.append("> 產生方式：`python tools/consonance.py`（ROADMAP_PHYSICS.md M9-9a/9b）。"
                "本表**全部由 `--dump-modes` 的理論模態頻譜（freq/amp/body_mag，"
                "M2 已驗證過的同一組理論值）+ Sethares (1993) dissonance-curve 公式計算**，"
                "未使用聽感、未從渲染音訊校準（no-circularity rule，ROADMAP_PHYSICS.md §0）。\n")
    out.append("## 0. 方法與公式來源\n")
    out.append(
        "Sethares, W.A. \"Local consonance and the relationship between timbre and "
        "scale\", *J. Acoust. Soc. Am.* 94(3), 1993 (同一封閉式亦見作者網頁 "
        "sethares.engr.wisc.edu/consemi.html)。兩個部分音 (f1,a1)、(f2,a2) 的成對粗糙度：\n"
    )
    out.append(
        "```text\n"
        "fmin = min(f1, f2)          fdif = |f2 - f1|          amin = min(a1, a2)\n"
        "s    = d* / (s1*fmin + s2)\n"
        "d(f1,f2,a1,a2) = amin * ( exp(-b1*s*fdif) - exp(-b2*s*fdif) )\n"
        "```\n"
    )
    out.append(
        "擬合常數（引用自 Sethares 1993，本工具未調整）："
        "d\\*=0.24　s1=0.0207　s2=18.96　b1=3.51　b2=5.75。\n\n"
        "一個音程的總協和度 = 兩音（A 的部分音集合 vs A 的部分音集合整體移調該音程）之間"
        "**所有跨音對**的 d(...) 加總（同音自己內部的音對是音程不變量，不影響曲線極值位置，"
        "故不計入）。掃描範圍 0–1200 cents，5-cent 為一步（241 點）。\n"
    )
    out.append(
        "**建議音程集**＝落在某個局部極小值 ±10 cents 內的音程（task 規格）。"
        "**不建議音程範圍**＝局部極大值 ±15 cents（本工具的報告呈現選擇，非 Sethares 常數——"
        "見程式碼 `MAX_BAND_CENTS` 註解：非諧引擎的極大值是較寬的高原，比 10-cent 的極小值"
        "窗略寬一些才不會漏報）。\n"
    )

    spectra = {}
    for eng in CONSONANCE_ENGINES:
        spectra[eng] = get_spectrum(cli, eng, outdir)

    out.append("## 1. 各引擎部分音頻譜（MIDI 60 探針，前 8 個部分音）\n")
    for eng in CONSONANCE_ENGINES:
        out.append(f"### {eng}\n")
        out.append(fmt_spectrum_table(spectra[eng]) + "\n")

    out.append("## 2. 各引擎自身音程協和度曲線與建議音程\n")
    self_results = {}
    for eng in CONSONANCE_ENGINES:
        spec = spectra[eng]
        cents_axis, vals = sweep_curve(spec, spec)
        minima, maxima = find_extrema(cents_axis, vals)
        self_results[eng] = (cents_axis, vals, minima, maxima)
        out.append(f"### {eng}\n")
        out.append(f"部分音比例（f_n/f_1）："
                    + ", ".join(f"{f/spec[0][0]:.3f}" for f, _ in spec) + "\n")
        out.append("局部極小值（建議音程，±10 cents 內視為推薦）：\n")
        if minima:
            for c, v in minima:
                out.append(f"- **{c} cents** ({nearest_name(c)}), dissonance={v:.4f}"
                            f" -> 建議範圍 [{max(0,c-MIN_WINDOW_CENTS)}, {min(1200,c+MIN_WINDOW_CENTS)}] cents\n")
        else:
            out.append("- (無局部極小值)\n")
        out.append("局部極大值（不建議音程，±15 cents 為不建議帶）：\n")
        if maxima:
            for c, v in maxima:
                out.append(f"- **{c} cents** ({nearest_name(c)}), dissonance={v:.4f}"
                            f" -> 不建議範圍 [{max(0,c-MAX_BAND_CENTS)}, {min(1200,c+MAX_BAND_CENTS)}] cents\n")
        else:
            out.append("- (無局部極大值)\n")
        out.append("\n完整曲線（每 25 cents 取樣；程式以 5-cent 解析度計算，"
                    "重跑 `python tools/consonance.py` 可得逐 5-cent 完整資料）：\n")
        out.append(fmt_curve_table(cents_axis, vals) + "\n")

    out.append("## 3. 跨引擎音程協和度\n")
    out.append("每一對「聲部 A 固定、聲部 B 整體移調該音程」計算跨音對總協和度——"
                "用來判斷兩個不同引擎的音同時響起時，音程差要落在哪裡才不會泛音打架。"
                "至少涵蓋 ROADMAP_PHYSICS.md M9 指定的 tongue_drum（色彩）vs cimbalom"
                "（和聲）；本表額外算了另外兩對排列組合，供 9d 新作的三引擎配器決策使用。\n")
    cross_pairs = [
        ("cimbalom", "tongue_drum", "cimbalom（和聲）vs tongue_drum（色彩，M9 指定必算）"),
        ("cimbalom", "water_gong", "cimbalom（和聲）vs water_gong（色彩/結構標記）"),
        ("tongue_drum", "water_gong", "tongue_drum（色彩/節奏）vs water_gong（色彩/結構標記）"),
    ]
    cross_results = {}
    for eng_a, eng_b, label in cross_pairs:
        spec_a, spec_b = spectra[eng_a], spectra[eng_b]
        cents_axis, vals = sweep_curve(spec_a, spec_b)
        minima, maxima = find_extrema(cents_axis, vals)
        cross_results[(eng_a, eng_b)] = (cents_axis, vals, minima, maxima)
        out.append(f"### {label}\n")
        out.append(f"{eng_a} 部分音固定，{eng_b} 部分音整體移調該音程後計算跨音對總協和度。\n")
        out.append("局部極小值（同時響起時建議的音程差）：\n")
        for c, v in minima:
            out.append(f"- **{c} cents** ({nearest_name(c)}), dissonance={v:.4f}"
                        f" -> 建議範圍 [{max(0,c-MIN_WINDOW_CENTS)}, {min(1200,c+MIN_WINDOW_CENTS)}] cents\n")
        out.append("局部極大值（不建議同時響起的音程差）：\n")
        for c, v in maxima:
            out.append(f"- **{c} cents** ({nearest_name(c)}), dissonance={v:.4f}"
                        f" -> 不建議範圍 [{max(0,c-MAX_BAND_CENTS)}, {min(1200,c+MAX_BAND_CENTS)}] cents\n")
        out.append("\n" + fmt_curve_table(cents_axis, vals) + "\n")

    out.append("\n## 4. 時值規則（M9-9b）：T60/3 = 衰減 20 dB 所需時間\n")
    out.append(
        "`--dump-modes` 的 `decay` 欄位是 T60（衰減 60dB 所需時間，`ModalResonator::excite()` "
        "定義，M5 已用音訊實測驗證 measured/model 比值 1.00–1.28）。單一指數衰減的 dB 值對時間"
        "**線性**，故衰減 20dB 所需時間精確等於 T60/3（不是新常數，是既有已驗證 T60 欄位的代數"
        "推論）。\n\n"
        "建議：同一音高要再次擊發前，至少等待「T60/3」秒，讓上一擊衰減 20dB 以上，"
        "避免共鳴堆疊變濁（月月觀察「短暫且不和諧」的其中一個可測量成因）。\n"
        "音符密度上限（同音高連續擊發）＝ 1 / (T60/3) 音符/秒。\n"
    )
    rows = duration_rules(cli, duration_outdir)
    out.append("| engine | MIDI | register | T60 (s) | min spacing = T60/3 (s) | density ceiling (notes/s) |")
    out.append("|---|---:|---|---:|---:|---:|")
    reg_name = {48: "C3", 60: "C4", 72: "C5"}
    for r in rows:
        out.append(f"| {r['engine']} | {r['midi']} | {reg_name.get(r['midi'], '')} | "
                    f"{r['t60']:.3f} | {r['min_spacing']:.3f} | {r['density_ceiling']:.2f} |")
    out.append("")

    return "\n".join(out), self_results, rows


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                  formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--cli", default=None)
    ap.add_argument("--out", default=None, help="output report path "
                     "(default reports/consonance_tables.md)")
    args = ap.parse_args()

    cli = Path(args.cli) if args.cli else find_cli()
    if not cli:
        print("ERROR: TsukiSynthCLI not found. Build it or pass --cli.", file=sys.stderr)
        return 1

    root = Path(__file__).resolve().parent.parent
    out_path = Path(args.out) if args.out else root / "reports" / "consonance_tables.md"
    out_path.parent.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory() as td:
        spectra_dir = Path(td) / "spectra"
        duration_dir = Path(td) / "duration"
        spectra_dir.mkdir()
        duration_dir.mkdir()
        report, self_results, duration = build_report(cli, spectra_dir, duration_dir)

    out_path.write_text(report, encoding="utf-8")
    print(f"wrote {out_path}")

    # console summary (short)
    print("\n== recommended self-intervals (cents) ==")
    for eng, (cents_axis, vals, minima, maxima) in self_results.items():
        print(f"  {eng:16} minima: {[c for c, _ in minima]}")
    print("\n== duration rules (T60/3, s) ==")
    for r in duration:
        print(f"  {r['engine']:16} MIDI {r['midi']:>3}  T60={r['t60']:.3f}s "
              f"min_spacing={r['min_spacing']:.3f}s  density<={r['density_ceiling']:.2f}/s")
    return 0


if __name__ == "__main__":
    sys.exit(main())
