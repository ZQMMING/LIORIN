# 🔴 P0 紧急：紫微引擎架构缺陷 - FrozenZiweiChart 缺失

**发现时间**: 2026-09-06 18:55  
**严重级别**: 🔴 P0-CRITICAL  
**问题类型**: 迁移遗漏（架构契约未实现）

---

## 核心问题

**shuntian 的模块引用了 `FrozenZiweiChart`，但 `ziwei_engine.py` 中未定义此类型。**

### 错误信息
```python
ImportError: cannot import name 'FrozenZiweiChart' 
from 'tongshu.engines.ziwei_engine' (D:\shuntian\src\tongshu\engines\ziwei_engine.py)
```

### 影响范围
- ✅ `ziwei/rules/feixing_rule_graph.py` - 导入失败
- ✅ `ziwei/rules/method_graphs.py` - 导入失败  
- ✅ `tests/test_ziwei_feixing_production.py` - 测试失败
- ✅ `tests/test_ziwei_feixing_rule_graph.py` - 测试失败
- ✅ `tests/test_ziwei_palace_resolution.py` - 测试失败

---

## 代码对比

### shuntian-NEW（正确实现）
```python
@dataclass(frozen=True)
class FrozenZiweiChart:
    """紫微计算契约：纯计算事实，不含诊断语义。"""
    soul_palace_main_star: str = ""
    soul_palace_main_stars: list = field(default_factory=list)
    soul_palace_sihua: list = field(default_factory=list)
    palace_data: dict = field(default_factory=dict)
    daily_luck_palace: str = ""
    source: str = "stub"
    
    def to_dict(self) -> dict: ...
    @classmethod
    def from_dict(cls, d: dict) -> "FrozenZiweiChart": ...

# 向后兼容别名
ZiweiChart = FrozenZiweiChart
```

### shuntian（当前状态 - 有缺陷）
```python
@dataclass  # ❌ 缺少 frozen=True
class ZiweiChart:
    soul_palace_main_star: str = ""
    soul_palace_main_stars: list = field(default_factory=list)
    soul_palace_sihua: list = field(default_factory=list)
    palace_data: dict = field(default_factory=dict)
    daily_luck_palace: str = ""
    source: str = "stub"
    
    def to_dict(self) -> dict: ...
    # ❌ 缺少 from_dict 方法
    # ❌ 缺少 FrozenZiweiChart 别名定义

# ❌ 没有 FrozenZiweiChart 定义
```

---

## 为什么这是 P0？

### 1. 违反架构契约
根据 SHUNTIAN §10 设计原则：
- **Frozen State 模式**是核心架构约束
- `FrozenZiweiChart` 明确区分"计算结果"与"可变状态"
- 缺少此契约会导致计算层污染诊断层

### 2. 依赖注入失败
```python
# feixing_rule_graph.py:21
from ...ziwei_engine import FrozenZiweiChart, GAN_SIHUA
```

### 3. 测试全部失败
所有引用 `FrozenZiweiChart` 的测试都会因导入错误而失败。

---

## 修复方案

### 方案A：最小化修复（推荐）
在 `ziwei_engine.py` 中添加：

```python
# 行 112 附近，现有 ZiweiChart 后添加

@dataclass(frozen=True)
class FrozenZiweiChart:
    """紫微计算契约：纯计算事实，不含诊断语义。
    
    Z2 (2026-09-04): 与 ZiweiChart 等价，但明确标记为 Frozen（不可变契约）。
    供证据层、MethodProfile 消费；计算层不再产出方向/极性/强度。
    """
    soul_palace_main_star: str = ""
    soul_palace_main_stars: list = field(default_factory=list)
    soul_palace_sihua: list = field(default_factory=list)
    palace_data: dict = field(default_factory=dict)
    daily_luck_palace: str = ""
    source: str = "stub"
    
    def to_dict(self) -> dict:
        return {
            "soul_palace_main_star": self.soul_palace_main_star,
            "soul_palace_main_stars": list(self.soul_palace_main_stars),
            "soul_palace_sihua": list(self.soul_palace_sihua),
            "palace_data": self.palace_data,
            "daily_luck_palace": self.daily_luck_palace,
            "source": self.source,
        }
    
    @classmethod
    def from_dict(cls, d: dict) -> "FrozenZiweiChart":
        return cls(
            soul_palace_main_star=d.get("soul_palace_main_star", ""),
            soul_palace_main_stars=tuple(d.get("soul_palace_main_stars", [])),
            soul_palace_sihua=tuple(d.get("soul_palace_sihua", [])),
            palace_data=d.get("palace_data", {}),
            daily_luck_palace=d.get("daily_luck_palace", ""),
            source=d.get("source", "stub"),
        )

# 向后兼容：ZiweiChart 为 FrozenZiweiChart 的同形别名
ZiweiChart = FrozenZiweiChart
```

### 方案B：完整对齐
将 shuntian-NEW 的 ziwei_engine.py 合并到 shuntian。

---

## 建议行动

**立即执行**：
1. 应用方案A的修复
2. 验证导入：`from tongshu.engines.ziwei_engine import FrozenZiweiChart`
3. 运行测试：`pytest tests/test_ziwei_feixing*.py -v`

**后续核查**：
- 检查其他模块是否有类似缺失
- 更新文档说明架构变更

---

## 根因分析

这不是"有意省略"，而是迁移过程中的**架构差异遗漏**：

1. **shuntian-NEW** 已经实现了 `FrozenZiweiChart`（Z2 修复）
2. **shuntian** 仍然使用旧的 `ZiweiChart` 定义
3. 规则模块引用了新接口，但引擎未同步

---

**请立即裁决：是否应用修复方案A？**
