# 引擎主張域清單（Engine Domain Claims）

> 建立：2026-09-15（WF0914-D13，月月裁決選項 B）
> 用途：集中記錄「每個引擎物理模型**模擬的是什麼、不是什麼**」的正式主張域聲明。
> 體例比照 `docs/EARFREE_MELODY_GATE_DESIGN.zh-TW.md` §8.5 的主張域總結——
> 收窄主張是誠實工程的一部分，不是缺陷清單。新增聲明時附裁決記錄與分析文件出處。

---

## 1. `water_gong`（自由邊平板模型）——不是乳突鑼

**月月 2026-09-15 裁決（D13 選項 B：維持自由邊平板，主張域收窄）**：

> 「`water_gong` 引擎模擬的是完全自由邊的平板（無 boss、無鑼緣），這是「不加額外構造特徵
> 的圓板」的物理模型；它**不是**乳突鑼（泰國鑼、爪哇鑼等常見的 boss+盤面構造）的模型。
> 2.0× 基頻附近沒有模態是這個域限制的直接結果，不是計算錯誤，見
> `docs/GONG_PARTIAL_ANALYSIS.zh-TW.md`。」

支撐數字（出處：`GONG_PARTIAL_ANALYSIS.zh-TW.md` §1.3、`reports/gate_outputs/wf0914_D13_plate_ratios.txt`）：
- 現行 bronze（ν=0.34）自由邊平板模態比值序列 1 : 1.738 : 2.329 : 3.925 : …，
  2.0× 夾在第 2 根（低 242.66 音分）與第 3 根（高 263.39 音分）之間，**結構性無模態落在 2.0×**。
- 真實泰國鑼（乳突鑼）最強泛音在 2.000×，McLachlan (1997) 證實這是 **boss 幾何造成的模態調諧**
  （矽青銅鑄造鑼實測 + FEA：boss 厚度加倍可把比值調進八度關係）。
- 解除此域限制的路（裁決包選項 A）需要可溯源的乳突鑼模態表；
  關鍵原始文獻 Rossing & Shepherd (1982) 全文未取得（見裁決包
  `reports/decision_packets/D13_gong_2x_partial.zh-TW.md` §2 選項 A 前提）。

**同步記錄（2026-09-25 更新）**：`src/physics/PlateModel.h` 檔頭註解與
`scores/examples/water_gong_free.score.json` 的 `meta.description` 已於 **WF0925-K1** 帶上這段聲明：
PlateModel.h 檔頭加了「主張域」段（自由邊平板、不是乳突鑼，引本檔 §1 與 bronze ν=0.34 比值
1 : 1.738 : 2.329 : 3.925）；water_gong_free 的 description 拿掉「hung gong 的物理上合適邊界」的說法，
改寫成「不是乳突鑼」的聲明並換成同一組比值（出處 `reports/gate_outputs/wf0914_D13_plate_ratios.txt`）。
純註解／描述，不影響渲染：8 首代表曲位元不變 8/8 IDENTICAL（water_gong_free 在這 8 首內，
`reports/gate_outputs/wf0925_K1_bit_identity.txt`、`wf0925_K1K2fix_bit_identity.txt`）；render manifest 的
`root_score_sha256` 會變（預期）。改動目前 staged、未 commit，可用
`git diff --cached -- src/physics/PlateModel.h scores/examples/water_gong_free.score.json` 查看。
原備忘（2026-09-15）：「尚未帶上這段聲明——留待下一張本來就要動這兩個檔案的卡順路同步」。
