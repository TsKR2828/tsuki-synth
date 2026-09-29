#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""WF0925-V1 Part B: print, verbatim with line numbers, every source range the
voice-pool report (reports/voice_pool_occupancy_2026-09-25.zh-TW.md section 1)
cites. Line numbers are HEAD (git show HEAD:<file>); for each range the
current working tree is searched for the same text verbatim and the line it
now sits at is printed (other cards may have uncommitted edits that shift
lines). Read-only; judges nothing.

Usage (cwd = repo root):
  python reports/wf0925_method/voice_pool_code_citations.py
"""
import subprocess, sys
from pathlib import Path
REPO = Path(".").resolve()
def head_lines(f):
    return subprocess.run(["git","show","HEAD:"+f],capture_output=True,text=True,encoding="utf-8").stdout.split("\n")
def wt_lines(f):
    return (REPO/f).read_text(encoding="utf-8").split("\n")
cites = [
 ("src/PluginProcessor.cpp",34,36,"pool: Cimbalom addSound + 16-voice loop"),
 ("src/PluginProcessor.cpp",69,71,"pool: Chromatic addSound + 16-voice loop"),
 ("src/PluginProcessor.cpp",103,105,"pool: FM Piano addSound + 16-voice loop"),
 ("src/PluginProcessor.cpp",305,305,"processBlock ScopedNoDenormals"),
 ("src/PluginProcessor.cpp",350,359,"only the selected engine receives MIDI (engine 0/3 -> cimbalomSynth)"),
 ("src/ParameterLayout.cpp",26,28,"engine choice: Cimbalom, Chromatic, FM Piano, Piano"),
 ("src/ParameterLayout.cpp",30,48,"Macro defaults 0.5"),
 ("src/engines/CimbalomEngine.h",246,249,"startNote: Macro scales (1.0 at 0.5)"),
 ("src/engines/CimbalomEngine.h",265,266,"startNote: applyStringDecayTimes(..., dampingOverride=-1, ...)"),
 ("src/engines/CimbalomEngine.h",323,324,"startNote: second applyStringDecayTimes(..., -1, ...)"),
 ("src/engines/CimbalomEngine.h",345,367,"stopNote (tail-off -> applyDamp; steal -> damp(0.002)+clearCurrentNote) and CC64 release"),
 ("src/engines/CimbalomEngine.h",817,870,"renderNextBlock (clearCurrentNote when no string mode / exciter active) + applyDamp damp(0.05)"),
 ("src/engines/ChromaticEngine.h",267,293,"stopNote damp(0.08) / steal / CC64"),
 ("src/engines/ChromaticEngine.h",406,413,"standalone noteOff damp(0.08) (CLI path)"),
 ("src/engines/ChromaticEngine.h",645,672,"renderNextBlock: active = resonator modes or exciter; clearCurrentNote when inactive"),
 ("src/dsp/ModalResonator.h",89,98,"excite: stopAmp = 0.001*start (-60 dB), decayCoeff from decayTime"),
 ("src/dsp/ModalResonator.h",106,117,"damp(factor): decayTime*factor"),
 ("src/dsp/ModalResonator.h",175,181,"processSample: mode skipped once |amp| <= stopAmp"),
 ("src/engines/FMPianoEngine.h",40,48,"FMParams defaults attack 5 ms / release 500 ms"),
 ("src/engines/FMPianoEngine.h",125,146,"startNote release*dmpScale; stopNote tail-off -> ampEnv.noteOff(); steal -> clearCurrentNote"),
 ("src/engines/FMPianoEngine.h",194,215,"renderNextBlock: clearCurrentNote when envelope Idle"),
 ("src/engines/FMPianoEngine.h",393,394,"preset decay / sustain tables"),
 ("src/dsp/Envelope.h",29,42,"noteOff: restarts release from current level whenever state != Idle; isActive"),
 ("src/dsp/Envelope.h",76,85,"Release -> Idle"),
 ("src/score/ScoreRenderer.h",1197,1229,"CLI renderCimbalom: one voice per event, noteOff at 0.9*duration, loop while isActive"),
 ("src/score/ScoreRenderer.h",1310,1311,"CLI chromatic path noteOff at 0.9*duration"),
 ("src/score/ScoreRenderer.h",1559,1590,"eventEndTime: buffer sizing uses 0.05 for every modal engine"),
 ("tests/host_probe.cpp",232,245,"HostProbe renderNotes: note-off at time+duration"),
 ("src/dsp/BodyResonance.h",55,68,"BodyResonance::processSample (runs per sample in every voice's render)"),
]
print("# All line numbers below are HEAD 18430c4. For each range the text in the current working tree")
print("# (which carries other cards' uncommitted edits, e.g. WF0925-K1 in PluginProcessor.cpp / CimbalomEngine.h /")
print("# ChromaticEngine.h / host_probe.cpp) is searched for verbatim: 'WT: identical at line N' = same text, shifted.")
for f,a,b,label in cites:
    h = head_lines(f); w = wt_lines(f)
    block = h[a-1:b]
    # find the same block in WT
    pos = None
    for i in range(len(w)-len(block)+1):
        if w[i:i+len(block)] == block:
            pos = i+1; break
    print("\n=== HEAD:%s:%d-%d  -- %s  [WT: %s]" % (f,a,b,label, ("identical at line %d" % pos) if pos else "NOT FOUND VERBATIM"))
    for k,line in enumerate(block, start=a):
        print("%5d  %s" % (k, line))
