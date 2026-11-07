# YHZP补切Skill

## 任务
YHZP原314章只切了33个，漏了244个。按冻结规范补切全部遗漏章节。

## 原文路径
`D:\顺天系统资料\豆包资料\六部经典最终原著版\YHZP_渊海子平.md`

## 已有切片
`D:\shuntian-ziping-p0\p0_v2\output\YHZP\YHZP_slices.jsonl`（33个）

## 补切范围
跳过已切的33个，补切其余244个章节。

## 切片单元规范
每个切片必须包含12个字段：
- slice_id: YHZP.章节名
- book: YHZP
- section: 基础/月令/格局/十神/旺衰/用神/行运/命例/etc
- chapter: 章节名
- category: 20类之一
- subject: 切片主体
- source_text: 原文（不改写）
- source_location: 文件名+行号/章节
- conditions: 原文明确的条件（无则[]）
- result: 原文明确的结果（无则null）
- relations: 原文显式关系（无则[]）
- status: ACCEPT

## 不切的内容
- 神煞（贵人/禄/驿马/华盖/空亡等）放OTHER，第一轮不切
- 无明确语义事实的章节=ZERO_HIT

## Relation提取铁律
只提取原文显式表达：
- "甲己合"→TG_HE(甲,己)
- "甲生丙"→SHENG(甲,丙)
- "子午冲"→CHONG(子,午)
禁止：
- 理论推导（木生火是理论，原文没说就不提取）
- 共现误判（甲乙同时出现≠关系）
- 方向反判

## 输出
补切后合并到YHZP_slices.jsonl，总切片数应该接近270+。
