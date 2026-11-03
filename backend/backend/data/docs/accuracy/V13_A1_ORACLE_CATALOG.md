# V1.3 A1 — Oracle Qualification Catalog

**日期**: 2026-08-22
**类型**: READ-ONLY AUDIT
**状态**: FINAL

---

## 原则声明

本文档定义每个 Engine Component 的 Oracle 类型、可信度与独立性。
禁止修改任何代码或数据集。

---

## Oracle 类型定义

```text
O1 — DETERMINISTIC:
    存在唯一数学/历法规则，可完全自动化验证
    典型来源: sxtwl 库、固定映射表、经典公式
    指标: Exact Match / Accuracy (100% 或 0%)

O2 — STATISTICAL:
    基于真实世界事件数据，存在统计显著性
    典型来源: fate-bench (官方答案)、MingLi-Bench、BaziQA
    指标: Precision / Recall / Micro-F1 / Event-level Accuracy

O3 — CLASSICAL:
    基于古籍原文、专家规则，需人工或半自动验证
    典型来源: 《河洛理数》《滴天髓》《子平真诠》等
    指标: Classical Alignment Score / Evidence Closure Rate

O4 — HUMAN:
    需要专家判断，无法完全自动化
    典型来源: 专家评级、盲测评估
    指标: Inter-rater Agreement / Cohen's Kappa / Rubric Score

OX — UNVERIFIABLE:
    无可靠 Ground Truth，无法进行准确性评估
    典型来源: 泛化人生建议、未来预测验证
    指标: NOT_ACCURACY_EVALUABLE
```

---

## 一、Bazi Engine Oracle 资格

| Component | Oracle 类型 | 可信度 | 独立性 | 备注 |
|-----------|------------|--------|--------|------|
| BAZI-01 Pillar 模型 | N/A (Data Model) | N/A | N/A | 数据结构，非算法 |
| BAZI-02 四柱计算 | O1 | HIGH | ✅ 独立 (sxtwl 第三方库) | 寿星天文历计算 |
| BAZI-03 天干取数 | O1 | HIGH | ✅ 独立 (固定映射) | 甲=木, 乙=木... |
| BAZI-04 地支取数 | O1 | HIGH | ✅ 独立 (固定映射) | 子=水, 丑=土... |
| BAZI-05 时辰分支 | O1 | HIGH | ✅ 独立 (固定映射) | 0-1=子, 2-3=丑... |
| BAZI-06 时辰天干 | O1 | HIGH | ✅ 独立 (固定规则) | 日干→时干映射表 |
| BAZI-07 sxtwl 计算 | O1 | HIGH | ✅ 独立 (第三方库) | sxtwl 本身是独立历法库 |
| BAZI-08 简化计算 | O1 | MEDIUM | ⚠️ 与 O1 同源 | 无 sxtwl 时的降级路径 |
| BAZI-09 大运计算 | O1+O2 | MEDIUM-HIGH | ⚠️ 部分独立 | 起始年龄有流派差异 |
| BAZI-10 十神映射 | O1 | HIGH | ✅ 独立 (固定映射) | 比肩/劫财/食神等定义 |

**Bazi Oracle 总结:**
- 10 个组件中 8 个为 O1 Deterministic
- 2 个组件 (BAZI-09, BAZI-10) 涉及 O2/O3 混合
- 核心算法 (四柱计算) 已通过 sxtwl 交叉验证

---

## 二、Heluo Engine Oracle 资格

