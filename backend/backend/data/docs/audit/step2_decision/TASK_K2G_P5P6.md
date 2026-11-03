# TASK-K2G-P5P6 · Phase 3 后续任务单

**依据**: K2G Development Spec V1.0 P5-P6
**前置**: P3✅ P4✅ P7✅
**性质**: 核心映射与关系融合规则

---

## P5: Mapping Registry 映射注册表

### 目标
建立五大体系 → 语义的映射（每体系不少于30条）

### 输入来源
1. `D:/today/backend/src/tongshu/k2g/concepts/` (P3产出)
2. `D:/today/backend/src/tongshu/k2g/semantics/` (P4产出)
3. `D:/today/开发资料/参考资料/词库V4.0/04_MAPPING_REGISTRY.json` (已有156条)

### 产出物
```
D:/today/backend/src/tongshu/k2g/mappings/
├── bazi_mappings.yaml      (八字→语义映射)
├── ziwei_mappings.yaml     (紫微→语义映射)
├── calendar_mappings.yaml  (黄历→语义映射)
└── mapping_registry.yaml   (索引)
```

### 验收标准
- 每个Mapping有 ≥1 条Evidence引用
- 每个Mapping有conflict_resolution策略
- 覆盖十大神煞、十二宫位、五行生克、四化等核心概念
- 总数 ≥100 条

---

## P6: Relation Registry 关系融合注册表

### 目标
核心关系规则（不少于20条），支持9种关系类型

### 输入来源
1. `D:/today/backend/src/tongshu/k2g/semantics/` (P4产出)
2. `D:/today/开发资料/参考资料/词库V4.0/05_RELATIONAL — 关系映射层/*.md`

### 产出物
```
D:/today/backend/src/tongshu/k2g/relations/
├── relation_registry.yaml
└── relation_rules.yaml
```

### 验收标准
- 覆盖9种关系类型: SUPPORT/CONTRADICT/QUALIFY/AMPLIFY/REDUCE/COMPLEMENT/CONFLICT/SEQUENCE/CONDITION
- 每条关系有conditions和fallback
- 无逻辑冲突

---

## BOUNDARY
- 禁止修改P3/P4/P7已完成的文件
- 禁止发明传统规则，只整理现有知识
- 所有新条目status必须为DRAFT

---

*Hermes PM Agent 派发*
