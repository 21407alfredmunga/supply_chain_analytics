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
- `create_datascience_env.sh` – Utility script that provisions a Python virtual environment preloaded with common analytics libraries.
 
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

## Working with the notebooks

1. With the environment activated, launch Jupyter Lab or Notebook:

   ```bash
   jupyter lab
   ```

2. Open any of the `.ipynb` files to reproduce or extend the analyses. The notebooks assume the `data/` directory remains in the project root.

3. Run the cells top-to-bottom. Several notebooks read from the Excel workbook; if you relocate files, update the paths accordingly.

4. Use the existing visualisations and summary tables as starting points for deeper dives—e.g., scenario modelling, safety stock calculations, or channel-specific performance tracking.

## Data highlights

- **Inventory**: Provides SKU-level availability by warehouse, enabling coverage and safety stock checks.
- **Orders**: Captures city-, channel-, and customer-level demand with expected delivery dates to support prioritisation.
- **Production plan**: Weekly commitments per SKU that can be stacked against orders to surface shortages or idle capacity.

## Suggested next steps

- Automate KPI calculation (fill rate, on-time in full, days of cover) and surface them via dashboards or Streamlit.
- Extend the optimisation notebook with linear programming or heuristic approaches to rebalance supply across markets.
- Add unit tests or validation scripts to monitor data quality before running the analyses.

## Contributing

Feel free to fork the project, open issues for bugs or enhancement ideas, and submit pull requests with improvements. Please document any new datasets or dependencies in this README.

