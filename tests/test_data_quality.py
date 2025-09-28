"""Data quality and integrity checks for Prosacco datasets."""
from pathlib import Path

import numpy as np
import pandas as pd

from analytics import kpi

DATA_DIR = Path(__file__).resolve().parents[1] / "data"


def test_inventory_availability_non_negative():
    inventory = kpi.load_inventory(DATA_DIR / "Prosacco-Initial-Inventory.csv")
    assert inventory["available"].ge(0).all(), "Inventory availability contains negative values"
    assert inventory["sku"].notna().all(), "Inventory has missing SKU codes"


def test_orders_have_positive_quantities():
    orders = kpi.load_orders(DATA_DIR / "Prosacco-order-report.csv")
    assert orders["qty_ord"].ge(0).all(), "Order quantities should be non-negative"
    assert orders["sku"].notna().all(), "Orders contain missing SKU codes"


def test_expected_dates_parsed():
    orders = kpi.load_orders(DATA_DIR / "Prosacco-order-report.csv")
    parsed_ratio = orders["expected_date"].notna().mean()
    assert parsed_ratio > 0.75, "At least 75% of expected dates should parse into valid datetimes"


def test_production_plan_week_values():
    production = kpi.load_production_plan(DATA_DIR / "Prosacco-production-plan.xlsx")
    assert production["week"].ge(0).all(), "Production plan weeks should be non-negative"
    assert production["produced"].ge(0).all(), "Production plan includes negative output"


def test_kpi_results_bounds():
    inventory = kpi.load_inventory(DATA_DIR / "Prosacco-Initial-Inventory.csv")
    orders = kpi.load_orders(DATA_DIR / "Prosacco-order-report.csv")
    production = kpi.load_production_plan(DATA_DIR / "Prosacco-production-plan.xlsx")

    kpi_df, totals = kpi.compute_kpis(inventory, orders, production)

    fill_rate_valid = kpi_df["Fill Rate"].dropna().between(0, 1).all()
    otif_valid = kpi_df["OTIF"].dropna().between(0, 1).all()

    assert fill_rate_valid, "Fill rates should lie between 0 and 1"
    assert otif_valid, "OTIF should lie between 0 and 1"

    if not np.isnan(totals.get("Fill Rate", np.nan)):
        assert 0 <= totals["Fill Rate"] <= 1, "Overall fill rate should be between 0 and 1"
    if not np.isnan(totals.get("OTIF", np.nan)):
        assert 0 <= totals["OTIF"] <= 1, "Overall OTIF should be between 0 and 1"
