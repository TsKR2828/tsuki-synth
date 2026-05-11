// engines.jsx — TsukiSynth engine definitions, presets, defaults

const ENGINES = {
  cimbalom: {
    id: "cimbalom",
    label: "Cimbalom",
    subtitle: "Physical Modeling String",
    accent: "#c49a6c",
    accentVivid: "#d8a878",
    accentSubtle: "#a3825b",
  },
  chromatic: {
    id: "chromatic",
    label: "Chromatic",
    subtitle: "Beam / Plate / Custom",
    accent: "#8bb8a8",
    accentVivid: "#a3d2c0",
    accentSubtle: "#719b8c",
  },
  fm: {
    id: "fm",
    label: "FM Piano",
    subtitle: "Frequency Modulation Synthesis",
    accent: "#a88bc4",
    accentVivid: "#bda1d6",
    accentSubtle: "#8c73a3",
  },
};

// Parameter schema: each param has {key, kind: 'knob'|'combo', label, ...}
const PARAM_SCHEMAS = {
  cimbalom: [
    { key: "material", kind: "combo", label: "Material",
      options: ["Brass", "Steel", "Bronze", "Copper", "Silver"] },
    { key: "hammer", kind: "combo", label: "Hammer",
      options: ["Soft Felt", "Hard Felt", "Wooden", "Plastic"] },
    { key: "strike", kind: "knob", label: "Strike Position",
      min: 0, max: 100, step: 0.1, unit: "%", hero: false },
    { key: "diameter", kind: "knob", label: "Diameter",
      min: 8, max: 32, step: 0.1, unit: " mm", hero: true },
    { key: "strings", kind: "knob", label: "Strings",
      min: 1, max: 5, step: 1, unit: "" },
    { key: "detuning", kind: "knob", label: "Detuning",
      min: 0, max: 50, step: 0.1, unit: " ¢" },
  ],
  chromatic: [
    { key: "subengine", kind: "combo", label: "Sub-engine",
      options: ["Beam", "Plate", "Water Gong", "Custom"] },
    { key: "material", kind: "combo", label: "Material",
      options: ["Wood", "Glass", "Bronze", "Stone"] },
    { key: "strike", kind: "knob", label: "Strike Pos",
      min: 0, max: 100, step: 0.1, unit: "%" },
    { key: "thickness", kind: "knob", label: "Thickness",
      min: 0.5, max: 12, step: 0.05, unit: " mm" },
    { key: "size", kind: "knob", label: "Size",
      min: 50, max: 300, step: 1, unit: " mm", hero: true },
    { key: "exciter", kind: "combo", label: "Exciter",
      options: ["Mallet", "Bow", "Fingers"] },
    { key: "glide", kind: "knob", label: "Pitch Glide",
      min: 0, max: 100, step: 0.1, unit: "%",
      enabledWhen: (p) => p.subengine === "Water Gong" },
  ],
  fm: [
    { key: "soundType", kind: "combo", label: "Sound Type",
      options: ["Classic DX", "E.Piano", "Bell", "Bass", "Soft Lead"] },
    { key: "ratio", kind: "knob", label: "Ratio",
      min: 0.5, max: 8, step: 0.01, unit: "",
      format: (v) => v.toFixed(2) + ":1" },
    { key: "modIndex", kind: "knob", label: "Mod Index",
      min: 0, max: 12, step: 0.01, unit: "", hero: true,
      format: (v) => v.toFixed(2) },
    { key: "brightness", kind: "knob", label: "Brightness",
      min: 0, max: 100, step: 0.1, unit: "%" },
    { key: "feedback", kind: "knob", label: "Feedback",
      min: 0, max: 7, step: 0.01, unit: "" },
    { key: "attack", kind: "knob", label: "Attack",
      min: 0, max: 2000, step: 1, unit: "",
      format: (v) => v < 1000 ? `${Math.round(v)} ms` : `${(v/1000).toFixed(2)} s` },
    { key: "release", kind: "knob", label: "Release",
      min: 0, max: 3000, step: 1, unit: "",
      format: (v) => v < 1000 ? `${Math.round(v)} ms` : `${(v/1000).toFixed(2)} s` },
  ],
};

// Layout: rows of [left, right] keys per the design guide
const PARAM_LAYOUTS = {
  cimbalom: [
    ["material", "hammer"],
    ["strike", "diameter"],
    ["strings", "detuning"],
  ],
  chromatic: [
    ["subengine", "material"],
    ["strike", "thickness"],
    ["size", "exciter"],
    ["glide", null],
  ],
  fm: [
    ["soundType", null],
    ["ratio", "modIndex"],
    ["brightness", "feedback"],
    ["attack", "release"],
  ],
};

