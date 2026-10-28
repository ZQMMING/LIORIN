# -*- coding: utf-8 -*-
"""河洛引擎命令行入口（CLI）—— 供服务器/运维直接调用，无需写代码。

用法
----
::

    # 排一个盘（默认输出 JSON）
    heluo-engine compute --birth 1983-11-03 --time 12:00 --gender male \
        --target 2026-10-23

    # 只看关键字段
    heluo-engine compute --birth 1983-11-03 --time 12:00 --brief

    # 看解读层（平台信号 / 诊断 / 指引 / 维度视图 / 事件候选）
    heluo-engine interpret --birth 1983-11-03 --time 12:00 --target 2026-10-23

    # 查判词（某卦某爻）
    heluo-engine gua --name 观 --yao 初六

    # 自检：确认包内资源齐备（部署后第一条命令）
    heluo-engine doctor

    # 版本与安装位置
    heluo-engine --version
    heluo-engine --where

设计约束
--------
* **零依赖**：只用标准库（argparse/json）⇒ 装完即用，不引入额外依赖面。
* **退出码**：0 = 成功；1 = 参数/运行错误（便于 shell 判成败）。
* **不吞错**：失败信息走 stderr，不静默。
"""
from __future__ import annotations

import argparse
import json
import locale
import sys
from datetime import datetime
from typing import Any, Optional


def _parse_birth(s: str) -> tuple[int, int, int, int]:
    """``YYYY-MM-DD``（可选带 ``HH:MM``）→ (y, m, d, hour)。"""
    s = (s or "").strip()
    if " " in s:
        s = s.replace(" ", "T")
    if "T" in s:
        date_part, _, time_part = s.partition("T")
        hour = int((time_part or "0").split(":")[0] or 0)
    else:
        date_part, hour = s, 0
    y, m, d = (int(x) for x in date_part.split("-"))
    return (y, m, d, hour)


def _parse_time(s: Optional[str]) -> int:
    if not s:
        return 0
    s = s.strip()
    if ":" in s:
        return int(s.split(":")[0])
    return int(s)


def _json_default(o: Any) -> Any:
    if isinstance(o, datetime):
        return o.isoformat()
    if hasattr(o, "to_dict"):
        try:
            return o.to_dict()
        except Exception:
            pass
    if hasattr(o, "__dict__"):
        return {k: v for k, v in vars(o).items() if not k.startswith("_")}
    return str(o)


def _cmd_compute(args: argparse.Namespace) -> int:
    from heluo_engine import HeluoAdapter

    y, m, d, h_from_birth = _parse_birth(args.birth)
    hour = _parse_time(args.time) or h_from_birth
    ad = HeluoAdapter()
    res = ad.compute((y, m, d, hour), gender=args.gender,
                     target_date=args.target)

    if args.brief:
        out = {
            "prenatal": res.prenatal.hexagram_name,
            "yuantang": res.yuantang.yuantang,
            "postnatal": res.postnatal.hexagram_name,
            "target_date": res.target_date,
            "era": res.era,
        }
        if res.hua_gong:
            out["hua_gong"] = res.hua_gong.state.value
        if res.seasonal_hexagram:
            out["jiehou"] = {
                "jq": res.seasonal_hexagram.get("jq_name"),
                "main_gua": res.seasonal_hexagram.get("main_gua"),
                "result_gua": res.seasonal_hexagram.get("result_gua"),
            }
        print(json.dumps(out, ensure_ascii=False, indent=2))
        return 0

    payload = {
        "prenatal": res.prenatal.hexagram_name,
        "yuantang": res.yuantang.yuantang,
        "postnatal": res.postnatal.hexagram_name,
        "numbers": {
            "tian_shu": res.numbers.tian_shu,
            "di_shu": res.numbers.di_shu,
        },
        "era": res.era,
        "era_source": res.era_source,
        "target_date": res.target_date,
        "target_date_caliber": res.target_date_caliber,
        "target_date_note": res.target_date_note,
        "structure": res.structure.to_dict() if hasattr(res.structure, "to_dict")
                     else (str(res.structure) if res.structure else None),
    }
    if res.hua_gong:
        payload["hua_gong"] = {
            "state": res.hua_gong.state.value,
            "trigram": res.hua_gong.huagong_trigram,
            "level": getattr(res.hua_gong, "level", None),
        }
    if res.seasonal_hexagram:
        payload["jiehou"] = res.seasonal_hexagram
    if res.guajie:
        payload["guajie_keys"] = sorted(res.guajie.keys())
    print(json.dumps(payload, ensure_ascii=False, indent=2, default=_json_default))
    return 0


