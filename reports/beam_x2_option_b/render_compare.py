#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""WF0925b-BR: render corpus scores with two CLIs (base / noX2) and compare.

Descriptive only (NOT a GATE; no thresholds are applied anywhere here).

For each score: render once with each CLI (same invocation as
reports/gate_outputs/wf0907_method/render_wf_scores.py: `<cli> <score> --output <dir>`),
then record per WAV:
  sha256 (raw file bytes), length, RMS dBFS (mono mixdown, same definition as
  render_wf_scores.py), sample peak dBFS (max |x| over all channels),
  tail energy = sum(x^2)/sr over the mono mixdown AFTER the score's last
  note-off (max over events of time + 0.9*duration, the renderer's own note-off
  rule, ScoreRenderer.h noteOffSample); for a layered score the layer offsets
  come from `--dump-modes` ("layers[].offset_s").  Expressed in dB (re 1 FS^2*s).
Optionally compares the base render's sha256 with a product master WAV
(exports/products/clean_batch2/masters/..., read-only) when --products is given.

Usage (workdir must be outside the repo, CLIs as absolute Windows paths):
  python reports/beam_x2_option_b/render_compare.py --cli-base C:\\...\\cli_base\\TsukiSynthCLI.exe
      --cli-nox2 C:\\...\\cli_noX2\\TsukiSynthCLI.exe --workdir <SCRATCH>\\corpus
      --list corpus|beam|nonbeam --out <csv> [--products]
