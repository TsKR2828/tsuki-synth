// Screen 8: KT / FAQ
const Screen8 = () => {
  return (
    <>
      <Topbar />
      <div className="charta-layout no-right">
        <LeftNav activeNum="08" />
        <div className="charta-main">
          <ScreenHead en="Special Sections" zh="Key Takeaways / FAQ" right={
            <>
              <Button kind="ghost" size="sm">重生 KT placeholder</Button>
              <Button kind="solid" size="sm">產生 KT final</Button>
            </>
          } />
          <Divider />
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1.2fr', gap: 18 }}>
            <Panel en="Key Takeaways" zh="重點摘要" corners headRight={<Badge kind="gold">DRAFT PLACEHOLDER</Badge>}>
              <div style={{ padding: '14px 20px', background: 'rgba(201,169,97,0.05)', borderBottom: '1px solid var(--gold-line)', fontSize: 12, color: 'var(--cream-dim)' }}>
                這是根據 Brief / Outline 產生的暫存版 Key Takeaways。
                正式版需在 Body H2 完成後重新生成。
              </div>
              <div style={{ padding: '18px 24px' }}>
                {[
                  '查不到聯徵不代表債務消失，銀行內部系統與聯徵資料庫並非同步。',
                  '呆帳常被打包出售給資產管理公司（AMC），由受讓方繼續追償。',
                  '收到法院支付命令必須於 20 日內提出異議，否則視同確定。',
                  '長期未處理可能導致薪資遭強制執行，並影響未來十年信用紀錄。',
                ].map((t, i) => (
                  <div key={i} style={{ display: 'flex', gap: 14, padding: '10px 0', borderBottom: '1px solid rgba(201,169,97,0.08)' }}>
                    <span style={{ fontFamily: 'var(--serif-en)', color: 'var(--gold)', fontSize: 14, width: 24 }}>0{i + 1}</span>
                    <span style={{ flex: 1, fontSize: 14, lineHeight: 1.7, color: 'var(--cream)' }}>{t}</span>
                  </div>
                ))}
              </div>
              <div style={{ padding: '12px 20px', borderTop: '1px solid var(--gold-line)', fontSize: 11, color: 'var(--cream-faint)' }}>
                ※ KT final 生成後，placeholder 將自動 archive。已修改的人工版本將作為參考輸入。
              </div>
            </Panel>

            <Panel en="FAQ Candidate Ledger" zh="FAQ 候選表" headRight={<Button kind="ghost" size="sm">＋ 手動新增</Button>}>
              <table className="ctable">
                <thead><tr><th style={{ width: 50 }}>Use</th><th>Question</th><th style={{ width: 110 }}>Source</th><th style={{ width: 90 }}>Confidence</th><th style={{ width: 130 }}>Category</th></tr></thead>
                <tbody>
                  {[
                    { use: true, q: '欠卡債查不到聯徵，還需要還嗎？', src: 'review_gap', conf: 0.82, cat: 'reader_question_unanswered' },
                    { use: true, q: '債權被轉讓後，原銀行還能催繳嗎？', src: 'PAA', conf: 0.78, cat: 'unclear_condition' },
                    { use: true, q: '收到法院支付命令的回應期限是多久？', src: 'review_gap', conf: 0.91, cat: 'missing_explanation' },
                    { use: false, q: '我可以直接放著不管嗎？', src: 'PAA', conf: 0.34, cat: 'reader_question_unanswered' },
                    { use: true, q: '如何確認債權目前在誰手上？', src: 'manual', conf: 0.88, cat: 'process_gap' },
                    { use: false, q: '債務會傳給家人嗎？', src: 'AI suggested', conf: 0.45, cat: 'missing_edge_case' },
                  ].map((f, i) => (
                    <tr key={i} className={f.use ? 'selected' : ''}>
                      <td><span style={{ width: 14, height: 14, border: '1px solid var(--gold)', display: 'inline-block', position: 'relative' }}>{f.use && <span style={{ position: 'absolute', inset: 2, background: 'var(--gold)' }}></span>}</span></td>
                      <td style={{ color: 'var(--cream)' }}>{f.q}</td>
                      <td><Badge kind={f.src === 'review_gap' ? 'gold' : f.src === 'PAA' ? 'queued' : f.src === 'manual' ? 'done' : 'soft'}>{f.src}</Badge></td>
                      <td className="mono" style={{ color: f.conf > 0.7 ? 'var(--status-success)' : f.conf > 0.5 ? 'var(--status-warning)' : 'var(--status-blocker)' }}>{f.conf.toFixed(2)}</td>
                      <td style={{ fontSize: 11 }}>{f.cat.replace(/_/g, ' · ')}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
              <div style={{ padding: '12px 16px', background: 'rgba(214,168,95,0.08)', borderTop: '1px solid rgba(214,168,95,0.4)', fontSize: 12, color: 'var(--cream)' }}>
                目前 4 個 FAQ 候選信心 ≥ 0.7，已可進入正式生成。建議手動補充與「債務協商」相關的常見疑問。
              </div>
            </Panel>
          </div>
        </div>
      </div>
    </>
  );
};
window.Screen8 = Screen8;