def _cmd_interpret(args: argparse.Namespace) -> int:
    from heluo_engine import HeluoAdapter

    y, m, d, h_from_birth = _parse_birth(args.birth)
    hour = _parse_time(args.time) or h_from_birth
    res = HeluoAdapter().compute((y, m, d, hour), gender=args.gender,
                                 target_date=args.target)
    it = res.interpretation or {}
    payload = {k: it.get(k) for k in (
        "platform_signals", "diagnosis", "guidance", "metrics",
        "hexagram_state", "dimension_view", "dimension_coverage",
        "event_candidates", "warnings",
    ) if k in it}
    print(json.dumps(payload, ensure_ascii=False, indent=2, default=_json_default))
    return 0


def _cmd_gua(args: argparse.Namespace) -> int:
    from heluo_engine.engines.heluo.guajie import query_yao_duan

    y = query_yao_duan(args.name, args.yao)
    if y is None:
        print("查无此爻：%s %s" % (args.name, args.yao), file=sys.stderr)
        return 1
    print(json.dumps({
        "gua": args.name, "yao": y.yao, "ci": y.ci,
        "xiang": y.xiang, "yi": y.yi,
    }, ensure_ascii=False, indent=2))
    return 0


def _cmd_doctor(args: argparse.Namespace) -> int:
    """部署自检：确认包内资源齐备、可定位。"""
    import heluo_engine
    from heluo_engine._paths import pkg_data, pkg_orig, pkg_doc

    checks = []
    ok = True
    for label, path, must in (
        ("包位置", heluo_engine.__file__, True),
        ("data/canping", pkg_data("canping"), True),
        ("data/guajie_data.json", pkg_data("guajie_data.json"), True),
        ("data/kuozhan_duanyu.json", pkg_data("kuozhan_duanyu.json"), True),
        ("orig/河洛真数_起例卷之上.txt", pkg_orig("河洛真数_起例卷之上.txt"), True),
        ("docs/河洛回灌接线决策单_20261024.md",
         pkg_doc("河洛回灌接线决策单_20261024.md"), False),
    ):
        import os
        exists = bool(path) and os.path.exists(str(path))
        need = must and not exists
        if need:
            ok = False
        checks.append({"item": label, "path": str(path),
                       "exists": exists, "required": must,
                       "status": "MISSING" if need else ("OK" if exists else "absent")})

    # ⚠ 2026-10-25：CWD 里若有与标准库同名的 .py（inspect.py / json.py…），
    #   会**shadow 标准库** ⇒ dataclasses 在 import 期抛
    #   ``module 'inspect' has no attribute 'get_annotations'``，
    #   且那个 shadow 文件会被执行并向 stdout 打印无关内容，把错误淹没。
    #   （本项目实测踩过：系统 TEMP 里的 inspect.py。）
    #   ⇒ 在 doctor 里显式查，避免部署方踩坑时无从判断。
    import os
    shadowed = []
    try:
        for _name in set(sys.stdlib_module_names):
            _p = os.path.join(os.getcwd(), _name + ".py")
            if os.path.exists(_p):
                shadowed.append(_p)
    except Exception:
        pass
    if shadowed:
        ok = False
    checks.append({
        "item": "CWD 无标准库同名 .py（否则会 shadow 标准库）",
        "path": os.getcwd(),
        "exists": not shadowed,
        "required": True,
        "status": "SHADOWED: " + ", ".join(sorted(shadowed)[:5]) if shadowed else "OK",
    })

    print(json.dumps({
        "version": heluo_engine.__version__,
        "package": os.path.dirname(heluo_engine.__file__),
        "checks": checks,
        "result": "PASS" if ok else "FAIL",
    }, ensure_ascii=False, indent=2))
    return 0 if ok else 1


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="heluo-engine",
        description="《河洛真数》推命引擎 —— 命令行入口",
    )
    p.add_argument("--version", action="store_true", help="打印版本")
    p.add_argument("--where", action="store_true", help="打印包安装位置")
    sub = p.add_subparsers(dest="cmd")

    c = sub.add_parser("compute", help="排一个盘")
    c.add_argument("--birth", required=True, help="出生日期 YYYY-MM-DD（可带 HH:MM）")
    c.add_argument("--time", default="", help="出生时刻 HH:MM（默认 0 时）")
    c.add_argument("--gender", default="male", choices=["male", "female"])
    c.add_argument("--target", default="", help="目标日 YYYY-MM-DD（默认今天·北京时间）")
    c.add_argument("--brief", action="store_true", help="只输出关键字段")
    c.set_defaults(func=_cmd_compute)

    i = sub.add_parser("interpret", help="解读层输出")
    i.add_argument("--birth", required=True)
    i.add_argument("--time", default="")
    i.add_argument("--gender", default="male", choices=["male", "female"])
    i.add_argument("--target", default="")
    i.set_defaults(func=_cmd_interpret)

    g = sub.add_parser("gua", help="查判词")
    g.add_argument("--name", required=True, help="卦名（简称，如 观）")
    g.add_argument("--yao", required=True, help="爻名（如 初六）")
    g.set_defaults(func=_cmd_gua)

    d = sub.add_parser("doctor", help="部署自检（资源是否齐备）")
    d.set_defaults(func=_cmd_doctor)
    return p


