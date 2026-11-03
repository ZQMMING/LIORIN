# 盲派 Phase A 立即纠偏裁决执行记录

## 裁决日期: 2026-09-02

### 裁决来源
用户对 commit `211562f` 的裁决，以及后续发布的《顺天｜盲派 Phase A 立即纠偏裁决》

---

## 一、核心原则

**Phase A 仍然是 Evidence Collection，但必须以"盲派原生理论结构"为前提。**

```text
盲派
├── 理法
│   ├── 宾主
│   ├── 体用
│   ├── 做功
│   │   ├── 结构层: 制用/化用/生用/泄用/合用/墓用/复合做功
│   │   ├── 机制层: 合/冲/刑/克/穿/墓（具体作用方式）
│   │   ├── 结果层: 功神/废神/能量/效率
│   │   └── 特殊层: 贼神/捕神
│   ├── 势党
│   └── 虚实
│
├── 象法
│   ├── 干支象
│   ├── 宫位象
│   ├── 十神象
│   └── 职业/六亲象
│
└── 技法
    ├── 应期
    ├── 大运流年作用
    └── 具体断法
```

---

## 二、禁止事项

1. **禁止将子平 Feature → Signal → Rule 思维套到盲派**
2. **禁止把盲派"旺衰 + 用神"当作另一套实现**
3. **禁止用一句话包含"做功"就归入 WORK_METHOD**
4. **禁止建立等价映射**:
   - 克 ≠ 制用
   - 参与做功 ≠ 功神
   - 力量大 ≠ 效率高
   - A克B ≠ A自动成为捕神

---

## 三、原有 Topic 重新定位

当前以下 Topic **只能视为检索/抽取标签**，不是最终 Blind Signal Taxonomy：

```text
BODY_USE_RELATION
GUEST_HOST
WORK_METHOD
WORK_RELATION
WORK_EFFICIENCY
WORK_TARGET
WORK_TYPE
POWER_PARTY
EMPTY_USELESS
IMAGE
YING_QI
COMPLEX_WORK
WORK_ACTOR
```

**这些 Topic 暂时保留用于现有 Evidence 分类，但新扩充时必须：**
1. 先确定理论层归属（理法/象法/技法）
2. 再确定具体层次（结构/机制/结果/特殊角色）
3. 确认原文为真实出处
4. 不得标 DIRECT/HIGH 除非完成文献核验

---

## 四、新 Topic 建议

### 理法 - 结构层
- GUEST_HOST (宾主)
- BODY_USE_RELATION (体用)
- POWER_PARTY (势党)
- EMPTY_USELESS (虚实)

### 理法 - 机制层（做功方式）
- WORK_MERGE (合做功)
- WORK_GRAVE (墓做功)
- WORK_PUSH (冲做功)
- WORK_PENETRATE (穿做功)
- WORK_RESTRAINT (制做功)
- WORK_TRANSFORM (化做功)
- WORK_NOURISH (生做功)
- WORK_DRAIN (泄做功)

### 理法 - 结果层
- WORK_EFFICIENCY (做功效率)
- GONG_SHEN (功神)
- FEI_SHEN (废神)
- ENERGY (能量)

### 理法 - 特殊角色
- ZEI_SHEN (贼神)
- BU_SHEN (捕神)

### 理法 - 主体层
- WORK_ACTOR (做功主体)
- WORK_TARGET (做功目标)

### 象法
- IMAGE (象法)

### 技法
- YING_QI (应期)

---

## 五、原 WORK_METHOD/WORK_RELATION/WORK_TYPE 处理

这三个 Topic **压扁了盲派做功理论的分层结构**，需要拆分：

| 原 Topic | 拆分方向 |
|---------|---------|
| WORK_METHOD | 拆分为合/墓/冲/穿/制/化/生/泄做功 |
| WORK_RELATION | 拆分为合/墓/冲/穿等具体作用方式 |
| WORK_TYPE | 重新归类到做功机制或合并 |

---

## 六、当前状态

```text
总证据数: 74条
Layer分布: A=2, B=57, C=15
Topic覆盖: 13/13

PENDING_VERIFICATION: 18条
DIRECT/HIGH: 56条

架构审计: COMPLETED
下一步: 等待裁决
```

---

## 七、禁止事项重申

**在 Architecture Audit 完成前，禁止继续机械扩充 Evidence 数量。**

现在的工作重点：
1. ✅ 完成 74 条 Evidence 的架构审计
2. ✅ 识别混层、错误 Topic、疑似二次整理文本
3. ⏸️ 暂停机械扩充（不再从 74 → 85 → 100）
4. ⏳ 等待进一步裁决后再决定下一步行动

---

## 八、下一步指示

等待用户对以下问题的裁决：
1. 原 WORK_METHOD/WORK_RELATION/WORK_TYPE 如何拆分？
2. 是否建立新的 Topic Taxonomy？
3. 是否需要重新分类现有 74 条 Evidence？
4. Phase A 是否继续进行？以何种方式继续？
