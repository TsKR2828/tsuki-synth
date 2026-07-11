#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
report_html.py -- ROADMAP_PHYSICS.md Milestone M4 (4a/4b): renders the
single-file, self-contained HTML visual verification report that
verify_score.py's `--html` mode writes.

This module does NOT re-implement any pass/fail judgment. Every checkmark
and tolerance number that decides PASS/FAIL comes from the `Check` objects
verify_score.py already produced (verify_one()). This file only turns
already-computed check results and the already-rendered audio into
pictures: a spectrogram, a predicted-vs-measured f0 strip chart, a loudness
curve, and a phrase/rest timeline -- plus badges and a footer that restate
(never redefine) the ROADMAP_PHYSICS.md Sec.6 tolerance table.

Audience note (see task brief): the end user is deaf. Every claim on this
page must be visual/numeric ("+3.2 cents", a red dot, a shaded rest span),
never "sounds like" or "audibly".

Everything below is a pure function: given data, return a string (HTML/SVG
fragment) or bytes (PNG). No file I/O, no subprocess calls, no network.
That is also what keeps this file's <img>/<a> attributes free of
http(s):// -- every image is a data: URI built in-process.
"""

import base64
import html
import math
import struct
import zlib
from datetime import datetime, timezone

import numpy as np

# ── constants (visualization-only; NEVER the source of truth for PASS/FAIL --
#    see ROADMAP_PHYSICS.md Sec.6, "AI 不得修改本表數值") ───────────────────
F0_CENTS_GREEN = 5.0     # ROADMAP_PHYSICS.md Sec.3 M4 4a: color thresholds
F0_CENTS_YELLOW = 12.0   # for the predicted-vs-measured strip chart
F0_CENTS_CLAMP = 25.0    # display clamp for the y-axis of that chart
F0_WINDOW_S = 0.25       # measurement window per event (task 4a spec)
F0_MIN_FFT = 16384
F0_SEARCH_PCT = 0.03     # +/- 3% search band around the predicted f0
F0_SNR_GUARD_PCT = 0.06  # guard band excluded from the noise-floor estimate
F0_SNR_MIN_DB = 20.0     # below this -> "cannot be measured independently"

SPEC_WINDOW = 2048
SPEC_HOP = 512
SPEC_FLOOR_DB = -90.0
SPEC_FREQ_MAX_HZ = 8000.0
SPEC_MAX_TIME_COLS = 1600

LOUDNESS_HOP_S = 0.05

# ROADMAP_PHYSICS.md Sec.6 tolerance snapshot for display only -- NOT verbatim:
# where Sec.6 lists both a current value and a milestone target (e.g. partial
# amplitude, velocity, rest RMS), this table shows the CURRENTLY ENFORCED
# value that today's checks actually judge against. This is NOT read by any
# check -- nothing here feeds back into pass/fail logic. If Sec.6 ever
# changes, update this list too (display drift is a docs bug, not a GATE
# failure).
TOLERANCE_TABLE_SNAPSHOT = [
    ("f0 誤差 / f0 error", "±12 cents", "±5 cents (M7)", "人耳可辨閾約 5 cents"),
    ("Partial 頻率誤差 / partial freq error", "2–4% (依引擎)", "維持, M7 檢討", "FFT 量測窗解析限制"),
    ("Partial 振幅誤差 / partial amp error", "±3.0 dB (M2)", "維持", "M2 --amps 實測後訂定"),
    ("T60 比值 / T60 ratio", "0.2–5.0 (informational)", "0.5–2.0 判定制 (M5)", "量測法改進後收緊"),
    ("velocity ×2 電平 / velocity x2 level", "+6.0 ± 1.0 dB 判定制", "維持", "振幅正比力的物理律"),
    ("休止區 RMS / rest RMS", "≤ −50 dBFS", "維持", "M3 實測後訂定, 含殘響衰減窗"),
    ("跨引擎等 RMS / cross-engine RMS", "0.2 dB", "維持", "2026-06 校準"),
    ("決定性 / determinism", "SHA256 一致 (同機)", "跨機另訂 (NTH-4)", "—"),
]

_CHECK_LIST_EXPLAIN = [
    ("schema.*", "schema 合法性 / schema sanity (欄位, 排序, MIDI 範圍, 平均律頻率)"),
    ("modes.*", "全事件模態掃描 / whole-score mode scan (空集合, NaN/Inf, 頻率範圍, 衰減常數, f0 偏差)"),
    ("rests.*", "休止實測 / rest verification (渲染音訊 RMS 低於門檻)"),
    ("audio.*", "峰值與削波 / peak & clipping (≤-0.3 dBFS, 無連續削波, 非全零)"),
    ("determinism.*", "決定性 / determinism (兩次渲染 SHA256 一致)"),
]


# ── tiny pure utilities (duplicated on purpose -- see module docstring: this
#    file must stay import-free of verify_score.py to avoid a circular
#    import, since verify_score.py imports THIS module) ─────────────────────
_NOTE_BASE = {"A": 9, "B": 11, "C": 0, "D": 2, "E": 4, "F": 5, "G": 7}


def note_to_midi(note):
    if note is None:
        return None
    if isinstance(note, (int, float)):
        return int(round(note))
    s = str(note).strip()
    if not s:
        return None
    if s[0].isdigit():
        try:
            return int(round(float(s)))
        except ValueError:
            return None
    letter = s[0].upper()
    if letter not in _NOTE_BASE:
        return None
    base = _NOTE_BASE[letter]
    pos = 1
    if pos < len(s) and s[pos] == "#":
        base += 1
        pos += 1
    elif pos < len(s) and s[pos] == "b":
        base -= 1
        pos += 1
    octave_str = s[pos:]
    octave = 4
    if octave_str:
        try:
            octave = int(octave_str)
        except ValueError:
            return None
    return (octave + 1) * 12 + base


def midi_to_hz(midi):
    return 440.0 * 2.0 ** ((midi - 69) / 12.0)


def cents_between(f_measured, f_predicted):
    if f_measured is None or f_predicted is None or f_measured <= 0 or f_predicted <= 0:
        return None
    return 1200.0 * math.log2(f_measured / f_predicted)


def event_predicted_hz(ev):
    """Best-effort predicted fundamental for a score event: prefer the
    authored performance.frequency_hz (what the renderer actually targets),
    fall back to equal temperament from the note name/MIDI number."""
    if not isinstance(ev, dict):
        return None
    perf = ev.get("performance") or {}
    f = perf.get("frequency_hz")
    if isinstance(f, (int, float)) and f > 0:
        return float(f)
    midi = note_to_midi(ev.get("note"))
    if midi is None:
        return None
    return midi_to_hz(midi)


def esc(s):
    return html.escape("" if s is None else str(s), quote=True)


# ── pure-stdlib PNG encoder (8-bit RGB, single IDAT, filter type 0) ─────────
def _png_chunk(tag, data):
    return (struct.pack(">I", len(data)) + tag + data +
            struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF))


def encode_png_rgb(width, height, rgb_bytes):
    """rgb_bytes: exactly width*height*3 bytes, row-major, top row first."""
    assert len(rgb_bytes) == width * height * 3, (
        f"encode_png_rgb: expected {width * height * 3} bytes, got {len(rgb_bytes)}")
    sig = b"\x89PNG\r\n\x1a\n"
    ihdr = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)  # 8-bit, RGB
    stride = width * 3
    raw = bytearray((stride + 1) * height)
    for y in range(height):
        row_off = y * (stride + 1)
        raw[row_off] = 0  # filter type 0 = None
        raw[row_off + 1: row_off + 1 + stride] = rgb_bytes[y * stride:(y + 1) * stride]
    idat = zlib.compress(bytes(raw), 6)
    return sig + _png_chunk(b"IHDR", ihdr) + _png_chunk(b"IDAT", idat) + _png_chunk(b"IEND", b"")


def png_data_uri(width, height, rgb_bytes):
    png = encode_png_rgb(width, height, rgb_bytes)
    return "data:image/png;base64," + base64.b64encode(png).decode("ascii")


# ── hardcoded 16-step viridis-like colormap (RGB 0-255), linearly
#    interpolated to a 256-entry LUT for fast vectorized lookup ────────────
VIRIDIS16 = [
    (68, 1, 84), (72, 26, 108), (71, 47, 125), (65, 68, 135),
    (57, 86, 140), (49, 104, 142), (42, 120, 142), (35, 136, 142),
    (31, 152, 139), (34, 168, 132), (53, 183, 121), (84, 197, 104),
    (122, 209, 81), (165, 219, 54), (210, 226, 27), (253, 231, 37),
]


def _build_viridis_lut():
    n = len(VIRIDIS16) - 1
    lut = np.zeros((256, 3), dtype=np.uint8)
    stops = np.array(VIRIDIS16, dtype=np.float64)
    for i in range(256):
        pos = (i / 255.0) * n
        i0 = int(math.floor(pos))
        i1 = min(i0 + 1, n)
        frac = pos - i0
        lut[i] = np.round(stops[i0] + (stops[i1] - stops[i0]) * frac).astype(np.uint8)
    return lut


VIRIDIS_LUT = _build_viridis_lut()


# ── section 2: spectrogram ──────────────────────────────────────────────────
def compute_spectrogram(sr, mono, window=SPEC_WINDOW, hop=SPEC_HOP,
                         floor_db=SPEC_FLOOR_DB, freq_max=SPEC_FREQ_MAX_HZ,
                         max_time_cols=SPEC_MAX_TIME_COLS):
    """Returns dict with: rgb_bytes, width, height, duration_s, freq_max_hz
    (actual, clamped to Nyquist), n_frames_raw. STFT with a Hann window,
    dB magnitude relative to the whole spectrogram's own peak, floored at
    `floor_db`. Time axis is downsampled (mean-pooled in linear magnitude,
    not in dB) to at most `max_time_cols` columns if the raw STFT has more
    frames than that."""
    n = len(mono)
    if n < window:
        mono = np.pad(mono, (0, window - n))
        n = len(mono)
    duration_s = n / sr if sr else 0.0
    freq_max = min(freq_max, sr / 2.0) if sr else freq_max

    win = np.hanning(window)
    n_frames = 1 + (n - window) // hop
    if n_frames < 1:
        n_frames = 1
    from numpy.lib.stride_tricks import sliding_window_view
    usable = (n_frames - 1) * hop + window
    frames = sliding_window_view(mono[:usable], window)[::hop, :]  # (n_frames, window)
    frames = frames * win[np.newaxis, :]
    spec = np.abs(np.fft.rfft(frames, axis=1))  # (n_frames, window//2+1)
    freqs = np.fft.rfftfreq(window, d=1.0 / sr) if sr else np.arange(spec.shape[1])
    keep = freqs <= freq_max
    mags = spec[:, keep]  # (n_frames, n_bins)

    # time-axis downsample (mean-pool in linear magnitude)
    if n_frames > max_time_cols:
        edges = np.linspace(0, n_frames, max_time_cols + 1).astype(int)
        pooled = np.zeros((max_time_cols, mags.shape[1]), dtype=np.float64)
        for i in range(max_time_cols):
            a, b = edges[i], max(edges[i] + 1, edges[i + 1])
            pooled[i] = mags[a:b].mean(axis=0)
        mags = pooled

    peak = float(mags.max()) if mags.size else 1.0
    ref = peak if peak > 0 else 1.0
    with np.errstate(divide="ignore"):
        db = 20.0 * np.log10(np.maximum(mags / ref, 10 ** (floor_db / 20.0)))
    db = np.clip(db, floor_db, 0.0)

    # image: row 0 = highest frequency (top), last row = 0 Hz (bottom);
    # column = time, left to right.
    db_img = db.T[::-1, :]  # (n_bins, n_time) with row0 = highest freq
    norm = (db_img - floor_db) / (0.0 - floor_db)
    norm = np.clip(norm, 0.0, 1.0)
    idx = np.round(norm * 255.0).astype(np.uint8)
    rgb = VIRIDIS_LUT[idx]  # (n_bins, n_time, 3)
    height, width = rgb.shape[0], rgb.shape[1]
    rgb_bytes = np.ascontiguousarray(rgb, dtype=np.uint8).tobytes()

    return {
        "rgb_bytes": rgb_bytes, "width": width, "height": height,
        "duration_s": duration_s, "freq_max_hz": freq_max,
        "n_frames_raw": n_frames, "floor_db": floor_db,
    }


def render_spectrogram_section(sr, mono):
    spec = compute_spectrogram(sr, mono)
    uri = png_data_uri(spec["width"], spec["height"], spec["rgb_bytes"])
    dur = spec["duration_s"]
    fmax_khz = spec["freq_max_hz"] / 1000.0

    n_xticks = 6
    xticks = []
    for i in range(n_xticks + 1):
        t = dur * i / n_xticks
        pct = 100.0 * i / n_xticks
        xticks.append(f'<div class="axis-tick" style="left:{pct:.3f}%">{t:.1f}s</div>')

    n_yticks = 4
    yticks = []
    for i in range(n_yticks + 1):
        f_khz = fmax_khz * i / n_yticks
        pct_from_top = 100.0 * (1.0 - i / n_yticks)
        yticks.append(f'<div class="axis-tick-y" style="top:{pct_from_top:.3f}%">{f_khz:.1f}k</div>')

    return f"""
