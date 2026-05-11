# SEO Content Studio — Charta 風格 UI/UX 置換設計指南

> 用途：給 Claude Design / 前端設計模型生成 SEO Content Studio 的 Charta 風格 UI mockup、React prototype、Design System 或 Wireframe。
>
> 本文件只置換前端視覺、排版、元件語彙與互動呈現。  
> 保留 Studio 原本的產品架構：三欄式桌面工作台、11 個主要 screen、H2 分段生成、Review / Blocker、Refine / Diff、KT / FAQ、內外連、Export Gate、Log / Version。
>
> 不在此階段實作後端、API、資料庫、Claude API 呼叫、Tauri sidecar 或 Python engine。

---

## 0. 設計任務摘要

請將 **SEO Content Studio** 的原生工具型 dashboard 視覺，置換成 **Charta** 的品牌美學。

保留 Studio 的專業控制台骨架：

1. 建立文章任務
2. 匯入 / 選擇站點與文風指南
3. 分析關鍵字、SERP、Brief、來源
4. 逐段生成 H2 內容
5. 顯示每段生成狀態、版本、token / cost
6. 跑審稿與 blocker 檢查
7. 針對單一 H2 局部重跑
8. 比對修改差異
9. 整合 Key Takeaways、FAQ、內外連
10. 依照不同客戶導出 HTML / MD / Google Docs 用稿
11. 查看 Log / Version / API Call / Prompt Fingerprint

置換後的視覺方向：

- 深海軍藍背景
- 燙金線條與分隔
- 書頁米色文字
- 明體與古典襯線字體
- 花札角飾、藏書票、黃銅書房感
- 密度高但清楚，不做 SaaS 行銷首頁感
- 功能優先，裝飾服從資訊層級

---

## 1. 產品定位

### 1.1 產品名稱

**SEO Content Studio**

可視覺化副標：

```txt
CHARTA WORKBENCH
SEO Content Studio
```

或：

```txt
CHARTA CONTENT ATELIER
SEO Content Studio
```

### 1.2 使用者角色

主要使用者：

- SEO 寫手
- 內容策略師
- 接案型內容工作者
- 管理多客戶、多站點、多文風指南的人

使用者需求：

- 熟悉 SEO 寫作流程
- 需要處理金融、品牌、在地服務、產品介紹等不同內容類型
- 在意文章語氣、審稿規則、合規風險
- 需要局部修改、逐段確認、保留版本紀錄
- 需要把最終內容貼到 WordPress、Google Docs 或交給客戶 review

### 1.3 產品氣質

此工具應像一張深色皮革書桌上的內容控制台。

關鍵詞：

- 書卷氣
- 編輯室
- 顧問工作台
- 藏書票
- 花札牌面
- 黃銅儀表
- 精密但不冰冷
- 克制、清楚、可控

避免：

- 聊天 App
- 行銷型 SaaS 首頁
- 可愛裝飾
- 亮色 dashboard
- 科技霓虹
- 大量漸層卡片
- stock photo 拼貼
- 過度情緒化文案

---

## 2. Charta 視覺系統置換

### 2.1 色彩系統

請用 Charta 的深底 + 金色 + 米色系統，取代 Studio 原本的泛用工具色。

```css
:root {
  /* Base */
  --navy: #1a2332;
  --navy-deep: #111925;
  --navy-light: #212d3f;
  --navy-mid: #2a3750;
  --navy-soft: #334466;

  /* Charta Gold */
  --gold: #c9a961;
  --gold-dim: #a08448;
  --gold-muted: rgba(201,169,97,0.58);
  --gold-line: rgba(201,169,97,0.25);
  --gold-line-strong: rgba(201,169,97,0.48);
  --gold-glow: rgba(201,169,97,0.12);

  /* Text */
  --cream: #f5f0e6;
  --cream-dim: rgba(245,240,230,0.68);
  --cream-muted: rgba(245,240,230,0.52);
  --cream-faint: rgba(245,240,230,0.35);
  --warm-gray: #8a8070;

  /* Surface */
  --surface-panel: rgba(33,45,63,0.92);
  --surface-panel-soft: rgba(33,45,63,0.68);
  --surface-input: rgba(17,25,37,0.75);
  --surface-hover: rgba(201,169,97,0.08);
  --surface-selected: rgba(201,169,97,0.12);

  /* Semantic status */
  --status-ready: #9bb8d3;
  --status-running: #d8c48a;
  --status-success: #9fbf9b;
  --status-warning: #d6a85f;
  --status-blocker: #d97866;
  --status-stale: #b99ad6;
  --status-info: #9db7c8;
}
```

### 2.2 狀態色使用規則

Charta 風格不能犧牲狀態辨識。

| 狀態 | 色彩 | 顯示方式 |
|---|---|---|
| not_started | cream-faint | 空心細線 badge |
| queued | status-info | clock icon + 文字 |
| running | status-running | spinner + 金色細線 |
| done | status-success | check outline + 已生成 |
| accepted | status-success | check filled + 已採用 |
| soft_stale | status-stale | 紫色細線 badge + Soft stale |
| hard_stale | status-stale | 紫色實線 badge + Hard stale |
| blocked | status-blocker | 紅色實線 badge + Blocked |
| archived | warm-gray | Archived |

