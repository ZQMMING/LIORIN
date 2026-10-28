# PATCH-191 188-190 Structural Entry 四态语义审计（SEALED）

## 审计问题
确认所有新增 Entry 不存在：未命中→FALSE / UNKNOWN→FALSE / NOT_AUTHORIZED→FALSE。

## 逐个核 False 分支来源

| Entry | False 触发条件 | False 性质 |
|---|---|---|
| 188 曲直/炎上/稼穑/从革/润下/井栏叉 | 日干不符 或 地支局不全 | 确定Fact不满足，非UNKNOWN |
| 189 六阴朝阳 | 非辛日/非戊子时/天干或藏干有官杀 | 确定Fact合取，非"没搜到" |
| 190 刑合 | 非癸日/非甲寅时/有申/天干有戊己 | 排除项为L0确定Fact |
| 190 合禄 | 非戊癸日/非庚申时/天干透官 | 天干官杀存在性为确定枚举 |

## 审计结论
1. **L0 Structural Entry 层没有 UNKNOWN。** 四柱干支齐全、日干/时柱/地支集合/天干官杀存在性都是确定性Fact。False=确定不构成该结构，合法。
2. **UNKNOWN/NOT_AUTHORIZED 不出现于此层。** 它们在Rule/Judgment层（160旺衰、174有效关系、179缓急、从化化真等）。L0只出确定结构事实。
3. **没有"未命中→FALSE"。** 例：六阴朝阳"天干无官杀"=枚举全部天干后any()==False，是真Fact；合禄"天干不透官"同理。藏干/天干官杀存在性均来自全量枚举，非Rule搜索。
4. **合禄语义修正已正确：** 只查天干不透，不查藏干，避免把时支申藏官误判。

## 分层确认
```
L0 Structural Entry: 确定布尔(有/无), 无UNKNOWN
  ↓
Rule 层: SAT/UNSAT/UNKNOWN 三态
  ↓
Judgment: SUPPORTED/PENDING/NOT_SUPPORTED
  ↓
NOT_AUTHORIZED 项(160/174/179/从化)永不降级为FALSE
```

## 结论
188-190 全部通过四态审计。无 FALSE 污染。可继续扩规则。
