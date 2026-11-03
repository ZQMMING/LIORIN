# P0-3.5 裁决文档

**日期**: 2026-08-30  
**状态**: 🟢 PASS  
**Commit**: https://github.com/ZQMMING/wisdom/commit/606f122  
**裁决者**: Gemini

---

## 一、裁决结果

🟢 P0-3.5 PASS，但不批准"直接规模化"

---

## 二、为什么 PASS

9 条 C 类证据：
- 4 条 VERIFIED
- 5 条 UNRESOLVED
- 0 PARTIAL
- 0 INVALID

最关键的是：没有为了提高通过率替古人补条件。

已经实际跑通：
```
原典 → Evidence → Primitive → Condition → Local Judgment
```

并且代码、JSON、验证报告三者都有落地。

---

## 三、需要收紧的表述

报告写：
"9 条全部结构化、可执行、可测试"

这个表述需要收紧。

5 条 UNRESOLVED 实际上是：
```
Primitive 已识别
Condition 暂无法解析
Local Judgment = 条件待解析
```

所以它们目前不能算"完整的可执行 Judgment"。

应该区分：
```
STRUCTURED = 已完成结构化
EXECUTABLE = 条件已明确并可执行
VERIFIED = 原典条件得到验证
UNRESOLVED = 保留但不得授权
```

否则后面规模化时，很容易出现：
"结构化成功" → 被误认为"规则已经可以运行"。

---

## 四、下一步裁决

🟢 可以进入 P0-3.6

但目标不是"把 5 条 UNRESOLVED 变成 VERIFIED"。

而是：
建立 Primitive/Condition 正式 Schema + Authorization 边界。

尤其把：
```
UNRESOLVED → 可以保存、可以检索、可以继续研究、禁止产生 Judgment
VERIFIED → 可以进入 Rule Resolver、才能产生 Local Judgment
```

变成真正的机器可执行状态。

---

## 五、暂时不要做

❌ 规模化生产 284 条 Primitive  
❌ 直接做 Composite Judgment  
❌ 直接做"身强/身弱总公式"  
❌ 强行解析 5 条 UNRESOLVED  
❌ 用 AI 猜隐含条件

---

## 六、当前状态

| 任务 | 状态 |
|------|------|
| T2 strength isolation | 🟢 PASS |
| T3 primitive validation | 🟢 PASS |
| P0-3.4 semantic attribution | 🟢 PASS |
| P0-3.5 primitive structure | 🟢 PASS |
| Primitive/Condition 工程化 | 🟢 已证明可工程化 |
| Primitive/Condition Schema | 🟡 下一步（P0-3.6） |
| Composite Judgment | 🔒 暂缓 |
| 五经综合辨证 | 🔒 暂缓 |

---

## 七、结论

606f122 通过。

下一步做 P0-3.6：冻结 Primitive/Condition 的机器契约与 Authorization 边界，而不是扩大规则数量。
