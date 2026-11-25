Reusable cleaning pipeline for the mobile-money agent network data.
"""
from __future__ import annotations
import pandas as pd
import numpy as np
from typing import Tuple, List, Dict, Any


def clean_agent_data(
    txns: pd.DataFrame,
    agents: pd.DataFrame,
) -> Tuple[pd.DataFrame, List[Dict[str, Any]]]:
    """
    Clean agent transaction data and merge with the agent register.

    Parameters
    ----------
    txns : pd.DataFrame
        Raw transaction extract (columns: txn_id, agent_id, txn_type, amount, txn_date).
    agents : pd.DataFrame
        Agent register (columns: agent_id, county, onboarded).

    Returns
    -------
    clean_df : pd.DataFrame
        Cleaned and enriched transactions with flags and county.
    log : list of dict
        Cleaning log recording each step, rows affected, and decisions.
    """
    log: List[Dict[str, Any]] = []
    df = txns.copy()

    # 1. Uniqueness – remove duplicate txn_id
    n_before = len(df)
    dup_mask = df.duplicated(subset=["txn_id"], keep="first")
    n_dups = int(dup_mask.sum())
    df = df.loc[~dup_mask].copy()
    log.append({
        "step": "remove_duplicates",
        "dimension": "Uniqueness",
        "column": "txn_id",
        "rows_affected": n_dups,
        "detail": f"Removed {n_dups} duplicate txn_id rows (kept first occurrence).",
    })

    # 2. Consistency – standardise txn_type
    original_types = df["txn_type"].astype(str).str.strip().str.lower()
    mapping = {"deposit": "Deposit", "withdrawal": "Withdrawal"}
    df["txn_type"] = original_types.map(mapping)
    invalid_type = df["txn_type"].isna()
    n_invalid_type = int(invalid_type.sum())
    if n_invalid_type:
        df = df.loc[~invalid_type].copy()
    log.append({
        "step": "standardise_txn_type",
        "dimension": "Consistency",
        "column": "txn_type",
        "rows_affected": n_invalid_type,
        "detail": "Mapped all variants to exact values 'Deposit' and 'Withdrawal'.",
    })

    # 3. Validity & types – amount → numeric, txn_date → datetime
    amount_raw = df["amount"].astype(str).str.strip()
    amount_raw = amount_raw.replace({"N/A": np.nan, "nan": np.nan, "": np.nan})
    df["amount"] = pd.to_numeric(amount_raw, errors="coerce")
    n_non_numeric = int(df["amount"].isna().sum())
    log.append({
        "step": "convert_amount_numeric",
        "dimension": "Validity / Accuracy",
        "column": "amount",
        "rows_affected": n_non_numeric,
        "detail": "Converted amount to numeric; 'N/A', blanks and non-parsable strings became NaN.",
    })

    date_str = df["txn_date"].astype(str).str.strip().str.replace("/", "-", regex=False)
    df["txn_date"] = pd.to_datetime(date_str, format="%Y-%m-%d", errors="coerce")
    n_bad_dates = int(df["txn_date"].isna().sum())
    log.append({
        "step": "parse_txn_date",
        "dimension": "Validity / Accuracy",
        "column": "txn_date",
        "rows_affected": n_bad_dates,
        "detail": "Parsed txn_date to datetime (normalised / to -). Unparseable dates set to NaT.",
    })

    # 4. Completeness – impute missing amounts with median, flag them
    n_missing_amt = int(df["amount"].isna().sum())
    median_amt = df["amount"].median()
    df["amount_imputed"] = df["amount"].isna()
    df["amount"] = df["amount"].fillna(median_amt)
    log.append({
        "step": "impute_missing_amount",
        "dimension": "Completeness",
        "column": "amount",
        "rows_affected": n_missing_amt,
        "detail": (
            f"Imputed {n_missing_amt} missing/invalid amounts with median ({median_amt:.0f}). "
            "Justification: median is robust to extreme values; flag column records every imputation."
        ),
    })

    # 5. Outliers – IQR method
    q1 = df["amount"].quantile(0.25)
    q3 = df["amount"].quantile(0.75)
    iqr = q3 - q1
    lower = q1 - 1.5 * iqr
    upper = q3 + 1.5 * iqr
    df["is_outlier"] = (df["amount"] < lower) | (df["amount"] > upper)
    n_outliers = int(df["is_outlier"].sum())
    n_250k = int((df["amount"] == 250000).sum())
    log.append({
        "step": "flag_outliers_iqr",
        "dimension": "Accuracy / Validity",
        "column": "amount",
        "rows_affected": n_outliers,
        "detail": (
            f"IQR bounds [{lower:.0f}, {upper:.0f}]. Flagged {n_outliers} outliers "
            f"(including {n_250k} exact 250000 values). Recommend investigating 250k values with operations."
        ),
    })

    # 6. Merge with agents (left join)
    df = df.merge(agents[["agent_id", "county"]], on="agent_id", how="left")
    n_unknown = int(df["county"].isna().sum())
    df["county"] = df["county"].fillna("Unknown")
    log.append({
        "step": "merge_agents",
        "dimension": "Consistency / Completeness",
        "column": "agent_id / county",
        "rows_affected": n_unknown,
        "detail": (
            f"Left-joined agents register. {n_unknown} transactions reference unknown "
            "agent_id (AG099). County set to 'Unknown'; rows retained."
        ),
    })

    df = df.reset_index(drop=True)
    log.append({
        "step": "final_shape",
        "dimension": "Integrity",
        "column": "all",
        "rows_affected": len(df),
        "detail": f"Clean dataset has {len(df)} rows (started from {n_before}).",
    })

    return df, log
