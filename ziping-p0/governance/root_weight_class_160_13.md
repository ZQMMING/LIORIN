# PATCH-160.13 根重根轻原典校对 PASS/READ-ONLY SEALED

## 原典依据
《子平真诠·论十干得时不旺失时不弱》
"长生禄刃，根之重者也；墓库余气，根之轻者也。"
"得三比肩不如得一长生禄刃。干多不如根重。"

## 核心定义
长生/禄/刃 -> 根重(HEAVY)
墓库/余气 -> 根轻(LIGHT)

## 可执行范围
- 支->日主根类型(长生/禄/刃/墓库/余气): 确定性Signal
- 输出 root_weight_class = HEAVY/LIGHT 定性档
- 保留root_type+支位provenance

## 禁止
数值化/权重求和/123分/root_weight->身强/->旺/数量->强弱。
比肩数量vs根类型的比较论述=定性比较, 不转线性评分。

## 工程状态
qi_position已有; root_type分类尚缺。
当前只允许研究/定义Root Type Signal, 不进Relative Strength Rule。
根重只是强弱输入关系之一, 非结论(秋木根深而强是结合全命局)。

## 后续
Root Type -> Root Weight Class -> 与得时/党助/损益/类聚共同研究强弱。
不单独产生身强弱。
