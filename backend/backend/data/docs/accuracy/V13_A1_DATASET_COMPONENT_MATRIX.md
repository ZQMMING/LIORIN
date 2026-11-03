# V1.3 A1 — Dataset → Component Mapping

**日期**: 2026-08-22
**类型**: READ-ONLY AUDIT
**状态**: FINAL

---

## 原则声明

本文档建立数据集与 Component 的映射关系，确保每个测试都有明确的数据来源。
禁止修改数据集或测试代码。

---

## 一、数据集清单与可用性

### 1.1 外部数据集

| 数据集 | 案例数 | 可用组件 | 可信度 | 许可 | 状态 |
|--------|--------|---------|--------|------|------|
| fate-bench (官方答案) | 215题 | BAZI-02, ZW-03 | A (HIGH) | CC BY 4.0 | ✅ 可用 |
| fate-bench (第三方答案) | 80题 | BAZI-02 | B (MEDIUM) | CC BY 4.0 | ✅ 可用 (降权) |
| MingLi-Bench | 160题 | BAZI-02, ZW-03 | A (HIGH) | MIT | ✅ 可用 |
| BaziQA (去重后) | ~160题 | BAZI-02 | A (HIGH) | MIT | ✅ 可用 |
| CBDB | 649,533人 | 待筛选 | A (HIGH) | CC BY-NC-SA | ⚠️ 非商业限制 |
| chunqiu | 71人/121事 | 历史案例 | A (HIGH) | CC BY 4.0 | ⚠️ 需下载 |
| Ziwei Dataset | 518,400命盘 | ZW-03~10 | C-D | CC BY 4.0 | ⚠️ 解读非GT |

### 1.2 自建数据集

| 数据集 | 案例数 | 可用组件 | 可信度 | 许可 | 状态 |
|--------|--------|---------|--------|------|------|
| Golden Dataset v1 | 50案例/518事件 | BAZI-02, HELUO-20~21, ZW-03 | B-C | 自建 | ✅ 可用 |
| fate-bench_local | 63人/295题 | BAZI-02 | A | CC BY 4.0 | ✅ 已本地化 |
| boundary_cases | ~30边界案例 | BAZI-02, HELUO-09~12 | B | 自建 | ✅ 可用 |

---

## 二、组件 → 数据集映射

### 2.1 Bazi Engine

| Component | 主要数据集 | 案例数 | 通过率 | 备注 |
|-----------|-----------|--------|--------|------|
| BAZI-02 四柱计算 | fate-bench (官方) | 215 | 96.7% (59/61命主) | ✅ 已通过 |
| BAZI-02 四柱计算 | MingLi-Bench | 160 | 待验证 | ⚠️ 未集成到测试 |
| BAZI-02 四柱计算 | Golden Dataset | 50 | 100% | ✅ 通过 |
| BAZI-09 大运 | 自建 boundary | ~30 | 待验证 | ⚠️ 流派差异 |

### 2.2 Heluo Engine

| Component | 主要数据集 | 案例数 | 通过率 | 备注 |
|-----------|-----------|--------|--------|------|
| HELUO-09~12 卦象计算 | Golden Dataset | 50 | 100% | ✅ 纪晓岚案例 |
| HELUO-13~15 流年/月/日 | 待建立 | 0 | N/A | ❌ 缺失 |
| HELUO-20~21 本命卦验证 | Golden Dataset | 50 | 100% | ✅ 通过 |

### 2.3 Ziwei Engine

| Component | 主要数据集 | 案例数 | 通过率 | 备注 |
|-----------|-----------|--------|--------|------|
| ZW-03~10 排盘 | fate-bench (交叉) | 63人 | 96.7% | ⚠️ 通过 iztro |
| ZW-03~10 排盘 | Ziwei Dataset | 518,400 | 待验证 | ⚠️ 仅排盘部分 |

### 2.4 Huangli Engine

| Component | 主要数据集 | 案例数 | 通过率 | 备注 |
|-----------|-----------|--------|--------|------|
| HL-01~06 历法计算 | sxtwl 内置 | N/A | 100% | ✅ 继承 Bazi |
| HL-07~10 规则验证 | 待对照经典 | 0 | N/A | ❌ 缺失 |