<section class="card">
  <h2>2. 全曲頻譜圖 <span class="en">Spectrogram (whole rendered mix)</span></h2>
  <p class="hint">STFT, window 2048 / hop 512 (Hann), dB floor {spec['floor_db']:.0f} dB,
     linear frequency axis 0–{fmax_khz:.1f} kHz, viridis-like colormap
     ({spec['n_frames_raw']} STFT frame(s) → {spec['width']} display column(s)).</p>
  <div class="specgram-wrap">
    <div class="specgram-yaxis">{''.join(yticks)}</div>
    <div class="specgram-img-container">
      <img src="{uri}" width="{spec['width']}" height="{spec['height']}"
           alt="spectrogram" class="specgram-img"/>
    </div>
  </div>
  <div class="specgram-xaxis-row"><div class="specgram-xaxis-spacer"></div>
    <div class="specgram-xaxis">{''.join(xticks)}</div>
  </div>
</section>
"""


# ── section 3: per-event predicted vs measured f0 (the verification core) ──
def _spectrum_and_noise(seg, sr, predicted_hz, min_fft=F0_MIN_FFT):
    win = np.hanning(len(seg))
    N = 1
    target = max(min_fft, len(seg))
    while N < target:
        N <<= 1
    spec = np.abs(np.fft.rfft(seg * win, N))
    binhz = sr / N
    lo, hi = predicted_hz * (1 - F0_SEARCH_PCT), predicted_hz * (1 + F0_SEARCH_PCT)
    klo = max(1, int(lo / binhz))
    khi = min(len(spec) - 1, int(hi / binhz) + 1)
    return spec, binhz, klo, khi


def measure_event_f0(mono, sr, t_start, predicted_hz, duration_s, window_s=F0_WINDOW_S):
    """Measures f0 in a `window_s` Hann window starting at `t_start`
    (clamped to the file). FFT >= F0_MIN_FFT, zero-padded, parabolic peak
    interpolation, search band = predicted_hz +/- F0_SEARCH_PCT. Returns a
    dict; see HONESTY RULE in the module docstring / task brief -- a low-SNR
    window returns status="weak" with no numeric cents, never a guessed
    number."""
    result = {"predicted_hz": predicted_hz, "measured_hz": None, "cents": None,
              "snr_db": None, "status": "gray", "reason": None}
    if predicted_hz is None or predicted_hz <= 0:
        result["reason"] = "無法從 note/frequency_hz 推得預測頻率"
        return result

    n = len(mono)
    start_i = max(0, int(round(t_start * sr)))
    end_i = min(n, int(round((t_start + window_s) * sr)))
    result["window_s"] = [start_i / sr if sr else 0.0, end_i / sr if sr else 0.0]
    if end_i - start_i < 512:
        result["reason"] = "量測窗被檔案結尾截斷過短 (< 512 samples)"
        return result

    seg = mono[start_i:end_i]
    spec, binhz, klo, khi = _spectrum_and_noise(seg, sr, predicted_hz)
    if khi <= klo:
        result["reason"] = "搜尋頻段超出 FFT 可用範圍"
        return result

    k = klo + int(np.argmax(spec[klo:khi]))
    if k <= klo or k >= khi - 1:
        # The loudest bin inside the +/-3% search band sits right at the
        # band's edge -- i.e. no interior local maximum was found, so the
        # true spectral peak is either exactly at the boundary or (more
        # likely for low fundamentals, where the FFT's own frequency
        # resolution at F0_MIN_FFT can be coarser than the +/-3% band
        # itself) actually OUTSIDE the band we were honest enough to
        # declare. Extrapolating a parabola through a neighbor bin that
        # lies outside the declared search band would silently smuggle in
        # a number the HONESTY RULE says we shouldn't report -- see the
        # regression this guards against: a 69.3 Hz water_gong event whose
        # true peak sat one bin past khi produced a fabricated +75 cent
        # "measurement" before this check existed.
        result["snr_db"] = None
        result["measured_hz"] = None
        result["reason"] = ("搜尋頻段內找不到內部峰值 (最大值落在頻段邊界) -- 真正的峰值可能"
                             "在宣告的 ±3% 頻段之外，拒絕外推假數字"
                             " / no interior peak inside the +/-3% search band")
        return result
    a = spec[max(k - 1, 0)]
    b = spec[k]
    c = spec[min(k + 1, len(spec) - 1)]
    d = a - 2 * b + c
    delta = 0.5 * (a - c) / d if abs(d) > 1e-12 else 0.0
    measured_hz = (k + delta) * binhz
    peak_mag = float(b)

    guard_lo = predicted_hz * (1 - F0_SNR_GUARD_PCT)
    guard_hi = predicted_hz * (1 + F0_SNR_GUARD_PCT)
    gklo = max(1, int(guard_lo / binhz))
    gkhi = min(len(spec) - 1, int(guard_hi / binhz) + 1)
    mask = np.ones(len(spec), dtype=bool)
    mask[0:1] = False
    mask[gklo:gkhi] = False
    upper_bin = min(len(spec) - 1, int(SPEC_FREQ_MAX_HZ / binhz))
    mask[upper_bin + 1:] = False
    noise_vals = spec[mask]
    noise_med = float(np.median(noise_vals)) if noise_vals.size else 0.0
    snr_db = (20.0 * math.log10(peak_mag / noise_med)
              if (noise_med > 1e-12 and peak_mag > 0) else 120.0)
    result["snr_db"] = snr_db
    result["measured_hz"] = measured_hz

    if snr_db < F0_SNR_MIN_DB:
        result["status"] = "gray"
        result["reason"] = f"視窗峰值 SNR {snr_db:.1f} dB < {F0_SNR_MIN_DB:.0f} dB 門檻 (訊號太弱)"
        return result

    result["cents"] = cents_between(measured_hz, predicted_hz)
    result["status"] = "measured"
    return result


def _time_sorted_spans(events):
    spans = []
    for i, ev in enumerate(events):
        if not isinstance(ev, dict):
            continue
        t, d = ev.get("time"), ev.get("duration")
        if t is None or d is None:
            continue
        spans.append((float(t), float(t) + max(float(d), 0.0), i))
    spans.sort()
    return spans


def detect_collision(sorted_spans, dumped_map, events, subject_idx, win_start, win_end, predicted_hz):
    """True if some OTHER simultaneously-sounding event has a partial (from
    --dump-modes for modal engines, or an approximate harmonic series for
    non-modal/FM events) landing inside the subject's own search band --
    collisions are computed from the score itself, per the task's HONESTY
    RULE. `sorted_spans` is time-sorted so the scan can stop once a
    candidate event starts at/after `win_end` (no later event can overlap
    either, since spans are sorted by start time)."""
    search_lo = predicted_hz * (1 - F0_SEARCH_PCT)
    search_hi = predicted_hz * (1 + F0_SEARCH_PCT)
    for j_start, j_end, j in sorted_spans:
        if j_start >= win_end:
            break
        if j == subject_idx or j_end <= win_start:
            continue
        dumped = dumped_map.get(j)
        if dumped is not None:
            for p in dumped.get("partials", []):
                f = p.get("freq")
                if isinstance(f, (int, float)) and search_lo <= f <= search_hi:
                    return True, j
        else:
            f0j = event_predicted_hz(events[j]) if 0 <= j < len(events) else None
            if f0j:
                for n in range(1, 9):
                    f = f0j * n
                    if search_lo <= f <= search_hi:
                        return True, j
    return False, None


def build_f0_events(events, dumped_map, mono, sr, duration_s):
    """Returns a list of per-event dicts (one per score event with a
    resolvable time/predicted frequency) carrying everything the strip
    chart and worst-10 table need."""
    sorted_spans = _time_sorted_spans(events)
    out = []
    for i, ev in enumerate(events):
        if not isinstance(ev, dict):
            continue
        t0 = ev.get("time")
        if t0 is None:
            continue
        t0 = float(t0)
        predicted_hz = event_predicted_hz(ev)
        note_name = ev.get("note")
        engine = ev.get("engine")
        win_end = min(t0 + F0_WINDOW_S, duration_s)

        entry = {"index": i, "time": t0, "note": note_name, "engine": engine,
                 "predicted_hz": predicted_hz, "measured_hz": None,
                 "cents": None, "status": "gray", "reason": None, "snr_db": None}

        if predicted_hz is None:
            entry["reason"] = "無法解析 note/frequency_hz"
            out.append(entry)
            continue
        if t0 >= duration_s:
            entry["reason"] = "事件起始時間超出渲染音檔長度"
            out.append(entry)
            continue

        collided, other = detect_collision(sorted_spans, dumped_map, events, i, t0, win_end, predicted_hz)
        if collided:
            other_note = events[other].get("note") if 0 <= other < len(events) else "?"
            entry["reason"] = f"碰撞: 事件 #{other} ({esc(other_note)}) 的泛音落在搜尋頻段內"
            out.append(entry)
            continue

        m = measure_event_f0(mono, sr, t0, predicted_hz, duration_s)
        entry["measured_hz"] = m["measured_hz"]
        entry["snr_db"] = m["snr_db"]
        if m["status"] == "measured":
            entry["status"] = "measured"
            entry["cents"] = m["cents"]
        else:
            entry["reason"] = m["reason"]
        out.append(entry)
    return out


def _cents_color(cents):
    a = abs(cents)
    if a <= F0_CENTS_GREEN:
        return "#2e7d32"
    if a <= F0_CENTS_YELLOW:
        return "#f9a825"
    return "#c62828"


def render_f0_section(f0_events, duration_s):
    W, H = 1100, 320
    pad_l, pad_r, pad_t, pad_b = 56, 16, 16, 28
    plot_w = W - pad_l - pad_r
    plot_h = H - pad_t - pad_b
    dur = max(duration_s, 1e-6)

    def xf(t):
        return pad_l + (t / dur) * plot_w

    def yf(cents):
        c = max(-F0_CENTS_CLAMP, min(F0_CENTS_CLAMP, cents))
        return pad_t + (1.0 - (c + F0_CENTS_CLAMP) / (2 * F0_CENTS_CLAMP)) * plot_h

    grid_lines = []
    for c in (-F0_CENTS_CLAMP, -F0_CENTS_YELLOW, -F0_CENTS_GREEN, 0, F0_CENTS_GREEN, F0_CENTS_YELLOW, F0_CENTS_CLAMP):
        y = yf(c)
        grid_lines.append(f'<line x1="{pad_l}" y1="{y:.1f}" x2="{W - pad_r}" y2="{y:.1f}" '
                           f'class="{"gridline-zero" if c == 0 else "gridline"}"/>')
        grid_lines.append(f'<text x="{pad_l - 6}" y="{y + 4:.1f}" class="axis-label" text-anchor="end">{c:+.0f}c</text>')

    points = []
    gray_n = measured_n = 0
    for e in f0_events:
        x = xf(e["time"])
        if e["status"] == "measured" and e["cents"] is not None:
            measured_n += 1
            y = yf(e["cents"])
            color = _cents_color(e["cents"])
            title = (f"#{e['index']} {esc(e['note'])} ({esc(e['engine'])})\n"
                     f"predicted {e['predicted_hz']:.2f} Hz, measured {e['measured_hz']:.2f} Hz\n"
                     f"{e['cents']:+.2f} cents, SNR {e['snr_db']:.1f} dB")
            points.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="4" fill="{color}" stroke="#111" '
                           f'stroke-width="0.5"><title>{esc(title)}</title></circle>')
        else:
            gray_n += 1
            y = yf(0)
            title = (f"#{e['index']} {esc(e['note'])} ({esc(e['engine'])})\n"
                     f"predicted {e['predicted_hz'] if e['predicted_hz'] else '?'} Hz\n"
                     f"無法独立量測: {esc(e['reason'])}")
            points.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="3.5" fill="#9e9e9e" stroke="#555" '
                           f'stroke-width="0.5" opacity="0.85"><title>{esc(title)}</title></circle>')

    n_xticks = 6
    xticks_svg = []
    for i in range(n_xticks + 1):
        t = dur * i / n_xticks
        x = xf(t)
        xticks_svg.append(f'<text x="{x:.1f}" y="{H - 8}" class="axis-label" text-anchor="middle">{t:.1f}s</text>')

    svg = f"""<svg viewBox="0 0 {W} {H}" class="f0-chart" role="img"
       aria-label="predicted vs measured f0 deviation per event">
    {''.join(grid_lines)}
    {''.join(xticks_svg)}
    {''.join(points)}
  </svg>"""

    worst = sorted([e for e in f0_events if e["status"] == "measured"],
                    key=lambda e: -abs(e["cents"]))[:10]
    rows = []
    for e in worst:
        color = _cents_color(e["cents"])
        rows.append(f"""<tr>
        <td>{e['index']}</td><td>{e['time']:.2f}s</td><td>{esc(e['note'])}</td><td>{esc(e['engine'])}</td>
        <td>{e['predicted_hz']:.2f}</td><td>{e['measured_hz']:.2f}</td>
        <td style="color:{color};font-weight:600">{e['cents']:+.2f}</td>
        <td>{e['snr_db']:.1f}</td></tr>""")
    if not rows:
        rows.append('<tr><td colspan="8" class="hint">沒有可獨立量測的事件 (皆為碰撞或訊號太弱)。'
                     '<span class="en">No independently-measurable events (all collided or weak).</span></td></tr>')

    return f"""
