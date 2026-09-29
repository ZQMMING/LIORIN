"""P1: 真太阳时计算 + 全球时间层

真太阳时 = 北京时间 + 经度差修正 + 均时差

公式:
    真太阳时 = 标准时间 + (经度 - 120) × 4分钟 + 均时差

均时差来源:
    - 预计算表（年历精度±2秒）优先
    - 天文算法（NASA JPL DE440）备选
"""
from __future__ import annotations
import json
import logging
import psycopg2
from datetime import datetime, timedelta
from typing import Tuple, Optional

from tongshu.db.config import get_kb_dsn

log = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════════
# 均时差预计算表（近似值，精度±15秒）
# 来源: NASA JPL Horizons 简化版
# 格式: (month, day) -> equation_of_time_seconds
# ═══════════════════════════════════════════════════════════════════
EQUATION_OF_TIME_TABLE = {
    (1, 1): -3, (1, 15): 0, (1, 31): 14,
    (2, 15): 14, (2, 28): 6,
    (3, 15): -10, (3, 31): -7,
    (4, 15): 0, (4, 30): 2,
    (5, 15): 3, (5, 31): -2,
    (6, 15): -4, (6, 30): 0,
    (7, 15): 6, (7, 31): 10,
    (8, 15): 7, (8, 31): -2,
    (9, 15): -8, (9, 30): -10,
    (10, 15): -6, (10, 31): 3,
    (11, 15): 12, (11, 30): 16,
    (12, 15): 11, (12, 31): 0,
}


def get_equation_of_time(year: int, month: int, day: int) -> float:
    """
    获取指定日期的均时差（秒）。
    
    均时差 = 真太阳时 - 平太阳时
    
    正值表示真太阳时快于平太阳时
    负值表示真太阳时慢于平太阳时
    """
    # P1-3 统一：委托 eot.py (Meeus 级数)，返回秒。
    # 原预计算表插值实现失效（对表中缺失日期恒返回 0），已弃用表查询；
    # EQUATION_OF_TIME_TABLE 保留作为文档参考（NASA JPL 近似点）。
    from .eot import equation_of_time as _eot

    return _eot(datetime(year, month, day).date()) * 60.0


def calculate_true_solar_time(
    beijing_time: datetime,
    longitude: float,
    latitude: float = 31.0,
    use_equation_of_time: bool = True
) -> dict:
    """
    计算真太阳时。
    
    Args:
        beijing_time: 北京时间（东八区）
        longitude: 当地经度（东经为正）
        latitude: 当地纬度（北纬为正）
        use_equation_of_time: 是否使用均时差修正
    
    Returns:
        {
            "beijing_time": datetime,
            "longitude_correction_minutes": float,
            "equation_of_time_seconds": float,
            "true_solar_time": datetime,
            "timezone_offset": float
        }
    """
    # 北京时间基准经度
    BASE_LONGITUDE = 120.0
    
    # 1. 经度差修正（分钟）
    longitude_diff = longitude - BASE_LONGITUDE
    longitude_correction_minutes = longitude_diff * 4  # 每度4分钟
    
    # 2. 均时差修正（秒转分钟）
    if use_equation_of_time:
        eot_seconds = get_equation_of_time(
            beijing_time.year, 
            beijing_time.month, 
            beijing_time.day
        )
        eot_correction_minutes = eot_seconds / 60.0
    else:
        eot_correction_minutes = 0
    
    # 3. 总修正
    total_correction_minutes = longitude_correction_minutes + eot_correction_minutes
    
    # 4. 计算真太阳时
    true_solar_time = beijing_time + timedelta(minutes=total_correction_minutes)
    
    return {
        "beijing_time": beijing_time.isoformat(),
        "longitude": longitude,
        "latitude": latitude,
        "longitude_correction_minutes": round(longitude_correction_minutes, 2),
        "equation_of_time_seconds": round(eot_seconds if use_equation_of_time else 0, 2),
        "total_correction_minutes": round(total_correction_minutes, 2),
        "true_solar_time": true_solar_time.isoformat(),
        "timezone_offset": 8.0 + (longitude - BASE_LONGITUDE) / 15.0
    }


def calculate_solar_terms_for_location(
    year: int,
    longitude: float,
    latitude: float
) -> list:
    """
    计算指定位置的节气时刻。
    
    TODO: 需要完整的天文算法支持
    当前使用简化版
    """
    # 简化版：固定时刻 + 经度修正
    base_solar_terms = get_base_solar_terms(year)
    
    longitude_correction_minutes = (longitude - 120.0) * 4
    
    adjusted_terms = []
    for term in base_solar_terms:
        adjusted_time = term["time"] + timedelta(minutes=longitude_correction_minutes)
        adjusted_terms.append({
            **term,
            "local_time": adjusted_time.isoformat(),
            "correction_minutes": round(longitude_correction_minutes, 2)
        })
    
    return adjusted_terms


