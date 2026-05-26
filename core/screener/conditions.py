"""Stock screening condition functions."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable


@dataclass
class Condition:
    field: str
    operator: str  # gt, lt, gte, lte, eq, between
    value: float
    label: str = ""

    def __post_init__(self):
        if not self.label:
            self.label = f"{self.field} {self.operator} {self.value}"


PRESET_CONDITIONS: dict[str, list[Condition]] = {
    "value_stocks": [
        Condition("pe", "lt", 15, "PE < 15"),
        Condition("pb", "lt", 1.5, "PB < 1.5"),
        Condition("roe", "gt", 10, "ROE > 10%"),
    ],
    "growth_stocks": [
        Condition("roe", "gt", 15, "ROE > 15%"),
        Condition("pe", "lt", 40, "PE < 40"),
    ],
    "oversold": [
        Condition("rsi14", "lt", 30, "RSI(14) < 30 (超卖)"),
    ],
    "overbought": [
        Condition("rsi14", "gt", 70, "RSI(14) > 70 (超买)"),
    ],
    "ma_golden_cross": [
        Condition("ma5", "gt", 0, "MA5 > MA10 (即将金叉)"),
    ],
}


def evaluate_condition(condition: Condition, stock_data: dict[str, Any]) -> bool:
    value = stock_data.get(condition.field)
    if value is None:
        return False
    try:
        value = float(value)
    except (ValueError, TypeError):
        return False

    op = condition.operator
    threshold = float(condition.value)

    if op == "gt":
        return value > threshold
    elif op == "lt":
        return value < threshold
    elif op == "gte":
        return value >= threshold
    elif op == "lte":
        return value <= threshold
    elif op == "eq":
        return abs(value - threshold) < 1e-6
    elif op == "between":
        return False  # handled separately
    return False


def run_screen(stocks: list[dict], conditions: list[Condition]) -> list[dict]:
    results = []
    for stock in stocks:
        match_count = 0
        passed = True
        for cond in conditions:
            if evaluate_condition(cond, stock):
                match_count += 1
            else:
                passed = False
        if passed:
            stock["match_score"] = match_count
            results.append(stock)
    results.sort(key=lambda x: x.get("match_score", 0), reverse=True)
    return results
