def build_summary_rows(nutrients_data: list[dict]) -> list[dict]:
    """
    Build summary rows from nutrients-daily API response.
    Fields are flat: energy, carb, protein, fat, energy_goal.
    """
    rows = []
    for item in nutrients_data:
        calories = _safe_float(item.get("energy"))
        calorie_goal = _safe_float(item.get("energy_goal"))
        row = {
            "date": item.get("date", ""),
            "calories": calories,
            "protein": _safe_float(item.get("protein")),
            "carbs": _safe_float(item.get("carb")),
            "fat": _safe_float(item.get("fat")),
            "calorie_goal": calorie_goal,
            "goal_minus_calories": calorie_goal - calories,
        }
        rows.append(row)

    rows.sort(key=lambda r: r["date"])
    return rows


def build_detail_rows(consumed_by_date: dict[str, list[dict]], products_cache: dict[str, dict]) -> list[dict]:
    """
    Build detail rows from consumed items.
    Regular products: look up product_id in products_cache, multiply per-gram values * amount.
    Simple products: use name/nutrients directly from the item (nutrients are totals).
    """
    rows = []

    for day_str in sorted(consumed_by_date.keys()):
        items = consumed_by_date[day_str]
        for item in items:
            item_type = item.get("type", "")

            if item_type == "simple_product":
                # Simple products carry name and total nutrients directly
                item_nutrients = item.get("nutrients", {})
                row = {
                    "date": day_str,
                    "meal": item.get("daytime", "other").capitalize(),
                    "food_name": item.get("name", "Unknown"),
                    "producer": "",
                    "amount": "",
                    "unit": "",
                    "calories": _get_nutrient_value(item_nutrients, "energy.energy"),
                    "protein": _get_nutrient_value(item_nutrients, "nutrient.protein"),
                    "carbs": _get_nutrient_value(item_nutrients, "nutrient.carb"),
                    "fat": _get_nutrient_value(item_nutrients, "nutrient.fat"),
                    "fiber": _get_nutrient_value(item_nutrients, "nutrient.dietaryfiber"),
                    "ai_generated": _is_ai_generated(item, {}),
                }
            else:
                product_id = item.get("product_id", "")
                product = products_cache.get(product_id, {})
                product_nutrients = product.get("nutrients", {})
                amount = _safe_float(item.get("amount"))

                row = {
                    "date": day_str,
                    "meal": item.get("daytime", "other").capitalize(),
                    "food_name": product.get("name", "Unknown"),
                    "producer": product.get("producer", ""),
                    "amount": amount,
                    "unit": "g",
                    "calories": amount * _get_nutrient_value(product_nutrients, "energy.energy"),
                    "protein": amount * _get_nutrient_value(product_nutrients, "nutrient.protein"),
                    "carbs": amount * _get_nutrient_value(product_nutrients, "nutrient.carb"),
                    "fat": amount * _get_nutrient_value(product_nutrients, "nutrient.fat"),
                    "fiber": amount * _get_nutrient_value(product_nutrients, "nutrient.dietaryfiber"),
                    "ai_generated": _is_ai_generated(item, product),
                }
            rows.append(row)

    return rows


def _get_nutrient_value(nutrients: dict, key: str) -> float:
    """Extract per-gram nutrient value from product nutrients dict."""
    val = nutrients.get(key)
    if val is None:
        return 0.0
    if isinstance(val, dict):
        return _safe_float(val.get("value", 0))
    return _safe_float(val)


def _safe_float(val) -> float:
    if val is None:
        return 0.0
    try:
        return float(val)
    except (ValueError, TypeError):
        return 0.0


def _is_ai_generated(item: dict, product: dict) -> bool:
    """Check if a consumed item or its product was AI-generated."""
    for obj in (item, product):
        if obj.get("ai_generated", False):
            return True
        if obj.get("is_ai_generated", False):
            return True
        if obj.get("source") == "ai":
            return True
    return False


def calculate_daily_fiber(detail_rows: list[dict]) -> dict[str, float]:
    """Calculate total fiber per day from detail rows."""
    fiber_by_date = {}
    for row in detail_rows:
        date = row.get("date")
        fiber = _safe_float(row.get("fiber", 0.0))
        if date:
            fiber_by_date[date] = fiber_by_date.get(date, 0.0) + fiber
    return fiber_by_date


def build_weight_change_rows(weight_by_date: dict[str, float]) -> list[dict]:
    """Build rows for weight changes, keeping only changed weight values."""
    rows = []
    first_weight = None
    previous_weight = None

    for day_str, raw_weight in sorted(weight_by_date.items()):
        weight = round(_safe_float(raw_weight), 1)

        if previous_weight is not None and weight == previous_weight:
            continue

        if first_weight is None:
            first_weight = weight
            change = 0.0
            total_change = 0.0
        else:
            change = round(weight - previous_weight, 1)
            total_change = round(weight - first_weight, 1)

        rows.append({
            "date": day_str,
            "weight": weight,
            "change": change,
            "total_change": total_change,
        })

        previous_weight = weight

    return rows
