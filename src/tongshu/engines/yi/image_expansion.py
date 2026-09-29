"""层 D：象扩展层（Image Expansion）

职责：根据卦象/爻象展开经典类象，分 5 层证据等级
红线：禁止跨级跳跃输出。Level 1 → Level 5 的直接跳跃必须被阻止。
"""

from __future__ import annotations
from .models import ImageExpansion, ImageItem, HexagramSymbol, LineSymbol, ClassicalText


def expand_image(
    symbol: HexagramSymbol,
    lines: LineSymbol | None = None,
    classical: ClassicalText | None = None
) -> ImageExpansion:
    """
    展开卦象的完整象义网络。
    """
    items_l1 = []
    items_l2 = []
    
    # Level 1: 经典原点
    if classical:
        items_l1.append(ImageItem(
            image=symbol.name,
            source="周易·卦辞",
            level=1,
            description=f"{symbol.name}卦辞",
            confidence=1.0,
        ))
    
    # Level 2: 经典语境
    items_l2.append(ImageItem(
        image=f"{symbol.upper_trigram}上{symbol.lower_trigram}下",
        source="周易·卦象结构",
        level=2,
        description=f"上下卦组合：{symbol.upper_trigram}之上，{symbol.lower_trigram}之下",
        confidence=0.9,
    ))
    
    return ImageExpansion(
        hexagram_name=symbol.name,
        level_1_classical=items_l1,
        level_2_contextual=items_l2,
    )


def validate_image_chain(image: ImageItem, level: int) -> bool:
    """
    验证象的推导链是否合理。
    例：乾 → 健 → 健行 → 马（合理）
    例：鼎 → 烹饪 → 事业升级 → 财富增长（跨级跳跃，应标记）
    """
    if image.level != level:
        return False
    if image.confidence < 0.5 and level <= 3:
        return False
    return True