規則：

- 狀態不可只用顏色表示，必須有文字。
- blocker 使用紅色，但避免大面積紅底。
- stale 必須顯示 `soft_stale` 或 `hard_stale`，不可只寫 stale。
- success / warning / blocker 色彩要低飽和，融入深色書房調。

---

## 3. 字體系統

請使用 Charta 的襯線字體語彙，取代工具預設 sans-serif。

| 用途 | 字體 | 大小 | 備註 |
|---|---|---:|---|
| App Logo | Cormorant Garamond 300/400 | 20–24px | 大寫，letter-spacing: 4–6px |
| 英文小標 | Cormorant Garamond 400 | 10–12px | uppercase，letter-spacing: 3–5px |
| Screen Title | Noto Serif TC 500 | 20–26px | 中文主標 |
| Section Title | Noto Serif TC 500 | 16–20px | 工作區標題 |
| 內文預覽 | Noto Serif TC 400 | 15–16px | line-height: 1.75–2.1 |
| UI Label | Noto Serif TC 400 | 12–13px | 表單、欄位 |
| Metadata | Cormorant Garamond + Noto Serif TC | 11–12px | compact layout |
| Table | Noto Serif TC 400 | 12–13px | row 高度需控制 |
| Code / Hash | ui-monospace | 11–12px | hash、artifact id、path |

禁止：

- Arial
- Roboto
- Inter
- 圓體
- 大量黑體
- 全站只用 sans-serif

補充：

- 表格與密集 metadata 可少量使用 monospace。
- Markdown preview 的正文維持 Noto Serif TC，讓文章區有「編輯室手稿」感。
- 操作按鈕仍可用 Noto Serif TC，不要做成厚重科技按鈕。

---

## 4. 全域佈局架構

### 4.1 三欄式工作台

保留 Studio 的三欄式桌面工作台，但套用 Charta 牌面語彙。

```txt
┌──────────────────────────────────────────────────────────────┐
│ Top Bar：CHARTA / Site / Project / Guide / API / Budget       │
├──────────────┬────────────────────────────────┬──────────────┤
│ Left Nav     │ Main Workspace                 │ Right Panel  │
│ 流程階段      │ 表單 / Preview / Diff / Table   │ Metadata     │
│ 專案清單      │                                │ 狀態 / 版本   │
└──────────────┴────────────────────────────────┴──────────────┘
```

建議尺寸：

| 區域 | 桌面寬度 |
|---|---:|
| Left Nav | 236–272px |
| Main Workspace | flex: 1 |
| Right Panel | 300–360px |
| Top Bar | 60–68px |
| Content padding | 20–28px |

### 4.2 背景

背景不可純平。

建議：

```css
body {
  background:
    radial-gradient(circle at 50% 0%, rgba(201,169,97,0.08), transparent 36%),
    linear-gradient(180deg, #1a2332 0%, #111925 100%);
  color: var(--cream);
}
```

可加入極淡噪點：

```css
.app::before {
  content: "";
  position: fixed;
  inset: 0;
  pointer-events: none;
  opacity: 0.035;
  background-image: url("noise-texture.svg");
}
```

### 4.3 面板語彙

所有主要工作區面板都像「花札牌面 / 藏書票 / 文件夾」。

| 元件 | 規格 |
|---|---|
| Panel background | `rgba(33,45,63,0.86)` |
| Border | `1px solid var(--gold-line)` |
| Border radius | 0–3px |
| Shadow | 最多一層，極淡 |
| Header | 英文小標 + 中文主標 |
| Divider | 金色菱形分隔線 |
| Corner ornament | 重要區塊可用，透明度 10–18% |

禁止：

- 16px 以上圓角
- 泡泡卡片
- 厚重陰影
- 霓虹發光
- 彩色漸層卡
- 裝飾蓋過資訊

---

## 5. 裝飾語彙：花札工作台化

### 5.1 角飾

用於：

- Main Workspace 的主要 panel
- H2 生成 preview 區
- Review report header
- Export Gate 結果 panel
- Empty state

規格：

- 最大 48×48px
- 金色線條
- opacity 0.1–0.18
- 四角成對出現
- 不可放在表格密集區遮擋文字

### 5.2 分隔線

Charta divider：

```txt
───── ◇ ─────
```

使用位置：

- Screen header 下方
- Modal 內容分隔
- Right Panel metadata group
- Export Gate 檢查組別

規格：

- 線寬 60–160px
- 中央菱形 gold
- 左右線為 gold-line 漸淡

### 5.3 Badge 與 Tag

Badge 像小型藏書票標籤。

```txt
[ BLOCKED ]
[ SOFT STALE ]
[ v3 ACCEPTED ]
[ GUIDE v9.7 ]
```

規格：

- border: 1px solid 對應狀態色
- background: 深底透明
- 字距微寬
- 高度 22–26px
- 圓角 0–2px

### 5.4 表格

表格視覺像書目索引。

規格：

- sticky header
- header 底線 gold-line
- row 底線 `rgba(201,169,97,0.12)`
- hover 背景 `surface-hover`
- selected row 背景 `surface-selected`
- 第一欄可用細金線 accent
- 不要大卡片化

