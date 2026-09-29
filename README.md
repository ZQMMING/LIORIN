# Shuntian Bazi — 八字排盘引擎独立切片

从 D:\shuntian (LIORIN 前身) 提取的最小可运行八字排盘引擎 + 测试集。

## 结构
```
src/tongshu/
  engines/
    bazi_engine.py        # BaziEngine.compute() 核心排盘
    bazi_engine_spec.py   # 规范 / 契约层
    bazi_adapter.py       # BaziAdapter (走 TimeResolver 真太阳时 + 子正换日)
    bazi_l1_facts.py      # L1 事实 (十二长生 / 藏干)
    time/                 # 时间层 (TimeResolver / jd_converter / eot / day_boundary ...)
    time_resolver.py      # 真太阳时解析 (P0-14)
  facts/bazi_facts.py     # 基础事实常量 (单源真相)
  reasoning/bazi_ten_gods.py  # 十神单源
  models/canonical_bazi.py    # CanonicalBaziChart 契约
  k2g/registry_loader.py      # (测试 test_k2g_baziqa 依赖)
tests/                    # 20 个 bazi 测试 + conftest
data/locations.json       # 793 城市经纬度 registry (TimeResolver 城市名路径)
```

## 运行
```
.venv\Scripts\python.exe -m pytest tests -q
```

## 依赖 (pyproject.toml)
sxtwl 2.0.7 / lunar_python / timezonefinder / tzdata / pytest

## 子正换日裁决
23:00-23:59 夜子时：日柱保持当天、时柱按次日日干五鼠遁起子时；0:00 起换日换时柱。
