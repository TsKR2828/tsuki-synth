> 【版控副本】原檔在 exports/products/moonlight_batch1/PRODUCT_SHEET.md（exports/ 不進版控），本副本供追溯。

# 月光奏鳴曲產品線 — 第一批（moonlight_batch1）

> 產製日期：2026-08-28
> 依據：`docs/PRODUCT_MARKET_NOTES.zh-TW.md`（月月情報：產出單位=完整樂曲，不是音效）
> 分支：`fix/deep-physics-audit-20260716`（HEAD=53e6c76，工作樹另有 B5 batch unstaged，與本次渲染無關）
> 渲染器：`build/TsukiSynthCLI_artefacts/Release/TsukiSynthCLI.exe`（renderer_version 0.3.0，Release/MSVC 19.50.35730.0）
> 響度處理：`C:\Users\admin\Desktop\Tools\ffmpeg-8.1.1-full_build\bin\ffmpeg.exe`（8.1.1-full_build）

---

## ⚠️ 上架前必讀：來源授權注意事項（誠實揭露，非「已確認可商用」）

四份 score 的 `meta.description` 皆註明來源 MIDI 為：

> Mutopia Project, **Stewart Holmes edition**, Berners 1908 source, **CC BY-SA 2.5**

- 貝多芬《月光奏鳴曲》Op.27 No.2 原曲**作曲本身**公版無疑。
- 但這四份 score 的**音符序列來自 Mutopia 上一份具名編輯版本的 MIDI 轉譯**，該版本標示 **CC BY-SA 2.5**（姓名標示＋相同方式分享）。
- Share-Alike 條款是否延伸到「用該 MIDI 重新合成演奏音檔」這件事，**屬於需要月月自行判斷或找人確認的法律問題**，本檔不代替下判斷。
- 建議至少在商品頁註明來源版本出處（Stewart Holmes edition, Mutopia Project, CC BY-SA 2.5），若採較保守作法可考慮是否需要以相同授權釋出，或改用其他版權清楚的轉譯來源。
- **改編/合成本身**（音色設計、混音、TsukiSynth 物理引擎演奏）著作權歸 TsKR2828；上述僅涉及「音符序列」這一層來源。

---

## 曲目一覽

| # | 標題（中/英） | 配器 | 時長 | 母帶 | 母帶 SHA256（前16碼） |
|---|---|---|---|---|---|
| 1 | 月光奏鳴曲 完整版 / Moonlight Sonata — Complete | FM Piano（2-op FM 合成器音色，**非物理建模**——repo 內誠實標註域外；三樂章全） | 14:39.10 (879.10s) | 48kHz/24bit | a628a3b6e2891385 |
| 2 | 月光奏鳴曲 第一樂章 揚琴版 / Moonlight Sonata I — Yangqin | Physical Cimbalom/Yangqin（steel弦/wood mallet） | 5:17.49 (317.49s) | 48kHz/24bit | 49514b007e3e01fc |
| 3 | 月光奏鳴曲 第一樂章 空靈鋼舌鼓版 / Moonlight Sonata I — Ethereal Tongue Drum | Physical Steel Tongue Drum ⚠️ **QA 判定未達發行標準，暫緩上架**（見下方「已知缺陷」） | 5:27.29 (327.29s) | 48kHz/24bit | c37ac02d01f08a30 |
| 4 | 月光奏鳴曲 第一樂章 揚琴+空靈鼓 混音版 / Moonlight Sonata I — Yangqin + Ethereal Tongue Drum Mix | Yangqin 主奏 + Tongue Drum 18ms 延遲光暈層 | 5:25.87 (325.87s) | 48kHz/24bit | 7b0413dd4f858079 |

原曲：Ludwig van Beethoven, Piano Sonata No. 14 in C-sharp minor, Op. 27 No. 2「月光奏鳴曲」（公版）。
音符來源：Mutopia Project, Stewart Holmes edition, Berners 1908 source, CC BY-SA 2.5（見上方授權注意事項）。
改編／合成著作權：TsKR2828。

---

## 實測數據（可測量項，無主觀聽感宣稱）

方法：ffmpeg `loudnorm` 兩段式（第一段量測，第二段 `linear=true` 套用量測值），完成後對成品 distribution WAV 做**獨立第二次量測**驗證（非套用時 filter 自報數字）。