---

## 6. Top Bar

### 6.1 結構

```txt
┌──────────────────────────────────────────────────────────────┐
│ CHARTA WORKBENCH │ Site: LoginHeart │ Project: ... │ Guide v9.7 │ API ready │ Budget $3.20/$20 │
└──────────────────────────────────────────────────────────────┘
```

### 6.2 視覺

| 區塊 | 規格 |
|---|---|
| 高度 | 64px |
| 背景 | `rgba(26,35,50,0.92)` + blur |
| 底線 | 1px gold-line |
| Logo | Cormorant Garamond，金色，letter-spacing 5px |
| Context chips | 深底 + 金色細線 |
| API / Budget | badge，必須文字清楚 |

### 6.3 文案

App Name 顯示：

```txt
CHARTA WORKBENCH
```

副標或 tooltip：

```txt
SEO Content Studio
```

API 狀態例：

```txt
API READY
2 / 3 JOBS
BUDGET $3.20 / $20
```

---

## 7. Left Nav

### 7.1 導覽項目

1. 專案總覽
2. 任務設定
3. 關鍵字 / SERP
4. Brief / 來源
5. H2 生成
6. 審稿
7. 局部重跑
8. KT / FAQ
9. 內外連
10. 導出
11. Log / 版本紀錄

### 7.2 視覺

Left Nav 像書房左側的目錄索引。

| 元件 | 規格 |
|---|---|
| 背景 | navy-deep / navy |
| 右邊線 | 1px gold-line |
| Item | 左側 2px 金線 active indicator |
| Active | gold text + gold-glow 背景 |
| Hover | surface-hover |
| Section number | Cormorant Garamond，gold-dim |
| Badge | compact，不藏資訊 |

### 7.3 Item 範例

```txt
05  H2 生成        [RUNNING]
06  審稿           [BLOCKED 3]
07  局部重跑        [READY]
```

---

## 8. Right Panel

### 8.1 用途

Right Panel 顯示 metadata，不承擔主要操作。

可顯示：

- 當前 section metadata
- artifact status
- version
- hash
- stale_level
- prompt family
- guide sections
- token / cost
- dependencies
- updated_at
- created_by / updated_by
- blocker 摘要
- export profile 摘要

### 8.2 視覺

Right Panel 像黃銅索引卡櫃。

| 元件 | 規格 |
|---|---|
| Group title | Cormorant uppercase，gold-dim |
| Value | cream |
| Secondary | cream-faint |
| Hash | monospace，cream-muted |
| Group divider | Charta divider 小版 |
| Warning group | status border + 深底 |

範例：

```txt
SECTION
h2-2
欠卡債查不到聯徵代表債務消失了嗎？

ARTIFACT
status: accepted
version: v3
stale_level: soft_stale
hash: 9f31a0c7

GUIDE
v9.7
sections: A / C / G
```

---

## 9. 共用元件規格

### 9.1 Button

#### Primary / Solid

用途：主要行動，如 Generate Selected、Accept Version、Export。

```css
.button--solid {
  background: var(--gold);
  color: var(--navy-deep);
  border: 1px solid var(--gold);
  border-radius: 2px;
  letter-spacing: 0.08em;
}
```

hover：

- opacity 0.9
- 不加強烈陰影

#### Ghost

用途：次要行動，如 View Prompt、Compare Versions。

```css
.button--ghost {
  background: transparent;
  color: var(--gold);
  border: 1px solid var(--gold-line-strong);
}
```

hover：

- background: gold-glow
- border-color: gold

#### Danger

用途：忽略 blocker、清除、刪除。

```css
.button--danger {
  background: transparent;
  color: var(--status-blocker);
  border: 1px solid rgba(217,120,102,0.5);
}
```

### 9.2 Input / Textarea / Select

視覺像深色墨水欄位。

| 狀態 | 規格 |
|---|---|
| default | navy-deep 背景 + gold-line |
| focus | gold-line-strong + 細金色外框 |
| invalid | blocker 色邊框 + 錯誤文字 |
| disabled | opacity 0.45 |

Label：

- 英文 label 可用 Cormorant uppercase
- 中文 label 用 Noto Serif TC
- 必填用小金色菱形，不用大紅星號

### 9.3 Modal

Modal 像一張置中的花札牌面。

| 元件 | 規格 |
|---|---|
| 背景遮罩 | rgba(8,12,18,0.68) |
| Panel | navy-light + gold-line |
| 角飾 | 可用 |
| Header | 英文小標 + 中文標 |
| Footer | 右側操作按鈕 |
| 高風險 modal | 額外左側 blocker 色細線 |

### 9.4 Toast

Toast 不要浮誇。

範例：

```txt
已建立 h2-3 v4，不覆蓋 accepted.md。
```

```txt
Export blocked：2 個 blocker 未處理。
```

---

## 10. Diff View Charta 化

### 10.1 基本要求

Diff 是核心畫面，不可為了美感降低可讀性。

支援：

- side-by-side diff
- inline diff
- word-level diff
- markdown preview after diff
- accept / reject / rerun