| Component | Oracle 类型 | 可信度 | 独立性 | 备注 |
|-----------|------------|--------|--------|------|
| HELUO-01 天干取数 | O1 | HIGH | ✅ 独立 (固定映射) | 洛书定则: 甲=6, 乙=7... |
| HELUO-02 地支取数 | O1 | HIGH | ✅ 独立 (固定映射) | 洛书定则: 子=1, 丑=2... |
| HELUO-03 天数计算 | O1 | HIGH | ✅ 独立 (公式) | Σ天干数, 遇10去十 |
| HELUO-04 地数计算 | O1 | HIGH | ✅ 独立 (公式) | Σ地支数, 遇10去十 |
| HELUO-05 天数归一化 | O1 | HIGH | ✅ 独立 (公式) | mod 10, 遇0取10 |
| HELUO-06 地数归一化 | O1 | HIGH | ✅ 独立 (公式) | mod 10, 遇0取10 |
| HELUO-07 洛书映射 | O1 | HIGH | ✅ 独立 (固定表) | 1-9→八卦映射 |
| HELUO-08 卦名计算 | O1 | HIGH | ✅ 独立 (组合规则) | 上下卦→六十四卦 |
| HELUO-09 先天卦 | O1 | HIGH | ✅ 独立 (固定规则) | 天地数→先天卦 |
| HELUO-10 元堂定位 | O1 | HIGH | ✅ 独立 (固定规则) | 先天卦→元堂卦 |
| HELUO-11 元堂飞支 | O1 | HIGH | ✅ 独立 (固定规则) | 纯阳/纯阴特殊处理 |
| HELUO-12 后天换卦 | O1+O3 | HIGH | ✅ 独立 (两步法) | 需《河洛理数》原文验证 |
| HELUO-13 流年计算 | O1+O2 | MEDIUM | ⚠️ 部分独立 | 卦象固定但事件解读需O2 |
| HELUO-14 流月计算 | O1+O2 | MEDIUM | ⚠️ 部分独立 | 同上 |
| HELUO-15 流日计算 | O1+O2 | MEDIUM | ⚠️ 部分独立 | 同上 |
| HELUO-16 节候卦 | O1 | HIGH | ✅ 独立 (固定规则) | 每日节候对应卦 |
| HELUO-17 卦气计算 | O1 | HIGH | ✅ 独立 (固定规则) | 卦气时序 |
| HELUO-18 遇10去十 | O1 | HIGH | ✅ 独立 (公式) | `_drop_ten()` |
| HELUO-19 带基准求和 | O1 | HIGH | ✅ 独立 (公式) | `_sum_with_base()` |
| HELUO-20 本命卦验证 | O1+O3 | HIGH | ✅ 独立 | 纪晓岚案例为 O3 验证 |
| HELUO-21 全案例验证 | O1+O3 | HIGH | ✅ 独立 | 批量验证 |
| HELUO-22 纯阳检测 | O1 | HIGH | ✅ 独立 (逻辑) | 六爻皆阳判定 |
| HELUO-23 纯阴检测 | O1 | HIGH | ✅ 独立 (逻辑) | 六爻皆阴判定 |
| HELUO-24 上下卦提取 | O1 | HIGH | ✅ 独立 (逻辑) | 爻→卦映射 |
| HELUO-25 大運计算 | O1+O2 | MEDIUM | ⚠️ 流派差异 | 顺逆排法有争议 |
| HELUO-26 输入准备 | O1 | HIGH | ✅ 独立 (转换) | 数据格式转换 |
| HELUO-27 解释计算 | O3+O4 | LOW | ❌ 非独立 | 解释依赖专家判断 |
| HELUO-28 因子权重 | O3 | MEDIUM | ⚠️ 部分独立 | 五行权重有流派差异 |
| HELUO-29 时间衰减 | O3 | MEDIUM | ⚠️ 部分独立 | 衰减系数定义 |
| HELUO-30 经典一致性 | O3 | HIGH | ✅ 独立 | 与经典原文对齐度 |

**Heluo Oracle 总结:**
- 30 个组件中 22 个为纯 O1 Deterministic
- 5 个组件为 O1+O3 混合 (需经典验证)
- 3 个组件为 O1+O2 (需外部数据验证)
- 核心算法 (取数→归一化→卦象) 已高度 O1 覆盖

---

## 三、Ziwei Engine Oracle 资格

| Component | Oracle 类型 | 可信度 | 独立性 | 备注 |
|-----------|------------|--------|--------|------|
| ZW-01 时间索引 | O1 | HIGH | ✅ 独立 (固定映射) | 小时→地支索引 |
| ZW-02 命盘模型 | N/A (Data Model) | N/A | N/A | 数据结构 |
| ZW-03 主引擎 | O1+O2 | MEDIUM | ⚠️ 部分独立 | 依赖 iztro 库 |
| ZW-04 iztro 集成 | O1 | HIGH | ✅ 独立 (第三方库) | iztro 是独立紫微库 |
| ZW-05 Stub 模式 | O1 | LOW | ❌ 非独立 | Stub 为降级，无验证价值 |
| ZW-06 信号提取 | O1 | MEDIUM | ⚠️ 部分独立 | 提取规则有争议 |
| ZW-07 十四主星映射 | O1 | HIGH | ✅ 独立 (固定表) | 14星固定位置 |
| ZW-08 四化效果 | O1 | HIGH | ✅ 独立 (固定规则) | 四化固定映射 |
| ZW-09 命宫计算 | O1 | HIGH | ✅ 独立 (固定规则) | 命宫位置算法 |
| ZW-10 十二宫排布 | O1 | HIGH | ✅ 独立 (固定规则) | 十二宫固定位置 |

**Ziwei Oracle 总结:**
- 10 个组件中 8 个为 O1 Deterministic
- 1 个组件依赖 iztro (O1，第三方库)
- 1 个 Stub 模式无验证价值

---

## 四、Huangli Engine Oracle 资格