<section class="card">
  <h2>3. 每事件 f0：預測 vs 實測 <span class="en">Per-event predicted vs measured f0
      (verification core)</span></h2>
  <p class="hint">250 ms Hann 量測窗，FFT ≥ 16384 zero-padded，拋物線峰值內插，
     搜尋頻段 = 預測 f0 ± 3%。綠 ≤{F0_CENTS_GREEN:.0f} cents / 黃 ≤{F0_CENTS_YELLOW:.0f} cents
     / 紅 &gt;{F0_CENTS_YELLOW:.0f} cents（此為顯示用色階，非 GATE 容差 — 見頁尾容差表）。
     灰點 = 訊號碰撞或太弱，誠實標示「無法獨立量測」而非造假數字。
     {measured_n} 個事件可量測，{gray_n} 個標示為無法獨立量測。</p>
  <div class="f0-chart-wrap">{svg}</div>
  <table class="data-table">
    <thead><tr><th>#</th><th>time</th><th>note</th><th>engine</th>
      <th>predicted Hz</th><th>measured Hz</th><th>cents</th><th>SNR dB</th></tr></thead>
    <tbody>{''.join(rows)}</tbody>
  </table>
  <p class="hint">最大偏差前 10 名（僅列可獨立量測的事件）
     <span class="en">worst 10 deviations (measurable events only)</span>.</p>
