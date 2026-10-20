import pytest

from foodbot.schema import AnalysisError, validate


def good(**over):
    base = {
        "is_food": True, "name": "雞腿便當", "unclear": False,
        "ingredients": [
            {"name": "白飯", "weight_g": 150, "kcal": 200},
            {"name": "雞腿", "weight_g": "120", "kcal": 250.5},
        ],
        "estimated_weight_g": 9999, "estimated_kcal": 9999,
    }
    base.update(over)
    return base


def test_totals_are_summed_not_trusted():
    a = validate(good())
    assert a.weight_g == 270 and a.kcal == 450.5 and a.is_food


def test_not_food_blanks_numbers():
    a = validate(good(is_food=False, name="馬克杯", ingredients=[]))
    assert (a.is_food, a.name, a.weight_g, a.kcal, a.ingredients) == (False, "馬克杯", None, None, ())


def test_not_food_ignores_garbage_numbers():
    a = validate({"is_food": False, "name": "貓", "unclear": False, "ingredients": [],
                  "estimated_kcal": "很多"})
    assert a.kcal is None


def test_more_than_8_ingredients_merged():
    items = [{"name": f"x{i}", "weight_g": 10, "kcal": 10} for i in range(10)]
    a = validate(good(ingredients=items))
    assert len(a.ingredients) == 8
    assert a.ingredients[-1].name == "其他" and a.ingredients[-1].kcal == 30
    assert a.kcal == 100


def test_empty_ingredients_uses_claude_total():
    a = validate(good(ingredients=[], estimated_weight_g=300, estimated_kcal="500"))
    assert (a.weight_g, a.kcal) == (300, 500)


def test_long_name_truncated():
    assert len(validate(good(name="a" * 100)).name) == 60


@pytest.mark.parametrize("raw", [
    None, "text", [], {},
    good(is_food="yes"), good(unclear=None), good(name=""), good(name="   "), good(name=5),
    good(ingredients="x"), good(ingredients=[{"name": "a", "weight_g": "很多", "kcal": 1}]),
    good(ingredients=[{"name": "a", "weight_g": "約150", "kcal": 1}]),
    good(ingredients=[{"name": "a", "weight_g": 1, "kcal": -5}]),
    good(ingredients=[{"name": "a", "weight_g": 1, "kcal": 5001}]),
    good(ingredients=[{"name": "a", "weight_g": 1, "kcal": float("nan")}]),
    good(ingredients=[{"name": "a", "weight_g": 1, "kcal": float("inf")}]),
    good(ingredients=[{"name": "a", "weight_g": 1, "kcal": ""}]),
    good(ingredients=[{"name": "a", "weight_g": 1, "kcal": True}]),
    good(ingredients=[{"name": "", "weight_g": 1, "kcal": 1}]),
    good(ingredients=[{"weight_g": 1, "kcal": 1}]),
    good(ingredients=[], estimated_kcal=None, estimated_weight_g=None),
])
def test_bad_results_raise_analysis_error(raw):
    with pytest.raises(AnalysisError):
        validate(raw)


def test_missing_required_field():
    raw = good()
    del raw["unclear"]
    with pytest.raises(AnalysisError):
        validate(raw)