### 10.2 視覺

| Diff 類型 | 顯示 |
|---|---|
| Added | 左側 gold-green 細線 + `Added` 文字 |
| Removed | 左側 blocker 細線 + `Removed` 文字 |
| Changed | 左側 gold 線 + `Changed` 文字 |
| Source changed | source marker badge |
| Keyword removed | 高風險 badge |
| Heading changed | 高風險 badge |

不要只靠紅綠色。

### 10.3 高風險 Diff 警示

以下行為需在 diff header 顯示警示：

- 主關鍵字被移除
- H2 標題被改
- 來源標記被移除
- 數字被改
- compliance disclaimer 被刪除
- CTA 被刪除
- FAQ 問題被合併或刪除

警示文案：

```txt
此 diff 包含高風險變更：H2 標題已被修改。
接受後會建立 h2-2 v4，不覆蓋目前 accepted.md。
```

---

## 11. Screen 1：專案總覽

### 11.1 目的

讓使用者快速看到所有站點、文章專案、進度、阻擋狀態與最近操作。

### 11.2 Charta 版面

```txt
┌──────────────────────────────────────────────────────────────┐
│ CHARTA WORKBENCH                                             │
├──────────────┬───────────────────────────────────────────────┤
│ Site Ledger  │ PROJECT INDEX                                 │
│ LoginHeart   │ ───── ◇ ─────                                 │
│ 金融客戶      │ [新文章] [匯入文風指南] [匯入舊專案]             │
│ 順周堂        │                                               │
│              │ 最近專案表格                                   │
└──────────────┴───────────────────────────────────────────────┘
```

### 11.3 視覺

- 左側 Site List 像書脊索引。
- Project Dashboard 像藏書目錄。
- 專案不要做成大卡片堆疊，優先用列表 / 表格。
- 表格 row hover 為金色極淡底。
- blocked 專案左側有 blocker 細線。

### 11.4 欄位

| 欄位 | 顯示 |
|---|---|
| Project Title | cream |
| Site | gold-dim badge |
| Primary Keyword | cream-dim |
| Stage | badge |
| Review Status | clean / blocked / stale_level |
| Guide Version | v9.7 badge |
| Last Updated | Cormorant date |
| Cost | compact |
| Export Status | 未導出 / 已導出 |

---

## 12. Screen 2：Site Config / 文風指南

### 12.1 目的

管理多站點設定，避免不同客戶的文風指南、合規規則、內連資料庫互相混用。

### 12.2 Charta 版面

```txt
┌──────────────────────────────────────────────────────────────┐
│ SITE CONFIG REGISTRY                                         │
│ 站點與文風指南                                                │
│ ───── ◇ ─────                                                │
├──────────────────────────────┬───────────────────────────────┤
│ Site Config Registry Table   │ Guide Section Preview          │
└──────────────────────────────┴───────────────────────────────┘
```

### 12.3 視覺

- Site Config Registry 像書目總表。
- Guide Section Preview 像翻開的規則卡。
- `Required` 使用金色菱形。
- `Forbidden` 使用 blocker 細線，不用大紅底。
- prompt fingerprint 用 monospace。

### 12.4 操作

- 匯入文風指南 MD
- 切換 guide version
- 預覽 section
- 啟用 / 停用 custom section
- 查看 action_section_map
- 查看 prompt fingerprint

---

## 13. Screen 3：建立任務

### 13.1 目的

讓使用者用表單建立 B 格式任務，並明確定義文章目標。

### 13.2 Charta 版面

```txt
┌──────────────────────────────────────────────────────────────┐
│ NEW ARTICLE TASK                                             │
│ 建立文章任務                                                  │
│ ───── ◇ ─────                                                │
├──────────────────────────────┬───────────────────────────────┤
│ Task Form                    │ Outline Editor                 │
└──────────────────────────────┴───────────────────────────────┘
```

### 13.3 表單視覺

- Label 使用英文小標 + 中文欄位名。
- Input 像深色墨水格。
- Select 右側箭頭用細金線。
- 必填欄位用小金菱形。
- 欄位群組用小 divider。

### 13.4 Outline Editor

Outline Editor 像目錄編排器。

每個 section item：

```txt
◇ h2-1  欠卡債查不到聯徵代表債務消失了嗎？
   h3-1  可能原因
   h3-2  還款責任
```

支援：

- 新增 H2
- 新增 H3
- 拖曳排序
- 標記 body section / special section
- 顯示 section_id
- 禁止重複 section_id
- `key_takeaways` 與 `faq` 顯示在 special section 區，不混入普通 H2 清單

---

## 14. Screen 4：關鍵字 / SERP / Brief / 來源

### 14.1 目的

承接 SEO 策略層，讓內容生成前有清楚的搜尋意圖、來源與缺口。

### 14.2 Tabs

Tabs 採用藏書籤形式。

1. Keyword Map
2. SERP Analysis
3. Brief
4. Sources
5. Missing Info

### 14.3 Keyword Map

表格像研究筆記索引。

| Selected | Keyword | Intent | Intent Reason | SERP Validated | PAA | Priority |
|---|---|---|---|---|---|---|

視覺：

