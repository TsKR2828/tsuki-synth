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

---

## 2026-10-02 升格批次（WF1002-D）——讀 §2～§11 前先看這段

> 依據：月月 2026-10-02 裁決「照 Fable 的說法做」，以 `docs/workcards/WF1002_README.md` §1 裁定表為唯一依據。
> - **Q19＝C（逐條）**：C1～C4、C7、C8 甲（升格）；C6 甲（因 Q17=A）；C9 甲（因 Q09 含 B）；**C5 等 Q16 研究卡，本批不升格**（§11）。
> - 同批寫進主張域的還有：**Q08=C**（現在先做 B：收窄，§9）、**Q09=D（含 B）＋Q09c=B**（§10）、**Q17=A**（§6）。
>
> 體例：「」內是出處原文（省略原文的粗體與換行，`…` 表示中間省略）；**只照原出處升格，不新增主張**。
> 候選編號 C1～C9 對應 `docs/KNOWN_LIMITS_INDEX.zh-TW.md` §C；裁決包是 `reports/decision_packets/WF0925_open_decisions.zh-TW.md`。
> 行號一律是 HEAD `b41298c`。`ROADMAP_PHYSICS.md` §0 驗證域表（:140-:148）在 WF1002 同輪沒有位移。
> 同輪 C++ lane（WF1002-C1）會改 `src/physics/BeamModel.h` 註解（Q17）等檔，那些檔的行號之後可能位移，以原文字串為準。

---

## 2. FM Piano——域外（不是物理合成）〔C1〕

**月月 2026-10-02 裁決（Q19 C1 甲：升格）**：

> 「FM Piano｜❌ 域外｜已誠實標註「非物理合成」，維持此標註」

出處：`ROADMAP_PHYSICS.md` §0 驗證域表（:144；該列 git 最早見於 2026-07-09 `7c150d1`，沒有單獨的裁決包）。
`TODO.md`「Deliberately outside the physical claim」（:1021-1023）同一件事的原文：「FM Piano, Custom Harmonics' authored ratios, Body macro and the artistic effect chain may remain useful, but must stay labelled non-physical/half-domain.」

---

## 3. Custom Harmonics——半域內〔C2〕

**月月 2026-10-02 裁決（Q19 C2 甲：升格）**：

> 「Custom Harmonics｜⚠️ 半域內｜加法合成，頻率比可驗但非物理推導」

出處：`ROADMAP_PHYSICS.md` §0 驗證域表（:143；同上，2026-07-09 `7c150d1`）；`TODO.md` :1023（同 §2 引的那句）。

---

## 4. Cimbalom／Piano 的振幅含 creative 層與校準層〔C3〕

**月月 2026-10-02 裁決（Q19 C3 甲：升格）**。三段原文：

> 「振幅含已文件化 creative 層（`spectralTilt`，見 `CimbalomEngine.h` 註解），頻率／衰減不受影響；月月 2026-07-23 裁決保留並劃界。」
> ——`ROADMAP_PHYSICS.md` §0 驗證域表 Cimbalom / Piano 列（:140）

> 「spectralTilt heuristic 層去留——2026-07-23 裁決：降級保留，聲音不動，劃界為已文件化 creative 層（不算入物理主張）」
> ——`TODO.md`（:921）

> 「noteOn 攻擊能量正規化（`ModalResonator::loudnessCompensationGain`，amount=0.78 月月審聽定案，已文件化校準層、比照 spectralTilt 劃界）」
> ——`TODO.md`「2026-08-06（夜）跨音域響度失衡修正」（:902-904）；前後對照 `reports/loudness_keytrack_before_after.md`

裁決日期：`spectralTilt` 2026-07-23 月月；`loudnessCompensationGain` 2026-08-06 月月。

---

## 5. `frequency_mode: midi` 是混合系統〔C4〕

**月月 2026-10-02 裁決（Q19 C4 甲：升格）**：

> 「`frequency_mode: midi`｜⚠️ 設計聲明｜混合系統：物理決定頻譜形狀、平均律決定基頻，不得宣稱絕對尺寸音高」

出處：`ROADMAP_PHYSICS.md` §0 驗證域表（:147；該列 git 最早見於 2026-07-23 `e0eb06a`）。

---

## 6. 舌鼓 BeamModel 的 ×2 阻尼——DECIDED CONVENTION（經驗係數，無文獻錨點）〔C6／Q17〕

**月月 2026-10-02 裁決 Q17=A（保留 ×2，改標）＋Q19 C6 甲（升格）**。主張域措辭照 Q17=A 原文：

> **`src/physics/BeamModel.h` 衰減式裡內部摩擦項的 `* 2.0f`，是「DECIDED CONVENTION，經驗係數，無文獻錨點」。**

