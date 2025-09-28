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

if refresh:
    load_data.clear()

inventory_df, orders_df, production_df = load_data(custom_dir)

kpi_df, totals = compute_kpis(inventory_df, orders_df, production_df)

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
st.bar_chart(chart_df, use_container_width=True)

st.subheader("Inventory coverage")
coverage_df = filtered_df[["Days of Cover"]]
st.line_chart(coverage_df, use_container_width=True)

st.divider()

st.markdown(
    """
    ### Notes
    - Fill rate reflects the portion of cumulative demand that can be served with available inventory and planned production.
    - OTIF assumes production is available within the same week it is planned and compares cumulative supply against demand deadlines.
    - Days of cover estimates how long supply will last based on the historical demand window in the order data.
    """
)
