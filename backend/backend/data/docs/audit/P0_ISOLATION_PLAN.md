# 🔴 P0 BLOCKER 隔离方案

**时间**: 2026-08-31  
**状态**: 待Claude审计确认后执行

---

## 必须隔离的内容

### 1. wang_score 生产路径

**当前调用链**:
```
strength_engine.py
  ↓ evaluate_strength()
    ↓ annual_event_evaluator.py:37
    ↓ judgment_engine.py:41
    ↓ health_signals.py:99
```

**隔离方案**:
- [ ] 从production verdict chain移除
- [ ] 保留为LEGACY/RESEARCH ONLY
- [ ] 添加明确的DEPRECATED注释
- [ ] 确认所有import断开

---

### 2. threshold 阈值判定

**当前代码**:
```python
_WANG_SCORE_THRESHOLD = 2.0
if wang_score >= _WANG_SCORE_THRESHOLD:
    verdict = "身强"
else:
    verdict = "身弱"
```

**隔离方案**:
- [ ] 移除threshold判定逻辑
- [ ] 保留计算但不用于verdict
- [ ] 添加警告：此计算仅为RESEARCH用途

---

### 3. 身强/身弱 verdict

**当前状态**: 仍作为最终授权依据

**隔离方案**:
- [ ] 不再作为Production Verdict
- [ ] 改为Evidence layer的参考信息
- [ ] 最终判断必须由五经辨证完成

---

## 执行顺序

1. **STEP 1 Claude审计** - 确认所有调用路径
2. **STEP 2 Hermes裁定** - 确定KEEP/FIX/REMOVE
3. **STEP 3 OpenCode实现** - 执行隔离
4. **STEP 4 Claude复审** - 确认隔离完成
5. **STEP 5 验证测试** - 确保无回归
6. **STEP 6 GPT裁决** - 确认P0解决

---

## 禁止事项

❌ 不得删除strength_engine.py（保留历史研究价值）  
❌ 不得修改五经辨证核心逻辑  
❌ 不得绕过审计直接修复  
❌ 不得继续使用wang_score作为verdict依据  

---

**状态**: 等待Claude审计确认后执行隔离