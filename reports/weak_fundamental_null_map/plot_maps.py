#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""WF0925-N1：把 grid_*.csv / fur_elise_*.csv 畫成 PNG（單一藍色系，深=基頻越弱；不用彩虹色）。

  map_piano_felt.png          piano 引擎 n1/n2 熱圖 + 理論零點線 x1=3/5/7/9 + 給愛麗絲實際用到的格子
  map_four_configs.png        四組設定並排（同一色階）
  fur_elise_validation.png    給愛麗絲 905 顆：x1 vs stem 基頻頻帶峰值（實測 149 顆 + dump 預測全部）
  mechanism_H.png             機制圖：半正弦力脈衝頻譜 H(x)，E5 在兩個力度下第 1/第 2 partial 落點
色階固定在 -20..+20 dB（超出的夾到端點），**只為了看圖，不是判定門檻**。
"""
import csv
import math
import os
import sys

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.colors import LinearSegmentedColormap  # noqa: E402
from matplotlib.lines import Line2D  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import null_map_lib as L  # noqa: E402

plt.rcParams["font.sans-serif"] = ["Noto Sans CJK TC", "Microsoft JhengHei", "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False
plt.rcParams["font.size"] = 10

# 單一色相（藍）順序色階，由淺到深——dataviz 參考色板的 blue 100..700
BLUES = ["#cde2fb", "#b7d3f6", "#9ec5f4", "#86b6ef", "#6da7ec", "#5598e7", "#3987e5",
         "#2a78d6", "#256abf", "#1c5cab", "#184f95", "#104281", "#0d366b"]
# 深 = n1/n2 低（基頻弱）：色階反向，值低 -> 深
CMAP = LinearSegmentedColormap.from_list("blue_seq_rev", BLUES[::-1])
INK = "#1a1a1a"
MUTED = "#6b6b6b"
GRID = "#d9d9d9"
VMIN, VMAX = -20.0, 20.0

CONFIG_LABEL = {
    "piano_felt": "piano 引擎（給愛麗絲鋼琴版）— Felt，τc = pianoHammerTauC()",
    "cimbalom_wood": "cimbalom 預設 wood_mallet（給愛麗絲揚琴版）— τc = 0.5 ms 系",
    "cimbalom_felt": "cimbalom felt_mallet（ai_radiance_m3）— 同 pianoHammerTauC()",
    "string_bow": "string bow（韋瓦第四季）— Cotton，τc = 6 ms 系",
}
CONFIG_ENGINE = {
    "piano_felt": ("piano", {"material": "steel", "diameter_mm": 1.0}),
    "cimbalom_wood": ("cimbalom", {"material": "steel", "diameter_mm": 1.0}),
    "cimbalom_felt": ("cimbalom", {"exciter": "felt_mallet", "strike_position": 0.295}),
    "string_bow": ("string", {"exciter": "bow", "strike_position": 0.18}),
}


def read_csv(name):
    with open(os.path.join(HERE, name), encoding="utf-8") as f:
        return list(csv.DictReader(f))


def grid_matrix(cfg):
    rows = [r for r in read_csv("grid_%s.csv" % cfg) if r["grid_kind"] == "regular"]
    midis = sorted({int(r["midi"]) for r in rows})
    vels = sorted({float(r["velocity"]) for r in rows})
    Z = np.full((len(vels), len(midis)), np.nan)
    for r in rows:
        if r["n1n2_dump_db"] == "":
            continue
        Z[vels.index(float(r["velocity"])), midis.index(int(r["midi"]))] = float(r["n1n2_dump_db"])
    return np.array(midis), np.array(vels), Z


def theory_x1(cfg, midis_fine, vels_fine):
    eng, params = CONFIG_ENGINE[cfg]
    _, hidx, _ = L.effective_string_params(eng, params)
    X = np.zeros((len(vels_fine), len(midis_fine)))
    for j, m in enumerate(midis_fine):
        f1 = L.midi_hz(m)
        for i, v in enumerate(vels_fine):
            # 鏡像函式接受非整數 MIDI（錨點表分段線性內插本來就連續），只為了畫出平滑的零點線
            X[i, j] = 2 * f1 * L.tauc_engine(hidx, float(v), float(m))
    return X


def draw_map(ax, cfg, show_fe=False, compact=False):
    midis, vels, Z = grid_matrix(cfg)
    mx = np.concatenate([midis - 0.5, [midis[-1] + 0.5]])
    vy = np.concatenate([vels - 0.0125, [vels[-1] + 0.0125]])
    mesh = ax.pcolormesh(mx, vy, np.clip(Z, VMIN, VMAX), cmap=CMAP, vmin=VMIN, vmax=VMAX,
                         shading="flat", rasterized=True)
    # 理論零點線：x1 = 3, 5, 7, 9（鏡像公式在 0.25 半音 × 191 個力度點上算，基頻用十二平均律）
    mf = np.arange(21, 108.01, 0.25)
    vf = np.linspace(0.05, 1.0, 191)
    X = theory_x1(cfg, mf, vf)
    levels = [lv for lv in (3, 5, 7, 9, 11) if X.min() < lv < X.max()]
    if levels:
        cs = ax.contour(mf, vf, X, levels=levels, colors=INK, linewidths=0.9, linestyles="--")
        labs = ax.clabel(cs, fmt=lambda v: "零點 x=%d" % v, fontsize=7 if compact else 8, inline=True)
        for t in labs:
            t.set_bbox(dict(boxstyle="round,pad=0.1", fc="white", ec="none", alpha=0.8))
    if show_fe:
        agg = read_csv("fur_elise_note_velocity.csv")
        ok = [(int(a["midi"]), float(a["velocity"])) for a in agg if int(a["fail_0914"]) == 0]
        bad = [(int(a["midi"]), float(a["velocity"]), int(a["fail_0914"])) for a in agg
               if int(a["fail_0914"]) > 0]
        ax.scatter([p[0] for p in ok], [p[1] for p in ok], s=14, facecolors="none",
                   edgecolors=MUTED, linewidths=0.8, zorder=3)
        ax.scatter([p[0] for p in bad], [p[1] for p in bad], s=70, marker="X", c="white",
                   edgecolors=INK, linewidths=1.2, zorder=4)
        nudge = {93: (-44, 8), 94: (8, 8)}   # A6/A#6 相鄰，標籤左右錯開
        for m, v, n in bad:
            ax.annotate("%s ×%d" % (L.midi_to_name(m), n), (m, v), xytext=nudge.get(m, (6, 6)),
                        textcoords="offset points", fontsize=8, color=INK, zorder=5,
                        bbox=dict(boxstyle="round,pad=0.15", fc="white", ec="none", alpha=0.85))
    cticks = [m for m in range(24, 109, 12)]
    ax.set_xticks(cticks)
    ax.set_xticklabels(["%s\n(%d)" % (L.midi_to_name(m), m) for m in cticks], fontsize=8)
    ax.set_xlim(20.5, 108.5)
    ax.set_ylim(0.0375, 1.0125)
    ax.set_ylabel("velocity（score 力度 0–1）")
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    return mesh


def fig_piano():
    fig, ax = plt.subplots(figsize=(12, 6.2), dpi=150)
    mesh = draw_map(ax, "piano_felt", show_fe=True)
    ax.set_xlabel("音高（MIDI）")
    ax.set_title("piano 引擎弱基頻零點地圖：基頻叢 ÷ 第 2 partial 叢（dB，--dump-modes 實測）",
                 loc="left", fontsize=12, color=INK)
    cb = fig.colorbar(mesh, ax=ax, fraction=0.03, pad=0.02, extend="both")
    cb.set_label("n1/n2（dB）：顏色越深 = 基頻越弱（色階夾在 ±20 dB，只為看圖）")
    handles = [Line2D([0], [0], color=INK, ls="--", lw=0.9, label="理論零點線 x1 = 2·f1·τc = 3、5、7、9、11"),
               Line2D([0], [0], marker="o", ls="", mfc="none", mec=MUTED, label="給愛麗絲鋼琴版用到的（音高, 力度）：stem_verify 無 FAIL"),
               Line2D([0], [0], marker="X", ls="", mfc="white", mec=INK, ms=9, label="給愛麗絲鋼琴版 stem_verify FAIL（09-14 D14 全量）")]
    ax.legend(handles=handles, loc="upper left", fontsize=8, frameon=True, framealpha=0.9)
    fig.text(0.01, 0.005, "資料：reports/weak_fundamental_null_map/grid_piano_felt.csv（MIDI 21–108 × velocity 0.05–1.00 每 0.025）；"
             "steel Ø1.0 mm、3 弦 ±5 cent（與 fur_elise_complete 相同）；CLI = build\\ 09-15 版複本",
             fontsize=7, color=MUTED)
    fig.tight_layout(rect=(0, 0.02, 1, 1))
    fig.savefig(os.path.join(HERE, "map_piano_felt.png"))
    plt.close(fig)


def fig_four():
    fig, axes = plt.subplots(2, 2, figsize=(14, 9), dpi=130, sharex=True, sharey=True,
                             layout="constrained")
    mesh = None
    for ax, cfg in zip(axes.flat, ["piano_felt", "cimbalom_felt", "string_bow", "cimbalom_wood"]):
        mesh = draw_map(ax, cfg, compact=True)
        ax.set_title(CONFIG_LABEL[cfg], loc="left", fontsize=10, color=INK)
    for ax in axes[1]:
        ax.set_xlabel("音高（MIDI）")
    cb = fig.colorbar(mesh, ax=axes.ravel().tolist(), fraction=0.025, pad=0.02, extend="both")
    cb.set_label("n1/n2（dB，dump 實測）：越深 = 基頻越弱")
    fig.suptitle("四種 corpus 實際在用的弦類激發：哪裡的基頻掉進力脈衝零點（虛線 = 理論零點 x1=3/5/7/9/11）",
                 x=0.01, ha="left", fontsize=12, color=INK)
    fig.savefig(os.path.join(HERE, "map_four_configs.png"), bbox_inches="tight")
    plt.close(fig)


def fig_validation():
    ev = read_csv("fur_elise_events.csv")
    st = read_csv("fur_elise_stems.csv")
    fig, ax = plt.subplots(figsize=(11, 5.6), dpi=150)
    for lv in (3, 5, 7):
        ax.axvspan(lv - 0.2045, lv + 0.2045, color=BLUES[1], zorder=0, lw=0)
        ax.text(lv, -81.5, "零點 x=%d\n凹口深度 ≤−10 dB" % lv, ha="center", va="bottom", fontsize=7.5, color=MUTED)
    ax.axhline(-70, color=INK, lw=0.9, ls="--", zorder=1)
    ax.text(7.95, -69.3, "−70 dBFS：melody_verify 既有 BAND_GATE_DBFS", ha="right", va="bottom", fontsize=8, color=INK)
    # dump 預測（全部 905 顆，含 UNVERIFIED 的低音）
    xp = [float(r["x1"]) for r in ev]
    yp = [float(r["band_peak_pred_dbfs"]) for r in ev]
    ax.scatter(xp, yp, s=8, c=BLUES[6], alpha=0.35, lw=0, zorder=2, label="dump 預測（905 顆全部）")
    sp = [r for r in st if r["verdict_rerun"] == "PASS"]
    sf = [r for r in st if r["verdict_rerun"] == "FAIL"]
    su = [r for r in st if r["verdict_rerun"] == "UNVERIFIED"]
    xi = {int(r["index"]): float(r["x1"]) for r in ev}
    ax.scatter([xi[int(r["index"])] for r in su], [float(r["band_peak_dbfs"]) for r in su], s=22,
               marker="s", facecolors="none", edgecolors=MUTED, lw=0.8, zorder=3,
               label="stem 實測：UNVERIFIED（f0<167 Hz 低音，不判 onset）")
    ax.scatter([xi[int(r["index"])] for r in sp], [float(r["band_peak_dbfs"]) for r in sp], s=26,
               facecolors="white", edgecolors=BLUES[10], lw=1.0, zorder=4, label="stem 實測：PASS")
    ax.scatter([xi[int(r["index"])] for r in sf], [float(r["band_peak_dbfs"]) for r in sf], s=70,
               marker="X", c=BLUES[12], edgecolors="white", lw=0.8, zorder=5, label="stem 實測：FAIL")
    ax.set_xlim(0, 8)
    ax.set_ylim(-82, max(yp + [float(r["band_peak_dbfs"]) for r in st]) + 2)
    ax.set_xlabel("x1 = 2 · f1 · τc（理論；基頻落在力脈衝頻譜的哪裡）")
    ax.set_ylabel("stem 基頻頻帶峰值（dBFS）")
    ax.set_title("給愛麗絲鋼琴版 905 顆：FAIL 全部在零點凹口內、而且基頻頻帶低於 −70 dBFS",
                 loc="left", fontsize=12, color=INK)
    ax.grid(axis="y", color=GRID, lw=0.6)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax.legend(loc="upper right", fontsize=8, frameon=True, framealpha=0.95)
    fig.tight_layout()
    fig.savefig(os.path.join(HERE, "fur_elise_validation.png"))
    plt.close(fig)


def fig_mechanism():
    x = np.linspace(0.01, 8, 4000)
    H = np.array([L.force_spectrum_h(xx / 2.0, 1.0) for xx in x])   # f=x/2, tau=1 -> x
    HdB = 20 * np.log10(np.maximum(H, 1e-6))
    xe = x[x >= 1.8]
    env = 20 * np.log10(1.0 / np.abs(1 - xe ** 2))
    fig, ax = plt.subplots(figsize=(11, 4.8), dpi=150)
    ax.plot(xe, env, color=MUTED, lw=0.8, ls=":", label="旁瓣包絡 1/|1−x²|（x≥2 時「沒有零點的話會有多高」）")
    ax.plot(x, HdB, color=BLUES[10], lw=2, label="半正弦力脈衝頻譜 H(x)（HammerImpulse::forceSpectrumMagnitude）")
    ev = read_csv("fur_elise_events.csv")
    e_low = next(r for r in ev if r["note"] == "E5" and abs(float(r["velocity"]) - 0.278) < 1e-6)
    e_hi = next(r for r in ev if r["note"] == "E5" and abs(float(r["velocity"]) - 0.427) < 1e-6)
    grid = read_csv("grid_piano_felt.csv")

    def x2_of(v):
        g = next(r for r in grid if int(r["midi"]) == 76 and abs(float(r["velocity"]) - v) < 1e-6)
        return float(g["x1"]), float(g["x2"])
    for v, mk, lab in ((0.278, "X", "E5 力度 0.278（9 顆 FAIL）"), (0.427, "o", "E5 力度 0.427（37 顆 PASS）")):
        x1, x2 = x2_of(v)
        for xx, nm in ((x1, "第1"), (x2, "第2")):
            hh = 20 * math.log10(max(L.force_spectrum_h(xx / 2.0, 1.0), 1e-6))
            ax.scatter([xx], [hh], s=80 if mk == "X" else 50, marker=mk,
                       c=BLUES[12] if mk == "X" else "white", edgecolors=BLUES[12], lw=1.2, zorder=5)
            off = {("X", "第1"): (10, -28), ("X", "第2"): (-20, 16),
                   ("o", "第1"): (10, 8), ("o", "第2"): (10, 4)}[(mk, nm)]
            ax.annotate("%s\n%s partial x=%.2f" % (lab, nm, xx), (xx, hh), xytext=off,
                        textcoords="offset points", fontsize=7.5, color=INK)
    for lv in (3, 5, 7):
        ax.axvline(lv, color=GRID, lw=0.8, zorder=0)
    ax.set_xlim(0, 8)
    ax.set_ylim(-75, 3)
    ax.set_xlabel("x = 2 · f · τc（partial 頻率 × 接觸時間 × 2）")
    ax.set_ylabel("H（dB，DC = 0 dB）")
    ax.set_title("機制：同一顆 E5，力度 0.278 → τc 變長 → 基頻剛好踩在 x=3 零點；力度 0.427 → 換成第 2 partial 踩在 x=5 零點",
                 loc="left", fontsize=10.5, color=INK)
    ax.legend(loc="upper right", fontsize=8, frameon=True, framealpha=0.95)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    fig.tight_layout()
    fig.savefig(os.path.join(HERE, "mechanism_H.png"))
    plt.close(fig)


if __name__ == "__main__":
    fig_piano()
    fig_four()
    fig_validation()
    fig_mechanism()
    print("wrote map_piano_felt.png map_four_configs.png fur_elise_validation.png mechanism_H.png")
