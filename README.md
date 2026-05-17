# ⚡ Catena — Design-Time Supply Chain Intelligence

Upload a BOM. Instantly see where you're exposed — before tape-out, not at procurement time.

---

## Run the demo (no API key needed)

```bash
# 1. Clone the repo
git clone https://github.com/SwethaSrinivasan07/Semis-at-GSB-Hackathon-Project.git
cd Semis-at-GSB-Hackathon-Project

# 2. Install dependencies  (Python 3.9+ required)
pip install -r requirements.txt

# 3. Launch
streamlit run frontend/manufacturer_app.py
```

Open **http://localhost:8501** in your browser, then click **"Try Sample BOM"**.

That's it — no API key, no `.env`, no setup. The demo runs entirely on hardcoded photonics data.

---

## What you'll see

- **9 parts** from a realistic Nokia/Infinera optical line card BOM
- **4 RED** (high risk) · **2 YELLOW** · **3 GREEN**
- Click **OP-27635** (top row) to drill into the worst part:
  - InP Photonic IC · $8,400 · 60-week lead · only 8 units in stock · single-source globally
  - Three ranked substitutes: EFFECT Photonics (drop-in), Lumentum (minor rework), Intel SiPh (redesign path)
- Download the **Annotated BOM (Excel)** or **Risk Report (TXT)**

---

## Run with live Claude AI (optional)

To use real Claude-powered BOM parsing and substitution reasoning:

```bash
cp .env.example .env
# paste your Anthropic API key into .env

streamlit run frontend/manufacturer_app.py
```

Upload any CSV BOM, then click **"⚡ Analyze with Claude"**.

---

## Project structure

```
├── frontend/
│   └── manufacturer_app.py      # Streamlit dashboard (Parul)
├── backend/
│   ├── bom_parser.py            # Photonics-aware BOM normalization (Jed)
│   ├── risk_engine.py           # 6-dimension risk scoring w/ 2025 market data (Jed)
│   ├── substitution.py          # Ranked substitute suggestions (Jed)
│   ├── avl_engine.py            # AVL qualification tracking (Jed)
│   ├── risk_narrative.py        # VP-level plain-English briefings (Jed)
│   ├── distributor_api.py       # Mock distributor data layer (Josh)
│   ├── report_generator.py      # Excel + PDF exports (Josh)
│   ├── demo_mode.py             # Pandas BOM parser, no API key needed (Swetha)
│   ├── main.py                  # FastAPI app for future React frontend (Josh)
│   └── api_integrations.py      # DigiKey / Mouser / Arrow stub clients (Josh)
├── data/
│   ├── photonics_bom.csv        # 15-part Nokia optical line card BOM
│   ├── mock_distributor_data.json
│   └── geo_risk_map.json
├── demo_script.md               # 3-minute judge demo script
└── requirements.txt
```

---

## Requirements

- Python 3.9 or higher
- No other dependencies beyond `requirements.txt`
- Anthropic API key only needed for live Claude analysis (demo works without it)
