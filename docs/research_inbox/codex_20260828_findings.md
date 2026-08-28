# Codex 補搜回饋（2026-08-28，月月轉交）

> 狀態：**inbox 原文，未經本 repo Opus 稽核**。入庫（寫進正式 SOURCES 文件）前
> 必須逐條稽核；本地 PDF 在 Codex 工作目錄（見文中 citation 路徑）。
> Codex 自述：「只列我在原始 PDF 頁面或表格親眼核過的數字。」

## 1. 槌具／接觸實測
- 中國鑼 xiaoluo（Effects of Internal Resonances in the Pitch Glide of Chinese
  Gongs, 2018, DOI 10.1121/1.5038114）：槌等效質量 ≈3 kg（F/a 動態等效，非秤重；
  50 次槌擊校正，B&K 4374 + PCB 208C02）；校正力域 6–95 N（Fig.6）；
  實擊 8/13/16/32 N（Fig.7）；p.435 Sec.III Figs.4-6。無 K/α/接觸時間。
  開放稿：https://sam.ensam.eu/bitstream/handle/10985/15360/LISPEN_JASA_2018_THOMAS.pdf
- 木魚槌（Mokugyo Function Model, 1999）：接觸時間 線槌 1 ms／矽橡膠 4 ms／
  皮槌 6 ms；力頻寬 3.5k/500/700 Hz；p.42 Fig.1。
- 木魚（JASA 2005, DOI 10.1121/1.1868192）：線包頭槌 23cm/26g、皮包頭 40cm/173g、
  橡膠包頭 55cm/250g（整支質量非槌頭）；接觸脈衝 1–6 ms；峰值力 170 N；
  RION PF-60；p.2250 Sec.II.C Fig.5。
- 板—槌 K/α 標定（Giordano 2005 博士論文，McGill，
  https://www.mcgill.ca/mpcl/files/mpcl/giordano_2005_phdthesis.pdf）：
  F=K·δ^(3/2)（α=3/2，p.140）；半球槌頭 ~1cm 半徑；
  秤重 橡木 1.844g/松木 1.543g/Plexiglas 1.844g（Table 8.5 p.139）；
  回歸動態質量 10.382/10.082/10.382 g（Table 8.6 p.142）；
  鋼板 225/450/900 cm² 的 K（10⁹ N·m^-3/2，Table 8.7 p.146）：
  橡木 0.282/0.496/0.297、松木 0.339/0.541/0.360、Plexiglas 1.352/1.417/1.458；
  K 反算式 p.145 Eq.(8.5)：K=35.4/τ³·√(μ³/F_max)，μ=m_h·m_P/(m_h+m_P)；
  2184 個 K 估計、75% 落在 ±23.43%。
  本地 PDF：C:/Users/admin/Documents/Codex/2026-08-28/codex-repo-doi-d2-sonnet-handpan/work/pdfs/giordano_2005.pdf
- 鼓棒接觸（Motor Control in Drumming, 2008,
  https://dael.euracoustics.org/confs/acoustics2008/data/articles/002529.pdf）：
  接觸 5.12–5.65 ms、峰值力 50.03–89.76 N、Vic Firth 5B 整支 60g；
  銅箔+導電石墨電路直接量 on/off；160 kHz；p.2612-2613 Table 1。
- 鋼舌鼓實驗（Experimental Characterization of the Steel Tongue Drum, 2021,
  https://unige.iris.cineca.it/retrieve/e268c4ce-2f55-a6b7-e053-3a05fe0adea1/full_paper_1117_20210430223100647.pdf）：
  11 音/外徑 250±1mm、軟橡膠槌、麥克風 1m；**無接觸參數**（D2 仍未閉合）。
- 待追：Ingolf Bork, Measuring the Acoustical Properties of Mallets, 1990,
  DOI 10.1016/0003-682X(90)90044-U（未取得全文，Codex 不報數字）。

## 2. 台灣樹種
- 《三種測定木材彈性模數方法之比較》2007，臺灣林業科學 22(3):297-306，
  https://ws.tfri.gov.tw/001/Upload/OldFile/files/07-96-22.pdf ：
  **真正縱向振動 E_L**（E_L=4ρf₁²L²，每種 90 支 35×35×600mm，20°C/65%RH）：
  杉木 ρ=419(36) kg/m³、MC 13.3%(1.16)、E_L=11.25(1.64) GPa；
  柳杉 ρ=508(65)、MC 14.2%(0.63)、E_L=9.84(1.96) GPa。p.299 Table 1、p.300 Eq.(1)。
- 《常見國產木材性質分析…成果報告書》2022，中興大學/林務局新竹處，
  https://hsinchu.forest.gov.tw/file.aspx?fno=82028 （靜態抗彎 MOE，**非 E_L**，
  不得悄悄改名）：臺灣二葉松 519(55)/13.0%/7.9(2.3) GPa（p.19 T1、p.21 T2）；
  臺灣杉 358(42)/12.2%/7.1(1.4)（p.22 T3）；相思樹 901(63)/11.2%/12.6(2.3)
  （p.50 T14）；櫸木/臺灣櫸 847(60)/10.6%/10.9(1.6)（p.50 T14）。
  本地 PDF：C:/Users/admin/Documents/Codex/2026-08-28/codex-repo-doi-d2-sonnet-handpan/work/pdfs/taiwan_wood_report.pdf
- 臺灣紅豆杉 Taxus sumatrana：**仍無**同含密度+MOE+含水率的實測表；
  勿誤中 Styrax sumatrana（安息香科）。

## 3. 正交異向板驅動點導納（B5 §11 (a) 阻擋項的解）
- Vibrational Response Prediction of a Pneumatic Tyre Using an Orthotropic
  Two-Plate Wave Model, 2003, DOI 10.1016/S0022-460X(02)01190-2，p.938 Eq.(28)：
  Y_dp = 1/(8·(ρ²h²·Dxx·Dyy)^(1/4)) = 1/(8·√(ρh)·(Dxx·Dyy)^(1/4))
  即 Y_dp = 1/(8·√(m·D_eff))，m=ρh、D_eff=√(Dxx·Dyy)。
  限制：Kirchhoff 正交異向薄板、點驅動、無限板高頻漸近；純實數不隨頻率；
  非有限板逐模態曲線。
- Vibrational Energy Flow Models of Finite Orthotropic Plates, 2003,
  DOI 10.1155/2003/428705，p.98 Eq.(3) 採 H_c=√(D_xc·D_yc)，同頁明指
  Cremer/Heckl/Ungar 顯示正交異向板驅動點阻抗接近「剛度=幾何平均」的均質板；
  參考文獻 p.110 列 Structure-Borne Sound, Springer, 1973。

## 4. 杵音直接聲學實測（非同儕審查，科展）
- 《搗杵之音》2009，第 49 屆中小學科展，
  https://twsf.ntsec.gov.tw/activity/race-1/49/pdf/030108.pdf ，p.23 Table 23：
  櫸木 248cm/⌀11cm → 531.0–596.0 Hz；櫸木 225cm/⌀13cm → 674.0–675.0 Hz；
  樟木 188cm/⌀8.5cm → 837.0–892.0 Hz；樟木 176cm/⌀8cm → 926.0–992.0 Hz。
  （邵族現場錄音頻譜分析）受控試驗：60cm/⌀6cm 木條、大理石地板、5 kgw
  敲擊力（p.7 Table 5）。
