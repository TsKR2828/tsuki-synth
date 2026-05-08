// components.jsx — TsukiSynth UI primitives
// Knob, ComboBox, EngineTab, EffectPanel, MidiKeyboard, MoonIcon, IconBtn

// ─── helpers ────────────────────────────────────────────────────────────────
function tsPolar(cx, cy, r, angle) {
  // 12 o'clock = 0deg, clockwise positive
  const rad = ((angle - 90) * Math.PI) / 180;
  return { x: cx + r * Math.cos(rad), y: cy + r * Math.sin(rad) };
}

function tsArcPath(cx, cy, r, startAngle, endAngle) {
  if (endAngle - startAngle < 0.5) return "";
  const s = tsPolar(cx, cy, r, startAngle);
  const e = tsPolar(cx, cy, r, endAngle);
  const large = endAngle - startAngle > 180 ? 1 : 0;
  return `M ${s.x.toFixed(2)} ${s.y.toFixed(2)} A ${r} ${r} 0 ${large} 1 ${e.x.toFixed(2)} ${e.y.toFixed(2)}`;
}

function tsClamp(v, mn, mx) { return Math.max(mn, Math.min(mx, v)); }
function tsLerp(a, b, t) { return a + (b - a) * t; }

// ─── Knob ───────────────────────────────────────────────────────────────────
// 270deg sweep, 7 o'clock to 5 o'clock. Vertical drag rotates; shift = fine.
function Knob({
  value,
  min = 0,
  max = 1,
  step = 0,
  size = 52,
  accent = "#c49a6c",
  format,
  label,
  unit = "",
  disabled = false,
  hero = false,
  arcStyle = "solid",        // 'solid' | 'segmented' | 'dashed' | 'line'
  onChange,
}) {
  const [hover, setHover] = React.useState(false);
  const [drag, setDrag] = React.useState(false);
  const startRef = React.useRef({ y: 0, val: value });

  const range = max - min;
  const t = range === 0 ? 0 : tsClamp((value - min) / range, 0, 1);
  const startAngle = -135;
  const endAngle = 135;
  const fillEnd = startAngle + t * (endAngle - startAngle);

  const cx = size / 2;
  const cy = size / 2;
  const trackR = size * 0.42;
  const indicatorR = size * 0.32;

  const formatted = format
    ? format(value)
    : (Number.isInteger(step) && step >= 1
      ? String(Math.round(value))
      : value.toFixed(2)) + unit;

  const onPointerDown = (e) => {
    if (disabled) return;
    e.preventDefault();
    e.target.setPointerCapture?.(e.pointerId);
    setDrag(true);
    startRef.current = { y: e.clientY, val: value };
    const move = (ev) => {
      const dy = startRef.current.y - ev.clientY;
      const sens = ev.shiftKey ? 600 : 200;
      const newT = tsClamp(((startRef.current.val - min) / range) + dy / sens, 0, 1);
      let v = min + newT * range;
      if (step > 0) v = Math.round(v / step) * step;
      v = tsClamp(v, min, max);
      onChange(v);
    };
    const up = () => {
      setDrag(false);
      window.removeEventListener("pointermove", move);
      window.removeEventListener("pointerup", up);
    };
    window.addEventListener("pointermove", move);
    window.addEventListener("pointerup", up);
  };

  const onWheel = (e) => {
    if (disabled) return;
    e.preventDefault();
    const delta = -Math.sign(e.deltaY) * (e.shiftKey ? range / 200 : range / 50);
    let v = value + delta;
    if (step > 0) v = Math.round(v / step) * step;
    onChange(tsClamp(v, min, max));
  };

  const onDoubleClick = (e) => {
    if (disabled) return;
    // reset to midpoint as a sensible default
    onChange(min + range * 0.5);
  };

  const tip = tsPolar(cx, cy, indicatorR, fillEnd);
  const dim = disabled ? 0.32 : 1;

  // Build dash array for segmented/dashed arc styles
  const trackCirc = 2 * Math.PI * trackR * (270 / 360);
  let dashArr;
  if (arcStyle === "segmented") {
    const seg = 11;
    dashArr = `${(trackCirc / seg) * 0.7} ${(trackCirc / seg) * 0.3}`;
  } else if (arcStyle === "dashed") {
    dashArr = "2 3";
  }

  return (
    <div className={`knob ${disabled ? "knob-disabled" : ""} ${hero ? "knob-hero" : ""}`}
         style={{ opacity: dim }}>
      {label && <div className="knob-label">{label}</div>}
      <div
        className="knob-dial"
        style={{ width: size, height: size, cursor: disabled ? "default" : (drag ? "ns-resize" : "grab") }}
        onPointerDown={onPointerDown}
        onWheel={onWheel}
        onDoubleClick={onDoubleClick}
        onMouseEnter={() => setHover(true)}
        onMouseLeave={() => setHover(false)}
      >
        <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`} style={{ overflow: "visible" }}>
          <defs>
            <radialGradient id={`knob-face-${accent.replace("#", "")}`} cx="40%" cy="35%" r="70%">
              <stop offset="0%" stopColor="#2a2a44" />
              <stop offset="55%" stopColor="#1d1d33" />
              <stop offset="100%" stopColor="#11111e" />
            </radialGradient>
            <linearGradient id={`knob-arc-${accent.replace("#", "")}`} x1="0" y1="1" x2="1" y2="0">
              <stop offset="0%" stopColor={accent} stopOpacity="0.55" />
              <stop offset="100%" stopColor={accent} stopOpacity="1" />
            </linearGradient>
            <filter id={`knob-glow-${accent.replace("#", "")}`} x="-30%" y="-30%" width="160%" height="160%">
              <feGaussianBlur stdDeviation="1.4" />
            </filter>
          </defs>

          {/* outer subtle ring */}
          <circle cx={cx} cy={cy} r={trackR + 4} fill="none" stroke="rgba(255,255,255,0.025)" strokeWidth="1" />

          {/* unfilled track */}
          {arcStyle !== "line" && (
            <path
              d={tsArcPath(cx, cy, trackR, startAngle, endAngle)}
              fill="none"
              stroke="#10101c"
              strokeWidth="3"
              strokeLinecap="round"
            />
          )}

          {/* filled arc */}
          {arcStyle !== "line" && t > 0.001 && (
            <path
              d={tsArcPath(cx, cy, trackR, startAngle, fillEnd)}
              fill="none"
              stroke={`url(#knob-arc-${accent.replace("#", "")})`}
              strokeWidth="3"
              strokeLinecap="round"
              strokeDasharray={dashArr}
              style={{ filter: hover || drag ? `url(#knob-glow-${accent.replace("#", "")})` : "none" }}
            />
          )}

          {/* face */}
          <circle cx={cx} cy={cy} r={size * 0.34} fill={`url(#knob-face-${accent.replace("#", "")})`}
                  stroke="rgba(0,0,0,0.5)" strokeWidth="0.5" />

          {/* inner highlight ring */}
          <circle cx={cx} cy={cy} r={size * 0.34} fill="none"
                  stroke="rgba(255,255,255,0.05)" strokeWidth="0.5"
                  transform={`translate(0,-0.5)`} />

          {/* indicator line from center toward current angle */}
          <line
            x1={cx} y1={cy}
            x2={tip.x} y2={tip.y}
            stroke={accent}
            strokeWidth={drag ? 2.2 : 1.6}
            strokeLinecap="round"
            opacity={drag ? 1 : 0.92}
          />

          {/* indicator tip dot */}
          <circle cx={tip.x} cy={tip.y} r={drag ? 2.4 : 1.8}
                  fill={drag || hover ? "#e8c88a" : accent} />
        </svg>
      </div>
      <div className={`knob-value ${drag ? "knob-value-active" : ""}`}>{formatted}</div>
    </div>
  );
}

