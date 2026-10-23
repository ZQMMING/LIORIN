# -*- coding: utf-8 -*-
"""量化地点注册表的覆盖缺口（重点：内地主要城市 + 省+市拼接写法）。"""
import io
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))
os.environ.setdefault("TONGSHU_ALLOW_ZIWEI_STUB", "1")

from heluo_engine.engines.time.location_registry import LocationRegistry  # noqa: E402

reg = LocationRegistry()
alias = set(getattr(reg, "_by_alias", {}))
out = []

out.append("别名总数: %d" % len(alias))

# 广东 21 地级市，逐个查（用户实际会写的名字）
GD = ["广州", "韶关", "深圳", "珠海", "汕头", "佛山", "江门", "湛江", "茂名",
      "肇庆", "惠州", "梅州", "汕尾", "河源", "阳江", "清远", "东莞", "中山",
      "潮州", "揭阳", "云浮"]
out.append("")
out.append("== 广东 21 地级市 ==")
miss = []
for c in GD:
    ok = c in alias
    if not ok:
        miss.append(c)
    out.append("  %-4s %s" % (c, "✅" if ok else "❌ 不在注册表"))
out.append("  → 缺 %d 个: %s" % (len(miss), "、".join(miss)))

# 省+市拼接（用户最自然的写法）
out.append("")
out.append("== 「省+市」拼接写法 ==")
for s in ["广东中山", "广东广州", "广东深圳", "浙江省杭州市", "江苏省南京市",
          "北京市", "上海市", "广东，中国", "中山"]:
    out.append("  %-12s %s" % (s, "✅" if s in alias else "❌"))

# 其他省份代表城市
out.append("")
out.append("== 其他省份代表城市 ==")
OTHER = ["杭州", "南京", "武汉", "成都", "西安", "长沙", "郑州", "济南", "青岛",
         "沈阳", "大连", "哈尔滨", "长春", "福州", "厦门", "南昌", "合肥",
         "石家庄", "太原", "昆明", "贵阳", "南宁", "兰州", "西宁", "银川",
         "乌鲁木齐", "呼和浩特", "海口", "拉萨", "重庆", "天津"]
miss2 = [c for c in OTHER if c not in alias]
out.append("  在库 %d/%d；缺: %s"
           % (len(OTHER) - len(miss2), len(OTHER), "、".join(miss2)))

io.open(ROOT / "tools" / "heluo" / "quzheng_20261008" / "loc_coverage.txt",
        "w", encoding="utf-8", newline="\n").write("\n".join(out))
print("\n".join(out))