</section>
"""


# ── section 4: loudness curve + rest verification shading ──────────────────
def compute_loudness_curve(sr, mono, hop_s=LOUDNESS_HOP_S):
    hop = max(1, int(round(hop_s * sr)))
    n = len(mono)
    pts = []
    for start in range(0, max(n, 1), hop):
        seg = mono[start:start + hop]
        if seg.size == 0:
            continue
        rms = float(np.sqrt(np.mean(seg.astype(np.float64) ** 2)))
        db = 20.0 * math.log10(rms) if rms > 1e-9 else -120.0
        t_center = (start + seg.size / 2.0) / sr if sr else 0.0
        pts.append((t_center, max(db, -120.0)))
    return pts


def _rest_status_color(status):
    return {"pass": "#2e7d32", "exempt": "#f9a825", "fail": "#c62828"}.get(status, "#9e9e9e")


def render_loudness_section(loud_pts, duration_s, rest_intervals):
    """`rest_intervals`: list of dicts {start, end, level_dbfs, status}
    where status in {"pass","exempt","fail"} -- see check_rests()'s
    "intervals" detail, which this function only draws, never recomputes."""
    W, H = 1100, 260
    pad_l, pad_r, pad_t, pad_b = 56, 16, 16, 28
    plot_w = W - pad_l - pad_r
    plot_h = H - pad_t - pad_b
    dur = max(duration_s, 1e-6)
    y_lo, y_hi = -80.0, 0.0

    def xf(t):
        return pad_l + (t / dur) * plot_w

    def yf(db):
        d = max(y_lo, min(y_hi, db))
        return pad_t + (1.0 - (d - y_lo) / (y_hi - y_lo)) * plot_h

    rest_rects = []
    rest_marks = []
    for r in rest_intervals:
        x0, x1 = xf(r["start"]), xf(r["end"])
        color = _rest_status_color(r["status"])
        rest_rects.append(f'<rect x="{x0:.1f}" y="{pad_t}" width="{max(x1 - x0, 1):.1f}" '
                           f'height="{plot_h}" fill="{color}" opacity="0.15"/>')
        mark = {"pass": "✓", "exempt": "✓(豁免)", "fail": "✗"}.get(r["status"], "?")
        mx = (x0 + x1) / 2.0
        title = f"rest {r['start']:.2f}s-{r['end']:.2f}s, RMS {r['level_dbfs']:.1f} dBFS ({r['status']})"
        rest_marks.append(f'<text x="{mx:.1f}" y="{pad_t + 14}" text-anchor="middle" '
                           f'fill="{color}" font-weight="700" font-size="13">{mark}'
                           f'<title>{esc(title)}</title></text>')

    poly_pts = " ".join(f"{xf(t):.1f},{yf(db):.1f}" for t, db in loud_pts)
    grid = []
    for db in (0, -20, -40, -60, -80):
        y = yf(db)
        grid.append(f'<line x1="{pad_l}" y1="{y:.1f}" x2="{W - pad_r}" y2="{y:.1f}" class="gridline"/>')
        grid.append(f'<text x="{pad_l - 6}" y="{y + 4:.1f}" class="axis-label" text-anchor="end">{db:.0f}</text>')
    n_xticks = 6
    xticks = []
    for i in range(n_xticks + 1):
        t = dur * i / n_xticks
        xticks.append(f'<text x="{xf(t):.1f}" y="{H - 8}" class="axis-label" text-anchor="middle">{t:.1f}s</text>')

    svg = f"""<svg viewBox="0 0 {W} {H}" class="loudness-chart" role="img"
       aria-label="RMS loudness over time with rest verification">
    {''.join(rest_rects)}
    {''.join(grid)}
    <polyline points="{poly_pts}" fill="none" stroke="#3b6fd6" stroke-width="1.6"/>
    {''.join(rest_marks)}
    {''.join(xticks)}
  </svg>"""

    legend = ('<span class="legend-item"><span class="swatch" style="background:#2e7d32"></span>'
              '休止通過 rest pass ✓</span>'
              '<span class="legend-item"><span class="swatch" style="background:#f9a825"></span>'
              '休止豁免 rest exempt ✓(豁免)</span>'
              '<span class="legend-item"><span class="swatch" style="background:#c62828"></span>'
              '休止失敗 rest fail ✗</span>')

    return f"""