// ─── ComboBox (custom dropdown) ─────────────────────────────────────────────
function ComboBox({ value, options, accent = "#c49a6c", onChange, disabled = false, label }) {
  const [open, setOpen] = React.useState(false);
  const ref = React.useRef(null);
  const btnRef = React.useRef(null);

  React.useEffect(() => {
    if (!open) return;
    const onDoc = (e) => {
      if (ref.current && !ref.current.contains(e.target) && !btnRef.current?.contains(e.target)) {
        setOpen(false);
      }
    };
    const onKey = (e) => { if (e.key === "Escape") setOpen(false); };
    document.addEventListener("mousedown", onDoc);
    document.addEventListener("keydown", onKey);
    return () => {
      document.removeEventListener("mousedown", onDoc);
      document.removeEventListener("keydown", onKey);
    };
  }, [open]);

  return (
    <div className="combo-wrap">
      {label && <div className="combo-label">{label}</div>}
      <button
        ref={btnRef}
        className={`combo ${open ? "combo-open" : ""} ${disabled ? "combo-disabled" : ""}`}
        onClick={() => !disabled && setOpen((o) => !o)}
        disabled={disabled}
        style={{ "--combo-accent": accent }}
      >
        <span className="combo-val">{value}</span>
        <svg width="8" height="6" viewBox="0 0 8 6" className="combo-chev">
          <path d="M0 0 L8 0 L4 6 Z" fill={accent} />
        </svg>
      </button>
      {open && (
        <div ref={ref} className="combo-menu" style={{ "--combo-accent": accent }}>
          {options.map((opt) => (
            <div
              key={opt}
              className={`combo-item ${opt === value ? "combo-item-active" : ""}`}
              onClick={() => { onChange(opt); setOpen(false); }}
            >
              {opt === value && <span className="combo-bar" />}
              <span>{opt}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

// ─── Engine Tab ─────────────────────────────────────────────────────────────
function EngineTab({ id, label, accent, active, icon, onClick, style = "filled" }) {
  return (
    <button
      className={`tab tab-${style} ${active ? "tab-active" : ""}`}
      onClick={onClick}
      style={{
        "--tab-accent": accent,
        "--tab-accent-15": accent + "26",
        "--tab-accent-08": accent + "14",
      }}
    >
      <span className="tab-icon">{icon}</span>
      <span className="tab-label">{label}</span>
    </button>
  );
}

// ─── Effect Panel ───────────────────────────────────────────────────────────
function EffectPanel({ title, children, dimmed }) {
  return (
    <div className={`effect-panel ${dimmed ? "effect-dimmed" : ""}`}>
      <div className="effect-header">
        <span className="effect-title">{title}</span>
      </div>
      <div className="effect-knobs">{children}</div>
    </div>
  );
}

// ─── Engine icons (small line icons drawn inline) ───────────────────────────
const EngineIcons = {
  cimbalom: (
    <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
      <path d="M2 4 L12 4 M2 7 L12 7 M2 10 L12 10" stroke="currentColor" strokeWidth="0.9" strokeLinecap="round" />
      <circle cx="9" cy="2.5" r="1" fill="currentColor" />
      <path d="M9 3.5 L8 6.5" stroke="currentColor" strokeWidth="0.9" strokeLinecap="round" />
    </svg>
  ),
  chromatic: (
    <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
      <path d="M2 7 Q4 3 7 7 T12 7" stroke="currentColor" strokeWidth="0.9" strokeLinecap="round" fill="none" />
      <circle cx="7" cy="7" r="3.2" stroke="currentColor" strokeWidth="0.7" fill="none" opacity="0.5" />
    </svg>
  ),
  fm: (
    <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
      <path d="M1 7 Q3 3 5 7 T9 7 T13 7" stroke="currentColor" strokeWidth="0.9" strokeLinecap="round" fill="none" />
    </svg>
  ),
};

// ─── Moon icon (variant: 'crescent' | 'phase' | 'mark' | 'none') ────────────
function MoonIcon({ variant = "crescent", size = 18, color = "#d4b896" }) {
  if (variant === "none") return null;
  if (variant === "mark") {
    return (
      <span style={{
        fontFamily: "'Noto Serif JP', 'Yu Mincho', serif",
        fontWeight: 400,
        fontSize: size,
        color,
        letterSpacing: 0,
        lineHeight: 1,
      }}>月</span>
    );
  }
  if (variant === "phase") {
    return (
      <svg width={size} height={size} viewBox="0 0 20 20">
        <defs>
          <radialGradient id="moon-phase-g" cx="40%" cy="40%" r="60%">
            <stop offset="0%" stopColor={color} stopOpacity="0.95" />
            <stop offset="100%" stopColor={color} stopOpacity="0.5" />
          </radialGradient>
        </defs>
        <circle cx="10" cy="10" r="8" fill="url(#moon-phase-g)" />
        <circle cx="13.5" cy="10" r="7" fill="#0f0f1a" />
      </svg>
    );
  }
  // default crescent
  return (
    <svg width={size} height={size} viewBox="0 0 20 20">
      <path
        d="M14 3 a8 8 0 1 0 0 14 a6 6 0 0 1 0 -14 z"
        fill={color}
        opacity="0.95"
      />
    </svg>
  );
}

// ─── Icon button (save / load / etc) ───────────────────────────────────────
function IconBtn({ children, onClick, label, active = false }) {
  return (
    <button
      className={`icon-btn ${active ? "icon-btn-active" : ""}`}
      title={label}
      aria-label={label}
      onClick={onClick}
    >
      {children}
    </button>
  );
}

// ─── A/B compare ────────────────────────────────────────────────────────────
function ABCompare({ slot, onSelect, onCopy }) {
  return (
    <div className="ab-compare" role="group" aria-label="A/B compare">
      <button
        className={`ab-btn ${slot === "A" ? "ab-active" : ""}`}
        onClick={() => onSelect("A")}
      >A</button>
      <button
        className={`ab-btn ${slot === "B" ? "ab-active" : ""}`}
        onClick={() => onSelect("B")}
      >B</button>
      <button
        className="ab-copy"
        title="Copy current to other slot"
        onClick={onCopy}
      >
        <svg width="10" height="10" viewBox="0 0 12 12" fill="none">
          <path d="M2 6 L10 6 M7 3 L10 6 L7 9" stroke="currentColor" strokeWidth="1.4"
                strokeLinecap="round" strokeLinejoin="round" />
        </svg>
      </button>
    </div>
  );
}

// ─── MIDI Keyboard ──────────────────────────────────────────────────────────
// Two-octave strip from C3 to C5. Click to play. Maintains a 'last hit' glow
// on the active engine's accent so it feels alive.
function MidiKeyboard({ accent = "#c49a6c", startOctave = 3, octaves = 2, onNote }) {
  // Build keys: white keys laid out in a row, black keys absolutely positioned
  const NOTES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"];
  const keys = [];
  for (let o = 0; o < octaves; o++) {
    for (let i = 0; i < 12; i++) {
      keys.push({ note: NOTES[i], octave: startOctave + o, isBlack: NOTES[i].includes("#") });
    }
  }
  // Add final C
  keys.push({ note: "C", octave: startOctave + octaves, isBlack: false });

  const whites = keys.filter((k) => !k.isBlack);
  const totalWhites = whites.length;
  const whiteW = 100 / totalWhites; // % width per white key

  const [active, setActive] = React.useState({}); // key id -> timestamp
  const triggerKey = (k) => {
    const id = `${k.note}${k.octave}`;
    setActive((a) => ({ ...a, [id]: Date.now() }));
    onNote?.(k);
    setTimeout(() => {
      setActive((a) => {
        const next = { ...a };
        delete next[id];
        return next;
      });
    }, 220);
  };

  const whiteIdxOf = (k) => whites.findIndex((w) => w.note === k.note && w.octave === k.octave);

  // Map each black key to its left position (between white n and n+1)
  const blackKeys = keys.filter((k) => k.isBlack).map((k, idx) => {
    // Find the white key just before this black key
    const i = keys.indexOf(k);
    const prevWhite = keys.slice(0, i).reverse().find((kk) => !kk.isBlack);
    const wIdx = whiteIdxOf(prevWhite);
    return { ...k, leftPct: (wIdx + 1) * whiteW - whiteW * 0.32 };
  });

  return (
    <div className="midi-kb" style={{ "--kb-accent": accent }}>
      <div className="midi-whites">
        {whites.map((k) => {
          const id = `${k.note}${k.octave}`;
          return (
            <div
              key={id}
              className={`midi-white ${active[id] ? "midi-active" : ""} ${k.note === "C" ? "midi-c" : ""}`}
              style={{ width: whiteW + "%" }}
              onPointerDown={() => triggerKey(k)}
            >
              {k.note === "C" && <span className="midi-c-label">C{k.octave}</span>}
            </div>
          );
        })}
      </div>
      <div className="midi-blacks">
        {blackKeys.map((k) => {
          const id = `${k.note}${k.octave}`;
          return (
            <div
              key={id}
              className={`midi-black ${active[id] ? "midi-active" : ""}`}
              style={{ left: k.leftPct + "%", width: whiteW * 0.62 + "%" }}
              onPointerDown={(e) => { e.stopPropagation(); triggerKey(k); }}
            />
          );
        })}
      </div>
    </div>
  );
}

// Export
Object.assign(window, {
  Knob, ComboBox, EngineTab, EffectPanel, EngineIcons,
  MoonIcon, IconBtn, ABCompare, MidiKeyboard,
});