支撐原文：
- 程式碼原註解（`src/physics/BeamModel.h:44-48`，引用的是 :46-47）：「寬頻化後內部摩擦在全音域都與文獻對齊，`*2` 因此變成全音域一律 2 倍過阻尼、不再有任何錨點理由的純經驗係數。」
- 文獻補搜（`docs/D1_BEAM_PLATE_DAMPING_SEARCH.zh-TW.md` §0 第 2 點）：「反對把它當物理項——沒有任何一份來源用「材料損耗乘一個固定倍數」來描述梁的額外阻尼」；「無法判斷它的量該不該拿掉」；「結論是「文獻不能替 `*2` 的去留提供錨點」」。

範圍與後續：
- 只影響用到 BeamModel 的事件（舌鼓等）；頻率不受 ×2 影響（裁決包 Q17 背景：拿掉 ×2「頻率完全不變」）。
- 保留 ×2 是 10-02 的慣例決定，不是物理推導。拿掉 ×2 的前後數字（描述用、非 GATE）在 `reports/beam_x2_option_b_before_after_2026-09-25.zh-TW.md`，沒有被採用。
- `BeamModel.h` 註解改標同一句由 WF1002-C1 做（純註解，8/8 位元不變），以該卡證據為準。
- 相關但**沒有升格**的缺口：`beam_plate_beta_air`／`beam_plate_gamma_radiation` 未溯源、阻尼項在頻率趨近 0 時全變 0、衰減不看舌片厚度（`docs/KNOWN_LIMITS_INDEX.zh-TW.md` B1；D1 §0 第 3、4 點）。

---

## 7. Chromatic（舌鼓／水鑼）的槌具沒有標定〔C7〕

**月月 2026-10-02 裁決（Q19 C7 甲：升格）**。兩段原文：

> 「只適用 Cimbalom/Piano；Chromatic 在 D2 補搜完成前不得套用。」
> ——`TODO.md` B4 條目（:515；B4 槌氈接觸求解器，2026-08-27 完工）

> 「D2 舌鼓／鑼的槌具接觸參數 … handpan/鋼舌鼓/tam-tam 自身成套接觸數據仍缺，且 Giordano 的 `α=3/2` 是採用而非量測、槌頭為硬木/Plexiglas，缺口未閉合。」
> ——`TODO.md` D2（:833）；補搜進度 `docs/D2_CHROMATIC_CONTACT_SEARCH.zh-TW.md` §8

---

## 8. 絕對聲壓輸出是慣例錨定〔C8〕

**月月 2026-10-02 裁決（Q19 C8 甲：升格）**：

> 「`--dump-modes` 已輸出 `absolute_pressure_per_force` 和 `acoustic_transfer[]`，但這是月月裁決的慣例錨定，不是實測也不是推導。」
> ——`TODO.md` Verification gaps 輻射條目的「09-25 現況」（:988）

裁決記錄：`reports/decision_packets/B6_calibration_choice.md`「裁決記錄（2026-08-28 月月）」（:142-，「照建議走」＝方案 B）。
同一條目接著寫：「拾音位置、相位、指向性仍 `UNVERIFIED`，缺口維持開放。」（:989）。這個值只出現在 `--dump-modes` 診斷輸出。

---

## 9. 物理驗證涵蓋的是 CLI 渲染，不是外掛即時演奏〔Q08〕

**月月 2026-10-02 裁決 Q08=C（現在先做 B：文案與主張域收窄；parity GATE 排進 TODO 當後續 L 卡）**：

> **物理驗證涵蓋 CLI 渲染；外掛即時演奏共用衰減律，激發與效果鏈未逐項驗證。**（裁定表原句，與商品文案一致）

依下方背景數字展開：「激發」在這裡包含激發、振幅、macro、BodyResonance——這幾項在外掛和 CLI 是各自組裝的（見下一點）。
另外 WF1002 研究卡 R-a 查到（`reports/wf1002_preset_overshoot_root_cause.zh-TW.md`）：Body 共鳴層（Body 0.8 在基頻 +15 dB；CLI 預設 0）與壓縮器自動補償（CLI 預設關閉；工廠 preset +2.0～+7.5 dB，超標的 7／11／15 號是 +4.5～+5.0 dB）是 CLI 渲染沒有的；大空間殘響尾巴 CLI 也有（同一個 `SimpleReverb.h`，預設開），但物理驗證一律 FX 全關。

支撐事實（裁決包 Q08「背景數字」，行號已換成 HEAD `b41298c`）：
- 共用的是衰減律：`applyStringDecayTimes()`（`src/engines/CimbalomEngine.h` :156 起）。
- 激發、振幅、macro、BodyResonance、EffectChain 是兩邊各自組裝：外掛走 `startNote()`，CLI 走 `noteOn()`。
- HostProbe 只驗音高、onset 和 tail 長度（H8），不驗模態頻率，也不驗 T60。
- 效果鏈本來就在 §0 域外：「驗證一律 FX 全關；用了效果的 score 不在物理主張範圍」（`ROADMAP_PHYSICS.md` §0 :145）。
- 「Plugin ↔ CLI 一致性驗證」仍是 `ROADMAP_PHYSICS.md` §4 Nice to have 第 1 條（:441），**還沒做**；做了以後（Q08 C 的 A 部分），本節再依結果改寫。