<section class="card">
  <h2>4. 響度曲線 <span class="en">Loudness curve (RMS, 50 ms hops)</span></h2>
  <p class="hint">陰影區間 = 休止 (rest) 區間，顏色對應該休止的驗證結果
     （見 check "rests.rms_below_limit"）；標記符號畫在區間中央。</p>
  <div class="legend-row">{legend}</div>
  <div class="loudness-chart-wrap">{svg}</div>
</section>
"""


# ── section 5: phrases/rests structural timeline ───────────────────────────
_TRACK_PALETTE = ["#3b6fd6", "#8e5fd6", "#2e9e6b", "#d68c3b", "#d64f6f", "#4f9fd6", "#a0a03b"]


def render_phrases_section(score, events, duration_s):
    phrases = score.get("phrases")
    rests_meta = score.get("rests")
    W = 1100
    row_h = 22
    pad_l, pad_r, pad_t = 120, 16, 10
    dur = max(duration_s, 1e-6)
    plot_w = W - pad_l - pad_r

    def xf(t):
        return pad_l + (min(max(t, 0.0), dur) / dur) * plot_w

    if phrases or rests_meta:
        tracks = []
        seen = set()
        for p in (phrases or []):
            k = p.get("track") or p.get("role") or "?"
            if k not in seen:
                seen.add(k)
                tracks.append(k)
        for r in (rests_meta or []):
            k = r.get("track") or r.get("role") or "?"
            if k not in seen:
                seen.add(k)
                tracks.append(k)
        track_row = {t: i for i, t in enumerate(tracks)}
        H = pad_t + row_h * len(tracks) + 24

        bars = []
        for i, t in enumerate(tracks):
            y = pad_t + i * row_h
            color = _TRACK_PALETTE[i % len(_TRACK_PALETTE)]
            bars.append(f'<text x="4" y="{y + row_h * 0.65:.1f}" class="axis-label">{esc(t)}</text>')
            bars.append(f'<line x1="{pad_l}" y1="{y + row_h * 0.5:.1f}" x2="{W - pad_r}" '
                        f'y2="{y + row_h * 0.5:.1f}" class="gridline"/>')
        for p in (phrases or []):
            k = p.get("track") or p.get("role") or "?"
            row = track_row.get(k, 0)
            y = pad_t + row * row_h
            x0, x1 = xf(p.get("start", 0.0)), xf(p.get("end", 0.0))
            title = f"phrase #{p.get('number','?')} {p.get('start',0):.2f}s-{p.get('end',0):.2f}s"
            bars.append(f'<rect x="{x0:.1f}" y="{y + 3:.1f}" width="{max(x1 - x0, 1):.1f}" '
                        f'height="{row_h - 8:.1f}" fill="{_TRACK_PALETTE[row % len(_TRACK_PALETTE)]}" '
                        f'opacity="0.75" rx="2"><title>{esc(title)}</title></rect>')
        for r in (rests_meta or []):
            k = r.get("track") or r.get("role") or "?"
            row = track_row.get(k, 0)
            y = pad_t + row * row_h
            t0 = r.get("time", 0.0)
            t1 = t0 + r.get("duration", 0.0)
            x0, x1 = xf(t0), xf(t1)
            kind = r.get("kind", "rest")
            title = f"{kind} {t0:.2f}s-{t1:.2f}s"
            bars.append(f'<rect x="{x0:.1f}" y="{y + 7:.1f}" width="{max(x1 - x0, 1):.1f}" '
                        f'height="{row_h - 16:.1f}" fill="#cccccc" opacity="0.9" rx="1"'
                        f'><title>{esc(title)}</title></rect>')

        svg = f'<svg viewBox="0 0 {W} {H}" class="phrase-chart" role="img" ' \
              f'aria-label="phrase and rest timeline">{"".join(bars)}</svg>'
        source_note = ("讀取 score 的 \"phrases\"/\"rests\" 欄位繪製。"
                        "<span class=\"en\">drawn from the score's phrases/rests fields.</span>")
    else:
        # fallback: merged event-activity timeline (say which -- task 4a spec)
        spans = []
        for ev in events:
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
        H = pad_t + row_h + 24
        y = pad_t
        bars = [f'<text x="4" y="{y + row_h * 0.65:.1f}" class="axis-label">events</text>',
                f'<line x1="{pad_l}" y1="{y + row_h * 0.5:.1f}" x2="{W - pad_r}" '
                f'y2="{y + row_h * 0.5:.1f}" class="gridline"/>']
        for s, e in merged:
            x0, x1 = xf(s), xf(e)
            bars.append(f'<rect x="{x0:.1f}" y="{y + 3:.1f}" width="{max(x1 - x0, 1):.1f}" '
                        f'height="{row_h - 8:.1f}" fill="#3b6fd6" opacity="0.75" rx="2">'
                        f'<title>sounding {s:.2f}s-{e:.2f}s</title></rect>')
        svg = f'<svg viewBox="0 0 {W} {H}" class="phrase-chart" role="img" ' \
              f'aria-label="merged event activity timeline">{"".join(bars)}</svg>'
        source_note = ("此 score 沒有 \"phrases\"/\"rests\" 欄位，改繪合併後的事件發聲時間軸。"
                        "<span class=\"en\">no phrases/rests fields on this score -- showing the "
                        "merged event-activity timeline instead.</span>")

    return f"""
