
## PATCH-012 干支组合/六亲/神煞·命例边界（commit 待）

### A 干支组合（4 Candidate）
YHZP-131-001 看日主→提纲→财官 / PZZQ-005-006 刑冲会合 / QTBJ-048-002 地支成局 / SFTK-119-002 入墓冲刑冲。禁日时断语泛化；SMTH-030-002（黨盛為強）引用不实不得再入。

### B 六亲（3 Candidate）
YHZP-102-001 印母财父 / SFTK-007-002 六亲宫位（年祖月父母日夫妻时子女）/ DTS-045-001 反局六亲（君赖臣/母慈灭子，结构层独立）。禁跨书混用、禁母慈灭子=通用六亲。

### C 边界冻结
神煞 EXCLUDED_FROM_RULE（文献检索/参考展示；禁命局核心裁决/用神判断/吉凶自动输出）；命例 REFERENCE_ONLY（Rule 验证/Golden/回归测试；禁反推规则）。

### Golden 4 个
地支成局（禁成局=贵）/ 刑冲会合（禁=吉凶）/ 印母财父（禁六亲=吉凶）/ 母慈灭子（禁反局=通用六亲）。

### 产物
governance/patch_012_ganzhi_liuqin_boundary.json（7 Candidate + 边界冻结 + 4 Golden）
