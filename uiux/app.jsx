// app.jsx — TsukiSynth main App + state
// Orchestrates: engine selection, parameters, effects, presets, A/B compare,
// MIDI keyboard. Wires the Tweaks panel for visual variations.

const TWEAK_DEFAULTS = /*EDITMODE-BEGIN*/{
  "background": "twilight",
  "knobStyle": "solid",
  "tabStyle": "filled",
  "moonMotif": "subtle",
  "accentVivid": false,
  "density": "regular",
  "hideTweaksHint": false
}/*EDITMODE-END*/;

function App() {
  const [t, setTweak] = useTweaks(TWEAK_DEFAULTS);

  // ── core state ───────────────────────────────────────────────
  const [activeEngine, setActiveEngine] = React.useState("fm");
  const [params, setParams] = React.useState(DEFAULT_PARAMS);
  const [effects, setEffects] = React.useState(DEFAULT_EFFECTS);
  const [presetIdx, setPresetIdx] = React.useState(0);
  const [presetOpen, setPresetOpen] = React.useState(false);
  const [presetFlash, setPresetFlash] = React.useState(false);
  const [savedToast, setSavedToast] = React.useState(null);

  // A/B slots — each holds a snapshot of {activeEngine, params, effects}
  const [abSlot, setAbSlot] = React.useState("A");
  const slotsRef = React.useRef({
    A: { activeEngine: "fm", params: DEFAULT_PARAMS, effects: DEFAULT_EFFECTS },
    B: null,
  });

  // ── apply preset on init / on dropdown selection ────────────
  React.useEffect(() => {
    const p = PRESETS[0];
    setActiveEngine(p.engine);
    setParams((prev) => ({ ...prev, [p.engine]: { ...prev[p.engine], ...p.params } }));
    setEffects(p.effects);
    // eslint-disable-next-line
  }, []);

  const applyPreset = (idx) => {
    const p = PRESETS[idx];
    setPresetIdx(idx);
    setActiveEngine(p.engine);
    setParams((prev) => ({ ...prev, [p.engine]: { ...prev[p.engine], ...p.params } }));
    setEffects(p.effects);
    setPresetFlash(true);
    setTimeout(() => setPresetFlash(false), 360);
  };

  const stepPreset = (dir) => {
    const next = (presetIdx + dir + PRESETS.length) % PRESETS.length;
    applyPreset(next);
  };

  // ── param updates ──────────────────────────────────────────
  const updateParam = (engineId, key, value) => {
    setParams((prev) => ({
      ...prev,
      [engineId]: { ...prev[engineId], [key]: value },
    }));
  };

  const updateEffect = (group, key, value) => {
    setEffects((prev) => ({
      ...prev,
      [group]: { ...prev[group], [key]: value },
    }));
  };

  // ── A/B logic ──────────────────────────────────────────────
  const switchSlot = (slot) => {
    if (slot === abSlot) return;
    // Save current state into the active slot
    slotsRef.current[abSlot] = { activeEngine, params, effects };
    if (slotsRef.current[slot]) {
      const s = slotsRef.current[slot];
      setActiveEngine(s.activeEngine);
      setParams(s.params);
      setEffects(s.effects);
    } else {
      // First visit to B — initialize from current state
      slotsRef.current[slot] = { activeEngine, params, effects };
    }
    setAbSlot(slot);
  };

  const copyToOther = () => {
    const other = abSlot === "A" ? "B" : "A";
    slotsRef.current[other] = {
      activeEngine,
      params: JSON.parse(JSON.stringify(params)),
      effects: JSON.parse(JSON.stringify(effects)),
    };
    flashToast(`Copied → ${other}`);
  };

  const flashToast = (text) => {
    setSavedToast(text);
    setTimeout(() => setSavedToast(null), 1400);
  };

  // ── derived ────────────────────────────────────────────────
  const eng = ENGINES[activeEngine];
  const accent = t.accentVivid ? eng.accentVivid : eng.accent;
  const schema = PARAM_SCHEMAS[activeEngine];
  const layout = PARAM_LAYOUTS[activeEngine];
  const enginePs = params[activeEngine];
  const preset = PRESETS[presetIdx];

  // Engine subtitle (uppercase, per brief)
  const subtitle = eng.subtitle.toUpperCase();

  // ── render a parameter widget by key ───────────────────────
  const renderParam = (key, isLeft) => {
    if (!key) return <div className="param-spacer" />;
    const s = schema.find((x) => x.key === key);
    const value = enginePs[key];
    const enabled = !s.enabledWhen || s.enabledWhen(enginePs);

    if (s.kind === "combo") {
      return (
        <div className="param param-combo">
          <ComboBox
            label={s.label.toUpperCase()}
            value={value}
            options={s.options}
            accent={accent}
            onChange={(v) => updateParam(activeEngine, key, v)}
          />
        </div>
      );
    }
    // knob
    const heroBoost = s.hero ? 8 : 0;
    const baseSize = t.density === "compact" ? 46 : t.density === "spacious" ? 56 : 52;
    return (
      <div className="param param-knob">
        <div className="param-label">{s.label.toUpperCase()}</div>
        <Knob
          value={value}
          min={s.min}
          max={s.max}
          step={s.step}
          size={baseSize + heroBoost}
          accent={accent}
          unit={s.unit || ""}
          format={s.format}
          disabled={!enabled}
          arcStyle={t.knobStyle}
          onChange={(v) => updateParam(activeEngine, key, v)}
        />
      </div>
    );
  };

  // ── effect knob factory ────────────────────────────────────
  const fxKnob = (group, key, label, opts) => {
    const v = effects[group][key];
    return (
      <div className="param param-knob param-fx">
        <div className="param-label fx-label">{label}</div>
        <Knob
          value={v}
          size={t.density === "compact" ? 32 : 36}
          accent={accent}
          arcStyle={t.knobStyle}
          {...opts}
          onChange={(nv) => updateEffect(group, key, nv)}
        />
      </div>
    );
  };

  const reverbDimmed = effects.reverb.mix < 1;
  const delayDimmed = effects.delay.mix < 1;
  const compDimmed = effects.compressor.ratio <= 1.05;

  // ── moon variant from tweaks
  const moonVariant =
    t.moonMotif === "whisper" ? "crescent"
    : t.moonMotif === "subtle" ? "crescent"
    : t.moonMotif === "featured" ? "phase"
    : t.moonMotif === "kanji" ? "mark"
    : t.moonMotif === "none" ? "none"
    : "crescent";

  return (
    <div
      className={`page bg-${t.background} density-${t.density}`}
      data-screen-label="01 TsukiSynth Plugin"
    >
      <NoiseTexture />

      <div
        className="plugin"
        style={{
          "--accent": accent,
          "--accent-soft": accent + "40",
          "--accent-hover": "#e8c88a",
        }}
      >
        {/* faint moon halo behind the title (only when 'featured') */}
        {t.moonMotif === "featured" && (
          <div className="plugin-halo" style={{ "--accent": accent }} />
        )}

        {/* ─────── Title bar ─────── */}
        <header className="title-bar">
          <div className="title-left">
            <span className="title-moon">
              <MoonIcon variant={moonVariant} size={moonVariant === "phase" ? 20 : 18} color="#d4b896" />
            </span>
            <h1 className="wordmark">TsukiSynth</h1>
          </div>
          <div className="title-sub">
            <span className="sub-engine">{eng.label.toUpperCase()} ENGINE</span>
            <span className="sub-pipe">|</span>
            <span className="sub-tag">{subtitle}</span>
          </div>
        </header>

        {/* ─────── Preset row ─────── */}
        <div className="preset-row">
          <div className="preset-left">
            <div className="preset-step">
              <button className="step-btn" onClick={() => stepPreset(-1)} aria-label="Previous preset">
                <svg width="6" height="9" viewBox="0 0 6 9"><path d="M5 1 L1 4.5 L5 8" fill="none" stroke="currentColor" strokeWidth="1.2" strokeLinecap="round" strokeLinejoin="round" /></svg>
              </button>
              <button className="step-btn" onClick={() => stepPreset(1)} aria-label="Next preset">
                <svg width="6" height="9" viewBox="0 0 6 9"><path d="M1 1 L5 4.5 L1 8" fill="none" stroke="currentColor" strokeWidth="1.2" strokeLinecap="round" strokeLinejoin="round" /></svg>
              </button>
            </div>
            <button
              className={`preset-pill ${presetOpen ? "preset-open" : ""} ${presetFlash ? "preset-flash" : ""}`}
              onClick={() => setPresetOpen((o) => !o)}
            >
              <span className="preset-key">PRESET</span>
              <span className="preset-divider" />
              <span className="preset-name">{preset.name}</span>
              <span className="preset-bank">{preset.bank}</span>
              <svg className="preset-chev" width="8" height="6" viewBox="0 0 8 6">
                <path d="M0 0 L8 0 L4 6 Z" fill="currentColor" />
              </svg>
            </button>
            {presetOpen && (
              <>
                <div className="preset-scrim" onClick={() => setPresetOpen(false)} />
                <div className="preset-menu">
                  {PRESETS.map((p, i) => (
                    <div
                      key={p.name}
                      className={`preset-item ${i === presetIdx ? "preset-item-active" : ""}`}
                      onClick={() => { applyPreset(i); setPresetOpen(false); }}
                    >
                      <span className="preset-engine-dot" style={{ background: ENGINES[p.engine].accent }} />
                      <span className="preset-item-name">{p.name}</span>
                      <span className="preset-item-bank">{p.bank}</span>
                    </div>
                  ))}
                </div>
              </>
            )}
          </div>
          <div className="preset-right">
            <ABCompare slot={abSlot} onSelect={switchSlot} onCopy={copyToOther} />
            <div className="preset-tools">
              <IconBtn label="Save preset" onClick={() => flashToast("Preset saved")}>
                <svg width="12" height="12" viewBox="0 0 14 14" fill="none">
                  <path d="M2 2 H10 L12 4 V12 H2 Z" stroke="currentColor" strokeWidth="1.1" />
                  <path d="M4 2 V5 H9 V2" stroke="currentColor" strokeWidth="1.1" />
                  <rect x="4" y="8" width="6" height="4" stroke="currentColor" strokeWidth="1.1" />
                </svg>
              </IconBtn>
              <IconBtn label="Open preset folder" onClick={() => flashToast("Browser opened")}>
                <svg width="12" height="12" viewBox="0 0 14 14" fill="none">
                  <path d="M1 4 L1 11 H13 V5 H7 L5.5 3.5 H1 Z" stroke="currentColor" strokeWidth="1.1" strokeLinejoin="round" />
                </svg>
              </IconBtn>
            </div>
          </div>
        </div>

        {/* ─────── Engine tabs ─────── */}
        <div className="engine-tabs" data-tab-style={t.tabStyle}>
          {Object.values(ENGINES).map((e) => (
            <EngineTab
              key={e.id}
              id={e.id}
              label={e.label}
              accent={t.accentVivid ? e.accentVivid : e.accent}
              icon={EngineIcons[e.id]}
              active={activeEngine === e.id}
              onClick={() => setActiveEngine(e.id)}
              style={t.tabStyle}
            />
          ))}
        </div>

        {/* ─────── Engine parameters ─────── */}
        <section className="engine-section">
          <SectionDivider label="ENGINE" sub={`${schema.length} params`} />
          <div className={`param-grid eng-${activeEngine}`} key={activeEngine}>
            {layout.map((row, ri) => (
              <div className="param-row" key={ri}>
                <div className="param-cell">{renderParam(row[0], true)}</div>
                <div className="param-cell">{renderParam(row[1], false)}</div>
              </div>
            ))}
          </div>
        </section>

        {/* ─────── Effects section ─────── */}
        <section className="effects-section">
          <SectionDivider label="EFFECTS" />
          <div className="effects-row">
            <EffectPanel title="REVERB" dimmed={reverbDimmed}>
              {fxKnob("reverb", "mix", "MIX", { min: 0, max: 100, step: 0.1, format: (v) => `${v.toFixed(0)}%` })}
              {fxKnob("reverb", "size", "SIZE", { min: 0, max: 100, step: 0.1, format: (v) => `${v.toFixed(0)}%` })}
            </EffectPanel>
            <EffectPanel title="DELAY" dimmed={delayDimmed}>
              {fxKnob("delay", "time", "TIME", { min: 0, max: 2000, step: 1,
                format: (v) => v < 1000 ? `${Math.round(v)}` : `${(v/1000).toFixed(2)}s` })}
              {fxKnob("delay", "feedback", "FB", { min: 0, max: 100, step: 0.1, format: (v) => `${v.toFixed(0)}%` })}
              {fxKnob("delay", "mix", "MIX", { min: 0, max: 100, step: 0.1, format: (v) => `${v.toFixed(0)}%` })}
            </EffectPanel>
            <EffectPanel title="COMPRESSOR" dimmed={compDimmed}>
              {fxKnob("compressor", "threshold", "THRESH", { min: -60, max: 0, step: 0.1, format: (v) => `${v.toFixed(1)}` })}
              {fxKnob("compressor", "ratio", "RATIO", { min: 1, max: 20, step: 0.1, format: (v) => `${v.toFixed(1)}:1` })}
            </EffectPanel>
          </div>
        </section>

        {/* ─────── MIDI keyboard ─────── */}
        <footer className="kb-foot">
          <MidiKeyboard accent={accent} startOctave={3} octaves={2} />
        </footer>

        {/* toast */}
        {savedToast && <div className="toast">{savedToast}</div>}
      </div>

      {/* small hint chip below plugin */}
      {!t.hideTweaksHint && (
        <div className="hint">
          <span className="hint-key">drag</span> a knob vertically to set
          <span className="hint-sep">·</span>
          <span className="hint-key">double-click</span> to reset
          <span className="hint-sep">·</span>
          tap keys to play
        </div>
      )}

      {/* ─────── Tweaks panel ─────── */}
      <TweaksPanel title="Tweaks">
        <TweakSection label="Atmosphere">
          <TweakRadio
            label="Background"
            value={t.background}
            options={[
              { value: "twilight", label: "Twilight" },
              { value: "midnight", label: "Midnight" },
              { value: "ink",      label: "Ink" },
            ]}
            onChange={(v) => setTweak("background", v)}
          />
          <TweakSelect
            label="Moon motif"
            value={t.moonMotif}
            options={[
              { value: "whisper",  label: "Whisper — crescent only" },
              { value: "subtle",   label: "Subtle — default" },
              { value: "featured", label: "Featured — full moon halo" },
              { value: "kanji",    label: "Kanji 月 mark" },
              { value: "none",     label: "None" },
            ]}
            onChange={(v) => setTweak("moonMotif", v)}
          />
        </TweakSection>

        <TweakSection label="Components">
          <TweakSelect
            label="Knob arc"
            value={t.knobStyle}
            options={[
              { value: "solid",     label: "Solid arc" },
              { value: "segmented", label: "Segmented" },
              { value: "dashed",    label: "Dashed" },
              { value: "line",      label: "Indicator only" },
            ]}
            onChange={(v) => setTweak("knobStyle", v)}
          />
          <TweakRadio
            label="Tab style"
            value={t.tabStyle}
            options={[
              { value: "filled",    label: "Filled" },
              { value: "underline", label: "Underline" },
              { value: "pill",      label: "Pill" },
            ]}
            onChange={(v) => setTweak("tabStyle", v)}
          />
          <TweakToggle
            label="Vivid engine accents"
            value={t.accentVivid}
            onChange={(v) => setTweak("accentVivid", v)}
          />
        </TweakSection>

        <TweakSection label="Layout">
          <TweakRadio
            label="Density"
            value={t.density}
            options={[
              { value: "compact",   label: "Compact" },
              { value: "regular",   label: "Regular" },
              { value: "spacious",  label: "Spacious" },
            ]}
            onChange={(v) => setTweak("density", v)}
          />
          <TweakToggle
            label="Hide hint strip"
            value={t.hideTweaksHint}
            onChange={(v) => setTweak("hideTweaksHint", v)}
          />
        </TweakSection>
      </TweaksPanel>
    </div>
  );
}

// ── Section divider ───────────────────────────────────────────────────────
function SectionDivider({ label, sub }) {
  return (
    <div className="divider">
      <span className="divider-label">{label}</span>
      {sub && <span className="divider-sub">{sub}</span>}
      <span className="divider-line" />
    </div>
  );
}

// ── Noise texture overlay (SVG turbulence as CSS mask) ────────────────────
function NoiseTexture() {
  return (
    <svg className="noise-tex" aria-hidden="true">
      <filter id="ts-noise">
        <feTurbulence type="fractalNoise" baseFrequency="0.85" numOctaves="2" stitchTiles="stitch" />
        <feColorMatrix values="0 0 0 0 1  0 0 0 0 0.92  0 0 0 0 0.78  0 0 0 0.5 0" />
      </filter>
      <rect width="100%" height="100%" filter="url(#ts-noise)" />
    </svg>
  );
}

// Mount
ReactDOM.createRoot(document.getElementById("root")).render(<App />);
