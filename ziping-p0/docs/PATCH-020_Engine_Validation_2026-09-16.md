
## PATCH-020 Engine Validation Layer（commit 待）

### 020-01 验证管线框架
engines/common/validation_layer.py：加载 017/018/019 + 各域 Registry，三层验证（静态验证 / Golden 拦截 / Conflict 单测）。本层不实现命理计算（不产生辰→状态推导），只验证规则库正确性；真正八字输入计算属 Engine Execution（未启动）。

### 020-02 静态验证（STATIC_VALIDATION）
60 条全量：source 可回查/output 非空/condition 非空/禁转换已声明/scope 非空/rule_id 非空 → 59 STATIC_PASS + 1 DESIGN_EXEMPT（CAND-RUO-001 弱概念，005A Human 裁决无单锚，设计豁免）。修复 005C 4 条 predicate 缺 source_ids/excluded_transition 字段（补 YHZP-138-001）。

### 020-03 首批 Golden 验证
5 条全局必测反例全部 BLOCKED：旺≠强 / 得令≠强 / 有根≠强 / 调候≠旺衰 / 病药≠用神 —— 规则库元数据级确认不存在允许禁转换的规则。Conflict Resolver 8 类单测 PASS。

### 状态
规则库 60 条全通过静态+拦截验证；ADMITTED 仍=0（引擎执行层未启动，golden_pass=false 不变）。下一阶段=Engine Execution（八字输入→State/Factor→Rule 匹配）需新授权。
