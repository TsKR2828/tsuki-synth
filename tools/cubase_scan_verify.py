#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
cubase_scan_verify.py -- ear-free, GUI-free verification that a real Cubase
host has scanned and accepted TsukiSynth (EARFREE_MELODY_GATE_DESIGN L3-3a).

WHY: A9's first manual step was "confirm the host's plugin scan recognises
the plug-in" -- done by eye in Cubase's plugin manager. But Cubase persists
its whole scan result as plain XML:

    %APPDATA%/Steinberg/<Cubase edition>/<... VST3 Cache>/vst3plugins.xml
    %APPDATA%/Steinberg/<Cubase edition>/<... VST3 Cache>/vst3blacklist.xml

so "the host scanned us, classified us as an instrument, and did not
blacklist us" is a text fact, checkable by command output (R1) with no GUI,
no screenshots and no human. What this does NOT prove: audible playback
inside Cubase (L3-3b: AI-driven export + melody_verify) or anything about
binaries never installed to the system VST3 folder (S6 reports that
difference informationally).

Checks:
  S1 an entry whose path ends in TsukiSynth.vst3 exists in vst3plugins.xml
  S2 no TsukiSynth entry exists in vst3blacklist.xml
  S3 the entry has an "Audio Module Class" with an Instrument subcategory
  S4 the entry also has its "Component Controller Class" (complete VST3 pair)
  S5 the cache's recorded executable timestamp matches the installed
     .vst3 file on disk (+/- 5 s: cache stores whole-second UTC) -- i.e. the
     cache describes the binary that is actually installed, not a ghost of
     a replaced one. Missing installed file = FAIL.
  S6 (informational, no verdict) SHA256 of installed binary vs the repo's
     build artefact -- deployment lag is expected on a working tree and is
     not a scan failure.

Exit codes: 0 = S1-S5 all PASS, 1 = any FAIL, 2 = no Cubase cache found.
"""

import argparse
import hashlib
import os
import sys
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path

PLUGIN_BASENAME = "TsukiSynth.vst3"
REPO_ARTEFACT = (Path(__file__).resolve().parents[1] / "build"
                 / "TsukiSynth_artefacts" / "Release" / "VST3"
                 / "TsukiSynth.vst3" / "Contents" / "x86_64-win"
                 / "TsukiSynth.vst3")

results = []


def check(name, ok, message):
    results.append(ok)
    print("[%s] %s: %s" % ("PASS" if ok else "FAIL", name, message))
    return ok


def find_cache_dirs():
    root = Path(os.path.expandvars("%APPDATA%")) / "Steinberg"
    if not root.is_dir():
        return []
    out = []
    for edition in sorted(root.iterdir()):
        if not edition.is_dir() or "cubase" not in edition.name.lower():
            continue
        for sub in sorted(edition.iterdir()):
            if sub.is_dir() and "vst3 cache" in sub.name.lower():
                out.append(sub)
    return out


def tsuki_entries(xml_path):
    if not xml_path.is_file():
        return None
    tree = ET.parse(xml_path)
    return [p for p in tree.getroot().iter("plugin")
            if (p.findtext("path") or "").replace("\\", "/")
                .rstrip("/").endswith("/" + PLUGIN_BASENAME)
            or (p.findtext("path") or "").endswith(PLUGIN_BASENAME)]


def sha256(path, chunk=1 << 20):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while True:
            b = f.read(chunk)
            if not b:
                break
            h.update(b)
    return h.hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cache-dir", help="explicit '... VST3 Cache' directory "
                    "(default: search %%APPDATA%%/Steinberg/Cubase*)")
    a = ap.parse_args()

    dirs = [Path(a.cache_dir)] if a.cache_dir else find_cache_dirs()
    if not dirs:
        print("NO CUBASE VST3 CACHE FOUND under %APPDATA%/Steinberg")
        sys.exit(2)
    cache = dirs[-1]
    print("cache dir: %s" % cache)

    entries = tsuki_entries(cache / "vst3plugins.xml")
    if entries is None:
        print("vst3plugins.xml missing in cache dir")
        sys.exit(2)
    check("S1.scanned", len(entries) >= 1,
          "%d %s entry(ies) in vst3plugins.xml" % (len(entries), PLUGIN_BASENAME))

    black = tsuki_entries(cache / "vst3blacklist.xml")
    check("S2.not_blacklisted", not black,
          "%d entries in vst3blacklist.xml" % (len(black or [])))

    if not entries:
        sys.exit(1)
    e = entries[-1]
    classes = e.findall("class")
    module = [c for c in classes
              if c.findtext("category") == "Audio Module Class"]
    ctrl = [c for c in classes
            if c.findtext("category") == "Component Controller Class"]
    is_inst = any("Instrument" in (c.findtext("subCategories") or "")
                  for c in module)
    check("S3.instrument_class", bool(module) and is_inst,
          "Audio Module Class present, subCategories=%s, version=%s"
          % ([c.findtext("subCategories") for c in module],
             [c.findtext("version") for c in module]))
    check("S4.controller_class", bool(ctrl),
          "Component Controller Class present" if ctrl else "controller class MISSING")

    cached_path = Path((e.findtext("path") or "").replace("/", os.sep))
    ts_text = e.findtext("timestamps/executable") or ""
    ok5 = False
    detail = "no executable timestamp in cache"
    if ts_text and cached_path.is_file():
        cached_ts = datetime.fromisoformat(ts_text.replace("Z", "+00:00"))
        disk_ts = datetime.fromtimestamp(cached_path.stat().st_mtime,
                                         tz=timezone.utc)
        delta = abs((disk_ts - cached_ts).total_seconds())
        ok5 = delta <= 5.0
        detail = ("cache %s vs disk %s (|delta| = %.1f s)"
                  % (cached_ts.isoformat(), disk_ts.isoformat(), delta))
    elif not cached_path.is_file():
        detail = "installed file missing: %s" % cached_path
    check("S5.cache_matches_disk", ok5, detail)

    if cached_path.is_file() and REPO_ARTEFACT.is_file():
        same = sha256(cached_path) == sha256(REPO_ARTEFACT)
        print("[INFO] S6.deploy_lag: installed binary %s repo build artefact"
              % ("==" if same else "!=")
              + ("" if same else
                 " (expected on an uncommitted working tree; redeploy to"
                 " update the host)"))
    else:
        print("[INFO] S6.deploy_lag: skipped (missing %s)"
              % ("installed file" if not cached_path.is_file() else "repo artefact"))

    ok = all(results)
    print("RESULT: " + ("PASS (S1-S5)" if ok else "FAIL"))
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
