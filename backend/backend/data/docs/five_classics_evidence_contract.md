# 五经证据整理规范 v1.0

## 核心原则

1. **原典优先** — 所有证据必须来自原文，禁止凭记忆或理解编写
2. **EVIDENCE ≠ ASSERTION** — 本阶段只做证据提取，不做断言生成
3. **互补不比较** — 五经互补，不投票，不比较对错
4. **INSUFFICIENT_SOURCE** — 找不到原文必须标记，不能伪造

## Evidence 合同

每条证据必须包含以下字段：

```json
{
  "evidence_id": "E-{CLASSIC_CODE}-{TYPE}-{PASSAGE_ID}",
  "classic_id": "di_tian_sui" | "ziping_zhenquan" | "qiong_tong_bao_jian" | "san_ming_tong_hui" | "yuan_hai_zi_ping",
  "classic_name": "滴天髓" | "子平真诠" | "穷通宝鉴" | "三命通会" | "渊海子平",
  "evidence_type": "STRING",
  "observation_dimension": "STRING",
  "relation_semantics": "SUPPORT" | "CONSTRAINT" | "MODIFIER" | "CONTEXT" | "NEUTRAL",
  "original_text": "STRING — 必须是非空原文",
  "source_locator": {
    "classic": "di_tian_sui",
    "work": "滴天髓",
    "chapter": "通神论·衰旺",
    "section": "",
    "passage_id": "DTS_0001",
    "source_hash": "sha256 of original_text"
  },
  "evidence_text": {
    "original_text": "STRING",
    "text_layer": "ORIGINAL",
    "context_before": "STRING",
    "context_after": "STRING"
  },
  "canonical_state": {},
  "authorization_level": "PARTIAL" | "AUTHORIZED" | "INSUFFICIENT_SOURCE",
  "verification_status": "UNVERIFIED",
  "extraction_quality": 0.0-1.0,
  "notes": "STRING"
}
```

## 证据类型定义

每个 Agent 根据自己负责的经典定义证据类型：

### 滴天髓 (DTS) — 旺衰气势辨证
- SEASONAL_SUPPORT — 得令证据
- ROOT_PRESENT — 得地证据（根气存在）
- MAIN_QI_ROOT — 本气根证据
- RESOURCE_SUPPORT — 印生身证据
- PEER_SUPPORT — 比劫帮身证据
- OFFICER_CONTROL — 官杀制约证据
- OUTPUT_DRAIN — 食伤泄身证据
- WEALTH_DRAIN — 财星耗身证据
- FLOW_SMOOTH — 气势流通证据
- FLOW_BLOCKED — 气势阻滞证据

### 子平真诠 (PZZQ) — 格局成败辨证
- GEJU_SUCCESS — 成格证据
- GEJU_FAILURE — 破格证据
- YONGSHEN_VALID — 用神有力证据
- YONGSHEN_WEAK — 用神无力证据
- TIAN_GAN_SUPPORT — 天干辅佐证据
- DI_ZHI_SUPPORT — 地支辅佐证据

### 穷通宝鉴 (QTBJ) — 调候寒暖辨证
- TEMPERAMENT_COLD — 寒证据
- TEMPERAMENT_HOT — 暖证据
- TEMPERAMENT_DRY — 燥证据
- TEMPERAMENT_WET — 湿证据
- ADJUSTMENT_SUPPORT — 调候得宜证据
- ADJUSTMENT_FAILED — 调候失宜证据

### 三命通会 (SMTH) — 关系转化辨证
- RELATION_GENERATE — 相生关系证据
- RELATION_CONTROL — 相克关系证据
- RELATION_COMBINE — 相合关系证据
- RELATION_CLASH — 相冲关系证据
- RELATION_PUNISH — 相刑关系证据
- TRANSFORMATION_SUCCESS — 化气成功证据
- TRANSFORMATION_FAILED — 化气失败证据

### 渊海子平 (YHZP) — 基础语义辨证
- DAYMASTER_STRONG — 日主强证据
- DAYMASTER_WEAK — 日主弱证据
- MONTH_BRANCH Dominant — 月令主导证据
- TEN_GODS_BALANCE — 十神平衡证据
- STRUCTURE_CLEAR — 格局清晰证据
- STRUCTURE_MIXED — 格局混杂证据

## 输出要求

每个 Agent 输出：
1. `data/evidence/{CLASSIC_CODE}/` — 证据 JSON 文件目录
2. `data/reports/{CLASSIC_CODE}_evidence_summary.json` — 统计报告
3. `data/reports/{CLASSIC_CODE}_insufficient_source.json` — INSUFFICIENT_SOURCE 清单

## 禁止事项

- ❌ 禁止生成 AUTHORIZED 证据（默认 PARTIAL）
- ❌ 禁止跳过 provenance 链条
- ❌ 禁止为通过率强行授权
- ❌ 禁止把古文直接改写成断言
- ❌ 禁止伪造原文

## 执行步骤

1. 加载本经典原文数据
2. 按证据类型分类扫描原文
3. 对每条相关原文提取证据
4. 保存证据到 output_dir
5. 统计并生成报告
