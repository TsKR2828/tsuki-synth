# B1+B2 合併 Rule 10 前後對照報告：琴橋導納 + 阻尼寬頻化

> 產出：2026-08-21（施工卡 `docs/workcards/B2.md` §9）
> 範圍：2026-08-10 阻尼寬頻化 + 2026-08-16 B1 琴橋導納 + 2026-08-21 B2 錨點重測，三者合併的單一聽感改變。
> 授權：月月 2026-08-20 全權委託（TODO.md C3-b 委託記錄）。

---

## §0 白話導讀卡

**一句話結論：低音無限拖長的問題修好了，而且整體音量和音色平衡幾乎沒動。**

之前的狀況：我們把「弦的能量怎麼消失」從一個湊出來的數字換成真正的物理公式（寬頻化），
結果暴露一個洞——公式裡三個損耗管道在低音端全部趨近於零，低音 C2 的殘響變成
128 秒（等於敲一下響兩分鐘，物理上荒謬）。B1 補上了第四個管道：**弦的能量會經過
琴橋流進共鳴板**（這是真實樂器最主要的能量出口，之前完全沒建模）。這個管道不隨
頻率消失，所以低音端被自然封頂——C2 從 128 秒收斂到 17.7 秒。

本報告用數字證明三件事：(1) 發散確實消失了；(2) 全部 73 首驗證曲目零失敗；
(3) 整曲的響度與音色平衡變化極小（六首代表曲實測 RMS 差最多 0.6 dB）。

**你要做的裁決**：接受這批改變（聽感上低音尾巴會明顯變短、更接近真實揚琴），
或指名回退。所有檔案未 commit，你保有完整否決權。

---

## §1 T60 對照表（steel cimbalom 基頻，模型值）

| 音 | f (Hz) | 2026-08-06 舊模型 | 2026-08-10 寬頻化（B1 前）* | B1+B2 疊加後 | 新/舊比值 |
|---|---|---|---|---|---|
| C2 | 65.4 | 39.03 s | **128.75 s（發散）** | **17.66 s** | 0.452 |
| C3 | 130.8 | 35.12 s | 60.39 s | 8.75 s | 0.249 |
| C4 | 261.6 | 26.85 s | 26.86 s | 4.30 s | 0.160 |
| C5 | 523.3 | 14.90 s | 11.00 s | 2.08 s | 0.139 |
| C6 | 1046.5 | 5.68 s | 4.04 s | 0.97 s | 0.171 |
| C7 | 2093.0 | 1.69 s | 1.32 s | 0.43 s | 0.255 |
| C8 | 4186.0 | 0.45 s | 0.39 s | 0.18 s | 0.388 |

\* 中間欄照施工卡指示直接抄 `reports/damping_broadband_findings.md` §3.1，未重新渲染。
舊模型欄與 B1+B2 欄由 `af849ec` worktree 舊 CLI 與現工作樹新 CLI 各自 `--dump-modes`
（中央弦）量得；舊欄與 findings §3.1 的「T60 舊」欄一致（39.03 vs 39.05，量測擾動 <0.1%）。

**解讀**：
- 寬頻化的低音發散（C2 128.75 s）被 B1 的頻率無關損耗率完全封頂 → **B2 的核心前提成立**。
- 全音域 T60 縮短是琴橋耦合的物理結果：損耗率 ∝ T/L，高音短弦經橋漏能更快，
  與真實鋼琴/揚琴高音衰減快的實情方向一致。
- C4 錨點交叉檢查：模型 4.30 s vs `BRIDGE_ADMITTANCE_SOURCES.md` §3 事前獨立算的
  並聯預測 4.18 s，差 3%。
- 已知侷限（非本卡缺陷）：單一平均 G 對個別音的預測（如 C3）與 Wogram 實測仍可能有
  差距——量級核對而非逐音精確驗證，見 `BRIDGE_ADMITTANCE_SOURCES.md` §3/§4。

## §2 corpus 影響對照（休止 RMS，限 −50.0 dBFS）

| 檔案 | 2026-08-10 寬頻化（B1 前） | B1+B2 疊加後 |
|---|---|---|
| `vivaldi_four_seasons_summer_m2` | **FAIL**：3/3 休止段超標，最差 −46.8 dBFS（短少 3.2 dB） | **PASS**：3/3 低於限值，最差 −52.2 dBFS（餘裕 2.2 dB） |
| `vivaldi_four_seasons_summer_m3` | PASS（round-3 後餘裕 ~2.5 dB） | **PASS**：1/1 低於限值，−56.8 dBFS（餘裕 6.8 dB） |

寬頻化那輪唯一的 FAIL（`summer_m2`）在 B1 落地後自動回綠，未動任何容差（R2）、
未動兩檔的 score.json、未新增豁免。

## §3 corpus 73 檔四分片總結果

**73/73 PASS、零 FAIL、豁免僅既有 moonlight 1 筆**（19+18+18+18；
`b2_corpus_{A,B,C,D}.txt`）。分片數以 `verify_score.py` 自印的
`Selected shard N/4` 為準。

