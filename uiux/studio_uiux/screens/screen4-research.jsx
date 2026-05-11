// Screen 4: Keyword / SERP / Brief / Sources
const Screen4 = () => {
  const [tab, setTab] = React.useState('keyword');
  const tabs = [
    ['keyword', 'Keyword Map', '關鍵字'],
    ['serp', 'SERP Analysis', 'SERP'],
    ['brief', 'Brief', '大綱'],
    ['sources', 'Sources', '來源'],
    ['missing', 'Missing Info', '缺口'],
  ];
  const keywords = [
    { sel: true, kw: '欠卡債聯徵無資料', intent: 'informational', reason: '使用者想理解現況', serp: true, paa: 4, prio: 'P1' },
    { sel: true, kw: '聯徵中心 卡債查詢', intent: 'informational', reason: '查詢路徑說明', serp: true, paa: 3, prio: 'P1' },
    { sel: true, kw: '債權轉讓 資產管理公司', intent: 'navigational', reason: '了解流程主體', serp: true, paa: 2, prio: 'P2' },
    { sel: false, kw: '卡債協商', intent: 'transactional', reason: '與本文意圖不符', serp: false, paa: 8, prio: '—' },
    { sel: true, kw: '呆帳 五年揭露期', intent: 'informational', reason: '解釋為何查不到', serp: true, paa: 1, prio: 'P2' },
    { sel: false, kw: '個人破產', intent: 'informational', reason: '範疇過大', serp: false, paa: 5, prio: '—' },
  ];
  const sources = [
    { use: true, t: '金管會 2024 呆帳處理白皮書', url: 'fsc.gov.tw/…/2024-…', type: 'official', trust: 9, used: 'h2-2 / h2-3', comp: false },
    { use: true, t: '聯合徵信中心 — 個人信用揭露條例', url: 'jcic.org.tw/…', type: 'official', trust: 9, used: 'h2-1 / h2-2', comp: false },
    { use: true, t: '消費者債務清理條例', url: 'law.moj.gov.tw/…', type: 'law', trust: 10, used: 'h2-5 / h2-6', comp: false },
    { use: false, t: '某律師事務所 — 卡債解套指南', url: 'competitor.tw/…', type: 'blog', trust: 4, used: '—', comp: true },
    { use: false, t: 'Yahoo 知識家 — 卡債 PTT', url: 'tw.answers…', type: 'forum', trust: 2, used: '—', comp: false },
  ];
  return (
    <>
      <Topbar />
      <div className="charta-layout no-right">
        <LeftNav activeNum="04" />
        <div className="charta-main">
          <ScreenHead en="Research Workbench" zh="關鍵字 / SERP / Brief / 來源" right={
            <Button kind="solid" size="sm">產生 Brief</Button>
          } />
          <Divider />
          <div style={{ display: 'flex', gap: 0, marginBottom: 16, borderBottom: '1px solid var(--gold-line)' }}>
            {tabs.map(([id, en, zh]) => (
              <div key={id} onClick={() => setTab(id)} style={{
                padding: '12px 22px', cursor: 'pointer',
                borderBottom: tab === id ? '2px solid var(--gold)' : '2px solid transparent',
                marginBottom: -1,
              }}>
                <div style={{ fontFamily: 'var(--serif-en)', fontSize: 10, letterSpacing: 2.5, color: tab === id ? 'var(--gold)' : 'var(--gold-dim)', textTransform: 'uppercase' }}>{en}</div>
                <div style={{ fontSize: 13, color: tab === id ? 'var(--cream)' : 'var(--cream-muted)', marginTop: 2 }}>{zh}</div>
              </div>
            ))}
          </div>

          {tab === 'keyword' && (
            <Panel en="Keyword Map" zh="關鍵字索引">
              <table className="ctable">
                <thead><tr><th style={{ width: 60 }}>Use</th><th>Keyword</th><th style={{ width: 110 }}>Intent</th><th>Reason</th><th style={{ width: 80 }}>SERP ✓</th><th style={{ width: 50 }}>PAA</th><th style={{ width: 60 }}>Priority</th></tr></thead>
                <tbody>
                  {keywords.map((k, i) => (
                    <tr key={i} className={k.sel ? 'selected' : ''}>
                      <td><span style={{ width: 14, height: 14, border: '1px solid var(--gold)', display: 'inline-block', position: 'relative' }}>{k.sel && <span style={{ position: 'absolute', inset: 2, background: 'var(--gold)' }}></span>}</span></td>
                      <td style={{ color: 'var(--cream)' }}>{k.kw}</td>
                      <td><Badge kind={k.intent === 'transactional' ? 'warning' : 'gold'}>{k.intent}</Badge></td>
                      <td>{k.reason}</td>
                      <td style={{ color: k.serp ? 'var(--status-success)' : 'var(--cream-faint)' }}>{k.serp ? '✓ Validated' : '—'}</td>
                      <td>{k.paa}</td>
                      <td>{k.prio !== '—' ? <Badge kind="gold">{k.prio}</Badge> : <span style={{ color: 'var(--cream-faint)' }}>—</span>}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </Panel>
          )}

          {tab === 'serp' && (
            <Panel en="SERP Analysis" zh="競品頁面索引">
              <table className="ctable">
                <thead><tr><th style={{ width: 30 }}>#</th><th>頁面標題</th><th style={{ width: 100 }}>Type</th><th style={{ width: 60 }}>H2 #</th><th>差異化機會</th></tr></thead>
                <tbody>
                  {[
                    [1, '欠卡債怎麼辦？律師完整解析', 'service', 8, '缺：債權轉讓細節、AMC 角色'],
                    [2, '卡債逾期 5 年完整指南', 'guide', 6, '缺：法院支付命令處理'],
                    [3, '聯徵中心查詢教學 2024', 'tutorial', 5, '缺：為何查不到的解釋'],
                    [4, '消債條例與更生程序', 'law', 7, '不重疊，可作為延伸'],
                    [5, '債務協商 PTT 心得', 'forum', 4, '低品質參考'],
                  ].map(([n, t, ty, h2, opp], i) => (
                    <tr key={i}>
                      <td className="mono">{n}</td>
                      <td style={{ color: 'var(--cream)' }}>{t}</td>
                      <td><Badge kind="gold">{ty}</Badge></td>
                      <td className="mono">{h2}</td>
                      <td>{opp}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </Panel>
          )}

          {tab === 'brief' && (
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
              <Panel en="Editor" zh="Brief 編輯">
                <textarea className="ctextarea" rows="22" defaultValue={`# 欠卡債聯徵無資料怎麼辦\n\n## 文章目標\n讀者搜尋此關鍵字時，往往在自查聯徵後感到困惑。\n本文需在 H2-2 段內明確回答「查不到 ≠ 消失」。\n\n## H2 規劃\n1. 常見原因\n2. 是否真的消失？  [待確認：AMC 流程細節]\n3. 債權轉讓\n4. 紀錄重新出現\n5. 法院支付命令\n6. 長期後果\n\n## 必引來源\n- 金管會 2024\n- 聯徵中心\n- 消債條例 [待補：條文編號]\n`} style={{ minHeight: 480, fontFamily: 'var(--mono)', fontSize: 12 }}></textarea>
              </Panel>
              <Panel en="Preview" zh="手稿預覽">
                <div style={{ padding: '20px 24px', minHeight: 480, background: 'rgba(17,25,37,0.4)', fontSize: 14, lineHeight: 1.9, color: 'var(--cream-dim)' }}>
                  <h2 style={{ fontSize: 20, color: 'var(--cream)', borderBottom: '1px solid var(--gold-line)', paddingBottom: 8 }}>欠卡債聯徵無資料怎麼辦</h2>
                  <h3 style={{ fontSize: 15, color: 'var(--cream)', marginTop: 16 }}>文章目標</h3>
                  <p>讀者搜尋此關鍵字時，往往在自查聯徵後感到困惑。本文需在 H2-2 段內明確回答「查不到 ≠ 消失」。</p>
                  <h3 style={{ fontSize: 15, color: 'var(--cream)', marginTop: 14 }}>H2 規劃</h3>
                  <ol style={{ paddingLeft: 22 }}>
                    <li>常見原因</li>
                    <li>是否真的消失？ <Badge kind="gold">待確認</Badge></li>
                    <li>債權轉讓</li><li>紀錄重新出現</li><li>法院支付命令</li><li>長期後果</li>
                  </ol>
                  <h3 style={{ fontSize: 15, color: 'var(--cream)', marginTop: 14 }}>必引來源</h3>
                  <ul style={{ paddingLeft: 22 }}>
                    <li>金管會 2024</li>
                    <li>聯徵中心</li>
                    <li>消債條例 <Badge kind="gold">待補</Badge></li>
                  </ul>
                </div>
              </Panel>
            </div>
          )}

          {tab === 'sources' && (
            <Panel en="Sources Ledger" zh="來源檢核表">
              <table className="ctable">
                <thead><tr><th style={{ width: 50 }}>Use</th><th>Title</th><th>URL</th><th style={{ width: 80 }}>Type</th><th style={{ width: 70 }}>Trust</th><th>Used For</th><th style={{ width: 80 }}>Status</th></tr></thead>
                <tbody>
                  {sources.map((s, i) => (
                    <tr key={i} className={s.comp ? 'blocker-row' : (s.trust < 5 && !s.comp ? 'warning-row' : '')}>
                      <td><span style={{ width: 14, height: 14, border: '1px solid var(--gold)', display: 'inline-block', position: 'relative' }}>{s.use && <span style={{ position: 'absolute', inset: 2, background: 'var(--gold)' }}></span>}</span></td>
                      <td style={{ color: 'var(--cream)' }}>{s.t}</td>
                      <td className="mono">{s.url}</td>
                      <td><Badge kind="gold">{s.type}</Badge></td>
                      <td className="mono" style={{ color: s.trust >= 8 ? 'var(--status-success)' : s.trust >= 5 ? 'var(--cream)' : 'var(--status-blocker)' }}>{s.trust}/10</td>
                      <td>{s.used}</td>
                      <td>{s.comp ? <Badge kind="blocked">COMPETITOR</Badge> : s.trust < 5 ? <Badge kind="warning">LOW TRUST</Badge> : <Badge kind="done">OK</Badge>}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </Panel>
          )}

          {tab === 'missing' && (
            <Panel en="Missing Info" zh="缺口清單">
              <div style={{ padding: '4px 0' }}>
                {[
                  { sec: 'h2-2', m: 'AMC 債權受讓的法律依據未引述', sev: 'blocker' },
                  { sec: 'h2-3', m: '消債條例條文編號未補', sev: 'warning' },
                  { sec: 'h2-5', m: '法院支付命令的回應時限未說明', sev: 'blocker' },
                  { sec: 'h2-6', m: '長期未處理的信用後果可加入具體案例', sev: 'suggestion' },
                ].map((m, i) => (
                  <div key={i} style={{
                    padding: '14px 18px', borderBottom: '1px solid rgba(201,169,97,0.1)',
                    borderLeft: `2px solid ${m.sev === 'blocker' ? 'var(--status-blocker)' : m.sev === 'warning' ? 'var(--status-warning)' : 'var(--gold-line-strong)'}`,
                    display: 'flex', gap: 14, alignItems: 'center',
                  }}>
                    <span className="mono" style={{ color: 'var(--gold)' }}>{m.sec}</span>
                    <span style={{ flex: 1, color: 'var(--cream)' }}>{m.m}</span>
                    <Badge kind={m.sev === 'blocker' ? 'blocked' : m.sev === 'warning' ? 'warning' : 'gold'}>{m.sev.toUpperCase()}</Badge>
                  </div>
                ))}
              </div>
            </Panel>
          )}
        </div>
      </div>
    </>
  );
};
window.Screen4 = Screen4;
