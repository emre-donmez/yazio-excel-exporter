from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side, numbers
from openpyxl.utils import get_column_letter


def export_to_excel(summary_rows: list[dict], detail_rows: list[dict], output_path: str):
    """Export data to Excel file with Summary and Details sheets."""
    wb = Workbook()

    _create_summary_sheet(wb, summary_rows)
    _create_detail_sheet(wb, detail_rows)

    wb.save(output_path)
    print(f"Excel file saved to: {output_path}")


def _create_summary_sheet(wb: Workbook, rows: list[dict]):
    ws = wb.active
    ws.title = "Summary"

    headers = ["Date", "Calories (kcal)", "Protein (g)", "Carbs (g)", "Fat (g)", "Calorie Goal", "Goal - Calories"]
    fields = ["date", "calories", "protein", "carbs", "fat", "calorie_goal", "goal_minus_calories"]

    # Style
    header_font = Font(bold=True, color="FFFFFF", size=11)
    header_fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
    header_alignment = Alignment(horizontal="center", vertical="center")
    thin_border = Border(
        left=Side(style="thin"),
        right=Side(style="thin"),
        top=Side(style="thin"),
        bottom=Side(style="thin")
    )

    # Headers
    for col, header in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col, value=header)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = header_alignment
        cell.border = thin_border

    # Data
    for row_idx, row_data in enumerate(rows, 2):
        for col_idx, field in enumerate(fields, 1):
            val = row_data.get(field, "")
            cell = ws.cell(row=row_idx, column=col_idx, value=val)
            cell.border = thin_border
            if col_idx == 1:
                cell.alignment = Alignment(horizontal="center")
            else:
                cell.number_format = '#,##0.0'
                cell.alignment = Alignment(horizontal="right")

    # Alternating row colors
    light_fill = PatternFill(start_color="D9E2F3", end_color="D9E2F3", fill_type="solid")
    for row_idx in range(2, len(rows) + 2):
        if row_idx % 2 == 0:
            for col_idx in range(1, len(headers) + 1):
                ws.cell(row=row_idx, column=col_idx).fill = light_fill

    # Auto-fit column widths
    for col_idx in range(1, len(headers) + 1):
        max_len = len(headers[col_idx - 1])
        for row_idx in range(2, len(rows) + 2):
            val = str(ws.cell(row=row_idx, column=col_idx).value or "")
            max_len = max(max_len, len(val))
        ws.column_dimensions[get_column_letter(col_idx)].width = max_len + 3

    # Freeze top row
    ws.freeze_panes = "A2"


def _create_detail_sheet(wb: Workbook, rows: list[dict]):
    ws = wb.create_sheet("Details")

    headers = ["Date", "Meal", "Food Name", "Producer", "Amount (g)", "Calories (kcal)", "Protein (g)", "Carbs (g)", "Fat (g)", "Fiber (g)", "AI Generated"]
    fields = ["date", "meal", "food_name", "producer", "amount", "calories", "protein", "carbs", "fat", "fiber", "ai_generated"]

    # Style
    header_font = Font(bold=True, color="FFFFFF", size=11)
    header_fill = PatternFill(start_color="548235", end_color="548235", fill_type="solid")
    header_alignment = Alignment(horizontal="center", vertical="center")
    thin_border = Border(
        left=Side(style="thin"),
        right=Side(style="thin"),
        top=Side(style="thin"),
        bottom=Side(style="thin")
    )

    # Headers
    for col, header in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col, value=header)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = header_alignment
        cell.border = thin_border

    # Data
    for row_idx, row_data in enumerate(rows, 2):
        for col_idx, field in enumerate(fields, 1):
            val = row_data.get(field, "")
            if field == "ai_generated":
                val = "Yes" if val else "No"
            cell = ws.cell(row=row_idx, column=col_idx, value=val)
            cell.border = thin_border
            if field in ("calories", "protein", "carbs", "fat", "fiber", "amount"):
                cell.number_format = '#,##0.0'
                cell.alignment = Alignment(horizontal="right")
            elif field == "ai_generated":
                cell.alignment = Alignment(horizontal="center")
                if val == "Yes":
                    cell.font = Font(color="FF0000")
            else:
                cell.alignment = Alignment(horizontal="left")

    # Alternating row colors
    light_fill = PatternFill(start_color="E2EFDA", end_color="E2EFDA", fill_type="solid")
    for row_idx in range(2, len(rows) + 2):
        if row_idx % 2 == 0:
            for col_idx in range(1, len(headers) + 1):
                ws.cell(row=row_idx, column=col_idx).fill = light_fill

    # Auto-fit column widths
    for col_idx in range(1, len(headers) + 1):
        max_len = len(headers[col_idx - 1])
        for row_idx in range(2, min(len(rows) + 2, 100)):  # Sample first 100 rows
            val = str(ws.cell(row=row_idx, column=col_idx).value or "")
            max_len = max(max_len, len(val))
        ws.column_dimensions[get_column_letter(col_idx)].width = min(max_len + 3, 50)

    # Freeze top row
    ws.freeze_panes = "A2"
