# 裁决执行记录 · de_di 方案甲 + de_ling 统一 + f 程级 + 行号纠错（2026-10-09）

> 依据 User 互联网核对（pasted_content）确认的四条裁决 + 裁令三（41% 归因）：
> ① de_di 中余气=根（PZZQ L201 明文）→ 方案甲；② de_ling/f 统一口径 得令={旺,相}；
> ③ f 改程级（AND→加权）标 ENGINE_DEFINED；④ PZZQ L261 双向互含（非成>破）。
> 全部落 `p0_v2/bazi_gate.py` 工作区（未 commit，commit 归引擎线）。实测全程走 paipan() 权威入口。

## 一、4 处 patch（bazi_gate.py，git diff 36+/12-）

```
P1 de_di 方案甲  L337: bool(_heavy_eff) → bool(_heavy_eff or _light_eff)
   依据 PZZQ L201「长生禄旺根之重者; 墓库余气根之轻者」+ L204「不通根即判弱=谬论」
   下游 l3_contract["de_di"] 0 消费(grep 0 命中) → 零连带

P2 de_ling 统一  L443: == "旺" → in ("旺","相")
   依据 DTS L220「气象得令者吉」(原标 L225✗); 与 f(L373 已用"旺,相") 口径对齐

P3 f 改程级      L371-376: STRONG 由 得令 AND 有根 AND 党多 → 得令 AND (有根 OR 党多)
   ENGINE_DEFINED(程级序: 得令为主, 有根/党多程级辅); 相对权重标【待反标定】, 未拍数值
   f 输入仍用 dm_ben_eff(本气严口径), 不混 de_di 中余气, 避免跨口径

P4 注释行号纠错  L428-436: de_ling L225→L220 / de_di DTS L83-119→PZZQ L201-204(L68/L114/L122)
                  dang_duo L280-604→L275-302 / f L235-245→L230-240 / L431 恒等式错更正
```

## 二、实测（paipan 权威入口，reset kernel 防双实例）

```
de_di 方案甲 AFTER (4 代表盘):
  丁未庚戌庚辰丙子 金: de_di 旧F→新T (root_grade=余 中余气根, 案例判强) ✓
  丁酉癸卯丙辰丙申 火: de_di=F (root_grade=无 真无根) ✓ 不变
  癸卯甲寅丁卯甲辰 火: de_di 旧F→新T (root_grade=余) ✓
  壬辰壬寅甲寅庚午 木: de_di=T (root_grade=本 dm_ben_eff=2) ✓ 不变
  100 案例 中余气有根盘 de_di 翻转: 30 盘

f 程级 41% → 54% (可映射 305):
  BEFORE (AND 三全且): 一致 127/305 = 41%
  AFTER  (程级序):     一致 166/305 = 54%
  value 分布: STRONG 126 / WEAK 146 / EXTREME_WEAK 33
  分书: DTS 66% / SFTK 61% / PZZQ 52% / QTBJ 51% / SMTH 47% / YHZP 39%
```

## 三、诚实定性（不粉饰）

```
★ 41%→54% 是改善, 但 54% 不是天花板
  剩余 46% 大头仍是 层级差(丁): 归因坐实 169/178 单向"案例强/引擎弱"里 97% 断语含综合推论词
  → L3 单层值 对 综合结论词, 结构性差在缺 L4/P1/P2
  → f 程级改造解决的是 "有根/党多 OR 全且" 的漏判(丙1), 不解 层级差(丁)
★ f 程级加权 "有根 vs 党多" 相对权重 = 待反标定(未拍数值)
  现用 OR 并(不加权), 是"给 f 补程级"非"收紧 f", 但 精确权重仍需 L4 展开后综合判层定
★ de_di/de_ling/strength_verdict 下游 0 消费 → 本轮 patch 对 L4/P1 零连带(回归口径实测)
```

## 四、下一步（按裁令执行清单第 6/7）

```
6. L0/L1/L2/P3 无原典程级明文 → 标 ENGINE_DEFINED + 触发条件 (已在双审计表 v2 §5 列, 未落码, 非本轮)
7. 41% 已重测 = 54%; 真正验收要等 L4/P1 展开后 用【综合判层】对案例词 (非 L3 单层)
   ★ 41% 作为 L3 收口判据 作废, 54% 同 不作 L3 合格线 —— 层级差(丁) 非 f 能解
```
