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
      [--ffmpeg PATH]
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
from PIL import Image, ImageDraw, ImageFont

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

# -- palette (monochrome slate-blue + red-only-for-deviation) ----------------
BG          = (13, 16, 21)
GRID_MINOR  = (23, 28, 35)
GRID_MAJOR  = (36, 44, 54)
GRID_OCT    = (52, 62, 75)
TEXT_DIM    = (98, 108, 122)
TEXT_MAIN   = (196, 203, 214)
PLAYHEAD    = (224, 229, 236)
LEGEND_BG   = (18, 22, 28)

BLOCK = {
    "PASS":       {"fill": (52, 78, 106),  "edge": (104, 142, 179)},
    "UNVERIFIED": {"fill": (33, 37, 44),   "edge": (68, 75, 86)},
    "FAIL":       {"fill": (104, 30, 30),  "edge": (206, 66, 58)},
}
TRACE_COLOR = {
    "PASS":       (150, 184, 216),
    "UNVERIFIED": (80, 88, 100),
    "FAIL":       (226, 96, 86),
}
EXTRA_COLOR = (226, 96, 86)

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
    strip = Image.new("RGB", (strip_w, height), BG)
    dr = ImageDraw.Draw(strip)

    def x_of(t):
        return left_pad + t * pps

    # -- gridlines: octave (C) rows + 5s time columns --------------------
    fnt_grid = font(13)
    midi_lo = int(math.floor(semi_min))
    midi_hi = int(math.ceil(semi_max))
    for m in range(midi_lo, midi_hi + 1):
        y = y_of(vs.midi_to_hz(m))
        if m % 12 == 0:
            dr.line([(0, y), (strip_w, y)], fill=GRID_OCT, width=1)
            dr.text((4, y - 14), note_name(m), font=fnt_grid, fill=TEXT_DIM)
        elif m % 12 in (0, 2, 4, 5, 7, 9, 11):  # white keys: faint row
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

    # -- score note blocks (drawn slightly ABOVE center; the audio-detected
    # trace below at the same x -- two adjacent bars so a PASS reads as two
    # thin parallel lines and a FAIL/misalignment is visibly two separate
    # bars instead of one blended one) ---------------------------------
    BLOCK_OFFSET = 5.0
    for d in disp:
        x0 = x_of(d["time"])
        x1 = x_of(d["time"] + d["duration"])
        y = y_of(d["f0"]) - BLOCK_OFFSET
        col = BLOCK.get(d["verdict"], BLOCK["UNVERIFIED"])
        h = 3.5
        dr.rectangle([x0, y - h, max(x0 + 1.5, x1), y + h],
                      fill=col["fill"], outline=col["edge"], width=1)

    # -- audio-detected trace (reuses mv.Spectrogram/band_of/BAND_GATE_DBFS) -
    # Each declared event gets its OWN bounded window (band_windows) rather
    # than one energy gate scanned across the whole file -- see RING_CAP_S's
    # docstring for why the unbounded version painted false multi-second
    # bars in a dense polyphonic render.
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
            color = TRACE_COLOR.get(verdict, TRACE_COLOR["UNVERIFIED"])
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
                dr.line([(xa, y), (max(xb, xa + 1.0), y)], fill=color, width=3)
                i = j + 1

    # -- unexplained-extra ticks (reused verbatim from melody_verify's own
    # extra_scan, not recomputed) ------------------------------------------
    for x_item in report["extra_scan"].get("unexplained", []):
        t_r = x_item["rise_time"]
        f0 = x_item["band_hz"]
        x = x_of(t_r)
        y = y_of(f0)
        dr.line([(x, y - 9), (x, y + 9)], fill=EXTRA_COLOR, width=3)
        dr.ellipse([x - 3, y - 3, x + 3, y + 3], fill=EXTRA_COLOR)

    return strip, duration_total, y_of


def make_legend(width, height):
    """Fixed-size overlay drawn onto every frame (small, cheap)."""
    img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    dr = ImageDraw.Draw(img)
    fnt = font(14)
    fnt_b = font(15, bold=True)
    pad = 10
    lines = [
        ("PASS -- score matched audio", BLOCK["PASS"]["edge"]),
        ("FAIL -- deviation (red)", BLOCK["FAIL"]["edge"]),
        ("UNVERIFIED -- refused (grey)", BLOCK["UNVERIFIED"]["edge"]),
        ("* unexplained audio", EXTRA_COLOR),
    ]
    box_w, box_h = 250, 20 * len(lines) + 12
    dr.rectangle([pad - 4, pad - 4, pad + box_w, pad + box_h], fill=(*LEGEND_BG, 210))
    for n, (text, color) in enumerate(lines):
        y = pad + n * 20
        dr.rectangle([pad, y + 4, pad + 12, y + 14], fill=(*color, 255))
        dr.text((pad + 18, y), text, font=fnt, fill=(*TEXT_MAIN, 255))
    return img


def write_video(strip, duration_total, y_of, width, height, fps, left_pad, pps,
                 wav_path, out_path, ffmpeg, top_margin, bottom_margin):
    legend = make_legend(width, height)
    fnt_t = font(20, bold=True)
    n_frames = int(math.ceil(duration_total * fps))
    strip_w, strip_h = strip.size
    strip_arr = np.asarray(strip)

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
            t = k / fps
            xc = left_pad + t * pps
            left = int(round(xc - width / 2.0))
            left = max(0, min(left, strip_w - width))
            crop = strip_arr[:, left:left + width, :]
            frame = Image.fromarray(crop, "RGB").convert("RGBA")
            frame.alpha_composite(legend)
            dr = ImageDraw.Draw(frame)
            cx = width // 2
            dr.line([(cx, top_margin - 20), (cx, height - bottom_margin + 4)],
                     fill=PLAYHEAD, width=2)
            dr.text((cx + 6, height - bottom_margin + 6), "t=%.2fs" % t,
                     font=fnt_t, fill=TEXT_MAIN)
            out = np.asarray(frame.convert("RGB"))
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
    ap.add_argument("--ffmpeg", default=str(DEFAULT_FFMPEG))
    a = ap.parse_args()

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

    out_path = Path(a.out) if a.out else Path("exports/videos") / (score_path.stem + "_melody_roll.mp4")
    n_frames = write_video(strip, duration_total, y_of, a.width, a.height, a.fps,
                            left_pad, pps, wav_path, out_path, a.ffmpeg,
                            top_margin, bottom_margin)
    size_mb = out_path.stat().st_size / (1024.0 * 1024.0)
    print("[video] %s  frames=%d  duration=%.2fs  size=%.2f MB"
          % (out_path, n_frames, n_frames / a.fps, size_mb))

    if tmpdir:
        tmpdir.cleanup()


if __name__ == "__main__":
    main()
