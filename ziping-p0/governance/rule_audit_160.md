# PATCH-160 只读规则缺口审计基线

定位：160 起点基线，非新架构规范。六书分域并行，不投票不分主次。
SFTK(神峰) 2519 Evidence 正式纳入，不再称外围。

## 已完成(封板)
Root / Transparent / 六合六冲 / 五合 / 三合三会 / target官星合冲 /
required-blocked-supported三桶 / Candidate State / Judgment / Interpretation。

## 已注册原子条件
Root: 有根通根无根(可判) 财身官印有根(可判) 根深根浅/无气(NOT_IMPLEMENTED)
Transparent: 财官印食伤杀透(月令) 见财见印见官(anywhere) 官杀透/财官双透(NOT_IMPLEMENTED)
Combination: 6合6冲pair 五合 三合三会结构 官星被合/受冲(target) 刑破害未建

## 实际三桶
财格: req[财有根,财透] blocked[财太露] supp[格清,配合,运之喜忌]
官格: req[官有根,官透] blocked[官星受冲,见财] supp[财印护官,运之喜忌]
印格: req[印有根,印透] blocked(无)
别名已注册8类格局(七杀/偏财/偏印/食神/伤官/建禄/月劫/外格) 三桶未建

## 三态真实
SUPPORTED=官格; NOT_SUPPORTED=财不透/官见财; PENDING=财格财太露

## 缺口逐项(六书×Registry×Assertion)
裁决四类: 已有事实->复用 / 缺原子事实->列缺什么 / 语义明确->可进下一实现 / 综合判断->暂UNKNOWN
1. 根深/根浅: 只判有无, 未判深浅
2. 无气: 与无根拆开, 未建
3. 旺衰/身强身弱: 禁直出, 160研究主对象
4. 官杀透/财官双透: multi_target未建
5. 刑/破/害 Relation: 未建
6. 财太露: 当前阶段UNKNOWN/PENDING; 暂未找到足够明确可验证的原子事实拆解;
   未来若经典证据能拆出明确原子关系可另立研究阶段; 禁止count shortcut
7. 身强/身弱/得令权重: 禁直出
8. 剩余8类格局三桶: 别名已注册 Assertion未建
9. 岁运等后续子平规则

## 铁律
三态不降级; supported不参与硬判; 有合≠官被合; 有冲≠官受冲;
不评分不投票; 不输出成格/吉凶; 财太露禁计数; 有根≠身强; 得令≠身强。
