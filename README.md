# Architectural Fee Calculator

A Streamlit prototype for estimating architectural fees, phase allocations, and project schedules. Built for architectural professionals exploring fee structures aligned with AIA B101 basic services phases.

## Features

- **Fee estimation** via percentage of construction cost, staffing build-up, per-drawing set, or stipulated sum
- **Phase breakdown** across Schematic Design, Design Development, Construction Documents, Bidding, and Construction Administration
- **Schedule timeline** with milestone dates and CSV export
- **Market benchmarking** against indicative U.S. rate ranges by project type
- **Claude AI integration** (optional) for project intake, fee advisory, and proposal narrative generation

## Quick Start

```bash
# Clone and enter the repo
cd aia-class-12-fee-calculator-demo

# Create a virtual environment (recommended)
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Optional: enable Claude AI features
cp .env.example .env
# Edit .env and set ANTHROPIC_API_KEY=sk-ant-...

# Run the app
streamlit run app.py
```

The app opens at [http://localhost:8501](http://localhost:8501).

## Claude API Setup

1. Create an API key at [console.anthropic.com](https://console.anthropic.com/).
2. Add it to a `.env` file in the project root:

   ```
   ANTHROPIC_API_KEY=sk-ant-your-key-here
   ```

3. For Streamlit Community Cloud deployment, add the same key under **Settings → Secrets**:

   ```toml
   ANTHROPIC_API_KEY = "sk-ant-your-key-here"
   ```

Claude is used only when you click an AI button — fee calculations remain deterministic.

## Usage

1. **Sidebar** — Set project type, region, construction budget, fee method, and timeline.
2. **Staff & Rates** — Edit hourly rates and hours per phase for the staffing cross-check.
3. **Milestones** — Adjust AIA phase fee and duration percentages.
4. **Drawing Set** — Enter sheet counts by discipline for the per-drawing estimate.
5. **Results** — Review total fee, phase breakdown, schedule, and market comparison.

Optional: describe your project in the sidebar and click **Analyze project with Claude** to pre-fill inputs.

## Project Structure

```
app.py                  # Streamlit entry point
config/market_rates.yaml  # Editable market benchmarks
models/                 # Pydantic data models
calculators/            # Deterministic fee & schedule engine
services/               # Claude API client and prompts
ui/                     # Streamlit UI components
```

## Disclaimer

All figures are **indicative estimates** for educational and planning purposes. Market rates vary by jurisdiction, project complexity, and firm positioning. This tool does not constitute legal, contractual, or professional advice.

## License

See [LICENSE](LICENSE).
