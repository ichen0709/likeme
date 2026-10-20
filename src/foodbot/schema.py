"""claude -p 的 JSON 規格，以及 agent 對結果的檢查（架構文件第 5 節）。"""

import math
import re
from dataclasses import dataclass

MAX_INGREDIENTS = 8
NAME_MAX_CHARS = 60
INGREDIENT_NAME_MAX_CHARS = 30
ITEM_MAX = 5000  # 單項重量（公克）、熱量（大卡）上限

JSON_SCHEMA = {
    "type": "object",
    "properties": {
        "is_food": {"type": "boolean", "description": "照片是不是食物"},
        "name": {"type": "string", "description": "食物名稱；不是食物時寫它是什麼東西"},
        "ingredients": {
            "type": "array",
            "description": "成份清單，最多 8 項；不是食物時給空清單",
            "items": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "weight_g": {"type": "number"},
                    "kcal": {"type": "number"},
                },
                "required": ["name", "weight_g", "kcal"],
            },
        },
        "estimated_weight_g": {"type": ["number", "null"], "description": "整餐估計重量（公克）"},
        "estimated_kcal": {"type": ["number", "null"], "description": "整餐估計熱量（大卡）"},
        "unclear": {"type": "boolean", "description": "照片是否模糊、不確定"},
    },
    "required": ["is_food", "name", "ingredients", "unclear"],
}

_PLAIN_NUMBER = re.compile(r"^[+-]?\d+(\.\d+)?$")


class AnalysisError(Exception):
    """結果不合格；訊息只給終端機看，不顯示給使用者。"""


@dataclass(frozen=True)
class Ingredient:
    name: str
    weight_g: float
    kcal: float


@dataclass(frozen=True)
class Analysis:
    is_food: bool
    name: str
    ingredients: tuple[Ingredient, ...]
    weight_g: float | None
    kcal: float | None
    unclear: bool


def _number(value, what: str) -> float:
    if isinstance(value, bool):
        raise AnalysisError(f"{what} 不是數字")
    if isinstance(value, (int, float)):
        number = float(value)
    elif isinstance(value, str) and _PLAIN_NUMBER.match(value.strip()):
        number = float(value.strip())
    else:
        raise AnalysisError(f"{what} 不是數字：{value!r}"[:100])
    if not math.isfinite(number):
        raise AnalysisError(f"{what} 不是有限數字")
    return number


def _in_range(number: float, what: str) -> float:
    if not 0 <= number <= ITEM_MAX:
        raise AnalysisError(f"{what} 超出合理範圍：{number}")
    return number


def _boolean(value, what: str) -> bool:
    if not isinstance(value, bool):
        raise AnalysisError(f"{what} 不是是／否")
    return value


def validate(raw) -> Analysis:
    if not isinstance(raw, dict):
        raise AnalysisError("結果不是 JSON 物件")
    for key in ("is_food", "name", "ingredients", "unclear"):
        if key not in raw:
            raise AnalysisError(f"缺少欄位 {key}")
    is_food = _boolean(raw["is_food"], "is_food")
    unclear = _boolean(raw["unclear"], "unclear")
    if not isinstance(raw["name"], str):
        raise AnalysisError("name 不是文字")
    name = raw["name"].strip()[:NAME_MAX_CHARS].strip()
    if not name:
        raise AnalysisError("name 是空的")
    if not isinstance(raw["ingredients"], list):
        raise AnalysisError("ingredients 不是清單")

    if not is_food:
        # 不是食物：忽略 Claude 給的任何重量、熱量，強制留空
        return Analysis(False, name, (), None, None, unclear)

    items: list[Ingredient] = []
    for i, item in enumerate(raw["ingredients"]):
        if not isinstance(item, dict) or not isinstance(item.get("name"), str):
            raise AnalysisError(f"成份 {i + 1} 格式不對")
        ing_name = item["name"].strip()[:INGREDIENT_NAME_MAX_CHARS].strip()
        if not ing_name:
            raise AnalysisError(f"成份 {i + 1} 沒有名稱")
        items.append(Ingredient(
            ing_name,
            _in_range(_number(item.get("weight_g"), f"成份 {i + 1} 重量"), f"成份 {i + 1} 重量"),
            _in_range(_number(item.get("kcal"), f"成份 {i + 1} 熱量"), f"成份 {i + 1} 熱量"),
        ))
    if len(items) > MAX_INGREDIENTS:
        rest = items[MAX_INGREDIENTS - 1:]
        items = items[:MAX_INGREDIENTS - 1] + [Ingredient(
            "其他", sum(r.weight_g for r in rest), sum(r.kcal for r in rest))]

    if items:  # 整餐數字由 agent 自己加總，不採信 Claude 給的總數
        weight = sum(i.weight_g for i in items)
        kcal = sum(i.kcal for i in items)
    else:
        weight = _in_range(_number(raw.get("estimated_weight_g"), "整餐重量"), "整餐重量")
        kcal = _in_range(_number(raw.get("estimated_kcal"), "整餐熱量"), "整餐熱量")
    return Analysis(True, name, tuple(items), round(weight, 1), round(kcal, 1), unclear)
