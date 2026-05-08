// Screen 5: H2 分段生成
const Screen5 = () => {
  const sections = [
    { id: 'h2-1', title: '欠卡債查不到聯徵的常見原因', status: 'accepted', version: 'v2', tokens: 1840 },
    { id: 'h2-2', title: '欠卡債查不到聯徵代表債務消失了嗎？', status: 'accepted', version: 'v3', stale: 'soft', issues: 1, tokens: 2210, current: true },
    { id: 'h2-3', title: '債權轉讓後，討債流程會怎麼進行？', status: 'running', version: 'v4', tokens: 1620 },
    { id: 'h2-4', title: '若聯徵突然又出現紀錄，可能發生了什麼事？', status: 'queued', version: '—' },
    { id: 'h2-5', title: '收到法院支付命令該如何回應？', status: 'queued', version: '—' },
    { id: 'h2-6', title: '長期未處理可能面臨的法律與信用後果', status: 'ready', version: '—' },
  ];
  const statusBadge = (s, v, stale) => {
    if (s === 'accepted') return <Badge kind="accepted">ACCEPTED {v}</Badge>;
    if (s === 'running') return <Badge kind="running" dot>RUNNING</Badge>;
    if (s === 'queued') return <Badge kind="queued">QUEUED</Badge>;
    if (s === 'ready') return <Badge kind="ready">NOT STARTED</Badge>;
    return null;
  };
  return (
    <>
      <Topbar />
      <div className="charta-layout">
        <LeftNav activeNum="05" />
        <div className="charta-main">
          <ScreenHead en="Body Section Generator" zh="H2 分段生成" right={
            <>
              <Button kind="ghost" size="sm">View Prompt</Button>
              <Button kind="ghost" size="sm">View API Log</Button>
              <Button kind="danger" size="sm">Stop Current Job</Button>
              <Button kind="solid" size="sm">Generate Selected</Button>
            </>
          } />
          <Divider />
          <div style={{ display: 'grid', gridTemplateColumns: '280px 1fr', gap: 18 }}>
            {/* Section List */}
            <Panel en="Sections" zh="章節索引">
              <div style={{ padding: '6px 0' }}>
                {sections.map(s => (
                  <div key={s.id} style={{
                    padding: '12px 18px',
                    borderLeft: s.current ? '2px solid var(--gold)' : '2px solid transparent',
                    background: s.current ? 'var(--surface-selected)' : 'transparent',
                    borderBottom: '1px solid rgba(201,169,97,0.08)',
                    cursor: 'pointer',
                  }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 6 }}>
                      <span style={{ fontFamily: 'var(--mono)', fontSize: 11, color: 'var(--gold)' }}>◇ {s.id}</span>
                      {statusBadge(s.status, s.version, s.stale)}
                    </div>
                    <div style={{ fontSize: 12.5, color: 'var(--cream-dim)', lineHeight: 1.5, marginBottom: 6 }}>{s.title}</div>
                    <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
                      {s.stale === 'soft' && <Badge kind="soft">SOFT STALE</Badge>}
                      {s.issues > 0 && <Badge kind="blocked">{s.issues} BLOCKER</Badge>}
                      {s.tokens && <span style={{ fontFamily: 'var(--serif-en)', fontSize: 10, color: 'var(--cream-faint)', letterSpacing: 1.5 }}>{s.tokens} TOK</span>}
                    </div>
                  </div>
                ))}
              </div>
            </Panel>

            {/* Manuscript Preview */}
            <Panel en="Manuscript" zh="手稿預覽 — h2-2" corners headRight={
              <>
                <Badge kind="accepted">ACCEPTED v3</Badge>
                <Badge kind="soft">SOFT STALE</Badge>
              </>
            }>
              <div style={{ padding: '24px 32px', minHeight: 480, background: 'rgba(17,25,37,0.4)' }}>
                <h2 style={{
                  fontFamily: 'var(--serif)', fontSize: 22, fontWeight: 500, color: 'var(--cream)',
                  borderBottom: '1px solid var(--gold-line)', paddingBottom: 10, marginBottom: 18
                }}>
                  欠卡債查不到聯徵代表債務消失了嗎？
                </h2>
                <p style={{ lineHeight: 2, fontSize: 15, color: 'var(--cream-dim)', marginBottom: 16 }}>
                  許多讀者在自己的聯徵紀錄裡，找不到那筆原本欠下的卡債，便以為「沒紀錄＝沒事了」。
                  事實上，<span style={{ color: 'var(--gold)', borderBottom: '1px dashed var(--gold-muted)' }}>查不到聯徵不等於債務消失</span>，
                  銀行的內部債權系統與聯合徵信中心的資料庫並非同步運作。
                </p>
                <p style={{ lineHeight: 2, fontSize: 15, color: 'var(--cream-dim)', marginBottom: 16, position: 'relative' }}>
                  <span style={{
                    position: 'absolute', left: -14, top: 4, width: 2, height: 'calc(100% - 8px)',
                    background: 'var(--status-blocker)'
                  }}></span>
                  根據實務觀察，債權可能已被轉讓給資產管理公司
                  <span style={{
                    background: 'rgba(217,120,102,0.12)', borderBottom: '1px solid var(--status-blocker)',
                    padding: '0 2px', color: 'var(--cream)'
                  }}>[待補來源]</span>，
                  此時即便聯徵不顯示，債務仍存在於受讓方手上。
                </p>
                <h3 style={{ fontSize: 16, color: 'var(--cream)', marginTop: 24, marginBottom: 12 }}>
                  ◇ 三種「聯徵查無」但債務仍存在的情境
                </h3>
                <ol style={{ lineHeight: 2, fontSize: 14.5, color: 'var(--cream-dim)', paddingLeft: 22 }}>
                  <li>原銀行已將債權打包出售給資產管理公司（AMC）。</li>
                  <li>呆帳已逾五年揭露期，但債權人仍保有追償權。</li>
                  <li>聯徵紀錄因系統延遲尚未更新，債權仍在執行中。</li>
                </ol>
                <p style={{ marginTop: 18, fontSize: 13, color: 'var(--cream-faint)', fontStyle: 'italic' }}>
                  ※ key sentence highlighted · source marker [待補] · 1 issue annotated
                </p>
              </div>
            </Panel>
          </div>
        </div>

        <div className="charta-rightpanel">
          <RP title="Section">
            <RPRow k="ID" v="h2-2" mono />
            <RPRow k="Title" v="欠卡債查不到聯徵…" />
            <RPRow k="Type" v="body_section" />
          </RP>
          <RP title="Artifact">
            <RPRow k="Status" v={<Badge kind="accepted">ACCEPTED</Badge>} />
            <RPRow k="Version" v="v3" />
            <RPRow k="Stale" v={<Badge kind="soft">SOFT</Badge>} />
            <RPRow k="Hash" v="9f31a0c7" mono />
          </RP>
          <RP title="Guide">
            <RPRow k="Version" v="v9.7" />
            <RPRow k="Sections" v="A / C / G" />
            <RPRow k="Fingerprint" v="3b2d…91ef" mono />
          </RP>
          <RP title="Tokens · Cost">
            <RPRow k="Input" v="4,210" />
            <RPRow k="Output" v="2,210" />
            <RPRow k="Cost" v="$0.062" />
          </RP>
          <RP title="Queue">
            <RPRow k="h2-3" v={<Badge kind="running" dot>RUNNING</Badge>} />
            <RPRow k="h2-4" v={<Badge kind="queued">QUEUED</Badge>} />
            <RPRow k="h2-5" v={<Badge kind="queued">QUEUED</Badge>} />
            <div style={{ marginTop: 10, padding: 10, border: '1px solid var(--gold-line)', background: 'rgba(17,25,37,0.5)' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 11, color: 'var(--cream-muted)', marginBottom: 6 }}>
                <span>BUDGET TODAY</span>
                <span style={{ color: 'var(--gold)' }}>$3.20 / $20</span>
              </div>
              <div style={{ height: 3, background: 'rgba(201,169,97,0.15)' }}>
                <div style={{ width: '16%', height: '100%', background: 'var(--gold)' }}></div>
              </div>
            </div>
          </RP>
        </div>
      </div>
    </>
  );
};
window.Screen5 = Screen5;
