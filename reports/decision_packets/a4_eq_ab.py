# -*- coding: utf-8 -*-
"""A4 免耳裁決包溯源腳本 — 亮度 EQ 應急層 A/B 量測。

做法（原檔絕不動）：
  1. 把三首代表曲 score.json 複製到暫存目錄，做三個版本：
     eq_off = 原檔原樣（現行出貨狀態：repo 內沒有任何 score 寫 eq 區塊，
              gain 0 = 硬 bypass，渲染位元與沒寫 eq 完全相同）
     eq_on6 = 加上 playbook 文件例值 {"high_shelf_freq_hz": 2000, "high_shelf_gain_db": 6.0}
     eq_on4 = 同上但 gain = 4.0（playbook 建議區間 +4~+8 dB 的下緣）
  2. 各自用同一顆 build/TsukiSynthCLI_artefacts/Release/TsukiSynthCLI.exe --batch 渲染。
  3. 量測（mono 平均、soundfile 24-bit 正確解碼、Welch PSD nperseg=16384）：
     整曲 RMS/peak dBFS、頻譜質心、各倍頻程能量差 dB、>=2k/4k/8k 高頻段能量差 dB
     與其佔全曲能量比例。

用法：python a4_eq_ab.py <work_dir>
（work_dir 為可寫暫存目錄；腳本自行建立 eq_off/eq_on6/eq_on4/render_* 子目錄）
"""
import json, pathlib, shutil, subprocess, sys

import numpy as np
import soundfile as sf
from scipy.signal import welch

REPO = pathlib.Path(__file__).resolve().parents[2]
CLI = REPO / "build/TsukiSynthCLI_artefacts/Release/TsukiSynthCLI.exe"
SCORES = [
    "scores/library/akashic/akashic_opening_bell_001.score.json",   # tongue_drum + water_gong
    "scores/examples/moonlight_sonata_movement1_yangqin.score.json",  # cimbalom
    "scores/examples/water_gong_clamped.score.json",                # water_gong
]
RENDER_NAMES = ["akashic_opening_bell_001", "moonlight_sonata_i_yangqin", "water_gong_clamped"]


def prepare(work: pathlib.Path):
    for sub in ("eq_off", "eq_on6", "eq_on4"):
        (work / sub).mkdir(parents=True, exist_ok=True)
    for rel in SCORES:
        src = REPO / rel
        shutil.copy(src, work / "eq_off" / src.name)
        for sub, gain in (("eq_on6", 6.0), ("eq_on4", 4.0)):
            d = json.loads(src.read_text(encoding="utf-8"))
            d["global"].setdefault("effects", {})["eq"] = {
                "high_shelf_freq_hz": 2000.0, "high_shelf_gain_db": gain}
            (work / sub / src.name).write_text(
                json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")


def render(work: pathlib.Path):
    for sub in ("eq_off", "eq_on6", "eq_on4"):
        out = work / f"render_{sub}"
        out.mkdir(exist_ok=True)
        subprocess.run([str(CLI), "--batch", str(work / sub), "--output", str(out)], check=True)


def analyze(path):
    x, fs = sf.read(path)
    if x.ndim > 1:
        x = x.mean(axis=1)
    f, P = welch(x, fs=fs, nperseg=16384)
    return dict(
        rms_db=20 * np.log10(np.sqrt(np.mean(x ** 2))),
        peak_db=20 * np.log10(np.max(np.abs(x))),
        centroid=float(np.sum(f * P) / np.sum(P)),
        bands={fc: float(np.sum(P[(f >= fc / np.sqrt(2)) & (f < fc * np.sqrt(2))]))
               for fc in (63, 125, 250, 500, 1000, 2000, 4000, 8000, 16000)},
        hi={c: float(np.sum(P[f >= c])) for c in (2000, 4000, 8000)},
        total=float(np.sum(P)))


def main():
    work = pathlib.Path(sys.argv[1]).resolve()
    prepare(work)
    render(work)
    out = {}
    for name in RENDER_NAMES:
        off = analyze(work / "render_eq_off" / f"{name}.wav")
        row = {"rms_off_db": round(off["rms_db"], 2), "peak_off_db": round(off["peak_db"], 2),
               "centroid_off_hz": round(off["centroid"], 1),
               "hi_share_off_pct": {c: round(100 * off["hi"][c] / off["total"], 4) for c in off["hi"]}}
        for sub in ("eq_on6", "eq_on4"):
            on = analyze(work / f"render_{sub}" / f"{name}.wav")
            row[sub] = {
                "rms_delta_db": round(on["rms_db"] - off["rms_db"], 2),
                "peak_delta_db": round(on["peak_db"] - off["peak_db"], 2),
                "centroid_hz": round(on["centroid"], 1),
                "band_delta_db": {fc: round(10 * np.log10(on["bands"][fc] / off["bands"][fc]), 2)
                                  for fc in off["bands"] if off["bands"][fc] > 0},
                "hi_delta_db": {c: round(10 * np.log10(on["hi"][c] / off["hi"][c]), 2)
                                for c in off["hi"]},
            }
        out[name] = row
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