外掛只會發生、CLI 不會發生的 voice 行為見 §10。

---

## 10. 外掛每個引擎 16 顆 voice；搶音與同音規則照 JUCE；GATE 只涵蓋 CLI〔C9／Q09、Q09c〕

**月月 2026-10-02 裁決 Q09=D（含 B）、Q09c=B（同音提前制音不改、寫進主張域）、Q19 C9 甲（升格）**。主張原句（`reports/voice_pool_occupancy_2026-09-25.zh-TW.md` §6 選項 B）：

> 「外掛每個引擎同時最多 16 顆，超過時照 JUCE 規則搶最舊的；同音重疊時照 JUCE 同音規則處理；物理驗證（GATE）只涵蓋 CLI 渲染」

逐點（出處都是同一份 voice_pool 報告；報告行號是 HEAD `18430c4` 的程式碼行號）：
1. **16 顆／引擎**：三個引擎各一個 `juce::Synthesiser`、各 16 顆；Cimbalom 和 Piano 共用 cimbalomSynth 的 16 顆（§1）。
2. **搶音照 JUCE 預設**：沒有呼叫 `setNoteStealingEnabled`，所以會搶；先保護還按著的音裡最低和最高的兩顆，再依序搶「同音高最舊 → 已放鍵最舊 → 沒按著最舊 → 不受保護最舊」，最後才搶受保護的兩顆；被搶的 voice 直接切掉、不收尾（§1）。
3. **同音提前制音（Q09c=B：不改）**：「同一個音高的前一顆還沒放鍵、後一顆就開始時，JUCE 會先把前一顆制音；前一顆放鍵時，又會把後一顆也一起制音。」給愛麗絲（商品）有 21 顆這樣的音；加大 pool 也不會變（§0 第 4 點、§4.4）。
4. **CLI 不一樣**：「CLI 是每個事件自己 new 一顆 voice，沒有 pool、不會搶」（§1），也不會同音提前制音。物理 GATE 驗的是這條路（§9）。
5. **數字（全部是照程式碼規則推算的估計，不是外掛實測）**：
   - 要上架的 50 件商品照正常彈法都不超過 16 顆：給愛麗絲兩版最多 12 顆、AI Radiance 最多 8 顆、音效包最多 4 顆（§0 第 1 點）。
   - 全 corpus 75 首有 3 首超過，都不是商品（月光全曲 FM 196 顆、月光舌鼓版 20 顆、混合版舌鼓部分 20 顆；§0 第 2 點）。
   - 假設整首踩住延音踏板（corpus 沒有踏板資料，只是上限）：商品有 4 件超過——給愛麗絲兩版各 22 顆、AI Radiance 全曲 FM 19 顆、第三樂章 FM 17 顆（§0 第 3 點、§4.2）。
   - 多聲部塞進同一個外掛：四季（外掛沒有 `damping_override`）12 個樂章有 6 個超過、最多 26 顆；一個聲部一個外掛就 0 個超過（§0 第 3 點）。
6. **FM 同音反覆時舊 voice 不結束**（§0 第 4 點）：Q09b=A 決定要修，但依 R10 先在隔離副本做前後對照報告＋patch，**不直接落地**。patch 落地前，現行外掛仍有這個行為。
7. **Q09 D 的實測（WF1002-C1 已做，`reports/gate_outputs/wf1002_C1_hostprobe.txt`）**：外掛 VST3 即時串流整首樂譜，同時用同引擎組出的「雙胞胎」合成器記錄搶音（雙胞胎與外掛輸出整首逐樣本相同）。給愛麗絲鋼琴版：搶 0 次、最多 12 顆，與估計一致；月光第一樂章舌鼓版：搶 64 次（4 次搶到還按著的音）、最多 20 顆、第一次在 17.920 s，與估計一致。唯一對不上的是「被別顆放鍵一起制音」：實測計到 11 顆、報告估 21 顆，兩邊計數定義不同，數字只供參考。所以第 5 點的估計已有兩首實測背書；其餘曲目仍是估計。

---

## 11. 尚未升格：弦長／弦徑模型假設〔C5〕

**本批不升格**：依裁定表 Q19，「C5 等 Q16 研究卡」。Q16=D：`TODO.md` 登記「F5 PASS 依賴探針 0.8 mm」為已知脆弱點，另開研究卡（真鋼琴 T60 文獻對照候選＋F5 量法可改方向，只研究）。研究卡回來後再裁 C5。
現況出處：`docs/KNOWN_LIMITS_INDEX.zh-TW.md` A24、§C C5；`reports/decision_packets/D11_string_scale_candidate.zh-TW.md` §0 與檔尾 F5 根因補記。
