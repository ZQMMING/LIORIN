# Skill: 渊海子平切片（YHZP）

## 书籍信息
- 文件: D:\顺天系统资料\豆包资料\六部经典最终原著版\YHZP_渊海子平.md
- 特点: 基础体系+完整子平框架，切得最全面

## 这本书的特点
子平命理的基础框架书。
要切得最全面，覆盖所有基础体系。

## 切片原则（铁律）
1. **按章节切**，每章一个完整语义单元
2. **Relation只提取原文显式表达**
3. **十神分别切**，不全部压成一个SHISHEN
4. **神煞第一轮不切**（放OTHER/SECONDARY）

## YHZP必切全面覆盖

### 必切分类（全覆盖）
```
FOUNDATION   基础事实
YUE_LING      月令
GE_JU         格局
WANG_SHUAI    旺衰
SHISHEN       十神
SHENG_KE      五行生克
GANZHI        干支关系
XING_CHONG    刑冲合害
YONG_SHEN     用神
XI_SHEN       喜神
JI_SHEN       忌神
DA_YUN        大运
LIU_NIAN      流年
JI_XIONG      吉凶
ZAO_XIANG     命例
```

### 十神重点切（YHZP特色）
十神分别切，每神独立：
1. 比肩
2. 劫财
3. 食神
4. 伤官
5. 偏财
6. 正财
7. 七杀
8. 正官
9. 偏印
10. 正印

每神必切：
- 十神是什么
- 十神之间关系
- 十神得令
- 十神透干
- 十神坐支
- 十神生克
- 十神成格
- 十神为喜
- 十神为忌

切片分类: SHISHEN

### 神煞
第一轮不切，放OTHER/SECONDARY。
不要让神煞把主线切片工程带偏。

## 输出格式
同DTS_LB，十神切片增加：
```json
{
  "slice_id": "YHZP.论十神.正官",
  "chapter": "论正官",
  "category": "SHISHEN",
  "shishen": "正官",
  "definition": "克我者，异性为正官",
  "conditions": ["得令", "透干"],
  "auspicious": ["为喜", "成格"],
  "inauspicious": ["为忌", "混杂"],
  "source_text": "..."
}
```

## 验收标准
1. 十神全部分别切到
2. 基础体系全覆盖
3. 无理论推导
4. 无共现误判
5. 神煞不混入主线
