# Supply Chain Analytics – Prosacco Case Study

## Project overview

This repository explores end-to-end supply chain performance for Prosacco products using inventory, order, and production plan data. The included Jupyter notebooks walk through data preparation, descriptive analytics, supply–demand matching, and opportunities to improve sales coverage. The goal is to give analysts and planners a repeatable workspace for investigating bottlenecks, visualising trends, and drafting recommendations.

## Repository layout

- `Prosacco_Analysis.ipynb` – Comprehensive analysis notebook that loads the Excel workbook, cleans each sheet, and produces inventory, demand, logistics, and financial views plus supporting charts.
- `prosacco_supply_demand_analysis.ipynb` – Narrative-style report that blends orders, inventory, and manufacturing plans to highlight shortages, delays, and overproduction, concluding with recommendations.
- `sales_coverage_optimization.ipynb` – Work-in-progress notebook outlining a plan to optimise sales coverage by comparing inventory, orders, and weekly production to flag stock-out risks.
- `project1.ipynb` – Scratch notebook for experimentation and quick calculations on the Prosacco datasets.
- `data/` – Raw inputs used across the notebooks, including:
  - `Prosacco-Initial-Inventory.csv` – On-hand counts per SKU and warehouse.
  - `Prosacco-order-report.csv` – Customer demand by city, channel, and SKU (fields include `QTY ORD`, `Sales $`, and `Expected` dates).
  - `Prosacco-production-plan.xlsx` – Weekly production commitments per SKU.
  - `Prosacco-analysis-solution.xlsx` – Excel workbook with the three data sheets (`Data1`, `Data2`, `Data3`) used in `Prosacco_Analysis.ipynb`.
- `data/Prosacco-lane-costs.csv` – Transportation cost per unit and lane capacity assumptions for every market served. Used by the optimisation model.
- `create_datascience_env.sh` – Utility script that provisions a Python virtual environment preloaded with common analytics libraries.
- `analytics/` – Reusable Python modules. `kpi.py` computes fill rate, OTIF, and days-of-cover metrics and can export summaries to `outputs/`.
- `dashboard/streamlit_app.py` – Streamlit dashboard that visualises KPI results and lets you interactively filter SKUs.
- `tests/` – Automated data-quality checks powered by `pytest` to flag issues before running analyses.

## Getting started

1. **Clone the repository** (or download the ZIP) onto your machine.

2. **Create the Python environment**:

   ```bash
   ./create_datascience_env.sh
   ```

   This script builds a `datascience_env/` virtual environment and installs pandas, matplotlib, seaborn, scikit-learn, TensorFlow, PyTorch, and other frequently used packages.

3. **Activate the environment** before working in the notebooks:

   ```bash
   source datascience_env/bin/activate
   ```

4. (Optional) **Install additional packages** as you extend the analysis:

   ```bash
   pip install <package-name>
   ```

When you finish a session, deactivate the environment with `deactivate`.

## KPI automation & dashboard

Generate KPI artefacts from the command line:

```bash
python -m analytics.kpi
```

This command writes `outputs/kpi_summary.csv` and `outputs/kpi_overview.json`.

Launch the Streamlit dashboard for interactive exploration:

```bash
streamlit run dashboard/streamlit_app.py
```

Use the sidebar to point at an alternative data directory if you keep copies outside the repo.

The dashboard exposes scenario controls so you can model demand surges, production delays, overtime (production multipliers), and inventory buffers. Metrics, charts, and OTIF calculations update instantly based on these assumptions.

## Working with the notebooks

1. With the environment activated, launch Jupyter Lab or Notebook:

   ```bash
   jupyter lab
   ```

2. Open any of the `.ipynb` files to reproduce or extend the analyses. The notebooks assume the `data/` directory remains in the project root.

3. Run the cells top-to-bottom. Several notebooks read from the Excel workbook; if you relocate files, update the paths accordingly.

4. Use the existing visualisations and summary tables as starting points for deeper dives—e.g., scenario modelling, safety stock calculations, or channel-specific performance tracking.

### Linear programming scenario (sales coverage notebook)

- Open `sales_coverage_optimization.ipynb` and execute the newly added section on linear programming to compute an optimised allocation plan.
- The workbook aggregates inventory, demand, production, **and** transportation lane characteristics before solving a `PuLP` model that maximises fulfilled units while penalising expensive lanes and enforcing capacity limits.
- Outputs include SKU and city level fill rates, transport cost, lane utilisation, and remaining supply—compare these to descriptive analytics earlier in the notebook to quantify uplift.

### Running data-quality checks

Execute automated validations whenever the raw files change:

```bash
pytest
```

The tests verify non-negative inventory, order quantities, production weeks, and ensure KPI calculations stay within expected bounds.

### Nightly automation

A GitHub Actions workflow (`.github/workflows/nightly-refresh.yml`) runs every night at 03:00 UTC (and on-demand) to:

- Install Python dependencies.
- Execute automated data-quality tests (`pytest`).
- Recompute KPI exports (`python -m analytics.kpi`).
- Publish the refreshed KPI files (`outputs/kpi_summary.csv`, `outputs/kpi_overview.json`) as workflow artifacts.

## Data highlights

- **Inventory**: Provides SKU-level availability by warehouse, enabling coverage and safety stock checks.
- **Orders**: Captures city-, channel-, and customer-level demand with expected delivery dates to support prioritisation.
- **Production plan**: Weekly commitments per SKU that can be stacked against orders to surface shortages or idle capacity.

## Suggested next steps

- Extend the optimisation model with additional objectives (e.g., CO₂ impact, carrier-level SLAs) and compare trade-offs via sensitivity runs.
- Connect the dashboard to live data sources or a data warehouse table so stakeholders can refresh analyses without manual file drops.
- Add automated notifications (email/Slack) to the nightly workflow so data quality issues or KPI anomalies alert the team immediately.

## Contributing

Feel free to fork the project, open issues for bugs or enhancement ideas, and submit pull requests with improvements. Please document any new datasets or dependencies in this README.

