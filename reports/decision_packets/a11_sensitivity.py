# -*- coding: utf-8 -*-
"""A11 免耳裁決包 — 共鳴板厚度 h 與材質敏感度分析（純解析式，不動 src、不 build）。

公式鏈逐條照抄自 src/physics/StringModel.h（2026-08-24 當日版本）：
  - StringModel::lengthFromMidiNote:  L = 0.35 * 2^(-(n-69)/12)
  - StringModel::tensionForNote:      T = mu * (2*L*f1)^2, mu = rho_string*pi*(d/2)^2
  - StringModel::bridgeLossRate:      D = E*h^3/(12*(1-nu^2)); rhoS = rho*h;
                                      Y_inf = 1/(8*sqrt(D*rhoS)); G = Y_inf;
                                      bridgeLoss = T*G/(ln(1000)*L),
                                      ln(1000) 字面值 6.907755278982137（與 C++ 同）
  - StringModel::decayTimeForFrequency:
        1/T60(f) = eta*f/2.2 + beta_air*f^2 + gamma_radiation*f + bridgeLoss
    （MaterialDB::internalFrictionRate, kEtaToDecayRate = 2.2）
弦參數 = Cimbalom 引擎預設：steel 弦、直徑 0.8 mm（CimbalomParams.diameterMm 預設）。
材質數值逐字取自 data/materials.json（不另造第二份來源；本腳本僅讀取該檔）。
本腳本用 float64；C++ 為 float32，對本敏感度分析的位數（3 位有效）無影響。
"""
import json
import math
import os

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
MATERIALS_JSON = os.path.join(REPO, "data", "materials.json")

LN1000 = 6.907755278982137          # StringModel.h kLn1000 字面值
K_ETA_TO_DECAY = 2.2                # MaterialDB.h kEtaToDecayRate
REF_LENGTH = 0.35                   # lengthFromMidiNote referenceLength 預設
DIAMETER_M = 0.0008                 # CimbalomParams.diameterMm = 0.8 預設
CURRENT_H_MM = 9.0                  # CimbalomEngine.h kBridgeSoundboardThicknessM = 0.009
CURRENT_MAT = "wood_spruce"         # CimbalomEngine.h kBridgeSoundboardMaterialKey

with open(MATERIALS_JSON, "r", encoding="utf-8") as f:
    MATS = json.load(f)["materials"]

STEEL = MATS["steel"]

# 木材候選：materials.json 中全部 wood_* 項 + bamboo（木質類比，僅供參考列）
WOOD_KEYS = ["wood_spruce", "wood_maple", "wood_birch", "wood_oak", "bamboo"]
H_MM_LIST = [8.0, 9.0, 10.0]
NOTES = {"C2": 36, "C4": 60, "C6": 84, "C8": 108}


def midi_freq(n):
    return 440.0 * 2.0 ** ((n - 69) / 12.0)


def string_TL(n):
    """回傳 (T, L, f1)——照抄 lengthFromMidiNote / tensionForNote。"""
    L = REF_LENGTH * 2.0 ** (-(n - 69) / 12.0)
    f1 = midi_freq(n)
    mu = STEEL["density"] * math.pi * (DIAMETER_M / 2.0) ** 2
    v = 2.0 * L * f1
    T = mu * v * v
    return T, L, f1


def Y_inf(mat, h_m):
    E = mat["youngs_modulus"]
    nu = mat["poisson_ratio"]
    rho = mat["density"]
    D = E * h_m ** 3 / (12.0 * (1.0 - nu * nu))
    rhoS = rho * h_m
    return 1.0 / (8.0 * math.sqrt(D * rhoS))


def bridge_loss(T, L, mat, h_m):
    return T * Y_inf(mat, h_m) / (LN1000 * L)


def t60_terms(f, T, L, sb_mat, h_m):
    """回傳 (T60, dict of 1/T60 各項) —— steel 弦阻尼 + 指定共鳴板。"""
    d = STEEL["damping"]
    internal = d["eta"] * f / K_ETA_TO_DECAY
    air = d["beta_air"] * f * f
    rad = d["gamma_radiation"] * f
    br = bridge_loss(T, L, sb_mat, h_m)
    denom = internal + air + rad + br
    return 1.0 / denom, {"internal": internal, "air": air, "rad": rad, "bridge": br}