<section class="card">
  <h2>5. 樂句／休止結構 <span class="en">Phrases / rests structure</span></h2>
  <p class="hint">{source_note}</p>
  <div class="phrase-chart-wrap">{svg}</div>
</section>
"""


# ── section 1: summary badges ───────────────────────────────────────────────
_FAMILY_ORDER = ["schema", "modes", "rests", "peak", "determinism"]
_FAMILY_LABELS = {
    "schema": "Schema", "modes": "Modes", "rests": "Rests",
    "peak": "Peak/Clip", "determinism": "Determinism",
}


def _family_of(check_name):
    if check_name.startswith("modes."):
        return "modes"
    if check_name.startswith("rests."):
        return "rests"
    if check_name.startswith("audio."):
        return "peak"
    if check_name.startswith("determinism."):
        return "determinism"
    # file.*, schema.*, render.* -- foundational validity, bucketed with schema
    return "schema"


def _badge_html(label, status, sublabel=""):
    color = {"PASS": "#2e7d32", "FAIL": "#c62828", "EXEMPT": "#f9a825"}[status]
    sub = f'<div class="badge-sub">{sublabel}</div>' if sublabel else ""
    return f"""<div class="badge" style="border-color:{color}">
      <div class="badge-label">{esc(label)}</div>
      <div class="badge-status" style="color:{color}">{status}</div>{sub}
    </div>"""


def render_badges_section(score_path, ok, checks, exempt_count, measured=None):
    families = {f: {"total": 0, "fail": 0, "exempt": 0} for f in _FAMILY_ORDER}
    for c in checks:
        fam = _family_of(c.name)
        families[fam]["total"] += 1
        if c.exempt_reason:
            families[fam]["exempt"] += 1
        elif not c.ok:
            families[fam]["fail"] += 1

    badges = []
    for fam in _FAMILY_ORDER:
        d = families[fam]
        if d["total"] == 0:
            continue
        if d["fail"] > 0:
            status = "FAIL"
        elif d["exempt"] > 0:
            status = "EXEMPT"
        else:
            status = "PASS"
        badges.append(_badge_html(_FAMILY_LABELS[fam], status, f"{d['total']} check(s)"))

    overall_status = "PASS" if ok else "FAIL"
    overall_color = {"PASS": "#2e7d32", "FAIL": "#c62828"}[overall_status]
    exempt_note = (f'<div class="banner-sub">（含 {exempt_count} 項已登記豁免 '
                    f'registered exemption(s)）</div>' if exempt_count else "")

    # Whole-file numeric stats (duration/peak/RMS), sourced from the same
    # `measured` dict verify_one() already computed -- see audience note in
    # this module's docstring: every quality claim must be VISUAL and
    # NUMERIC (the deaf end user cannot rely on "sounds fine"), so the peak
    # and RMS numbers a sighted/hearing reviewer would get from the console
    # output must also be printed here, not just folded into a PASS badge.
    stats_line = ""
    if measured:
        dur = measured.get("duration_s")
        peak = measured.get("peak_dbfs")
        rms = measured.get("rms_dbfs")
        if dur is not None and peak is not None and rms is not None:
            stats_line = (f'<div class="banner-stats">'
                           f'渲染長度 duration: <b>{dur:.2f}s</b> &middot; '
                           f'峰值 peak: <b>{peak:.2f} dBFS</b> &middot; '
                           f'全曲 RMS: <b>{rms:.2f} dBFS</b>'
                           f'</div>')

    return f"""