def get_base_solar_terms(year: int) -> list:
    """
    获取基准节气时刻（北京时间）。
    TODO: 从 solar_terms 表或天文算法获取
    """
    # 简化版：固定日期 + 时刻
    return [
        {"name": "立春", "month": 2, "day": 4, "hour": 10, "minute": 33},
        {"name": "雨水", "month": 2, "day": 19, "hour": 22, "minute": 45},
        {"name": "惊蛰", "month": 3, "day": 6, "hour": 0, "minute": 44},
        {"name": "春分", "month": 3, "day": 21, "hour": 9, "minute": 33},
        {"name": "清明", "month": 4, "day": 5, "hour": 13, "minute": 14},
        {"name": "谷雨", "month": 4, "day": 20, "hour": 20, "minute": 34},
        {"name": "立夏", "month": 5, "day": 6, "hour": 2, "minute": 16},
        {"name": "小满", "month": 5, "day": 21, "hour": 9, "minute": 24},
        {"name": "芒种", "month": 6, "day": 6, "hour": 4, "minute": 12},
        {"name": "夏至", "month": 6, "day": 21, "hour": 22, "minute": 12},
        {"name": "小暑", "month": 7, "day": 8, "hour": 1, "minute": 45},
        {"name": "大暑", "month": 7, "day": 23, "hour": 6, "minute": 0},
        {"name": "立秋", "month": 8, "day": 8, "hour": 7, "minute": 20},
        {"name": "处暑", "month": 8, "day": 24, "hour": 21, "minute": 11},
        {"name": "白露", "month": 9, "day": 8, "hour": 1, "minute": 24},
        {"name": "秋分", "month": 9, "day": 23, "hour": 10, "minute": 43},
        {"name": "寒露", "month": 10, "day": 9, "hour": 1, "minute": 40},
        {"name": "霜降", "month": 10, "day": 24, "hour": 13, "minute": 16},
        {"name": "立冬", "month": 11, "day": 8, "hour": 6, "minute": 58},
        {"name": "小雪", "month": 11, "day": 23, "hour": 1, "minute": 25},
        {"name": "大雪", "month": 12, "day": 7, "hour": 18, "minute": 53},
        {"name": "冬至", "month": 12, "day": 22, "hour": 9, "minute": 13},
        {"name": "小寒", "month": 1, "day": 6, "hour": 4, "minute": 12},
        {"name": "大寒", "month": 1, "day": 20, "hour": 14, "minute": 12},
    ]


def create_global_time_table(conn) -> dict:
    """创建 global_time_params 表并插入数据。"""
    cur = conn.cursor()
    
    # 创建表
    cur.execute("""
        CREATE TABLE IF NOT EXISTS global_time_params (
            param_key       VARCHAR(50) PRIMARY KEY,
            param_value     TEXT NOT NULL,
            param_type      VARCHAR(20) CHECK (param_type IN ('number', 'string', 'json')),
            description     TEXT,
            source_ref      TEXT,
            created_at      TIMESTAMPTZ DEFAULT NOW()
        )
    """)
    
    # 插入全球时区参数
    params = [
        ("beijing_longitude", "120.0", "number", "北京时间基准经度（东经120度）", "《时宪书》"),
        ("beijing_timezone_offset", "8.0", "number", "北京时间时区偏移（UTC+8）", "ISO 8601"),
        ("equation_of_time_precision", "15", "number", "均时差精度（秒）", "NASA JPL DE440"),
        ("true_solar_time_default", "true", "string", "默认启用真太阳时", "配置项"),
    ]
    
    inserted = 0
    for key, value, ptype, desc, source in params:
        cur.execute("""
            INSERT INTO global_time_params (param_key, param_value, param_type, description, source_ref)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (param_key) DO NOTHING
        """, (key, value, ptype, desc, source))
        inserted += cur.rowcount or 0
    
    conn.commit()
    return {"global_time_params_table": 1, "inserted": inserted}


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # 测试真太阳时计算
    test_cases = [
        {"name": "北京", "longitude": 116.4, "lat": 39.9},
        {"name": "上海", "longitude": 121.5, "lat": 31.2},
        {"name": "乌鲁木齐", "longitude": 87.6, "lat": 43.8},
        {"name": "伦敦", "longitude": -0.1, "lat": 51.5},
    ]
    
    print("=== 真太阳时计算测试 ===")
    for tc in test_cases:
        beijing_time = datetime(2025, 8, 21, 12, 0, 0)
        result = calculate_true_solar_time(beijing_time, tc["longitude"], tc["lat"])
        print(f"\n{tc['name']}:")
        print(f"  北京时间: {result['beijing_time']}")
        print(f"  经度修正: {result['longitude_correction_minutes']} 分钟")
        print(f"  真太阳时: {result['true_solar_time']}")
    
    # 测试数据库表创建
    conn = psycopg2.connect(get_kb_dsn())
    with conn.cursor() as _cur:
        _cur.execute("SELECT current_database()")
        _db = _cur.fetchone()[0]
        if _db != "shuntian_kb":
            raise RuntimeError(f"Expected shuntian_kb, connected to {_db}")
    try:
        stats = create_global_time_table(conn)
        print(f"\n=== 数据库表创建 ===")
        print(json.dumps(stats, ensure_ascii=False))
    finally:
        conn.close()
