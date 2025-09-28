"""KPI computation utilities for the Prosacco supply chain analytics project."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, Optional, Tuple

import numpy as np
import pandas as pd

DATA_DIR = Path(__file__).resolve().parents[1] / "data"
EXCEL_EPOCH = "1899-12-30"


@dataclass
class KpiResult:
    sku: str
    total_demand: float
    total_supply: float
    fill_rate: float
    otif: float
    days_of_cover: float


def _ensure_path(path: Optional[Path], default: Path) -> Path:
    if path is None:
        return default
    return Path(path)


def load_inventory(path: Optional[Path] = None) -> pd.DataFrame:
    """Load the Prosacco inventory snapshot."""
    path = _ensure_path(path, DATA_DIR / "Prosacco-Initial-Inventory.csv")
    df = pd.read_csv(path)
    df.columns = [col.strip().lower().replace(" ", "_") for col in df.columns]
    df["available"] = pd.to_numeric(df["available"], errors="coerce").fillna(0)
    return df


def load_orders(path: Optional[Path] = None) -> pd.DataFrame:
    """Load the Prosacco order report and normalise key fields."""
    path = _ensure_path(path, DATA_DIR / "Prosacco-order-report.csv")
    df = pd.read_csv(path)
    df.columns = [col.strip().lower().replace(" ", "_") for col in df.columns]
    qty_col = "qty_ord"
    value_col = "sales_$" if "sales_$" in df.columns else "sales$"
    expected_col = "expected"

    df[qty_col] = pd.to_numeric(df[qty_col], errors="coerce").fillna(0)
    if value_col in df.columns:
        df[value_col] = pd.to_numeric(df[value_col], errors="coerce")

    if expected_col in df.columns:
        if pd.api.types.is_numeric_dtype(df[expected_col]):
            df["expected_date"] = pd.to_datetime(df[expected_col], origin=EXCEL_EPOCH, unit="D", errors="coerce")
        else:
            df["expected_date"] = pd.to_datetime(df[expected_col], errors="coerce")
    else:
        df["expected_date"] = pd.NaT
    df["expected_week"] = df["expected_date"].dt.isocalendar().week
    df["expected_year"] = df["expected_date"].dt.isocalendar().year
    df["sku"] = df["sku"].astype(str)
    return df


def load_production_plan(path: Optional[Path] = None) -> pd.DataFrame:
    """Load the Prosacco production plan and return a long-form dataframe."""
    path = _ensure_path(path, DATA_DIR / "Prosacco-production-plan.xlsx")
    matrix = pd.read_excel(path, header=1)
    matrix = matrix[matrix["SKU"].notna()].copy()
    matrix["SKU"] = matrix["SKU"].astype(str)

    value_cols = [col for col in matrix.columns if col != "SKU"]
    long_df = matrix.melt(id_vars=["SKU"], value_vars=value_cols, var_name="week_label", value_name="produced")
    long_df["produced"] = pd.to_numeric(long_df["produced"], errors="coerce").fillna(0)
    long_df["week"] = (
        long_df["week_label"].astype(str).str.extract(r"(\d+)", expand=False).fillna("0").astype(int)
    )
    long_df.drop(columns=["week_label"], inplace=True)
    long_df.rename(columns={"SKU": "sku"}, inplace=True)
    return long_df


def _demand_window_days(orders: pd.DataFrame) -> Dict[str, float]:
    by_sku = {}
    grouped = orders.dropna(subset=["expected_date"]).groupby("sku")
    for sku, group in grouped:
        if group.empty:
            continue
        span = (group["expected_date"].max() - group["expected_date"].min()).days + 1
        by_sku[sku] = max(span, 1)
    return by_sku


def _supply_by_week(production_long: pd.DataFrame) -> pd.Series:
    if production_long.empty:
        return pd.Series(dtype=float)
    return production_long.groupby(["sku", "week"])["produced"].sum()


def _inventory_by_sku(inventory: pd.DataFrame) -> pd.Series:
    return inventory.groupby("sku")["available"].sum()


def _demand_by_sku(orders: pd.DataFrame) -> pd.Series:
    return orders.groupby("sku")["qty_ord"].sum()


def _production_by_sku(production_long: pd.DataFrame) -> pd.Series:
    if production_long.empty:
        return pd.Series(dtype=float)
    return production_long.groupby("sku")["produced"].sum()


def _otif_ratio_for_sku(
    sku: str,
    demand_weekly: pd.Series,
    supply_weekly: pd.Series,
    starting_inventory: float,
) -> float:
    total_demand = demand_weekly.sum()
    if total_demand <= 0:
        return 1.0

    weeks = sorted(set(demand_weekly.index).union(supply_weekly.index))
    cumulative_supply = starting_inventory
    cumulative_demand = 0.0
    on_time_units = 0.0

    for week in weeks:
        cumulative_demand += demand_weekly.get(week, 0)
        cumulative_supply += supply_weekly.get(week, 0)
        on_time_units = min(on_time_units + demand_weekly.get(week, 0), cumulative_supply)

    return float(on_time_units / total_demand)


def compute_kpis(
    inventory: pd.DataFrame,
    orders: pd.DataFrame,
    production_long: pd.DataFrame,
) -> Tuple[pd.DataFrame, Dict[str, float]]:
    """Compute fill rate, OTIF, and days of cover for each SKU and overall."""
    inventory_by_sku = _inventory_by_sku(inventory)
    demand_by_sku = _demand_by_sku(orders)
    production_by_sku = _production_by_sku(production_long)
    supply_weekly = _supply_by_week(production_long)

    demand_window_days = _demand_window_days(orders)

    results: Iterable[KpiResult] = []
    kpi_rows = []

    all_skus = sorted(set(demand_by_sku.index) | set(inventory_by_sku.index) | set(production_by_sku.index))
    weekly_demand = orders.groupby(["sku", "expected_week"])["qty_ord"].sum().rename("demand")
    weekly_supply = supply_weekly.rename("supply")

    for sku in all_skus:
        demand_total = float(demand_by_sku.get(sku, 0.0))
        inventory_total = float(inventory_by_sku.get(sku, 0.0))
        production_total = float(production_by_sku.get(sku, 0.0))
        supply_total = inventory_total + production_total
        fill_rate = np.nan if demand_total <= 0 else min(supply_total, demand_total) / demand_total

        try:
            demand_weeks = weekly_demand.xs(sku, level=0)
        except KeyError:
            demand_weeks = pd.Series(dtype=float)

        try:
            supply_weeks = weekly_supply.xs(sku, level=0)
        except KeyError:
            supply_weeks = pd.Series(dtype=float)

        otif = _otif_ratio_for_sku(sku, demand_weeks, supply_weeks, inventory_total)

        window_days = demand_window_days.get(sku)
        avg_daily_demand = demand_total / window_days if window_days else 0.0
        if avg_daily_demand <= 0:
            days_cover = float("inf") if supply_total > 0 else np.nan
        else:
            days_cover = supply_total / avg_daily_demand

        kpi_rows.append(
            {
                "SKU": sku,
                "Total Demand": demand_total,
                "Total Supply": supply_total,
                "Fill Rate": round(fill_rate, 4) if not np.isnan(fill_rate) else np.nan,
                "OTIF": round(otif, 4),
                "Days of Cover": round(days_cover, 2) if np.isfinite(days_cover) else days_cover,
            }
        )

    kpi_df = pd.DataFrame(kpi_rows).set_index("SKU").sort_index()

    overall_demand = kpi_df["Total Demand"].sum()
    overall_supply = kpi_df["Total Supply"].sum()
    overall_fill_rate = float(min(overall_supply, overall_demand) / overall_demand) if overall_demand > 0 else np.nan
    weighted_otif = float(
        (kpi_df["OTIF"] * kpi_df["Total Demand"]).sum() / overall_demand
    ) if overall_demand > 0 else np.nan
    weighted_days_cover = float(
        (kpi_df["Days of Cover"].replace({np.inf: np.nan}) * kpi_df["Total Demand"]).sum() / overall_demand
    ) if overall_demand > 0 else np.nan

    totals = {
        "Total Demand": overall_demand,
        "Total Supply": overall_supply,
        "Fill Rate": overall_fill_rate,
        "OTIF": weighted_otif,
        "Days of Cover": weighted_days_cover,
    }

    return kpi_df, totals


def calculate_and_save_kpis(
    data_dir: Optional[Path] = None,
    output_dir: Optional[Path] = None,
) -> Tuple[pd.DataFrame, Dict[str, float]]:
    """Convenience function to compute KPIs and persist the results to disk."""
    data_dir = _ensure_path(data_dir, DATA_DIR)
    output_dir = _ensure_path(output_dir, Path("outputs"))
    output_dir.mkdir(parents=True, exist_ok=True)

    inventory = load_inventory(data_dir / "Prosacco-Initial-Inventory.csv")
    orders = load_orders(data_dir / "Prosacco-order-report.csv")
    production = load_production_plan(data_dir / "Prosacco-production-plan.xlsx")

    kpi_df, totals = compute_kpis(inventory, orders, production)
    kpi_path = output_dir / "kpi_summary.csv"
    kpi_df.to_csv(kpi_path)

    totals_path = output_dir / "kpi_overview.json"
    pd.Series(totals).to_json(totals_path, indent=2)

    return kpi_df, totals


if __name__ == "__main__":
    df, totals = calculate_and_save_kpis()
    print("Saved KPI summary to outputs/kpi_summary.csv")
    print("Overall metrics:")
    for metric, value in totals.items():
        print(f"  {metric}: {value:.3f}" if isinstance(value, (int, float)) and not np.isnan(value) else f"  {metric}: {value}")