- Selected 用金色 checkbox。
- Priority 用小型 badge。
- SERP Validated 需文字 + icon。

### 14.4 SERP Analysis

競品頁面列表不要用大卡片，用「頁面索引表」。

顯示：

- 前 5 / 前 10 競品頁面
- 頁面類型
- H2 / H3 結構
- 共同架構
- 差異化機會
- 可採用建議

### 14.5 Brief

Markdown editor + preview。

- Editor 背景 navy-deep
- Preview 像書頁手稿
- H2 / H3 層級要清楚
- `[待補]` / `[待確認]` 用 gold-line badge

### 14.6 Sources

來源表格：

| Use | Title | URL | Source Type | Trust Score | Used For | Competitor | Reason |
|---|---|---|---|---|---|---|---|

來源風險：

- trust_score < 5：blocker 色細線
- competitor：Blocked badge
- lack official source：金融站點顯示 blocker

---

## 15. Screen 5：H2 分段生成

### 15.1 目的

逐段生成 body sections，讓使用者即時預覽與控制每段內容。

### 15.2 Charta 版面

```txt
┌──────────────────────────────────────────────────────────────┐
│ BODY SECTION GENERATOR                                       │
│ H2 分段生成                                                   │
│ ───── ◇ ─────                                                │
├──────────────┬──────────────────────────────┬───────────────┤
│ Section List │ Manuscript Preview           │ Metadata      │
│ h2-1         │ ## H2 Title                  │ status        │
│ h2-2         │ generated content...         │ tokens        │
│ h2-3         │                              │ guide         │
└──────────────┴──────────────────────────────┴───────────────┘
```

### 15.3 Section List

Section List 像左側書籤。

每個 item 顯示：

- section_id
- title
- status
- version
- stale_level
- token cost
- accepted marker
- review issue count

範例：

```txt
◇ h2-2
欠卡債查不到聯徵代表債務消失了嗎？
[ACCEPTED v3] [SOFT STALE] [1 Blocker]
```

### 15.4 Manuscript Preview

Preview 像深色稿紙。

支援：

- H2 / H3 標題
- Key sentence highlight
- source marker
- `[待補]` / `[待確認]`
- link placeholder
- issue highlight
- diff overlay optional

H2 標題：

- Noto Serif TC 500
- cream
- 下方 gold-line 細線

Issue highlight：

- 文字底色淡，不蓋過閱讀
- 左側顯示 severity 細線

### 15.5 操作列

主要按鈕：

- Generate All Body H2
- Generate Selected
- Stop Current Job
- Accept Version
- Archive Version
- Compare Versions
- Rebuild Summary
- View Prompt
- View API Log

按鈕層級：

- Generate Selected：solid
- Accept Version：solid
- Stop Current Job：danger ghost
- View Prompt / Log：ghost

### 15.6 Queue 顯示

右側 metadata：

```txt
QUEUE
h2-2 running
h2-3 queued
h2-4 queued

GLOBAL RATE LIMIT
2 / 3 active jobs

BUDGET
$3.20 / $20 today
```

---

## 16. Screen 6：Review / Blocker 檢查

### 16.1 目的

顯示審稿結果、blocker、warning、suggestion，並讓使用者逐條處理。

### 16.2 Charta 版面

```txt
┌──────────────────────────────────────────────────────────────┐
│ REVIEW REPORT                                                │
│ 審稿與 Blocker 檢查                                           │
│ ───── ◇ ─────                                                │
├──────────────────────────────┬───────────────────────────────┤
│ Issue Ledger                 │ Content Highlight              │
└──────────────────────────────┴───────────────────────────────┘
```

### 16.3 Review Header

像一張審稿封面卡。

顯示：

- review_status
- stale_level
- review_scope
- created_at
- based_on_artifacts
- issue count by severity
- export gate status

文案：

```txt
Review blocked：3 個 blocker 需要處理。
```

```txt
Review report soft_stale：內容已被修改，這份審稿結果只能參考，不能通過導出 gate。
```

### 16.4 Issue Table

欄位：

| Severity | Section | Location | Category | Message | Action |
|---|---|---|---|---|---|

視覺：

- blocker row 左側紅色細線
- warning row 左側琥珀色細線
- suggestion row 左側金色淡線
- info row 左側藍灰細線
- Action 按鈕保持 compact

### 16.5 Action 顯示規則

「套用精確修正」只有在以下條件全部成立才顯示：

- issue 有 `matched_text`
- issue 有 `matched_text_hash`
- issue 有 `replacement_text`
- matched_text 可唯一定位，或 char range 驗證成功

其他情況顯示 disabled，tooltip：

```txt
此建議不是可直接替換文字，請使用 AI Patch 或局部重跑。
```

### 16.6 轉入 FAQ 候選

只允許以下 category：

- missing_explanation
- reader_question_unanswered
- unclear_condition
- missing_edge_case
- process_gap

不允許：

- ai_tone
- grammar
- formatting
- compliance_risk
- source_missing

---

## 17. Screen 7：局部重跑 / Diff

### 17.1 目的

讓使用者選擇特定 H2 或 special section，搭配指定 guide sections 局部重跑，並用 diff 預覽結果。

