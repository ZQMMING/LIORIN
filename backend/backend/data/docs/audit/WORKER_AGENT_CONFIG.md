# Worker Agent 配置 - 五书并行生产

**时间**: 2026-08-31  
**依据**: GPT裁决 455db5d  
**状态**: 🟢 APPROVED启动

---

## Worker 配置

### WORKER-DTS: 《滴天髓》Worker
```yaml
agent_id: WORKER-DTS
source_book: 滴天髓
target_sections:
  - 通神论·天道篇
  - 通神论·地道篇
  - 通神论·人论篇
  - 通神论·天干篇
  - 通神论·地支篇
  - 十干赋
  - 十二支赋
output_target: 25个Primitive Candidate
schema_version: V3
output_file: data/canonical/candidates_worker_dts.json
```

### WORKER-ZPZQ: 《子平真诠》Worker
```yaml
agent_id: WORKER-ZPZQ
source_book: 子平真诠
target_sections:
  - 论格局
  - 论用神
  - 论相神
  - 论杂格
output_target: 25个Primitive Candidate
schema_version: V3
output_file: data/canonical/candidates_worker_zpzq.json
```

### WORKER-QTBJ: 《穷通宝鉴》Worker
```yaml
agent_id: WORKER-QTBJ
source_book: 穷通宝鉴
target_sections:
  - 甲木
  - 乙木
  - 丙火
  - 丁火
  - 戊土
  - 己土
output_target: 20个Primitive Candidate
schema_version: V3
output_file: data/canonical/candidates_worker_qtbj.json
```

### WORKER-SMTH: 《三命通会》Worker
```yaml
agent_id: WORKER-SMTH
source_book: 三命通会
target_sections:
  - 论天干
  - 论地支
  - 论五行
output_target: 25个Primitive Candidate
schema_version: V3
output_file: data/canonical/candidates_worker_smth.json
```

### WORKER-YHZP: 《渊海子平》Worker
```yaml
agent_id: WORKER-YHZP
source_book: 渊海子平
target_sections:
  - 论天干
  - 论地支
  - 论十干
output_target: 20个Primitive Candidate
schema_version: V3
output_file: data/canonical/candidates_worker_yhzp.json
```

---

## 并行生产协议

### 每个Worker必须执行
1. **原典挖掘**: 从目标章节提取语义单元
2. **A/B/C分类**: 按Step 1方法分类
3. **Primitive提取**: 只提取最小语义事实，禁止Judgment
4. **Evidence定位**: 明确原文位置
5. **V3 Schema校验**: 写入前自动校验

### 禁止事项
❌ 禁止提取Condition
❌ 禁止提取Judgment
❌ 禁止包含L4力量问题
❌ 禁止把注释当原文

---

## 产出格式

每个Worker产出JSON数组：
```json
[
  {
    "candidate_id": "CAND-{BOOK}-{SEQ}",
    "source_book": "...",
    "text_layer": "ORIGINAL_TEXT|ORIGINAL_COMMENTARY|LATER_COMMENTARY",
    "original_text": "",
    "commentary_text": "",
    "later_commentary_text": "",
    "source_location": "...",
    "semantic_unit": "...",
    "primitive_candidate": "...",
    "canonical_mapping": "CANONICAL|PARTIAL|UNRESOLVED",
    "confidence": "HIGH|MEDIUM|LOW",
    "unresolved_questions": [],
    "agent_id": "WORKER-{BOOK}",
    "creation_time": "...",
    "red_team_flags": [],
    "audit_status": "PENDING"
  }
]
```

---

## 执行顺序

### Phase 1: 并行生产（当前）
启动5个Worker并行执行，每个Worker独立运行

### Phase 2: Dedup/Merge
收集所有Worker产出，去重合并

### Phase 3: Red-Team审查
独立审查所有Candidate

### Phase 4: Claude独立审计
Claude审核语义正确性

### Phase 5: GPT裁决
最终裁决哪些进入Production

---

## 立即执行

**启动5个Worker并行生产**