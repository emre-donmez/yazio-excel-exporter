# Yazio Excel Exporter

Export your [Yazio](https://www.yazio.com/) food diary to an Excel file. Automatically discovers all your logged data and generates a formatted `.xlsx` with daily summaries and per-item details.

## Features

- **Auto-discovery** — scans your account to find all days with data (no need to specify dates)
- **Summary sheet** — daily totals: calories, protein, carbs, fat, calorie goal, and goal difference
- **Details sheet** — every logged food item with meal type, nutritional breakdown, and AI-generated flag
- **AI-generated items** — correctly extracts names and nutrients for Yazio's AI-logged simple products
- **Formatted output** — styled headers, alternating row colors, auto-fitted columns, frozen header rows

## Output

The generated Excel file contains two sheets:

| Sheet | Columns |
|-------|---------|
| **Summary** | Date, Calories, Protein, Carbs, Fat, Calorie Goal, Goal - Calories |
| **Details** | Date, Meal, Food Name, Producer, Amount, Calories, Protein, Carbs, Fat, Fiber, AI Generated |

## Installation

```bash
git clone https://github.com/<your-username>/yazio-excel-exporter.git
cd yazio-excel-exporter
pip install -r requirements.txt
```

## Usage

### Standalone Exe (No Python Required)

Download `yazio-exporter.exe` from [Releases](https://github.com/emre-donmez/yazio-excel-exporter/releases) and double-click to run. The app will prompt for:

1. Your Yazio email
2. Your Yazio password
3. Date range selection (week / month / year / all)

The Excel file will be saved in the same folder as the exe.

### With command-line arguments

```bash
python main.py --email your@email.com --password yourpassword
```

### With a predefined date range

```bash
python main.py --range week      # Last 7 days
python main.py --range month     # Last 30 days
python main.py --range year      # Last 365 days
python main.py --range all       # Auto-discover all data (default)
```

### With environment variables

```bash
cp .env.example .env
# Edit .env with your Yazio credentials
python main.py
```

### Options

| Flag | Description | Default |
|------|-------------|---------|
| `--email` | Yazio account email | `YAZIO_EMAIL` env var |
| `--password` | Yazio account password | `YAZIO_PASSWORD` env var |
| `--range` | Predefined range: `week`, `month`, `year`, `all` | Auto-discover |
| `--from-date` | Custom start date (YYYY-MM-DD) | — |
| `--to-date` | Custom end date (YYYY-MM-DD) | — |
| `--output` | Output file path | `yazio_export.xlsx` |

## Project Structure

```
├── main.py              # CLI entry point — orchestrates login, fetch, export
├── yazio_api.py         # Yazio API client — auth, endpoints, date range discovery
├── data_processor.py    # Transforms API responses into summary/detail rows
├── excel_exporter.py    # Generates formatted Excel workbook
├── requirements.txt
├── .env.example
└── .gitignore
```

## License

MIT
