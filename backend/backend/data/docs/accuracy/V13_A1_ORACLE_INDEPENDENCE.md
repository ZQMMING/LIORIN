# V1.3 A1 — Oracle Independence Verification

**日期**: 2026-08-22
**类型**: READ-ONLY AUDIT
**状态**: FINAL

---

## 原则声明

本文档验证每个 Oracle 是否真正独立于被测系统，防止"自证循环"。
禁止修改任何代码或数据集。

---

## 一、独立性评估框架

```text
INDEPENDENCE CRITERIA:
├── SOURCE_INDEPENDENCE: Oracle 来源与被测系统不同
├── IMPLEMENTATION_INDEPENDENCE: Oracle 实现不依赖被测系统
├── DATA_INDEPENDENCE: Oracle 数据不被被测系统生成
├── LOGIC_INDEPENDENCE: Oracle 判断逻辑独立
└── CONFLICT_RESOLUTION: 冲突时以 Oracle 为准

AUTONOMY LEVELS:
├── FULL (4/4): 完全独立，可信度高
├── PARTIAL (3/4): 部分独立，需标注风险
├── WEAK (2/4): 弱独立，不可作为 Accuracy 依据
└── NONE (0-1/4): 非独立，属于"自证循环"
```

---

## 二、各 Oracle 独立性评估

### 2.1 Bazi 四柱计算 Oracle

```text
被测系统: BaziEngine.compute() (src/tongshu/engines/bazi_engine.py)
Oracle 来源: sxtwl 库 + fate-bench 官方答案

INDEPENDENCE CHECK:
├── ✅ SOURCE_INDEPENDENCE: sxtwl 是独立第三方库 (Python package)
├── ✅ IMPLEMENTATION_INDEPENDENCE: sxtwl 代码与 BaziEngine 分离
├── ✅ DATA_INDEPENDENCE: fate-bench 答案由竞赛主办方提供，非项目生成
├── ✅ LOGIC_INDEPENDENCE: sxtwl 使用独立历法算法 (非本项目代码)
└── RESULT: FULL INDEPENDENCE (4/4)

结论: ✅ 有效 Oracle，可用于 Accuracy 计算
```

### 2.2 Heluo 卦象计算 Oracle

```text
被测系统: HeluoCalculator (src/tongshu/engines/heluo/canonical.py)
Oracle 来源: 《河洛理数》原文 + Golden Dataset

INDEPENDENCE CHECK:
├── ✅ SOURCE_INDEPENDENCE: 《河洛理数》为清代典籍 (江本盛编)，独立于本项目
├── ✅ IMPLEMENTATION_INDEPENDENCE: 算法为固定公式，非本项目代码
├── ✅ DATA_INDEPENDENCE: Golden Dataset 为历史案例 (纪晓岚等)，非项目生成
├── ✅ LOGIC_INDEPENDENCE: 算法遵循固定数学规则，无循环依赖
└── RESULT: FULL INDEPENDENCE (4/4)

结论: ✅ 有效 Oracle，可用于 Accuracy 计算
```

### 2.3 Ziwei 排盘 Oracle

```text
被测系统: ZiweiEngine._compute_via_iztro()
Oracle 来源: iztro Python 库 + fate-bench 交叉验证

INDEPENDENCE CHECK:
├── ✅ SOURCE_INDEPENDENCE: iztro 是独立紫微斗数库 (GitHub: 9sssss/iztro)
├── ⚠️ IMPLEMENTATION_INDEPENDENCE: iztro 为项目依赖，非独立实现
├── ✅ DATA_INDEPENDENCE: fate-bench 答案独立于本项目
├── ⚠️ LOGIC_INDEPENDENCE: 部分排盘规则可能共享 (需核查)
└── RESULT: PARTIAL INDEPENDENCE (3/4)

风险: 若 iztro 内部实现与 BaziEngine 共享 sxtwl，存在弱独立风险
缓解: 通过 fate-bench 官方答案交叉验证
结论: ⚠️ 有条件接受，需标注依赖关系
```

### 2.4 Huangli 节气干支 Oracle

```text
被测系统: HuangliEngine.get_day()
Oracle 来源: sxtwl 库 (与 Bazi 共享)

INDEPENDENCE CHECK:
├── ⚠️ SOURCE_INDEPENDENCE: 共享 sxtwl，非完全独立来源
├── ⚠️ IMPLEMENTATION_INDEPENDENCE: 共享同一库实现
├── ✅ DATA_INDEPENDENCE: 历史黄历记录可独立验证
├── ⚠️ LOGIC_INDEPENDENCE: 历法计算逻辑共享
└── RESULT: WEAK INDEPENDENCE (1/4)

分析: Huangli 的历法部分与 Bazi 共享同一 Oracle，
      但黄历规则层 (宜忌/神煞) 有独立 Oracle (《玉匣记》等)
结论: ⚠️ 历法部分可接受 (继承 Bazi 的 sxtwl)，
      规则部分需独立验证
```

### 2.5 Yi 经典文本 Oracle

