// Screen 2: Site Config / 文風指南
const Screen2 = () => {
  const sites = [
    { id: 'finance_client', name: 'LoginHeart 金融客戶', guide: 'v9.7', sections: 14, fp: '3b2d…91ef', active: true },
    { id: 'shun_zhou_tang', name: '順周堂', guide: 'v3.2', sections: 9, fp: 'a710…2f8c' },
    { id: 'loginheart_main', name: 'LoginHeart 主站', guide: 'v2.1', sections: 7, fp: 'c022…b4d1' },
    { id: 'local_service', name: '在地服務客戶', guide: 'v4.0', sections: 11, fp: 'e591…3c7a' },
  ];
  const sections = [
    { id: 'A', t: '主關鍵字密度', state: 'required' },
    { id: 'B', t: '競品分析參考', state: 'optional' },
    { id: 'C', t: '來源規範', state: 'required' },
    { id: 'D', t: 'CTA 文案模板', state: 'optional' },
    { id: 'E', t: '行銷誇飾用語', state: 'forbidden' },
    { id: 'F', t: '業配案例引用', state: 'forbidden' },
    { id: 'G', t: '金融合規禁用詞', state: 'required' },
    { id: 'H', t: '免責聲明 disclaimer', state: 'required' },
  ];
  return (
    <>
      <Topbar project="—" />
      <div className="charta-layout">
        <LeftNav activeNum="02" />
        <div className="charta-main">
          <ScreenHead en="Site Config Registry" zh="站點與文風指南" right={
            <>
              <Button kind="ghost" size="sm">匯出 JSON</Button>
              <Button kind="solid" size="sm">＋ 匯入文風指南</Button>
            </>
          } />
          <Divider />
          <div style={{ display: 'grid', gridTemplateColumns: '1.2fr 1fr', gap: 18 }}>
            <Panel en="Sites · Guides" zh="站點清單" corners>
              <table className="ctable">
                <thead>
                  <tr>
                    <th>Site</th>
                    <th style={{ width: 60 }}>Guide</th>
                    <th style={{ width: 80 }}>Sections</th>
                    <th>Fingerprint</th>
                    <th style={{ width: 80 }}>Action</th>
                  </tr>
                </thead>
                <tbody>
                  {sites.map(s => (
                    <tr key={s.id} className={s.active ? 'selected' : ''}>
                      <td>
                        <div style={{ color: 'var(--cream)' }}>{s.name}</div>
                        <div className="mono" style={{ marginTop: 2 }}>{s.id}</div>
                      </td>
                      <td className="mono" style={{ color: 'var(--gold)' }}>{s.guide}</td>
                      <td>{s.sections}</td>
                      <td className="mono">{s.fp}</td>
                      <td><Button kind="ghost" size="sm">View</Button></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </Panel>

            <Panel en="Guide Sections · finance v9.7" zh="文風規則卡">
              <div style={{ padding: '6px 0' }}>
                {sections.map(sec => (
                  <div key={sec.id} style={{
                    padding: '12px 18px',
                    borderBottom: '1px solid rgba(201,169,97,0.1)',
                    borderLeft: sec.state === 'forbidden' ? '2px solid var(--status-blocker)' : '2px solid transparent',
                    display: 'flex', alignItems: 'center', gap: 12,
                  }}>
                    <span style={{ fontFamily: 'var(--serif-en)', fontSize: 13, color: 'var(--gold)', letterSpacing: 1, width: 14 }}>{sec.id}</span>
                    <span style={{ fontSize: 13, color: 'var(--cream)', flex: 1 }}>{sec.t}</span>
                    {sec.state === 'required' && (
                      <span style={{ display: 'flex', gap: 5, alignItems: 'center', fontSize: 11, color: 'var(--gold)', fontFamily: 'var(--serif-en)', letterSpacing: 2 }}>
                        <span style={{ width: 6, height: 6, background: 'var(--gold)', transform: 'rotate(45deg)', display: 'inline-block' }}></span>
                        REQUIRED
                      </span>
                    )}
                    {sec.state === 'optional' && <Badge kind="ready">OPTIONAL</Badge>}
                    {sec.state === 'forbidden' && <Badge kind="blocked">FORBIDDEN</Badge>}
                  </div>
                ))}
              </div>
            </Panel>
          </div>
        </div>
        <div className="charta-rightpanel">
          <RP title="Selected Site">
            <RPRow k="site_id" v="finance_client" mono />
            <RPRow k="guide_version" v="v9.7" />
            <RPRow k="updated" v="2026·04·22" />
            <RPRow k="updated_by" v="ariel.hsu" />
          </RP>
          <RP title="Action ✕ Section Map">
            <RPRow k="generate_body" v="A · C · G · H" />
            <RPRow k="refine_section" v="A · C · G" />
            <RPRow k="generate_kt" v="A · D · H" />
            <RPRow k="generate_faq" v="A · D" />
          </RP>
          <RP title="Prompt Fingerprint">
            <div style={{ padding: 10, border: '1px dashed var(--gold-line)', fontFamily: 'var(--mono)', fontSize: 10.5, color: 'var(--cream-muted)', wordBreak: 'break-all' }}>
              3b2d8a1c91ef47bd1c0f<br/>e2a9837c5be40d129a7e
            </div>
          </RP>
        </div>
      </div>
    </>
  );
};
window.Screen2 = Screen2;
