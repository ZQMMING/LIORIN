
# PATCH-033：SFTK 病药（RULE-033-01）— 2026-09-16

## 里程碑
qu_yong_state 出值——三用神（USE_GOD/QU_YONG/CLIMATE_USE）全部告别 UNDETERMINED。

## 证据（A 级）
- SFTK-008-001：「何以爲之病？原八字中原有所害之神也……如用財見比肩爲病，喜官殺爲藥也」
- SFTK-009-002：「日主太弱宜行身旺之地」

## 关键异文发现（S1，登记 text-variant-schema.md）
SFTK-008-001 底本「四柱純土……**水日干**則爲財多身弱」疑为「**木日干**」——木克土=财，水日干土=杀（前句已列殺重身輕）。工程按木日干采信（命中 1983 乙木戌月），PENDING 待 Human 取证裁决。

## 1983-1103 病药
- **病=财多身弱**：月令戌土=乙木之财当令 + 日主失令弱根
- **药=印比帮身**：印透三（癸壬壬）已在局中（SFTK-009-002 日主太弱宜行身旺之地）
- 次病：比劫仅支藏（亥甲/未乙）为日主之根，未成夺财重病（SFTK-008-001 用財見比肩喜官殺 登记）

## 逻辑修正（测试抓出）
日干自身≠比肩——首版 stems[1:] 误把日干乙计入比劫，修正为排除日干位（bijie_tou=0）。

## 三用神全部出值
use_god=CANDIDATE(财)｜qu_yong=DETERMINED(病=财多身弱,药=印比帮身)｜climate_use=DETERMINED(癸水)
pattern=DETERMINED(财格)；strength 仍 UNDETERMINED（无授权综合）。

## 验证
Golden GC-001 回归通过；枚举 22/22 缺口=0。

## 产物
- engines/common/bingyao_rules.py（RULE-033-01）
- engines/common/golden_cases.py（GC-001 更新）
- governance/patch_033_bingyao.json
- text-variant-schema.md（异文 S1 登记）
