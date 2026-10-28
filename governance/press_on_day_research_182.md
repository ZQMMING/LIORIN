# PATCH-182 岁运压日 只读裁决（SEALED）

## 代码现状核查
relation_178.py 无 same_branch/伏吟/并临/压日代码，纯边界研究。

## 原典
《三命通会·总论岁运》："岁运与日相对谓之返吟，岁运压日谓之伏吟"；"岁用天元，运用地支"；"甲子流年又是甲子运谓之岁运并临"；"甲子日见甲子太岁谓之日年相并"。

## 裁决
### 授权机器化（两个原子 Fact）
| 原子 | 判定 | Semantic |
|---|---|---|
| day_year_same | 流年干支==日柱干支 | 日年相并 |
| yun_year_same | 流年干支==大运干支 | 岁运并临 |

### 暂不授权
- 岁运压日 / 返吟 / 伏吟：原典给术语但无唯一机器公式
- 不能反推 流年+大运共同压日
- 不能反推 流年==日柱（已有独立术语"日年相并"）
- day_year_same 与 yun_year_same 是两个独立结构，不合成 pressure_on_day

## 工程层
```
178 原子Relation
181 Projection: yun_year_same(岁运并临)/day_year_same(日年相并)/birth_year_same(真太岁)
182: 岁运压日 = semantic candidate / NOT_AUTHORIZED
```

铁边界：结构事实 ≠ 术语自动升级 ≠ 作用成立 ≠ 强弱 ≠ 喜忌 ≠ 吉凶。
下一刀：进入下一个原子岁运结构，不再围绕岁运压日打转。
