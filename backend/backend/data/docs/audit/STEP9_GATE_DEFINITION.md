# Step 9: Judgment Production Implementation - 门禁定义

**时间**: 2026-08-31  
**阶段**: Phase 6规划  
**依据**: GPT裁决 9d770f6  
**状态**: 🟢 APPROVED

---

## 生产实现范围

### ✅ 允许实现（4条）
```
DTS-JUDG-001: 有病方为贵
ZPZQ-JUDG-002: 合伤存官，遂成贵格
ZPZQ-JUDG-003: 相神无破，贵格已成
ZPZQ-JUDG-004: 相神有伤，立败其格
```

### ❌ 禁止实现（6条）
```
DTS-JUDG-002: HOLD - 不准进入生产
ZPZQ-JUDG-001: HOLD - 不准进入生产
DTS-JUDG-003: PERMANENT REJECT
DTS-JUDG-004: PERMANENT REJECT
其他未经授权的五经断言: 禁止实现
```

---

## 门禁定义

### 门禁1: 授权验证
```
输入: 4个APPROVED Judgment
验证项:
• 原典明确授权 ✅
• Condition→Judgment因果链完整 ✅
• 无L4风险 ✅
• Claude审计通过 ✅
• GPT裁决通过 ✅
输出: 生产授权清单（4/4 APPROVED）
```

### 门禁2: Schema合规
```
验证项:
• judgment_id唯一且连续 ✅
• source_book正确 ✅
• original_text与原典一致 ✅
• text_layer = "ORIGINAL_TEXT" ✅
• production_status = "APPROVED_FOR_PRODUCTION" ✅
输出: Schema合规报告
```

### 门禁3: 无Legacy回流
```
验证项:
• 不得调用evaluate_strength生产路径 ✅
• 不得引用wang_score阈值 ✅
• 不得从Condition自动推导Judgment ✅
• 不得跨层直接推导 ✅
输出: 无Legacy回流声明
```

---

## 生产输出要求

### 输出1: judgment_production.py
```python
"""
Judgment Production Engine - 4条已授权Judgment
"""

class JudgmentProducer:
    """
    仅实现4条APPROVED Judgment:
    - DTS-JUDG-001: 有病方为贵
    - ZPZQ-JUDG-002: 合伤存官，遂成贵格
    - ZPZQ-JUDG-003: 相神无破，贵格已成
    - ZPZQ-JUDG-004: 相神有伤，立败其格
    """
    
    APPROVED_JUDGMENTS = [
        "DTS-JUDG-001",
        "ZPZQ-JUDG-002",
        "ZPZQ-JUDG-003",
        "ZPZQ-JUDG-004"
    ]
    
    def __init__(self):
        self.registry = self._load_registry()
    
    def _load_registry(self):
        """加载judgment_registry_v2.json"""
        pass
    
    def evaluate(self, judgment_id, condition_state):
        """
        评估单个Judgment
        仅允许评估APPROVED的4条
        """
        if judgment_id not in self.APPROVED_JUDGMENTS:
            raise ValueError(f"Judgment {judgment_id} not approved for production")
        # 实现评估逻辑
        pass
```

### 输出2: test_judgment_production.py
```python
"""
测试覆盖4条APPROVED Judgment的生产实现
"""

def test_dts_judg_001():
    """有病方为贵 - 原典明确授权"""
    pass

def test_zpzq_judg_002():
    """合伤存官，遂成贵格 - 原典具体例证"""
    pass

def test_zpzq_judg_003():
    """相神无破，贵格已成 - 原典明确授权"""
    pass

def test_zpzq_judg_004():
    """相神有伤，立败其格 - 原典明确授权"""
    pass
```

### 输出3: production_governance_v2.json
```json
{
  "step": 9,
  "phase": "Judgment Production Implementation",
  "approved_for_production": 4,
  "hold": 2,
  "rejected": 2,
  "rules": [
    "仅实现4条APPROVED Judgment",
    "禁止实现HOLD条目",
    "禁止实现REJECTED条目",
    "禁止实现其他未经授权的五经断言",
    "不得引入L4风险",
    "不得回流Legacy Strength"
  ]
}
```

---

## 执行流程

### Phase 6.1: 定义门禁（当前阶段）
- [x] 门禁1: 授权验证
- [x] 门禁2: Schema合规
- [x] 门禁3: 无Legacy回流
- [x] 生产输出要求
- [x] 执行流程

### Phase 6.2: OpenCode实施（待启动）
- [ ] 创建judgment_production.py
- [ ] 实现4个Judgment评估逻辑
- [ ] 编写测试用例
- [ ] 验证Schema合规

### Phase 6.3: 测试执行（待启动）
- [ ] 运行测试套件
- [ ] 验证1797+测试通过
- [ ] 验证无Legacy回流

### Phase 6.4: Claude独立代码审计（待启动）
- [ ] 审计生产代码
- [ ] 验证无L4风险
- [ ] 验证无Legacy回流
- [ ] 输出审计结果

### Phase 6.5: GPT最终裁决（待启动）
- [ ] 裁决Production Implementation是否通过
- [ ] 确认是否进入Production
- [ ] 输出Final Ruling

---

## 核心原则

> **仅实现4条APPROVED Judgment**
> 
> **禁止实现HOLD和REJECTED条目**
> 
> **禁止实现其他未经授权的五经断言**
> 
> **实现后必须再跑：Production → 测试 → Claude审计 → 检查L4/Legacy → GPT裁决**