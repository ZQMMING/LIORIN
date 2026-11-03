# V1.3 A2.6 — Holdout Freezing Protocol

**日期**: 2026-08-22
**类型**: READ-ONLY AUDIT
**状态**: FINAL

---

## 原则声明

本文档定义 HOLDOUT 数据集的永久冻结机制。
禁止修改任何代码或数据集。

---

## 一、Holdout Guardian 角色定义

```text
HOLDOUT GUARDIAN:
├── 职责: 监督 HOLDOUT 冻结状态
├── 权限: 只读访问 HOLDOUT 数据集
├── 报告: 定期检查冻结状态
└── 警告: 发现任何试图修改的行为立即报告
```

---

## 二、冻结触发条件

```text
FROZEN TRIGGER CONDITIONS:
├── 条件 1: BLIND 数据集正式投入使用
│   └── 触发: 第一个正式 Accuracy 评估完成
│
├── 条件 2: HOLDOUT 数据集构建完成
│   └── 触发: 所有案例通过 Source Qualification
│
└── 条件 3: Gate Keeper 批准冻结
    └── 触发: A2.7 Gate 签字
```

---

## 三、冻结状态管理

### 3.1 冻结前检查清单

```text
PRE-FREEZE CHECKLIST:
├── [ ] 所有案例通过 Source Qualification
├── [ ] 所有案例通过 Leakage Classification
├── [ ] 所有案例时间精度声明完整
├── [ ] 所有案例映射到 G1 本体
├── [ ] 去重检查通过 (L05/L06)
├── [ ] 质量评分 ≥ Tier 1 标准
├── [ ] 元数据完整
└── [ ] Guardian 签字确认
```

### 3.2 冻结后约束

```text
POST-FREEZE CONSTRAINTS:
├── 禁止事项:
│   ├── ❌ 不得添加新案例
│   ├── ❌ 不得修改现有案例
│   ├── ❌ 不得删除案例
│   ├── ❌ 不得改变事件标签
│   ├── ❌ 不得调整时间字段
│   └── ❌ 不得重新分类泄漏状态
│
├── 允许事项:
│   ├── ✅ 只读访问
│   ├── ✅ 复制备份
│   ├── ✅ 用于最终独立验证
│   └── ✅ 审计日志记录
│
└── 异常处理:
    └── 如发现严重错误，必须提交 Guardian + Gate Keeper 联合审批
```

---

## 四、冻结执行步骤

```text
FROZEN EXECUTION STEPS:
┌──────────────────────────────────────────────────────────────────┐
│ Step 1: Final Quality Verification                               │
│   ├── 执行 A2.7 Gate 全部检查项                                   │
│   ├── 确认所有数据质量符合要求                                     │
│   └── 生成最终质量报告                                             │
└──────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────────┐
│ Step 2: Cryptographic Hashing                                    │
│   ├── 对数据集文件计算 SHA-256 hash                               │
│   ├── 记录 hash 值到元数据                                        │
│   └── 建立哈希链式验证                                            │
└──────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────────┐
│ Step 3: Immutable Storage                                        │
│   ├── 移动到只读存储位置                                            │
│   ├── 设置文件系统权限 (chmod 444)                                │
│   └── 创建备份 (离线/云存储)                                        │
└──────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────────┐
│ Step 4: Guardian Assignment                                      │
│   ├── 指定 Holdout Guardian                                       │
│   ├── 传达冻结状态和约束                                            │
│   └── 建立定期检查机制                                              │
└──────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────────┐
│ Step 5: Documentation                                            │
│   ├── 生成冻结报告                                                  │
│   ├── 记录冻结时间和原因                                            │
│   └── 归档所有相关文档                                              │
└──────────────────────────────────────────────────────────────────┘
```

---

## 五、解冻条件 (极端情况)

```text
THAW CONDITIONS (EXTREME CASES ONLY):
├── 条件: 发现系统性错误影响所有数据
│   └── 处理: 重新构建 HOLDOUT 数据集
│
├── 条件: 法律/许可问题
│   └── 处理: 移除相关问题案例，重新冻结
│
└── 决策: 必须 Gate Keeper + Guardian 联合审批
    └── 记录解冻原因和时间
```

---

## 六、HOLDOUT 访问日志模板

```yaml
access_log:
  timestamp: "ISO8601"
  accessor: "str"
  purpose: "str"                    # 访问目的
  operation: "READ"                 # 操作类型 (仅允许 READ)
  result: "SUCCESS" | "DENIED"      # 结果
  notes: "str"                      # 备注
  
  # 示例
  - timestamp: "2026-08-22T10:00:00Z"
    accessor: "Gate Keeper"
    purpose: "Pre-freeze verification"
    operation: "READ"
    result: "SUCCESS"
    notes: "All checks passed"
  
  - timestamp: "2026-08-22T15:00:00Z"
    accessor: "Unknown"
    purpose: "Trying to modify"
    operation: "WRITE"
    result: "DENIED"
    notes: "Permission denied - frozen"
```

---

## 七、冻结状态检查脚本

```python
"""
HOLDOUT FROZEN STATUS CHECKER
Usage: python check_holdout_frozen.py
"""

import hashlib
import json
from pathlib import Path
from datetime import datetime

HOLDOUT_PATH = Path("dataset/accuracy/holdout_frozen.jsonl")
META_PATH = Path("dataset/accuracy/metadata/holdout_frozen_meta.json")

def compute_hash(filepath):
    sha256 = hashlib.sha256()
    with open(filepath, 'rb') as f:
        sha256.update(f.read())
    return sha256.hexdigest()

def check_frozen_status():
    # Check file exists
    if not HOLDOUT_PATH.exists():
        return {"status": "ERROR", "message": "Holdout file not found"}
    
    # Check permissions (should be read-only)
    perms = oct(HOLDOUT_PATH.stat().st_mode)[-3:]
    is_readonly = perms == "444"
    
    # Verify hash
    current_hash = compute_hash(HOLDOUT_PATH)
    
    # Load metadata
    if META_PATH.exists():
        with open(META_PATH) as f:
            meta = json.load(f)
        stored_hash = meta.get("hash")
        hash_match = current_hash == stored_hash
    else:
        hash_match = False
        meta = {}
    
    return {
        "status": "FROZEN" if (is_readonly and hash_match) else "COMPROMISED",
        "is_readonly": is_readonly,
        "hash_matches": hash_match,
        "current_hash": current_hash,
        "last_verified": meta.get("frozen_at"),
        "guardian": meta.get("guardian"),
    }

if __name__ == "__main__":
    result = check_frozen_status()
    print(json.dumps(result, indent=2))
```

---

## 八、文档结构

```text
docs/accuracy/
├── V13_A26_HOLDOUT_PROTOCOL.md      (本文件)
└── dataset/accuracy/metadata/
    ├── holdout_frozen_meta.json     # 冻结元数据
    └── access_log.json              # 访问日志
```

---

**报告结束**
**下一步**: A2.7 Gate Audit
