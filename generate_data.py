Dataset generators for PLP DA A3:
- Duka Electronics sales (seed 2026) → duka_sales.csv
- Mobile-money agent network (seed 44) → agents.csv, agent_transactions.csv
"""
import numpy as np
import pandas as pd

def generate_duka_sales(seed: int = 2026, n: int = 1000) -> None:
    rng = np.random.default_rng(seed)

    branches = ["Nairobi CBD", "Westlands", "Mombasa", "Kisumu", "Nakuru", "Eldoret"]
    products = [
        "Samsung Galaxy A15", "iPhone 13", "Tecno Spark 20", "Infinix Note 40",
        "Sony WH-1000XM5", "JBL Flip 6", "HP Pavilion 15", "Dell Inspiron 14",
        "LG 43-inch Smart TV", "Hisense 55-inch ULED", "Canon EOS 2000D",
        "Anker PowerCore 20K", "Xiaomi Redmi Buds", "Lenovo IdeaPad 3",
    ]
    channels = ["Online", "In-store"]

    branch_city = {
        "Nairobi CBD": "Nairobi", "Westlands": "Nairobi", "Mombasa": "Mombasa",
        "Kisumu": "Kisumu", "Nakuru": "Nakuru", "Eldoret": "Eldoret",
    }

    start = pd.Timestamp("2026-01-01")
    end = pd.Timestamp("2026-06-30")
    days = (end - start).days
    order_dates = start + pd.to_timedelta(rng.integers(0, days + 1, n), unit="D")

    base_prices = {
        "Samsung Galaxy A15": 18500, "iPhone 13": 72000, "Tecno Spark 20": 14500,
        "Infinix Note 40": 22000, "Sony WH-1000XM5": 35000, "JBL Flip 6": 9800,
        "HP Pavilion 15": 68500, "Dell Inspiron 14": 62000, "LG 43-inch Smart TV": 42000,
        "Hisense 55-inch ULED": 58000, "Canon EOS 2000D": 47500, "Anker PowerCore 20K": 6500,
        "Xiaomi Redmi Buds": 4200, "Lenovo IdeaPad 3": 55000,
    }

    product_list = rng.choice(products, n)
    unit_price = np.array([base_prices[p] * rng.uniform(0.92, 1.08) for p in product_list]).round(0)
    quantity = rng.integers(1, 5, n)
    branch_list = rng.choice(branches, n, p=[0.28, 0.18, 0.16, 0.14, 0.12, 0.12])
    channel_list = rng.choice(channels, n, p=[0.35, 0.65])
    city_list = [branch_city[b] for b in branch_list]

    df = pd.DataFrame({
        "order_id": [f"ORD{i:05d}" for i in range(1, n + 1)],
        "order_date": order_dates.strftime("%Y-%m-%d"),
        "branch": branch_list,
        "city": city_list,
        "product": product_list,
        "quantity": quantity,
        "unit_price": unit_price.astype(int),
        "channel": channel_list,
    })
    df.to_csv("duka_sales.csv", index=False)
    print(f"Wrote duka_sales.csv ({len(df)} rows)")


def generate_agent_data(seed: int = 44, n: int = 600) -> None:
    rng = np.random.default_rng(seed)

    agents = pd.DataFrame({
        "agent_id": [f"AG{i:03d}" for i in range(1, 21)],
        "county": rng.choice(["Nairobi", "Kiambu", "Nakuru", "Mombasa", "Kisumu"], 20),
        "onboarded": pd.date_range("2024-01-01", periods=20, freq="MS").strftime("%Y-%m-%d"),
    })

    txns = pd.DataFrame({
        "txn_id": [f"TX{i:05d}" for i in range(1, n + 1)],
        "agent_id": rng.choice(agents["agent_id"], n),
        "txn_type": rng.choice(["Deposit", "withdrawal", "DEPOSIT ", "Withdrawal", "deposit"], n),
        "amount": rng.lognormal(7.5, 0.8, n).round(0).astype(str),
        "txn_date": (pd.to_datetime("2026-03-01") + pd.to_timedelta(rng.integers(0, 60, n), unit="D")).strftime("%Y-%m-%d"),
    })

    idx = rng.choice(n, 30, replace=False)
    txns.loc[idx[:15], "amount"] = np.nan
    txns.loc[idx[15:20], "amount"] = "N/A"
    txns.loc[idx[20:25], "amount"] = "250000"
    txns.loc[idx[25:], "txn_date"] = txns.loc[idx[25:], "txn_date"].str.replace("-", "/")
    txns = pd.concat([txns, txns.sample(12, random_state=1)], ignore_index=True)
    txns.loc[rng.choice(len(txns), 8, replace=False), "agent_id"] = "AG099"

    agents.to_csv("agents.csv", index=False)
    txns.to_csv("agent_transactions.csv", index=False)
    print(f"Wrote agents.csv ({len(agents)} rows) and agent_transactions.csv ({len(txns)} rows)")


if __name__ == "__main__":
    generate_duka_sales()
    generate_agent_data()
