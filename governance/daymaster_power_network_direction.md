# 身强身弱多维网络设计方向与标准（PATCH-160-B V2）

状态：FROZEN / 基准点 099967a1
锁死日期：2026-09-17

---

## 一、核心方向（绝对锁死）

**不做总裁决器，不压缩成 STRONG/WEAK 总分。**

```
错误方向（已废）:
  事实 → 强弱计算 → STRONG/WEAK 总分

正确方向（当前）:
  Canonical Facts
    ↓
  多维关系网络（节点+边+维度）
    ↓
  经典规则各自查询网络
    ↓
  各命题各自结论
```

---

## 二、原著依据

| 原著命题 | 网络对应 |
|---|---|
| 《子平真诠》"得时为旺，失时为衰" | SEASONAL 维度 |
| 《子平真诠》"党众为强，助寡为弱" | SUPPORT 维度 |
| 《子平真诠》"只要四柱有根，便能受财官" | ROOT 维度 |
| 《子平真诠》"得时而不旺" | SEASONAL=得令 + DRAIN=成势，矛盾共存不裁 |
| 《子平真诠》"失时而不弱" | SEASONAL=失令 + SUPPORT=成势，矛盾共存不裁 |
| 《滴天髓》"强众敌寡/强寡敌众" | TWO_SIDE 维度（两端查询） |

---

## 三、五维独立轴（绝不汇总）

```
SEASONAL   得令/失令/月令生扶
ROOT       通根/根重(HEAVY/LIGHT)
SUPPORT    党众/助寡（印比）
DRAIN      泄耗（食伤/财）
CONTROL    克制（官杀）
```

每维独立输出，禁止：
- 不评分
- 不权重
- 不阈值
- 不计数（不数"太多/太重"）
- 不比较两端大小
- 不汇总成 STRONG/WEAK

---

## 四、网络 Schema

### Node Types
- DAYMASTER
- ROOT_BRANCH
- SUPPORT_GROUP
- DRAIN_GROUP
- CONTROL_GROUP
- SEASON

### Edge Types
- ROOT_RELATION（日主 ← 根）
- SEASONAL_RELATION（月令 ↔ 日主）
- SUPPORT_RELATION（印/比劫 → 日主）
- DRAIN_RELATION（日主 → 食伤/财）
- CONTROL_RELATION（官杀 → 日主）
- PRODUCE_RELATION（传递链，C级）
- COMBINATION（合冲刑害破）

### Authorization
- A = 直接结构，可独立存在
- C = 五行生克可查，但"有效力量传递"未授权，不参与强弱

---

## 五、矛盾共存原则

允许：
```
得令 = YES
通根 = HEAVY
扶身 = 成势
泄耗 = 明显
克制 = 明显
两端 = 双方成势
强弱 = UNDETERMINED
```

**这不是失败，是多维网络保留信息后的正确结果。**

禁止：
- 强行裁掉任一维
- 为得到 STRONG/WEAK 而压掉矛盾
- 用"太重/太轻"的数量语义替代存在性

---

## 六、Query Interface（未来）

经典规则查询网络，不汇总：
```
Rule
 ↓
需要哪些结构条件？
 ↓
网络查询
 ↓
满足 / 不满足 / 未知
```

不同规则对"强"的定义不同，各自查询，不共享总裁决。

---

## 七、永久边界

- 不输出 STRONG / WEAK 总分
- 不做 score / totalizer
- 传递链（食伤→财→官→印）C 级，不参与强弱
- 两端成势不裁，保留节点
- 不改 dbadfedc 主链
- 不接生产（当前）

---

## 八、对应工程

- `engines/common/daymaster_power_structure.py` = 160-A（已有，封板）
- `engines/common/daymaster_power_network.py` = 160-B V2（当前）
- HEAD = 099967a1