def _fix_argv_encoding() -> None:
    """修正 Windows 上 ``sys.argv`` 的中文乱码。

    ⚠ 2026-10-25 实测（Windows）：命令行参数在**创建进程时**按 ANSI 代码页
      （= 区域编码，中文 Windows = cp936/GBK）编码；Python 启动时按
      ``sys.getfilesystemencoding()``（3.6+ 在 Windows 上是 **utf-8**）解码
      ⇒ **编码口径不一致**，卦名「观」变成乱码，CLI 查词直接查不到。

      方向：``ansi(cp936)`` 字节 → ``utf-8`` 文本。

    修法：把 ``sys.argv`` 按「区域编码 → 文件系统编码」**尝试**重解码一次；
    解不出（说明本来就是对的）就保持原样。
    ⚠ 重解码是**幂等安全**的：已是正确 UTF-8 文本时
      ``encode(ansi).decode(utf8)`` 会抛异常（GBK 解不了某些字节）
      或解出同样内容 ⇒ 回退原值。
    """
    enc = (sys.getfilesystemencoding() or "utf-8")
    try:
        ansi = locale.getpreferredencoding(False) or enc
    except Exception:
        ansi = enc
    if ansi.lower().replace("_", "-") == enc.lower().replace("_", "-"):
        return
    new_argv = [sys.argv[0]]
    for a in sys.argv[1:]:
        try:
            new_argv.append(a.encode(ansi, errors="strict").decode(enc))
        except (UnicodeEncodeError, UnicodeDecodeError):
            new_argv.append(a)
    sys.argv = new_argv


def _fix_stdout_encoding() -> None:
    """把 stdout 固定为 UTF-8（否则中文 JSON 会在 Windows 上变乱码）。

    ⚠ 2026-10-25 实测：``print(json.dumps(..., ensure_ascii=False))``
      输出的是 **UTF-8 字节**，但 Windows 控制台/管道默认按 ANSI 代码页
      （cp936/GBK）解码 ⇒ 业务侧拿到的 JSON 里中文全成 ``�``，
      ``json.loads`` 虽能过，字段值却是坏的。

    修法：把 ``sys.stdout``/``sys.stderr`` 重绑到 UTF-8 包装器
    （``errors="replace"`` 避免个别字符直接抛异常）。
    """
    for stream_name in ("stdout", "stderr"):
        stream = getattr(sys, stream_name, None)
        if stream is None:
            continue
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError, OSError):
            pass


def main(argv: Optional[list[str]] = None) -> int:
    if argv is None:
        _fix_argv_encoding()
    _fix_stdout_encoding()
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.version:
        import heluo_engine
        print(heluo_engine.__version__)
        return 0
    if args.where:
        import heluo_engine
        import os
        print(os.path.dirname(heluo_engine.__file__))
        return 0
    if not getattr(args, "cmd", None):
        parser.print_help()
        return 1

    try:
        return args.func(args)
    except Exception as exc:                     # noqa: BLE001
        print("执行失败：%s: %s" % (type(exc).__name__, exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
