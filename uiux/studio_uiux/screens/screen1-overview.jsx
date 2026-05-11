// Screen 1: 專案總覽
const Screen1 = () => {
  const projects = [
    { title: '欠卡債聯徵無資料怎麼辦', site: 'finance', kw: '欠卡債聯徵無資料', stage: 'review', review: 'blocked', guide: 'v9.7', upd: '05·07', cost: '$3.20', exp: '未導出', blocked: true },
    { title: '信用卡呆帳五年揭露期完整解析', site: 'finance', kw: '信用卡呆帳五年', stage: 'body', review: 'soft_stale', guide: 'v9.7', upd: '05·06', cost: '$5.10', exp: '未導出' },
    { title: '中醫調理體質的常見迷思', site: '順周堂', kw: '中醫調理體質', stage: 'export_ready', review: 'clean', guide: 'v3.2', upd: '05·05', cost: '$4.40', exp: '已導出' },
    { title: 'LoginHeart 個人化登入流程介紹', site: 'LoginHeart', kw: '登入流程', stage: 'brief', review: '—', guide: 'v2.1', upd: '05·04', cost: '$0.42', exp: '未導出' },
    { title: '債務協商與更生程序差異', site: 'finance', kw: '債務協商 更生', stage: 'sources', review: '—', guide: 'v9.7', upd: '05·03', cost: '$1.10', exp: '未導出' },
    { title: '結婚登記的完整流程與所需文件', site: '在地服務', kw: '結婚登記流程', stage: 'export_ready', review: 'clean', guide: 'v4.0', upd: '05·02', cost: '$3.80', exp: '已導出' },
    { title: '保單借款 vs 信用貸款比較', site: 'finance', kw: '保單借款', stage: 'review', review: 'blocked', guide: 'v9.7', upd: '04·30', cost: '$6.20', exp: '未導出', blocked: true },
  ];
  const sites = [
    { id: 'finance', name: 'LoginHeart 金融', count: 12, active: true },
    { id: 'shun', name: '順周堂', count: 8 },
    { id: 'login', name: 'LoginHeart 主站', count: 4 },
    { id: 'local', name: '在地服務客戶', count: 6 },
  ];
  const stageBadge = (s) => {
    const m = { brief: ['gold', 'BRIEF'], sources: ['queued', 'SOURCES'], body: ['running', 'BODY'], review: ['warning', 'REVIEW'], export_ready: ['accepted', 'READY'] };
    const [k, t] = m[s] || ['ready', s.toUpperCase()];
    return <Badge kind={k}>{t}</Badge>;
  };
  return (
    <>
      <Topbar project="—" />
      <div className="charta-layout">
        <div className="charta-leftnav">
          <div className="nav-section">Site Ledger</div>
          {sites.map(s => (
            <div key={s.id} className={`nav-item ${s.active ? 'active' : ''}`}>
              <span className="num">◇</span>
              <span>{s.name}</span>
              <span className="nav-badge">{s.count}</span>
            </div>
          ))}
          <div className="nav-section" style={{ marginTop: 24 }}>Quick Actions</div>
          <div className="nav-item"><span className="num">＋</span><span>新增站點</span></div>
          <div className="nav-item"><span className="num">↑</span><span>匯入文風指南</span></div>
        </div>

        <div className="charta-main" style={{ gridColumn: '2 / span 2' }}>
          <ScreenHead en="Project Index" zh="專案總覽 — LoginHeart 金融客戶" right={
            <>
              <Button kind="ghost" size="sm">匯入舊專案</Button>
              <Button kind="ghost" size="sm">匯入文風指南</Button>
              <Button kind="solid" size="sm">＋ 新文章</Button>
            </>
          } />
          <Divider />

          {/* stat strip */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(5, 1fr)', gap: 14, marginBottom: 20 }}>
            {[
              ['Active Projects', '12', null],
              ['In Review', '4', 'warning'],
              ['Blocked', '2', 'blocker'],
              ['Stale Artifacts', '7', 'stale'],
              ['Today Spend', '$14.20', 'gold'],
            ].map(([k, v, c], i) => (
              <div key={i} className="charta-panel padded" style={{ padding: 14 }}>
                <div style={{ fontFamily: 'var(--serif-en)', fontSize: 10, letterSpacing: 2.5, color: 'var(--gold-dim)', textTransform: 'uppercase' }}>{k}</div>
                <div style={{
                  fontSize: 26, fontFamily: 'var(--serif-en)', fontWeight: 400, marginTop: 4,
                  color: c === 'blocker' ? 'var(--status-blocker)' : c === 'warning' ? 'var(--status-warning)' : c === 'stale' ? 'var(--status-stale)' : c === 'gold' ? 'var(--gold)' : 'var(--cream)',
                }}>{v}</div>
              </div>
            ))}
          </div>

          <Panel en="Recent Projects" zh="近期文章專案" corners>
            <table className="ctable">
              <thead>
                <tr>
                  <th>Title</th>
                  <th style={{ width: 100 }}>Site</th>
                  <th>Primary Keyword</th>
                  <th style={{ width: 80 }}>Stage</th>
                  <th style={{ width: 110 }}>Review</th>
                  <th style={{ width: 70 }}>Guide</th>
                  <th style={{ width: 70 }}>Updated</th>
                  <th style={{ width: 70 }}>Cost</th>
                  <th style={{ width: 80 }}>Export</th>
                </tr>
              </thead>
              <tbody>
                {projects.map((p, i) => (
                  <tr key={i} className={p.blocked ? 'blocker-row' : ''}>
                    <td style={{ color: 'var(--cream)' }}>{p.title}</td>
                    <td><Badge kind="gold">{p.site}</Badge></td>
                    <td className="mono">{p.kw}</td>
                    <td>{stageBadge(p.stage)}</td>
                    <td>{p.review === 'blocked' ? <Badge kind="blocked">BLOCKED</Badge> : p.review === 'soft_stale' ? <Badge kind="soft">SOFT</Badge> : p.review === 'clean' ? <Badge kind="done">CLEAN</Badge> : <span style={{ color: 'var(--cream-faint)' }}>—</span>}</td>
                    <td className="mono">{p.guide}</td>
                    <td style={{ fontFamily: 'var(--serif-en)', letterSpacing: 1 }}>{p.upd}</td>
                    <td className="mono">{p.cost}</td>
                    <td style={{ fontSize: 11.5, color: p.exp === '已導出' ? 'var(--status-success)' : 'var(--cream-muted)' }}>{p.exp}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </Panel>
        </div>
      </div>
    </>
  );
};
window.Screen1 = Screen1;
