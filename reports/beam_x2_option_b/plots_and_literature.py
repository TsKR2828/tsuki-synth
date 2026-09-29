#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""WF0925b-BR: figures (monochrome) + literature-position table.

Descriptive only (NOT a GATE). Reads the CSVs written by sweep_t60.py and
render_compare.py in this folder; writes:
  fig1_t60_steel_aluminum.png     mode-1/mode-2 T60 vs f0, base vs noX2
  fig2_t60_ratio_materials.png    T60(noX2)/T60(base) of mode 1, 8 corpus materials
  fig3_corpus_delta.png           per-score dRMS / d(tail share) / d(length) (changed scores)
  corpus_beam_tail_share.csv      tail energy re whole-file energy, base vs noX2
  fig4_literature_position.png    model alpha (base, noX2) against the literature
                                  intervals quoted in docs/D1_BEAM_PLATE_DAMPING_SEARCH.zh-TW.md
  literature_position.csv         the numbers behind fig4

Literature numbers: ONLY values already printed in D1 (§3.2, §3.4) -- no new
source numbers. "below / inside / above" in literature_position.csv is a
plain description of where a number sits relative to D1's interval edges; it
is not a pass/fail threshold (R2).

Colour: one ink family (monochrome, per the project's design preference);
identity is never colour-alone -- base = solid line / filled marker,
noX2 = dashed line / hollow marker, plus a legend and direct labels.
"""
import csv
import math
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import matplotlib.ticker  # noqa: E402

HERE = Path(__file__).resolve().parent
INK = "#1d2126"      # base
INK2 = "#8c929b"     # noX2
GRID = "#e4e6e9"
BAND = "#d5d8dc"
LN1000 = math.log(1000.0)

plt.rcParams.update({"font.family": ["Microsoft JhengHei", "DejaVu Sans"],
                     "axes.edgecolor": "#555a61", "axes.labelcolor": INK,
                     "xtick.color": "#555a61", "ytick.color": "#555a61",
                     "axes.spines.top": False, "axes.spines.right": False,
                     "figure.facecolor": "white", "axes.facecolor": "white",
                     "font.size": 9, "axes.unicode_minus": False})


def load_sweep():
    rows = list(csv.DictReader(open(HERE / "t60_sweep.csv", encoding="utf-8")))
    out = {}
    for r in rows:
        out.setdefault((r["material"], int(r["mode"])), []).append(
            (int(r["midi"]), float(r["freq_hz"]), float(r["t60_base_s"]), float(r["t60_nox2_s"])))
    return out


def sweep_at(sw, mat, midi, mode=1):
    for m, f, tb, tx in sw[(mat, mode)]:
        if m == midi:
            return f, tb, tx
    raise KeyError((mat, midi, mode))


def style(ax):
    ax.grid(True, which="major", color=GRID, linewidth=0.6)
    ax.set_axisbelow(True)
    # plain "%g" tick labels: the CJK font has no glyph for mathtext's minus in 10^-1
    fmt = matplotlib.ticker.FuncFormatter(lambda v, _: "%g" % v)
    for axis, scale in ((ax.xaxis, ax.get_xscale()), (ax.yaxis, ax.get_yscale())):
        if scale == "log":
            axis.set_major_formatter(fmt)


def fig1(sw):
    fig, axes = plt.subplots(1, 2, figsize=(10, 4.2), sharey=True)
    for ax, mat, title in ((axes[0], "steel", "鋼 steel"), (axes[1], "aluminum", "鋁 aluminum")):
        for mode, lw in ((1, 2.0), (2, 1.2)):
            pts = sw[(mat, mode)]
            f0 = [sweep_at(sw, mat, m, 1)[0] for m, *_ in pts]
            ax.plot(f0, [tb for *_, tb, tx in pts], color=INK, lw=lw, ls="-",
                    label="現行（保留 ×2）模態 %d" % mode)
            ax.plot(f0, [tx for *_, tb, tx in pts], color=INK2, lw=lw, ls="--",
                    label="拿掉 ×2 模態 %d" % mode)
        for midi, name in ((48, "C3"), (60, "C4"), (72, "C5")):
            f, tb, tx = sweep_at(sw, mat, midi)
            ax.plot([f], [tb], "o", color=INK, ms=5)
            ax.plot([f], [tx], "o", mfc="white", mec=INK2, ms=5)
            ax.annotate("%s %.1f→%.1f s" % (name, tb, tx), (f, tx), textcoords="offset points",
                        xytext=(6, 4), fontsize=8, color=INK)
        ax.set_xscale("log")
        ax.set_yscale("log")
        ax.set_xlabel("基頻 f0（Hz，已調到 MIDI 21–108）")
        ax.set_title(title, color=INK, loc="left")
        style(ax)
    axes[0].set_ylabel("T60（秒，對數）")
    axes[1].legend(frameon=False, fontsize=8, loc="lower left")
    fig.suptitle("tongue_drum 模態 T60：現行 vs 拿掉 ×2（--dump-modes；描述用、非 GATE）",
                 x=0.01, ha="left", color=INK)
    fig.tight_layout()
    fig.savefig(HERE / "fig1_t60_steel_aluminum.png", dpi=150)
    plt.close(fig)


def fig2(sw):
    mats = ["steel", "aluminum", "brass", "glass", "bamboo", "wood_oak", "wood_birch", "wood_maple"]
    fig, axes = plt.subplots(2, 4, figsize=(11, 5), sharex=True, sharey=True)
    for ax, mat in zip(axes.flat, mats):
        pts = sw[(mat, 1)]
        ax.plot([f for _, f, _, _ in pts], [tx / tb for _, _, tb, tx in pts], color=INK, lw=2)
        ax.axhline(2.0, color=INK2, lw=0.8, ls=":")
        ax.axhline(1.0, color=INK2, lw=0.8, ls=":")
        ax.set_xscale("log")
        ax.set_ylim(0.95, 2.05)
        ax.set_title(mat, loc="left", color=INK)
        style(ax)
    for ax in axes[1]:
        ax.set_xlabel("f0（Hz）")
    for ax in axes[:, 0]:
        ax.set_ylabel("T60 拿掉×2 ÷ 現行")
    fig.suptitle("模態 1 的 T60 變長倍數（1＝不變，2＝上限：×2 那一項佔全部衰減時）；描述用、非 GATE",
                 x=0.01, ha="left", color=INK)
    fig.tight_layout()
    fig.savefig(HERE / "fig2_t60_ratio_materials.png", dpi=150)
    plt.close(fig)


def tail_share_db(r, label):
    """tail energy re whole-file energy (dB); independent of the export's
    peak normalisation gain. whole-file energy = RMS^2 * length (mono)."""
    rms = 10 ** (float(r["rms_" + label]) / 20.0)
    tot = rms * rms * float(r["len_%s_s" % label])
    return float(r["tail_e_%s_db" % label]) - 10.0 * math.log10(tot)


def fig3():
    rows = list(csv.DictReader(open(HERE / "corpus_beam_before_after.csv", encoding="utf-8")))
    rows = [r for r in rows if r["identical"] == "False"]
    for r in rows:
        r["d_tail_share_db"] = tail_share_db(r, "nox2") - tail_share_db(r, "base")
        r["d_len_s"] = float(r["len_nox2_s"]) - float(r["len_base_s"])
    rows.sort(key=lambda r: r["d_tail_share_db"])
    names = [r["score"].split("/")[-1].replace(".score.json", "") for r in rows]
    y = list(range(len(rows)))
    fig, axes = plt.subplots(1, 3, figsize=(12, 0.26 * len(rows) + 1.8), sharey=True)
    for ax, key, title in ((axes[0], "d_rms_db", "全檔 RMS 差（dB，峰值正規化之後）"),
                           (axes[1], "d_tail_share_db", "尾段能量佔全檔比例的差（dB）"),
                           (axes[2], "d_len_s", "檔案長度差（秒）")):
        v = [float(r[key]) for r in rows]
        ax.hlines(y, 0, v, color=INK2, lw=1.2)
        ax.plot(v, y, "o", color=INK, ms=4)
        ax.axvline(0, color="#555a61", lw=0.8)
        ax.set_title(title, loc="left", color=INK)
        style(ax)
    axes[0].set_yticks(y)
    axes[0].set_yticklabels(names, fontsize=7)
    fig.suptitle("拿掉 ×2 的版本 減 現行版（corpus 內會變的 %d 檔；正值＝變大／變長）。"
                 "39 檔都是 normalize:true，取樣峰值前後都一樣（差 0.000 dB），所以沒畫；描述用、非 GATE"
                 % len(rows), x=0.01, ha="left", color=INK, fontsize=9)
    fig.tight_layout()
    fig.savefig(HERE / "fig3_corpus_delta.png", dpi=150)
    plt.close(fig)
    with open(HERE / "corpus_beam_tail_share.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["score", "tail_share_base_db", "tail_share_nox2_db", "d_tail_share_db", "d_len_s"])
        for r in sorted(rows, key=lambda r: r["score"]):
            w.writerow([r["score"], "%.3f" % tail_share_db(r, "base"), "%.3f" % tail_share_db(r, "nox2"),
                        "%+.3f" % r["d_tail_share_db"], "%+.3f" % r["d_len_s"]])


def literature_rows(sw):
    """Only numbers already printed in D1 (section cited per row)."""
    a = lambda t: LN1000 / t  # alpha (1/s) from T60
    cases = []
    # (label, material, midi, lit_low, lit_high, lit_note, D1 section)
    spec = [
        ("鋼 3 mm，262 Hz（C4）", "steel", 60, 0.11, 0.36,
         "已知機制描述用合計（熱彈性＋黏性空氣＋材料表縱向損耗）；支撐、窄條輻射沒算，只會往上加", "§3.2"),
        ("鋁 3 mm，262 Hz（C4）", "aluminum", 60, 0.376, 0.541,
         "只有熱彈性一項（S3／S1）；其他機制沒算，只會往上加", "§3.2"),
        ("鋼 3.2 mm，43.7 Hz（出貨低音群最低音 MIDI 29）", "steel", 29, 0.069, 0.088,
         "只有熱彈性一項，S3；S5 換算只有 0.010（兩篇差 7～9 倍）", "§3.4"),
        ("鋼 2.6 mm，110 Hz（出貨主體群最低音 MIDI 45）", "steel", 45, 0.104, 0.133,
         "只有熱彈性一項，S3；S5 換算 0.015", "§3.4"),
        ("鋼 2.6 mm，659 Hz（出貨主體群最高音 MIDI 76）", "steel", 76, 0.104, 0.133,
         "只有熱彈性一項，S3（音頻範圍內與頻率無關）；S5 換算 0.015", "§3.4"),
        ("鋁 2.0 mm，740 Hz（出貨高音群最低音 MIDI 78）", "aluminum", 78, 0.85, 1.22,
         "只有熱彈性一項：S1 0.85、S3 1.22（兩個點，不是區間）", "§3.4"),
        ("鋁 2.0 mm，1245 Hz（出貨高音群最高音 MIDI 87）", "aluminum", 87, 0.85, 1.22,
         "只有熱彈性一項：S1 0.85、S3 1.22", "§3.4"),
    ]
    for label, mat, midi, lo, hi, note, sec in spec:
        f, tb, tx = sweep_at(sw, mat, midi)
        ab, ax_ = a(tb), a(tx)
        pos = lambda v: "below" if v < lo else ("above" if v > hi else "inside")
        cases.append({"case": label, "material": mat, "midi": midi, "freq_hz": "%.1f" % f,
                      "lit_low_per_s": lo, "lit_high_per_s": hi, "lit_note": note,
                      "d1_section": sec, "t60_base_s": "%.4g" % tb, "t60_nox2_s": "%.4g" % tx,
                      "alpha_base_per_s": "%.3f" % ab, "alpha_nox2_per_s": "%.3f" % ax_,
                      "pos_base": pos(ab), "pos_nox2": pos(ax_)})
    return cases


def fig4(cases):
    fig, ax = plt.subplots(figsize=(10, 4.6))
    ys = list(range(len(cases)))[::-1]
    for y, c in zip(ys, cases):
        lo, hi = c["lit_low_per_s"], c["lit_high_per_s"]
        ax.plot([lo, hi], [y, y], color=BAND, lw=9, solid_capstyle="butt")
        ab, ax_ = float(c["alpha_base_per_s"]), float(c["alpha_nox2_per_s"])
        ax.plot([ab], [y], "o", color=INK, ms=8, zorder=3)
        ax.plot([ax_], [y], "o", mfc="white", mec=INK, mew=1.5, ms=8, zorder=3)
        ax.annotate("%.3f" % ab, (ab, y), textcoords="offset points", xytext=(0, 8),
                    ha="center", fontsize=7, color=INK)
        ax.annotate("%.3f" % ax_, (ax_, y), textcoords="offset points", xytext=(0, -13),
                    ha="center", fontsize=7, color=INK2)
    ax.set_yticks(ys)
    ax.set_yticklabels([c["case"] for c in cases], fontsize=8)
    ax.set_xscale("log")
    ax.set_xlabel("振幅衰減速度 α = ln(1000)/T60（1/秒，對數；越大＝越快安靜）")
    from matplotlib.lines import Line2D
    handles = [Line2D([], [], color=BAND, lw=9, label="D1 已引述的文獻數字範圍"),
               Line2D([], [], marker="o", color=INK, ls="", ms=7, label="現行（保留 ×2）"),
               Line2D([], [], marker="o", mfc="white", mec=INK, ls="", ms=7, label="拿掉 ×2")]
    ax.legend(handles=handles, frameon=False, fontsize=8, loc="upper right")
    style(ax)
    fig.suptitle("模型的基頻衰減 vs D1 文件裡的文獻數字（灰帶多數只含熱彈性一項）；描述用、非 GATE",
                 x=0.01, ha="left", color=INK)
    fig.tight_layout()
    fig.savefig(HERE / "fig4_literature_position.png", dpi=150)
    plt.close(fig)


def main():
    sw = load_sweep()
    fig1(sw)
    fig2(sw)
    fig3()
    cases = literature_rows(sw)
    with open(HERE / "literature_position.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(cases[0].keys()))
        w.writeheader()
        w.writerows(cases)
    for c in cases:
        print("%-44s base α=%s (%s)  noX2 α=%s (%s)  lit %s..%s"
              % (c["case"], c["alpha_base_per_s"], c["pos_base"], c["alpha_nox2_per_s"],
                 c["pos_nox2"], c["lit_low_per_s"], c["lit_high_per_s"]))
    fig4(cases)
    print("figures written")


if __name__ == "__main__":
    main()
