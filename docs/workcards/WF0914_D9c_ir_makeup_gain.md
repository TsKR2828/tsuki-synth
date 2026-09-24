# 施工卡 WF0914-D9c：IR wet 路徑固定補償增益（月月 2026-09-16 裁決選項 A）

> lane：C++（`build-wf\`）。依據：`reports/decision_packets/D9_ir_loudness_alignment.zh-TW.md`
> §5 選項 A ＋文末裁決記錄。先讀：`WF0914_README.md`、`WF0907_README.md`、該裁決包全文、
> `reports/gate_outputs/wf0914_D9b_ir_injection.txt`、`src/effects/EffectChain.h`（IR/ALGO wet 路徑）、
> `tests/audit_repro.cpp` 的 K-02 兩支量測函式（合成＋外部 IR 變體）。

## 0. 一句話目標

把量出來的結構性落差補平：IR 模式的 wet 路徑加**固定補償增益 ×26.9（+28.58 dB）**，
讓使用者從 ALGO 切到 IR 時響度不再暴跌 ~28.6 dB。

## 1. 實作要求

1. 增益只作用於 **IR（Convolution）模式的 wet 訊號**；ALGO 路徑、dry 訊號、其他效果一概不動。
   施加點選在與 K-02 量測點一致的位置（讓 GATE 4 能直接驗證）。
2. 常數註解必寫：`kIrWetMakeupGain = 26.9f`（+28.58 dB）＝ **DECIDED CONVENTION
   （月月 2026-09-16 裁決 D9 選項 A）**，推導=4 樣本（3 顆 EchoThief 真實 IR＋1 合成 IR）
   wet-vs-ALGO 落差平均 −28.58 dB 的反相補償，出處=裁決包 §3/§5；**非物理常數，
   樣本僅 4 組、涵蓋 3 種空間尺度**（照裁決包的誠實聲明轉寫）。
3. `tests/audit_repro.cpp` K-02 量測輸出若因此改變（預期會：落差應變成 ≈0 dB）：
   量測**方法不動**，只更新輸出敘述/期望，註解引用本裁決；若存在硬 CHECK 斷言舊落差值，
   更新為新約定值並在報告寫明（這是月月裁決的行為變更，不是 R2 調容差）。
4. HostProbe 若有涵蓋 IR wet 響度的情境，確認新行為下仍 PASS；沒有就不新增（本卡從小）。

## 2. GATE（build-wf lane，X4 規約）

1. 三 build target + 五測試 target 重建 exit 0；`ctest` 全綠。
2. **補償驗證（本卡核心）**：重跑 K-02 合成 IR＋`TSUKI_K02_EXTERNAL_IR` 三顆 EchoThief
   （SHA256 先驗）——wet-vs-ALGO 落差四組皆應落在 **0 ± 0.25 dB** 附近
   （0.24 dB 是 D9b 實測的樣本展幅，非新容差；如實記錄四個數字）。
3. `python tools/physics_verify.py --full --cli <build-wf CLI>`：與基線零差異（CLI 不走 IR 路）。
4. **位元不變（本卡碰 `src/`，必跑）**：`render_wf_scores.py --cli <build-wf CLI>` 對
   `sha256_before_post_a14.txt` → **8/8 IDENTICAL**（corpus 不經 IR 路，任何 SHA 變化=BLOCKED 停下）。
5. HostProbe 對 build-wf VST3 全套 0 failures。
6. `git diff` 只含 `src/effects/EffectChain.h`（或實際施加點檔案）＋`tests/audit_repro.cpp`
   ＋證據檔＋`TODO.md` D9 條目一行。

證據 `reports/gate_outputs/wf0914_D9c_*.txt`。
