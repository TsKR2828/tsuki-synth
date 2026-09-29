#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""WF0925-V1 (open-work:P1-voice-steal) helper: run `--dump-modes` once per
corpus score with an EXPLICIT CLI binary and cache the raw JSON.

Analysis-only. Reads scores, calls the existing CLI flag, writes cache files
under the directory given by --out-dir (meant to be output/wf0925/V1/dumps,
gitignored). Touches nothing under src/, tools/ or tests/.

Corpus = tools/verify_score.py find_all_scores() (the same 75-file list
`verify_score --all` uses), imported, not re-implemented.

Usage:
  python reports/wf0925_method/dump_corpus_modes.py --cli output/wf0925/V1/cli.exe \
      --out-dir output/wf0925/V1/dumps
"""
import argparse
import hashlib
import json
import subprocess
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "tools"))
import verify_score as vs  # noqa: E402  (find_all_scores only)


def cache_name(score_path):
    rel = score_path.resolve().relative_to(REPO).as_posix()
    return rel.replace("/", "__") + ".dump.json"


def sha256_file(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cli", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--root", default=str(REPO),
                    help="tree whose scores/ subfolders are enumerated (default: repo); "
                         "used for the plugin-reachable copy written by "
                         "make_plugin_reachable_scores.py")
    args = ap.parse_args()
    cli = Path(args.cli).resolve()
    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    scores = vs.find_all_scores(Path(args.root).resolve())
    manifest = {"cli": str(cli), "cli_sha256": sha256_file(cli), "root": str(args.root),
                "scores": []}
    print("cli=%s sha256=%s scores=%d" % (cli, manifest["cli_sha256"], len(scores)))
    for sp in scores:
        dst = out / cache_name(sp)
        t0 = time.time()
        r = subprocess.run([str(cli), "--dump-modes", str(sp)], cwd=str(REPO),
                           capture_output=True, text=True, encoding="utf-8",
                           errors="replace")
        dt = time.time() - t0
        ok = r.returncode == 0
        if ok:
            try:
                json.loads(r.stdout)
            except json.JSONDecodeError:
                ok = False
        if ok:
            dst.write_text(r.stdout, encoding="utf-8")
        entry = {"score": sp.resolve().relative_to(REPO).as_posix(),
                 "score_sha256": sha256_file(sp), "rc": r.returncode,
                 "json_ok": ok, "seconds": round(dt, 2),
                 "bytes": len(r.stdout)}
        manifest["scores"].append(entry)
        print("%-90s rc=%d ok=%s %.1fs %d B" % (entry["score"], r.returncode, ok, dt,
                                               entry["bytes"]))
        if not ok:
            print("   stderr: %s" % r.stderr[:500])
    (out / "manifest.json").write_text(json.dumps(manifest, indent=1), encoding="utf-8")
    bad = [e for e in manifest["scores"] if not e["json_ok"]]
    print("done: %d scores, %d failed" % (len(manifest["scores"]), len(bad)))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
