
## PATCH-031 Golden Case Validation Framework（commit 待）

### Golden Case schema 冻结
case_id/input_version/canonical_input/admitted_rules/expected_states/expected_trace/forbidden_outputs/regression_gate。

### GC-001 命盘版本锁定
V1：1983-11-03 11:30 男 广东中山→癸亥 壬戌 乙未 壬午（日主乙木，藏干亥壬甲/戌戊辛丁/未己丁乙/午丁己）。排盘变更须升 input_version，旧 case 保留不覆盖。

### 预期输出+预期 trace 锁定
shuai=SHUAI(MATCHED/EVID-001)；wang=UNKNOWN(ABSTAIN)；qiang=UNKNOWN；strength/pattern/三用神/climate 全 UNDETERMINED。

### forbidden_outputs 断言
strength≠六值域之一；pattern 不成立；用神未确定；climate_type 无具体判定；无未经注册输出。

### Regression 门（用户点名）
四层漂移检测：Producer 稳定（state 不变）/Rule 不漂移（match_result 不变）/Namespace 不污染（trace 不变）/Runtime 不越权（无 forbidden）。失败→FAIL_CLOSED 禁升级真实执行。

### Golden Case 定位（用户点名）
=Canonical Input+Admitted Rules+Expected Trace+Expected State（非人工经验案例）。

### 1983-1103 实跑（engines/common/golden_cases.py）
全部通过 ✓——Producer/Rule/Namespace/Runtime 四层无漂移。
