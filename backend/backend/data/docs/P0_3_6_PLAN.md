# P0-3.6 工作计划：Primitive/Condition 正式 Schema + Authorization 边界

**目标**: 建立机器可执行的 Primitive/Condition 契约，区分 UNRESOLVED vs VERIFIED 状态

---

## 一、背景

P0-3.5 验证结果：
- 9 条 C 类证据：4 条 VERIFIED，5 条 UNRESOLVED
- 没有替古人补条件 ✅
- 验证链路完整：原典 → Evidence → Primitive → Condition → Local Judgment ✅

但报告表述需要收紧：
- UNRESOLVED 不是"完整可执行 Judgment"
- 必须区分 STRUCTURED / EXECUTABLE / VERIFIED / UNRESOLVED

---

## 二、核心问题

当前代码中 UNRESOLVED 和 VERIFIED 的边界不够清晰：
- UNRESOLVED 能否产生 Judgment？
- VERIFIED 如何授权进入 Rule Resolver？

需要在机器契约层面明确：

```
UNRESOLVED
→ 可以保存
→ 可以检索
→ 可以继续研究
→ 禁止产生 Judgment

VERIFIED
→ 可以进入 Rule Resolver
→ 才能产生 Local Judgment
```

---

## 三、具体任务

### Phase 1: 定义 Primitive Schema（v2）

```python
@dataclass(frozen=True)
class Condition:
    """Condition 最小验证单元"""
    text: str                              # 条件文本
    condition_type: str                    # NECESSARY/SUFFICIENT/SUPPORTING/CONSTRAINING/BLOCKING
    status: ConditionStatus                # RESOLVED/UNRESOLVED/IMPLICIT/COMPOSITE
    evidence_ref: str                      # 支撑证据 ID
    authorization: str                     # 原典授权文本
    feature_ref: Optional[str] = None      # 对应 Feature 字段（可为 None）
    operator: Optional[str] = None         # >/</==/contains/exists（可为 None）
    value: Optional[Any] = None            # 阈值（可为 None）

@dataclass(frozen=True)
class Primitive:
    """Primitive 最小验证单元"""
    evidence_id: str                       # 来源证据 ID
    source_text: str                      # 原典原文
    subject: str                           # 判断主体
    domain: str                            # 辨证域
    primitive_name: str                    # Primitive 名称
    primitive_type: PrimitiveType          # PROPERTY/RELATION/RULE/PATTERN
    conditions: List[Condition]            # 条件列表
    scope: Scope                          # PRIMITIVE/COMPOSITE/LOCAL
    authorization_level: str              # CLASSICAL_EXPLICIT/IMPLICIT/UNRESOLVED
    verification_status: VerificationStatus  # STRUCTURED/VERIFIED/UNRESOLVED/INVALID
    local_judgment: Optional[str] = None  # 局部判断结果（仅 VERIFIED 时填充）
```

### Phase 2: 定义 VerificationStatus 枚举

```python
class VerificationStatus(str, Enum):
    """验证状态"""
    STRUCTURED = "STRUCTURED"     # 已结构化，但未验证条件
    VERIFIED = "VERIFIED"         # 条件已验证，可执行
    UNRESOLVED = "UNRESOLVED"     # 条件无法解析，禁止授权
    INVALID = "INVALID"           # 结构化失败

    @property
    def is_executable(self) -> bool:
        return self == VerificationStatus.VERIFIED

    @property
    def can_authorize_judgment(self) -> bool:
        """是否可以授权 Judgment"""
        return self == VerificationStatus.VERIFIED
```

### Phase 3: 定义 Authorization 边界

```python
class AuthorizationLevel(str, Enum):
    """授权级别"""
    CLASSICAL_EXPLICIT = "CLASSICAL_EXPLICIT"   # 原典明确授权
    CLASSICAL_IMPLICIT = "CLASSICAL_IMPLICIT"   # 原典隐含授权
    UNRESOLVED = "UNRESOLVED"                   # 未解析，禁止授权

def check_authorization(primitive: Primitive) -> bool:
    """检查 Primitive 是否获得授权"""
    if primitive.authorization_level == AuthorizationLevel.UNRESOLVED:
        return False
    if primitive.verification_status != VerificationStatus.VERIFIED:
        return False
    return True
```

### Phase 4: 修改 Rule Resolver

```python
def resolve_local_judgment(primitive: Primitive) -> Optional[str]:
    """从 Primitive 推导 Local Judgment
    
    关键：仅当 VERIFIED 时才产生 Judgment
    """
    if not check_authorization(primitive):
        return None  # 未授权，返回 None
    
    # 只有 VERIFIED 才产生 Judgment
    if primitive.verification_status != VerificationStatus.VERIFIED:
        return None
    
    # 原有的推导逻辑
    return generate_judgment(primitive)
```

### Phase 5: 更新验证脚本

对 9 条 C 类证据重新验证：
- STRUCTURED：已结构化，但条件未解析
- VERIFIED：条件已验证，可产生 Judgment
- UNRESOLVED：保留，禁止授权

---

## 四、禁止事项

❌ 不要规模化生产 284 条 Primitive  
❌ 不要做 Composite Judgment  
❌ 不要做"身强/身弱总公式"  
❌ 不要强行解析 5 条 UNRESOLVED  
❌ 不要用 AI 猜隐含条件

---

## 五、成功标准

✅ Primitive Schema v2 定义清晰  
✅ VerificationStatus 枚举定义明确  
✅ Authorization 边界固化到代码  
✅ Rule Resolver 仅接受 VERIFIED  
✅ 9 条 C 类证据重新验证通过

---

**等待 Gemini 裁决后开始执行**
