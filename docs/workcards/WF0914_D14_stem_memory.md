# 施工卡 WF0914-D14：stem_verify 記憶體線性成長修復

> lane：Python（用 `build\` 現成 CLI；**不碰 `src/`**）
> 先讀：`tools/stem_verify.py` 全文、`tests/` 裡 stem_verify 相關測試、
> `reports/gate_outputs/wf0907_C11_*.txt`／`wf0907_C12_*.txt`（現行行為基準）。

## 0. 一句話目標

D14 登記：905 事件全曲跑 stem_verify 記憶體 >28 GB（隨事件數線性成長），現在只能 `--limit 300`。
本卡把峰值記憶體與事件數**解耦**（串流/分批/即時釋放），行為與輸出判定**逐位元不變**。

## 1. 實作要求

- 先診斷：報告寫明線性成長的具體來源（哪個結構在累積什麼，file:line）。
- 修法自選（逐事件處理完即釋放／分批渲染／memmap），但**判定邏輯、容差、輸出 schema 一個都不動**
  （R2/R3；provenance 欄位語意不變）。
- `--limit`、`--jobs`、`--json`、`--analysis-dry` 既有介面全部保留。

## 2. GATE

1. **等價性**：修改前後各跑一次 `--limit 300`（同 score、同參數），輸出 JSON 逐欄比對——
   除 provenance 裡本來就會變的執行期欄位（哪些欄位屬此類，先讀 C12 卡證據確認再列清單）外
   **完全相同**。比對腳本與結果存證據檔。
2. **記憶體證據**：對 905 事件 score 以 `--limit 300`／`600`／全量三檔各跑一次，
   用輪詢方式記峰值 working set（PowerShell `Get-Process` 輪詢或 psutil，方法寫進證據檔）。
   **不設數字門檻（R2 精神）**：如實記三個峰值；達標判準是「全量能跑完 + 峰值不再隨事件數
   線性成長」，數字表本身就是證據。
3. stem_verify 相關 pytest 測試檔全綠（**只跑相關檔，不跑全套**——lane 規約）；
   若既有測試依賴舊行為（例如記憶體中間結構），修測試前先確認那是實作細節而非規格。
4. `git diff` 只含 `tools/stem_verify.py`＋相關測試檔＋證據檔。

證據 `reports/gate_outputs/wf0914_D14_*.txt`；`TODO.md` D14 條目同步。
