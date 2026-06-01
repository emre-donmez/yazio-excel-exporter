import requests
from datetime import date, timedelta
import calendar
from typing import Callable, Optional

BASE_URL = "https://yzapi.yazio.com"
CLIENT_ID = "1_4hiybetvfksgw40o0sog4s884kwc840wwso8go4k8c04goo4c"
CLIENT_SECRET = "6rok2m65xuskgkgogw40wkkk8sw0osg84s8cggsc4woos4s8o"
DEFAULT_TIMEOUT = 30


class YazioSession:
    """Wraps requests.Session for connection reuse, default timeout, and auth headers."""

    def __init__(self, token: str):
        self._session = requests.Session()
        self._session.headers.update({"Authorization": f"Bearer {token}"})

    def get(self, url: str, **kwargs) -> requests.Response:
        kwargs.setdefault("timeout", DEFAULT_TIMEOUT)
        return self._session.get(url, **kwargs)

    def close(self):
        self._session.close()


def login(email: str, password: str) -> str:
    """Login to Yazio and return access token."""
    resp = requests.post(f"{BASE_URL}/v9/oauth/token", json={
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "username": email,
        "password": password,
        "grant_type": "password"
    }, timeout=DEFAULT_TIMEOUT)
    resp.raise_for_status()
    return resp.json()["access_token"]


def get_nutrients_daily(session: YazioSession, start: date, end: date) -> list[dict]:
    """Get daily nutrient summaries for a date range."""
    resp = session.get(
        f"{BASE_URL}/v9/user/consumed-items/nutrients-daily",
        params={"start": start.isoformat(), "end": end.isoformat()},
    )
    resp.raise_for_status()
    data = resp.json()
    if isinstance(data, list):
        return data
    return []


def get_consumed_items(session: YazioSession, day: date) -> list[dict]:
    """Get consumed items for a specific day. Returns combined list of products, recipes, and simple products."""
    resp = session.get(
        f"{BASE_URL}/v9/user/consumed-items",
        params={"date": day.isoformat()},
    )
    resp.raise_for_status()
    data = resp.json()
    if isinstance(data, dict):
        items = []
        items.extend(data.get("products", []))
        items.extend(data.get("recipe_portions", []))
        items.extend(data.get("simple_products", []))
        return items
    if isinstance(data, list):
        return data
    return []


def get_product(session: YazioSession, product_id: str) -> dict:
    """Get product detail by ID."""
    resp = session.get(
        f"{BASE_URL}/v9/products/{product_id}",
    )
    resp.raise_for_status()
    return resp.json()


def get_weight_for_date(session: YazioSession, day: date) -> Optional[float]:
    """Get the latest recorded body weight for a specific date."""
    resp = session.get(
        f"{BASE_URL}/v15/user/bodyvalues/weight/last",
        params={"date": day.isoformat()},
    )

    if resp.status_code in (204, 404):
        return None

    resp.raise_for_status()
    data = resp.json()

    if not isinstance(data, dict) or "value" not in data:
        return None

    value = data.get("value")
    if value is None:
        return None

    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def get_weight_by_date(
    session: YazioSession,
    start: date,
    end: date,
    progress_callback: Optional[Callable[[int, int], None]] = None,
) -> dict[str, float]:
    """Get body weight values for each day in the date range."""
    weights = {}
    current = start
    total_days = (end - start).days + 1
    completed_days = 0

    while current <= end:
        weight = get_weight_for_date(session, current)
        if weight is not None:
            weights[current.isoformat()] = weight
        current += timedelta(days=1)
        completed_days += 1

        if progress_callback:
            progress_callback(completed_days, total_days)

    return weights


def discover_date_range(session: YazioSession) -> tuple[date, date, list[dict]]:
    """
    Auto-discover the date range with data by scanning months
    forward and backward from today. Stops after 3 consecutive empty months.
    Returns (earliest_date, latest_date, all_nutrients_data).
    """
    today = date.today()

    def get_month_range(year: int, month: int) -> tuple[date, date]:
        first = date(year, month, 1)
        last_day = calendar.monthrange(year, month)[1]
        last = date(year, month, last_day)
        return first, last

    def has_data_for_month(year: int, month: int) -> list[dict]:
        first, last = get_month_range(year, month)
        return get_nutrients_daily(session, first, last)

    all_dates = []
    all_nutrients = []

    # Scan backward from current month
    current = today.replace(day=1)
    empty_count = 0
    while empty_count < 3:
        data = has_data_for_month(current.year, current.month)
        if data:
            empty_count = 0
            all_nutrients.extend(data)
            for item in data:
                if "date" in item:
                    all_dates.append(date.fromisoformat(item["date"]))
        else:
            empty_count += 1
        # Go to previous month
        if current.month == 1:
            current = current.replace(year=current.year - 1, month=12)
        else:
            current = current.replace(month=current.month - 1)

    # Scan forward from next month
    next_month = today.replace(day=1)
    if next_month.month == 12:
        next_month = next_month.replace(year=next_month.year + 1, month=1)
    else:
        next_month = next_month.replace(month=next_month.month + 1)

    empty_count = 0
    while empty_count < 3:
        data = has_data_for_month(next_month.year, next_month.month)
        if data:
            empty_count = 0
            all_nutrients.extend(data)
            for item in data:
                if "date" in item:
                    all_dates.append(date.fromisoformat(item["date"]))
        else:
            empty_count += 1
        # Go to next month
        if next_month.month == 12:
            next_month = next_month.replace(year=next_month.year + 1, month=1)
        else:
            next_month = next_month.replace(month=next_month.month + 1)

    if not all_dates:
        raise ValueError("No data found in Yazio account")

    return min(all_dates), max(all_dates), all_nutrients
