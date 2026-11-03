# Phase A Governance Backlog

## P-A-GOV-01: Provenance Immutable / Historical Audit
**状态**: 🟡 尚未实现  
**优先级**: Medium  
**创建日期**: 2026-09-02  

### 问题描述
PM-001 / PM-004 规则目前无法真正执行历史不可变性检查：
- 当前 validator 只检查文件当前状态
- 无法检测 commit 历史中的 provenance 升级（如 B→A）
- 文件被覆盖后原始 provenance 丢失

### 解决方案（未来）
```
方案 A: Git-based provenance audit
- 使用 git log --follow 追踪文件历史
- 比较不同 commit 的 provenance_layer
- 检测非法升级操作

方案 B: Immutable manifest + hash
- 创建 Evidence ID 与 first_seen_provenance 绑定
- 每次修改生成新 Evidence ID
- 原 Evidence 标记 SUPERSEDED/INVALIDATED

方案 C: Provenance ledger
- 维护独立的 provenance 变更记录表
- 记录每次 provenance 修改的操作人/时间/原因
- 需要人工审核才能修改
```

### 影响范围
- 不影响当前 Phase A 证据收集
- 在五经+盲派整体冻结候选时实现

---

## P-A-GOV-02: Validator Portable Path + CI Integration
**状态**: 🟡 需修复  
**优先级**: Low  
**创建日期**: 2026-09-02  

### 问题描述
`scripts/validate_provenance.py` 中硬编码了 Windows 路径：
```python
evidence_dir = Path('C:/Users/wisdom/wisdom/data/evidence/blind_seg')
```

这会导致：
- 换机器失效
- CI/CD 环境失效
- Claude/OpenCode 多 agent 环境失效

### 解决方案
```python
# 方案 1: 相对路径
evidence_dir = Path(__file__).resolve().parent.parent / "data/evidence/blind_seg"

# 方案 2: CLI 参数
import argparse
parser = argparse.ArgumentParser()
parser.add_argument('--evidence-dir', default='data/evidence/blind_seg')
args = parser.parse_args()

# 方案 3: 环境变量
evidence_dir = Path(os.environ.get('EVIDENCE_DIR', 'data/evidence/blind_seg'))
```

### 影响范围
- 工程性问题，不影响数据本身
- 建议在 Phase A 完成后统一修复

---

## 当前 Phase A 状态
```
证据总数: 30条
Topic覆盖: 13/13 (100%)
Layer分布: A=2, B=25, C=3
Validator: PASS (0 errors, 0 warnings)
独立性: ✅ 无交叉污染
Provenance Monotonicity: 已建立规则，历史审计尚未实现
```

## 下一步行动
1. 继续扩充盲派辨证据（有真实出处）
2. 确保每条 Evidence 符合 PM-003 分层要求
3. 不进入 Phase B（等待裁决）
4. 完成 Phase A 后启动 Multi-AI Final Verification
