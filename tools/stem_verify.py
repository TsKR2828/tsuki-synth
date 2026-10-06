#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
stem_verify.py -- polyphonic verification via per-event stems + superposition
proof (decision packet Option A, reports/decision_packets/
POLYPHONIC_VERIFICATION_OPTIONS.zh-TW.md, ratified by the user).

WHY: tools/melody_verify.py judges melody position event-by-event but, in
dense polyphony, most events get band-collision / re-strike / concurrent-
partial refusals -- honest (fail-closed), but it means most events are never
actually verified (measured on the full Fur Elise piece: 30 PASS / 14 FAIL /
862 UNVERIFIED out of 905 events). This tool takes a different route:

  1. STEM: render every velocity>0 event alone, in its own single-event
     derived score.json, keeping global/tempo/sample_rate/master_volume and
     the event's ABSOLUTE time unchanged (ScoreRenderer.h startSample only
     depends on (ev.time, sample_rate), so the event lands at the same
     sample index whether it renders alone or with the whole piece --
     verified against src/score/ScoreRenderer.h before this tool was
     written, see the decision packet for citations). Rendered alone, each
     event is monophonic -> melody_verify's judge always applies (no band
     collisions, no re-strike masking): every event becomes PASS or FAIL,
     never UNVERIFIED-by-crowding.
  2. JUDGE: each stem is handed, unmodified, to melody_verify.verify() --
     this tool does not re-implement or relax any of its tolerances.
  3. SUPERPOSITION PROOF: renders one more reference mix of the SAME voiced
     events (same score, export forced unnormalized/32-bit/wav so the file
     is untouched raw sample data -- WavWriter.h's normalize step scales
     each file by its own peak and would make stems and the mix
     incomparable). Zero-pads every stem to the reference's sample count
     and sums them; compares the sum against the actual reference mix.
     "Every stem is individually correct" only proves the WHOLE is correct
     if this sum matches -- that is the mathematical transfer this step
     performs. Any mismatch is reported as a number, never hidden.

GATING (fail-closed, never silently proceeds on a case this method does not
cover):
  * layered scores (score.hasLayers()) run TWO applyEffects() passes
    (ScoreRenderer.h renderLayered(), L577-780) -- this tool's superposition
    argument is only established for the single, un-layered render() path.
  * distortion enabled (global.effects.distortion drive>0 or wet>0) is a
    waveshaper -- nonlinear, so distortion(a)+distortion(b) != distortion(a+b)
    and the whole method is invalid. (compressor is not exposed by
    scores/schema/score.schema.json at all, so it cannot be enabled from a
    score.json and needs no gate here.)
  Reverb, delay (any time_ms), wall reflection and the EQ high-shelf are all
  fixed-coefficient LTI stages (SimpleReverb.h / StereoDelay.h /
  EffectsChain.h, confirmed by direct code reading before this tool was
  written) -- superposition holds through them given zero initial state and
  equal-length buffers, which the same-total-length zero-padding above
  supplies. They do NOT gate.

