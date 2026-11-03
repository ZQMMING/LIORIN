# Judgment Candidate Extraction - 原典挖掘计划

**时间**: 2026-08-31  
**阶段**: Step 7 Judgment提取启动  
**依据**: GPT裁决 755aaa2  
**状态**: 🟢 APPROVED启动

---

## 核心原则（GPT裁决明确）

### 禁止从9个Condition硬挖
```
❌ 从DTS-COND-006/010/002... → 推导Judgment
原因: 这些Condition都是定义性的，无事件推断
```

### 正确做法：重新从五部经典搜索
```
✅ 从五部经典原文搜索"若X则Y"结构
✅ 找到明确的"条件→结果"因果关系
✅ 提取Judgment Candidate（非当前9个Condition）
```

---

## Judgment模式识别

### 允许的模式（原典明确授权）
```
模式1: 若X → 则Y
示例: "若成格，则主贵"

模式2: X成 → 主Y
示例: "格局成，主贵显"

模式3: X见 → 主Y
示例: "财星见，主富"

模式4: X逢 → 某结果
示例: "逢禄马，主发达"

模式5: 若X破 → 则Y凶
示例: "若破格，则主贫"
```

### 禁止的模式（工程推断）
```
❌ Condition A + Condition B → 自动推断C
❌ 把"宜/喜"包装成"必"
❌ 从定义性Condition推导事件
❌ 跨层直接推导（Primitive→Judgment）
```

---

## 五部经典搜索策略

### 1. 《滴天髓》
**搜索关键词**:
- "若...则..."
- "...成...主..."
- "...见...主..."
- "...逢...则..."
- "有病方为贵，无病怕无根"
- "五阳从气不从势，五阴从势不顾情"

**预期Judgment类型**:
- 从格判断
- 破格救应
- 旺衰判断

### 2. 《子平真诠》
**搜索关键词**:
- "格局成...主..."
- "用神...见...则..."
- "...破...则..."
- "辅佐用神..."
- "护用之神..."

**预期Judgment类型**:
- 成格判断
- 破格判断
- 救应判断

### 3. 《穷通宝鉴》
**搜索关键词**:
- "宜...忌..."
- "...用...方..."
- "春木...宜..."
- "夏火...忌..."

**注意**: 这类多为建议性描述，需严格区分"宜/忌"vs"必/否"

### 4. 《三命通会》
**搜索关键词**:
- "...总论"
- "...性质..."
- "...主..."
- "...若...则..."

**预期Judgment类型**:
- 干支总论中的事件判断

### 5. 《渊海子平》
**搜索关键词**:
- "若...则..."
- "...成...主..."
- "十干化合..."
- "地支相合..."

**预期Judgment类型**:
- 合化判断
- 格局判断

---

## 提取规范

### Judgment Candidate格式
```json
{
  "judgment_id": "DTS-JUDG-001",
  "source_book": "滴天髓",
  "source_section": "通神论",
  "original_text": "有病方为贵，无病怕无根。",
  "condition_part": "有病（有症结）",
  "judgment_part": "方为贵（才能显贵）",
  "causal_relationship": "原典明确说'有病→贵'",
  "text_layer": "ORIGINAL_TEXT",
  "confidence": "HIGH",
  "risk_flags": [],
  "status": "CANDIDATE"
}
```

### 关键验证点
1. **原典是否明确说出"若X则Y"？**
2. **是否有完整的Condition-Result结构？**
3. **是否只是建议性描述（宜/忌）而非判断性描述（必/否）？**
4. **是否涉及L4 Strength风险？**

---

## 执行流程

### Phase 1: 原典搜索（当前）
- [ ] 搜索《滴天髓》中的"若X则Y"结构
- [ ] 搜索《子平真诠》中的格局判断
- [ ] 搜索《穷通宝鉴》中的宜忌判断
- [ ] 搜索《三命通会》中的干支总论
- [ ] 搜索《渊海子平》中的合化判断

### Phase 2: 提取Judgment Candidate
- [ ] 对每个找到的段落提取Judgment Candidate
- [ ] 标注Condition部分和Judgment部分
- [ ] 验证原典是否明确授权

### Phase 3: Red-Team审查
- [ ] 检查是否把建议包装成判断
- [ ] 检查是否有工程推断
- [ ] 检查是否有L4风险

### Phase 4: Claude独立审计
- [ ] 验证原典是否真正授权Judgment
- [ ] 验证无工程推断

### Phase 5: GPT裁决
- [ ] 最终裁决哪些Judgment进入Production

---

## 输出文件

1. `docs/audit/JUDGMENT_CANDIDATE_EXTRACTION_PLAN.md` - 本文件
2. `data/canonical/judgment_candidate_pool.json` - Judgment候选池
3. `docs/audit/JUDGMENT_REDTTEAM_REPORT.md` - Red-Team报告
4. `docs/audit/CLAUDE_AUDIT_JUDGMENT_RESULT.md` - Claude审计结果
5. `docs/audit/GPT_RULING_JUDGMENT_FINAL.md` - GPT最终裁决

---

## 时间线

### 当前（Phase 1）
- ⏳ 原典搜索中

### 下一步（Phase 2-5）
- 🔲 Judgment Candidate提取
- 🔲 Red-Team审查
- 🔲 Claude独立审计
- 🔲 GPT裁决

---

## 核心原则重申

> **不是从Condition硬挖Judgment**
> 
> **而是从原典搜索明确的"条件→结果"结构**
> 
> **只有原典明确授权的Judgment才能进入Production**