### 17.2 Charta 版面

```txt
┌──────────────────────────────────────────────────────────────┐
│ REFINE SECTION                                               │
│ 局部重跑與 Diff                                               │
│ ───── ◇ ─────                                                │
├──────────────┬──────────────────────────────┬───────────────┤
│ Section Pick │ Diff View                    │ Settings      │
└──────────────┴──────────────────────────────┴───────────────┘
```

### 17.3 Section Picker

顯示：

- body H2
- key_takeaways
- faq
- selected issues from review

每個 item 顯示：

- current accepted version
- stale_level
- issue count
- last refined at

### 17.4 Guide Section Selector

從 action_section_map 載入預設 sections。

顯示：

| Section | Required | Optional | Forbidden | Tags |
|---|---|---|---|---|

規則：

- Required 不可取消
- Forbidden 不可選
- Optional 可勾選
- Forbidden row 使用 blocker 細線

### 17.5 Diff View

Diff header 需顯示：

```txt
h2-2 v3 → v4
Guide sections: A / C / G
High-risk changes: 1
```

Diff 內容以兩欄或 inline 顯示。

接受文案：

```txt
接受後會建立 h2-2 v4，不覆蓋目前 accepted.md。
```

---

## 18. Screen 8：Key Takeaways / FAQ

### 18.1 目的

處理 special sections，不把 KT / FAQ 混成普通 H2。

### 18.2 Charta 版面

```txt
┌──────────────────────────────────────────────────────────────┐
│ SPECIAL SECTIONS                                             │
│ Key Takeaways / FAQ                                          │
│ ───── ◇ ─────                                                │
├──────────────────────────────┬───────────────────────────────┤
│ Key Takeaways                │ FAQ Candidate Ledger           │
└──────────────────────────────┴───────────────────────────────┘
```

### 18.3 Key Takeaways

狀態：

| 狀態 | UI |
|---|---|
| placeholder | Draft placeholder badge |
| final | Final badge |
| archived | Archived |
| soft_stale | Soft stale |
| hard_stale | Hard stale |

KT placeholder 文案：

```txt
這是根據 Brief / Outline 產生的暫存版 Key Takeaways。
正式版需在 Body H2 完成後重新生成。
```

KT final 生成後：

- placeholder 自動 archive
- 若 placeholder 有人工修改，作為參考輸入
- UI 顯示「已參考人工 placeholder」

### 18.4 FAQ

FAQ candidate table：

| Use | Question | Source | Confidence | Category | Reason |
|---|---|---|---|---|---|

FAQ 來源 badge：

- PAA
- Brief
- Manual
- Review gap
- AI suggested

低信心提示：

```txt
目前 FAQ 候選信心偏低，建議手動新增問題或回到 Brief 補充常見疑問。
```

---

## 19. Screen 9：內外連

### 19.1 目的

顯示外部連結與內部連結建議，使用者確認後再套入文章。

### 19.2 Charta 版面

```txt
┌──────────────────────────────────────────────────────────────┐
│ LINK CURATION                                                │
│ 內外連確認                                                    │
│ ───── ◇ ─────                                                │
├──────────────────────────────┬───────────────────────────────┤
│ External Sources             │ Internal Link Suggestions      │
└──────────────────────────────┴───────────────────────────────┘
```

### 19.3 外部連結

表格欄位：

| Use | Anchor | URL | Clean URL | Source Type | Trust Score | Position | Reason |
|---|---|---|---|---|---|---|---|

狀態：

- clean_url ready
- competitor blocked
- duplicate url
- low trust score
- missing official source

視覺：

- Clean URL 以 monospace 顯示
- competitor blocked 使用 blocker badge
- trust score 用數字 + 文字，不只用色彩

### 19.4 內部連結

表格欄位：

| Use | Anchor | Target Page | Weight | Relation | Position | Reason |
|---|---|---|---|---|---|---|

權重 breakdown：

- semantic
- intent
- pillar_cluster
- anchor_naturalness
- priority

操作：

- 跑內連 exe
- 匯入內連報告
- 套用選取
- 查看 bridge log
- 重新比對

---

## 20. Screen 10：導出

### 20.1 目的

依照 site export profile 輸出 final content。

### 20.2 Charta 版面

```txt
┌──────────────────────────────────────────────────────────────┐
│ EXPORT GATE                                                  │
│ 導出檢查                                                      │
│ ───── ◇ ─────                                                │
├──────────────────────────────┬───────────────────────────────┤
│ Gate Checklist               │ Output Preview                 │
└──────────────────────────────┴───────────────────────────────┘
```

### 20.3 Export Gate

導出前必須檢查：

| Gate | 條件 |
|---|---|
| Review Gate | review_status 不可 blocked，stale_level 必須為 null |
| Source Gate | 不可有未處理 `[待確認]` |
| Link Gate | 競品連結不可套入 |
| Artifact Gate | complete_draft / final_content 必須存在 |
| Profile Gate | export_profile 必須存在 |

Gate UI：

```txt
Export blocked
- 2 個 blocker 未處理
- Review report soft_stale
- FAQ 尚未 accepted
```

視覺：

