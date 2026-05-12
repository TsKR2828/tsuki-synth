// Screen 9: 內外連
const Screen9 = () => {
  const externals = [
    { use: true, anchor: '金管會 2024 呆帳處理白皮書', url: 'https://fsc.gov.tw/...', clean: 'fsc.gov.tw/2024-bad-debt', type: 'official', trust: 9, pos: 'h2-2', reason: '主要法源' },
    { use: true, anchor: '消費者債務清理條例', url: 'https://law.moj.gov.tw/...', clean: 'law.moj.gov.tw/消債條例', type: 'law', trust: 10, pos: 'h2-5', reason: '法律依據' },
    { use: true, anchor: '聯合徵信中心', url: 'https://jcic.org.tw/...', clean: 'jcic.org.tw/個人信用', type: 'official', trust: 9, pos: 'h2-1', reason: '查詢入口' },
    { use: false, anchor: '律師事務所卡債解套', url: 'https://competitor.tw/...', clean: '—', type: 'blog', trust: 4, pos: '—', reason: '競品頁面' },
    { use: false, anchor: '舊版金管會 2018 報告', url: 'https://fsc.gov.tw/old/...', clean: 'fsc.gov.tw/2018-...', type: 'official', trust: 6, pos: '—', reason: '已被 2024 版本取代' },
  ];
  const internals = [
    { use: true, anchor: '債務協商完整流程', target: '/finance/debt-negotiation', weight: 0.92, rel: 'sibling', pos: 'h2-3' },
    { use: true, anchor: '聯徵紀錄保留期限解析', target: '/finance/jcic-retention', weight: 0.88, rel: 'pillar→cluster', pos: 'h2-1' },
    { use: true, anchor: '法院支付命令處理指南', target: '/finance/court-order', weight: 0.84, rel: 'sibling', pos: 'h2-5' },
    { use: false, anchor: '信用卡推薦比較', target: '/finance/credit-card-rec', weight: 0.42, rel: 'unrelated', pos: '—' },
    { use: true, anchor: '個人信用分數提升 7 步', target: '/finance/score-up', weight: 0.71, rel: 'cluster', pos: 'h2-6' },
  ];
  return (
    <>
      <Topbar />
      <div className="charta-layout no-right">
        <LeftNav activeNum="09" />
        <div className="charta-main">
          <ScreenHead en="Link Curation" zh="內外連確認" right={
            <>
              <Button kind="ghost" size="sm">匯入內連報告</Button>
              <Button kind="ghost" size="sm">重新比對</Button>
              <Button kind="solid" size="sm">套用選取</Button>
            </>
          } />
          <Divider />
          <Panel en="External Sources" zh="外部連結" corners style={{ marginBottom: 18 }}>
            <table className="ctable">
              <thead><tr><th style={{ width: 50 }}>Use</th><th>Anchor</th><th>Clean URL</th><th style={{ width: 90 }}>Type</th><th style={{ width: 70 }}>Trust</th><th style={{ width: 60 }}>Pos</th><th>Reason</th></tr></thead>
              <tbody>
                {externals.map((e, i) => (
                  <tr key={i} className={e.type === 'blog' && !e.use ? 'blocker-row' : ''}>
                    <td><span style={{ width: 14, height: 14, border: '1px solid var(--gold)', display: 'inline-block', position: 'relative' }}>{e.use && <span style={{ position: 'absolute', inset: 2, background: 'var(--gold)' }}></span>}</span></td>
                    <td style={{ color: 'var(--cream)' }}>{e.anchor}</td>
                    <td className="mono">{e.clean}</td>
                    <td><Badge kind="gold">{e.type}</Badge></td>
                    <td className="mono" style={{ color: e.trust >= 8 ? 'var(--status-success)' : e.trust >= 5 ? 'var(--cream)' : 'var(--status-blocker)' }}>{e.trust}/10</td>
                    <td className="mono">{e.pos}</td>
                    <td>
                      {e.reason}
                      {!e.use && e.type === 'blog' && <span style={{ marginLeft: 8 }}><Badge kind="blocked">BLOCKED</Badge></span>}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </Panel>

          <Panel en="Internal Link Suggestions" zh="內部連結建議" headRight={<Button kind="ghost" size="sm">查看 bridge log</Button>}>
            <table className="ctable">
              <thead><tr><th style={{ width: 50 }}>Use</th><th>Anchor</th><th>Target Page</th><th style={{ width: 100 }}>Weight</th><th style={{ width: 130 }}>Relation</th><th style={{ width: 60 }}>Pos</th></tr></thead>
              <tbody>
                {internals.map((l, i) => (
                  <tr key={i} className={l.weight < 0.5 ? 'warning-row' : ''}>
                    <td><span style={{ width: 14, height: 14, border: '1px solid var(--gold)', display: 'inline-block', position: 'relative' }}>{l.use && <span style={{ position: 'absolute', inset: 2, background: 'var(--gold)' }}></span>}</span></td>
                    <td style={{ color: 'var(--cream)' }}>{l.anchor}</td>
                    <td className="mono">{l.target}</td>
                    <td>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                        <span className="mono" style={{ color: l.weight > 0.7 ? 'var(--status-success)' : l.weight > 0.5 ? 'var(--cream)' : 'var(--status-warning)', width: 36 }}>{l.weight.toFixed(2)}</span>
                        <span style={{ flex: 1, height: 3, background: 'rgba(201,169,97,0.15)', position: 'relative' }}>
                          <span style={{ position: 'absolute', inset: 0, width: `${l.weight * 100}%`, background: 'var(--gold)' }}></span>
                        </span>
                      </div>
                    </td>
                    <td><Badge kind={l.rel === 'unrelated' ? 'warning' : 'gold'}>{l.rel}</Badge></td>
                    <td className="mono">{l.pos}</td>
                  </tr>
                ))}
              </tbody>
            </table>
            <div style={{ padding: '14px 18px', borderTop: '1px solid var(--gold-line)', display: 'grid', gridTemplateColumns: 'repeat(5,1fr)', gap: 10, fontSize: 11 }}>
              {['semantic 0.34', 'intent 0.21', 'pillar/cluster 0.18', 'anchor naturalness 0.17', 'priority 0.10'].map((s, i) => (
                <div key={i} style={{ padding: 8, border: '1px dashed var(--gold-line)', textAlign: 'center', color: 'var(--cream-muted)' }}>
                  <div style={{ fontFamily: 'var(--serif-en)', letterSpacing: 1.5, color: 'var(--gold-dim)', fontSize: 9.5, textTransform: 'uppercase' }}>weight</div>
                  <div className="mono" style={{ marginTop: 2, color: 'var(--cream)' }}>{s}</div>
                </div>
              ))}
            </div>
          </Panel>
        </div>
      </div>
    </>
  );
};
window.Screen9 = Screen9;
