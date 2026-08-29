#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
melody_roll_video.py -- deaf-accessible melody SHAPE video for TsukiSynth.

WHY: tools/melody_verify.py's HTML report (write_html_report) proves melody
position is verifiable BY LOGIC AND SIGHT on a static spectrogram image, but
a static image of a 2-minute piece is too dense to eyeball note-by-note. This
tool renders the SAME judgment as a scrolling piano-roll VIDEO: the score's
declared notes as blocks, the WAV's actually-detected pitch as a moving
trace, so a deaf reviewer (or a sighted one, without listening) can watch the
melody's shape rise and fall over time and see at a glance whether the audio
followed the score.

Reuse, not reinvention (per instruction): every piece of pitch/onset
detection is imported from tools/melody_verify.py and called as-is --
  * mv.verify()            -- the full per-event PASS/FAIL/UNVERIFIED
                               judgment (same tolerances, same refusal logic)
  * mv.Spectrogram/band_of/BAND_GATE_DBFS -- the same STFT band-energy method
                               melody_verify uses for onset detection, reused
                               here to build a continuous "is this declared
                               pitch sounding right now" trace instead of
                               only its FIRST-rise time.
  * mv.vs (verify_score.py) -- find_cli/render_score/read_wav_mono/band math.
This file adds no new pitch-detection math: it only decides, for each frame
already classified "sounding" by melody_verify's own gate, which on-screen
color it gets (from melody_verify's own per-event verdict).

Color (2026-08-30 UPDATE): the default palette is now the "neon" theme --
月月 supplied a reference frame and asked for the video to look like it
(dark violet field, glowing violet/magenta bars). See THEMES below; the
original monochrome family is still available as --theme slate, and the
deviation rule it protected is kept (FAIL = far-off hue PLUS a triangle
marker). A fixed left-hand pitch ruler (note names + key ladder) now shows
absolute pitch, replacing the octave labels that used to scroll away inside
the strip. The original reasoning is preserved below for the record:

Color: the note-block/trace "matches" state does NOT get its own green hue.
月月's standing design rule (feedback_design_taste_charta.md) is a single
monochrome family with color reserved for warnings; the task brief's own
point 3 says the same for this tool explicitly ("僅偏差紅色警示" -- ONLY
deviation gets red). So: dark monochrome slate-blue background/blocks/trace
throughout, red used ONLY for FAIL / unexplained-extra. Where the task
brief's point 1 separately says "對上綠" (green on match), point 3's explicit
monochrome-except-red constraint is treated as authoritative for pixels
actually drawn -- flagged in this file's docstring so the resolution is
visible, not silently picked.

Pitch axis: continuous semitone position (12*log2(f/440)+69), so any
fundamental lands at its true height, not snapped to a piano-key row.

Detected trace mechanics: for each distinct declared fundamental (rounded
like melody_verify's own `track()` cache), take that band's energy-vs-time
track (mv.Spectrogram.band_db, same object melody_verify builds) and gate it
at mv.BAND_GATE_DBFS (same threshold melody_verify's detect_rises() uses).
Contiguous runs above gate become horizontal trace segments at that band's
frequency -- this is deliberately NOT a general pitch tracker (autocorrelation
etc.): it only asks "is THIS declared pitch active", which is exactly what
melody_verify already computes and is sufficient to show the melody's
up/down shape (a run of segments at different heights over time reads as a
moving contour once the video scrolls). Each declared event owns a bounded
display window (band_windows(): [event.time, event.time+duration+RING_CAP_S],
clipped at the next same-band event) inside which its OWN gate-crossing
samples are traced -- NOT a single energy>gate scan across the whole file:
a dense polyphonic render keeps most bands' raw energy above BAND_GATE_DBFS
almost continuously from cross-band spectral bleed of every OTHER note, so
an unbounded scan would attribute that bleed to whichever event happened to
be "most recent", painting a false multi-second bar between a band's real
(sparse) occurrences -- observed on the fur_elise render before this bound
was added. Segment color is the owning event's own melody_verify verdict --
reusing PASS/FAIL/UNVERIFIED, not a new judgment. melody_verify's own
extra_scan.unexplained rises (truly unexplained energy, already computed,
not recomputed here) are drawn as separate red tick marks.

Usage:
  python tools/melody_roll_video.py <score.json> [--wav existing.wav]
      [--json existing_melody_verify_report.json] [--out out.mp4]
      [--fps 30] [--width 1280] [--height 720] [--window-s 6.0]
      [--theme neon|slate] [--still-at SECONDS] [--ffmpeg PATH]
Exit codes: 0 success, 1 error, 2 usage.
"""

import argparse
import importlib.util
import json
import math
import subprocess
import sys
import tempfile
from bisect import bisect_right
from pathlib import Path

import numpy as np
from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parent
DEFAULT_FFMPEG = Path(
    r"C:\Users\admin\Desktop\Tools\ffmpeg-8.1.1-full_build\bin\ffmpeg.exe")


def _load(name, relpath):
    spec = importlib.util.spec_from_file_location(name, ROOT / relpath)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


mv = _load("melody_verify", "melody_verify.py")   # also loads mv.vs internally
vs = mv.vs

# -- palettes ---------------------------------------------------------------
# Two themes, selected with --theme.
#   slate : the original monochrome slate-blue family described in the
#           docstring above (kept intact so an earlier video can be
#           reproduced).
#   neon  : DEFAULT since 2026-08-29 -- 月月 supplied a reference frame (dark
#           violet space background, glowing violet/magenta note bars) and
#           asked for the video to look like it. That is a direct user
#           instruction and it overrides the docstring's monochrome rule for
#           this tool's video output.
# The deviation-salience half of that rule is preserved: FAIL keeps a hue far
# from every normal-state hue (hot red-orange vs the violet/magenta family)
# AND gets a shape cue (a solid triangle at its onset), so a reviewer who
# cannot separate red from magenta still cannot miss a FAIL.
THEMES = {
    "neon": {
        "glow": True,
        "glow_radius": 5,
        "stars": True,
        "bg": (9, 7, 18),
        "grid_minor": (22, 18, 38),
        "grid_major": (34, 27, 56),
        "grid_oct": (72, 52, 118),
        "text_dim": (138, 124, 176),
        "text_main": (228, 218, 255),
        "playhead": (245, 238, 255),
        "legend_bg": (18, 14, 32),
        "key_white": (74, 62, 112),
        "key_black": (34, 27, 60),
        "key_edge": (12, 10, 24),
        "block": {
            "PASS":       {"fill": (255, 96, 205), "edge": (255, 198, 240), "glow": (150, 30, 120)},
            "UNVERIFIED": {"fill": (124, 96, 214), "edge": (192, 172, 255), "glow": (56, 32, 128)},
            "FAIL":       {"fill": (255, 74, 43),  "edge": (255, 210, 194), "glow": (156, 34, 16)},
        },
        "trace": {
            "PASS":       {"core": (255, 176, 236), "glow": (150, 30, 120)},
            "UNVERIFIED": {"core": (160, 132, 240), "glow": (60, 36, 140)},
            "FAIL":       {"core": (255, 118, 84),  "glow": (140, 38, 16)},
        },
        "extra": (255, 74, 43),
    },
    "slate": {
        "glow": False,
        "glow_radius": 0,
        "stars": False,
        "bg": (13, 16, 21),
        "grid_minor": (23, 28, 35),
        "grid_major": (36, 44, 54),
        "grid_oct": (52, 62, 75),
        "text_dim": (98, 108, 122),
        "text_main": (196, 203, 214),
        "playhead": (224, 229, 236),
        "legend_bg": (18, 22, 28),
        "key_white": (58, 66, 78),
        "key_black": (24, 29, 36),
        "key_edge": (13, 16, 21),
        "block": {
            "PASS":       {"fill": (52, 78, 106), "edge": (104, 142, 179), "glow": (0, 0, 0)},
            "UNVERIFIED": {"fill": (33, 37, 44),  "edge": (68, 75, 86),    "glow": (0, 0, 0)},
            "FAIL":       {"fill": (104, 30, 30), "edge": (206, 66, 58),   "glow": (0, 0, 0)},
        },
        "trace": {
            "PASS":       {"core": (150, 184, 216), "glow": (0, 0, 0)},
            "UNVERIFIED": {"core": (80, 88, 100),   "glow": (0, 0, 0)},
            "FAIL":       {"core": (226, 96, 86),   "glow": (0, 0, 0)},
        },
        "extra": (226, 96, 86),
    },
}

# Module-level palette names (rather than a passed-around object) to match
# this file's existing constant style; apply_theme() rebinds them.
THEME_NAME = "neon"
BG = GRID_MINOR = GRID_MAJOR = GRID_OCT = None
TEXT_DIM = TEXT_MAIN = PLAYHEAD = LEGEND_BG = None
KEY_WHITE = KEY_BLACK = KEY_EDGE = None
BLOCK = TRACE_COLOR = EXTRA_COLOR = None
GLOW = STARS = False
GLOW_RADIUS = 0


def apply_theme(name):
    global THEME_NAME, BG, GRID_MINOR, GRID_MAJOR, GRID_OCT, TEXT_DIM, TEXT_MAIN
    global PLAYHEAD, LEGEND_BG, KEY_WHITE, KEY_BLACK, KEY_EDGE
    global BLOCK, TRACE_COLOR, EXTRA_COLOR, GLOW, GLOW_RADIUS, STARS
    t = THEMES[name]
    THEME_NAME = name
    BG, GRID_MINOR = t["bg"], t["grid_minor"]
    GRID_MAJOR, GRID_OCT = t["grid_major"], t["grid_oct"]
    TEXT_DIM, TEXT_MAIN = t["text_dim"], t["text_main"]
    PLAYHEAD, LEGEND_BG = t["playhead"], t["legend_bg"]
    KEY_WHITE, KEY_BLACK, KEY_EDGE = t["key_white"], t["key_black"], t["key_edge"]
    BLOCK, TRACE_COLOR, EXTRA_COLOR = t["block"], t["trace"], t["extra"]
    GLOW, GLOW_RADIUS, STARS = t["glow"], t["glow_radius"], t["stars"]


apply_theme("neon")

N_FFT, HOP = mv.N_FFT, mv.HOP


def semitone(f0):
    return 12.0 * math.log2(f0 / 440.0) + 69.0


def font(size, bold=False):
    path = r"C:\Windows\Fonts\consolab.ttf" if bold else r"C:\Windows\Fonts\consola.ttf"
    try:
        return ImageFont.truetype(path, size)
    except OSError:
        return ImageFont.load_default()


def note_name(midi_round):
    names = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
    n = int(round(midi_round))
    return "%s%d" % (names[n % 12], n // 12 - 1)


def make_background(width, height):
    """Flat theme background plus (neon only) a faint star field. Seeded from
    a fixed constant so two runs of the same score give identical frames --
    this is a verification tool, its output has to be reproducible."""
    arr = np.empty((height, width, 3), dtype=np.uint8)
    arr[:, :] = BG
    if STARS:
        rng = np.random.default_rng(20260829)
        n = max(1, int(width * height / 5200))
        xs = rng.integers(0, width, n)
        ys = rng.integers(0, height, n)
        b = rng.integers(14, 78, n).astype(np.float32)
        star = np.stack([b * 0.95, b * 0.82, b * 1.55], axis=1)
        arr[ys, xs] = np.clip(star, 0, 255).astype(np.uint8)
    return Image.fromarray(arr, "RGB")


def add_glow(base, glow_layer):
    """Blur the glow layer and add it into the base (bloom)."""
    if glow_layer is None:
        return base
    return ImageChops.add(base, glow_layer.filter(
        ImageFilter.GaussianBlur(GLOW_RADIUS)))


# -- fixed left-hand pitch ruler (drawn on EVERY frame, never scrolls) ------
GUTTER_W = 70
_LADDER_W = 18


def label_degrees_for(px_per_semitone):
    """Which scale degrees get a printed name, given the vertical room one
    semitone has: always each octave's C; add the fifth (G) when there is
    room; every white key when there is plenty."""
    if px_per_semitone >= 11.0:
        return (0, 2, 4, 5, 7, 9, 11)
    if px_per_semitone >= 4.5:
        return (0, 7)
    return (0,)


def make_gutter(height, top_margin, bottom_margin, semi_min, semi_max):
    """Opaque pitch ruler: chromatic key ladder + note names (C4, G4, D5 ...)
    so a reviewer reads a bar's ABSOLUTE pitch off the screen instead of only
    its relative up/down shape. Fixed overlay -- it does not scroll away like
    the in-strip labels it replaces."""
    img = Image.new("RGBA", (GUTTER_W, height), (0, 0, 0, 0))
    dr = ImageDraw.Draw(img)
    plot_h = height - top_margin - bottom_margin
    span = max(1e-9, semi_max - semi_min)
    px_per = plot_h / span

    def y_of_m(m):
        return top_margin + (1.0 - (m - semi_min) / span) * plot_h

    dr.rectangle([0, 0, GUTTER_W - 1, height - 1], fill=(*BG, 238))
    lad_x1 = GUTTER_W - 4
    lad_x0 = lad_x1 - _LADDER_W
    degrees = label_degrees_for(px_per)
    fnt, fnt_b = font(12), font(12, bold=True)
    for m in range(int(math.floor(semi_min)), int(math.ceil(semi_max)) + 1):
        yc = y_of_m(m)
        y0, y1 = yc - px_per / 2.0, yc + px_per / 2.0
        if y1 < top_margin or y0 > height - bottom_margin:
            continue
        y0, y1 = max(y0, top_margin), min(y1, height - bottom_margin)
        black = (m % 12) in (1, 3, 6, 8, 10)
        dr.rectangle([lad_x0, y0, lad_x1, y1],
                      fill=(*(KEY_BLACK if black else KEY_WHITE), 255),
                      outline=(*KEY_EDGE, 255))
        if (m % 12) in degrees:
            is_c = (m % 12) == 0
            name = note_name(m)
            col = (*(TEXT_MAIN if is_c else TEXT_DIM), 255)
            f = fnt_b if is_c else fnt
            w = dr.textlength(name, font=f)
            dr.text((lad_x0 - 6 - w, yc - 7), name, font=f, fill=col)
            dr.line([(lad_x0 - 4, yc), (lad_x0 - 1, yc)], fill=col, width=1)
    dr.line([(GUTTER_W - 1, 0), (GUTTER_W - 1, height)],
             fill=(*GRID_OCT, 255), width=1)
    return img


def radial_sprite(color, radius, core_frac=0.30, falloff=2.2):
    """Glowing dot: coloured halo fading out, white-hot centre."""
    d = radius * 2 + 1
    yy, xx = np.mgrid[0:d, 0:d]
    r = np.hypot(xx - radius, yy - radius) / float(radius)
    halo = np.clip(1.0 - r, 0.0, 1.0) ** falloff
    core = np.clip(1.0 - r / max(1e-6, core_frac), 0.0, 1.0)
    rgb = np.zeros((d, d, 3), dtype=np.float32)
    for c in range(3):
        rgb[..., c] = color[c] * halo + (255.0 - color[c]) * core
    alpha = np.clip(halo * 235.0 + core * 255.0, 0, 255)
    return Image.fromarray(
        np.dstack([np.clip(rgb, 0, 255), alpha]).astype(np.uint8), "RGBA")


def make_playhead_sprite(height, half_w=11):
    """Vertical glow column behind the crisp playhead line."""
    w = half_w * 2 + 1
    x = np.abs(np.arange(w) - half_w) / float(half_w)
    a = np.clip(1.0 - x, 0.0, 1.0) ** 2.4 * 150.0
    col = np.zeros((height, w, 4), dtype=np.float32)
    for c in range(3):
        col[..., c] = PLAYHEAD[c]
    col[..., 3] = a[None, :]
    return Image.fromarray(col.astype(np.uint8), "RGBA")


def build_report(score_path, wav_path, json_out):
    return mv.verify(score_path, wav_path=str(wav_path), keep_json=str(json_out) if json_out else None,
                      quiet=False)


def gather_display_events(score, report):
    """Per score-event display record: time, duration, verdict, f_disp
    (frequency used for both the on-screen block height AND, when it came
    from melody_verify's own expected_f0_hz, the audio-detection band)."""
    events = score.get("events", [])
    rows_by_index = {r["index"]: r for r in report["events"]}
    disp = []
    for i, ev in enumerate(events):
        if float(ev.get("velocity", 1.0) or 0.0) <= 0.0:
            continue  # zero-velocity: renders nothing by contract, no block
        r = rows_by_index.get(i, {})
        f_disp = r.get("expected_f0_hz")
        has_truth = f_disp is not None
        if f_disp is None:
            perf = ev.get("performance") or {}
            f_disp = perf.get("frequency_hz")
        if f_disp is None:
            f_disp = vs.midi_to_hz(vs.note_to_midi(ev.get("note")))
        if f_disp is None or not math.isfinite(f_disp) or f_disp <= 0:
            continue
        dur = float(ev.get("duration") or 0.0)
        if dur <= 0:
            dur = 0.05
        disp.append({
            "time": float(ev.get("time", 0.0)),
            "duration": dur,
            "f0": float(f_disp),
            "has_truth": has_truth,
            "verdict": r.get("verdict", "UNVERIFIED"),
            "note": ev.get("note"),
        })
    return disp


def build_bands(disp):
    """key(rounded f0, matching melody_verify's own track() cache key) ->
    {"f0":..., "events":[(time,duration,verdict), ...] sorted by time}.
    Only events with a melody_verify-judged expected_f0_hz (has_truth) seed a
    band -- there is no ground truth to build an audio-detection band for a
    refused event."""
    bands = {}
    for d in disp:
        if not d["has_truth"]:
            continue
        key = round(d["f0"], 3)
        b = bands.setdefault(key, {"f0": d["f0"], "events": []})
        b["events"].append((d["time"], d["duration"], d["verdict"]))
    for b in bands.values():
        b["events"].sort(key=lambda e: e[0])
        b["times_arr"] = [e[0] for e in b["events"]]
    return bands


# Display-only bound on how long a struck note is allowed to paint its trace
# (NOT a verification tolerance -- melody_verify's own onset/pitch tolerances
# are untouched; this only stops one distant event's color from bleeding
# across a whole silent gap). A dense polyphonic render keeps most bands'
# raw energy above BAND_GATE_DBFS almost continuously (bleed from every OTHER
# concurrently-sounding note, not this band's own note) -- observed on the
# full fur_elise render: the C3 band's gate stayed "active" from t=0 to its
# first real strike at t=11.25s, so an unbounded scan painted that FAIL a
# false ~11s red bar it never actually occupied. Each event's window is
# additionally clipped at the NEXT same-band event's own start, so two
# strikes of the same pitch never bleed into each other's color either.
RING_CAP_S = 3.0


def band_windows(band):
    """[(t_start, t_end, verdict), ...] non-overlapping display windows for
    one band, each owned by exactly one declared event."""
    events = band["events"]
    wins = []
    for k, (t, dur, verdict) in enumerate(events):
        end = t + max(dur, 0.05) + RING_CAP_S
        if k + 1 < len(events):
            end = min(end, events[k + 1][0])
        wins.append((t, end, verdict))
    return wins


def render_strip(score, report, disp, bands, spectro, pad_s, pps, height,
                  left_pad, semi_min, semi_max, top_margin, bottom_margin):
    plot_h = height - top_margin - bottom_margin

    def y_of(f0):
        s = semitone(f0)
        frac = (s - semi_min) / max(1e-9, (semi_max - semi_min))
        return top_margin + (1.0 - frac) * plot_h

    duration_total = max((d["time"] + d["duration"] for d in disp), default=1.0)
    strip_w = int(math.ceil(left_pad + duration_total * pps + left_pad)) + 4
    strip = make_background(strip_w, height)
    dr = ImageDraw.Draw(strip)

    def x_of(t):
        return left_pad + t * pps

    # -- gridlines: octave (C) rows + 5s time columns --------------------
    # (Note NAMES are no longer painted into the scrolling strip -- they now
    # live in the fixed left gutter, make_gutter(), where they stay readable
    # instead of sliding off-screen.)
    fnt_grid = font(13)
    midi_lo = int(math.floor(semi_min))
    midi_hi = int(math.ceil(semi_max))
    for m in range(midi_lo, midi_hi + 1):
        y = y_of(vs.midi_to_hz(m))
        if m % 12 == 0:
            dr.line([(0, y), (strip_w, y)], fill=GRID_OCT, width=1)
        elif m % 12 in (2, 4, 5, 7, 9, 11):  # white keys: faint row
            dr.line([(0, y), (strip_w, y)], fill=GRID_MINOR, width=1)
    t = 0.0
    while t <= duration_total + 1.0:
        x = x_of(t)
        major = (int(round(t)) % 5 == 0)
        dr.line([(x, top_margin), (x, height - bottom_margin)],
                fill=(GRID_MAJOR if major else GRID_MINOR), width=1)
        if major:
            dr.text((x + 3, top_margin - 16), "%ds" % int(round(t)),
                     font=fnt_grid, fill=TEXT_DIM)
        t += 1.0

    # -- geometry pass: score blocks / detected-trace segments / extras ----
    # Computed once, then painted twice: first (fattened, dim) into the glow
    # layer that gets blurred and added underneath, then crisply on top. The
    # expensive part (spectro.band_db per band) runs only in this pass.
    BLOCK_OFFSET = 5.0
    BLOCK_H = 3.5
    # score note blocks sit slightly ABOVE centre and the audio-detected
    # trace below at the same x -- two adjacent bars, so a PASS reads as two
    # thin parallel lines and a misalignment is visibly two separate bars.
    blocks = []      # (x0, x1, y, verdict)
    for d in disp:
        blocks.append((x_of(d["time"]),
                       max(x_of(d["time"]) + 1.5, x_of(d["time"] + d["duration"])),
                       y_of(d["f0"]) - BLOCK_OFFSET,
                       d["verdict"]))

    # Each declared event gets its OWN bounded window (band_windows) rather
    # than one energy gate scanned across the whole file -- see RING_CAP_S's
    # docstring for why the unbounded version painted false multi-second
    # bars in a dense polyphonic render.
    segs = []        # (xa, xb, y, verdict)
    for key, band in bands.items():
        times, db = spectro.band_db(*mv.band_of(band["f0"]))
        times_shift = times - pad_s   # back to score-time (PAD_S removed)
        y = y_of(band["f0"]) + BLOCK_OFFSET
        for win_start, win_end, verdict in band_windows(band):
            lo = bisect_right(times_shift, win_start - 0.01)
            hi = bisect_right(times_shift, win_end)
            if hi <= lo:
                continue
            active = db[lo:hi] > mv.BAND_GATE_DBFS
            t_slice = times_shift[lo:hi]
            n = len(t_slice)
            i = 0
            while i < n:
                if not active[i]:
                    i += 1
                    continue
                j = i
                while j + 1 < n and active[j + 1]:
                    j += 1
                xa, xb = x_of(t_slice[i]), x_of(t_slice[j])
                segs.append((xa, max(xb, xa + 1.0), y, verdict))
                i = j + 1

    # unexplained-extra marks (reused verbatim from melody_verify's own
    # extra_scan, not recomputed)
    extras = [(x_of(x_item["rise_time"]), y_of(x_item["band_hz"]))
              for x_item in report["extra_scan"].get("unexplained", [])]

    # -- glow pass --------------------------------------------------------
    if GLOW:
        glow = Image.new("RGB", (strip_w, height), (0, 0, 0))
        gdr = ImageDraw.Draw(glow)
        for x0, x1, y, verdict in blocks:
            g = BLOCK.get(verdict, BLOCK["UNVERIFIED"])["glow"]
            gdr.rectangle([x0 - 2, y - BLOCK_H - 3, x1 + 2, y + BLOCK_H + 3],
                           fill=g)
        for xa, xb, y, verdict in segs:
            g = TRACE_COLOR.get(verdict, TRACE_COLOR["UNVERIFIED"])["glow"]
            gdr.line([(xa, y), (xb, y)], fill=g, width=9)
        for x, y in extras:
            gdr.ellipse([x - 8, y - 12, x + 8, y + 12], fill=EXTRA_COLOR)
        strip = add_glow(strip, glow)
        dr = ImageDraw.Draw(strip)

    # -- crisp pass -------------------------------------------------------
    for x0, x1, y, verdict in blocks:
        col = BLOCK.get(verdict, BLOCK["UNVERIFIED"])
        dr.rectangle([x0, y - BLOCK_H, x1, y + BLOCK_H],
                      fill=col["fill"], outline=col["edge"], width=1)
        if verdict == "FAIL":
            # shape cue on top of the hue cue: a FAIL is findable even for a
            # reviewer who cannot tell red from magenta.
            dr.polygon([(x0 - 5, y - BLOCK_H - 11), (x0 + 5, y - BLOCK_H - 11),
                        (x0, y - BLOCK_H - 3)], fill=col["edge"])
    for xa, xb, y, verdict in segs:
        col = TRACE_COLOR.get(verdict, TRACE_COLOR["UNVERIFIED"])["core"]
        dr.line([(xa, y), (xb, y)], fill=col, width=3)
    for x, y in extras:
        dr.line([(x, y - 9), (x, y + 9)], fill=EXTRA_COLOR, width=3)
        dr.ellipse([x - 3, y - 3, x + 3, y + 3], fill=EXTRA_COLOR)

    return strip, duration_total, y_of


def make_legend(width, height):
    """Fixed-size overlay drawn onto every frame (small, cheap). Sits at the
    TOP-RIGHT: the top-left is now occupied by the pitch ruler gutter."""
    img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    dr = ImageDraw.Draw(img)
    fnt = font(14)
    lines = [
        ("PASS -- score matched audio", BLOCK["PASS"]["edge"]),
        ("FAIL -- deviation (red + triangle)", BLOCK["FAIL"]["edge"]),
        ("UNVERIFIED -- refused (violet)", BLOCK["UNVERIFIED"]["edge"]),
        ("* unexplained audio", EXTRA_COLOR),
    ]
    box_w, box_h = 300, 20 * len(lines) + 12
    pad_y = 10
    x0 = width - box_w - 12
    dr.rectangle([x0 - 6, pad_y - 4, x0 + box_w, pad_y + box_h],
                  fill=(*LEGEND_BG, 214), outline=(*GRID_MAJOR, 255))
    for n, (text, color) in enumerate(lines):
        y = pad_y + n * 20
        dr.rectangle([x0, y + 4, x0 + 12, y + 14], fill=(*color, 255))
        dr.text((x0 + 18, y), text, font=fnt, fill=(*TEXT_MAIN, 255))
    return img


def make_composer(strip, y_of, width, height, left_pad, pps,
                   top_margin, bottom_margin, disp, semi_min, semi_max):
    """Build the per-frame painter once (overlays and sprites are fixed) and
    return frame(t) -> RGB Image. Shared by write_video and write_still so a
    still is pixel-identical to the corresponding video frame."""
    legend = make_legend(width, height)
    gutter = make_gutter(height, top_margin, bottom_margin, semi_min, semi_max)
    ph_sprite = make_playhead_sprite(height) if GLOW else None
    ph_half = (ph_sprite.size[0] - 1) // 2 if ph_sprite is not None else 0
    # Note-head flash: when a declared note crosses the playhead it lights up,
    # so the eye gets an event-level "this one, now" cue on top of the bars.
    FLASH_R = 17
    flash_sprites = ({v: radial_sprite(BLOCK[v]["edge"], FLASH_R,
                                        core_frac=0.34, falloff=1.8)
                      for v in BLOCK} if GLOW else {})
    flashes = []
    if disp and GLOW:
        for d in disp:
            flashes.append((d["time"], d["time"] + d["duration"],
                            y_of(d["f0"]) - 5.0,
                            d["verdict"] if d["verdict"] in BLOCK else "UNVERIFIED"))
        flashes.sort(key=lambda f: f[0])
    flash_starts = [f[0] for f in flashes]
    FLASH_HOLD = 0.12   # keep a hit lit briefly after its onset passes
    fnt_t = font(20, bold=True)
    strip_w = strip.size[0]
    strip_arr = np.asarray(strip)
    cx = width // 2

    def frame_at(t):
        xc = left_pad + t * pps
        left = int(round(xc - width / 2.0))
        left = max(0, min(left, max(0, strip_w - width)))
        crop = strip_arr[:, left:left + width, :]
        frame = Image.fromarray(crop, "RGB").convert("RGBA")
        # note-head flash for every declared note under the playhead
        if flashes:
            hi_i = bisect_right(flash_starts, t)
            for idx in range(hi_i - 1, -1, -1):
                t0, t1, y, verdict = flashes[idx]
                if t - t0 > 12.0:
                    break
                if t0 - 0.02 <= t <= max(t1, t0 + FLASH_HOLD):
                    frame.alpha_composite(
                        flash_sprites[verdict],
                        dest=(cx - FLASH_R, int(round(y)) - FLASH_R))
        if ph_sprite is not None:
            frame.alpha_composite(ph_sprite, dest=(cx - ph_half, 0))
        frame.alpha_composite(gutter)
        frame.alpha_composite(legend)
        dr = ImageDraw.Draw(frame)
        dr.line([(cx, top_margin - 20), (cx, height - bottom_margin + 4)],
                 fill=PLAYHEAD, width=2)
        dr.text((cx + 6, height - bottom_margin + 6), "t=%.2fs" % t,
                 font=fnt_t, fill=TEXT_MAIN)
        return frame.convert("RGB")

    return frame_at


def write_still(strip, t, y_of, width, height, left_pad, pps, out_path,
                 top_margin, bottom_margin, disp, semi_min, semi_max):
    frame_at = make_composer(strip, y_of, width, height, left_pad, pps,
                              top_margin, bottom_margin, disp, semi_min, semi_max)
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    frame_at(t).save(out_path)


def write_video(strip, duration_total, y_of, width, height, fps, left_pad, pps,
                 wav_path, out_path, ffmpeg, top_margin, bottom_margin,
                 disp=None, semi_min=0.0, semi_max=1.0):
    frame_at = make_composer(strip, y_of, width, height, left_pad, pps,
                              top_margin, bottom_margin, disp, semi_min, semi_max)
    n_frames = int(math.ceil(duration_total * fps))

    cmd = [str(ffmpeg), "-y", "-loglevel", "warning", "-nostats",
           "-f", "rawvideo", "-pix_fmt", "rgb24",
           "-s", "%dx%d" % (width, height), "-r", str(fps), "-i", "-",
           "-i", str(wav_path),
           "-map", "0:v", "-map", "1:a",
           "-c:v", "libx264", "-preset", "medium", "-crf", "18",
           "-pix_fmt", "yuv420p",
           "-c:a", "aac", "-b:a", "192k",
           "-shortest",
           str(out_path)]
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    # stderr goes to a FILE, not a pipe: ffmpeg's own progress/diagnostic
    # writes to stderr would otherwise fill the pipe buffer while nobody is
    # draining it (we only read stderr after closing stdin), deadlocking
    # ffmpeg's stdin read against our blocked stdin write (observed on the
    # sentinel fixture: both processes idle, 0% CPU, stuck forever). -nostats
    # additionally silences the high-frequency per-frame progress line.
    err_log = Path(str(out_path) + ".ffmpeg.log")
    err_fh = open(err_log, "wb")
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE,
                             stdout=subprocess.DEVNULL, stderr=err_fh)
    write_err = None
    try:
        for k in range(n_frames):
            out = np.asarray(frame_at(k / fps))
            proc.stdin.write(out.tobytes())
    except (BrokenPipeError, OSError) as e:
        write_err = e
    finally:
        try:
            proc.stdin.close()
        except OSError:
            pass
        rc = proc.wait()
        err_fh.close()
    if rc != 0 or write_err is not None:
        err_text = err_log.read_text(encoding="utf-8", errors="replace")
        raise RuntimeError(
            "ffmpeg failed (exit %s, write_err=%r):\ncmd=%s\n%s"
            % (rc, write_err, " ".join(cmd), err_text))
    return n_frames


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("score")
    ap.add_argument("--wav")
    ap.add_argument("--json")
    ap.add_argument("--out")
    ap.add_argument("--fps", type=int, default=30)
    ap.add_argument("--width", type=int, default=1280)
    ap.add_argument("--height", type=int, default=720)
    ap.add_argument("--window-s", type=float, default=6.0)
    ap.add_argument("--theme", choices=sorted(THEMES), default="neon",
                     help="neon (default, glowing violet/magenta) or slate "
                          "(original monochrome slate-blue)")
    ap.add_argument("--ffmpeg", default=str(DEFAULT_FFMPEG))
    ap.add_argument("--still-at", type=float, default=None,
                     help="write a single PNG frame at this time (seconds) "
                          "instead of a video -- for quick palette review")
    a = ap.parse_args()
    apply_theme(a.theme)

    score_path = Path(a.score)
    score = json.loads(score_path.read_text(encoding="utf-8"))
    cli = vs.find_cli()
    if cli is None:
        print("ERROR: TsukiSynthCLI.exe not found under build/ -- build first.", file=sys.stderr)
        sys.exit(1)

    tmpdir = None
    wav_path = a.wav
    if wav_path is None:
        tmpdir = tempfile.TemporaryDirectory(prefix="melody_roll_")
        print("[render] CLI rendering %s ..." % score_path.name)
        wav_path = vs.render_score(cli, str(score_path), tmpdir.name)
        print("[render] -> %s" % wav_path)

    if a.json and Path(a.json).exists():
        report = json.loads(Path(a.json).read_text(encoding="utf-8"))
        print("[verify] reusing existing report %s" % a.json)
    else:
        print("[verify] running melody_verify.verify() ...")
        report = build_report(score_path, wav_path, a.json)
        su = report["summary"]
        print("[verify] summary: %d PASS / %d FAIL / %d UNVERIFIED  extra-scan: %s"
              % (su["pass"], su["fail"], su["unverified"], report["extra_scan"]["verdict"]))

    disp = gather_display_events(score, report)
    if not disp:
        print("ERROR: no displayable events (all zero-velocity or unresolvable).", file=sys.stderr)
        sys.exit(1)
    bands = build_bands(disp)

    sr, mono, _ch = vs.read_wav_mono(wav_path)
    pad_s = mv.PAD_S
    mono_p = np.concatenate([np.zeros(int(pad_s * sr)), mono])
    spectro = mv.Spectrogram(mono_p, sr)

    semis = [semitone(d["f0"]) for d in disp]
    semi_min, semi_max = min(semis) - 2.0, max(semis) + 2.0

    top_margin, bottom_margin = 44, 44
    pps = a.width / a.window_s
    left_pad = a.width / 2.0

    print("[layout] %d events, %d bands, pitch range %.1f..%.1f semitones (MIDI)"
          % (len(disp), len(bands), semi_min, semi_max))

    strip, duration_total, y_of = render_strip(
        score, report, disp, bands, spectro, pad_s, pps, a.height,
        left_pad, semi_min, semi_max, top_margin, bottom_margin)
    print("[strip] %dx%d px, timeline %.2fs" % (strip.size[0], strip.size[1], duration_total))

    wav_dur = len(mono) / sr
    duration_total = max(duration_total, wav_dur)

    if a.still_at is not None:
        still = Path(a.out) if a.out else Path("exports/videos") / (
            score_path.stem + "_melody_roll_%s.png" % a.theme)
        write_still(strip, a.still_at, y_of, a.width, a.height, left_pad, pps,
                     still, top_margin, bottom_margin, disp, semi_min, semi_max)
        print("[still] %s at t=%.2fs" % (still, a.still_at))
        if tmpdir:
            tmpdir.cleanup()
        return

    out_path = Path(a.out) if a.out else Path("exports/videos") / (score_path.stem + "_melody_roll.mp4")
    n_frames = write_video(strip, duration_total, y_of, a.width, a.height, a.fps,
                            left_pad, pps, wav_path, out_path, a.ffmpeg,
                            top_margin, bottom_margin, disp, semi_min, semi_max)
    size_mb = out_path.stat().st_size / (1024.0 * 1024.0)
    print("[video] %s  frames=%d  duration=%.2fs  size=%.2f MB"
          % (out_path, n_frames, n_frames / a.fps, size_mb))

    if tmpdir:
        tmpdir.cleanup()


if __name__ == "__main__":
    main()