def main():
    print("=== A11 sensitivity: soundboard h x material (steel string, fundamental) ===\n")

    print("-- Y_inf (s/kg) by material x h --")
    hdr = "material".ljust(14) + "".join(f"h={h:g}mm".rjust(14) for h in H_MM_LIST)
    print(hdr)
    for k in WOOD_KEYS:
        row = k.ljust(14)
        for h in H_MM_LIST:
            row += f"{Y_inf(MATS[k], h/1000.0):14.4e}"
        print(row)
    print()

    print("-- T60 (s) at fundamental, per note x h, material=wood_spruce --")
    print("note".ljust(6) + "".join(f"h={h:g}mm".rjust(12) for h in H_MM_LIST)
          + "  no-bridge".rjust(12))
    for name, n in NOTES.items():
        T, L, f1 = string_TL(n)
        row = name.ljust(6)
        for h in H_MM_LIST:
            t60, _ = t60_terms(f1, T, L, MATS[CURRENT_MAT], h / 1000.0)
            row += f"{t60:12.3f}"
        d = STEEL["damping"]
        nb = 1.0 / (d["eta"] * f1 / K_ETA_TO_DECAY + d["beta_air"] * f1 * f1
                    + d["gamma_radiation"] * f1)
        row += f"{nb:12.3f}"
        print(row)
    print()

    print("-- T60 (s) at fundamental, per note x material, h=9mm --")
    print("note".ljust(6) + "".join(k.rjust(13) for k in WOOD_KEYS))
    for name, n in NOTES.items():
        T, L, f1 = string_TL(n)
        row = name.ljust(6)
        for k in WOOD_KEYS:
            t60, _ = t60_terms(f1, T, L, MATS[k], 0.009)
            row += f"{t60:13.3f}"
        print(row)
    print()

    print("-- term shares of 1/T60 (%), material=wood_spruce, h=9mm --")
    print("note".ljust(6) + "internal".rjust(10) + "air".rjust(10)
          + "radiation".rjust(11) + "bridge".rjust(10))
    for name, n in NOTES.items():
        T, L, f1 = string_TL(n)
        _, terms = t60_terms(f1, T, L, MATS[CURRENT_MAT], 0.009)
        s = sum(terms.values())
        print(name.ljust(6)
              + f"{100*terms['internal']/s:10.1f}"
              + f"{100*terms['air']/s:10.1f}"
              + f"{100*terms['rad']/s:11.1f}"
              + f"{100*terms['bridge']/s:10.1f}")
    print()

    print("-- extremes: h 8->10mm T60 change (%), spruce; and material spread at h=9mm --")
    for name, n in NOTES.items():
        T, L, f1 = string_TL(n)
        t8, _ = t60_terms(f1, T, L, MATS[CURRENT_MAT], 0.008)
        t10, _ = t60_terms(f1, T, L, MATS[CURRENT_MAT], 0.010)
        t9s = {k: t60_terms(f1, T, L, MATS[k], 0.009)[0] for k in WOOD_KEYS}
        lo, hi = min(t9s, key=t9s.get), max(t9s, key=t9s.get)
        print(f"{name}: T60 h=8mm {t8:.3f}s -> h=10mm {t10:.3f}s "
              f"(+{100*(t10-t8)/t8:.1f}%); material h=9mm min {lo} {t9s[lo]:.3f}s / "
              f"max {hi} {t9s[hi]:.3f}s (spread {100*(t9s[hi]-t9s[lo])/t9s[lo]:.1f}%)")

    print("\n-- bridge-loss ratio checks --")
    print(f"Y_inf(h=8)/Y_inf(h=10) = {(10.0/8.0)**2:.4f}  (analytic h^-2 law)")
    for a, b in [("wood_spruce", "wood_maple"), ("wood_spruce", "wood_birch"),
                 ("wood_spruce", "wood_oak"), ("wood_spruce", "bamboo")]:
        r = Y_inf(MATS[a], 0.009) / Y_inf(MATS[b], 0.009)
        print(f"Y_inf({a})/Y_inf({b}) = {r:.4f}")


if __name__ == "__main__":
    main()
