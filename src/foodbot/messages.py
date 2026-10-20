"""各種回覆文字（架構文件第 10 節）。"""

from .config import DAILY_LIMIT_PER_USER, MAX_IMAGES_PER_MESSAGE
from .schema import Analysis

FAILED = "分析失敗，請再傳一次"
QUEUE_FULL = "目前太多人在排隊，請稍後再傳。"
USER_LIMIT = f"你今天已達 {DAILY_LIMIT_PER_USER} 張上限，請明天再傳。"
TOTAL_LIMIT = "今天全體額度已用完，請明天再傳。"
TOO_MANY_IMAGES = f"一次最多處理 {MAX_IMAGES_PER_MESSAGE} 張，其餘已忽略。"
DISCORD_LIMIT = 1900


def partial_quota(n: int) -> str:
    return f"今天只剩 {n} 張額度，其餘已忽略。"


def processing(ahead: int) -> str:
    return "收到，分析中…" if ahead == 0 else f"收到，前面還有 {ahead} 張在排隊…"


def _safe(text: str) -> str:
    """Claude 回來的字：讓 @ 不會真的提到任何人。"""
    return text.replace("@", "@​").replace("<#", "<​#")


def _num(x: float) -> str:
    return f"{round(x):,}"


def result(user_id: int, a: Analysis, day_total: float) -> str:
    head = f"<@{user_id}>"
    if not a.is_food:
        body = (f"{head}\n你傳的不是食物，是{_safe(a.name)}。\n"
                f"你今天已攝取：{_num(day_total)} kcal（沒有變動）")
        return body[:DISCORD_LIMIT]
    lines = [head, f"這是食物：{_safe(a.name)}"]
    if a.ingredients:
        lines.append("成份：")
        lines += [f"・{_safe(i.name)}  {_num(i.weight_g)}g，約 {_num(i.kcal)} kcal"
                  for i in a.ingredients]
    lines.append(f"整餐：{_num(a.weight_g)}g，約 {_num(a.kcal)} kcal")
    if a.unclear:
        lines.append("照片不清楚，數值僅供參考")
    lines.append(f"你今天已攝取：{_num(day_total)} kcal")
    lines.append("（以上為估計值）")
    return "\n".join(lines)[:DISCORD_LIMIT]


def ingredients_text(a: Analysis) -> str:
    """Excel「成份」欄：食物逐項；不是食物寫判定出的東西。"""
    if not a.is_food:
        return a.name
    return "；".join(f"{i.name} {_num(i.weight_g)}g {_num(i.kcal)}kcal"
                     for i in a.ingredients) or a.name
