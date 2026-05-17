# ⚡ ChainSight — Semiconductor Supply Chain Risk Intelligence

Upload a BOM. Instantly see where you're exposed.

## What it does

- Parses any CSV or Excel BOM using Claude AI
- Scores every component across 5 risk dimensions: **Availability, Lead Time, Cost, Lifecycle, Geopolitical**
- Flags each part RED / YELLOW / GREEN
- Shows: description, unit price, stock, provider, lead time, lifecycle status, datasheet link
- Suggests ranked substitutes with compatibility grade (Drop-in / Minor rework / Redesign required)
- Exports annotated Excel BOM + PDF risk report

## Setup

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Add your Anthropic API key
cp .env.example .env
# Edit .env and paste your key

# 3. Run
streamlit run frontend/manufacturer_app.py
```

## Project structure

```
├── backend/
│   ├── bom_parser.py        # Claude parses & normalizes BOM uploads
│   ├── distributor_api.py   # Part data lookup (mock → real API swap-in)
│   ├── risk_engine.py       # 5-dimension risk scoring
│   ├── substitution.py      # Claude-powered substitute suggestions
│   └── report_generator.py  # Annotated Excel BOM + PDF report
├── frontend/
│   └── manufacturer_app.py  # Streamlit dashboard
├── data/
│   ├── sample_bom.csv           # Demo BOM (10 parts)
│   ├── mock_distributor_data.json
│   └── geo_risk_map.json
└── requirements.txt
```

## Demo

Upload `data/sample_bom.csv` to see a live demo with pre-loaded supply chain data.
