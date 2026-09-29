#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""WF0925-N1 弱基頻「零點地圖」共用函式庫（研究 lane，不改 src/tools/tests）。

內容：
  1. src/physics/HammerImpulse.h 的 float64 Python 鏡像（本卡自己重寫，逐項對照原始碼）：
     keytrackScale()、tauCForHardness()、tauCForStrike()、tauCForNote()、
     pianoHammerG()/pianoHammerTauC()（A14 B-2 落地後的現行版）、以及 B4 舊版
     pianoHammerTauC()（只用來回頭解釋 08-30 那 22 顆舊 FAIL，現行渲染不用）、
     forceSpectrumMagnitude() = H(f, tau_c)。
  2. src/score/ScoreRenderer.h 的 exciter 字串 -> 硬度檔位對照
     （cimbalomExciterFromString()），與 piano 引擎的覆寫規則
     （exciter "wood_mallet" -> "felt"、strike_position 0.3 -> 0.125）。
  3. src/physics/StringModel.h::calculateModes() 的擊弦點因子 |sin(n*pi*beta)| 與
     src/engines/CimbalomEngine.h 的 spectralTilt 創意層（CLI 路徑 noteOn()），
     組成「理論 n1/n2」——這個比例與 noteComp/gain 無關（整組同乘會消掉）。
  4. --dump-modes 讀檔與逐事件指標（dump 實測值與理論值並列）。