## §4 六首代表曲整曲對照（舊=af849ec CLI、新=工作樹 CLI，各自完整渲染）

| 曲目 | RMS 舊 (dBFS) | RMS 新 | ΔRMS (dB) | 質心舊 (Hz) | 質心新 | Δ質心 |
|---|---|---|---|---|---|---|
| vivaldi_summer_m2 | −20.69 | −21.15 | −0.46 | 488 | 484 | −4 |
| vivaldi_summer_m3 | −16.90 | −16.68 | +0.22 | 441 | 441 | +0 |
| moonlight_yangqin | −23.97 | −23.89 | +0.08 | 821 | 806 | −15 |
| akashic_opening_bell | −21.60 | −21.00 | +0.59 | 380 | 365 | −15 |
| ai_radiance_m1 | −22.56 | −22.32 | +0.24 | 2164 | 2112 | −52 |
| vivaldi_autumn_m2 | −25.99 | −26.38 | −0.38 | 445 | 452 | +8 |

T60 結構性大改（C4 縮到 1/6）之下整曲 RMS 全部落在 ±0.6 dB、質心偏移 ≤2.4%——
因為激發端響度錨點同步重測（§5），校準鏈守住整體平衡。聽感的主要差異集中在
**音尾長度**，不在音量或亮度。

## §5 響度錨點常數變更（量測，非文獻/推導；Rule 4 標註在各檔頭）

| 常數 | 舊值 | 新值 | 說明 |
|---|---|---|---|
| `kCimbalomAttackEnergyRefA4` | 0.1497 | **0.0874** | B1 縮短 A4 的 T60 → 攻擊窗能量下降（歷史：0.1609→0.1497→0.0874） |
| `kChromaticAttackEnergyRefA4[0]`（TongueDrum） | 0.009504 | 0.009504（不變） | B1 刻意不接 Chromatic，反解 noteComp=0.999997 |
| `kChromaticAttackEnergyRefA4[1]`（WaterGong） | 0.07770 | 0.07770（不變） | 同上，noteComp=0.999996 |

量測方法＝**中央弦反解法**（velocity=0.5 使 τc_actual=τcRef 相消；預設 3 弦 course
中央弦 freqMul=1，dump 的 freq/decay 與引擎 attackE 用的 baseModes 位元一致；
定點迭代解出補償前攻擊能量）。兩個 Chromatic 常數到第 6 位不變是方法的內建自我驗證
——B1 只接 Cimbalom/Piano，它們本來就不該變。逐步數字與一次性腳本：
`reports/gate_outputs/b2_attack_energy_remeasure.txt`。
`amount=0.78` 未動（月月欽點）。

## §6 BeamModel `*2` 現況重申

`reports/damping_broadband_findings.md` §5 指出的 BeamModel `*2` 經驗加權
「寬頻化後失去錨點理由」問題，**本卡未處理、已登記**——B1 的橋耦合推導只針對
行波弦（`BRIDGE_ADMITTANCE_SOURCES.md` §5 明寫 Beam/Plate 本輪不推），
Chromatic 引擎目前是「寬頻化＋舊 `*2` 加權、無橋耦合」的狀態。其去留是另一張卡的
裁決項（相關文獻缺口＝TODO D1）。**本報告不代表全部已知問題都解決。**

## §7 決定性（determinism）聲明

**所有含 Cimbalom/Piano 事件的既有 score，渲染 WAV 的 SHA256 都會改變——這是預期
行為（T60 與響度錨點變了），不是回歸。** 渲染本身仍是決定性的：corpus 檢查含
determinism 雙渲染比對，73/73 全過。純 Chromatic/FM 的檔案理論上位元不變
（bridgeLoss 不進入其路徑、其錨點常數未變）。

## 附：§8 GATE 清單完成狀態（全部以新常數重跑後的最終版）

| GATE | 結果 | 證據 |
|---|---|---|
| `--t60 --notes 60 72` | ALL WITHIN TOLERANCE（ratio 1.00–1.06） | `b2_t60_baseline.txt` |
| `--full` | NO CHECKED FAILURES（3 rubber UNVERIFIED 為既有） | `b2_gate_full_final.txt` |
| CLI/Standalone/VST3 build | 三者 exit 0 | `b2_build_{cli,standalone,vst3}.txt` |
| ctest（三 target 先全重建，X4 規約） | 3/3 Passed | `b2_ctest_final.txt` |
| pytest | 121 passed | `b2_pytest_final.txt` |
| corpus 四分片 | 73/73 PASS、僅既有 1 豁免 | `b2_corpus_{A,B,C,D}.txt` |

施工卡 §7 的錨點回歸哨兵測試**未實作，理由**：它要求在測試裡重算引擎的攻擊能量，
但 `CimbalomEngine::startNote` 的模態準備鏈（spectralTilt、macro、tune、橋損耗 decay
重算）是引擎內聯程式碼，測試端重算必然是第二份會靜默漂移的複本——複本漂移正是
X1 這類回歸的根源。替代機制：`b2_attack_energy_remeasure.txt` 保存了可隨時重跑的
一次性反解腳本與量測 score，且 Chromatic 雙 null result 提供交叉驗證。
