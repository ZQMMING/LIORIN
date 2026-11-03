# TASK-K2G-P3 · Phase 3 启动任务单

**依据**: K2G Development Spec V1.0 P3-P15
**前置**: P0✅ P1✅ P2✅ (Legacy Lexicon Inventory已完成)
**性质**: State Engine 核心实现

---

## 当前状态

| 阶段 | 状态 | 说明 |
|------|------|------|
| P0 Architecture Freeze | ✅ | K2G_ARCHITECTURE_V1.0.md 已冻结 |
| P1 Schema / DB / Registry | ✅ | models.py + registry_loader.py + schema/ |
| P2 Legacy Lexicon Inventory | ✅ | LEGACY_LEXICON_INVENTORY_DRAFT.md 已生成 |
| **P3 Concept Normalization** | ⏳ | **当前任务** |
| P4 Semantic Registry | ⏳ | 待P3完成后 |
| P5 Mapping Registry | ⏳ | 待P4完成后 |
| P6 Relation Registry | ⏳ | 待P5完成后 |
| P7 Context Registry | ⏳ | 需新建 (当前为空) |
| P8 State Engine | ⏳ | 需新建 (当前为空) |
| P9-D15 | ⏳ | 后续阶段 |

---

## P3: Concept Normalization 任务

### 目标
建立五大体系概念的统一 ID 体系，为后续 Registry 构建奠定基础。

### 输入来源
1. `D:/today/开发资料/参考资料/词库V4.0/02_BAZI — 八字词库/*.md` (18文件)
2. `D:/today/开发资料/参考资料/词库V4.0/03_ZIWEI — 紫微词库/*.md` (12文件)
3. `D:/today/开发资料/参考资料/词库V4.0/01_CALENDAR — 黄历词库/*.md` (10文件)
4. `D:/today/开发资料/参考资料/词库V4.0/11_DELIVERABLES — 交付物层/02_TRADITIONAL_TERMS.json` (26条)

### 产出物
```
backend/data/k2g/concepts/
├── bazi_concepts.yaml      (十神、五行、日主等)
├── ziwei_concepts.yaml     (星曜、宫位等)
├── calendar_concepts.yaml  (神煞、宜忌等)
└── concept_registry.yaml   (统一索引)
```

### 验收标准
1. 每个概念有唯一 `concept_id` (格式: `{DOMAIN}_{TYPE}_{SEQ}`)
2. 每个概念有 `source_refs` 指向原典
3. 覆盖十大神煞、十二宫位、五行生克核心概念
4. `verification_status` 全部为 DRAFT

---

## P4: Semantic Registry 任务

### 目标
创建核心语义库（不少于100条），覆盖六大主题。

### 输入来源
1. `D:/today/开发资料/参考资料/词库V4.0/04_PRODUCT_SEMANTICS — 产品语义层/*.md`
2. `D:/today/docs/k2g/K2G_SEMANTIC_产品语义层六大主题词条集.md`
3. P3 产出

### 产出物
```
backend/data/k2g/semantics/
├── theme_xing_semantics.yaml    (行/行动主题)
├── theme_shi_semantics.yaml     (事/事业主题)
├── theme_ren_semantics.yaml     (人/关系主题)
├── theme_ju_semantics.yaml      (居/稳定主题)
├── theme_yang_semantics.yaml    (养/健康主题)
├── theme_shi_t_semantics.yaml   (时/时机主题)
└── semantic_registry.yaml
```

### 验收标准
1. 覆盖六大主题 (XING/SHI/REN/JU/YANG/SHI_T)
2. 每条语义有 positive/negative keywords
3. 每条语义有 forbidden_claims
4. 无循环引用
5. 总数 ≥100 条

---

## P7: Context Registry 任务 (当前缺失，需优先)

### 目标
定义场景上下文，连接语义与产品需求。

### 产出物
```
backend/data/k2g/contexts/
├── context_career.yaml          (事业与工作)
├── context_relationship.yaml    (人际与情感)
├── context_health.yaml          (健康与修养)
├── context_finance.yaml         (财务与资源)
├── context_family.yaml          (家庭与六亲)
└── context_daily.yaml           (日常与综合)
```

---

## BOUNDARY

- 禁止修改 `backend/src/tongshu/engines/` 下任何算法代码
- 禁止修改现有 evidence/rules 数据
- 禁止使用 AI 生成传统知识（只整理、不发明）
- 所有新条目 status 必须为 DRAFT

---

## COMMIT 规范

```
feat(P3): K2G concept normalization - 五大体系概念统一ID体系
feat(P4): K2G semantic registry - 六大主题语义库100+条
feat(P7): K2G context registry - 产品上下文定义
```

---

## 执行顺序

1. **先执行 P3** (Concept Normalization) - 建立概念基础
2. **并行执行 P4 + P7** (Semantic + Context) - 语义与上下文
3. **然后执行 P5** (Mapping Registry) - 概念→语义映射
4. **然后执行 P6** (Relation Registry) - 关系融合规则
5. **最后执行 P8** (State Engine) - 状态融合引擎

---

*Hermes PM Agent 派发*