// Default state per engine
const DEFAULT_PARAMS = {
  cimbalom: {
    material: "Brass", hammer: "Soft Felt",
    strike: 35, diameter: 22, strings: 3, detuning: 6.5,
  },
  chromatic: {
    subengine: "Beam", material: "Wood",
    strike: 45, thickness: 3.5, size: 180, exciter: "Mallet", glide: 0,
  },
  fm: {
    soundType: "E.Piano", ratio: 2.00, modIndex: 4.5,
    brightness: 62, feedback: 2.1, attack: 8, release: 480,
  },
};

const DEFAULT_EFFECTS = {
  reverb:     { mix: 28, size: 62 },
  delay:      { time: 380, feedback: 38, mix: 18 },
  compressor: { threshold: -18, ratio: 3.5 },
};

// Curated presets — each preset names the engine + full param snapshot
// + an effects snapshot. All presets selectable from the dropdown.
const PRESETS = [
  {
    name: "Velvet Touch",
    bank: "Init",
    engine: "fm",
    params: {
      soundType: "E.Piano", ratio: 2.00, modIndex: 4.5,
      brightness: 62, feedback: 2.1, attack: 8, release: 480,
    },
    effects: { reverb: { mix: 28, size: 62 }, delay: { time: 380, feedback: 38, mix: 18 }, compressor: { threshold: -18, ratio: 3.5 } },
  },
  {
    name: "Tsukimi Pad",
    bank: "Twilight",
    engine: "fm",
    params: {
      soundType: "Bell", ratio: 3.50, modIndex: 6.8,
      brightness: 48, feedback: 1.4, attack: 240, release: 1800,
    },
    effects: { reverb: { mix: 64, size: 88 }, delay: { time: 540, feedback: 52, mix: 30 }, compressor: { threshold: -22, ratio: 2.8 } },
  },
  {
    name: "Glass Spire",
    bank: "Twilight",
    engine: "fm",
    params: {
      soundType: "Bell", ratio: 4.50, modIndex: 8.2,
      brightness: 78, feedback: 0.8, attack: 4, release: 2400,
    },
    effects: { reverb: { mix: 52, size: 80 }, delay: { time: 420, feedback: 32, mix: 22 }, compressor: { threshold: -16, ratio: 3.0 } },
  },
  {
    name: "Hammered Brass",
    bank: "Forge",
    engine: "cimbalom",
    params: {
      material: "Brass", hammer: "Hard Felt",
      strike: 28, diameter: 24, strings: 4, detuning: 5.2,
    },
    effects: { reverb: { mix: 22, size: 58 }, delay: { time: 320, feedback: 24, mix: 12 }, compressor: { threshold: -14, ratio: 4.5 } },
  },
  {
    name: "Moonlit Cimbalom",
    bank: "Twilight",
    engine: "cimbalom",
    params: {
      material: "Bronze", hammer: "Soft Felt",
      strike: 42, diameter: 28, strings: 3, detuning: 11.0,
    },
    effects: { reverb: { mix: 56, size: 78 }, delay: { time: 480, feedback: 42, mix: 24 }, compressor: { threshold: -20, ratio: 3.0 } },
  },
  {
    name: "Crystal Tongue Drum",
    bank: "Init",
    engine: "chromatic",
    params: {
      subengine: "Beam", material: "Glass",
      strike: 50, thickness: 2.4, size: 160, exciter: "Mallet", glide: 0,
    },
    effects: { reverb: { mix: 38, size: 70 }, delay: { time: 360, feedback: 30, mix: 16 }, compressor: { threshold: -18, ratio: 3.5 } },
  },
  {
    name: "Wooden Plate",
    bank: "Forge",
    engine: "chromatic",
    params: {
      subengine: "Plate", material: "Wood",
      strike: 60, thickness: 5.0, size: 220, exciter: "Mallet", glide: 0,
    },
    effects: { reverb: { mix: 18, size: 48 }, delay: { time: 220, feedback: 18, mix: 8 }, compressor: { threshold: -12, ratio: 5.0 } },
  },
  {
    name: "Water Gong",
    bank: "Twilight",
    engine: "chromatic",
    params: {
      subengine: "Water Gong", material: "Bronze",
      strike: 55, thickness: 6.5, size: 280, exciter: "Mallet", glide: 42,
    },
    effects: { reverb: { mix: 72, size: 92 }, delay: { time: 620, feedback: 48, mix: 32 }, compressor: { threshold: -22, ratio: 2.5 } },
  },
];

Object.assign(window, {
  ENGINES, PARAM_SCHEMAS, PARAM_LAYOUTS,
  DEFAULT_PARAMS, DEFAULT_EFFECTS, PRESETS,
});
