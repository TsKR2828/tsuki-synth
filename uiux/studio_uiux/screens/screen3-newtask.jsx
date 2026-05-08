// Screen 3: 建立任務
const Screen3 = () => {
  const outline = [
    { id: 'h2-1', t: '欠卡債查不到聯徵的常見原因', children: ['可能原因', '系統延遲'] },
    { id: 'h2-2', t: '欠卡債查不到聯徵代表債務消失了嗎？', children: ['還款責任', '債權轉讓'] },
    { id: 'h2-3', t: '債權轉讓後，討債流程怎麼進行？', children: [] },
    { id: 'h2-4', t: '若聯徵突然又出現紀錄…', children: [] },
    { id: 'h2-5', t: '收到法院支付命令該如何回應？', children: [] },
    { id: 'h2-6', t: '長期未處理可能面臨的後果', children: [] },
  ];
  return (
    <>
      <Topbar project="（新任務）" />
      <div className="charta-layout">
        <LeftNav activeNum="03" />
        <div className="charta-main">
          <ScreenHead en="New Article Task" zh="建立文章任務" right={
            <>
              <Button kind="ghost" size="sm">儲存草稿</Button>
              <Button kind="solid" size="sm">建立任務 · 進入 Brief</Button>
            </>
          } />
          <Divider />
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 18 }}>
            <Panel en="Task Form" zh="任務表單" padded>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 14 }}>
                <div style={{ gridColumn: '1 / -1' }}>
                  <div className="field-label"><span className="req"></span><span className="en">Project Title</span><span>專案標題</span></div>
                  <input className="cinput" defaultValue="欠卡債聯徵無資料怎麼辦" />
                </div>
                <div>
                  <div className="field-label"><span className="req"></span><span className="en">Site</span><span>客戶站點</span></div>
                  <select className="cselect" defaultValue="finance_client">
                    <option>LoginHeart 金融客戶</option>
                    <option>順周堂</option>
                  </select>
                </div>
                <div>
                  <div className="field-label"><span className="req"></span><span className="en">Guide Version</span></div>
                  <select className="cselect"><option>v9.7（current）</option><option>v9.6</option></select>
                </div>
                <div style={{ gridColumn: '1 / -1' }}>
                  <div className="field-label"><span className="req"></span><span className="en">Primary Keyword</span><span>主關鍵字</span></div>
                  <input className="cinput" defaultValue="欠卡債聯徵無資料" />
                </div>
                <div style={{ gridColumn: '1 / -1' }}>
                  <div className="field-label"><span className="en">Secondary Keywords</span><span>次要關鍵字（逗號分隔）</span></div>
                  <input className="cinput" defaultValue="債權轉讓, 資產管理公司, 呆帳, 消債條例" />
                </div>
                <div>
                  <div className="field-label"><span className="en">Article Type</span></div>
                  <select className="cselect"><option>解答型 / How-to</option><option>比較型</option><option>清單型</option></select>
                </div>
                <div>
                  <div className="field-label"><span className="en">Export Profile</span></div>
                  <select className="cselect"><option>wordpress_finance_html</option></select>
                </div>
                <div style={{ gridColumn: '1 / -1' }}>
                  <div className="field-label"><span className="en">Reader Profile</span><span>讀者輪廓</span></div>
                  <textarea className="ctextarea" defaultValue="30–45 歲，曾有信用卡逾期紀錄，正自行查詢聯徵資料以評估後續處理。對法律與金融術語接受度中等。"></textarea>
                </div>
              </div>
            </Panel>

            <Panel en="Outline Editor" zh="目錄編排器" headRight={<Button kind="ghost" size="sm">＋ 新增 H2</Button>}>
              <div style={{ padding: '4px 0' }}>
                {outline.map((h, i) => (
                  <div key={h.id} style={{ borderBottom: '1px solid rgba(201,169,97,0.1)' }}>
                    <div style={{ padding: '11px 18px', display: 'flex', gap: 10, alignItems: 'center' }}>
                      <span style={{ color: 'var(--gold)' }}>◇</span>
                      <span className="mono" style={{ color: 'var(--gold-dim)', width: 36 }}>{h.id}</span>
                      <span style={{ flex: 1, color: 'var(--cream)', fontSize: 13.5 }}>{h.t}</span>
                      <span style={{ fontFamily: 'var(--serif-en)', fontSize: 10, color: 'var(--cream-faint)', letterSpacing: 1.5, cursor: 'grab' }}>≡</span>
                    </div>
                    {h.children.map((c, j) => (
                      <div key={j} style={{ padding: '6px 18px 6px 64px', display: 'flex', gap: 10, alignItems: 'center', fontSize: 12, color: 'var(--cream-muted)' }}>
                        <span className="mono" style={{ color: 'var(--gold-dim)', width: 36 }}>h3-{j + 1}</span>
                        <span>{c}</span>
                      </div>
                    ))}
                  </div>
                ))}
                <div style={{ padding: '14px 18px', background: 'rgba(185,154,214,0.05)', borderTop: '1px solid var(--gold-line)' }}>
                  <div style={{ fontFamily: 'var(--serif-en)', fontSize: 10, letterSpacing: 2.5, color: 'var(--status-stale)', textTransform: 'uppercase', marginBottom: 8 }}>Special Sections</div>
                  <div style={{ display: 'flex', gap: 10, alignItems: 'center', padding: '4px 0' }}>
                    <span className="mono" style={{ color: 'var(--status-stale)', width: 60 }}>KT</span>
                    <span style={{ flex: 1, color: 'var(--cream)' }}>Key Takeaways · 4 條重點</span>
                  </div>
                  <div style={{ display: 'flex', gap: 10, alignItems: 'center', padding: '4px 0' }}>
                    <span className="mono" style={{ color: 'var(--status-stale)', width: 60 }}>FAQ</span>
                    <span style={{ flex: 1, color: 'var(--cream)' }}>FAQ · 4–6 題</span>
                  </div>
                </div>
              </div>
            </Panel>
          </div>
        </div>
        <div className="charta-rightpanel">
          <RP title="Validation"><RPRow k="必填欄位" v={<Badge kind="done">完整</Badge>} /><RPRow k="section_id 重複" v={<Badge kind="done">無</Badge>} /><RPRow k="預估字數" v="3,200–4,000" /></RP>
          <RP title="Estimated Cost"><RPRow k="brief" v="$0.40" /><RPRow k="6 H2 × v1" v="$2.20" /><RPRow k="KT + FAQ" v="$0.60" /><RPRow k="review" v="$0.50" /><RPRow k="total est." v="$3.70" /></RP>
        </div>
      </div>
    </>
  );
};
window.Screen3 = Screen3;
