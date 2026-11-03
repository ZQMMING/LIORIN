# 📨 HERMES-DISPATCH: TASK-003 - 移除wang_score阈值判定

---

## 基本信息

**Task ID**: TASK-003  
**Priority**: P0 BLOCKER  
**Owner**: OpenCode (Implementer)  
**Auditor**: Claude (Independent)  
**Parent Task**: STEP3-P0-ISOLATION  

---

## WHY

TASK-001/002已切断调用链并添加标注，现在需要移除wang_score阈值判定逻辑，确保不再产生verdict输出。

---

## WHAT

修改`src/tongshu/engines/strength_engine.py`：

1. **删除或注释掉**:
   - `_WANG_SCORE_THRESHOLD = 2.0` (line 75)
   - `wang_score`计算逻辑 (line 353-358)
   - `strong = wang_score >= _WANG_SCORE_THRESHOLD` (line 396)
   - `verdict = "身强" if strong else "身弱"` (line 397)

2. **保留**:
   - 中间特征计算（得令、得地、得势等）
   - D1StrengthResult数据结构
   - evaluate_strength_features函数（V4隔离层）

3. **修改返回值**:
   - verdict字段设为空字符串""
   - verdict_condition设为"LEGACY_REMOVED"
   - 添加注释说明wang_score不再用于判定

---

## BOUNDARY

- **只修改strength_engine.py**
- **不修改其他文件**
- **不删除calculate逻辑**（保留为RESEARCH参考）
- **不修改测试文件**

---

## ACCEPTANCE CRITERIA

1. ✅ strength_engine.py不再有wang_score阈值判定
2. ✅ evaluate_strength返回空verdict
3. ✅ 代码语法正确
4. ✅ 无其他生产文件受影响

---

## TEST

不需要运行完整测试，只验证strength_engine.py语法正确。

---

**Status**: 等待OpenCode执行后Claude复审