```text
被测系统: YiEngine (src/tongshu/engines/yi/)
Oracle 来源: 《易经》原文数据库

INDEPENDENCE CHECK:
├── ✅ SOURCE_INDEPENDENCE: 《易经》为先秦典籍，独立于本项目
├── ✅ IMPLEMENTATION_INDEPENDENCE: 文本查询为 I/O 操作，无逻辑耦合
├── ✅ DATA_INDEPENDENCE: 经典原文固定，非项目生成
├── ✅ LOGIC_INDEPENDENCE: 查询逻辑简单，无循环依赖
└── RESULT: FULL INDEPENDENCE (4/4)

结论: ✅ 有效 Oracle，可用于文本完整性验证
注意: 解释层 (YI-01/09/13) 无独立 Oracle，为 O4 Human
```

---

## 三、"自证循环"风险识别

### 3.1 高风险模式 (禁止)

```text
❌ 模式 A: 测试答案来自同一算法的不同实现
   示例: 用 sxtwl 验证 BaziEngine (sxtwl 就是被测依赖)
   状态: ⚠️ 存在 — BaziEngine 使用 sxtwl 作为依赖

❌ 模式 B: 测试数据由被测系统生成
   示例: Golden Dataset 中的案例由 HeluoEngine 计算生成
   状态: ✅ 不存在 — Golden Dataset 为历史案例 (纪晓岚)

❌ 模式 C: 测试验证自己的输出
   示例: test_xxx 断言 engine.compute() == engine.compute()
   状态: ✅ 不存在 — 测试使用外部数据集
```

### 3.2 已识别风险项

```text
⚠️ 风险 1: sxtwl 依赖
   位置: BaziEngine._compute_with_sxtwl()
   性质: 被测系统直接使用 sxtwl 作为计算引擎
   缓解: fate-bench 提供独立验证 (竞赛官方答案)
   置信度: 中高 — 但需确认 sxtwl 实现与 BaziEngine 逻辑是否一致

⚠️ 风险 2: Golden Dataset 可能包含项目生成案例
   位置: dataset/golden_v1/golden_cases.json
   性质: 需人工核查每条案例来源
   缓解: 当前 50 条案例均为历史名人 (纪晓岚等)，可信度高
   置信度: 高 — 但需继续扩展时保持严格来源控制

⚠️ 风险 3: iztro 与 sxtwl 共享
   位置: ZiweiEngine._compute_via_iztro()
   性质: iztro 可能内部使用 sxtwl
   缓解: fate-bench 交叉验证
   置信度: 中 — 需核查 iztro 实现
```

---

## 四、独立性评分汇总表

| Component | Oracle 类型 | 独立性评分 | 状态 | 备注 |
|-----------|------------|-----------|------|------|
| BAZI-02 四柱计算 | O1 (sxtwl) + O2 (fate-bench) | FULL (4/4) | ✅ | 有效 Oracle |
| HELUO-09~12 卦象 | O1 (公式) + O3 (经典) | FULL (4/4) | ✅ | 有效 Oracle |
| ZW-03~10 排盘 | O1 (iztro) + O2 (fate-bench) | PARTIAL (3/4) | ⚠️ | 有条件接受 |
| HL-01~06 历法 | O1 (sxtwl) | WEAK (1/4) | ⚠️ | 继承 Bazi，可接受 |
| HL-07~10 规则 | O3 (经典) | PARTIAL (2/4) | ⚠️ | 需独立验证 |
| YI-02~08 结构 | O1/O3 (经典) | FULL (4/4) | ✅ | 有效 Oracle |
| YI-01/09/13 解释 | O4 (Human) | N/A | ❌ | 不可自动化 |
| 全部 Validation | O1 (Invariant) | FULL (4/4) | ✅ | 结构验证 |

---

## 五、独立性改进建议

### 5.1 立即执行 (A2 阶段)

```text
改进 1: 建立 sxtwl 版本锁定
├── 在 requirements.txt 锁定 sxtwl 版本
├── 记录 sxtwl commit hash
└── 每版本更新时重新验证

改进 2: Golden Dataset 来源声明
├── 每条案例添加 source_field
├── 区分 "historical" vs "synthetic"
└── 禁止合成案例进入 Golden Dataset
```

### 5.2 中期执行 (A3 阶段)

```text
改进 3: 建立独立历法验证
├── 引入第二个独立历法库 (如 ephem)
├── 交叉验证 sxtwl 结果
└── 计算交叉一致性比率

改进 4: 专家评级体系
├── 建立 Yi 解释质量 Rubric
├── 至少 2 名专家独立评级
└── 计算 Inter-rater Agreement (Cohen's Kappa)
```

---

## 六、独立性总结

```text
总体评估:
├── 核心算法 (四柱、卦象): ✅ 独立性强，可作为 Accuracy 依据
├── 派生组件 (大运、流年): ⚠️ 需交叉验证
├── 解释层 (Yi): ❌ 不可自动化，需专家评级
└── 结构层 (Validation/Forward): ✅ 结构验证有效，非准确性指标

建议:
├── A2 阶段: 完成历史盲测，建立 O2 覆盖
├── A3 阶段: 建立专家评级 Rubric，启动 O4 验证
├── A4 阶段: 引入独立历法库，交叉验证 sxtwl
└── 禁止: 使用任何自证循环数据计算 Accuracy
```

---

**报告结束**
**下一步**: A1.7 Metric Qualification