本檔**沒有新增任何物理常數**：所有數字都是從上面列出的原始碼逐字抄來的鏡像，
並在 scan_grid.py 用 CLI 的 --dump-modes 實測值逐格核對（報告 §3）。
下面出現的「-10 dB」之類分界只用在報告的描述性分組，**描述用、非 GATE**。
"""
import json
import math
import os
import subprocess

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
DEFAULT_CLI = os.path.join(REPO, "output", "wf0925", "N1", "cli.exe")

# ---------------------------------------------------------------------------
# 1. HammerImpulse.h 鏡像（常數逐字抄自 src/physics/HammerImpulse.h）
# ---------------------------------------------------------------------------
K_TAU_C = [0.0060, 0.0020, 0.0005, 0.0002]   # Cotton, Felt, Wood, Metal (s)
K_TAU_C_FELT = 0.0020
PIANO_TAUC_MIN = 0.0003
PIANO_TAUC_MAX = 0.0080
K_ALPHA_ANCHOR = [36, 60, 96]
K_HAMMER_K = [4.0e8, 4.5e9, 1.0e12]
K_HAMMER_ALPHA = [2.3, 2.5, 3.0]
MASS_ANCHOR = [24, 36, 48, 60, 72, 84, 96, 108]
MASS_KG = [0.012, 0.011, 0.010, 0.009, 0.008, 0.007, 0.006, 0.005]
HARDNESS_NAME = {0: "Cotton", 1: "Felt", 2: "Wood", 3: "Metal"}

# CimbalomEngine.h getNextSample()/renderNextBlock() 的輸出增益（逐字：`sample * 0.069f`）。
# 只用在把 dump 振幅換算成接近 stem dBFS 的「說明用」位準，換算常數另由 stem 實測校準。
CIMBALOM_OUTPUT_GAIN = 0.069


def clamp(x, lo, hi):
    return lo if x < lo else hi if x > hi else x


def keytrack_scale(midi):
    k = 0.32
    return clamp(2.0 ** (-(midi - 69) * k / 12.0), 0.4, 2.6)


def tauc_for_hardness(h):
    idx = clamp(float(h), 0.0, 3.0)
    lo = int(idx)
    hi = min(lo + 1, 3)
    frac = idx - lo
    return K_TAU_C[lo] + (K_TAU_C[hi] - K_TAU_C[lo]) * frac


def tauc_for_strike(h, v):
    speed = clamp(v, 0.02, 1.0)
    hertz = clamp((0.5 / speed) ** 0.2, 0.8, 1.2)
    return tauc_for_hardness(h) * hertz


def tauc_for_note(h, v, midi):
    return tauc_for_strike(h, v) * keytrack_scale(midi)


def _interp_flat(anchor, values, midi):
    if midi <= anchor[0]:
        return values[0]
    if midi >= anchor[-1]:
        return values[-1]
    seg = 0
    while seg + 2 < len(anchor) and midi >= anchor[seg + 1]:
        seg += 1
    t = (midi - anchor[seg]) / float(anchor[seg + 1] - anchor[seg])
    return values[seg] + (values[seg + 1] - values[seg]) * t


def _alpha(midi):
    return _interp_flat(K_ALPHA_ANCHOR, K_HAMMER_ALPHA, midi)


def _k(midi):
    return 10.0 ** _interp_flat(K_ALPHA_ANCHOR, [math.log10(v) for v in K_HAMMER_K], midi)


def _mass(midi):
    return _interp_flat(MASS_ANCHOR, MASS_KG, midi)


def piano_hammer_g(midi, v):
    a = _alpha(midi)
    inv = 1.0 / (a + 1.0)
    return (_mass(midi) / _k(midi)) ** inv * (v ** (2.0 * inv - 1.0))


def piano_hammer_tauc(midi, v):
    """現行（A14 B-2，2026-09-10 落地）。"""
    v = clamp(v, 0.02, 1.0)
    val = K_TAU_C_FELT * keytrack_scale(midi) * (piano_hammer_g(midi, v) / piano_hammer_g(midi, 0.5))
    return clamp(val, PIANO_TAUC_MIN, PIANO_TAUC_MAX)


def piano_hammer_tauc_b4_before_a14(midi, v):
    """B4 舊版（A14 B-2 之前）。現行渲染不用；只拿來回頭解釋 08-30 的 22 顆舊 FAIL。"""
    v = clamp(v, 0.02, 1.0)
    val = K_TAU_C_FELT * (piano_hammer_g(midi, v) / piano_hammer_g(69, 0.5))
    return clamp(val, PIANO_TAUC_MIN, PIANO_TAUC_MAX)


def tauc_engine(hardness_idx, v, midi, variant="current"):
    """CimbalomEngine.h noteOn()：Felt(==1) 走 pianoHammerTauC()，其餘走 tauCForNote()。"""
    if hardness_idx == 1:
        if variant == "b4_before_a14":
            return piano_hammer_tauc_b4_before_a14(midi, v)
        return piano_hammer_tauc(midi, v)
    return tauc_for_note(float(hardness_idx), v, midi)


def force_spectrum_h(f_hz, tau):
    """forceSpectrumMagnitude(2*pi*f, tau)。x = 2*f*tau；H = |cos(pi*x/2)| / |1 - x^2|。"""
    if tau <= 0.0 or not math.isfinite(f_hz):
        return 1.0
    x = 2.0 * f_hz * tau
    denom = 1.0 - x * x
    if abs(denom) < 1e-4:
        return math.pi * 0.25
    return abs(math.cos(math.pi * x / 2.0) / denom)


def null_info(x):
    """回傳 (最近的零點序號 x=3/5/7..., 零點凹口深度 dB)。

    H(x) 的分子 |cos(pi*x/2)| 在 x=1,3,5,... 為 0，但 x=1 被分母抵消（不是零點，
    HammerImpulse.h 檔頭已註明）；所以只有 x>=2 才談「靠近零點」。
    凹口深度 = 20*log10|cos(pi*x/2)|：基頻因為零點，比旁瓣包絡 1/|1-x^2| 再低多少 dB。
    x<2 回傳 (None, 0.0)。這是描述量，不是判定門檻。"""
    if x is None or not math.isfinite(x) or x < 2.0:
        return None, 0.0
    order = int(2 * math.floor(x / 2.0) + 1)   # [2,4)->3, [4,6)->5, ...
    c = abs(math.cos(math.pi * x / 2.0))
    depth = 20.0 * math.log10(max(c, 1e-12))
    return order, depth


# ---------------------------------------------------------------------------
# 2. ScoreRenderer.h exciter 對照（逐字鏡像 cimbalomExciterFromString()）
# ---------------------------------------------------------------------------
def cimbalom_exciter_hardness(exciter):
    e = exciter
    if e in ("cotton", "cotton_mallet"):
        return 0
    if e in ("felt", "felt_mallet"):
        return 1
    if e in ("metal", "metal_mallet", "metal_hammer"):
        return 3
    if e in ("finger", "finger_tap"):
        return 1
    if e == "bow":
        return 0
    if e in ("hard_plastic", "wood", "wood_mallet", "pluck"):
        return 2
    if e == "rubber_mallet":
        return 1
    if e == "metal_scrape":
        return 3
    if e in ("bow_slow", "brush"):
        return 0
    return 2


def effective_string_params(engine, params):
    """回傳 renderCimbalom() 實際吃到的 (exciter字串, 硬度檔位, strike_position)。
    ScoreParser.h 預設：strike_position=0.3、exciter="wood_mallet"。
    piano 引擎覆寫：wood_mallet->felt、strike 0.3->0.125（ScoreRenderer.h renderEvent()）。
    strike 最後在 CimbalomEngine.h noteOn() 被 clamp 到 [0.05, 0.95]。"""
    params = params or {}
    exciter = params.get("exciter", "wood_mallet")
    strike = float(params.get("strike_position", 0.3))
    if engine == "piano":
        if exciter == "wood_mallet":
            exciter = "felt"
        if strike == 0.3:
            strike = 0.125
    strike = clamp(strike, 0.05, 0.95)
    return exciter, cimbalom_exciter_hardness(exciter), strike


_MATERIALS = None


def material_youngs(name):
    global _MATERIALS
    if _MATERIALS is None:
        with open(os.path.join(REPO, "data", "materials.json"), encoding="utf-8") as f:
            d = json.load(f)
        _MATERIALS = d.get("materials", d)
    m = _MATERIALS.get(name) or _MATERIALS.get("steel")
    return float(m["youngs_modulus"])


def spectral_tilt(material):
    """CimbalomEngine.h：clamp((log10(E)-7.5)/4, 0.1, 1.0)（創意層，原始碼自己標明未溯源）。"""
    return clamp((math.log10(material_youngs(material)) - 7.5) / 4.0, 0.1, 1.0)


# ---------------------------------------------------------------------------
# 3. --dump-modes 與逐事件指標
# ---------------------------------------------------------------------------
def run_dump(cli, score_path, timeout=1800):
    out = subprocess.run([cli, "--dump-modes", score_path], capture_output=True,
                         text=True, encoding="utf-8", errors="replace", timeout=timeout)
    if out.returncode != 0:
        raise RuntimeError("--dump-modes failed for %s (rc=%d):\n%s\n%s"
                           % (score_path, out.returncode, out.stdout[-2000:], out.stderr[-2000:]))
    return json.loads(out.stdout)


def db20(x):
    if x is None or x <= 0.0 or not math.isfinite(x):
        return None
    return 20.0 * math.log10(x)


def dump_strings(ev):
    s = ev.get("strings")
    if s:
        return s
    return [ev.get("partials") or []]


AMP_PRINT_QUANTUM = 0.00001   # dump 的 "amp" 以 %.5f 輸出（ScoreRenderer.h modeToJson）
LOW_PRECISION_AMP = 0.0005    # 小於這個值時，%.5f 四捨五入誤差 >1%——只用來標註，非判定


def event_metrics(ev, velocity, engine, params, variant="current"):
    """一個 --dump-modes 事件 -> 指標 dict。

    dump 側（引擎自己的輸出，本卡不做任何假設）：
      n1_course / n2_course = 同一音所有弦（預設 3 弦）第 1、第 2 個 partial 的 amp 相加
        （起音瞬間各弦同相位 excite()，相加 = 起音時基頻叢的振幅）；
      n1n2_dump_db = 20log10(n1_course/n2_course)；
      n1n2_s0_db   = 只看第 0 根弦（09-25 盤點 triage 檔用的是這個，保留做對照）；
      n1_vs_max_db = 基頻叢 vs 全部 partial 叢裡最強的那一根；
      L1_db        = 20log10(n1_course * velocity)：基頻起音振幅（未乘輸出增益 0.069 與 master_volume）。
    理論側（HammerImpulse.h 鏡像 + dump 的真實 partial 頻率）：
      tau_ms, x1 = 2*f1*tau_c, x2, H1_db, H2_db, null_order, null_depth_db,
      n1n2_theory_db = 各弦 |sin(n*pi*beta)| * tilt^((f_n/f_1-1)*0.2) * H(f_n) 相加後的比。
    """
    strings = dump_strings(ev)
    ns = len(strings)
    ok = ns > 0 and all(len(s) >= 2 for s in strings)
    r = {"n_strings": ns}
    if not ok:
        r["error"] = "fewer than 2 partials"
        return r
    exciter, hidx, beta = effective_string_params(engine, params)
    material = (params or {}).get("material", "steel")
    tilt = spectral_tilt(material)
    midi = int(ev["midi"])
    tau = tauc_engine(hidx, float(velocity), midi, variant)

    n1 = sum(float(s[0]["amp"]) for s in strings)
    n2 = sum(float(s[1]["amp"]) for s in strings)
    kmax = min(len(s) for s in strings)
    course = [sum(float(s[k]["amp"]) for s in strings) for k in range(kmax)]
    nmax = max(course) if course else 0.0
    s0 = strings[0]
    center = strings[ns // 2]
    f1c = float(center[0]["freq"])
    f2c = float(center[1]["freq"])

    th1 = th2 = 0.0
    for s in strings:
        f1 = float(s[0]["freq"])
        f2 = float(s[1]["freq"])
        th1 += abs(math.sin(math.pi * beta)) * force_spectrum_h(f1, tau)
        th2 += (abs(math.sin(2 * math.pi * beta)) * tilt ** ((f2 / f1 - 1.0) * 0.2)
                * force_spectrum_h(f2, tau))

    x1 = 2.0 * f1c * tau
    x2 = 2.0 * f2c * tau
    order, depth = null_info(x1)
    min_amp = min(min(float(s[0]["amp"]), float(s[1]["amp"])) for s in strings)
    r.update({
        "midi": midi, "exciter": exciter, "hardness": HARDNESS_NAME[hidx], "strike": beta,
        "material": material, "tau_ms": tau * 1000.0, "f1_hz": f1c, "f2_hz": f2c,
        "x1": x1, "x2": x2,
        "H1_db": db20(force_spectrum_h(f1c, tau)), "H2_db": db20(force_spectrum_h(f2c, tau)),
        "null_order": order, "null_depth_db": depth,
        "n1_course": n1, "n2_course": n2,
        "n1n2_dump_db": (db20(n1 / n2) if (n1 > 0 and n2 > 0) else None),
        "n1n2_s0_db": (db20(float(s0[0]["amp"]) / float(s0[1]["amp"]))
                        if float(s0[0]["amp"]) > 0 and float(s0[1]["amp"]) > 0 else None),
        "n1_vs_max_db": (db20(n1 / nmax) if (n1 > 0 and nmax > 0) else None),
        "n1n2_theory_db": (db20(th1 / th2) if (th1 > 0 and th2 > 0) else None),
        "L1_db": (db20(n1 * float(velocity)) if n1 > 0 else None),
        "low_precision": min_amp < LOW_PRECISION_AMP,
    })
    return r


NAMES = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']


def midi_to_name(m):
    return NAMES[m % 12] + str(m // 12 - 1)


def midi_hz(m):
    return 440.0 * 2.0 ** ((m - 69) / 12.0)


def fmt(x, nd=3):
    if x is None:
        return ""
    if isinstance(x, bool):
        return "1" if x else "0"
    if isinstance(x, float):
        return ("%." + str(nd) + "f") % x
    return str(x)


CORPUS_ROOTS = ["scores/examples", "scores/classical", "scores/originals/ai_radiance", "scores/library"]


def corpus_files():
    """與 tools/verify_score.py find_all_scores() 同一組根目錄（75 份）。"""
    from pathlib import Path
    out = []
    for r in CORPUS_ROOTS:
        p = Path(REPO) / r
        if p.exists():
            out.extend(sorted(p.rglob("*.score.json")))
    return out


def product_scores():
    """exports/products/clean_batch2/catalog.json 的 score 欄（相對 repo，正斜線）。"""
    path = os.path.join(REPO, "exports", "products", "clean_batch2", "catalog.json")
    with open(path, encoding="utf-8") as f:
        cat = json.load(f)
    out = {}
    for it in cat:
        s = (it.get("score") or "").replace("\\", "/")
        if s:
            out[s] = it.get("id")
    return out
