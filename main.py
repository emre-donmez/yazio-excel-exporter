import argparse
import os
import sys
from datetime import date, timedelta
from dotenv import load_dotenv

from yazio_api import login, YazioSession, discover_date_range, get_nutrients_daily, get_consumed_items, get_product
from data_processor import build_summary_rows, build_detail_rows
from excel_exporter import export_to_excel


def main():
    load_dotenv()

    parser = argparse.ArgumentParser(description="Export Yazio food diary to Excel")
    parser.add_argument("--email", default=os.getenv("YAZIO_EMAIL"), help="Yazio email (or set YAZIO_EMAIL env var)")
    parser.add_argument("--password", default=os.getenv("YAZIO_PASSWORD"), help="Yazio password (or set YAZIO_PASSWORD env var)")
    parser.add_argument("--from-date", type=date.fromisoformat, default=None, help="Start date (YYYY-MM-DD)")
    parser.add_argument("--to-date", type=date.fromisoformat, default=None, help="End date (YYYY-MM-DD)")
    parser.add_argument("--range", choices=["week", "month", "year", "all"], default=None,
                        help="Predefined date range: week, month, year, or all (auto-discover)")
    parser.add_argument("--output", default="yazio_export.xlsx", help="Output Excel file path")
    args = parser.parse_args()

    email = args.email
    password = args.password

    if not email:
        email = input("Yazio email: ").strip()
    if not password:
        import getpass
        password = getpass.getpass("Yazio password: ")

    if not email or not password:
        print("Error: Email and password are required.")
        sys.exit(1)

    # Step 1: Login
    print("Logging in to Yazio...")
    token = login(email, password)
    print("Login successful!")

    session = YazioSession(token)

    # Step 2: Determine date range
    all_nutrients = None
    today = date.today()
    range_choice = args.range

    if not args.from_date and not args.to_date and not range_choice:
        print("\nSelect date range:")
        print("  1) Last week")
        print("  2) Last month")
        print("  3) Last year")
        print("  4) All data (auto-discover)")
        choice = input("Choice [4]: ").strip()
        range_choice = {"1": "week", "2": "month", "3": "year"}.get(choice, "all")

    if args.from_date and args.to_date:
        start_date, end_date = args.from_date, args.to_date
        print(f"Using provided date range: {start_date} to {end_date}")
    elif range_choice and range_choice != "all":
        end_date = today
        if range_choice == "week":
            start_date = today - timedelta(days=7)
        elif range_choice == "month":
            start_date = today - timedelta(days=30)
        elif range_choice == "year":
            start_date = today - timedelta(days=365)
        print(f"Using range '{range_choice}': {start_date} to {end_date}")
    else:
        print("Auto-discovering date range...")
        start_date, end_date, all_nutrients = discover_date_range(session)
        print(f"Found data from {start_date} to {end_date}")

    # Step 3: Fetch daily nutrient summaries (skip if already fetched during discovery)
    if all_nutrients is None:
        print("Fetching daily nutrient summaries...")
        all_nutrients = get_nutrients_daily(session, start_date, end_date)
    print(f"Found {len(all_nutrients)} days with data")

    # Step 4: Fetch consumed items for each day
    print("Fetching consumed items for each day...")
    consumed_by_date = {}
    dates_with_data = sorted(set(item.get("date") for item in all_nutrients if item.get("date")))

    for i, day_str in enumerate(dates_with_data):
        day = date.fromisoformat(day_str)
        try:
            items = get_consumed_items(session, day)
        except Exception as e:
            print(f"\n  Warning: Failed to fetch items for {day_str}: {e}")
            continue
        if items:
            consumed_by_date[day_str] = items
        progress = (i + 1) / len(dates_with_data) * 100
        print(f"\r  Progress: {progress:.0f}% ({i + 1}/{len(dates_with_data)})", end="", flush=True)

    print(f"\n  Fetched consumed items for {len(consumed_by_date)} days")

    # Step 5: Fetch product details for all unique product IDs
    all_product_ids = set()
    for items in consumed_by_date.values():
        for item in items:
            pid = item.get("product_id")
            if pid:
                all_product_ids.add(pid)

    print(f"Fetching product details for {len(all_product_ids)} unique products...")
    products_cache: dict[str, dict] = {}
    for i, pid in enumerate(sorted(all_product_ids)):
        try:
            products_cache[pid] = get_product(session, pid)
        except Exception as e:
            print(f"\n  Warning: Failed to fetch product {pid}: {e}")
        progress = (i + 1) / len(all_product_ids) * 100
        print(f"\r  Progress: {progress:.0f}% ({i + 1}/{len(all_product_ids)})", end="", flush=True)
    print(f"\n  Fetched {len(products_cache)} product details")

    # Step 6: Build data
    print("Processing data...")
    summary_rows = build_summary_rows(all_nutrients)
    detail_rows = build_detail_rows(consumed_by_date, products_cache)

    # Step 7: Export to Excel
    print("Exporting to Excel...")
    export_to_excel(summary_rows, detail_rows, args.output)

    print(f"\nDone! {len(summary_rows)} days summarized, {len(detail_rows)} items detailed.")
    print(f"Output: {args.output}")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\nError: {e}")
    input("\nPress Enter to exit...")
