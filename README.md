# Shuntian Huangli — 黄历引擎独立切片

从 D:\shuntian 提取的最小可运行黄历排盘引擎 + 测试集（净物，不带旧仓库历史）。

## 结构
```
src/tongshu/
  engines/
    huangli_engine.py   # HuangliEngine.get_day(date) -> HuangliDay (核心)
    yi/                # 硬依赖: 八卦符号 + 六十四卦映射 (hexagram_symbol/core/models)
data/calendar_sources.json   # 黄历源注册表 (缺则降级空 registry, 不崩)
tests/                    # 4 个黄历测试 (52 条)
```

## 黄历算法要点
- 日柱干支双源锚定 (1900-01-01=甲戌 独立锚点) + lunar_python 实算
  (建除/值神/二十八宿/宜忌/冲煞/纳音/彭祖百忌/喜福财神方位/节气/生肖)
- 双源硬一致校验: 锚定干支 vs lunar 日干支漂移即 raise, 不静默输出冲突数据
- 六十甲子配卦当日卦 (癸酉→风山渐, 已由 2026-06-28 独立验证)

## 运行
```
.venv\Scripts\python.exe -m pytest tests -q
```

## 依赖
lunar_python / pytest

## 验证
2026-06-28 癸酉日 → 建除"平" 值神"明堂" 宿"房" 当日卦"风山渐"
4 测试文件 52 passed / 0 failed (0.42s)
