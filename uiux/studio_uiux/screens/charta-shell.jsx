// Shared Charta shell components
// Exposes: Topbar, LeftNav, RightPanel, Panel, Divider, Badge, Button, Corner, ScreenHead

const Corner = ({ pos = 'tl' }) => (
  <div className={`corner ${pos}`}>
    <svg viewBox="0 0 28 28" fill="none" stroke="currentColor" strokeWidth="0.8" style={{ color: 'var(--gold)' }}>
      <path d="M0 14 L0 0 L14 0" />
      <path d="M4 0 L4 4 L0 4" opacity="0.5" />
      <circle cx="2" cy="2" r="0.7" fill="currentColor" />
    </svg>
  </div>
);

const Divider = ({ width = 'auto' }) => (
  <div className="charta-divider" style={{ maxWidth: width }}>
    <span className="diamond"></span>
  </div>
);

const Badge = ({ kind = 'ready', children, dot }) => (
  <span className={`cb ${kind}`}>
    {dot && <span className="dot" />}
    {children}
  </span>
);

const Button = ({ kind = 'ghost', size, children, ...rest }) => (
  <button className={`cbtn ${kind === 'solid' ? 'solid' : kind === 'danger' ? 'danger' : ''} ${size === 'sm' ? 'sm' : ''}`} {...rest}>
    {children}
  </button>
);

const Panel = ({ children, padded, en, zh, headRight, corners, style, className = '' }) => (
  <div className={`charta-panel ${padded ? 'padded' : ''} ${className}`} style={style}>
    {corners && (
      <>
        <Corner pos="tl" />
        <Corner pos="tr" />
        <Corner pos="bl" />
        <Corner pos="br" />
      </>
    )}
    {(en || zh) && (
      <div className="panel-head">
        {en && <span className="en">{en}</span>}
        {zh && <span className="zh">{zh}</span>}
        {headRight && <div style={{ marginLeft: 'auto', display: 'flex', gap: 8, alignItems: 'center' }}>{headRight}</div>}
      </div>
    )}
    {children}
  </div>
);

const ScreenHead = ({ en, zh, right }) => (
  <div className="charta-screen-head" style={{ display: 'flex', alignItems: 'flex-end', gap: 24 }}>
    <div>
      <div className="eyebrow">{en}</div>
      <div className="title">{zh}</div>
    </div>
    {right && <div style={{ marginLeft: 'auto', display: 'flex', gap: 10, alignItems: 'center' }}>{right}</div>}
  </div>
);

const Topbar = ({ project = '欠卡債聯徵無資料怎麼辦', site = 'LoginHeart 金融客戶' }) => (
  <div className="charta-topbar">
    <div className="charta-logo">
      <span>CHARTA · WORKBENCH</span>
      <span className="sub">SEO Content Studio</span>
    </div>
    <div className="charta-context">
      <div className="charta-chip"><span className="label">Site</span><span className="value">{site}</span></div>
      <div className="charta-chip"><span className="label">Project</span><span className="value">{project}</span></div>
      <div className="charta-chip"><span className="label">Guide</span><span className="value">v9.7</span></div>
    </div>
    <div className="charta-status-cluster">
      <Badge kind="done" dot>API READY</Badge>
      <Badge kind="ready">2 / 3 JOBS</Badge>
      <Badge kind="gold">BUDGET $3.20 / $20</Badge>
    </div>
  </div>
);

const NAV_ITEMS = [
  { num: '01', label: '專案總覽', en: 'Overview' },
  { num: '02', label: '任務設定 / 文風指南', en: 'Site Config' },
  { num: '03', label: '建立任務', en: 'New Task' },
  { num: '04', label: '關鍵字 / SERP', en: 'Keyword' },
  { num: '05', label: 'H2 生成', en: 'Body', badge: { text: 'RUNNING', kind: 'running' } },
  { num: '06', label: '審稿', en: 'Review', badge: { text: 'BLOCKED 3', kind: 'blocker' } },
  { num: '07', label: '局部重跑 / Diff', en: 'Refine', badge: { text: 'READY', kind: 'ready' } },
  { num: '08', label: 'KT / FAQ', en: 'Special' },
  { num: '09', label: '內外連', en: 'Links' },
  { num: '10', label: '導出', en: 'Export' },
  { num: '11', label: 'Log / 版本紀錄', en: 'Archive' },
];

const LeftNav = ({ activeNum }) => (
  <div className="charta-leftnav">
    <div className="nav-section">Workflow</div>
    {NAV_ITEMS.map(it => (
      <div key={it.num} className={`nav-item ${it.num === activeNum ? 'active' : ''}`}>
        <span className="num">{it.num}</span>
        <span>{it.label}</span>
        {it.badge && <span className={`nav-badge ${it.badge.kind}`}>{it.badge.text}</span>}
      </div>
    ))}
  </div>
);

const RP = ({ title, children }) => (
  <div className="rp-group">
    <div className="rp-title">{title}</div>
    {children}
  </div>
);
const RPRow = ({ k, v, mono }) => (
  <div className="rp-row">
    <span className="k">{k}</span>
    <span className={`v ${mono ? 'mono' : ''}`}>{v}</span>
  </div>
);

Object.assign(window, { Corner, Divider, Badge, Button, Panel, ScreenHead, Topbar, LeftNav, RP, RPRow, NAV_ITEMS });
