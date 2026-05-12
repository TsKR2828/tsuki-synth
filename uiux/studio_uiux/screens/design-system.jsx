// Design System overview + Modal artboard

const DesignSystem = () => (
  <div className="charta-app" style={{ padding: 36, overflow: 'auto' }}>
    <div style={{ marginBottom: 24 }}>
      <div className="eyebrow" style={{ fontFamily: 'var(--serif-en)', fontSize: 12, letterSpacing: 5, color: 'var(--gold)', textTransform: 'uppercase' }}>CHARTA · DESIGN SYSTEM</div>
      <div style={{ fontSize: 28, fontWeight: 500, color: 'var(--cream)', marginTop: 4 }}>SEO Content Studio · 視覺語彙</div>
    </div>
    <Divider width={180} />

    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 22 }}>
      {/* Color tokens */}
      <Panel en="Color Tokens" zh="色彩系統" corners>
        <div style={{ padding: '18px 22px' }}>
          {[
            ['Base', [['--navy', '#1a2332'], ['--navy-deep', '#111925'], ['--navy-light', '#212d3f'], ['--navy-mid', '#2a3750']]],
            ['Charta Gold', [['--gold', '#c9a961'], ['--gold-dim', '#a08448'], ['--gold-line', 'rgba(201,169,97,.25)'], ['--gold-glow', 'rgba(201,169,97,.12)']]],
            ['Text', [['--cream', '#f5f0e6'], ['--cream-dim', '68%'], ['--cream-muted', '52%'], ['--cream-faint', '35%']]],
            ['Status', [['--ready', '#9bb8d3'], ['--running', '#d8c48a'], ['--success', '#9fbf9b'], ['--blocker', '#d97866'], ['--stale', '#b99ad6']]],
          ].map(([group, items]) => (
            <div key={group} style={{ marginBottom: 14 }}>
              <div style={{ fontFamily: 'var(--serif-en)', fontSize: 10, letterSpacing: 2.5, color: 'var(--gold-dim)', textTransform: 'uppercase', marginBottom: 8 }}>{group}</div>
              <div style={{ display: 'flex', gap: 8 }}>
                {items.map(([n, c]) => (
                  <div key={n} style={{ flex: 1 }}>
                    <div style={{
                      height: 44, border: '1px solid var(--gold-line)',
                      background: c.startsWith('#') ? c : c.includes('rgba') ? c : 'rgba(245,240,230,' + (parseInt(c) / 100) + ')',
                    }}></div>
                    <div style={{ fontFamily: 'var(--mono)', fontSize: 9.5, color: 'var(--cream-muted)', marginTop: 4 }}>{n}</div>
                    <div style={{ fontFamily: 'var(--mono)', fontSize: 9.5, color: 'var(--cream-faint)' }}>{c}</div>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      </Panel>

      {/* Typography */}
      <Panel en="Typography" zh="字體系統" corners>
        <div style={{ padding: '18px 22px' }}>
          <div style={{ marginBottom: 18, paddingBottom: 14, borderBottom: '1px solid var(--gold-line)' }}>
            <div style={{ fontFamily: 'var(--serif-en)', fontSize: 24, fontWeight: 400, letterSpacing: 6, color: 'var(--gold)' }}>CHARTA WORKBENCH</div>
            <div style={{ fontFamily: 'var(--serif-en)', fontSize: 11, letterSpacing: 3, color: 'var(--gold-dim)', marginTop: 4 }}>CORMORANT GARAMOND · 400</div>
          </div>
          <div style={{ marginBottom: 16, paddingBottom: 12, borderBottom: '1px solid var(--gold-line)' }}>
            <div style={{ fontFamily: 'var(--serif)', fontSize: 24, fontWeight: 500, color: 'var(--cream)' }}>欠卡債查不到聯徵</div>
            <div style={{ fontFamily: 'var(--serif-en)', fontSize: 10, letterSpacing: 2.5, color: 'var(--gold-dim)', marginTop: 4 }}>NOTO SERIF TC · 500 · 24px</div>
          </div>
          <div style={{ marginBottom: 16, paddingBottom: 12, borderBottom: '1px solid var(--gold-line)' }}>
            <div style={{ fontFamily: 'var(--serif)', fontSize: 16, fontWeight: 400, color: 'var(--cream)', lineHeight: 2 }}>銀行的內部債權系統與聯合徵信中心的資料庫並非同步運作。</div>
            <div style={{ fontFamily: 'var(--serif-en)', fontSize: 10, letterSpacing: 2.5, color: 'var(--gold-dim)', marginTop: 4 }}>NOTO SERIF TC · 400 · 16px · LH 2.0</div>
          </div>
          <div>
            <div style={{ fontFamily: 'var(--mono)', fontSize: 12, color: 'var(--cream)' }}>fp_3b2d91ef · 9f31a0c7</div>
            <div style={{ fontFamily: 'var(--serif-en)', fontSize: 10, letterSpacing: 2.5, color: 'var(--gold-dim)', marginTop: 4 }}>UI MONOSPACE · HASH / FINGERPRINT</div>
          </div>
        </div>
      </Panel>

      {/* Badges */}
      <Panel en="Badges · Status" zh="狀態藏書票" corners>
        <div style={{ padding: '18px 22px', display: 'flex', flexWrap: 'wrap', gap: 8 }}>
          <Badge kind="ready">NOT STARTED</Badge>
          <Badge kind="queued">QUEUED</Badge>
          <Badge kind="running" dot>RUNNING</Badge>
          <Badge kind="done">DONE</Badge>
          <Badge kind="accepted">ACCEPTED v3</Badge>
          <Badge kind="soft">SOFT STALE</Badge>
          <Badge kind="hard">HARD STALE</Badge>
          <Badge kind="blocked">BLOCKED</Badge>
          <Badge kind="warning">WARNING</Badge>
          <Badge kind="archived">ARCHIVED</Badge>
          <Badge kind="gold">GUIDE v9.7</Badge>
          <Badge kind="solid">PRIMARY</Badge>
        </div>
      </Panel>

      {/* Buttons */}
      <Panel en="Buttons" zh="操作按鈕" corners>
        <div style={{ padding: '18px 22px', display: 'flex', flexDirection: 'column', gap: 14 }}>
          <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap' }}>
            <Button kind="solid">Generate Selected</Button>
            <Button kind="solid">Accept Version</Button>
            <Button kind="solid">Export</Button>
          </div>
          <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap' }}>
            <Button kind="ghost">View Prompt</Button>
            <Button kind="ghost">Compare Versions</Button>
            <Button kind="ghost">View API Log</Button>
          </div>
          <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap' }}>
            <Button kind="danger">Stop Current Job</Button>
            <Button kind="danger">忽略 Blocker</Button>
            <Button kind="danger">清除版本</Button>
          </div>
          <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
            <Button kind="ghost" size="sm">View</Button>
            <Button kind="solid" size="sm">AI Patch</Button>
            <Button kind="ghost" size="sm">Refine</Button>
            <Button kind="danger" size="sm">Reject</Button>
          </div>
        </div>
      </Panel>

      {/* Diff sample */}
      <Panel en="Diff View · 高風險" zh="差異視覺" corners>
        <div style={{
          padding: '12px 16px',
          borderBottom: '1px solid var(--gold-line)',
          background: 'rgba(214,168,95,0.08)',
          fontSize: 11.5, color: 'var(--cream)',
        }}>
          <span style={{ color: 'var(--status-warning)', fontFamily: 'var(--serif-en)', letterSpacing: 2, fontSize: 10, marginRight: 8 }}>HIGH-RISK</span>
          H2 段落主關鍵字位置已被移動。
        </div>
        <div style={{ background: 'rgba(17,25,37,0.4)', padding: '10px 0', fontSize: 11.5 }}>
          <div className="diff-line context"><span className="marker">·</span>查不到聯徵 ≠ 債務消失。</div>
          <div className="diff-line removed"><span className="marker">REM</span>銀行系統與聯徵並非同步。</div>
          <div className="diff-line added"><span className="marker">ADD</span>銀行內部債權系統與聯合徵信中心採取不同更新節奏。</div>
          <div className="diff-line changed"><span className="marker">CHG</span>債務仍存在於受讓方手上 → 債務仍實質存在於 AMC。</div>
        </div>
      </Panel>

      {/* Form fields + Divider */}
      <Panel en="Form · Divider · Ornament" zh="表單與裝飾語彙" corners>
        <div style={{ padding: '18px 22px' }}>
          <div className="field-label"><span className="req"></span><span className="en">Primary Keyword</span><span>主關鍵字</span></div>
          <input className="cinput" defaultValue="欠卡債聯徵無資料" />
          <div style={{ height: 12 }}></div>
          <div className="field-label"><span className="en">Reader Profile</span></div>
          <textarea className="ctextarea" rows="2" defaultValue="30–45 歲，曾有信用卡逾期紀錄。"></textarea>
          <Divider width={120} />
          <div style={{ display: 'flex', gap: 14, alignItems: 'center', justifyContent: 'center', padding: 14 }}>
            <span style={{ width: 6, height: 6, background: 'var(--gold)', transform: 'rotate(45deg)' }}></span>
            <span style={{ fontFamily: 'var(--serif-en)', letterSpacing: 4, fontSize: 11, color: 'var(--gold-dim)' }}>REQUIRED MARK</span>
            <span style={{ width: 6, height: 6, background: 'var(--gold)', transform: 'rotate(45deg)' }}></span>
          </div>
        </div>
      </Panel>
    </div>
  </div>
);

const HighRiskModal = () => (
  <div className="charta-app" style={{ position: 'relative', overflow: 'hidden' }}>
    {/* dimmed background showing review */}
    <Topbar />
    <div className="charta-layout">
      <LeftNav activeNum="06" />
      <div className="charta-main" style={{ filter: 'blur(2px) opacity(0.5)' }}>
        <ScreenHead en="Refine Section" zh="局部重跑與 Diff" />
        <Divider />
        <div style={{ height: 400, background: 'rgba(33,45,63,0.6)', border: '1px solid var(--gold-line)' }}></div>
      </div>
      <div className="charta-rightpanel" style={{ filter: 'blur(2px) opacity(0.5)' }}></div>
    </div>
    {/* overlay */}
    <div style={{
      position: 'absolute', inset: 0, background: 'rgba(8,12,18,0.68)',
      display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 10,
    }}>
      <div style={{
        width: 540,
        background: 'var(--navy-light)',
        border: '1px solid var(--gold-line-strong)',
        boxShadow: '0 1px 0 var(--status-blocker) inset, 0 30px 80px rgba(0,0,0,0.5)',
        position: 'relative',
      }}>
        <div style={{ position: 'absolute', top: 0, bottom: 0, left: 0, width: 3, background: 'var(--status-blocker)' }}></div>
        <Corner pos="tl" /><Corner pos="tr" /><Corner pos="bl" /><Corner pos="br" />
        <div style={{ padding: '22px 28px 14px' }}>
          <div style={{ fontFamily: 'var(--serif-en)', fontSize: 11, letterSpacing: 4, color: 'var(--status-blocker)', textTransform: 'uppercase' }}>● High-Risk Operation</div>
          <div style={{ fontSize: 19, color: 'var(--cream)', marginTop: 6 }}>變更主關鍵字 will affect downstream artifacts</div>
        </div>
        <div style={{ padding: '14px 28px', borderTop: '1px solid var(--gold-line)', borderBottom: '1px solid var(--gold-line)' }}>
          <div style={{ fontSize: 13, color: 'var(--cream-dim)', marginBottom: 12 }}>這項變更會影響：</div>
          {[
            ['brief.md', 'hard_stale'],
            ['h2-1 ~ h2-6', 'hard_stale'],
            ['review_report.json', 'soft_stale'],
            ['final_content.md', 'hard_stale'],
          ].map(([a, s], i) => (
            <div key={i} style={{ display: 'flex', justifyContent: 'space-between', padding: '6px 0', borderBottom: i < 3 ? '1px solid rgba(201,169,97,0.08)' : 'none' }}>
              <span className="mono" style={{ color: 'var(--cream)' }}>{a}</span>
              <Badge kind={s === 'hard_stale' ? 'hard' : 'soft'}>{s.toUpperCase()}</Badge>
            </div>
          ))}
        </div>
        <div style={{ padding: '16px 28px 22px', display: 'flex', gap: 10, justifyContent: 'flex-end' }}>
          <Button kind="ghost">取消</Button>
          <Button kind="ghost">只改 metadata</Button>
          <Button kind="danger">標記並繼續</Button>
        </div>
      </div>
    </div>
  </div>
);

window.DesignSystem = DesignSystem;
window.HighRiskModal = HighRiskModal;
