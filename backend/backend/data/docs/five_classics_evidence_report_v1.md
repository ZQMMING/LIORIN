# 五经证据整理报告 v1.1

**生成时间**: 2026-09-01 13:55:00 UTC
**总证据数**: 1,412 条
**状态**: 阶段一完成（证据提取）→ 阶段二待启动（交叉验证）

---

## 一、五经证据分布

| 经典 | ID | 证据数 | 主要类型 |
|------|-----|--------|----------|
| 滴天髓 | DTS | 44 | ROOT_PRESENT (10类) |
| 穷通宝鉴 | QTBJ | 1,233 | ADJ (600), TEM (633) |
| 子平真诠 | PZZQ | 10 | YONGSHEN_VALID (3), KEY_CONCEPT (3), ... |
| 三命通会 | SMTH | 8 | KEY_PASSAGE (4), LU, SHW, TIANYI, JIANLU |
| 渊海子平 | YHZP | 117 | DAYMASTER_STRONG (52), TEN_GODS_BALANCE (14), ... |
| **总计** | — | **1,412** | — |

### 详细分布

```
di_tian_sui (44条):
  - ROOT_PRESENT, DAYMASTER_WEAK, WANG_SHUAI, ... 等10类

qiong_tong_bao_jian (1,233条):
  - ADJ (600): 调候相关证据
  - TEM (633): 温度/寒暖相关证据

san_ming_tong_hui (8条):
  - KEY_PASSAGE (4), LU, SHW, TIANYI, JIANLU

yuan_hai_zi_ping (117条):
  - DAYMASTER_STRONG (52): 日主强
  - DAYMASTER_WEAK (11): 日主弱
  - MONTH_BRANCH_DOMINANT (10): 月令主导
  - STRUCTURE_CLEAR (4): 格局清
  - STRUCTURE_MIXED (26): 格局杂
  - TEN_GODS_BALANCE (14): 十神平衡

ziping_zhenquan (10条):
  - YONGSHEN_VALID (3): 用神正当
  - KEY_CONCEPT (3): 关键概念
  - DI_ZHI_SUPPORT (1): 地支支持
  - PATTERN_RESCUE (1): 格局救应
  - TIAN_GAN_SUPPORT (1): 天干支持
  - GEJU_SUCCESS (1): 格局成功
```

---

## 二、证据合同合规性检查

### 必填字段检查

所有证据文件必须包含以下字段：

| 字段 | 状态 | 说明 |
|------|------|------|
| `evidence_id` | ✅ | 格式: E-{CLASSIC}-{TYPE}-{PASSAGE} |
| `classic_id` | ✅ | di_tian_sui / ziping_zhenquan / ... |
| `evidence_type` | ✅ | 证据类型标识 |
| `original_text` | ✅ | 原文引用 |
| `source_locator` | ✅ | 包含 source_hash |
| `authorization_level` | ✅ | PARTIAL |
| `verification_status` | ✅ | UNVERIFIED |

### 格式合规统计

- ✅ 滴天髓: 44/44 符合
- ✅ 穷通宝鉴: 1,233/1,233 符合
- ✅ 子平真诠: 10/10 符合
- ✅ 三命通会: 8/8 符合（已修复格式）
- ✅ 渊海子平: 117/117 符合
- **合计: 1412/1412 (100%) 符合**

---

## 三、INSUFFICIENT_SOURCE 清单

### 当前状态

所有证据均已完成原文提取，无 INSUFFICIENT_SOURCE 标记。

### 数据质量说明

- **子平真诠**: 仅10条证据，覆盖率较低（原始数据446段），建议补充
- **三命通会**: 仅8条证据，覆盖率较低，建议补充

---

## 四、下一步：交叉验证阶段

### 阶段二任务

1. **同概念比对**
   - 财星在五经中的不同表述
   - 官星/杀星的区分标准
   - 用神概念的演变

2. **条件化分析**
   - 同一规则在不同条件下的差异
   - 例外情况的识别
   - 适用范围的限定

3. **互补矩阵构建**
   - 证据关系矩阵
   - 条件/范围矩阵
   - 冲突解决规则

### 输出物

- [ ] 五经统一证据索引 (`data/evidence/unified_index.json`)
- [ ] 证据关系矩阵 (`docs/cross_classical_relationship_matrix.md`)
- [ ] 条件/范围矩阵 (`docs/condition_scope_matrix.md`)
- [ ] INSUFFICIENT_SOURCE 清单更新
- [ ] Candidate Evidence 列表

---

## 五、技术说明

### 证据ID格式

```
E-{CLASSIC_CODE}-{TYPE}-{PASSAGE_ID}
```

示例：
- `E-DTS-101-001` → 滴天髓, 类型101, passage 001
- `E-YHZP-DAYMASTER_STRONG-001` → 渊海子平, 日主强, passage 001

### 来源哈希

每条证据的 `source_locator.source_hash` 由原文计算生成：

```python
import hashlib
hashlib.sha256(original_text.encode('utf-8')).hexdigest()
```

---

## 六、文件位置

```
data/evidence/
├── _unified_summary.json          # 统一汇总
├── di_tian_sui/                   # 滴天髓证据 (44条)
│   ├── E-DTS-101-001.json
│   └── ...
├── qiong_tong_bao_jian/           # 穷通宝鉴证据 (1,233条)
│   ├── E-QTBJ-ADJ-001.json
│   └── ...
├── san_ming_tong_hui/             # 三命通会证据 (8条)
│   └── ...
├── yuan_hai_zi_ping/              # 渊海子平证据 (117条)
│   ├── E-YHZP-001-001.json
│   └── ...
├── ziping_zhenquan/               # 子平真诠证据 (10条)
│   ├── E-ZPZ-YONGSHEN_VALID-001.json
│   └── ...
└── _insufficient_source.json      # 缺失来源标记

docs/
└── five_classics_evidence_contract.md  # 证据合同规范
```

---

**报告生成**: Hermes 总协调器
**阶段**: 阶段一（证据提取）完成 → 阶段二（交叉验证）待启动
