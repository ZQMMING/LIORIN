# T3 计划：Primitive 小闭环验证（20-50条 Evidence → Primitive → Condition → Local Judgment）

**目标**: 选取 20-50 条真实五经证据，验证 Evidence → Primitive → Condition → Local Judgment 链路

**约束**: 不能直接扩大 infer_verdict()，必须证明每条 verdict 的 Evidence → Primitive → Condition → Authorization → Verdict

---

## 一、数据源

从 `data/p0_3_3_structured_evidence.json` 选取：
- 优先选择有 `conditions` 的证据（83条）
- 覆盖多经典（滴天髓/渊海子平/穷通宝鉴等）
- 覆盖多 domain（wangshuai/pattern/climate/ten_god）

---

## 二、验证流程

### 步骤 1: 选取样本（20-50条）
- 从 FOR-DAZI 385 条中选取
- 确保覆盖 primitive/composite/local 三种类型
- 确保有明确条件和无条件的对比

### 步骤 2: 定义 Primitive Schema
```python
@dataclass(frozen=True)
class Primitive:
    """Primitive 最小验证单元"""
    evidence_id: str                      # 来源证据ID
    source_text: str                      # 原典原文
    subject: str                          # 判断主体
    domain: str                           # 辨证域
    primitive_name: str                   # Primitive名称
    conditions: list[Condition]          # 条件列表
    authorization_level: str             # CLASSICAL_EXPLICIT/IMPLICIT/UNRESOLVED
    verification_status: str             # PENDING/VERIFIED/INVALID
```

### 步骤 3: 定义 Condition Schema
```python
@dataclass(frozen=True)
class Condition:
    """Condition 最小验证单元"""
    condition_type: str                  # NECESSARY/SUFFICIENT/SUPPORTING/CONSTRAINING/BLOCKING
    feature_ref: str                     # 对应 D1FeatureResult 字段
    operator: str                        # >/</==/contains/exists
    value: Any                           # 阈值或预期值
    evidence_ref: str                    # 支撑证据
    authorization: str                   # 原典授权文本
```

### 步骤 4: 验证链路
对每条样本执行：
```
Evidence (原典原文)
    ↓
Primitive (提取最小规则单元)
    ↓
Condition (转化为可计算条件)
    ↓
Local Judgment (在 D1FeatureResult 上验证)
    ↓
Authorization (证明授权链条完整)
```

### 步骤 5: 输出报告
- 通过/失败/待定 分类统计
- 每个失败项的原因分析
- 未被验证的 Primitive 标记为 UNVERIFIED

---

## 三、具体执行计划

### Phase 1: 样本选取（30分钟）
- 从 385 条中选取 30 条样本
- 覆盖 5 大经典
- 覆盖 4 大 domain

### Phase 2: Schema 定义（1小时）
- 定义 Primitive/Condition 数据结构
- 定义验证接口
- 编写最小验证脚本

### Phase 3: 验证执行（2小时）
- 逐条验证 Evidence → Primitive → Condition → Judgment
- 记录通过/失败/待定
- 分析问题原因

### Phase 4: 报告输出（30分钟）
- 汇总验证结果
- 生成 T3 状态报告
- 提交 GitHub

---

## 四、成功标准

✅ 全部通过：30/30 Evidence 完整验证  
⚠️ 部分通过：20-29/30 验证通过，需分析失败原因  
❌ 验证失败：<20/30 验证通过，需重新设计 Schema

---

## 五、输出文件

- `data/t3_primitive_validation_samples.json` — 样本数据
- `src/tongshu/canonical/primitive.py` — Primitive Schema
- `src/tongshu/canonical/condition.py` — Condition Schema
- `scripts/t3_primitive_validation.py` — 验证脚本
- `docs/T3_PRIMITIVE_VALIDATION_REPORT.md` — 验证报告
