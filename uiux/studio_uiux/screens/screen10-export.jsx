// Screen 10: Export Gate
const Screen10 = () => {
  const gates = [
    { name: 'Review Gate', en: 'review_status = clean · stale_level = null', pass: false, msg: 'review_status = blocked · soft_stale' },
    { name: 'Source Gate', en: '無未處理 [待確認]', pass: false, msg: '2 處 [待補來源] 尚未解決' },
    { name: 'Link Gate', en: '無競品連結', pass: true, msg: '12 個外連、6 個內連已驗證' },
    { name: 'Artifact Gate', en: 'complete_draft.md / final_content.md 必須存在', pass: false, msg: 'final_content.md 缺失' },
    { name: 'Profile Gate', en: 'export_profile = wordpress_finance_html', pass: true, msg: 'profile 已載入' },
    { name: 'KT / FAQ Gate', en: 'KT final · FAQ accepted', pass: false, msg: 'FAQ 尚未 accepted（4 題待確認）' },
  ];
  return (
    <>
      <Topbar />
      <div className="charta-layout">
        <LeftNav activeNum="10" />
        <div className="charta-main">
          <ScreenHead en="Export Gate" zh="導出檢查" right={
            <>
              <Button kind="ghost" size="sm">View Manifest</Button>
              <Button kind="solid" size="sm" disabled style={{ opacity: 0.5, cursor: 'not-allowed' }}>Export Blocked</Button>
            </>
          } />
          <Divider />

          <div style={{
            padding: '14px 18px', marginBottom: 16,
            borderLeft: '2px solid var(--status-blocker)',
            background: 'rgba(217,120,102,0.08)',
            border: '1px solid rgba(217,120,102,0.3)',
            color: 'var(--cream)', fontSize: 13,
          }}>
            <div style={{ color: 'var(--status-blocker)', fontFamily: 'var(--serif-en)', letterSpacing: 2.5, fontSize: 11, marginBottom: 6, textTransform: 'uppercase' }}>● Export Blocked</div>
            目前 4 個 gate 未通過。在所有 gate 通過前，無法產出 final_content.md 或 exports/wordpress_finance_html/final.html。
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 18 }}>
            <Panel en="Gate Checklist" zh="導出檢查清單" corners>
              <div style={{ padding: '4px 0' }}>
                {gates.map((g, i) => (
                  <div key={i} style={{
                    padding: '14px 18px',
                    borderBottom: '1px solid rgba(201,169,97,0.1)',
                    borderLeft: g.pass ? 'none' : '2px solid var(--status-blocker)',
                    display: 'flex', gap: 14, alignItems: 'flex-start',
                  }}>
                    <div style={{
                      width: 22, height: 22, marginTop: 2,
                      border: `1px solid ${g.pass ? 'var(--status-success)' : 'var(--status-blocker)'}`,
                      display: 'flex', alignItems: 'center', justifyContent: 'center',
                      color: g.pass ? 'var(--status-success)' : 'var(--status-blocker)',
                      fontSize: 12,
                    }}>{g.pass ? '✓' : '✕'}</div>
                    <div style={{ flex: 1 }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline' }}>
                        <span style={{ fontSize: 14, color: 'var(--cream)' }}>{g.name}</span>
                        {g.pass ? <Badge kind="done">PASSED</Badge> : <Badge kind="blocked">BLOCKED</Badge>}
                      </div>
                      <div style={{ fontFamily: 'var(--serif-en)', fontSize: 10.5, color: 'var(--gold-dim)', letterSpacing: 1.8, marginTop: 4, textTransform: 'uppercase' }}>{g.en}</div>
                      <div style={{ fontSize: 12, color: g.pass ? 'var(--cream-muted)' : 'var(--status-blocker)', marginTop: 6 }}>↳ {g.msg}</div>
                    </div>
                  </div>
                ))}
              </div>
            </Panel>

            <div style={{ display: 'flex', flexDirection: 'column', gap: 18 }}>
              <Panel en="Export Profile" zh="輸出設定">
                <div style={{ padding: '14px 18px' }}>
                  <div className="rp-row"><span className="k">profile_id</span><span className="v mono">wordpress_finance_html</span></div>
                  <div className="rp-row"><span className="k">output_format</span><span className="v">HTML · MD</span></div>
                  <div className="rp-row"><span className="k">heading policy</span><span className="v">H2/H3 only</span></div>
                  <div className="rp-row"><span className="k">link style</span><span className="v">target=_blank, rel=nofollow</span></div>
                  <div className="rp-row"><span className="k">CTA block</span><span className="v">finance_disclaimer_v2</span></div>
                  <div className="rp-row"><span className="k">image placeholder</span><span className="v">[image:slot-N]</span></div>
                  <div className="rp-row"><span className="k">WordPress mode</span><span className="v">Gutenberg blocks</span></div>
                  <div className="rp-row"><span className="k">Google Docs</span><span className="v">draft placeholder</span></div>
                </div>
              </Panel>

              <Panel en="Output Preview" zh="預覽 — final.html (gated)">
                <div style={{ padding: '16px 20px', background: 'rgba(17,25,37,0.5)', maxHeight: 240, overflow: 'auto', filter: 'blur(0.4px) opacity(0.55)' }}>
                  <div className="mono" style={{ fontSize: 11, color: 'var(--gold-dim)' }}>&lt;article class="post-finance"&gt;</div>
                  <div className="mono" style={{ fontSize: 11, color: 'var(--cream-muted)', paddingLeft: 14 }}>&lt;h1&gt;欠卡債聯徵無資料怎麼辦&lt;/h1&gt;</div>
                  <div className="mono" style={{ fontSize: 11, color: 'var(--cream-muted)', paddingLeft: 14 }}>&lt;div class="kt"&gt;…&lt;/div&gt;</div>
                  <div className="mono" style={{ fontSize: 11, color: 'var(--cream-muted)', paddingLeft: 14 }}>&lt;h2 id="h2-1"&gt;…&lt;/h2&gt;</div>
                  <div className="mono" style={{ fontSize: 11, color: 'var(--cream-muted)', paddingLeft: 14 }}>&lt;h2 id="h2-2"&gt;…&lt;/h2&gt;</div>
                  <div className="mono" style={{ fontSize: 11, color: 'var(--cream-muted)', paddingLeft: 14 }}>&lt;div class="faq"&gt;…&lt;/div&gt;</div>
                  <div className="mono" style={{ fontSize: 11, color: 'var(--gold-dim)' }}>&lt;/article&gt;</div>
                </div>
                <div style={{ padding: '12px 16px', borderTop: '1px solid var(--gold-line)', display: 'flex', gap: 8, flexWrap: 'wrap' }}>
                  <Button kind="ghost" size="sm" disabled style={{ opacity: 0.4 }}>Copy HTML</Button>
                  <Button kind="ghost" size="sm" disabled style={{ opacity: 0.4 }}>Copy Markdown</Button>
                  <Button kind="ghost" size="sm" disabled style={{ opacity: 0.4 }}>Download .html</Button>
                  <Button kind="ghost" size="sm" disabled style={{ opacity: 0.4 }}>Download .md</Button>
                </div>
              </Panel>
            </div>
          </div>
        </div>

        <div className="charta-rightpanel">
          <RP title="Artifacts">
            <RPRow k="merged_body.md" v={<Badge kind="done">EXISTS</Badge>} />
            <RPRow k="complete_draft.md" v={<Badge kind="soft">SOFT</Badge>} />
            <RPRow k="final_content.md" v={<Badge kind="blocked">MISSING</Badge>} />
            <RPRow k="exports/…/final.html" v={<Badge kind="blocked">MISSING</Badge>} />
          </RP>
          <RP title="Last Export">
            <RPRow k="Profile" v="wordpress_finance" />
            <RPRow k="Date" v="—" />
            <RPRow k="By" v="—" />
            <RPRow k="Hash" v="—" mono />
          </RP>
          <RP title="Site Profile">
            <RPRow k="site_id" v="finance_client" mono />
            <RPRow k="WP endpoint" v="—" />
            <RPRow k="GDocs folder" v="—" />
          </RP>
        </div>
      </div>
    </>
  );
};
window.Screen10 = Screen10;
