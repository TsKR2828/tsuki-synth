# Antonio Vivaldi — The Four Seasons

TsukiSynth physical-string transcription of all four concertos and twelve movements.

- 28,376 pitched events
- Explicit per-track rests and phrase regions
- Renderer 90% note-off compensation
- Physical string profiles for solo violin, two orchestral violin parts, viola, and cello/continuo

Start with [`vivaldi_four_seasons.catalog.json`](vivaldi_four_seasons.catalog.json).

## Source

Mutopia Project performers' facsimile edition:

- Spring, Music ID 301
- Summer, Music ID 336
- Autumn, Music ID 350
- Winter, Music ID 351

Source typesetting and MIDI: Creative Commons Attribution-ShareAlike 3.0.
The derived score JSON files retain attribution and share-alike licensing metadata.

## Rendering

Render one movement at a time:

```powershell
build\TsukiSynthCLI_artefacts\Release\TsukiSynthCLI.exe `
  scores\classical\vivaldi_four_seasons\spring\vivaldi_four_seasons_spring_m1.score.json `
  --output exports\wav\vivaldi_four_seasons
```

The current string engine is a damped modal-string interpretation, not a sampled or continuously bowed violin model.

## Validation

- 12/12 movement files pass the extended Score v1 JSON Schema.
- 28,376/28,376 events have sorted, finite timing.
- Renderer note-off compensation matches intended release times within 0.001 ms.
- Autumn Movement 2 was rendered end-to-end as stereo 48 kHz / 24-bit WAV (159.329 seconds).
