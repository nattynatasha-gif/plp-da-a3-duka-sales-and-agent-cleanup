from __future__ import annotations
import pandas as pd
import numpy as np
from typing import Tuple, List, Dict, Any

def clean_agent_data(txns: pd.DataFrame, agents: pd.DataFrame) -> Tuple[pd.DataFrame, List[Dict[str, Any]]]:
    """
    Clean agent transaction data and merge with the agent register.
    Returns (clean_df, log).
    """
    log: List[Dict[str, Any]] = []
    df = txns.copy()

    # 1. Uniqueness
    n_before = len(df)
    n_dups = int(df.duplicated(subset=["txn_id"], keep="first").sum())
    df = df.drop_duplicates(subset=["txn_id"], keep="first").copy()
    log.append({"step": "remove_duplicates", "dimension": "Uniqueness", "column": "txn_id",
                "rows_affected": n_dups, "detail": f"Removed {n_dups} duplicate txn_id rows."})

    # 2. Consistency – standardise txn_type
    df["txn_type"] = df["txn_type"].astype(str).str.strip().str.lower().map({
        "deposit": "Deposit", "withdrawal": "Withdrawal"
    })
    n_invalid = int(df["txn_type"].isna().sum())
    if n_invalid:
        df = df.dropna(subset=["txn_type"]).copy()
    log.append({"step": "standardise_txn_type", "dimension": "Consistency", "column": "txn_type",
                "rows_affected": n_invalid, "detail": "Mapped all variants to 'Deposit' and 'Withdrawal'."})

    # 3. Validity – amount to numeric, date to datetime
    amount_raw = df["amount"].astype(str).str.strip().replace({"N/A": np.nan, "nan": np.nan, "": np.nan})
    df["amount"] = pd.to_numeric(amount_raw, errors="coerce")
    n_non_num = int(df["amount"].isna().sum())
    log.append({"step": "convert_amount", "dimension": "Validity", "column": "amount",
                "rows_affected": n_non_num, "detail": "Converted to numeric; invalid became NaN."})

    date_str = df["txn_date"].astype(str).str.strip().str.replace("/", "-", regex=False)
    df["txn_date"] = pd.to_datetime(date_str, format="%Y-%m-%d", errors="coerce")
    n_bad_date = int(df["txn_date"].isna().sum())
    log.append({"step": "parse_date", "dimension": "Validity", "column": "txn_date",
                "rows_affected": n_bad_date, "detail": "Normalised / to - and parsed to datetime."})

    # 4. Completeness – impute missing amounts
    n_miss = int(df["amount"].isna().sum())
    median_amt = df["amount"].median()
    df["amount_imputed"] = df["amount"].isna()
    df["amount"] = df["amount"].fillna(median_amt)
    log.append({"step": "impute_amount", "dimension": "Completeness", "column": "amount",
                "rows_affected": n_miss,
                "detail": f"Imputed {n_miss} missing amounts with median ({median_amt:.0f}). Flagged in amount_imputed."})

    # 5. Outliers – IQR
    q1, q3 = df["amount"].quantile(0.25), df["amount"].quantile(0.75)
    iqr = q3 - q1
    lower, upper = q1 - 1.5 * iqr, q3 + 1.5 * iqr
    df["is_outlier"] = (df["amount"] < lower) | (df["amount"] > upper)
    n_out = int(df["is_outlier"].sum())
    log.append({"step": "flag_outliers", "dimension": "Accuracy", "column": "amount",
                "rows_affected": n_out,
                "detail": f"IQR bounds [{lower:.0f}, {upper:.0f}]. Flagged {n_out} outliers. Keep 250000 for review."})

    # 6. Merge
    df = df.merge(agents[["agent_id", "county"]], on="agent_id", how="left")
    n_unknown = int(df["county"].isna().sum())
    df["county"] = df["county"].fillna("Unknown")
    log.append({"step": "merge_agents", "dimension": "Consistency", "column": "agent_id",
                "rows_affected": n_unknown,
                "detail": f"{n_unknown} transactions have unknown agent (AG099). County set to 'Unknown'."})

    log.append({"step": "final", "dimension": "Integrity", "column": "all",
                "rows_affected": len(df), "detail": f"Final clean rows: {len(df)} (started from {n_before})."})
    return df.reset_index(drop=True), log