### 2.5 Yi Engine

| Component | 主要数据集 | 案例数 | 通过率 | 备注 |
|-----------|-----------|--------|--------|------|
| YI-02~03 经典文本 | 《易经》原文 | 64卦×384爻 | 100% | ✅ 结构验证 |
| YI-04~08 卦象规则 | 《易经》规则 | 64卦 | 100% | ✅ 结构验证 |
| YI-01/09/13 解释层 | 专家评级 | 0 | N/A | ❌ 不可自动化 |

---

## 三、数据覆盖矩阵

```text
                    fate-bench | MingLi | BaziQA | Golden | 自建边界
BAZI-02 四柱        ✅ 215题    | 160题  | ~160题 | ✅ 50  | ~30
HELUIO-09~12 卦象   ❌          | ❌     | ❌     | ✅ 50  | ❌
HELUIO-13~15 流年   ❌          | ❌     | ❌     | ❌     | ❌
ZW-03~10 排盘       ⚠️ 交叉     | ❌     | ❌     | ❌     | ❌
HL-07~10 规则验证   ❌          | ❌     | ❌     | ❌     | ❌
YI-02~08 结构       ❌          | ❌     | ❌     | ❌     | ❌
YI-01/09/13 解释    ❌          | ❌     | ❌     | ❌     | ❌
```

---

## 四、缺口分析

### 4.1 高优先级缺口 (P0)

| 缺口 | 影响组件 | 所需数据 | 预估工作量 |
|------|---------|---------|-----------|
| 流年/流月/流日 历史盲测 | HELUO-13~15 | fate-bench 中时间维度案例 | 2天 |
| 大运流派一致性验证 | BAZI-09, HELUO-25 | 多流派对比数据 | 1天 |
| 黄历规则经典对照 | HL-08~10 | 《玉匣记》《协纪辨方书》 | 3天 |

### 4.2 中优先级缺口 (P1)

| 缺口 | 影响组件 | 所需数据 | 预估工作量 |
|------|---------|---------|-----------|
| Ziwei 排盘独立验证 | ZW-03~10 | Ziwei Dataset 排盘部分 | 1天 |
| 十神流派差异 | BAZI-10 | 子平/盲派对比 | 1天 |
| Yi 象义链完整性 | YI-09 | 经典原文对照 | 2天 |

### 4.3 低优先级缺口 (P2)

| 缺口 | 影响组件 | 所需数据 | 预估工作量 |
|------|---------|---------|-----------|
| CBDB 历史案例筛选 | 全部 | CBDB 数据库 | 1周 |
| chunqiu 春秋案例 | 历史验证 | chunqiu 数据集 | 2天 |
| 专家评级体系 | YI-01/09/13 | 专家网络 | 不确定 |

---

## 五、数据预处理要求

### 5.1 每个案例必须包含

```yaml
required_fields:
  - birth_date: "YYYY-MM-DD"
  - birth_time: "HH:MM" or "时辰名"
  - gender: "male" or "female"
  - birth_location:  # 影响真太阳时
      longitude: 经度
      timezone: "IANA/Timezone"
  - known_events:  # 至少一个已知事件
      - date: "YYYY-MM-DD"
        type: "DOMAIN"  # career/relationship/health/wealth/migration
        direction: "POSITIVE" | "NEGATIVE" | "NEUTRAL"
        description: "事件描述"
        source: "文献/来源"
  - answer_provenance: "official" | "third-party" | "expert"
  - evidence_grade: "A" | "B" | "C"
```

### 5.2 重叠检测

```text
所有数据集案例必须通过重叠检测:
├── fate-bench ↔ MingLi-Bench: 120题重叠 (已标记)
├── fate-bench ↔ BaziQA: ~40题重叠 (需去重)
└── Golden Dataset ↔ 外部: 需逐条核对

去重策略:
├── 官方答案优先 (fate-bench official)
├── 第三方答案降权 (weight=0.7)
└── Golden Dataset 单独统计
```

---

**报告结束**
**下一步**: A1.6 Oracle Independence Verification