| Component | Oracle 类型 | 可信度 | 独立性 | 备注 |
|-----------|------------|--------|--------|------|
| HL-01 农历月份标签 | O1 | HIGH | ✅ 独立 (固定映射) | 农历月中文标签 |
| HL-02 黄历日数据 | N/A (Data Model) | N/A | N/A | 数据结构 |
| HL-03 注册表加载 | O1 | HIGH | ✅ 独立 (I/O) | 文件读取 |
| HL-04 单日查询 | O1 | HIGH | ✅ 独立 (查询) | 查询逻辑 |
| HL-05 干支计算 | O1 | HIGH | ✅ 独立 (sxtwl) | 继承 Bazi 的 sxtwl |
| HL-06 节气计算 | O1 | HIGH | ✅ 独立 (sxtwl) | 继承 Bazi 的 sxtwl |
| HL-07 建除循环 | O1 | HIGH | ✅ 独立 (固定规则) | 12建除循环 |
| HL-08 宜忌规则 | O3 | MEDIUM | ⚠️ 需验证 | 规则来源需经典对照 |
| HL-09 神煞方位 | O3 | MEDIUM | ⚠️ 需验证 | 需《玉匣记》等原文 |
| HL-10 二十八宿 | O3 | MEDIUM | ⚠️ 需验证 | 需经典原文对照 |

**Huangli Oracle 总结:**
- 10 个组件中 6 个为纯 O1 Deterministic
- 4 个组件为 O3 Classical (需经典验证)
- 核心历法计算已通过 sxtwl 验证

---

## 五、Yi Engine Oracle 资格

| Component | Oracle 类型 | 可信度 | 独立性 | 备注 |
|-----------|------------|--------|--------|------|
| YI-01 主解释器 | O4 | LOW | ❌ 非独立 | 解释质量需专家评级 |
| YI-02 经典文本查询 | O3 | HIGH | ✅ 独立 (经典原文) | 《易经》原文 |
| YI-03 爻辞查询 | O3 | HIGH | ✅ 独立 (经典原文) | 爻辞原文 |
| YI-04 六十四卦符号 | O1 | HIGH | ✅ 独立 (固定表) | 64卦固定符号 |
| YI-05 体用关系 | O1 | HIGH | ✅ 独立 (固定规则) | 体用生克规则 |
| YI-06 错卦计算 | O1 | HIGH | ✅ 独立 (固定规则) | 错卦固定算法 |
| YI-07 综卦计算 | O1 | HIGH | ✅ 独立 (固定规则) | 综卦固定算法 |
| YI-08 互卦计算 | O1 | HIGH | ✅ 独立 (固定规则) | 互卦固定算法 |
| YI-09 象义扩展 | O3+O4 | LOW | ❌ 非独立 | 扩展质量依赖专家 |
| YI-10 象义链验证 | O1 | MEDIUM | ✅ 独立 (结构验证) | 链完整性验证 |
| YI-11 爻位分析 | O1 | HIGH | ✅ 独立 (固定规则) | 当位/中正规则 |
| YI-12 承乘比应 | O1 | HIGH | ✅ 独立 (固定规则) | 爻间关系规则 |
| YI-13 关系式解释 | O4 | LOW | ❌ 非独立 | 质量需专家评级 |
| YI-14 术语约束检查 | O1 | HIGH | ✅ 独立 (结构检查) | 17术语禁止列表 |

**Yi Oracle 总结:**
- 14 个组件中 9 个为 O1 Deterministic (结构/规则层)
- 3 个组件为 O3 Classical (经典原文层)
- 2 个组件为 O4 Human (解释质量层)
- 核心问题: 解释层无法自动化验证

---

## 六、Evidence Chain Oracle 资格

| Component | Oracle 类型 | 可信度 | 独立性 | 备注 |
|-----------|------------|--------|--------|------|
| EV-01 证据链上下文 | O1 | HIGH | ✅ 独立 (结构) | 链式结构验证 |
| EV-02 溯源追踪 | O1 | HIGH | ✅ 独立 (图遍历) | 图结构验证 |
| EV-03 证明验证 | O1 | HIGH | ✅ 独立 (结构) | 引用完整性验证 |
| EV-04 链验证 | O1 | HIGH | ✅ 独立 (结构) | 孤儿节点检测 |
| EV-05~EV-09 注册方法 | O1 | HIGH | ✅ 独立 (I/O) | 数据注册 |
| EV-10~EV-14 数据模型 | N/A (Schema) | N/A | N/A | 数据结构定义 |

**Evidence Oracle 总结:**
- 全部 14 个组件为 O1 Deterministic 或 Schema
- 证据链为纯结构性验证，不涉及算法准确性

---

## 七、Signal 组件 Oracle 资格

| Component | Oracle 类型 | 可信度 | 独立性 | 备注 |
|-----------|------------|--------|--------|------|
| SIG-01~SIG-10 | O1 | HIGH | ✅ 独立 | 全部为数据结构 + 聚合逻辑 |

