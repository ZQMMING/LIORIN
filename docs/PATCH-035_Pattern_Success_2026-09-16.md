
# PATCH-035：格局成败 Production（RULE-035-01）— 2026-09-16

## 里程碑
**格局成败层正式生产**——pattern_success_state 首次出值（SUCCESS），成/败/带忌/救应/相神五要素接线。

## 证据（A 级，逐字）
- PZZQ-005-008：成「財格透印而位置安帖、兩不相剋，財格成也」；败「財輕比重，財透七煞，財格敗也」；带忌「成中有敗，必是帶忌」→「財旺生官而又逢傷逢合」；救应「敗中而成，全憑救應」→「財逢劫而透食以化之，生官以制之；逢煞而食神制煞以生財，或存財而合煞」
- PZZQ-007-004：相神「月令既得用神，則别位亦必有相」（相神 PZZQ_ONLY，022 系列冻结）

## 1983-1103 判定
- **pattern_success_state = SUCCESS(路径C財格透印)**：财藏支（戌未）、印透干（癸壬壬），干支分离两不相克 → 财格成也
- **败格未触发**：財輕比重（比劫透=0，双谓词不成立）｜財透七煞（财不透、煞不透）→ 均 FAIL
- **daiji = NO_DAIJI**：财不透、官不透、伤官不透 → 「財旺生官逢傷逢合」不成立
- **rescue = NO_RESCUE_NEEDED**：成格无需救应（救应参照登记：財逢劫透食化之/生官制之；逢煞食制煞生財）
- **相神 = PRESENT(印)**：月令得用神财，别位印透三相神成立（PZZQ_ONLY）

## namespace 隔离
pattern_success ≠ qing_za（清浊，PZZQ.qing_za/DTS.qing_zhuo 独立）——成败只管成/败/带忌/救应/相神。

## 谓词裁决
败条件「双谓词同时成立」：財輕比重=财透∧比劫透；財透七煞=财透∧七煞透。禁计数/评分/权重（比劫数>财数 之类一律禁止）。

## 枚举注册
enum_registry **v1.10.0（105 枚举）**：新增 pattern_success_state/daiji_state/rescue_state/xiangshen_state（PZZQ_ONLY 绑定）。

## 验证
Golden GC-001 回归通过（+4 状态 + trace + forbidden）；枚举 22/22 缺口=0。

## 产物
- engines/common/pattern_success_rules.py（RULE-035-01）
- engines/common/golden_cases.py（GC-001 v5）
- governance/enum_registry.json（v1.10.0）
