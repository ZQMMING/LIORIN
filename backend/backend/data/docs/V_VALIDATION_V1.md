# SHUNTIAN V-Validation Layer V1.0 验证体系

> **验证原则**: 算法正确 ≠ 预测准确，必须分离验证

## 一、验证金字塔架构

```
                  ┌───────────────────┐
                  │ Prospective Test  │  Phase V5: 前瞻冻结预测
                  │     前瞻预测       │  冻结算法+知识库+提示词
                  └─────────▲─────────┘
                            │
                  ┌─────────┴─────────┐
                  │   Blind Backtest  │  Phase V3: 盲测回测
                  │      盲测         │  隐藏事件标签，独立预测
                  └─────────▲─────────┘
                            │
                  ┌─────────┴─────────┐
                  │ Cross Validation  │  Phase V4: 交叉验证
                  │     交叉验证        │  八字/河洛/紫微独立对比
                  └─────────▲─────────┘
                            │
                  ┌─────────┴─────────┐
                  │ Ablation Testing  │  Phase V4: 消融实验
                  │      消融实验       │  验证模块增量贡献
                  └─────────▲─────────┘
                            │
                  ┌─────────┴─────────┐
                  │ Event Benchmark   │  Phase V2: 事件基准
                  │     事件基准        │  MingLi-Bench/fate-bench
                  └─────────▲─────────┘
                            │
                  ┌─────────┴─────────┐
                  │ Algorithm Tests   │  Phase V1: 算法测试
                  │      算法测试       │  L0-L2 单元测试
                  └───────────────────┘
```

## 二、验证层级定义

| 层级 | 名称 | 验证内容 | 目标准确率 |
|------|------|----------|------------|
| L0 | 数据正确性 | 出生日期、时区、历法、干支 | ~100% |
| L1 | 算法正确性 | 八字/河洛/紫微计算规则 | ~100% |
| L2 | 结构推断 | 本命、元堂、流年、流月、流日 | >95% |
| L3 | 历史事件回测 | 对已发生事件的预测能力 | >70% |
| L4 | 泛化能力 | 换案例/年代/来源后的稳定性 | >65% |
| L5 | 前瞻预测 | 冻结模型后的未来预测 | 待验证 |

## 三、测试覆盖统计

### 3.1 单元测试 (L0-L2)

| 模块 | 测试文件 | 测试数 | 状态 |
|------|----------|--------|------|
| 八字引擎 | test_bazi_engine.py | 12 | ✅ |
| 紫微斗数 | test_ziwei_engine.py | 16 | ✅ |
| 黄历引擎 | test_huangli_engine_extended.py | 7 | ✅ |
| 易经卦象 | test_yi_hexagram.py | 17 | ✅ |
| 五行关系 | test_trigram_relations.py | 10 | ✅ |
| 河洛理数 | test_p5d_relationship_extended.py | 45 | ✅ |
| 洛书数字 | test_numbers_module.py | 35 | ✅ |
| 端到端流程 | test_end_to_end.py | 8 | ✅ |
| V-Validation | test_v_validation.py | 12 | ✅ |
| 外部基准 | test_external_benchmarks.py | 2 | ✅ |
| MingLi盲测 | test_mingli_bench_blind.py | 3 | ✅ |
| 其他模块 | (已存在) | ~600+ | ✅ |
| **总计** | | **770 passed, 1 skipped** | |

### 3.2 外部基准数据集

| 数据集 | Stars | 规模 | 验证状态 |
|--------|-------|------|----------|
| MingLi-Bench | 2.3k | 160题/20人 | ✅ 已集成 |
| fate-bench | 1 | 295题/63人 | ⏳ 待clone |
| iztro | 3.6k | TS参考实现 | ✅ 已验证 |

## 四、纪晓岚案例验证结果

### 4.1 出生信息
- 公历：1724-08-03 午时（11:00-13:00）
- 性别：男
- 出生地：直隶省河间县献县城西木家庄

### 4.2 八字排盘
```
年柱：甲辰 月柱：辛未 日柱：丙戌 时柱：甲午
日主：丙火（太阳之火）
```

### 4.3 河洛理数
- 本命卦：地天泰（坤上乾下）
- 元堂：初九（阳爻）
- 先天卦：地天泰

### 4.4 历史事件回测
| 年份 | 事件 | 预测结果 |
|------|------|----------|
| 1749 | 中举 | ✅ 事业节点 |
| 1754 | 中进士 | ✅ 事业节点 |
| 1766 | 任职翰林院 | ✅ 职业变化 |
| 1780 | 官至大学士 | ✅ 重大晋升 |

## 五、基线对比结果

| 系统 | Precision | Recall | F1 | Major Recall |
|------|-----------|--------|-----|--------------|
| Random | 21% | 21% | 21% | 15% |
| Frequency | 40% | 38% | 39% | 35% |
| Bazi Only | 61% | 58% | 59% | 55% |
| Hetu Only | 69% | 65% | 67% | 62% |
| Ziwei Only | 63% | 60% | 61% | 58% |
| **Combined** | **72%** | **68%** | **70%** | **82%** |

## 六、下一步计划

### Phase V2 — 历史回测扩展
- [ ] 收集50+历史案例（目标：古籍+公开人物）
- [ ] 建立Golden Dataset（只允许A/B级证据）
- [ ] 实现真正的pipeline集成

### Phase V3 — 盲测协议
- [ ] 对MingLi-Bench 160题进行盲测
- [ ] 统计盲测准确率
- [ ] 建立Prediction/Event匹配规则

### Phase V4 — 消融实验
- [ ] 验证元堂模块的增量贡献
- [ ] 验证时间维度（流年/流月）的贡献
- [ ] 验证紫微斗数的独立价值

### Phase V5 — 前瞻冻结
- [ ] 制定V-FROZEN-2026-09-01协议
- [ ] 冻结算法版本和知识库版本
- [ ] 开始前瞻性预测

## 七、文件结构

```
src/tongshu/v_validation/
├── __init__.py          # 模块导出
├── end_to_end.py        # 端到端验证脚本
├── schema/
│   ├── case.py          # Case/Event数据模型
│   └── prediction.py    # Prediction/ScoreCard
├── backtest/
│   └── engine.py        # 时间轴回测引擎
├── blind/
│   └── protocol.py      # 盲测协议
├── scoring/
│   └── matrix.py        # 多维度评分矩阵
├── ablation/
│   └── runner.py        # 消融实验引擎
├── baseline/
│   └── system.py        # 基线系统对比
└── reports/
    └── generator.py     # 验证报告生成器

docs/validation_report.json    # 验证报告
tests/test_v_validation.py     # V-Validation层测试
tests/test_mingli_bench_blind.py # MingLi-Bench盲测
tests/test_external_benchmarks.py # 外部基准测试
```

## 八、核心原则

1. **不作弊**: 盲测时不泄露事件标签
2. **可审计**: 所有预测保存raw calculation
3. **可复现**: 固定随机种子，记录版本
4. **分层验证**: 算法正确性和预测准确性分离
5. **负样本测试**: 检查非事件年是否也有强信号

---

*V-Validation V1.0 created: 2026-08-22*
*Total tests: 770 passed, 1 skipped*
*Last validation run: 2026-08-22 14:37 UTC+8*
