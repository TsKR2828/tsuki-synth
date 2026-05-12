// Screen 7: Refine / Diff
const Screen7 = () => {
  const guideSections = [
    { name: 'A · 主關鍵字密度', req: true, opt: false, forb: false, tags: 'core' },
    { name: 'B · 競品分析', req: false, opt: true, forb: false, tags: 'optional' },
    { name: 'C · 來源規範', req: true, opt: false, forb: false, tags: 'compliance' },
    { name: 'D · CTA 文案', req: false, opt: true, forb: false, tags: 'optional' },
    { name: 'E · 行銷誇飾用語', req: false, opt: false, forb: true, tags: 'forbidden' },
    { name: 'F · 業配案例引用', req: false, opt: false, forb: true, tags: 'forbidden' },
    { name: 'G · 金融合規禁用詞', req: true, opt: false, forb: false, tags: 'compliance' },
  ];
  return (
    <>
      <Topbar />
      <div className="charta-layout">
        <LeftNav activeNum="07" />
        <div className="charta-main">
          <ScreenHead en="Refine Section" zh="局部重跑與 Diff" right={
            <>
              <Button kind="ghost" size="sm">Reject</Button>
              <Button kind="ghost" size="sm">Re-run</Button>
              <Button kind="solid" size="sm">Accept v4</Button>
            </>
          } />
          <Divider />

          <div style={{ display: 'grid', gridTemplateColumns: '220px 1fr 260px', gap: 16 }}>
            {/* Section Picker */}
            <Panel en="Pick Section" zh="選擇章節">
              <div style={{ padding: '4px 0' }}>
                {[
                  { id: 'h2-1', t: '欠卡債查不到聯徵的常見原因', v: 'v2', issues: 1 },
                  { id: 'h2-2', t: '欠卡債查不到聯徵代表債務消失了嗎？', v: 'v3', issues: 3, stale: true, current: true },
                  { id: 'h2-3', t: '債權轉讓後，討債流程怎麼進行？', v: 'v1', issues: 1 },
                  { id: 'h2-4', t: '若聯徵突然又出現紀錄…', v: '—', issues: 0 },
                  { id: 'KT', t: 'Key Takeaways', v: 'v1', issues: 0, special: true },
                  { id: 'FAQ', t: 'FAQ', v: 'v2', issues: 0, special: true },
                ].map(s => (
                  <div key={s.id} style={{
                    padding: '10px 14px',
                    borderLeft: s.current ? '2px solid var(--gold)' : '2px solid transparent',
                    background: s.current ? 'var(--surface-selected)' : 'transparent',
                    borderBottom: '1px solid rgba(201,169,97,0.08)',
                  }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline' }}>
                      <span style={{ fontFamily: 'var(--mono)', fontSize: 11, color: s.special ? 'var(--status-stale)' : 'var(--gold)' }}>{s.id}</span>
                      <span style={{ fontFamily: 'var(--serif-en)', fontSize: 10, color: 'var(--cream-faint)', letterSpacing: 1 }}>{s.v}</span>
                    </div>
                    <div style={{ fontSize: 12, color: 'var(--cream-dim)', marginTop: 4, lineHeight: 1.5 }}>{s.t}</div>
                    <div style={{ display: 'flex', gap: 4, marginTop: 6 }}>
                      {s.stale && <Badge kind="soft">STALE</Badge>}
                      {s.issues > 0 && <Badge kind="blocked">{s.issues}</Badge>}
                    </div>
                  </div>
                ))}
              </div>
            </Panel>

            {/* Diff View */}
            <Panel en="Diff View" zh="h2-2 · v3 → v4" corners headRight={
              <>
                <Badge kind="warning">1 HIGH-RISK</Badge>
                <Badge kind="gold">SECTIONS A·C·G</Badge>
              </>
            }>
              <div style={{
                padding: '12px 16px',
                borderBottom: '1px solid var(--gold-line)',
                background: 'rgba(214,168,95,0.08)',
                fontSize: 12.5, color: 'var(--cream)',
                display: 'flex', gap: 10, alignItems: 'flex-start',
              }}>
                <div style={{ width: 4, alignSelf: 'stretch', background: 'var(--status-warning)' }}></div>
                <div>
                  <div style={{ color: 'var(--status-warning)', fontFamily: 'var(--serif-en)', letterSpacing: 2, fontSize: 10, marginBottom: 4, textTransform: 'uppercase' }}>High-Risk Diff</div>
                  此 diff 包含高風險變更：H2 段落內主關鍵字「欠卡債聯徵」位置已被移動。
                  接受後會建立 <span className="mono" style={{ color: 'var(--gold)' }}>h2-2 v4</span>，不覆蓋目前 accepted.md。
                </div>
              </div>
              <div style={{ background: 'rgba(17,25,37,0.4)', padding: '10px 0', fontSize: 12 }}>
                <div className="diff-line context"><span className="marker">·</span>許多讀者在自己的聯徵紀錄裡，找不到原本欠下的卡債…</div>
                <div className="diff-line removed"><span className="marker">REM</span>事實上，查不到聯徵不等於債務消失，銀行的內部系統與聯徵並非同步。</div>
                <div className="diff-line added"><span className="marker">ADD</span>事實上，「欠卡債聯徵」查不到並不代表債務已消失——銀行內部債權系統與聯合徵信中心的資料庫，本就採取不同的更新節奏。</div>
                <div className="diff-line context"><span className="marker">·</span></div>
                <div className="diff-line removed"><span className="marker">REM</span>根據實務觀察，債權可能已被轉讓給資產管理公司[待補來源]。</div>
                <div className="diff-line added"><span className="marker">ADD</span>根據金管會 2024 年呆帳處理白皮書¹，呆帳債權於核銷後常被打包出售予資產管理公司（AMC），由受讓方繼續追償。</div>
                <div className="diff-line changed"><span className="marker">CHG</span>此時即便聯徵不顯示，債務仍存在於受讓方手上 → 此時聯徵紀錄即便為空，債務仍實質存在於 AMC 手上。</div>
                <div className="diff-line context"><span className="marker">·</span>### 三種「聯徵查無」但債務仍存在的情境</div>
                <div className="diff-line context"><span className="marker">·</span>1. 原銀行已將債權打包出售給資產管理公司（AMC）。</div>
                <div className="diff-line removed"><span className="marker">REM</span>2. 我們保證下來不會再被催討。</div>
                <div className="diff-line added"><span className="marker">ADD</span>2. 呆帳已逾五年揭露期，但債權人依《消費者債務清理條例》仍保有追償權。</div>
              </div>
            </Panel>

            {/* Settings */}
            <Panel en="Refine Settings" zh="重跑設定">
              <div style={{ padding: '14px 16px' }}>
                <div className="field-label"><span className="en">Action Section Map</span></div>
                <div style={{ background: 'rgba(17,25,37,0.5)', border: '1px solid var(--gold-line)', maxHeight: 280, overflow: 'auto' }}>
                  <table className="ctable" style={{ fontSize: 11 }}>
                    <thead>
                      <tr>
                        <th>Section</th>
                        <th style={{ width: 28, textAlign: 'center' }}>R</th>
                        <th style={{ width: 28, textAlign: 'center' }}>O</th>
                        <th style={{ width: 28, textAlign: 'center' }}>F</th>
                      </tr>
                    </thead>
                    <tbody>
                      {guideSections.map((g, i) => (
                        <tr key={i} className={g.forb ? 'blocker-row' : ''}>
                          <td style={{ color: 'var(--cream)', fontSize: 11.5 }}>{g.name}</td>
                          <td style={{ textAlign: 'center', color: g.req ? 'var(--gold)' : 'var(--cream-faint)' }}>{g.req ? '◆' : '·'}</td>
                          <td style={{ textAlign: 'center', color: g.opt ? 'var(--cream)' : 'var(--cream-faint)' }}>{g.opt ? '☐' : '·'}</td>
                          <td style={{ textAlign: 'center', color: g.forb ? 'var(--status-blocker)' : 'var(--cream-faint)' }}>{g.forb ? '✕' : '·'}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
                <div style={{ marginTop: 14 }}>
                  <div className="field-label"><span className="en">Issues to Address</span></div>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                    <label style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 12, color: 'var(--cream-dim)' }}>
                      <span style={{ width: 12, height: 12, border: '1px solid var(--gold)', display: 'inline-block', position: 'relative' }}>
                        <span style={{ position: 'absolute', inset: 2, background: 'var(--gold)' }}></span>
                      </span>
                      Issue 023 · source_missing
                    </label>
                    <label style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 12, color: 'var(--cream-dim)' }}>
                      <span style={{ width: 12, height: 12, border: '1px solid var(--gold)', display: 'inline-block', position: 'relative' }}>
                        <span style={{ position: 'absolute', inset: 2, background: 'var(--gold)' }}></span>
                      </span>
                      Issue 024 · compliance_risk
                    </label>
                    <label style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 12, color: 'var(--cream-muted)' }}>
                      <span style={{ width: 12, height: 12, border: '1px solid var(--gold-line)', display: 'inline-block' }}></span>
                      Issue 028 · tone_mismatch
                    </label>
                  </div>
                </div>
                <div style={{ marginTop: 14 }}>
                  <div className="field-label"><span className="en">Custom Instruction</span></div>
                  <textarea className="ctextarea" rows="3" placeholder="補充重跑指示…">補上來源引用，移除「保證下來」一類禁用詞。</textarea>
                </div>
              </div>
            </Panel>
          </div>
        </div>
      </div>
    </>
  );
};
window.Screen7 = Screen7;