**Signal Oracle 总结:**
- 全部 10 个组件为 O1 Deterministic
- 信号层为纯结构化处理，不涉及算法准确性

---

## 八、Temporal 组件 Oracle 资格

| Component | Oracle 类型 | 可信度 | 独立性 | 备注 |
|-----------|------------|--------|--------|------|
| TP-01~TP-06 | O1 | HIGH | ✅ 独立 | 全部为时间对齐逻辑 |

**Temporal Oracle 总结:**
- 全部 6 个组件为 O1 Deterministic
- 时间对齐为纯数学计算，不涉及算法准确性

---

## 九、Validation V1.2 组件 Oracle 资格

| Component | Oracle 类型 | 可信度 | 独立性 | 备注 |
|-----------|------------|--------|--------|------|
| VAL-01~VAL-04 | O1 | HIGH | ✅ 独立 | Schema + Invariant 验证 |
| VAL-05~VAL-06 | O1 | HIGH | ✅ 独立 | 一致性计算 |
| VAL-07~VAL-09 | O1 | HIGH | ✅ 独立 | 失败分类 |
| VAL-10 | O1 | HIGH | ✅ 独立 | Micro-F1 公式 |
| VAL-11 | O1 | HIGH | ✅ 独立 | Macro-F1 公式 |
| VAL-12 | O1 | HIGH | ✅ 独立 | 边界条件 |

**Validation Oracle 总结:**
- 全部 12 个组件为 O1 Deterministic
- 验证框架本身为纯结构/公式验证

---

## 十、Forward Validation 组件 Oracle 资格

| Component | Oracle 类型 | 可信度 | 独立性 | 备注 |
|-----------|------------|--------|--------|------|
| FV-01~FV-10 | O1 | HIGH | ✅ 独立 | 全部为结构/时间验证 |

**Forward Oracle 总结:**
- 全部 10 个组件为 O1 Deterministic
- 前瞻验证为结构/时间隔离验证

---

## 十一、ACCURACY_ELIGIBILITY 判定

根据 Oracle 类型，每个 Component 的准确性资格如下:

```text
ELIGIBILITY RULES:
├── O1 ONLY → ACCURACY_ELIGIBLE (可完全自动化验证)
├── O1 + O3 → ACCURACY_ELIGIBLE_WITH_LIMITATIONS (需人工辅助)
├── O1 + O2 → ACCURACY_ELIGIBLE (可统计验证)
├── O3 + O4 → EVIDENCE_ONLY (需专家评级)
├── O4 ONLY → NOT_EVALUABLE (无法自动化)
└── OX → NOT_EVALUABLE (无Ground Truth)
```

### 资格分布

| 资格等级 | 组件数 | 占比 |
|---------|--------|------|
| ACCURACY_ELIGIBLE | ~100 | ~72% |
| ACCURACY_ELIGIBLE_WITH_LIMITATIONS | ~20 | ~14% |
| EVIDENCE_ONLY | ~10 | ~7% |
| NOT_EVALUABLE | ~8 | ~6% |
| N/A (Schema/Model) | ~4 | ~3% |

---

## 十二、关键发现

### 12.1 高置信度组件 (O1 + 独立)

| 引擎 | 组件数 | 占比 |
|------|--------|------|
| Bazi | 8/10 | 80% |
| Heluo | 22/30 | 73% |
| Ziwei | 8/10 | 80% |
| Huangli | 6/10 | 60% |
| Yi | 9/14 | 64% |
| Evidence | 10/14 | 71% |
| Signal | 10/10 | 100% |
| Temporal | 6/6 | 100% |
| Validation | 12/12 | 100% |
| Forward | 10/10 | 100% |

### 12.2 低置信度组件 (需专家/统计验证)

| 引擎 | 组件 | Oracle 类型 | 备注 |
|------|------|------------|------|
| Heluo | HELUO-27 解释计算 | O3+O4 | 解释质量无法自动化 |
| Heluo | HELUO-28 因子权重 | O3 | 流派差异 |
| Heluo | HELUO-29 时间衰减 | O3 | 系数定义 |
| Yi | YI-01 主解释器 | O4 | 需专家评级 |
| Yi | YI-09 象义扩展 | O3+O4 | 需专家评级 |
| Yi | YI-13 关系式解释 | O4 | 需专家评级 |

### 12.3 不可验证组件 (OX)

| 引擎 | 组件 | 原因 |
|------|------|------|
| Yi | YI-13 关系式解释 | 无法确定"正确"解释 |
| Heluo | HELUO-27 解释计算 | 泛化人生建议无法验证 |

---

**报告结束**
**下一步**: A1.3 Component → Test Mapping