"""
import argparse
import csv
import hashlib
import json
import os
import subprocess
import sys
import wave
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent
sys.path.insert(0, str(HERE))
from scan_beam_usage import corpus_files, beam_events, load  # noqa: E402


def read_wav(path):
    with wave.open(str(path), "rb") as w:
        sr, n, sw, ch = w.getframerate(), w.getnframes(), w.getsampwidth(), w.getnchannels()
        raw = w.readframes(n)
    if sw == 2:
        data = np.frombuffer(raw, dtype="<i2").astype(np.float64) / 32768.0
    elif sw == 3:
        b = np.frombuffer(raw, dtype=np.uint8).reshape(-1, 3)
        v = (b[:, 0].astype(np.int32) | (b[:, 1].astype(np.int32) << 8)
             | (b[:, 2].astype(np.int32) << 16))
        v[v >= (1 << 23)] -= (1 << 24)
        data = v.astype(np.float64) / (1 << 23)
    elif sw == 4:
        data = np.frombuffer(raw, dtype="<i4").astype(np.float64) / (2 ** 31)
    else:
        raise ValueError("unsupported sampwidth %d" % sw)
    data = data.reshape(-1, ch)
    return sr, data


def sha256_of(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def db(x, floor=1e-30):
    return 10.0 * np.log10(max(x, floor))


def last_note_off(score_path, cli):
    d = load(score_path)
    if d.get("layers"):
        out = subprocess.run([cli, "--dump-modes", str(score_path)], capture_output=True,
                             text=True, encoding="utf-8", errors="replace")
        dump = json.loads(out.stdout)
        t = 0.0
        for layer in dump["layers"]:
            sub = load(Path(score_path).parent / layer["source"])
            for ev in sub.get("events", []) or []:
                t = max(t, layer["offset_s"] + float(ev["time"]) + 0.9 * float(ev.get("duration", 0.0)))
        return t
    return max((float(ev["time"]) + 0.9 * float(ev.get("duration", 0.0))
                for ev in d.get("events", []) or []), default=0.0)


def render(cli, score, outdir):
    outdir.mkdir(parents=True, exist_ok=True)
    for f in outdir.glob("*.wav"):
        f.unlink()
    r = subprocess.run([cli, str(score), "--output", str(outdir)], capture_output=True,
                       text=True, encoding="utf-8", errors="replace")
    wavs = sorted(outdir.glob("*.wav"))
    if r.returncode != 0 or len(wavs) != 1:
        raise RuntimeError("render failed %s rc=%d wavs=%s\n%s\n%s"
                           % (score, r.returncode, wavs, r.stdout[-2000:], r.stderr[-2000:]))
    return wavs[0]


def measure(wav, t_off):
    sr, data = read_wav(wav)
    mono = data.mean(axis=1)
    n = len(mono)
    rms = np.sqrt(np.mean(mono ** 2)) if n else 0.0
    peak = float(np.max(np.abs(data))) if n else 0.0
    i0 = min(n, int(round(t_off * sr)))
    tail = mono[i0:]
    e_tail = float(np.sum(tail ** 2)) / sr
    e_tot = float(np.sum(mono ** 2)) / sr
    return {"len_s": n / sr, "rms_dbfs": 20 * np.log10(max(rms, 1e-12)),
            "peak_dbfs": 20 * np.log10(max(peak, 1e-12)), "tail_s": max(0, n - i0) / sr,
            "tail_e_db": db(e_tail), "total_e_db": db(e_tot)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cli-base", required=True)
    ap.add_argument("--cli-nox2", required=True)
    ap.add_argument("--workdir", required=True)
    ap.add_argument("--list", choices=["corpus", "beam", "nonbeam"], default="corpus")
    ap.add_argument("--out", required=True)
    ap.add_argument("--products", action="store_true")
    a = ap.parse_args()

    workdir = Path(os.path.abspath(a.workdir))
    if str(workdir).lower().startswith(str(REPO).lower() + os.sep):
        sys.exit("refusing to render inside the repo: %s" % workdir)
    files = corpus_files()
    if a.list != "corpus":
        want_beam = a.list == "beam"
        files = [p for p in files if bool(beam_events(p)) == want_beam]

    masters = {}
    if a.products:
        cat = REPO / "exports" / "products" / "clean_batch2" / "catalog.csv"
        with open(cat, encoding="utf-8-sig") as f:
            for c in csv.DictReader(f):
                sp = (REPO / c["score"].replace("\\", "/")).resolve()
                masters[sp] = (c["id"], cat.parent / c["master"].replace("\\", "/"))

    cols = ["score", "beam_events", "t_last_off_s", "sha_base", "sha_nox2", "identical",
            "len_base_s", "len_nox2_s", "rms_base", "rms_nox2", "d_rms_db",
            "peak_base", "peak_nox2", "d_peak_db", "tail_s_base", "tail_s_nox2",
            "tail_e_base_db", "tail_e_nox2_db", "d_tail_e_db",
            "product_id", "master_sha", "base_equals_master"]
    rows = []
    for idx, p in enumerate(files):
        rel = p.resolve().relative_to(REPO).as_posix()
        nbeam = len(beam_events(p))
        t_off = last_note_off(p, a.cli_base)
        res = {}
        for label, cli in (("base", a.cli_base), ("nox2", a.cli_nox2)):
            # short dir names: the CLI writes <wav>.render.json next to the WAV and
            # long scratch paths hit the Windows 260-char limit (seen once).
            wav = render(cli, p, workdir / label[0] / ("%02d" % idx))
            m = measure(wav, t_off)
            m["sha"] = sha256_of(wav)
            res[label] = m
        b, x = res["base"], res["nox2"]
        row = {"score": rel, "beam_events": nbeam, "t_last_off_s": "%.3f" % t_off,
               "sha_base": b["sha"], "sha_nox2": x["sha"], "identical": b["sha"] == x["sha"],
               "len_base_s": "%.3f" % b["len_s"], "len_nox2_s": "%.3f" % x["len_s"],
               "rms_base": "%.3f" % b["rms_dbfs"], "rms_nox2": "%.3f" % x["rms_dbfs"],
               "d_rms_db": "%+.3f" % (x["rms_dbfs"] - b["rms_dbfs"]),
               "peak_base": "%.3f" % b["peak_dbfs"], "peak_nox2": "%.3f" % x["peak_dbfs"],
               "d_peak_db": "%+.3f" % (x["peak_dbfs"] - b["peak_dbfs"]),
               "tail_s_base": "%.3f" % b["tail_s"], "tail_s_nox2": "%.3f" % x["tail_s"],
               "tail_e_base_db": "%.3f" % b["tail_e_db"], "tail_e_nox2_db": "%.3f" % x["tail_e_db"],
               "d_tail_e_db": "%+.3f" % (x["tail_e_db"] - b["tail_e_db"]),
               "product_id": "", "master_sha": "", "base_equals_master": ""}
        mp = masters.get(p.resolve())
        if mp:
            row["product_id"] = mp[0]
            if mp[1].exists():
                row["master_sha"] = sha256_of(mp[1])
                row["base_equals_master"] = row["master_sha"] == b["sha"]
            else:
                row["master_sha"] = "(missing)"
        rows.append(row)
        print("%-72s beam=%4d same=%-5s len %s->%s  RMS %s  peak %s  tail %s dB%s"
              % (rel, nbeam, row["identical"], row["len_base_s"], row["len_nox2_s"],
                 row["d_rms_db"], row["d_peak_db"], row["d_tail_e_db"],
                 ("  master==base:%s" % row["base_equals_master"]) if mp else ""), flush=True)
    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        w.writerows(rows)
    print("files=%d identical=%d changed=%d" % (len(rows), sum(r["identical"] for r in rows),
                                                 sum(not r["identical"] for r in rows)))
    print("wrote", out.name)
    return 0


if __name__ == "__main__":
    sys.exit(main())
