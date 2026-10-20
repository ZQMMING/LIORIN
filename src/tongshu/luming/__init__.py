# -*- coding: utf-8 -*-
"""禄命法引擎 (Luming) 独立包。

独立于 ziping / ziwei / heluo / blind 等既有引擎, 只消费 BaziChart
(BaziEngine.compute 产物, 含禄命法基础事实: lu / nayin_five_element /
year_stem_ten_gods / year_growth / tai_yuan 等), 不修改、不重算排盘事实。

第一批功能 (确定性 + 判定层, 零破坏其他引擎):
  1. 年本三元立极视图 (干禄 / 支命 / 纳音身 + 各自旺衰)
  2. 禄马视图 (干禄 + 驿马, 互见/同宫)
  3. 化气成立判定 (六合得令透干 / 三合成局)
  4. 岁运消费接口 (大运; 小运来自 bazi_engine_spec, 待接)
"""