| # | 曲目 | 母帶削波樣本數 | 母帶 pre-normalize peak | Distribution 實測 Integrated LUFS | Distribution 實測 True Peak |
|---|---|---|---|---|---|
| 1 | Complete | 0 | 0.9087 (linear, full-scale=1.0) | **-13.89 LUFS** | **-1.00 dBTP** |
| 2 | Yangqin | 0 | 0.6207 | **-14.03 LUFS** | **-1.00 dBTP** |
| 3 | Tongue Drum | 0 | 0.1622 | **-13.98 LUFS** | **-1.00 dBTP** |
| 4 | Yangqin+Tongue Mix | 0 | 0.3806 | **-14.02 LUFS** | **-1.00 dBTP** |

- 「母帶削波樣本數」取自 CLI 渲染時的 `.render.json`（`samples_at_or_above_full_scale`），四份皆為 0——母帶本身無數位削波。
- 目標為 Integrated -14 LUFS / True Peak ≤ -1.0 dBTP；四份實測均落在 -13.89 ～ -14.03 LUFS 區間（±0.14 LU 內），True Peak 全數精確卡在 -1.00 dBTP，無溢出。
- 渲染為**決定性**（deterministic）：每份母帶的 `.render.json` 內含 `wav_sha256`／`root_score_sha256`／`renderer_executable_sha256`／`random_seed` 等完整可追溯鏈，同一份 score + 同一顆 exe 可重現位元相同結果。
- 以上僅為量測項目；**未進行、也未宣稱任何人耳審聽驗收**——美學/音樂性判斷留給月月或外部專業人士另行把關。

---

## 檔案清單

### 母帶（masters/，48kHz/24bit WAV，含 `.render.json` 溯源清單）

```
masters/moonlight_sonata_complete.wav                      (241.5 MB, 879.10s)
masters/moonlight_sonata_complete.wav.render.json
masters/moonlight_sonata_i_yangqin.wav                     (87.2 MB, 317.49s)
masters/moonlight_sonata_i_yangqin.wav.render.json
masters/moonlight_sonata_i_tongue_drum.wav                 (89.9 MB, 327.29s)
masters/moonlight_sonata_i_tongue_drum.wav.render.json
masters/moonlight_sonata_i_yangqin_tongue_mix.wav          (89.5 MB, 325.87s)
masters/moonlight_sonata_i_yangqin_tongue_mix.wav.render.json
```

### 發行版（distribution/，44.1kHz/16bit WAV，loudnorm -14 LUFS / -1.0 dBTP）

```
distribution/moonlight_sonata_complete_distribution_44k16bit.wav
distribution/moonlight_sonata_i_yangqin_distribution_44k16bit.wav
distribution/moonlight_sonata_i_tongue_drum_distribution_44k16bit.wav
distribution/moonlight_sonata_i_yangqin_tongue_mix_distribution_44k16bit.wav
```
（每份旁附 `_loudnorm_pass1.json` 量測值、`_loudnorm_verify.json` 獨立複測值，供稽核。）

### 試聽版（preview/，320kbps MP3，由 distribution WAV 轉出）

```
preview/moonlight_sonata_complete_preview.mp3               (14:39.10)
preview/moonlight_sonata_i_yangqin_preview.mp3               (5:17.49)
preview/moonlight_sonata_i_tongue_drum_preview.mp3           (5:27.29)
preview/moonlight_sonata_i_yangqin_tongue_mix_preview.mp3    (5:25.87)
```

完整 SHA256 見各檔案本身（`sha256sum` 可重算核對），主要摘要值已列於上方曲目表。

---

## 英文商品描述草稿（給音效網站上架用）

> **Moonlight Sonata Reimagined — Physically-Modeled Hammered Dulcimer & Steel Tongue Drum**
>
> Beethoven's *Moonlight Sonata* (Piano Sonata No. 14, Op. 27 No. 2 — public-domain composition) in four renditions: a complete three-movement FM-synthesis piano performance, plus alternate-instrumentation arrangements of the first movement built on a from-scratch **physical modeling** engine — voices you won't find anywhere else in stock music libraries:
>
> - **Complete Sonata — FM Piano**: all three movements in a dreamlike 2-operator FM piano voice (FM synthesis, not physical modeling — stated honestly).
> - **Hammered Dulcimer / Yangqin** (physical model): steel-string, wood-mallet simulation with per-register string gauge and damping — not a sample library, a simulated instrument.
> - **Hybrid Mix** (physical model lead): hammered dulcimer as the lead voice with a softly delayed (18ms) tongue-drum halo layer for shimmer and depth.
>
> All tracks are mastered to broadcast-standard loudness (-14 LUFS integrated, -1.0 dBTP true peak, verified by independent re-measurement) with zero clipping at the source render. Delivered as 48kHz/24-bit masters plus ready-to-use 44.1kHz/16-bit distribution WAVs and 320kbps MP3 previews.
>
> Perfect for: classical crossover content, meditative/ambient game and video backgrounds, documentary scoring, and anywhere a familiar melody needs an unfamiliar voice.
>
> *Note: melody source is a specific public-MIDI transcription (Mutopia Project, Stewart Holmes edition) licensed CC BY-SA 2.5 — attribution details available on request.*

