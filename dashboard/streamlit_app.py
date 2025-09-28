"""Streamlit dashboard for Prosacco supply chain KPIs."""
from __future__ import annotations

from pathlib import Path
from typing import Optional

import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import numpy as np
import pandas as pd
import streamlit as st

from analytics.kpi import (
    DATA_DIR,
    compute_kpis,
    load_inventory,
    load_orders,
    load_production_plan,
)


def _resolve_data_dir(data_dir: Optional[str]) -> Path:
    return Path(data_dir) if data_dir else DATA_DIR


@st.cache_data(show_spinner=False)
def load_data(data_dir: Optional[str] = None):
    base_path = _resolve_data_dir(data_dir)
    inventory = load_inventory(base_path / "Prosacco-Initial-Inventory.csv")
    orders = load_orders(base_path / "Prosacco-order-report.csv")
    production = load_production_plan(base_path / "Prosacco-production-plan.xlsx")
    return inventory, orders, production


def format_percentage(value: float) -> str:
    if value is None or np.isnan(value):
        return "N/A"
    return f"{value * 100:.1f}%"


st.set_page_config(page_title="Prosacco Supply Chain KPIs", layout="wide")
st.title("Prosacco Supply Chain KPI Dashboard")
st.caption(
    "Automated calculations for fill rate, on-time in full (OTIF), and inventory days of cover."
)

with st.sidebar:
    st.header("Configuration")
    custom_dir = st.text_input("Data directory", value=str(DATA_DIR))
    refresh = st.button("Recompute KPIs", type="primary")

    st.header("Scenario controls")
    demand_surge_pct = st.slider(
        "Demand surge (%)", min_value=-50, max_value=150, value=0, step=5,
        help="Scale customer orders to stress-test fulfilment (negative values model demand drops).",
    )
    production_delay_weeks = st.slider(
        "Production delay (weeks)", min_value=0, max_value=8, value=0,
        help="Shift the production plan forward to simulate delays in manufacturing or inbound supply.",
    )
    production_multiplier = st.slider(
        "Production multiplier",
        min_value=0.2,
        max_value=1.8,
        value=1.0,
        step=0.1,
        help="Scale weekly production volumes to reflect overtime, additional shifts, or capacity reductions.",
    )
    inventory_buffer_pct = st.slider(
        "Inventory buffer (%)",
        min_value=-50,
        max_value=100,
        value=0,
        step=5,
        help="Apply a buffer (or depletion) factor to current on-hand inventory.",
    )

if refresh:
    load_data.clear()

inventory_df, orders_df, production_df = load_data(custom_dir)

demand_multiplier = 1 + demand_surge_pct / 100
inventory_multiplier = 1 + inventory_buffer_pct / 100

scenario_orders = orders_df.copy()
scenario_orders["qty_ord"] = (scenario_orders["qty_ord"] * demand_multiplier).clip(lower=0)

scenario_inventory = inventory_df.copy()
scenario_inventory["available"] = (scenario_inventory["available"] * inventory_multiplier).clip(lower=0)

scenario_production = production_df.copy()
scenario_production["produced"] = scenario_production["produced"] * production_multiplier
if production_delay_weeks:
    scenario_production["week"] = scenario_production["week"] + int(production_delay_weeks)

kpi_df, totals = compute_kpis(scenario_inventory, scenario_orders, scenario_production)

st.info(
    f"Scenario: demand x{demand_multiplier:.2f}, production x{production_multiplier:.2f}, "
    f"production delay {production_delay_weeks} weeks, inventory x{inventory_multiplier:.2f}.",
    icon="⚙️",
)

st.subheader("Overall performance")
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Fill rate", format_percentage(totals.get("Fill Rate")))
with col2:
    st.metric("OTIF", format_percentage(totals.get("OTIF")))
with col3:
    doc_value = totals.get("Days of Cover")
    st.metric("Days of cover", f"{doc_value:.1f}" if doc_value and not np.isnan(doc_value) else "N/A")

st.divider()

st.subheader("KPI breakdown by SKU")
selected_skus = st.multiselect(
    "Filter SKUs",
    options=list(kpi_df.index),
    default=list(kpi_df.index),
)

filtered_df = kpi_df.loc[selected_skus] if selected_skus else kpi_df
st.dataframe(
    filtered_df.assign(
        **{
            "Fill Rate": filtered_df["Fill Rate"].apply(format_percentage),
            "OTIF": filtered_df["OTIF"].apply(format_percentage),
        }
    ),
    use_container_width=True,
)

st.subheader("Visual summary")
chart_df = filtered_df[["Fill Rate", "OTIF"]]
st.bar_chart(chart_df, height=320)

st.subheader("Inventory coverage")
coverage_df = filtered_df[["Days of Cover"]]
st.line_chart(coverage_df, height=320)

st.divider()

st.markdown(
    """
    ### Notes
    - Fill rate reflects the portion of cumulative demand that can be served with available inventory and planned production.
    - OTIF assumes production is available within the same week it is planned and compares cumulative supply against demand deadlines.
    - Days of cover estimates how long supply will last based on the historical demand window in the order data.
    """
)
