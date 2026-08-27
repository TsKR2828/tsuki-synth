# B4 受影響 score 清單（label=after）

> 產出腳本：`reports/gate_outputs/b4_method/scan_affected_scores.py`
> 判定條件：event engine ∈ {string, cimbalom, piano} 且有效 exciter 經
> `cimbalomExciterFromString()` 映為 `ExciterType::Felt`
> （felt / felt_mallet / finger / finger_tap / rubber_mallet；
> piano 引擎先套 renderEvent() 的 wood_mallet→felt 覆寫）。
> Chromatic 引擎（beam/tongue_drum/plate/water_gong/custom）一律不受影響
> （B4 不碰 ChromaticEngine，且其 exciter 走 chromaticExciterHardness()）。
> layers 型 score：任一 source 子譜受影響即受影響。
> track_profiles 只是 metadata（renderer 不套用），掃描以 event 層為準。

Corpus 總數：**73** 首（tools/verify_score.py --all 同一組枚舉）
受影響：**5** 首；不受影響：**68** 首

## 受影響清單

| # | score | Felt 事件數 | engine/exciter 明細 | 經由 layers |
|---|---|---|---|---|
| 1 | `scores/examples/physical_piano.score.json` | 4 | piano/wood_mallet ×4 | — |
| 2 | `scores/originals/ai_radiance/ai_radiance_complete.score.json` | 16 | cimbalom/felt_mallet ×16 | scores/originals/ai_radiance/ai_radiance_m3.score.json |
| 3 | `scores/originals/ai_radiance/ai_radiance_m3.score.json` | 16 | cimbalom/felt_mallet ×16 | — |
| 4 | `scores/library/akashic/akashic_action_001.score.json` | 1 | string/finger ×1 | — |
| 5 | `scores/library/ocean/ocean_action_001.score.json` | 1 | string/rubber_mallet ×1 | — |

## 不受影響清單（B4 後這些曲目渲染必須逐位元不變）

- `scores/examples/akashic_bell.score.json`
- `scores/examples/epiano_3stack_test.score.json`
- `scores/examples/fur_elise_opening.score.json`
- `scores/examples/layered_transition.score.json`
- `scores/examples/moonlight_sonata_complete.score.json`
- `scores/examples/moonlight_sonata_movement1_tongue_drum.score.json`
- `scores/examples/moonlight_sonata_movement1_yangqin.score.json`
- `scores/examples/moonlight_sonata_movement1_yangqin_tongue_mix.score.json`
- `scores/examples/rabbit_warning.score.json`
- `scores/examples/restraint_metal_click.score.json`
- `scores/examples/water_gong_clamped.score.json`
- `scores/examples/water_gong_free.score.json`
- `scores/classical/vivaldi_four_seasons/autumn/vivaldi_four_seasons_autumn_m1.score.json`
- `scores/classical/vivaldi_four_seasons/autumn/vivaldi_four_seasons_autumn_m2.score.json`
- `scores/classical/vivaldi_four_seasons/autumn/vivaldi_four_seasons_autumn_m3.score.json`
- `scores/classical/vivaldi_four_seasons/spring/vivaldi_four_seasons_spring_m1.score.json`
- `scores/classical/vivaldi_four_seasons/spring/vivaldi_four_seasons_spring_m2.score.json`
- `scores/classical/vivaldi_four_seasons/spring/vivaldi_four_seasons_spring_m3.score.json`
- `scores/classical/vivaldi_four_seasons/summer/vivaldi_four_seasons_summer_m1.score.json`
- `scores/classical/vivaldi_four_seasons/summer/vivaldi_four_seasons_summer_m2.score.json`
- `scores/classical/vivaldi_four_seasons/summer/vivaldi_four_seasons_summer_m3.score.json`
- `scores/classical/vivaldi_four_seasons/winter/vivaldi_four_seasons_winter_m1.score.json`
- `scores/classical/vivaldi_four_seasons/winter/vivaldi_four_seasons_winter_m2.score.json`
- `scores/classical/vivaldi_four_seasons/winter/vivaldi_four_seasons_winter_m3.score.json`
- `scores/originals/ai_radiance/ai_radiance_m1.score.json`
- `scores/originals/ai_radiance/ai_radiance_m2.score.json`
- `scores/originals/ai_radiance/ai_radiance_m4.score.json`
- `scores/library/akashic/akashic_ambient_001.score.json`
- `scores/library/akashic/akashic_loop_001.score.json`
- `scores/library/akashic/akashic_notify_001.score.json`
- `scores/library/akashic/akashic_opening_bell_001.score.json`
- `scores/library/akashic/akashic_transition_001.score.json`
- `scores/library/akashic/akashic_transition_var01.score.json`
- `scores/library/akashic/akashic_ui_001.score.json`
- `scores/library/clockwork/clockwork_action_001.score.json`
- `scores/library/clockwork/clockwork_ambient_001.score.json`
- `scores/library/clockwork/clockwork_loop_001.score.json`
- `scores/library/clockwork/clockwork_notify_001.score.json`
- `scores/library/clockwork/clockwork_notify_var01.score.json`
- `scores/library/clockwork/clockwork_transition_001.score.json`
- `scores/library/clockwork/clockwork_ui_001.score.json`
- `scores/library/forest/forest_action_001.score.json`
- `scores/library/forest/forest_ambient_001.score.json`
- `scores/library/forest/forest_loop_001.score.json`
- `scores/library/forest/forest_notify_001.score.json`
- `scores/library/forest/forest_notify_var01.score.json`
- `scores/library/forest/forest_transition_001.score.json`
- `scores/library/forest/forest_ui_001.score.json`
- `scores/library/ocean/ocean_ambient_001.score.json`
- `scores/library/ocean/ocean_loop_001.score.json`
- `scores/library/ocean/ocean_notify_001.score.json`
- `scores/library/ocean/ocean_notify_var01.score.json`
- `scores/library/ocean/ocean_transition_001.score.json`
- `scores/library/ocean/ocean_ui_001.score.json`
- `scores/library/rabbit/rabbit_action_001.score.json`
- `scores/library/rabbit/rabbit_ambient_001.score.json`
- `scores/library/rabbit/rabbit_loop_001.score.json`
- `scores/library/rabbit/rabbit_notify_001.score.json`
- `scores/library/rabbit/rabbit_notify_var01.score.json`
- `scores/library/rabbit/rabbit_transition_001.score.json`
- `scores/library/rabbit/rabbit_ui_001.score.json`
- `scores/library/restraint/restraint_action_001.score.json`
- `scores/library/restraint/restraint_ambient_001.score.json`
- `scores/library/restraint/restraint_loop_001.score.json`
- `scores/library/restraint/restraint_notify_001.score.json`
- `scores/library/restraint/restraint_notify_var01.score.json`
- `scores/library/restraint/restraint_transition_001.score.json`
- `scores/library/restraint/restraint_ui_001.score.json`