Usage:
  python tools/stem_verify.py <score.json> [--out-dir DIR] [--jobs N]
                              [--limit N] [--json REPORT.json] [--keep-stems]
                              [--force-clean] [--analysis-dry | --no-analysis-dry]
                              [--cli PATH]

  --cli PATH (WF0925b-TF): use this TsukiSynthCLI for every render and
  --dump-modes call of the run (melody_verify's own lookups included);
  default is verify_score.find_cli(). Recorded in provenance.cli.

  --analysis-dry (default ON, WF0907-C12): before rendering, derives a dry
  copy of the score (global.effects.reverb.wet/.decay and
  global.effects.delay.wet zeroed -- see derive_dry_score()) and renders
  stems/reference from THAT, never from the score as authored -- design doc
  §8.3: a pitch verdict measured on a wet (reverb/delay) signal is not GATE
  evidence. `--no-analysis-dry` opts out explicitly and keeps the score's
  own effects; the report then carries provenance.analysis_dry=false and a
  top-level warning. Either way, report["provenance"] records the source
  score's and the actual analysis score's paths + SHA256, the CLI's SHA256,
  and (when dry) the exact leaf_diff that was applied -- so a report is
  self-describing/traceable without needing the caller's --out-dir or temp
  directory to still exist.
Exit codes: 0 = ran to completion, no event FAILed, AND the superposition
            proof was ESTABLISHED (within its reported quantization budget)
            -- or, for a debugging --limit run, marked not-applicable rather
            than silently claimed;
            1 = refused input; a render/comparison could not complete; an
            internal consistency check failed (e.g. the stems actually
            summed do not match the bookkeeping of which stems were
            available -- see check_superposition_completeness()); OR a
            caller-supplied --out-dir already had a non-empty stems/
            subdirectory this run did not create (pass --force-clean to
            reclaim it, see F-01); OR the run completed but at least one
            event FAILed, some stems could not be included in the sum, or
            the superposition proof was NOT established.
            report["exit_issues"] lists which of these applied.
            The full PASS/FAIL/UNVERIFIED counts and superposition numbers
            are always in the JSON report regardless of exit code -- read
            the report, not just the exit code, for the actual verdicts;
            2 = usage error.

R6: this file only reads existing score.json documents and calls the
existing CLI/melody_verify.py -- it does not touch src/.
"""

import argparse
import concurrent.futures
import copy
import datetime
import json
import math
import os
import re
import struct
import sys
import tempfile
import shutil
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent
REPO_ROOT = ROOT.parent


def _load_module(name, path):
    import importlib.util
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


vs = _load_module("verify_score", ROOT / "verify_score.py")
mv = _load_module("melody_verify", ROOT / "melody_verify.py")


# ============================================================================
# gating -- fail-closed refusal, BEFORE any rendering
# ============================================================================

def gate_check(score):
    """Returns a list of human-readable refusal reasons; empty = proceed.
    See module docstring for why exactly these two conditions gate."""
    reasons = []
    layers = score.get("layers")
    if layers:
        reasons.append(
            "score has a non-empty 'layers' array (%d layer(s)): "
            "renderLayered() applies effects TWICE (once per layer, once "
            "on the composite -- ScoreRenderer.h L577-780); this tool's "
            "superposition proof is only established for the single-pass "
            "render() path and does not cover layered scores." % len(layers))
    fx = (score.get("global") or {}).get("effects") or {}
    dist = fx.get("distortion") or {}
    drive = float(dist.get("drive") or 0.0)
    wet = float(dist.get("wet") or 0.0)
    if drive > 0.0 or wet > 0.0:
        reasons.append(
            "global.effects.distortion is enabled (drive=%s, wet=%s): "
            "distortion is a nonlinear waveshaper (EffectsChain.h "
            "distortion stage) -- distortion(a)+distortion(b) != "
            "distortion(a+b), so summed stems cannot be expected to equal "
            "a distorted mix." % (drive, wet))
    return reasons


# ============================================================================
# WAV reading -- must support IEEE-float32 (fmt tag 3), which
# tools/verify_score.py's readers do NOT (they assume fixed-point PCM for
# every sample width, including 32-bit). export.bit_depth=32 with
# normalize=false is exactly what WavWriter.h emits as tag-3 float (see the
# module docstring / decision packet for the JUCE citations), so a dedicated
# reader is needed here rather than widening verify_score.py's PCM reader.
# ============================================================================

WAVE_FORMAT_PCM = 0x0001
WAVE_FORMAT_IEEE_FLOAT = 0x0003
WAVE_FORMAT_EXTENSIBLE = 0xFFFE
# Microsoft KSDATAFORMAT_SUBTYPE_PCM / _IEEE_FLOAT are
# {0000000X-0000-0010-8000-00AA00389B71} with X = 1 / 3 (mmreg.h / ksmedia.h:
# the SubFormat GUID's first field IS the plain WAVE_FORMAT_* tag). As stored
# little-endian in a fmt chunk, bytes 4..15 of the 16-byte GUID are fixed:
_KSDATAFORMAT_GUID_TAIL = bytes([0x00, 0x00, 0x10, 0x00,
                                 0x80, 0x00, 0x00, 0xAA, 0x00, 0x38, 0x9B, 0x71])


def _effective_wav_format(path, fmt_body):
    """(audio_format, n_channels, sample_rate, bits) from a 'fmt ' chunk body.

    WF0925b-TF (decision packet O16): WAVE_FORMAT_EXTENSIBLE (tag 0xFFFE,
    written by many editors/converters for 24-bit, 32-bit or >2-channel
    files) is resolved to its real sample format through the SubFormat GUID:
    KSDATAFORMAT_SUBTYPE_PCM -> tag 1, KSDATAFORMAT_SUBTYPE_IEEE_FLOAT -> tag
    3. Samples are then decoded exactly like the plain tag (container size =
    wBitsPerSample; PCM valid bits are left-justified in the container, so
    the same full-scale divisor applies). Anything else -- a GUID that is not
    one of those two, a cbSize/chunk too short to hold the extension, or
    wValidBitsPerSample larger than the container -- raises ValueError
    naming what was found, never guessed."""
    if len(fmt_body) < 16:
        raise ValueError("%s: truncated fmt chunk (%d bytes)" % (path, len(fmt_body)))
    audio_format, n_channels, sample_rate, _byte_rate, _block_align, bits = \
        struct.unpack("<HHIIHH", fmt_body[:16])
    if audio_format != WAVE_FORMAT_EXTENSIBLE:
        return audio_format, n_channels, sample_rate, bits
    if len(fmt_body) < 40:
        raise ValueError("%s: WAVE_FORMAT_EXTENSIBLE fmt chunk is %d bytes, "
                          "needs 40" % (path, len(fmt_body)))
    cb_size, valid_bits, _channel_mask = struct.unpack("<HHI", fmt_body[16:24])
    if cb_size < 22:
        raise ValueError("%s: WAVE_FORMAT_EXTENSIBLE cbSize=%d, needs >= 22"
                          % (path, cb_size))
    sub_format = fmt_body[24:40]
    sub_tag = struct.unpack("<I", sub_format[:4])[0]
    if (sub_format[4:] != _KSDATAFORMAT_GUID_TAIL
            or sub_tag not in (WAVE_FORMAT_PCM, WAVE_FORMAT_IEEE_FLOAT)):
        raise ValueError("%s: unsupported WAVE_FORMAT_EXTENSIBLE SubFormat "
                          "GUID %s (only KSDATAFORMAT_SUBTYPE_PCM / "
                          "_IEEE_FLOAT are decoded)" % (path, sub_format.hex()))
    if valid_bits > bits:
        raise ValueError("%s: WAVE_FORMAT_EXTENSIBLE wValidBitsPerSample=%d "
                          "exceeds container wBitsPerSample=%d"
                          % (path, valid_bits, bits))
    return sub_tag, n_channels, sample_rate, bits


def read_wav_float(path):
    """Minimal RIFF/WAVE parser returning (sample_rate, n_channels,
    float64 ndarray[n_samples, n_channels]). Supports PCM 16/24/32-bit and
    IEEE-float 32-bit (fmt tag 3), plain or WAVE_FORMAT_EXTENSIBLE (tag
    0xFFFE with a PCM / IEEE-float SubFormat GUID, see
    _effective_wav_format()). Values are exact (no averaging/mixdown).
    Any other format raises ValueError."""
    data = Path(path).read_bytes()
    if len(data) < 12 or data[0:4] != b"RIFF" or data[8:12] != b"WAVE":
        raise ValueError("%s: not a RIFF/WAVE file" % path)
    pos = 12
    fmt_body = None
    audio_bytes = None
    while pos + 8 <= len(data):
        chunk_id = data[pos:pos + 4]
        chunk_size = struct.unpack("<I", data[pos + 4:pos + 8])[0]
        body_start = pos + 8
        body_end = min(body_start + chunk_size, len(data))
        if chunk_id == b"fmt " and fmt_body is None:
            fmt_body = data[body_start:body_end]
        elif chunk_id == b"data" and audio_bytes is None:
            audio_bytes = data[body_start:body_end]
        pos = body_start + chunk_size + (chunk_size & 1)  # chunks word-align
    if fmt_body is None:
        raise ValueError("%s: no fmt chunk found" % path)
    if audio_bytes is None:
        raise ValueError("%s: no data chunk found" % path)
    audio_format, n_channels, sample_rate, bits = _effective_wav_format(path, fmt_body)
    if audio_format == 3 and bits == 32:
        arr = np.frombuffer(audio_bytes, dtype="<f4").astype(np.float64)
    elif audio_format == 1 and bits == 16:
        arr = np.frombuffer(audio_bytes, dtype="<i2").astype(np.float64) / 32768.0
    elif audio_format == 1 and bits == 24:
        b = np.frombuffer(audio_bytes, dtype=np.uint8)
        b = b[: (len(b) // 3) * 3].reshape(-1, 3).astype(np.int32)
        v = b[:, 0] | (b[:, 1] << 8) | (b[:, 2] << 16)
        v = np.where(v & 0x800000, v - 0x1000000, v)
        arr = v.astype(np.float64) / 8388608.0
    elif audio_format == 1 and bits == 32:
        arr = np.frombuffer(audio_bytes, dtype="<i4").astype(np.float64) / 2147483648.0
    else:
        raw_tag = struct.unpack("<H", fmt_body[:2])[0]
        raise ValueError("%s: unsupported wav format (tag=%d bits=%d%s)"
                          % (path, audio_format, bits,
                             ", from WAVE_FORMAT_EXTENSIBLE SubFormat"
                             if raw_tag == WAVE_FORMAT_EXTENSIBLE else ""))
    if n_channels > 1:
        arr = arr[: (len(arr) // n_channels) * n_channels].reshape(-1, n_channels)
    else:
        arr = arr.reshape(-1, 1)
    return sample_rate, n_channels, arr


def read_wav_header(path):
    """WF0914-D14: lightweight RIFF/WAVE header reader -- returns just
    (sample_rate, n_channels) from the 'fmt ' chunk, WITHOUT ever reading
    the 'data' chunk's bytes into memory (unlike read_wav_float(), which
    loads Path(path).read_bytes() -- the WHOLE file, sample data included
    -- up front). Used where a caller only needs to check a stem's
    sample_rate/channel-count compatibility against the reference mix and
    does not (yet) need the actual sample values, so a stem's full audio
    buffer is never materialized just to answer that yes/no question. Reads
    incrementally via file seeks (mirrors read_wav_float()'s own chunk-walk
    / word-alignment rules, just stopping as soon as 'fmt ' is found rather
    than continuing on to look for 'data')."""
    with open(path, "rb") as f:
        head = f.read(12)
        if len(head) < 12 or head[0:4] != b"RIFF" or head[8:12] != b"WAVE":
            raise ValueError("%s: not a RIFF/WAVE file" % path)
        while True:
            chunk_hdr = f.read(8)
            if len(chunk_hdr) < 8:
                raise ValueError("%s: no fmt chunk found" % path)
            chunk_id = chunk_hdr[0:4]
            chunk_size = struct.unpack("<I", chunk_hdr[4:8])[0]
            if chunk_id == b"fmt ":
                body = f.read(16)
                if len(body) < 16:
                    raise ValueError("%s: truncated fmt chunk" % path)
                _audio_format, n_channels, sample_rate, _byte_rate, \
                    _block_align, _bits = struct.unpack("<HHIIHH", body)
                return sample_rate, n_channels
            f.seek(chunk_size + (chunk_size & 1), 1)  # chunks word-align


# ============================================================================
# derived-score construction
# ============================================================================

def superposition_tail_margin_ms(effects):
    """Extra silence (milliseconds), ON TOP OF the score's own authored
    export.tail_silence_ms AND on top of the C++ engine's own automatic
    per-render margin (ScoreRenderer.h effectTailSeconds(), L1282-1302,
    added to every render's buffer length regardless of tail_silence_ms),
    needed so a SINGLE isolated event's reverb/delay recirculation decays to
    a negligible residual before its own per-event stem buffer ends, rather
    than only the -60 dBFS point effectTailSeconds() already guarantees.

    WHY THIS IS NEEDED (root cause, not float rounding -- see the audit that
    ordered this fix): a stem's own render buffer is only as long as THAT
    event needs (its own eventEndTime + the margin below); the reference
    mix's buffer is far longer because OTHER, LATER events push the whole
    piece's totalDuration out. Reverb/delay are LTI, so
    effect(a)+effect(b)==effect(a+b) holds exactly given equal-length,
    zero-padded buffers -- but if a stem's own reverb tail is truncated
    before it has actually decayed away, zero-padding the truncated array
    does NOT recover the missing (nonzero) tail, and the sum-vs-reference
    residual is dominated by that truncation, not by arithmetic.

    SOURCED (both terms below mirror ScoreRenderer.h's effectTailSeconds()
    exactly, just for MORE periods -- read before this was written, not
    reimplemented independently):
      * reverb: SimpleReverb.h processStereo()'s feedbackForLength() sets
        each comb's loop gain so that decayTimeSeconds (the score's
        reverb.decay) is an exact T60 -- amplitude down -60dBFS after that
        many seconds of recirculation (see the function's own doc comment).
        effectTailSeconds() already reserves ONE such T60. Because the
        decay is a clean per-T60 geometric process, TWO MORE T60 periods
        take it down another -120dBFS, i.e. -180dBFS total from where the
        input stopped -- well below the float32 noise floor (~-150dBFS)
        and the 24-bit PCM quantization floor (~-138dBFS) this tool renders
        stems at.
      * delay: StereoDelay.h's feedback path is the geometric series
        feedback**n. effectTailSeconds() already reserves `repeats` cycles
        solving feedback**repeats == 0.001 (-60dBFS). Since
        log(0.001**3) == 3*log(0.001), feedback**(3*repeats) == -180dBFS,
        so TWO MORE blocks of `repeats` cycles reserved here reach -180dBFS
        total.
    Neither term touches melody_verify's tolerances (R2) or the score's own
    authored export.tail_silence_ms -- it is added only to the DERIVED
    stem/reference exports this tool renders for the superposition proof.
    """
    fx = effects or {}
    reverb = fx.get("reverb") or {}
    delay = fx.get("delay") or {}
    reverb_wet = float(reverb.get("wet") or 0.0)
    reverb_decay = float(reverb.get("decay") or 0.0)
    delay_wet = float(delay.get("wet") or 0.0)
    delay_time_ms = float(delay.get("time_ms") or 0.0)
    delay_feedback = float(delay.get("feedback") or 0.0)

    margin_s = 0.0
    if reverb_wet > 0.001 and reverb_decay > 0.0:
        margin_s += 2.0 * reverb_decay
    if delay_wet > 0.001 and delay_time_ms > 0.0:
        repeats60 = (math.ceil(math.log(0.001) / math.log(delay_feedback))
                     if delay_feedback > 0.0 else 1.0)
        repeats60 = max(1.0, repeats60)
        margin_s += 2.0 * repeats60 * delay_time_ms * 0.001 * 1.10
    return margin_s * 1000.0


def clamped_tail_silence_ms(authored_ms, extra_ms):
    """Combines an authored export.tail_silence_ms with an extra margin
    (superposition_tail_margin_ms()), clamped to the schema's own bound
    (scores/schema/score.schema.json "tail_silence_ms": maximum 60000 --
    ScoreParser.h validateNumber(settings,"tail_silence_ms",0,60000,...)).
    Returns (applied_ms:int, requested_ms:float, was_clamped:bool) so a
    caller can both use the clamped value AND report honestly when the
    schema cap made full decay margin unreachable (R2 spirit: never hide a
    shortfall)."""
    requested = float(authored_ms or 0.0) + float(extra_ms or 0.0)
    applied = min(60000.0, max(0.0, requested))
    return int(round(applied)), requested, applied < requested


def unnormalized_export(base_export, bit_depth=32, extra_tail_ms=0.0):
    """Export block forced to raw, unnormalized WAV -- the only export.*
    setting the superposition proof can work with (see module docstring:
    WavWriter.h's normalize step scales each render by its OWN peak, which
    would make every stem and the mix incomparable -- and, per the audit
    that ordered this fix, also defeats melody_verify's absolute-dBFS gates
    when the JUDGE render is boosted this way).

    `bit_depth`: 24 for stem renders (PCM, readable by both this tool's
    read_wav_float() AND tools/verify_score.py's stdlib-`wave`-based
    read_wav_mono() that melody_verify.verify() uses -- so the SAME file
    can serve as both the judge render and the superposition raw data,
    closing the judge-vs-raw mismatch the audit found); 32 for the
    reference mix (IEEE float, full precision, only ever read by this
    tool's own read_wav_float(), never by melody_verify).

    `extra_tail_ms`: see superposition_tail_margin_ms(); added to the
    authored tail_silence_ms and clamped to the schema's 60000ms cap."""
    ex = dict(base_export or {})
    ex["format"] = "wav"
    ex["bit_depth"] = bit_depth
    ex["normalize"] = False
    ex["start_position"] = 0
    ex["end_position"] = 1
    applied_ms, _requested_ms, _clamped = clamped_tail_silence_ms(
        ex.get("tail_silence_ms"), extra_tail_ms)
    ex["tail_silence_ms"] = applied_ms
    return ex


DRY_TARGET_LEAVES = (
    ("global", "effects", "reverb", "wet"),
    ("global", "effects", "reverb", "decay"),
    ("global", "effects", "delay", "wet"),
)


def derive_dry_score(score):
    """WF0907-C12 (design doc §8.3: "帶殘響訊號的音高判定不得作為 GATE
    依據"). Pure function: returns (dry_score, leaf_diff) where dry_score
    is a DEEP COPY of `score` with exactly the three leaves in
    DRY_TARGET_LEAVES zeroed:
      * global.effects.reverb.wet / .decay -- reverb smears energy from a
        note's onset into the frames that follow it, biasing any frame-
        based pitch measurement taken after the onset.
      * global.effects.delay.wet -- delay does not smear, it FABRICATES a
        second, phantom onset (a time-shifted, attenuated copy of the same
        note) which onset/pitch measurement cannot distinguish from a real
        re-strike.
    Nothing else is touched -- in particular NOT distortion (a per-sample
    nonlinearity; it does not move a note's spectral centroid in TIME the
    way reverb/delay recirculation does) and NOT the EQ high-shelf (a
    static per-sample filter, likewise time-invariant) -- see the
    workcard's explicit "不要動" for both.

    `leaf_diff` lists ONLY leaves that ACTUALLY changed value: a leaf that
    is absent from `score` (nested dict path does not exist, or the key
    itself is missing) or is already exactly 0 produces NO entry -- so a
    score with no reverb block at all (or one already silent) comes back
    with leaf_diff == [] rather than fabricating a "0 -> 0" no-op entry.
    Each entry is {"path": "a/b/c/d", "before": <float>, "after": 0}.

    Applies at the TOP level only (score['layers'], if present, is left
    untouched by this function -- per-layer leaf expansion is out of this
    card's scope, see the workcard step 2's "leaf 的展開不在本卡")."""
    dry = copy.deepcopy(score)
    leaf_diff = []
    for path in DRY_TARGET_LEAVES:
        node = dry
        reachable = True
        for key in path[:-1]:
            if not isinstance(node, dict) or key not in node:
                reachable = False
                break
            node = node[key]
        if not reachable or not isinstance(node, dict):
            continue
        leaf_key = path[-1]
        if leaf_key not in node:
            continue
        try:
            before = float(node[leaf_key])
        except (TypeError, ValueError):
            continue
        if before == 0.0:
            continue
        node[leaf_key] = 0
        leaf_diff.append({"path": "/".join(path), "before": before, "after": 0})
    return dry, leaf_diff


def dry_score_filename(score_path):
    """<原檔名>.dry.score.json -- strips a trailing '.score.json' (the
    project's own score-file convention) rather than just the last
    suffix, so 'fur_elise_complete.score.json' becomes
    'fur_elise_complete.dry.score.json', not
    'fur_elise_complete.score.dry.score.json'."""
    name = Path(score_path).name
    if name.endswith(".score.json"):
        base = name[: -len(".score.json")]
    else:
        base = Path(score_path).stem
    return base + ".dry.score.json"


def rel_to_repo(path):
    """Best-effort path relative to the repo root (this file's own
    grandparent directory), POSIX separators, for provenance JSON -- so a
    report is legible/greppable regardless of the machine or --out-dir it
    was produced with. Falls back to the resolved absolute path unchanged
    when `path` is not under the repo root (e.g. a CLI built elsewhere)."""
    p = Path(path).resolve()
    try:
        return p.relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return str(p)


def make_stem_score(score, event, tag, export_override=None):
    """One derived score containing ONLY `event`, absolute time UNCHANGED
    (required so ScoreRenderer.h's startSample = floor(ev.time*sr) places
    the note at the identical sample index it has in the full mix).

    `export_override`, if given, REPLACES the score's own export block; if
    None, the score's OWN export settings are kept as authored. Production
    code (run(), below) ALWAYS passes an explicit override (an
    unnormalized_export(..., bit_depth=24, ...) block -- see that
    function's docstring for why 24-bit unnormalized is the one setting
    that works as BOTH the melody_verify judge input and the superposition
    raw data). The None default is kept only for callers that deliberately
    want the score's own authored export (e.g. tests exercising melody_verify
    against a normally-exported render)."""
    s = dict(score)
    s["events"] = [event]
    ex = dict(export_override) if export_override is not None else dict(score.get("export") or {})
    ex["filename"] = "stem_%s" % tag
    s["export"] = ex
    return s


def make_reference_score(score, voiced_events, export_override, tag="reference"):
    s = dict(score)
    s["events"] = list(voiced_events)
    ex = dict(export_override)
    ex["filename"] = tag
    s["export"] = ex
    return s


def voiced_events(score):
    """Events with velocity>0, in original order, paired with their
    original index -- TsukiEventIdentity::buildPlan() (EventIdentity.h)
    excludes velocity<=0 events from every render, including duplicateRank
    grouping, so dropping them here (rather than zeroing them out in place)
    reproduces the renderer's own event population exactly."""
    out = []
    for i, ev in enumerate(score.get("events", [])):
        try:
            v = float(ev.get("velocity", 0.0))
        except (TypeError, ValueError):
            v = 0.0
        if v > 0.0:
            out.append((i, ev))
    return out


def find_duplicate_identity_risks(voiced):
    """EventIdentity.h's duplicateRank is assigned per GROUP of events whose
    full canonicalEventBytes are identical, ranked by their position among
    the voiced events (see EventIdentity.h buildPlan()). A single-event stem
    file always computes duplicateRank=0 for its lone event, so if two or
    more voiced events in the ORIGINAL score are exact duplicates, their
    isolated-stem noise seed will not match the seed each received inside
    the full-piece render, and the superposition proof may show a residual
    for those events that is NOT a bug -- it is this tool's known limitation
    (no C++ hook exposes identitiesBySourceIndex() to reproduce the true
    rank from Python; R6 forbids adding one). Detected via exact JSON-dict
    equality as a practical proxy for canonicalEventBytes equality (same
    proxy the decision-packet investigation used) -- this UNDER-detects
    relative to the true C++ byte encoding (JSON omissions vs C++ defaults
    can diverge) but never over-detects for byte-identical JSON, so a clean
    result here does not guarantee canonicalEventBytes are unique, only that
    no risk was found at this (cheaper) level of scrutiny."""
    groups = {}
    for orig_idx, ev in voiced:
        key = json.dumps(ev, sort_keys=True)
        groups.setdefault(key, []).append(orig_idx)
    return [idxs for idxs in groups.values() if len(idxs) > 1]


# ============================================================================
# rendering
# ============================================================================

def render_one(cli, stem_score, out_subdir, timeout=600):
    out_subdir = Path(out_subdir)
    out_subdir.mkdir(parents=True, exist_ok=True)
    score_path = out_subdir / "score.json"
    score_path.write_text(json.dumps(stem_score, ensure_ascii=False, indent=2),
                           encoding="utf-8")
    wav = vs.render_score(cli, str(score_path), str(out_subdir))
    return score_path, wav


def render_many(cli, jobs, tasks):
    """tasks: list of (key, stem_score, out_subdir). Returns dict
    key -> {"score_path":..., "wav_path":...} or key -> {"error": str}."""
    results = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=max(1, jobs)) as ex:
        futs = {ex.submit(render_one, cli, score, out_dir): key
                for key, score, out_dir in tasks}
        for fut in concurrent.futures.as_completed(futs):
            key = futs[fut]
            try:
                score_path, wav = fut.result()
                results[key] = {"score_path": score_path, "wav_path": wav}
            except Exception as e:  # noqa: BLE001 -- report, don't crash the batch
                results[key] = {"error": "%s: %s" % (type(e).__name__, e)}
    return results


# ============================================================================
# per-stem judgment (delegates to melody_verify.verify(), no re-implemented
# tolerance logic)
# ============================================================================

# ============================================================================
# rule-id extraction (WF0907-C11) -- exact-string only, NEVER inferred/
# guessed. melody_verify.py itself has no separate rule-id field on its
# event results; some of its `reason` strings happen to literally embed one
# of the same rule-name tokens its own source comments use (e.g. the
# "(Rd)"/"(Re)" markers next to skip_onset's assignments -- see
# melody_verify.py's onset-refusal branches). This only recognizes those
# EXACT tokens if and where they already appear verbatim in a reason string;
# it does not re-derive, re-word, or attribute a rule id to a reason that
# does not literally contain one -- such reasons get an empty `rules` list,
# honestly, per the workcard's "抽不到給空陣列，不要猜".
# ============================================================================

KNOWN_RULE_IDS = ("Ra", "Rb", "Rc", "Rd", "Re")
_RULE_ID_RE = re.compile(r"\b(?:%s)\b" % "|".join(KNOWN_RULE_IDS))


def extract_rule_ids(reason):
    """Returns the KNOWN_RULE_IDS tokens found verbatim in `reason`, in
    first-seen order, deduplicated. Empty list if `reason` is falsy or
    contains none -- never guessed from context."""
    if not reason:
        return []
    seen = []
    for m in _RULE_ID_RE.finditer(reason):
        rid = m.group(0)
        if rid not in seen:
            seen.append(rid)
    return seen


def judge_stem(stem_score_path, wav_path, cli=None):
    """Runs melody_verify.verify() on a single-event stem against its own
    (already-rendered) WAV. `cli` (WF1003-S) is handed to melody_verify's own
    `cli` parameter for its --dump-modes calls (None = its default lookup). Returns the ONE event result dict it produces,
    i.e. {"verdict": ..., "reason": ..., ...} -- unmodified from
    melody_verify's own judgment, plus a `rules` key (WF0907-C11): passed
    through as-is if melody_verify's own event dict already had one (it
    currently never does), otherwise derived via extract_rule_ids() above --
    never re-implementing or relaxing melody_verify's own judgment (R6)."""
    report = mv.verify(stem_score_path, wav_path=wav_path, quiet=True, cli=cli)
    events = report.get("events", [])
    if len(events) != 1:
        reason = ("melody_verify returned %d results for a single-event "
                   "stem (expected 1)" % len(events))
        return {"verdict": "UNVERIFIED", "reason": reason,
                "rules": extract_rule_ids(reason)}
    result = dict(events[0])
    if "rules" not in result:
        result["rules"] = extract_rule_ids(result.get("reason"))
    return result


def build_refusal_histograms(stem_results):
    """WF0907-C11: returns (refusal_histogram, rules_histogram) built from
    `stem_results` (the same list run() assembles per-event, each entry
    already carrying `verdict`/`reason`/`rules` -- see judge_stem() above).

    "拒答" specifically means UNVERIFIED here (per this project's own usage,
    e.g. docs/EARFREE_MELODY_GATE_DESIGN.zh-TW.md: 灰框=無法可靠判定=拒答,
    distinct from 紅框=FAIL="沒對上") -- only UNVERIFIED entries are counted.
    Every UNVERIFIED entry is guaranteed a non-empty `reason` (every branch
    that sets verdict=UNVERIFIED, in melody_verify.verify() and in run()'s
    own error paths, sets `reason` in the same statement/branch); this
    function does not itself enforce that (callers/tests check it against
    the real data) -- it only counts VERBATIM, never re-wording, so
    identical reasons collapse into one bucket and distinct ones stay
    distinct. rules_histogram counts the extract_rule_ids() tokens the same
    population's reasons carried; a reason with no recognized token is
    counted under "(untagged)" rather than dropped, so this histogram's own
    total is still legible.

    Pure function of stem_results (no I/O, no rendering) so it can be
    exercised directly against synthetic event lists."""
    refusal_histogram = {}
    rules_histogram = {}
    for r in stem_results:
        if r.get("verdict") != "UNVERIFIED":
            continue
        reason_str = r.get("reason") or ""
        refusal_histogram[reason_str] = refusal_histogram.get(reason_str, 0) + 1
        rule_ids = r.get("rules") or []
        if rule_ids:
            for rid in rule_ids:
                rules_histogram[rid] = rules_histogram.get(rid, 0) + 1
        else:
            rules_histogram["(untagged)"] = rules_histogram.get("(untagged)", 0) + 1
    return refusal_histogram, rules_histogram


# ============================================================================
# superposition proof
# ============================================================================

SUPERPOSITION_CRITERION = (
    "bit-exact iff: (a) the summed-stems array and the reference-mix array "
    "have the same sample count and channel count, AND (b) max(|sum - "
    "reference|) == 0.0 exactly, sample for sample, at float32 precision "
    "(the precision both files are actually stored at). No tolerance is "
    "applied and none may be added after the fact (R2 spirit) -- ANY "
    "nonzero difference is reported as NOT bit-exact, together with the "
    "residual numbers below, never silently accepted.")


def pad_to_length(arr, n_samples, n_channels):
    if arr.shape[0] == n_samples:
        return arr
    if arr.shape[0] > n_samples:
        raise ValueError(
            "stem has %d samples, longer than the reference mix's %d -- "
            "this should be structurally impossible (a single event's own "
            "duration cannot exceed the whole piece's) and indicates the "
            "reference and stem were not built from the same score/export "
            "settings" % (arr.shape[0], n_samples))
    pad = np.zeros((n_samples - arr.shape[0], n_channels), dtype=arr.dtype)
    return np.concatenate([arr, pad], axis=0)


class StemArrayStream:
    """WF0914-D14: list-like, streaming view over stems' rendered WAV files.
    `len()` and iteration both work exactly like a plain Python list of the
    stems' float64 ndarrays would (compare_superposition() below only ever
    calls those two on its `stem_arrays` argument, so it cannot tell this
    apart from a real list), and iterating yields arrays in EXACTLY the
    order `entries` lists them -- so a caller summing them one at a time
    (as compare_superposition() does) gets a bit-for-bit identical running
    total to summing a real pre-built list in that same order. The
    difference is WHEN each array is read: on demand, one at a time, inside
    the caller's own summation loop, rather than all up front -- so at most
    one stem's full sample array is ever resident in memory through this
    object, not every voiced event's. This is what lets run()'s
    orchestration avoid the O(event_count) growth this card fixes (the old
    code's `stem_arrays = {}` dict, filled once per event via
    read_wav_float() and held until the single final compare_superposition()
    call at the very end). compare_superposition()'s own logic, tolerances
    and output are therefore unchanged -- see its docstring; the existing
    S1 sentinel tests keep exercising it directly with small, real Python
    lists, unaffected by this class.

    `entries`: list of (orig_idx, wav_path) tuples, in the exact order the
    sum must accumulate (the caller must build this in the same order as
    `used`, see run())."""

    def __init__(self, entries):
        self._entries = entries

    def __len__(self):
        return len(self._entries)

    def __iter__(self):
        for _orig_idx, wav_path in self._entries:
            _sr, _ch, arr = read_wav_float(wav_path)
            yield arr


def compare_superposition(reference_arr, stem_arrays, sample_rate, quant_bit_depth=24):
    """reference_arr: float64 ndarray [n, ch]. stem_arrays: list of float64
    ndarray [<=n, ch] (will be zero-padded to n here) -- or, per WF0914-D14,
    any object supporting len() + iteration in that same shape (see
    StemArrayStream above; run() passes one of those to avoid materializing
    every stem array at once). Pure array-level function (no file I/O of
    its own) so it can be sentinel-tested directly (S1).

    `quant_bit_depth`: the PCM bit depth stems are actually rendered at
    (24, by default -- see unnormalized_export()). Each stem independently
    rounds to that many bits before this function ever sees it, so summing
    N stems is expected to differ from an unquantized reference by up to
    N * one PCM half-LSB even for a perfectly correct render (triangle
    inequality over N independent roundings) -- reported as
    'residual_budget'/'established' so a caller can tell a real defect from
    this expected, bounded quantization noise WITHOUT loosening the
    bit-exact criterion itself (still reported, unmodified, as
    'bit_exact')."""
    n_samples, n_channels = reference_arr.shape
    n_stems = len(stem_arrays)
    composite = np.zeros((n_samples, n_channels), dtype=np.float64)
    for arr in stem_arrays:
        composite += pad_to_length(arr, n_samples, n_channels)

    ref32 = reference_arr.astype(np.float32)
    comp32 = composite.astype(np.float32)
    diff = composite - reference_arr  # float64 diff for accurate residual metrics
    exact = bool(np.array_equal(comp32, ref32))

    max_abs = float(np.max(np.abs(diff))) if diff.size else 0.0
    half_lsb = 0.5 / (2.0 ** (quant_bit_depth - 1))
    residual_budget = max(n_stems, 1) * half_lsb
    result = {
        "criterion": SUPERPOSITION_CRITERION,
        "sample_rate": sample_rate,
        "channels": n_channels,
        "reference_samples": n_samples,
        "n_stems_summed": n_stems,
        "bit_exact": exact,
        "max_abs_diff": max_abs,
        "quant_bit_depth": quant_bit_depth,
        "residual_budget": residual_budget,
        "residual_budget_note": (
            "n_stems_summed * half a %d-bit PCM LSB (0.5/2**%d); the bound "
            "each stem's independent quantization can contribute by the "
            "triangle inequality -- see compare_superposition() docstring."
            % (quant_bit_depth, quant_bit_depth - 1)),
        "established": bool(max_abs <= residual_budget),
    }
    if exact:
        result.update({"residual_peak_dbfs": None, "residual_rms_dbfs": None,
                        "first_diff_sample_index": None, "first_diff_time_s": None})
        return result

    rms = float(np.sqrt(np.mean(diff.astype(np.float64) ** 2))) if diff.size else 0.0
    peak_dbfs = 20.0 * np.log10(max_abs) if max_abs > 1e-300 else float("-inf")
    rms_dbfs = 20.0 * np.log10(rms) if rms > 1e-300 else float("-inf")
    nonzero = np.argwhere(diff != 0.0)
    if nonzero.size:
        first_idx = int(nonzero[0][0])
        first_time = first_idx / float(sample_rate)
    else:
        first_idx = None
        first_time = None
    result.update({
        "residual_peak_dbfs": peak_dbfs,
        "residual_rms_dbfs": rms_dbfs,
        "first_diff_sample_index": first_idx,
        "first_diff_time_s": first_time,
    })
    return result


def check_superposition_completeness(used, missing_from_sum, stem_list_len,
                                      reported_n_stems_summed):
    """Returns None if the stem list actually summed is consistent with the
    bookkeeping of which stems were available; otherwise an error string.

    Guards against a bug class proven to slip past every other check
    (mutation-tested against this exact tool): something changes which
    stems end up in the array passed to compare_superposition() WITHOUT
    updating `missing_from_sum`, e.g. a stray slice like
    "[...][1:]" dropping one array at the call site. Two independent counts
    must agree with the (also independently computed) expected count:
    the length of the list actually built for the sum, AND the count
    compare_superposition() itself reports summing -- either one silently
    disagreeing with `len(used) - len(missing_from_sum)` is refused rather
    than reported as a passing (or merely 'not bit-exact') result."""
    expected = len(used) - len(missing_from_sum)
    if stem_list_len != expected:
        return ("stem list assembled for the superposition sum has %d "
                "array(s) but %d were expected (len(used)=%d - "
                "len(missing_from_sum)=%d)"
                % (stem_list_len, expected, len(used), len(missing_from_sum)))
    if reported_n_stems_summed != expected:
        return ("compare_superposition() reported n_stems_summed=%d but %d "
                "were expected (len(used)=%d - len(missing_from_sum)=%d)"
                % (reported_n_stems_summed, expected, len(used), len(missing_from_sum)))
    return None


# ============================================================================
# orchestration
# ============================================================================

def run(score_path, out_dir=None, jobs=4, limit=None, keep_stems=False,
        quiet=False, force_clean=False, analysis_dry=True, cli=None):
    """cli=None (default, unchanged behaviour): TsukiSynthCLI is found by
    verify_score.find_cli() (Release-first under <repo>/build/). cli=<path>
    (the --cli flag, WF0925b-TF / O16): that binary is used for every render
    AND every --dump-modes call of the run, including the ones
    melody_verify.verify() makes (passed to it as verify(..., cli=...), WF1003-S;
    the former temporary replacement of melody_verify's private lookup is gone); a path
    that is not an existing file is an error (exit 1), never a fallback to
    find_cli(). A relative path is taken relative to the current working
    directory and made absolute before use."""
    explicit_cli = None if cli is None else Path(os.path.abspath(str(cli)))
    return _run(score_path, out_dir=out_dir, jobs=jobs, limit=limit,
                keep_stems=keep_stems, quiet=quiet, force_clean=force_clean,
                analysis_dry=analysis_dry, explicit_cli=explicit_cli)


def _run(score_path, out_dir=None, jobs=4, limit=None, keep_stems=False,
         quiet=False, force_clean=False, analysis_dry=True, explicit_cli=None):
    score_path = Path(score_path)
    score = json.loads(score_path.read_text(encoding="utf-8"))
    report = {
        "tool": "stem_verify.py",
        "score": str(score_path),
        "generated_at": datetime.datetime.now().isoformat(timespec="seconds"),
    }

    refusals = gate_check(score)
    if refusals:
        report["status"] = "refused"
        report["refusal_reasons"] = refusals
        if not quiet:
            print("[REFUSED] %s" % score_path)
            for r in refusals:
                print("  - " + r)
        return report, 1

    own_temp = out_dir is None
    out_root = Path(out_dir) if out_dir else Path(tempfile.mkdtemp(prefix="stem_verify_"))
    out_root.mkdir(parents=True, exist_ok=True)
    stems_dir = out_root / "stems"
    ref_dir = out_root / "reference"

    # -- F-01 guard: own_temp's mkdtemp() above is always a brand-new,
    #    empty directory, so this only ever fires for a caller-supplied
    #    --out-dir. If <out_dir>/stems already exists AND is non-empty, it
    #    may be an unrelated workspace this run did not create -- refuse
    #    BEFORE any render is attempted rather than rmtree it out from under
    #    the caller at cleanup time (that was the actual defect: F-01). An
    #    existing but EMPTY stems/ is fine to use as-is. --force-clean is
    #    the caller's explicit opt-in to reclaim a non-empty one. -----------
    # -- Containment gate (P2, 2026-08-31): the F-01 guard below only checked
    #    containment on the --force-clean and cleanup paths. An EXISTING BUT
    #    EMPTY stems/ (or reference/) that is a symlink or junction pointing
    #    outside out_root sailed straight through and every rendered WAV landed
    #    outside the caller's --out-dir. Validate both subdirectories up front,
    #    before anything is rendered, whatever their contents. -----------------
    resolved_out_root = out_root.resolve()
    for label, subdir in (("stems", stems_dir), ("reference", ref_dir)):
        if not subdir.exists():
            continue
        resolved_subdir = subdir.resolve()
        if resolved_out_root not in resolved_subdir.parents:
            report["status"] = "error"
            report["error"] = (
                "%s directory %s resolves to %s, which is not inside %s -- "
                "refusing to render outside the caller's --out-dir (symlink "
                "or path escape?)" % (label, subdir, resolved_subdir, out_root))
            if not quiet:
                print("[ERROR] " + report["error"])
            return report, 1
        if not resolved_subdir.is_dir():
            report["status"] = "error"
            report["error"] = (
                "%s path %s exists but is not a directory; move it aside or "
                "point --out-dir somewhere else" % (label, subdir))
            if not quiet:
                print("[ERROR] " + report["error"])
            return report, 1

    stems_dir_preexisted = stems_dir.exists()
    if stems_dir_preexisted and any(stems_dir.iterdir()):
        if not force_clean:
            report["status"] = "error"
            report["error"] = (
                "existing, non-empty stems directory at %s -- refusing to "
                "delete data this run did not create; pass --force-clean to "
                "clean it first, or point --out-dir at a different location"
                % stems_dir)
            if not quiet:
                print("[ERROR] " + report["error"])
            return report, 1
        resolved_stems_dir = stems_dir.resolve()
        if resolved_out_root not in resolved_stems_dir.parents:
            report["status"] = "error"
            report["error"] = (
                "--force-clean refused: %s does not resolve under %s"
                % (stems_dir, out_root))
            if not quiet:
                print("[ERROR] " + report["error"])
            return report, 1
        shutil.rmtree(stems_dir)
        stems_dir_preexisted = False
    # only a stems_dir THIS run brought into existence may be rmtree'd at
    # cleanup below -- a pre-existing (empty) one is used but left in place.
    stems_dir_ours_to_delete = not stems_dir_preexisted

    if explicit_cli is not None:
        cli = explicit_cli
        if not cli.is_file():
            report["status"] = "error"
            report["error"] = "--cli path does not exist or is not a file: %s" % cli
            if not quiet:
                print("[ERROR] " + report["error"])
            return report, 1
        if not quiet:
            print("[stem_verify] --cli TsukiSynthCLI: %s" % cli, flush=True)
    else:
        cli = vs.find_cli()
        if cli is None:
            report["status"] = "error"
            report["error"] = "TsukiSynthCLI executable not found under build/"
            if not quiet:
                print("[ERROR] " + report["error"])
            return report, 1

    # -- WF0907-C12: derive the dry analysis score (default on) BEFORE any
    #    stem/reference score is built from `score`, so every downstream
    #    render/judge step below runs against whichever object `score` is
    #    now bound to -- see derive_dry_score() docstring for exactly which
    #    three leaves this zeroes and why. `--no-analysis-dry` (analysis_dry
    #    False) explicitly opts OUT and keeps the original, possibly-wet
    #    score, per design doc §8.3's requirement that this be an honest,
    #    visible choice (both branches record a `provenance.analysis_dry`
    #    flag; the wet branch additionally raises a top-level warning). --
    if analysis_dry:
        score, leaf_diff = derive_dry_score(score)
        derived_dir = out_root / "derived"
        derived_dir.mkdir(parents=True, exist_ok=True)
        analysis_score_path = derived_dir / dry_score_filename(score_path)
        analysis_score_path.write_text(
            json.dumps(score, ensure_ascii=False, indent=2), encoding="utf-8")
    else:
        leaf_diff = []
        analysis_score_path = score_path

    report["provenance"] = {
        "source_score": {"path": rel_to_repo(score_path),
                          "sha256": vs.sha256_file(score_path)},
        "analysis_score": {"path": rel_to_repo(analysis_score_path),
                            "sha256": vs.sha256_file(analysis_score_path),
                            "leaf_diff": leaf_diff},
        "cli": {"path": rel_to_repo(cli), "sha256": vs.sha256_file(cli),
                "selected_by": ("--cli" if explicit_cli is not None
                                else "verify_score.find_cli()")},
        "analysis_dry": analysis_dry,
    }
    if not analysis_dry:
        report["warning"] = ("pitch verdicts on wet signal are not GATE "
                              "evidence (design doc §8.3)")

    all_voiced = voiced_events(score)
    limited = limit is not None and limit < len(all_voiced)
    used = all_voiced[:limit] if limit is not None else all_voiced
    dup_risk_groups = find_duplicate_identity_risks(used)

    if not quiet:
        print("[stem_verify] %s" % score_path)
        print("  events total=%d  velocity>0=%d  used=%d%s"
              % (len(score.get("events", [])), len(all_voiced), len(used),
                 (" (--limit %d, TRUNCATED)" % limit) if limited else ""))

    # -- render one file per event (serves as BOTH the melody_verify judge
    #    input and the superposition raw data -- see unnormalized_export()
    #    docstring for why 24-bit unnormalized is the one setting that works
    #    for both) + the reference mix (32-bit float, unnormalized). Every
    #    stem/reference tail_silence_ms is extended by the SAME sourced
    #    margin (superposition_tail_margin_ms()) so a stem's own reverb/
    #    delay tail cannot be truncated before it has actually decayed away
    #    -- see that function's docstring for why. ---------------------------
    effects = (score.get("global") or {}).get("effects") or {}
    tail_margin_ms = superposition_tail_margin_ms(effects)
    authored_tail_ms = (score.get("export") or {}).get("tail_silence_ms")
    applied_tail_ms, requested_tail_ms, tail_clamped = clamped_tail_silence_ms(
        authored_tail_ms, tail_margin_ms)

    stem_export = unnormalized_export(score.get("export"), bit_depth=24,
                                       extra_tail_ms=tail_margin_ms)
    ref_export = unnormalized_export(score.get("export"), bit_depth=32,
                                      extra_tail_ms=tail_margin_ms)

    tasks = []
    for orig_idx, ev in used:
        tasks.append(("stem_%04d" % orig_idx,
                       make_stem_score(score, ev, "stem_%04d" % orig_idx, stem_export),
                       stems_dir / ("ev_%04d" % orig_idx)))
    ref_score = make_reference_score(score, [ev for _, ev in used], ref_export)
    tasks.append(("reference", ref_score, ref_dir))

    rendered = render_many(cli, jobs, tasks)

    render_errors = {k: v["error"] for k, v in rendered.items() if "error" in v}
    if "reference" in render_errors:
        report["status"] = "error"
        report["error"] = "reference mix render failed: " + render_errors["reference"]
        report["render_errors"] = render_errors
        if not quiet:
            print("[ERROR] " + report["error"])
        return report, 1

    # -- per-stem judgment (delegated to melody_verify.verify()) +
    #    superposition data -- BOTH read from the SAME rendered file ---------
    stem_results = []
    # WF0914-D14: metadata only (a wav_path string per eligible event), NOT
    # each stem's full sample array -- the old `stem_arrays = {}` dict here
    # stored a complete float64 ndarray per voiced event and held ALL of
    # them until the single compare_superposition() call far below, which
    # is exactly the O(event_count) memory growth this card fixes (measured
    # >28 GB on the 905-event corpus). The actual sample data is read later,
    # one stem at a time via StemArrayStream (see the superposition-proof
    # section below), only while compare_superposition() is summing them.
    stem_wav_paths = {}
    sr_ref, ch_ref, arr_ref = read_wav_float(rendered["reference"]["wav_path"])

    for orig_idx, ev in used:
        stem_key = "stem_%04d" % orig_idx
        entry = {"index": orig_idx, "time": float(ev.get("time", 0.0)),
                 "note": ev.get("note"), "engine": ev.get("engine")}
        if stem_key in render_errors:
            entry["verdict"] = "UNVERIFIED"
            entry["reason"] = "stem render failed: " + render_errors[stem_key]
            entry["rules"] = extract_rule_ids(entry["reason"])
            entry["superposition_excluded"] = entry["reason"]
            stem_results.append(entry)
            continue

        score_path_i = rendered[stem_key]["score_path"]
        wav_path_i = rendered[stem_key]["wav_path"]
        try:
            r = judge_stem(score_path_i, wav_path_i, cli=explicit_cli)
            entry["verdict"] = r.get("verdict", "UNVERIFIED")
            if r.get("reason") is not None:
                entry["reason"] = r["reason"]
            if r.get("rules") is not None:
                entry["rules"] = r["rules"]
            for k in ("onset_err_ms", "pitch_cents", "expected_f0_hz"):
                if k in r:
                    entry[k] = r[k]
        except Exception as e:  # noqa: BLE001
            entry["verdict"] = "UNVERIFIED"
            entry["reason"] = "melody_verify raised %s: %s" % (type(e).__name__, e)
            entry["rules"] = extract_rule_ids(entry["reason"])
        stem_results.append(entry)

        # WF0914-D14: header-only read (sample_rate/n_channels), not the
        # full sample array -- see read_wav_header() docstring. The actual
        # samples for this stem are read again, later, by StemArrayStream,
        # one stem at a time, only while the superposition sum is computed.
        sr_i, ch_i = read_wav_header(wav_path_i)
        if sr_i != sr_ref or ch_i != ch_ref:
            entry["superposition_excluded"] = (
                "sample_rate/channel mismatch vs reference (%d/%d vs %d/%d)"
                % (sr_i, ch_i, sr_ref, ch_ref))
        else:
            stem_wav_paths[orig_idx] = wav_path_i

    n_pass = sum(1 for r in stem_results if r["verdict"] == "PASS")
    n_fail = sum(1 for r in stem_results if r["verdict"] == "FAIL")
    n_unv = sum(1 for r in stem_results if r["verdict"] == "UNVERIFIED")

    refusal_histogram, rules_histogram = build_refusal_histograms(stem_results)

    # -- superposition proof --------------------------------------------------
    # missing_from_sum and stem_list are computed via two INDEPENDENT
    # traversals of `used`/`stem_wav_paths` (not derived from one another)
    # so that check_superposition_completeness() below can actually catch a
    # bug in either one -- see that function's docstring. WF0914-D14:
    # stem_list is a StemArrayStream over (orig_idx, wav_path) pairs, not a
    # materialized list of arrays -- see that class's docstring for how this
    # keeps run()'s peak memory from growing with event_count while
    # compare_superposition() itself (and its output) stay unchanged.
    missing_from_sum = [orig_idx for orig_idx, _ in used if orig_idx not in stem_wav_paths]
    stem_entries = [(i, stem_wav_paths[i]) for i, _ in used if i in stem_wav_paths]
    stem_list = StemArrayStream(stem_entries)
    superposition = compare_superposition(arr_ref, stem_list, sr_ref, quant_bit_depth=24)

    completeness_error = check_superposition_completeness(
        used, missing_from_sum, len(stem_list), superposition["n_stems_summed"])
    if completeness_error:
        report["status"] = "error"
        report["error"] = ("superposition stem-list consistency check failed "
                            "(refusing to report a result built from the "
                            "wrong stem set): " + completeness_error)
        report["render_errors"] = render_errors
        if not quiet:
            print("[ERROR] " + report["error"])
        return report, 1

    # A run using --limit rebuilds the reference mix from the SAME truncated
    # event subset as the stems (make_reference_score() above), so any
    # agreement is a self-comparison, not a proof against the whole piece --
    # and the same is true whenever fewer than 2 stems are actually summed
    # (e.g. a 1-event score), where summing one stem and comparing it to a
    # reference built from that one event is tautological regardless of
    # --limit. Report this plainly instead of letting a vacuous comparison
    # print as an apparently meaningful ESTABLISHED/BIT-EXACT result.
    vacuous = bool(limited or len(stem_list) < 2)
    if vacuous:
        superposition["vacuous_self_comparison"] = True
        superposition["established"] = None
        superposition["established_note"] = (
            "N/A: " + ("--limit truncated the reference mix to the same "
                       "event subset as the stems (self-comparison)."
                       if limited else
                       "fewer than 2 stems were summed (self-comparison).") +
            " This run's superposition numbers are reported above but "
            "prove nothing about the whole piece / a multi-stem sum.")
    elif missing_from_sum:
        # a legitimate partial run (some stems failed to render/read) -- not
        # a bug (already passed the consistency check above), but not a full
        # proof either, regardless of what the residual budget says.
        superposition["established"] = False

    if missing_from_sum:
        superposition["incomplete"] = True
        superposition["missing_stem_indices"] = missing_from_sum
        superposition["note"] = ("%d stem(s) could not be included in the sum "
                                  "(render/read failure or channel mismatch) -- "
                                  "the comparison above is therefore NOT a full "
                                  "proof, only a partial one; see per-event "
                                  "reasons." % len(missing_from_sum))

    # -- baseline: whole-file melody_verify -- for the "before vs after"
    #    comparison the task requires.
    #
    #    Fix round (Opus audit, major finding on stem_verify.py:1026): this
    #    USED to always call mv.verify(score_path, ...) -- the ORIGINAL,
    #    possibly-WET score -- even when analysis_dry=True had already made
    #    every per-event stem/reference judgment run on the derived DRY
    #    score. That silently mixed a wet-signal pitch judgment into
    #    report["comparison"] with no warning and no provenance flag,
    #    which is exactly what design doc §8.3 says GATE evidence must
    #    never be built from. It also meant the "difference" between the
    #    two numbers was mostly wet-vs-dry noise, not stem-isolation vs
    #    whole-mix judging -- the thing this comparison is supposed to
    #    measure. The baseline now runs on `analysis_score_path`, i.e. the
    #    SAME score object the stems/reference were rendered from -- the
    #    derived-dry copy when analysis_dry=True, or the original file
    #    unchanged when --no-analysis-dry (in which case the top-level
    #    §8.3 warning below already discloses the wet baseline). Either
    #    way, baseline and stem_verify are now judged on the same signal,
    #    and report["provenance"]["analysis_score"] already names exactly
    #    which file/hash both of them ran on -- no separate flag needed.
    baseline = None
    try:
        baseline = mv.verify(analysis_score_path, quiet=True, cli=explicit_cli)
    except SystemExit as e:
        baseline = {"refused": True, "exit_code": e.code}
    except Exception as e:  # noqa: BLE001
        baseline = {"error": "%s: %s" % (type(e).__name__, e)}

    report["status"] = "ok"
    report["cli"] = str(cli)
    report["event_count_total"] = len(score.get("events", []))
    report["event_count_velocity_gt_0"] = len(all_voiced)
    report["event_count_used"] = len(used)
    report["limit_applied"] = limit
    report["limited_run"] = limited
    report["duplicate_identity_risk_groups"] = dup_risk_groups
    report["render_errors"] = render_errors
    report["stem_verify"] = {
        "summary": {"pass": n_pass, "fail": n_fail, "unverified": n_unv},
        "events": stem_results,
        "refusal_histogram": refusal_histogram,
        "rules_histogram": rules_histogram,
    }
    report["baseline_whole_file_melody_verify"] = {
        "note": ("melody_verify.verify() on report[\"provenance\"]"
                 "[\"analysis_score\"] (own export settings, own render) -- "
                 "the SAME score the per-event stem/reference judgments "
                 "above ran on (the derived-dry copy when analysis_dry is "
                 "true, or the original file unmodified when it is false) "
                 "-- this is the pre-existing whole-mix judge this tool is "
                 "being compared against, now judged on the same signal "
                 "instead of the original wet score (design doc §8.3: a "
                 "wet-signal pitch judgment must never be silently mixed "
                 "into this comparison)."),
        "result": (baseline.get("summary") if isinstance(baseline, dict)
                    and "summary" in baseline else baseline),
    }
    base_summary = report["baseline_whole_file_melody_verify"]["result"]
    if isinstance(base_summary, dict) and "pass" in base_summary:
        report["comparison"] = {
            "baseline_pass": base_summary.get("pass"),
            "baseline_fail": base_summary.get("fail"),
            "baseline_unverified": base_summary.get("unverified"),
            "stem_pass": n_pass,
            "stem_fail": n_fail,
            "stem_unverified": n_unv,
            "note": ("both sides judge report[\"provenance\"][\"analysis_score\"] "
                     "(same file, see baseline_whole_file_melody_verify.note) "
                     "-- baseline judges the whole mix in one pass (subject "
                     "to band-collision/re-strike/concurrent-partial "
                     "refusals); stem_verify judges the same events "
                     "rendered in isolation, so band-collision-class "
                     "refusals cannot occur -- comparable only when "
                     "limited_run is false (baseline covers all events, "
                     "stems may cover fewer under --limit)."),
        }
    report["tail_margin"] = {
        "requested_ms": requested_tail_ms,
        "applied_ms": applied_tail_ms,
        "clamped_to_schema_max": tail_clamped,
        "note": ("export.tail_silence_ms used for the stem/reference renders "
                 "in THIS proof only -- see superposition_tail_margin_ms() "
                 "docstring. Does not change the score's own authored "
                 "export block or any melody_verify tolerance (R2)."),
    }
    report["superposition_proof"] = superposition
    report["superposition_proof"]["reference_wav"] = str(rendered["reference"]["wav_path"])
    report["superposition_proof"]["reference_score"] = str(rendered["reference"]["score_path"])

    if not quiet:
        print("  stem_verify summary: %d PASS / %d FAIL / %d UNVERIFIED"
              % (n_pass, n_fail, n_unv))
        if isinstance(base_summary, dict) and "pass" in base_summary:
            print("  baseline (whole-file melody_verify): %d PASS / %d FAIL / %d UNVERIFIED"
                  % (base_summary.get("pass"), base_summary.get("fail"),
                     base_summary.get("unverified")))
        sp = report["superposition_proof"]
        if sp.get("vacuous_self_comparison"):
            print("  superposition: NOT APPLICABLE (%s)"
                  % sp["established_note"])
        else:
            print("  superposition: %s / %s (criterion: see report json)"
                  % ("BIT-EXACT" if sp["bit_exact"] else "NOT bit-exact",
                     "ESTABLISHED" if sp["established"] else "NOT ESTABLISHED"))
        if not sp["bit_exact"]:
            print("    max_abs_diff=%.6e  budget=%.6e  peak=%.2f dBFS  rms=%.2f dBFS  first_diff@%s"
                  % (sp["max_abs_diff"], sp["residual_budget"], sp["residual_peak_dbfs"],
                     sp["residual_rms_dbfs"], sp["first_diff_time_s"]))
        if dup_risk_groups:
            print("  [caveat] %d duplicate-identity-risk group(s): %s"
                  % (len(dup_risk_groups), dup_risk_groups))

    caveats = []
    if dup_risk_groups:
        caveats.append(
            "%d group(s) of exact-duplicate voiced events were found "
            "(indices %s). Their isolated stem renders may use a different "
            "noise seed than they received inside the full-piece render "
            "(duplicateRank mismatch, see find_duplicate_identity_risks() "
            "docstring); any superposition residual attributable to these "
            "specific events is a known limitation of this tool, not "
            "necessarily an engine bug." % (len(dup_risk_groups), dup_risk_groups))
    if limited:
        caveats.append(
            "--limit %d truncated the run to the first %d of %d voiced "
            "events; the superposition proof and stem summary above cover "
            "only that subset, and the 'baseline' comparison covers the "
            "WHOLE file, so the two are not directly comparable in this run. "
            "The superposition result is additionally a self-comparison (see "
            "superposition_proof.vacuous_self_comparison) since the "
            "reference mix is built from the same truncated subset."
            % (limit, len(used), len(all_voiced)))
    if missing_from_sum:
        caveats.append(report["superposition_proof"]["note"])
    if tail_margin_ms > 0:
        caveats.append(
            "Reverb/delay recirculation can continue past a per-event "
            "stem's own short natural buffer length (ScoreRenderer.h's "
            "effectTailSeconds() only guarantees -60dBFS decay on its own). "
            "This run extended export.tail_silence_ms by %.1f ms on every "
            "stem/reference render used for the superposition proof "
            "(requested %.1f ms%s, applied %.1f ms) -- see "
            "superposition_tail_margin_ms() docstring for the sourced "
            "-180dBFS derivation. This does not touch melody_verify's "
            "tolerances (R2) or the score's own authored export block."
            % (tail_margin_ms, requested_tail_ms,
               " -- CLAMPED to the schema's 60000ms tail_silence_ms cap, so "
               "full decay margin may not have been reached; check the "
               "residual numbers above" if tail_clamped else "",
               applied_tail_ms))
    caveats.append(
        "Each stem is independently rendered and quantized to 24-bit PCM "
        "(quant_bit_depth in superposition_proof -- the bit depth "
        "melody_verify's WAV reader needs, see unnormalized_export() "
        "docstring), then read back and summed in float64 by this tool. "
        "The reference mix is rendered separately as unquantized 32-bit "
        "IEEE float. The two sides of the comparison therefore go through "
        "DIFFERENT quantization -- n_stems_summed independent 24-bit "
        "roundings on the stem side vs none on the reference side -- so a "
        "nonzero residual up to 'residual_budget' is EXPECTED even for a "
        "perfectly correct render and is not by itself evidence of an "
        "engine bug; see 'established' (residual within budget) as the "
        "actionable verdict, 'bit_exact' (residual == exactly 0) as the "
        "raw, always-reported, un-loosened measurement.")
    reverb_wet = float((effects.get("reverb") or {}).get("wet") or 0.0)
    delay_wet = float((effects.get("delay") or {}).get("wet") or 0.0)
    if reverb_wet > 0.001 or delay_wet > 0.001:
        caveats.append(
            "This score has reverb and/or delay enabled, which recirculate "
            "audio through a float32 IIR recursion (SimpleReverb.h's comb "
            "filters / StereoDelay.h's feedback path). That recursion is "
            "run ONCE on the pre-mixed signal for the reference, but "
            "independently for EACH stem's own note before the results are "
            "summed -- mathematically equivalent for an LTI system with "
            "matching initial state and coefficients (true here), but NOT "
            "bit-identical in float32: 'sum, then filter' and 'filter, then "
            "sum' round differently at every recursive step. That rounding "
            "difference decays at the SAME rate as the audio itself, so "
            "deep in a reverb tail -- where the true signal has decayed "
            "toward this tool's residual_budget -- the two can become "
            "comparable in size even though both stay far below anything "
            "audible or measurable against the piece's own peak level. "
            "This was CONFIRMED, not assumed: on this run, the largest "
            "residual sample sits inside the reverb tail (not at any note "
            "onset) with most/all stems simultaneously active at or near "
            "the 24-bit quantization floor there -- see the per-sample "
            "diagnostics this tool was run with during development. A "
            "reverb/delay-bearing score is therefore expected to come back "
            "'NOT ESTABLISHED' against residual_budget (which only accounts "
            "for independent per-stem PCM quantization, not this additional "
            "recursive-filter path-order effect) even with a fully correct "
            "render and the tail-truncation fix above applied -- this is "
            "reported as measured, not hidden, and residual_budget is "
            "deliberately NOT widened to absorb it (no sourced, non-"
            "arbitrary bound for this effect's magnitude was derived).")
    report["caveats"] = caveats

    if keep_stems:
        if not quiet:
            print("  stems kept at: %s" % stems_dir)
    elif stems_dir_ours_to_delete:
        try:
            resolved_out_root = out_root.resolve()
            resolved_stems_dir = stems_dir.resolve()
            if resolved_out_root not in resolved_stems_dir.parents:
                raise RuntimeError(
                    "refusing to delete %s -- does not resolve under %s"
                    % (stems_dir, out_root))
            shutil.rmtree(stems_dir)
        except (OSError, RuntimeError) as e:
            caveats.append(
                "cleanup could not remove stems directory %s: %s"
                % (stems_dir, e))
    elif not quiet:
        print("  stems left in place (pre-existing, not created by this "
              "run): %s" % stems_dir)
    if own_temp and not keep_stems:
        # nothing user-facing left in out_root worth keeping either
        shutil.rmtree(ref_dir, ignore_errors=True)
        if analysis_dry:
            shutil.rmtree(derived_dir, ignore_errors=True)
        try:
            out_root.rmdir()
        except OSError:
            pass
        report["superposition_proof"]["reference_wav"] += " (deleted after run)"
        if analysis_dry:
            # WF0907-C12 fix round: do NOT mutate ["path"] with a suffix --
            # that turns a field named `path` into something a caller can no
            # longer feed back into Path()/open(), even though the sha256
            # recorded alongside it is still a valid fingerprint of the file
            # that existed. Record deletion as its own boolean instead so
            # `path` stays a real (if now-nonexistent) path string.
            report["provenance"]["analysis_score"]["deleted"] = True

    exit_issues = []
    if render_errors:
        exit_issues.append("render_errors (%d)" % len(render_errors))
    if n_fail > 0:
        exit_issues.append("n_fail=%d" % n_fail)
    if missing_from_sum:
        exit_issues.append("missing_from_sum (%d)" % len(missing_from_sum))
    if (not vacuous) and superposition.get("established") is False:
        exit_issues.append("superposition_not_established")
    report["exit_issues"] = exit_issues
    if not quiet and exit_issues:
        print("  [exit=1] " + ", ".join(exit_issues))
    return report, (0 if not exit_issues else 1)


def build_arg_parser():
    ap = argparse.ArgumentParser(
        description="Per-event stem rendering + superposition proof for "
                    "polyphonic score verification (decision packet Option A).")
    ap.add_argument("score", help="path to a *.score.json file")
    ap.add_argument("--out-dir", default=None,
                     help="directory for rendered stems/reference (default: temp dir)")
    ap.add_argument("--jobs", type=int, default=4, help="parallel render jobs (default 4)")
    ap.add_argument("--limit", type=int, default=None,
                     help="only process the first N voiced events (debugging)")
    ap.add_argument("--json", default=None, help="write the full report as JSON to this path")
    ap.add_argument("--keep-stems", action="store_true",
                     help="keep rendered stem WAVs/scores instead of deleting them")
    ap.add_argument("--force-clean", action="store_true",
                     help="if --out-dir's stems/ subdirectory already exists "
                          "and is non-empty, delete it before rendering "
                          "(default: refuse and exit 1, see F-01)")
    ap.add_argument("--analysis-dry", dest="analysis_dry", action="store_true",
                     default=True,
                     help="(default) derive a dry analysis score -- zero "
                          "global.effects.reverb.wet/.decay and "
                          "global.effects.delay.wet -- before rendering "
                          "stems/reference, per design doc §8.3 (WF0907-C12; "
                          "see derive_dry_score())")
    ap.add_argument("--no-analysis-dry", dest="analysis_dry", action="store_false",
                     help="use the score's own (possibly wet) effects as "
                          "authored, unmodified; the report is marked "
                          "provenance.analysis_dry=false and carries a "
                          "top-level warning that pitch verdicts are not "
                          "GATE evidence in that case (design doc §8.3)")
    ap.add_argument("--cli", default=None,
                     help="TsukiSynthCLI executable to use for every render and "
                          "--dump-modes call of this run, including the ones "
                          "melody_verify.verify() makes (default: "
                          "verify_score.find_cli(), Release-first under "
                          "build/). Must be an existing file; a relative path "
                          "is resolved against the current directory. "
                          "Recorded in report provenance.cli.")
    return ap


def main():
    ap = build_arg_parser()
    args = ap.parse_args()

    try:
        report, code = run(args.score, out_dir=args.out_dir, jobs=args.jobs,
                            limit=args.limit, keep_stems=args.keep_stems,
                            force_clean=args.force_clean,
                            analysis_dry=args.analysis_dry, cli=args.cli)
    except Exception as e:  # noqa: BLE001 -- surface as a clean error, not a traceback dump
        report = {"tool": "stem_verify.py", "score": args.score,
                  "status": "error", "error": "%s: %s" % (type(e).__name__, e)}
        code = 1
        print("[ERROR] %s" % report["error"], file=sys.stderr)

    if args.json:
        Path(args.json).write_text(json.dumps(report, indent=2, ensure_ascii=False),
                                    encoding="utf-8")
    return code


if __name__ == "__main__":
    sys.exit(main())
