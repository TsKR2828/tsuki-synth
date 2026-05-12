// Screen 11: Log / Archive
const Screen11 = () => {
  const [tab, setTab] = React.useState('versions');
  const tabs = [
    ['versions', 'Versions'],
    ['api', 'API Calls'],
    ['fp', 'Prompt Fingerprints'],
    ['patch', 'Patch Logs'],
    ['review', 'Review Reports'],
    ['export', 'Export History'],
    ['error', 'Error / Retry'],
    ['queue', 'Queue / Budget'],
  ];
  return (
    <>
      <Topbar />
      <div className="charta-layout no-right">
        <LeftNav activeNum="11" />
        <div className="charta-main">
          <ScreenHead en="Archive Log" zh="Log / 版本紀錄" right={<Button kind="ghost" size="sm">匯出 CSV</Button>} />
          <Divider />
          <div style={{ display: 'flex', gap: 0, marginBottom: 14, borderBottom: '1px solid var(--gold-line)', flexWrap: 'wrap' }}>
            {tabs.map(([id, en]) => (
              <div key={id} onClick={() => setTab(id)} style={{
                padding: '10px 16px', cursor: 'pointer',
                borderBottom: tab === id ? '2px solid var(--gold)' : '2px solid transparent',
                marginBottom: -1,
                fontFamily: 'var(--serif-en)', fontSize: 11, letterSpacing: 2,
                color: tab === id ? 'var(--gold)' : 'var(--gold-dim)', textTransform: 'uppercase',
              }}>{en}</div>
            ))}
          </div>

          {tab === 'versions' && (
            <Panel en="Versions" zh="版本紀錄">
              <table className="ctable">
                <thead><tr><th>Section</th><th>Version</th><th>Created</th><th>By</th><th>Hash</th><th>Status</th><th>Stale</th><th>Action</th></tr></thead>
                <tbody>
                  {[
                    ['h2-2', 'v3', '05·07 14:02', 'claude·haiku', '9f31a0c7', 'accepted', 'soft'],
                    ['h2-2', 'v2', '05·06 18:24', 'claude·haiku', '4d18ee21', 'archived', null],
                    ['h2-2', 'v1', '05·06 11:08', 'claude·haiku', '882a13bc', 'archived', null],
                    ['h2-3', 'v1', '05·07 13:48', 'claude·haiku', 'b7e25ad0', 'accepted', null],
                    ['KT', 'v1·placeholder', '05·06 11:30', 'claude·haiku', 'aa90e4f2', 'placeholder', null],
                    ['brief', 'v2', '05·06 10:55', 'ariel.hsu', '1a8c5519', 'accepted', null],
                    ['brief', 'v1', '05·06 09:41', 'ariel.hsu', '70c2a8e3', 'archived', null],
                  ].map((r, i) => (
                    <tr key={i}>
                      <td className="mono" style={{ color: 'var(--gold)' }}>{r[0]}</td>
                      <td>{r[1]}</td>
                      <td style={{ fontFamily: 'var(--serif-en)', letterSpacing: 1 }}>{r[2]}</td>
                      <td className="mono">{r[3]}</td>
                      <td className="mono">{r[4]}</td>
                      <td>{r[5] === 'accepted' ? <Badge kind="accepted">ACCEPTED</Badge> : r[5] === 'placeholder' ? <Badge kind="gold">PLACEHOLDER</Badge> : <Badge kind="archived">ARCHIVED</Badge>}</td>
                      <td>{r[6] === 'soft' ? <Badge kind="soft">SOFT</Badge> : <span style={{ color: 'var(--cream-faint)' }}>—</span>}</td>
                      <td><Button kind="ghost" size="sm">View</Button></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </Panel>
          )}

          {tab === 'api' && (
            <Panel en="API Calls" zh="API 呼叫紀錄">
              <table className="ctable">
                <thead><tr><th>Time</th><th>Action</th><th>Model</th><th>Input</th><th>Output</th><th>Cost</th><th>Latency</th><th>Status</th></tr></thead>
                <tbody>
                  {[
                    ['14:02:18', 'generate_body · h2-2', 'claude-haiku-4-5', 4210, 2210, '$0.062', '8.4s', 'success'],
                    ['13:48:02', 'generate_body · h2-3', 'claude-haiku-4-5', 3980, 1620, '$0.048', '6.2s', 'success'],
                    ['13:32:45', 'review · full', 'claude-sonnet-4', 12440, 3120, '$0.184', '14.1s', 'success'],
                    ['13:18:11', 'generate_brief', 'claude-haiku-4-5', 2210, 1840, '$0.041', '5.8s', 'success'],
                    ['12:55:40', 'generate_body · h2-2', 'claude-haiku-4-5', 4210, 0, '—', '21.0s', 'overloaded'],
                  ].map((r, i) => (
                    <tr key={i} className={r[7] === 'overloaded' ? 'warning-row' : ''}>
                      <td className="mono">{r[0]}</td>
                      <td style={{ color: 'var(--cream)' }}>{r[1]}</td>
                      <td className="mono">{r[2]}</td>
                      <td className="mono">{r[3]}</td>
                      <td className="mono">{r[4]}</td>
                      <td className="mono" style={{ color: 'var(--gold)' }}>{r[5]}</td>
                      <td className="mono">{r[6]}</td>
                      <td>{r[7] === 'success' ? <Badge kind="done">OK</Badge> : <Badge kind="warning">RETRIED</Badge>}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </Panel>
          )}

          {tab === 'fp' && (
            <Panel en="Prompt Fingerprints" zh="Prompt 指紋藏書票">
              <div style={{ padding: 22, display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: 16 }}>
                {[
                  { id: 'fp_3b2d91ef', action: 'generate_body', secs: 'A · C · G · H', model: 'claude-haiku-4-5', uses: 18 },
                  { id: 'fp_a7102f8c', action: 'refine_section', secs: 'A · C · G', model: 'claude-haiku-4-5', uses: 7 },
                  { id: 'fp_c022b4d1', action: 'generate_kt', secs: 'A · D · H', model: 'claude-haiku-4-5', uses: 3 },
                  { id: 'fp_e5913c7a', action: 'review · full', secs: 'A · C · E · F · G · H', model: 'claude-sonnet-4', uses: 4 },
                ].map((f, i) => (
                  <div key={i} style={{ position: 'relative', border: '1px solid var(--gold-line)', padding: '18px 20px', background: 'rgba(17,25,37,0.5)' }}>
                    <Corner pos="tl" /><Corner pos="tr" /><Corner pos="bl" /><Corner pos="br" />
                    <div style={{ fontFamily: 'var(--serif-en)', fontSize: 10, letterSpacing: 3, color: 'var(--gold-dim)', textTransform: 'uppercase' }}>Fingerprint</div>
                    <div className="mono" style={{ fontSize: 13, color: 'var(--gold)', marginTop: 4, marginBottom: 12 }}>{f.id}</div>
                    <div className="rp-row"><span className="k">action</span><span className="v">{f.action}</span></div>
                    <div className="rp-row"><span className="k">guide sections</span><span className="v">{f.secs}</span></div>
                    <div className="rp-row"><span className="k">model</span><span className="v mono">{f.model}</span></div>
                    <div className="rp-row"><span className="k">uses</span><span className="v">{f.uses}</span></div>
                  </div>
                ))}
              </div>
            </Panel>
          )}

          {(tab === 'patch' || tab === 'review' || tab === 'export' || tab === 'error' || tab === 'queue') && (
            <Panel en={tabs.find(t => t[0] === tab)[1]} zh="紀錄索引">
              <div style={{ padding: 30, textAlign: 'center', color: 'var(--cream-muted)' }}>
                <Divider width={120} />
                <div style={{ fontSize: 13 }}>此分頁採用相同的索引表格樣式，依 timestamp 倒序顯示，每筆 row 高度 compact，error 不做整排紅底，以左側細線標示。</div>
              </div>
            </Panel>
          )}
        </div>
      </div>
    </>
  );
};
window.Screen11 = Screen11;
