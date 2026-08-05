# Scene→Reverb 自動化設計地圖（方案1 對照表 + 方案2 Sabine/Eyring）

> 起草：2026-08-05（Fable 分析規劃；Sonnet 實作；Opus 驗證）
> 狀態：設計已定，實作中。所有改動為**新增檔案**，不碰 `src/`、不碰既有 tools、不 commit（月月審後決定）。

## 0. 定位與誠實邊界

- 產出目標：由「場景描述」推出 `global.effects.reverb.{decay, wet}`。
- `reverb.decay` 在 renderer 端經 `SimpleReverb::setDecayTime()` 直接作為 **authored T60（秒）**
  （見 `src/score/ScoreRenderer.h` effectTailSeconds 註解），故本工具的輸出語意就是 T60，
  與 corpus 的 T60 量測鏈同語意，無需引擎改動。
- 誠實分層（沿用 ROADMAP_PHYSICS.md §0 的域表精神）：
  - **方案2（Sabine/Eyring）＝物理推導層**：每個數字有公式與可引用依據，report 印出全部中間量。
  - **方案1（場景標籤預設）＝documented creative 層**：不是物理主張，是有文件的美術預設
    （同 spectralTilt 的劃界處理，round-4 裁決 (3) 的先例）。
  - 本工具**不進** §6 容差表、不改任何 GATE；它是 score 產製的上游輔助。

## 1. 交付物（全部新檔）

| 檔案 | 內容 |
|---|---|
| `tools/scene_reverb.py` | 核心模組 + CLI（stdlib only，不新增依賴） |
| `tests/test_scene_reverb.py` | pytest 合約測試（見 §6） |
| `docs/SCENE_REVERB_DESIGN.zh-TW.md` | 本檔（設計即文件） |

## 2. 輸入格式（scene JSON，fail-closed 驗證）

未知鍵一律報錯（沿用 `ScoreParser` validateKeys 文化），二選一：

```jsonc
// 方案1：標籤模式
{ "preset": "cave" }

// 方案2a：物理模式（逐面材質）
{
  "space": {
    "dimensions_m": [10.0, 8.0, 3.0],        // 長寬高 shoebox
    "surfaces": [
      { "material": "concrete", "area_m2": 188.0 },
      { "material": "carpet_heavy", "area_m2": 80.0 }
    ],
    "listener_distance_m": 3.0               // 可選，預設 3.0（用於 wet）
  }
}

// 方案2b：物理模式（全表面單一材質）——與 "surfaces" 互斥，恰好給其中一個
{
  "space": { "dimensions_m": [10.0, 8.0, 3.0], "material": "concrete" }
}
```

規則：
- `preset` 與 `space` 互斥，二者皆無或皆有 → 錯誤退出（exit≠0），不猜。
- `space` 內 `surfaces` 與 `material` 互斥，恰好提供一項，否則錯誤退出（不做「同給時忽略其一」）。
- `surfaces` 面積總和必須 = shoebox 總表面積 ±1%（否則 fail-closed；不默默補殘差）。
- 未知材質名 → 錯誤退出並列出合法材質表；**絕不默認一個 α**。

## 3. 方案2 數學（每步都要在 report 印出）

- 體積 `V = L·W·H`；總表面 `S = 2(LW + LH + WH)`。
- 平均吸音 `ᾱ = Σ(Sᵢ·αᵢ) / S`。
- **Sabine**：`T60 = 0.161·V / Σ(Sᵢ·αᵢ)`；適用 ᾱ ≤ 0.2。
- **Eyring**：`T60 = 0.161·V / (−S·ln(1−ᾱ))`；當 `ᾱ > 0.2` 時**自動改用**（Sabine 在高吸音下系統性高估），
  report 兩者皆印、標明採用哪個與理由。切換是判定制規則，非可調旋鈕。
- **wet（直達/殘響能量比推導）**：房間常數 `R = S·ᾱ/(1−ᾱ)`，臨界距離 `r_c = √(Q·R/(16π))`（Q=1），
  `wet_raw = r² / (r² + r_c²)`（r = listener_distance_m）。
  應用值 `wet = min(wet_raw, wet_max)`，`--wet-max` 預設 **0.6**（documented creative 上限，
  因物理 wet 在硬房間常逼近 1.0，音樂上不可用；report 必須同時印 raw 與應用值）。
- 夾限：decay clamp 到 schema 範圍 [0, 30]、wet [0, 1]（超界要在 report 標警告）。

### 3.1 材質 α 表（mid-frequency 500 Hz–1 kHz 平均，實作時逐條附引用註解）

以 Kuttruff《Room Acoustics》、Everest《Master Handbook of Acoustics》公表值為準，
落在下列錨點 ±0.02 內（Opus 驗證時逐條覆核合理範圍）。**引用基礎依材質類別而異
（實作 `tools/scene_reverb.py` 逐條附註）**：室內建材（`concrete`/`brick`/`glass`/
`plaster`/`wood_panel`/`wood_floor`/`carpet_heavy`/`curtain_heavy`/`acoustic_tile`/
`audience_seated`）取自上述兩書的室內吸音表列；戶外/地面材質
（`rock_rough`/`grass_ground`/`water_surface`/`snow_fresh`）中，僅 `snow_fresh`
在 Everest 書中有可引用的戶外表面列（"snow, fresh fallen, 4 in"），其餘三項該兩書
未表列，屬戶外聲傳播/地面阻抗文獻推估值，不掛兩書引用（誠實分層，見 §0）：