- Gate Checklist 像黃銅儀表板
- passed 用細金色 check
- blocked 用紅色細線與文字
- 不使用大面積成功綠

### 20.4 Export Profile

顯示目前 profile：

- profile_id
- output_format
- heading policy
- link style
- CTA block
- image placeholder
- WordPress mode
- Google Docs mode

### 20.5 Output

可輸出：

- Copy HTML
- Copy Markdown
- Download .html
- Download .md
- Export manifest
- Google Docs draft placeholder

輸出產物名稱：

| Artifact | 用途 |
|---|---|
| merged_body.md | 只含 body H2 |
| complete_draft.md | KT + body + FAQ |
| final_content.md | 套用內外連與最後格式 |
| exports/{profile_id}/final.html | profile 導出 HTML |
| exports/{profile_id}/final.md | profile 導出 Markdown |

禁止再使用未限定的 `final.md`。

---

## 21. Screen 11：Log / 版本紀錄

### 21.1 目的

讓使用者追蹤每一次 AI call、prompt、版本、diff、導出與錯誤。

### 21.2 Charta 版面

```txt
┌──────────────────────────────────────────────────────────────┐
│ ARCHIVE LOG                                                  │
│ Log / 版本紀錄                                                │
│ ───── ◇ ─────                                                │
├──────────────────────────────────────────────────────────────┤
│ Tabs: Versions / API Calls / Prompt Fingerprints / ...        │
└──────────────────────────────────────────────────────────────┘
```

### 21.3 Tabs

1. Versions
2. API Calls
3. Prompt Fingerprints
4. Patch Logs
5. Review Reports
6. Export History
7. Error / Retry
8. Queue / Budget

### 21.4 視覺

- Log 像檔案櫃索引。
- hash / fingerprint 用 monospace。
- 每筆紀錄 row 高度 compact。
- error 不做整排大紅底，以左側 blocker 細線處理。
- Prompt Fingerprint 可用「藏書票」樣式 badge。

---

## 22. 全域互動規則

### 22.1 人工確認

下列行為必須由使用者確認：

- 接受 H2 版本
- 套用 AI patch
- 接受 KT final
- 接受 FAQ final
- 套用外部連結
- 套用內部連結
- 忽略 blocker
- 導出 final content
- 重建大量 stale artifact
- eager rebuild summaries

### 22.2 高風險操作影響清單

例如：

- 改 primary_keyword
- 改 guide_version
- 改 outline
- 改 site_id
- 改 export_profile
- 重建 h2-2 之後所有 summary

Modal 文案：

```txt
這項變更會影響：
- brief.md：hard_stale
- h2-1 ~ h2-6：hard_stale
- review_report.json：soft_stale
- final_content.md：hard_stale

請選擇：
[標記並繼續] [取消] [只改 metadata]
```

### 22.3 Queue 與 Budget

使用者可以同時開多個專案，但 API job 要顯示：

- global queue
- per-site queue
- active jobs
- retrying jobs
- daily budget
- monthly budget
- hard cap reached

Budget cap reached UI：

```txt
API budget cap reached
目前只能查看、編輯、導出已完成內容。
新的 AI 生成任務已暫停。
```

---

## 23. 空狀態與錯誤狀態

### 23.1 空狀態

空狀態可使用 Charta 角飾，但文字要具體。

```txt
尚未建立任何 H2 section。
請先到「建立任務」新增文章架構，或從 Brief 匯入 H2/H3。
```

```txt
目前沒有 FAQ 候選問題。
可以從 PAA、審稿缺口或手動新增問題建立 FAQ。
```

### 23.2 錯誤狀態

錯誤訊息要包含：

- 發生位置
- 原因
- 使用者可做的下一步
- 是否已有半成品
- retry 狀態

範例：

```txt
H2-3 生成失敗：Claude API overloaded。
系統已保留 tmp_partial，不會覆蓋現有版本。
你可以稍後重試，或先處理其他 section。
```

---

## 24. 文案規則

### 24.1 文案語氣

文案要：

- 清楚
- 直接
- 具體
- 工具感
- 少情緒化
- 少抽象鼓勵
- 明確告知影響

### 24.2 避免文案

避免：

- 「別擔心」
- 「我們幫你搞定一切」
- 「AI 會自動完成」
- 「一鍵生成完美文章」
- 「這樣就夠了」
- 「智能魔法」
- 「讓創作更簡單」
- 「不用思考」
- 「完美解決」
- 「交給 AI」

### 24.3 推薦文案格式

```txt
目前 3 個 section 已過期，原因：Brief 已修改。
```

```txt
此 review report 基於舊版 h2-2，不能用於導出 gate。
```

```txt
這項修正會建立 h2-3 的 v4 版本，不會覆蓋 accepted.md。
```

---

## 25. Accessibility / 可用性

### 25.1 基本要求

- 所有狀態不能只靠顏色辨識
- 表格可鍵盤操作
- 主要按鈕有明確 focus 狀態
- modal 可用 Esc 關閉，但高風險操作需二次確認
- diff 必須有文字標記，例如 `Added` / `Removed`
- badge 要有文字，不只 icon
- long table 要支援 sticky header
- markdown preview 和 editor 要可調寬度
- 金色線條需有足夠對比
- cream 文字不可低到難讀
- 對小字 metadata 給足行高