<section class="card banner-card" style="border-color:{overall_color}">
  <div class="banner-row">
    <div class="banner-main" style="color:{overall_color}">{overall_status}</div>
    <div class="banner-text">
      <div class="banner-title">1. 總體驗證結果 <span class="en">Overall verification result</span></div>
      <div class="banner-score-path">{esc(score_path)}</div>
      {exempt_note}
      {stats_line}
      <div class="banner-exit">exit code: <b>{0 if ok else 1}</b>
        &mdash; 0 = 全部檢查通過 (with any registered exemptions) / all checks passed;
        1 = 一項以上檢查失敗 / one or more checks failed.</div>
    </div>
  </div>
  <div class="badge-row">{''.join(badges)}</div>
</section>
"""


# ── section 6: footer ───────────────────────────────────────────────────────
def render_footer_section(score_path, checks, exemptions_applied, tool_name="verify_score.py --html (M4)"):
    seen_names = []
    for c in checks:
        if c.name not in seen_names:
            seen_names.append(c.name)
    check_list_rows = "".join(
        f"<tr><td><code>{esc(prefix)}</code></td><td>{esc(desc)}</td></tr>"
        for prefix, desc in _CHECK_LIST_EXPLAIN)

    tol_rows = "".join(
        f"<tr><td>{esc(name)}</td><td>{esc(cur)}</td><td>{esc(target)}</td><td>{esc(basis)}</td></tr>"
        for name, cur, target, basis in TOLERANCE_TABLE_SNAPSHOT)

    if exemptions_applied:
        exempt_rows = "".join(
            f"<tr><td><code>{esc(c.name)}</code></td><td>{esc(c.exempt_reason)}</td></tr>"
            for c in exemptions_applied)
        exempt_block = f"""<table class="data-table">
        <thead><tr><th>check</th><th>reason</th></tr></thead>
        <tbody>{exempt_rows}</tbody></table>"""
    else:
        exempt_block = '<p class="hint">此檔案未套用任何豁免。<span class="en">No exemptions applied.</span></p>'

    ts = datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")

    return f"""
<section class="card">
  <h2>6. 頁尾 <span class="en">Footer</span></h2>
  <h3>本工具檢查項目 <span class="en">verify_score.py's own check list</span></h3>
  <table class="data-table"><thead><tr><th>check family</th><th>說明 / description</th></tr></thead>
    <tbody>{check_list_rows}</tbody></table>

  <h3>§6 容差登記表快照（顯示用，不定義判定）
    <span class="en">ROADMAP_PHYSICS.md Sec.6 tolerance table snapshot (display-only)</span></h3>
  <table class="data-table"><thead><tr><th>項目 item</th><th>現值 current</th>
    <th>目標值 target</th><th>依據 basis</th></tr></thead>
    <tbody>{tol_rows}</tbody></table>

  <h3>已套用之豁免記錄 <span class="en">exemption records applied to this file</span></h3>
  {exempt_block}

  <p class="meta-line">tool: {esc(tool_name)} &middot; score: {esc(str(score_path))}
     &middot; generated: {esc(ts)}</p>
</section>
"""


# ── page shell (CSS, theme-aware, zero external requests) ─────────────────
_CSS = """
:root { color-scheme: light dark; }
* { box-sizing: border-box; }
body { margin: 0; padding: 24px; font-family: -apple-system, "Segoe UI", "Noto Sans TC",
  "PingFang TC", "Microsoft JhengHei", sans-serif; line-height: 1.55; }