| 材質鍵 | α (mid) | | 材質鍵 | α (mid) |
|---|---|---|---|---|
| `concrete` | 0.02 | | `carpet_heavy` | 0.63 |
| `brick` | 0.03 | | `curtain_heavy` | 0.635 |
| `glass` | 0.04 | | `acoustic_tile` | 0.70 |
| `plaster` | 0.05 | | `audience_seated` | 0.80 |
| `wood_panel` | 0.10 | | `grass_ground` | 0.55 |
| `wood_floor` | 0.07 | | `water_surface` | 0.01 |
| `rock_rough` | 0.04 | | `snow_fresh` | 0.925 |

（`carpet_heavy` 取「carpet, heavy, on 40 oz hairfelt or foam rubber」列：500 Hz
0.57／1 kHz 0.69，中頻均值 0.63；`curtain_heavy` 取「draperies, heavy velour,
draped to half area」列：500 Hz 0.55／1 kHz 0.72，中頻均值 0.635；`snow_fresh`
取「snow, fresh fallen, 4 in」列：500 Hz 0.90／1 kHz 0.95，中頻均值 0.925。
2026-08-05 Opus 驗證發現舊表三值與所引列不符，已依實測公表值訂正，
見 fix/deep-physics-audit 系列同名修正紀錄。）

### 3.2 已知值測試錨（先手算，測試必須對到）

- 10×8×3 m 全 concrete：V=240、S=268、Σ(Sα)=5.36、ᾱ=0.02 → **Sabine T60 = 7.209 s**（±0.01）。
- 同房全 acoustic_tile：ᾱ=0.70 → 走 Eyring，`−S·ln(0.3)=322.65` → **T60 = 0.1198 s**（±0.001）；
  Sabine 值 0.206 s 僅列 report 對照。
- concrete 房 r=3.0：R=5.469、r_c=0.330 m → wet_raw=0.9881 → 應用 wet=0.6（觸 wet-max，report 標示）。

## 4. 方案1 預設表（documented creative 層，非物理主張）

| preset | decay (T60 s) | wet | | preset | decay | wet |
|---|---|---|---|---|---|---|
| `outdoor_open` | 0.10 | 0.05 | | `hall_large` | 1.8 | 0.30 |
| `forest` | 0.30 | 0.10 | | `cathedral` | 4.5 | 0.35 |
| `room_small` | 0.40 | 0.15 | | `cave` | 6.0 | 0.40 |
| `room_medium` | 0.60 | 0.20 | | `bathroom` | 1.0 | 0.30 |
| `corridor` | 1.2 | 0.25 | | `underwater` | 0.25 | 0.50 |

表為起始美術值，月月可改；表本身要在 `--list-presets` 可列印。

## 5. CLI 合約

```
python tools/scene_reverb.py --scene scene.json                  # 印 JSON 片段 + 人讀 report 到 stderr
python tools/scene_reverb.py --scene scene.json --report         # 完整推導 report（stdout, markdown）
python tools/scene_reverb.py --list-presets
python tools/scene_reverb.py --list-materials
python tools/scene_reverb.py --scene s.json --apply in.score.json --output out.score.json
```

- `--apply` **必須**搭配 `--output`，且 output 不得等於 input 路徑（不覆寫原檔文化，
  memory feedback_no_overwrite_originals）；無 `--in-place` 選項，就是不提供。
- `--apply` 只改 `global.effects.reverb.{decay,wet}` 兩個值，其餘 JSON 內容與鍵序不動
  （讀入→改值→照原結構寫回；縮排用 2 空格與 scores/ 現行一致）。
- 輸出決定性：無時間戳、無隨機、同輸入位元相同 stdout。
- 數值格式：decay/wet 輸出至多 4 位小數，避免浮點雜訊入 score。

## 6. 測試合約（pytest，全部 fail-closed 邊界都要有反例）

1. §3.2 三個已知值錨（Sabine、Eyring 切換、wet 觸頂）。
2. ᾱ=0.2 邊界：≤0.2 用 Sabine、>0.2 用 Eyring（兩側各一例）。
3. 未知材質 → 非零退出 + 訊息含合法清單。
4. `preset` 與 `space` 同給 / 皆缺 / 未知鍵 → 非零退出。
5. surfaces 面積和偏離 shoebox 表面積 >1% → 非零退出。
6. clamp：構造 T60>30 的場景（大體積硬房）→ 輸出 30 並帶警告。
7. `--apply`：output==input 路徑 → 拒絕；round-trip 後除 reverb 兩鍵外其餘內容 deep-equal。
8. 決定性：同輸入跑兩次 stdout 位元相同。
9. 每個 preset 的 decay∈[0,30]、wet∈[0,1] 全表掃描。
10. 全材質表掃描：α∈(0,1)。

## 7. 驗證分工（Opus）

- 鏡頭A 物理/數學：手工重算 §3.2 錨、逐條覆核 α 表落在公表合理範圍、Eyring/wet 推導式正確性。
- 鏡頭B 合約/文化：fail-closed 全覆蓋、不覆寫原檔、決定性、無 src/ 或既有檔案改動、
  文件誠實（creative vs 物理層劃界清楚）。
- 鏡頭C 測試充分性：實際跑 `pytest tests/test_scene_reverb.py` + 全套既有 pytest 確認零干擾。

## 8. 明確不做（本輪）

- 不改 `SimpleReverb`（pre-delay、頻變 damping、early reflections → 留待 merge 後另一分支）。
- 不做圖像自動判定場景（模糊性與 fail-closed 衝突；如需，做成遊戲側外部工具）。
- 不接 per-frequency α（先 mid-band 單值；schema 留 `material` 字串即可向後擴充）。