（草稿用途：投稿音效網站的商品說明起點，實際上架文案需依各平台格式與字數限制調整，且務必核實上一段授權注意事項後再決定是否保留/移除 CC BY-SA 出處揭露。）

---

## 已知缺陷（2026-08-28 Opus QA 發現，量測值非聽感判斷）

1. **曲目 3（空靈鼓獨奏版）未達發行標準，建議暫緩上架**：tongue_drum 引擎在相同
   velocity 下有 **40.3 dB 的音高-響度斜率**（MIDI 37 → 87：−32.8 → −73.1 dBFS
   RMS；揚琴同域僅 4.4 dB），本曲 54.2% 音符在 MIDI≥60 → 主旋律音域比低音弱
   20–40 dB；成品 97.4% 能量在 200 Hz 以下、2 kHz 以上能量為 0。且該引擎輸出
   接近純正弦（99.9% 能量在基頻，無泛音列）——真實鋼舌鼓應有豐富非諧泛音。
   已登記工程項 **TODO D8**（引擎級調查，非本批產線能解）。
2. **曲目 4（混音版）不受影響**：其中的 tongue_drum 依設計只作低頻光暈層
   （延遲 18ms、平均 velocity 0.127 vs 主奏 0.247），主旋律由揚琴承擔。
3. **溯源鏈註記**：`.render.json` 記錄的 `renderer_executable_sha256`
   （dc58ab5c…）是渲染當下的 CLI；其後 B6 工程重建過 CLI（現為 fa154956…）。
   **音訊不受影響**——QA 已用新 exe 重渲揚琴版，SHA256 與母帶逐位元相同
   （49514b00…），可重現性比溯源欄位字面更強。
4. **peak 欄位讀法**：上表「pre-normalize peak」是正規化**前**的峰值；
   實際交付母帶經 normalize 後四份峰值皆為 0.95（−0.45 dBFS）。

## 上架前注意事項（需月月確認，各平台規格可能不同）

1. **CC BY-SA 授權疑慮**（見最上方）——這是本批次最需要月月拍板的一項，會影響能否單純以「公版改編」名義上架、要不要揭露來源版本、要不要走相同授權釋出。
   **2026-08-28 月月裁決：換乾淨公開來源——本批四首在換源重製前不上架，僅作內部 demo/引擎對照用。**
2. **各平台採樣規格差異**：本批交付 44.1kHz/16bit + 320kbps MP3，但部分音效平台（如 AudioJungle、Pond5、Epidemic Sound 等）對交付格式/取樣率/最大檔案大小/是否要求 WAV-only 有各自規定，需依實際投稿平台核對。
3. **各平台響度規範差異**：-14 LUFS / -1.0 dBTP 是本次採用的通用發行基準，但部分平台（尤其影片配樂類）可能有自己的建議值（如 -16 LUFS 或 -23 LUFS broadcast），上架前需核對目標平台文件。
4. **關鍵字/分類標籤**：四份曲目的 `meta.tags`／`category` 已含 `yangqin`／`tongue_drum`／`cimbalom` 等稀缺配器關鍵字，上架時建議沿用以凸顏市場稀缺性（依 `PRODUCT_MARKET_NOTES` 情報：真實物理揚琴/空靈鼓是市場稀缺音色）。
5. **檔名/metadata 是否需要英文化或平台專屬命名規則**，需依平台要求另行調整（本批交付檔名以清楚辨識為原則，未做平台客製）。
6. **本產線未執行任何人耳審聽驗收**——美學/音樂性最終把關請月月安排外部專業人士（依鐵律要求，本檔不宣稱任何主觀品質已過關）。

---

## 產製紀錄（可稽核）

- 渲染指令：`TsukiSynthCLI.exe <score.json> --output exports/products/moonlight_batch1/masters`（無 diagnostic 覆蓋旗標，走預設驗證合約路徑）。
- 未執行任何 cmake build，未修改 `src/` 或 `scores/` 任何檔案（符合任務鐵律）。
- 響度腳本：`exports/products/moonlight_batch1/loudnorm_process.sh`（兩段式 loudnorm，pass2 用 pass1 量測值 + `linear=true`，並對輸出做獨立複測）。
- 全部四份母帶 `samples_at_or_above_full_scale = 0`（渲染時已內建 normalize，peak 見上表，均 < 1.0 無削波）。
