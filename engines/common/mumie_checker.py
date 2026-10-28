# -*- coding: utf-8 -*-
"""母灭判定(纯布尔枚举v3)"""
import sys
sys.path.insert(0, '.')
from engines.common.dangzhong_counter import calc_dangzhong, is_dangzhong_strong

WX_SHENG = {"木": "水", "火": "木", "土": "火", "金": "土", "水": "金"}

def check_mumie(branches, stems, day_master):
    dz = calc_dangzhong(branches, stems)
    dm_wx = _stem_wx(day_master)
    yin_wx = WX_SHENG[dm_wx]
    dm_data = dz.get(dm_wx, {})
    yin_data = dz.get(yin_wx, {})
    yin_strong = is_dangzhong_strong(yin_data)
    dm_rootless = dm_data.get("ben_qi_root", 0) == 0
    if not (yin_strong and dm_rootless):
        return {"status": "", "taishi": "", "state": ""}
    # 官杀/食伤"透干+通根"制化通道: 有通道则母灭不成立(反例守卫)
    # 精确判据: 官杀或食伤须【透干>=1 AND 本气根>=1 或 中气根>=1】才算真制化
    _KE_ME = {"木": "火", "火": "水", "土": "金", "金": "土", "水": "木"}
    _SHENG_ME = {"木": "水", "火": "木", "土": "火", "金": "土", "水": "金"}
    guan_sha_wx = _KE_ME.get(dm_wx, "")
    shi_shang_wx = _SHENG_ME.get(dm_wx, "")
    for _esc_wx in (guan_sha_wx, shi_shang_wx):
        if not _esc_wx:
            continue
        _ed = dz.get(_esc_wx, {})
        _tou = _ed.get("stem_count", 0) >= 1
        _rooted = _ed.get("ben_qi_root", 0) >= 1 or _ed.get("zhong_qi_root", 0) >= 1
        if _tou and _rooted:
            return {"status": "", "taishi": "", "state": ""}
    state = "CONFIRMED" if yin_data.get("has_sanhui", False) else "CANDIDATE"
    return {"status": "母灭", "taishi": yin_wx + "多" + dm_wx + "熄", "state": state}

def _stem_wx(stem):
    table = {"甲": "木", "乙": "木", "丙": "火", "丁": "火", "戊": "土", "己": "土", "庚": "金", "辛": "金", "壬": "水", "癸": "水"}
    return table.get(stem, "")

if __name__ == "__main__":
    r1 = check_mumie(["卯", "寅", "卯", "辰"], ["癸", "甲", "丁", "甲"], "丁")
    print("木多火熄:", r1)
