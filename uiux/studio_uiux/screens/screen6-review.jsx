// Screen 6: Review / Blocker
const Screen6 = () => {
  const issues = [
    { sev: 'blocker', section: 'h2-2', loc: 'p.2', cat: 'source_missing', msg: '此段提到債權轉讓流程，但沒有來源。', actions: ['view_source', 'refine'] },
    { sev: 'blocker', section: 'h2-2', loc: 'p.4', cat: 'compliance_risk', msg: '出現「保證下來」字樣，金融客戶禁用詞庫違規。', actions: ['ai_patch', 'refine'] },
    { sev: 'blocker', section: 'h2-3', loc: 'h2_title', cat: 'keyword_missing', msg: '主關鍵字「欠卡債聯徵」未在標題出現。', actions: ['refine'] },
    { sev: 'warning', section: 'h2-2', loc: 'p.3', cat: 'tone_mismatch', msg: '語氣偏口語，與金融文風指南不一致。', actions: ['ai_patch'] },
    { sev: 'warning', section: 'h2-1', loc: 'list', cat: 'redundant_info', msg: '與 h2-2 第二段內容有 78% 重疊。', actions: ['refine'] },
    { sev: 'suggestion', section: 'h2-2', loc: 'p.5', cat: 'reader_question_unanswered', msg: '可考慮加入：「我該怎麼確認債權目前在誰手上？」', actions: ['add_to_faq'] },
    { sev: 'info', section: 'h2-1', loc: 'p.1', cat: 'style_note', msg: '段落長度偏短，可考慮合併。', actions: [] },
  ];
  const sevBadge = (s) => {
    if (s === 'blocker') return <Badge kind="blocked">BLOCKER</Badge>;
    if (s === 'warning') return <Badge kind="warning">WARNING</Badge>;
    if (s === 'suggestion') return <Badge kind="gold">SUGGESTION</Badge>;
    return <Badge kind="queued">INFO</Badge>;
  };
  return (
    <>
      <Topbar />
      <div className="charta-layout">
        <LeftNav activeNum="06" />
        <div className="charta-main">
          <ScreenHead en="Review Report" zh="審稿與 Blocker 檢查" right={
            <>
              <Button kind="ghost" size="sm">Export Issues CSV</Button>
              <Button kind="solid" size="sm">Re-run Review</Button>
            </>
          } />
          <Divider />

          {/* Header card */}
          <Panel padded corners style={{ marginBottom: 18 }}>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(5, 1fr)', gap: 24 }}>
              <div>
                <div className="field-label"><span className="en">Status</span></div>
                <Badge kind="blocked">BLOCKED</Badge>
              </div>
              <div>
                <div className="field-label"><span className="en">Stale Level</span></div>
                <Badge kind="soft">SOFT STALE</Badge>
              </div>
              <div>
                <div className="field-label"><span className="en">Scope</span></div>
                <div style={{ fontSize: 13, color: 'var(--cream)' }}>全文 6 H2 + KT + FAQ</div>
              </div>
              <div>
                <div className="field-label"><span className="en">Created</span></div>
                <div style={{ fontFamily: 'var(--serif-en)', fontSize: 13, color: 'var(--cream)', letterSpacing: 1 }}>2026 · 05 · 07  14:22</div>
              </div>
              <div>
                <div className="field-label"><span className="en">Issues</span></div>
                <div style={{ display: 'flex', gap: 6 }}>
                  <Badge kind="blocked">3 BLK</Badge>
                  <Badge kind="warning">2 WRN</Badge>
                  <Badge kind="gold">1 SUG</Badge>
                </div>
              </div>
            </div>
            <div style={{
              marginTop: 16, padding: '12px 14px',
              borderLeft: '2px solid var(--status-blocker)',
              background: 'rgba(217,120,102,0.06)', fontSize: 13, color: 'var(--cream)'
            }}>
              Review blocked：3 個 blocker 需要處理。此 review report 基於 h2-2 v3，不能用於導出 gate。
            </div>
          </Panel>

          <div style={{ display: 'grid', gridTemplateColumns: '1.5fr 1fr', gap: 18 }}>
            <Panel en="Issue Ledger" zh="議題索引">
              <div style={{ overflow: 'auto', maxHeight: 520 }}>
                <table className="ctable">
                  <thead>
                    <tr>
                      <th style={{ width: 100 }}>Severity</th>
                      <th style={{ width: 60 }}>Sec</th>
                      <th style={{ width: 60 }}>Loc</th>
                      <th>Category · Message</th>
                      <th style={{ width: 130 }}>Action</th>
                    </tr>
                  </thead>
                  <tbody>
                    {issues.map((i, idx) => (
                      <tr key={idx} className={`${i.sev}-row`}>
                        <td>{sevBadge(i.sev)}</td>
                        <td className="mono">{i.section}</td>
                        <td className="mono">{i.loc}</td>
                        <td>
                          <div style={{ fontFamily: 'var(--serif-en)', fontSize: 10, color: 'var(--gold-dim)', letterSpacing: 2, textTransform: 'uppercase', marginBottom: 3 }}>
                            {i.cat.replace(/_/g, ' · ')}
                          </div>
                          <div style={{ color: 'var(--cream)' }}>{i.msg}</div>
                        </td>
                        <td>
                          <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
                            {i.actions.includes('ai_patch') && <Button kind="solid" size="sm">AI Patch</Button>}
                            {i.actions.includes('refine') && <Button kind="ghost" size="sm">Refine</Button>}
                            {i.actions.includes('view_source') && <Button kind="ghost" size="sm">View Source</Button>}
                            {i.actions.includes('add_to_faq') && <Button kind="ghost" size="sm">→ FAQ</Button>}
                            {i.actions.length === 0 && <span style={{ fontSize: 11, color: 'var(--cream-faint)', fontStyle: 'italic' }}>info only</span>}
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </Panel>

            <Panel en="Content Highlight" zh="原文高亮 — h2-2">
              <div style={{ padding: '20px 24px', maxHeight: 520, overflow: 'auto', fontSize: 14, lineHeight: 2, background: 'rgba(17,25,37,0.4)' }}>
                <h3 style={{ fontSize: 16, color: 'var(--cream)', borderBottom: '1px solid var(--gold-line)', paddingBottom: 8, marginBottom: 14 }}>
                  欠卡債查不到聯徵代表債務消失了嗎？
                </h3>
                <p style={{ color: 'var(--cream-dim)', marginBottom: 14 }}>
                  許多讀者在自己的聯徵紀錄裡，找不到原本欠下的卡債…
                </p>
                <p style={{ borderLeft: '2px solid var(--status-blocker)', paddingLeft: 12, color: 'var(--cream)', marginBottom: 14 }}>
                  根據實務觀察，<span style={{ background: 'rgba(217,120,102,0.18)', padding: '0 2px' }}>債權可能已被轉讓給資產管理公司</span>，此時即便聯徵不顯示…
                  <div style={{ fontSize: 11, color: 'var(--status-blocker)', fontFamily: 'var(--serif-en)', letterSpacing: 1.5, marginTop: 4 }}>↳ ISSUE 023 · SOURCE_MISSING</div>
                </p>
                <p style={{ borderLeft: '2px solid var(--status-warning)', paddingLeft: 12, color: 'var(--cream-dim)', marginBottom: 14 }}>
                  別擔心，其實只要慢慢處理…
                  <div style={{ fontSize: 11, color: 'var(--status-warning)', fontFamily: 'var(--serif-en)', letterSpacing: 1.5, marginTop: 4 }}>↳ TONE_MISMATCH</div>
                </p>
                <p style={{ borderLeft: '2px solid var(--status-blocker)', paddingLeft: 12, color: 'var(--cream)' }}>
                  我們<span style={{ background: 'rgba(217,120,102,0.18)', padding: '0 2px' }}>保證下來</span>會在六個月內結清…
                  <div style={{ fontSize: 11, color: 'var(--status-blocker)', fontFamily: 'var(--serif-en)', letterSpacing: 1.5, marginTop: 4 }}>↳ COMPLIANCE_RISK · 禁用詞</div>
                </p>
              </div>
            </Panel>
          </div>
        </div>

        <div className="charta-rightpanel">
          <RP title="Review Report">
            <RPRow k="ID" v="rev_2026_05_07" mono />
            <RPRow k="Status" v={<Badge kind="blocked">BLOCKED</Badge>} />
            <RPRow k="Stale" v={<Badge kind="soft">SOFT</Badge>} />
            <RPRow k="Scope" v="full document" />
          </RP>
          <RP title="Based On">
            <RPRow k="brief.md" v="v2 · 1a8c…" mono />
            <RPRow k="h2-1" v="v2 · 4d10…" mono />
            <RPRow k="h2-2" v="v3 · 9f31…" mono />
            <RPRow k="h2-3" v="v1 · b7e2…" mono />
          </RP>
          <RP title="Export Gate">
            <div style={{ padding: 10, border: '1px solid rgba(217,120,102,0.4)', background: 'rgba(217,120,102,0.06)' }}>
              <div style={{ color: 'var(--status-blocker)', fontSize: 12, marginBottom: 6 }}>● Gate blocked</div>
              <div style={{ fontSize: 11, color: 'var(--cream-muted)', lineHeight: 1.7 }}>
                3 個 blocker 未處理 · review soft_stale · 不符合 review_status = clean 要求
              </div>
            </div>
          </RP>
          <RP title="Categories">
            <RPRow k="source_missing" v="1" />
            <RPRow k="compliance_risk" v="1" />
            <RPRow k="keyword_missing" v="1" />
            <RPRow k="tone_mismatch" v="1" />
            <RPRow k="redundant_info" v="1" />
          </RP>
        </div>
      </div>
    </>
  );
};
window.Screen6 = Screen6;
