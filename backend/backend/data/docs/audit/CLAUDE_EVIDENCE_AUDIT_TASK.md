# Claude独立Evidence审计任务 - M3 Phase 3.1 第1批

**时间**: 2026-08-31  
**任务**: 逐条核验DTS-GEJU-001~005的Evidence  
**要求**: 必须找到原文，不能接受paraphrase作为证据

---

## 审计指令

### 核心要求（GPT裁决4762e19）
1. **必须逐条核验原文**
   - 不能接受`verification_status = pending_verification`
   - 不能接受`paraphrase`作为有效证据
   - 必须找到任铁樵《滴天髓阐微》通行本原文

2. **分层核验**
   - Original Text（原文）
   - Ren Commentary（任注：任铁樵注）
   - Later Commentary（后世解释）

3. **每条目必须证明**
   - 原文出处准确
   - Primitive没有扩大语义
   - Condition是原典明确条件（不是组合推断）
   - Composite的AND/OR/SEQUENCE有原典依据
   - Judgment没有从"描述现象"升级成"必然判断"

4. **特别关注**
   - DTS-GEJU-001: 原典是否说"得令+透干+生扶→成格"？
   - DTS-GEJU-002: 原典是否说"有根+根深+比劫→成格"？
   - DTS-GEJU-005: 是否涉及L4力量问题？

---

## 数据来源

### 主要来源
1. **中国哲学书电子化计划** (ctext.org)
   - URL: https://ctext.org/wiki.pl?if=gb&chapter=126492
   - 内容: 滴天髓闡微全文

2. **算准网** (suanzhun.net)
   - URL: https://www.suanzhun.net/book/362.html
   - 内容: 滴天髓阐微原文+白话+任注

3. **太极书馆** (8bei8.com)
   - URL: https://www.8bei8.com/book/ditiansui_19.html
   - 内容: 滴天髓原文

### 本地数据
- `data/evidence/E-DTS-*.json` - 已有Evidence记录（但多为paraphrase）
- `data/knowledge/passages.json` - 已有分段数据
- `docs/audit/DTS_ORIGINAL_TEXT_VERIFICATION.md` - 本次核验报告

---

## 审计输出格式

对每条断言（001-005），输出：

```markdown
### DTS-GEJU-XXX: [格局名称]

#### 原典定位
- 章节: 《滴天髓·通神论·XX》
- 原文: [完整原文引用]
- 任注: [任铁樵注释引用]

#### Evidence核验
| Evidence ID | 声称内容 | 核验结果 | 问题 |
|------------|---------|---------|------|
| E-DTS-XXX | ... | ✅ EXACT_MATCH / ⚠️ PARTIAL_MATCH / 🔴 NOT_FOUND | ... |

#### Primitive审计
| Primitive | 定义 | 原典依据 | 问题 |
|----------|------|---------|------|
| A: ... | ... | [原文定位] | [问题说明] |

#### Composite审计
- 声称: "[A且B且C → D]"
- 核验: [是否有原典明确授权]
- 结论: [✅ 有授权 / ⚠️ 部分授权 / 🔴 无授权]

#### Judgment审计
- 当前Judgment: "[...]"
- 核验: [是否在原典授权范围内]
- 结论: [✅ 通过 / 🔴 越界]

#### 最终裁决
- 状态: [✅ APPROVED / ⚠️ APPROVED_WITH_NOTES / 🔴 DENIED]
- 理由: [...]
```

---

## 特别注意事项

1. **不要接受字段作为证据本身**
   - `classical_authorization`字段存在 ≠ 原典真的授权
   - 必须验证字段后面的证据是否真的存在

2. **区分"描述现象"和"必然判断"**
   - 原典如果说"甲木生于春...则气旺" → 这是描述现象
   - 不能工程化为"如果月令是甲木且日主是春 → 必然成格"
   - 原典必须有明确的条件判断语句（如"若...则..."）

3. **L4力量问题**
   - DTS-GEJU-005的`KE_XIE_HAO_DOMINANT`涉及"势"的判断
   - 这触及V1.4基线删除Legacy Strength要解决的问题
   - 必须标注风险等级

---

## 输出文件

将审计结果写入:
`docs/audit/CLAUDE_EVIDENCE_AUDIT_M3_PHASE3.1_BATCH_001.md`

然后提交commit。

---

**开始执行审计。**