h1 { font-size: 1.5rem; margin: 0 0 4px 0; }
h2 { font-size: 1.15rem; margin: 0 0 8px 0; }
h3 { font-size: 0.95rem; margin: 18px 0 6px 0; }
.en { font-weight: 400; font-size: 0.78em; opacity: 0.65; margin-left: 6px; }
.hint { font-size: 0.85rem; opacity: 0.8; margin: 0 0 10px 0; }
.container { max-width: 1180px; margin: 0 auto; }
.card { border: 1px solid var(--card-border, #d9d9df); border-radius: 10px;
  padding: 16px 18px; margin-bottom: 18px; background: var(--card-bg, #fff); }
.banner-card { border-width: 2px; }
.banner-row { display: flex; align-items: center; gap: 20px; flex-wrap: wrap; }
.banner-main { font-size: 2.4rem; font-weight: 800; letter-spacing: 0.02em; }
.banner-title { font-weight: 700; }
.banner-score-path { font-family: monospace; font-size: 0.82rem; opacity: 0.75; word-break: break-all; }
.banner-sub { font-size: 0.82rem; color: #b8860b; }
.banner-stats { font-size: 0.85rem; margin-top: 6px; }
.banner-exit { font-size: 0.78rem; opacity: 0.7; margin-top: 4px; }
.badge-row { display: flex; gap: 10px; flex-wrap: wrap; margin-top: 14px; }
.badge { border: 2px solid; border-radius: 8px; padding: 6px 12px; min-width: 96px; text-align: center; }
.badge-label { font-size: 0.75rem; opacity: 0.75; }
.badge-status { font-weight: 800; font-size: 1.05rem; }
.badge-sub { font-size: 0.68rem; opacity: 0.6; }
.data-table { border-collapse: collapse; width: 100%; font-size: 0.82rem; margin-top: 4px; }
.data-table th, .data-table td { border: 1px solid var(--card-border, #d9d9df);
  padding: 4px 8px; text-align: left; }
.data-table th { background: var(--table-head, #f2f2f5); }
.specgram-wrap { display: flex; }
.specgram-yaxis { position: relative; width: 44px; flex-shrink: 0; }
.axis-tick-y { position: absolute; right: 6px; transform: translateY(-50%);
  font-size: 0.7rem; opacity: 0.7; }
.specgram-img-container { flex: 1; position: relative; }
.specgram-img { width: 100%; height: auto; display: block; image-rendering: pixelated;
  border: 1px solid var(--card-border, #d9d9df); }
.specgram-xaxis-row { display: flex; }
.specgram-xaxis-spacer { width: 44px; flex-shrink: 0; }
.specgram-xaxis { position: relative; flex: 1; height: 18px; }
.axis-tick { position: absolute; transform: translateX(-50%); font-size: 0.7rem; opacity: 0.7; }
.f0-chart-wrap, .loudness-chart-wrap, .phrase-chart-wrap { width: 100%; overflow-x: auto; }
.f0-chart, .loudness-chart, .phrase-chart { width: 100%; height: auto; display: block; }
.gridline { stroke: var(--grid-line, #ccc); stroke-width: 1; }
.gridline-zero { stroke: var(--grid-line-strong, #888); stroke-width: 1.2; }
.axis-label { font-size: 10px; fill: var(--axis-label, #777); }
.legend-row { display: flex; gap: 16px; margin-bottom: 6px; flex-wrap: wrap; }
.legend-item { font-size: 0.78rem; display: inline-flex; align-items: center; gap: 5px; }
.swatch { width: 12px; height: 12px; border-radius: 2px; display: inline-block; }
.meta-line { font-size: 0.72rem; opacity: 0.6; margin-top: 10px; }
code { font-family: ui-monospace, "Consolas", monospace; }
@media (prefers-color-scheme: dark) {
  body { background: #16161a; color: #e8e8ec; }
  .card { --card-bg: #1e1e24; --card-border: #34343c; }
  .data-table th { --table-head: #2a2a32; }
  .gridline { --grid-line: #3a3a42; }
  .gridline-zero { --grid-line-strong: #6a6a74; }
  .axis-label { --axis-label: #9a9aa4; }
}
:root[data-theme="dark"] body { background: #16161a; color: #e8e8ec; }
:root[data-theme="dark"] .card { --card-bg: #1e1e24; --card-border: #34343c; }
:root[data-theme="dark"] .data-table th { --table-head: #2a2a32; }
:root[data-theme="dark"] .gridline { --grid-line: #3a3a42; }
:root[data-theme="dark"] .gridline-zero { --grid-line-strong: #6a6a74; }
:root[data-theme="dark"] .axis-label { --axis-label: #9a9aa4; }
:root[data-theme="light"] body { background: #fff; color: #16161a; }
:root[data-theme="light"] .card { --card-bg: #fff; --card-border: #d9d9df; }
"""


def generate_html_report(score_path, ok, checks, measured):
    """Top-level entry point called from verify_score.py's main(). `measured`
    is verify_one()'s returned dict, which now carries (see verify_one()):
      _mono_audio, _sample_rate, _dumped_events, _score, _events
    when the render/decode succeeded. If any of those are missing (e.g. the
    render itself failed), the visual sections degrade gracefully to a
    short explanatory note instead of crashing -- the badges section always
    renders, since it only needs `checks`."""
    mono = measured.get("_mono_audio")
    sr = measured.get("_sample_rate")
    dumped_events = measured.get("_dumped_events") or []
    score = measured.get("_score") or {}
    events = measured.get("_events") or []

    exempt_checks = [c for c in checks if c.exempt_reason]
    title_text = (score.get("meta") or {}).get("title") or str(score_path)

    badges_html = render_badges_section(score_path, ok, checks, len(exempt_checks), measured)

    if mono is None or sr is None or len(mono) == 0:
        body_sections = badges_html + f"""
<section class="card">
  <p class="hint">此檔案沒有可用的渲染音訊（渲染失敗或非 WAV 輸出），略過頻譜圖／f0／響度／
     樂句視覺化。<span class="en">No decodable rendered audio for this file (render failed or
     non-WAV output) -- spectrogram/f0/loudness/phrase visualizations skipped.</span></p>
</section>
"""
        footer_html = render_footer_section(score_path, checks, exempt_checks)
        body = body_sections + footer_html
    else:
        duration_s = len(mono) / sr if sr else 0.0

        # dumped_events index-aligns with the subsequence of `events` that
        # are modal-engine (RenderApp.cpp's dumpModes() `continue`s past
        # fm/unmapped-material events) -- rebuild that alignment here so
        # collision detection can look up "what partials does event j have"
        # by ORIGINAL event index. See ScoreRenderer::dumpModes().
        modal_engines = {"string", "cimbalom", "piano", "beam", "tongue_drum",
                          "plate", "water_gong", "membrane", "custom"}
        dumped_map = {}
        di = 0
        for i, ev in enumerate(events):
            if isinstance(ev, dict) and ev.get("engine") in modal_engines:
                if di < len(dumped_events):
                    dumped_map[i] = dumped_events[di]
                    di += 1

        spectrogram_html = render_spectrogram_section(sr, mono)

        f0_events = build_f0_events(events, dumped_map, mono, sr, duration_s)
        f0_html = render_f0_section(f0_events, duration_s)

        loud_pts = compute_loudness_curve(sr, mono)
        rest_intervals = []
        for c in checks:
            if c.name == "rests.rms_below_limit" or (c.name == "rests.checked" and "intervals" in c.detail):
                for iv in c.detail.get("intervals", []):
                    status = "exempt" if c.exempt_reason else ("pass" if iv.get("pass") else "fail")
                    rest_intervals.append({"start": iv["start"], "end": iv["end"],
                                            "level_dbfs": iv["level_dbfs"], "status": status})
        loudness_html = render_loudness_section(loud_pts, duration_s, rest_intervals)

        phrases_html = render_phrases_section(score, events, duration_s)

        footer_html = render_footer_section(score_path, checks, exempt_checks)

        body = (badges_html + spectrogram_html + f0_html + loudness_html
                + phrases_html + footer_html)

    return f"""<!doctype html>
<html lang="zh-Hant">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>{esc(title_text)} — 視覺驗證報告 Visual Verification Report</title>
<style>{_CSS}</style>
</head>
<body>
<div class="container">
  <h1>{esc(title_text)}</h1>
  <p class="hint">TsukiSynth 視覺驗證報告（聾人可視化驗收介面，ROADMAP_PHYSICS.md M4）
    <span class="en">TsukiSynth visual verification report (deaf-accessible sign-off interface)</span></p>
  {body}
</div>
</body>
</html>
"""
