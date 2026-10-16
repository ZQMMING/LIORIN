# ZIWEI BASELINE REPORT
**日期**: 2026-09-04  
**Gate**: Z0

## 测试基线

```
tests/test_ziwei_engine.py                    15 passed
tests/test_ziwei_pattern.py                    7 passed
tests/test_ziwei_chart_cross_validate.py       4 passed (32 subtests)
tests/test_ziwei_phase_a0_extended.py         45 passed
tests/spec/test_vertical_slice_ziwei.py       13 passed
────────────────────────────────────────────────
TOTAL                                           84 passed, 0 failed
```

## 前置修复（非业务逻辑变更）

1. `node_modules/lunar-typescript/dist/` 目录为空（包未构建），从 npm registry 下载并解压 dist/ 修复
2. `i18next@23.16.8` 路径解析异常，执行 `npm install i18next@23.16.4 dayjs@1.11.23 lunar-lite@0.2.8` 恢复

## 全量测试（含非紫微）

存在 12 个 collection error（未安装的依赖/缺失文件），与紫微无关。紫微路径测试全部通过。
