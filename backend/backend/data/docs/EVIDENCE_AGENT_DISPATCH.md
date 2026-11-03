# 五经证据代理调度协议

> 制定时间: 2026-09-01
> 目标: 明确 Hermes 作为调度器的职责，五经 Agent 作为执行者的边界

---

## 一、Hermes 职责

### 1.1 可以做

- ✅ 拆分子任务给五个经典 Agent
- ✅ 收集各 Agent 的输出
- ✅ 汇总 QA 结果
- ✅ 追踪整体进度
- ✅ 提交裁决需求给 GPT

### 1.2 禁止做

- ❌ 自行定义经典规则
- ❌ 自行裁决生产状态
- ❌ 跳过 provenance 链条
- ❌ 为通过率强行授权

---

## 二、五经 Agent 职责

### 2.1 滴天髓证据代理（DTS）

**核心辨证目标**: 旺衰气势

**证据类型**:
- SEASONAL_SUPPORT（得令）
- ROOT_PRESENT（得地）
- MAIN_QI_ROOT（本气根）
- RESOURCE_SUPPORT（印生身）
- PEER_SUPPORT（比劫帮身）
- OFFICER_CONTROL（官杀制约）
- OUTPUT_DRAIN（食伤泄身）
- WEALTH_DRAIN（财星耗身）
- FLOW_SMOOTH（气势流通）
- FLOW_BLOCKED（气势阻滞）

### 2.2 子平真诠证据代理（PZZQ）

**核心辨证目标**: 格局成败

**证据类型**:
- PATTERN_CANDIDATE（格局候选）
- PATTERN_SUCCESS（成格）
- PATTERN_DAMAGE（破格）
- PATTERN_RESCUE（救应）
- YONG_SHEN（用神）
- XIANG_SHEN（相神）
- DE_DI_SUPPORT（十干得地）
- FIVE_COMBINE_PAIR（五合配对）

### 2.3 穷通宝鉴证据代理（QTBJ）

**核心辨证目标**: 调候寒暖

**证据类型**:
- CLIMATE_STATE（气候状态）
- PRIMARY_TIAOHOU（主调候）
- SECONDARY_TIAOHOU（次调候）
- TIAOHOU_PRESENT（调候出现）
- TIAOHOU_ROOTED（调候有根）
- TIAOHOU_BLOCKED（调候受阻）
- TIAOHOU_EXCESS（调候过量）
- WANG_XIANG_XIU_QIU_SI（五行时令）

### 2.4 三命通会证据代理（SMTH）

**核心辨证目标**: 关系转化

**证据类型**:
- GENERATES（相生）
- CONTROLS（相克）
- TRANSFORMATION（制化）
- CLASH（相冲）
- COMBINE（相合）
- HARM（相害）
- PUNISH（相刑）
- TIANYI_GUIREN（天乙贵人）
- TEN_GOD_BASIC（十神基础）

### 2.5 渊海子平证据代理（YHZP）

**核心辨证目标**: 基础语义

**证据类型**:
- MONTH_COMMAND（月令重要性）
- PATTERN_FROM_MONTH（格局从月令出）
- TEN_GOD_BASIC（十神基础）
- TEN_GOD_AUSPICIOUS（十神吉凶）
- SHENG_KE_ZHI_HUA（生克制化）
- XING_CHONG_HE_HAI（刑冲合害）
- WANG_XIANG_XIU_QIU_SI（旺相休囚）
- BASIC_SHASHA（基础神煞）

---

## 三、工作流程

### 3.1 单条证据提取流程

```text
1. Hermes 拆分任务 → 指定经典 + 证据类型
         ↓
2. Agent 从原典定位章节
         ↓
3. Agent 提取原文证据
         ↓
4. Agent 建立语义结构化映射
         ↓
5. Agent 生成 Assertion Candidate（CANDIDATE 状态）
         ↓
6. Agent 返回给 Hermes 汇总
         ↓
7. Hermes 提交给 Independent Audit
         ↓
8. GPT 裁决 → APPROVED/REJECTED/NEEDS_REVISION
         ↓
9. 进入 Production（如 APPROVED）
```

### 3.2 批量处理流程

```text
1. Hermes 批量拆分任务
         ↓
2. 五 Agent 并行处理各自经典
         ↓
3. Hermes 汇总所有候选
         ↓
4. Hermes 生成审计请求给 GPT
         ↓
5. GPT 批量裁决
         ↓
6. Hermes 更新状态
```

---

## 四、证据质量检查清单

每条证据必须通过以下检查：

- [ ] 有完整的 `source_locator`（经典 + 篇章 + 段落）
- [ ] 有 `evidence_text.original_text`（原文）
- [ ] 有 `evidence_text.text_layer`（原文/原注/后世注释）
- [ ] 有 `semantic_parse.observation_dimension`（观察维度）
- [ ] 有 `semantic_parse.evidence_type`（证据类型）
- [ ] 有 `semantic_parse.direction`（方向）
- [ ] 有 `authorization_level`（授权级别）
- [ ] `production_status` 默认为 `CANDIDATE`（Agent 不得自行提升）
- [ ] 无强行授权（找不到原文就标 `INSUFFICIENT_SOURCE`）

---

## 五、禁止事项

### 5.1 Agent 禁止

- ❌ 自行将 `production_status` 设为 `APPROVED`
- ❌ 跳过 provenance 链条
- ❌ 比较其他经典的结论
- ❌ 为通过率强行授权
- ❌ 自行决定进入生产

### 5.2 Hermes 禁止

- ❌ 自行定义经典规则
- ❌ 跳过五经 Agent 直接生成证据
- ❌ 为通过率修改 Agent 输出
- ❌ 自行裁决生产状态

---

## 六、文件结构

```text
src/tongshu/classic_evidence/
├── __init__.py          # 模块导出
├── base.py              # 基础框架（AssertionProvenance + ClassicEvidenceAgent）
├── dts_agent.py         # 滴天髓证据代理
├── pzzq_agent.py        # 子平真诠证据代理
├── qtbj_agent.py        # 穷通宝鉴证据代理
├── smth_agent.py        # 三命通会证据代理
└── yhzp_agent.py        # 渊海子平证据代理

data/assertions/
├── dts/                 # 滴天髓候选断言
├── pzzq/                # 子平真诠候选断言
├── qtbj/                # 穷通宝鉴候选断言
├── smth/                # 三命通会候选断言
└── yhzp/                # 渊海子平候选断言

docs/
├── AGENT_PERMISSION_BOUNDARY.md    # 权限边界协议
└── EVIDENCE_AGENT_DISPATCH.md      # 本文件
```

---

*本调度协议经 GPT 裁决后生效。*