### 25.2 桌面優先

目標解析度：

- 1440 × 900
- 1920 × 1080
- 2560 × 1440

手機版不是 MVP。  
窄螢幕可顯示簡化版，但不能犧牲桌面資訊密度。

---

## 26. 給 Claude Design 的生成要求

請根據本指南生成前端 UI/UX 設計時，遵守以下規則：

1. 先產出完整資訊架構與主要畫面 wireframe。
2. 再產出 Design System，包括 colors、typography、spacing、badge、table、button、modal、toast、diff view。
3. 再產出 11 個主要 screen 的高保真 mockup。
4. 所有 mockup 都使用繁體中文 UI 文案。
5. 整體風格以 Charta 為準：深底、金線、明體、花札角飾、藏書票、黃銅書房感。
6. 不要實作後端功能。
7. 不要真的呼叫 API。
8. 可使用 mock data。
9. 所有狀態都要在 UI 上看得見。
10. 審稿、stale、blocker、diff、export gate 是設計重點，不可省略。
11. 不要把畫面做成聊天介面。
12. 不要把專業工作流簡化成單一輸入框。
13. 不要把 KT / FAQ 當成普通 H2。
14. 不要使用未限定的 `final.md`。
15. 不要使用未限定的 `stale`。
16. light mode 可省略；若提供 light mode，需維持米色書頁底 + 深色文字 + 金色強調。
17. dark mode 為主設計。

---

## 27. Mock Data 範例

### Project

```json
{
  "project_id": "credit-card-debt-2026-05-06",
  "site_id": "finance_client",
  "title": "欠卡債聯徵無資料怎麼辦",
  "primary_keyword": "欠卡債聯徵無資料",
  "guide_version": "v9.7",
  "stage": "review",
  "review_status": "blocked",
  "stale_level": null,
  "export_profile_id": "wordpress_finance_html"
}
```

### Section

```json
{
  "section_id": "h2-2",
  "title": "欠卡債查不到聯徵代表債務消失了嗎？",
  "artifact_type": "body_section",
  "status": "accepted",
  "version": 3,
  "stale_level": "soft_stale",
  "issue_count": {
    "blocker": 1,
    "warning": 2,
    "suggestion": 1
  }
}
```

### Review Issue

```json
{
  "issue_id": "issue_023",
  "severity": "blocker",
  "category": "source_missing",
  "section_id": "h2-2",
  "message": "此段提到債權轉讓流程，但沒有來源。",
  "matched_text": "債權可能已被轉讓給資產管理公司",
  "replacement_text": null,
  "actions": ["ai_patch", "refine_section", "view_source"]
}
```

### FAQ Candidate

```json
{
  "candidate_id": "faq_cand_004",
  "question": "欠卡債查不到聯徵，還需要還嗎？",
  "source": "review_gap",
  "confidence": 0.82,
  "category": "reader_question_unanswered",
  "reason": "審稿發現正文沒有直接回答讀者最可能追問的還款責任問題。"
}
```

---

## 28. 最終交付物要求

Claude Design 請輸出：

1. UI/UX 設計總覽
2. 全域資訊架構圖
3. Charta 版 Design System
4. 主要元件清單
5. 11 個 screen 的 wireframe
6. 11 個 screen 的高保真設計描述
7. 狀態與 badge 規格
8. Review / Refine / Diff 互動規格
9. Export Gate 互動規格
10. Mock data 使用說明
11. 不實作項目清單
12. 花札角飾 SVG 元件
13. 代表性 table / diff / gate 的高密度狀態樣式

---

## 29. 禁止事項

請不要生成：

- 後端程式
- API client
- 真的 Claude API 呼叫
- 資料庫設計
- Tauri / Python sidecar 實作
- 登入系統
- 付款系統
- 手機優先設計
- Chatbot UI
- 過度行銷頁
- 自動發布 WordPress 的功能
- 自動忽略 blocker 的功能
- 沒有 diff 的局部重跑
- 沒有 gate 的導出畫面
- 沒有 stale 狀態顯示的版本畫面
- 亮色 SaaS dashboard
- 大量圓角泡泡卡片
- 霓虹科技感
- stock photo 或人物插圖
- 過度遊戲化的花札裝飾

---

## 30. 設計優先順序

最高優先：

1. H2 分段生成工作台
2. Review blocker 表格
3. Refine + Diff
4. Export Gate
5. Site / Guide Context 顯示
6. Stale / Version 狀態
7. Queue / Budget 顯示

中優先：

1. Keyword / SERP / Brief 畫面
2. Sources / Missing Info
3. KT / FAQ
4. 內外連確認
5. Log / Prompt Fingerprint

低優先：

1. Light mode
2. 動畫
3. onboarding
4. 多角色權限 UI
5. performance tracking dashboard

---

## 31. 一句話產品定義

SEO Content Studio 是 Charta 的內容工作台：以站點、文風指南、H2 分段、審稿、局部重跑、版本與導出 gate 為核心，讓專業 SEO 寫手精確控制 AI 參與 SEO 文章生產的每一個階段。
