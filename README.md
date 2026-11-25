# Duka Sales Exploration and Agent Network Clean-Up

**Repository:** `plp-da-a3-duka-sales-and-agent-cleanup`  
**Assignment:** PLP Data Analytics – Week 3

## Summary of engagements

### Engagement 1 – Duka Electronics
Junior analyst exploration of 1 000 half-year (Jan–Jun 2026) orders. Derived revenue and temporal columns, ranked branches and products, compared weekend vs weekday performance, identified best/worst months, filtered Premium Online coast/capital orders, and reproduced the branch ranking in Excel (SUMIFS + XLOOKUP + PivotTable).

### Engagement 2 – Mobile-money agent network
Audited a deliberately dirty transaction extract (duplicates, inconsistent type strings, missing/non-numeric amounts, mixed date formats, extreme values, unknown agents). Implemented a reusable `clean_agent_data()` pipeline, produced a six-dimension quality audit, merged with the agent register, and delivered county and weekly summary tables plus a formal Data Quality Report.

## How to regenerate the data and run the notebooks

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Generate the source CSVs (do not commit the raw files)
python generate_data.py
# → duka_sales.csv (seed 2026)
# → agents.csv + agent_transactions.csv (seed 44)

# 3. Run the exploration notebook
jupyter notebook duka_sales_exploration.ipynb
# or: jupyter nbconvert --to notebook --execute duka_sales_exploration.ipynb

# 4. Run the clean-up notebook
jupyter notebook agent_cleanup.ipynb
