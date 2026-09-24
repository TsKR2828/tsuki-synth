# 施工卡 WF0914-D10：B-1 真槌力譜滾降文獻獵取

> lane：研究（**不碰 `src/`、`tools/`、`tests/`；不實作 B-1**——B-1 落地會改渲染輸出＝R10，另立卡）
> 先讀：`docs/HAMMER_CONTACT_SOURCES.md`、A14 裁決包 `reports/decision_packets/A14_weak_fundamental_ruling.zh-TW.md`
> （理解 B-1 是什麼：真實槌力譜滾降取代半正弦外插）、`WF0914_README.md` §2 第 3 條（禁引未 fetch 的數字）。

## 0. 一句話目標

D10 缺的是文獻：**Hall 1987**（JASA 鋼琴弦激勵系列）與 **Chaigne & Askenfelt 1994**（JASA 兩部）
的槌力譜滾降資料至今未取得。本卡窮盡**開放管道**找全文或等價資料，找到就萃取（逐字引述＋頁碼），
找不到就誠實記錄查過哪些管道。

## 1. 管道（依序試，逐管道記結果）

1. 作者自存檔：KTH TMH 的 **STL-QPSR 季報**（Askenfelt & Jansson 系列多篇免費公開，
   `speech.kth.se` 已是 repo 既有引用來源）——找含力譜/力脈衝頻域圖的篇目。
2. arXiv / HAL（法國，Chaigne 後期任教 ENSTA，早期文章可能有 HAL 存檔）。
3. Google Scholar 連到的作者頁/機構 repository 免費 PDF。
4. Woodhouse *Euphonics*（euphonics.org，repo 已引用）相關章節是否轉載了力譜滾降數據
   （轉載數據可用，但溯源要寫「Euphonics 轉引自 X」，兩層都記）。
5. 找**替代文獻**：任何同儕審查來源給出「felt 槌接觸力的頻譜滾降實測（dB/octave 或頻譜圖數值）」
   都算達標，不限於這兩篇。

**不可用**：Sci-Hub 類、要付費/登入的全文、只有摘要的來源的內文數字。

## 2. 產出

- 找到 → `docs/HAMMER_CONTACT_SOURCES.md` 新增一節「§X 槌力譜滾降（B-1 依據）」：
  數據（逐字/逐圖描述＋頁碼＋URL）、適用域、與現行半正弦模型的差異點。**只記文獻，不提案實作**。
- 找不到 → 同文件新增一節誠實記錄：查過的管道清單、各管道實際結果、
  「B-1 維持等文獻狀態」。兩種結果都是本卡合法完成（比照 B7.md 的誠實體例）。
- `TODO.md` D10 條目同步一行。

## 3. GATE

- `git diff` 只含上列兩檔。
- 每條引文附 URL 且工兵**親自 fetch 過該頁**（證據：把 fetch 到的關鍵段落存
  `output/wf0914/D10/fetched_excerpts.md`，稽核會抽查重新 fetch 對照）。
