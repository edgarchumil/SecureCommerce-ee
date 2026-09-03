from dataclasses import dataclass


@dataclass(frozen=True)
class ScoredAnswer:
    function_code: str
    function_name: str
    category_code: str
    category_name: str
    weight: float
    maturity: int | None


def calculate_scores(rows: list[ScoredAnswer], target: int) -> dict[str, object]:
    function_groups: dict[tuple[str, str], list[ScoredAnswer]] = {}
    category_groups: dict[tuple[str, str], list[ScoredAnswer]] = {}
    for row in rows:
        function_groups.setdefault((row.function_code, row.function_name), []).append(row)
        category_groups.setdefault((row.category_code, row.category_name), []).append(row)

    def summarize(code: str, name: str, items: list[ScoredAnswer]) -> dict[str, object]:
        weight = sum(item.weight for item in items)
        achieved = sum((item.maturity or 0) * item.weight for item in items)
        score = round((achieved / (4 * weight)) * 100, 2) if weight else 0.0
        target_score = round(target / 4 * 100, 2)
        return {
            "code": code,
            "name": name,
            "score": score,
            "target": target_score,
            "gap": round(max(target_score - score, 0), 2),
            "answered": sum(item.maturity is not None for item in items),
            "total": len(items),
        }

    by_function = [summarize(*key, items) for key, items in function_groups.items()]
    by_category = [summarize(*key, items) for key, items in category_groups.items()]
    overall = summarize("GLOBAL", "Global", rows)
    return {
        "current_profile": overall["score"],
        "target_profile": overall["target"],
        "gap": overall["gap"],
        "answered": overall["answered"],
        "total": overall["total"],
        "by_function": by_function,
        "by_category": by_category,
    }
