# -*- coding: utf-8 -*-
"""PATCH-080 喜忌Namespace Contract
铁律: 喜忌≠单namespace, 拆五域; 禁止总输出'喜=甲 忌=戊'
"""
import io, sys

XIJI_NAMESPACE = {
    "PZZQ.xiji_pattern": "格局喜忌(成格扶格之喜/破格之忌)",
    "DTS.xiji_strength": "旺衰喜忌(扶抑之喜/泄耗之忌)",
    "QTBJ.xiji_climate": "调候喜忌(寒暖燥湿之喜)",
    "SFTK.xiji_bingyao": "病药喜忌(去病为喜/助病为忌)",
    "SMTH.xiji_luck": "岁运喜忌(引动格局之喜忌)"
}


def xiji_producer(domain, element, direction):
    """
    domain: 五域之一; direction: 喜/忌
    return: 分namespace喜忌, 非总输出
    """
    if domain not in XIJI_NAMESPACE:
        return {"state": "xiji_state", "status": "NOT_REGISTERED", "domain": domain}
    return {
        "state": "xiji_state",
        "namespace": domain,
        "domain_role": XIJI_NAMESPACE[domain],
        "element": element,
        "direction": direction,
        "note": f"分域喜忌: {domain}内{element}为{direction}, 非全局总喜忌"
    }


if __name__ == '__main__':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    print("=== PATCH-080 喜忌五域 ===")
    for d in XIJI_NAMESPACE:
        print(f"  {d}: {XIJI_NAMESPACE[d]}")
    print("\nGC-001示例:")
    print(xiji_producer("PZZQ.xiji_pattern", "财", "喜"))
    print(xiji_producer("SFTK.xiji_bingyao", "印", "喜(药)"))
    print(xiji_producer("QTBJ.xiji_climate", "癸", "喜(调候)"))
    print("\n禁总输出: 喜=甲/忌=戊 这种跨域合并")
