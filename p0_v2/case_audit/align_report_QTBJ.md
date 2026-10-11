# QTBJ 引擎对齐报告 v0.1

- 经典: **QTBJ** — 引擎主战场: 调候用神
- 案例总数: 802  (已跑 802)
- 八字解析失败: 0
- 引擎运行异常: 0
- label 分布: {'good': 533, 'mixed': 143, 'bad': 84, 'neutral': 42}

## 引擎输出侧（结构化）

每例记录 `engine_day_stem` + `engine_special`（cong/zhuanwang/huaqi/mumie/liangqi）。

## 文本结论侧（该部 analysis 提取）

按 QTBJ 主战场提取器产出。

## 前 15 例对齐数据（JSON）
```json
[
 {
  "case_id": "QT-0001",
  "bazi": "庚申 戊寅 甲寅 丙寅",
  "label": "good",
  "verdict": "pass",
  "engine_view": {
   "day_stem": "甲",
   "special": {},
   "climate_candidates": [
    "丙",
    "癸"
   ],
   "climate_state": "REGISTERED"
  },
  "text_extraction": {
   "xi_gan": [
    "庚"
   ],
   "yong_gan": [
    "丁",
    "丁",
    "丁",
    "辛",
    "丁",
    "庚",
    "庚",
    "庚",
    "丁",
    "庚",
    "丁"
   ]
  },
  "status": "OK"
 },
 {
  "case_id": "QT-0002",
  "bazi": "戊寅 甲寅 甲辰 乙亥",
  "label": "good",
  "verdict": "pass",
  "engine_view": {
   "day_stem": "甲",
   "special": {},
   "climate_candidates": [
    "丙",
    "癸"
   ],
   "climate_state": "REGISTERED"
  },
  "text_extraction": {
   "xi_gan": [],
   "yong_gan": []
  },
  "status": "OK"
 },
 {
  "case_id": "QT-0003",
  "bazi": "甲申 丙寅 甲寅 庚午",
  "label": "good",
  "verdict": "pass",
  "engine_view": {
   "day_stem": "甲",
   "special": {},
   "climate_candidates": [
    "丙",
    "癸"
   ],
   "climate_state": "REGISTERED"
  },
  "text_extraction": {
   "xi_gan": [],
   "yong_gan": [
    "庚",
    "庚"
   ]
  },
  "status": "OK"
 },
 {
  "case_id": "QT-0004",
  "bazi": "乙亥 己卯 甲申 乙亥",
  "label": "good",
  "verdict": "pass",
  "engine_view": {
   "day_stem": "甲",
   "special": {},
   "climate_candidates": [
    "庚",
    "丁"
   ],
   "climate_state": "REGISTERED"
  },
  "text_extraction": {
   "xi_gan": [],
   "yong_gan": []
  },
  "status": "OK"
 },
 {
  "case_id": "QT-0005",
  "bazi": "甲午 丁卯 甲寅 丁卯",
  "label": "mixed",
  "verdict": "pass",
  "engine_view": {
   "day_stem": "甲",
   "special": {
    "liangqi": {
     "name": "两气成象(木火)",
     "wuxing": [
      "木",
      "火"
     ],
     "relation": "相生",
     "xiu": "火",
     "state": "CONFIRMED"
    }
   },
   "climate_candidates": [
    "庚",
    "丁"
   ],
   "climate_state": "REGISTERED"
  },
  "text_extraction": {
   "xi_gan": [],
   "yong_gan": []
  },
  "status": "OK"
 },
 {
  "case_id": "QT-0006",
  "bazi": "己未 丁卯 甲戌 庚午",
  "label": "mixed",
  "verdict": "pass",
  "engine_view": {
   "day_stem": "甲",
   "special": {},
   "climate_candidates": [
    "庚",
    "丁"
   ],
   "climate_state": "REGISTERED"
  },
  "text_extraction": {
   "xi_gan": [],
   "yong_gan": []
  },
  "status": "OK"
 },
 {
  "case_id": "QT-0007",
  "bazi": "癸未 乙卯 甲子 己巳",
  "label": "bad",
  "verdict": "pass",
  "engine_view": {
   "day_stem": "甲",
   "special": {},
   "climate_candidates": [
    "庚",
    "丁"
   ],
   "climate_state": "REGISTERED"
  },
  "text_extraction": {
   "xi_gan": [],
   "yong_gan": []
  },
  "status": "OK"
 },
 {
  "case_id": "QT-0008",
  "bazi": "戊寅 乙卯 甲午 甲戌",
  "label": "mixed",
  "verdict": "pass",
  "engine_view": {
   "day_stem": "甲",
   "special": {},
   "climate_candidates": [
    "庚",
    "丁"
   ],
   "climate_state": "REGISTERED"
  },
  "text_extraction": {
   "xi_gan": [],
   "yong_gan": []
  },
  "status": "OK"
 },
 {
  "case_id": "QT-0009",
  "bazi": "乙亥 己卯 甲申 乙亥",
  "label": "good",
  "verdict": "pass",
  "engine_view": {
   "day_stem": "甲",
   "special": {},
   "climate_candidates": [
    "庚",
    "丁"
   ],
   "climate_state": "REGISTERED"
  },
  "text_extraction": {
   "xi_gan": [],
   "yong_gan": [
    "庚",
    "庚"
   ]
  },
  "status": "OK"
 },
 {
  "case_id": "QT-0010",
  "bazi": "乙丑 庚辰 甲申 丙寅",
  "label": "good",
  "verdict": "pass",
  "engine_view": {
   "day_stem": "甲",
   "special": {
    "cong_type": "从财格",
    "cong_state": "CANDIDATE"
   },
   "climate_candidates": [
    "庚",
    "壬"
   ],
   "climate_state": "REGISTERED"
  },
  "text_extraction": {
   "xi_gan": [],
   "yong_gan": []
  },
  "status": "OK"
 },
 {
  "case_id": "QT-0011",
  "bazi": "丙寅 壬辰 甲辰 庚午",
  "label": "good",
  "verdict": "pass",
  "engine_view": {
   "day_stem": "甲",
   "special": {},
   "climate_candidates": [
    "庚",
    "壬"
   ],
   "climate_state": "REGISTERED"
  },
  "text_extraction": {
   "xi_gan": [],
   "yong_gan": []
  },
  "status": "OK"
 },
 {
  "case_id": "QT-0012",
  "bazi": "丙寅 壬辰 甲子 庚午",
  "label": "good",
  "verdict": "pass",
  "engine_view": {
   "day_stem": "甲",
   "special": {},
   "climate_candidates": [
    "庚",
    "壬"
   ],
   "climate_state": "REGISTERED"
  },
  "text_extraction": {
   "xi_gan": [],
   "yong_gan": [
    "庚"
   ]
  },
  "status": "OK"
 },
 {
  "case_id": "QT-0013",
  "bazi": "丙寅 壬辰 甲辰 丁卯",
  "label": "bad",
  "verdict": "pass",
  "engine_view": {
   "day_stem": "甲",
   "special": {
    "zhuanwang": "曲直格",
    "zhuanwang_state": "CONFIRMED"
   },
   "climate_candidates": [
    "庚",
    "壬"
   ],
   "climate_state": "REGISTERED"
  },
  "text_extraction": {
   "xi_gan": [],
   "yong_gan": []
  },
  "status": "OK"
 },
 {
  "case_id": "QT-0014",
  "bazi": "壬午 甲辰 甲寅 戊辰",
  "label": "bad",
  "verdict": "pass",
  "engine_view": {
   "day_stem": "甲",
   "special": {},
   "climate_candidates": [
    "庚",
    "壬"
   ],
   "climate_state": "REGISTERED"
  },
  "text_extraction": {
   "xi_gan": [],
   "yong_gan": []
  },
  "status": "OK"
 },
 {
  "case_id": "QT-0015",
  "bazi": "戊辰 丙辰 甲寅 甲子",
  "label": "good",
  "verdict": "pass",
  "engine_view": {
   "day_stem": "甲",
   "special": {},
   "climate_candidates": [
    "庚",
    "壬"
   ],
   "climate_state": "REGISTERED"
  },
  "text_extraction": {
   "xi_gan": [],
   "yong_gan": []
  },
  "status": "OK"
 }
]
```