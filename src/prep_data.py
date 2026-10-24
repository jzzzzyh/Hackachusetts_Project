"""
PERSON 1 — Data Prep
====================
Downloads Boston 311 data and outputs report_counts.csv.
Run: python src/prep_data.py

Output: data/processed/report_counts.csv
  columns: neighborhood, month, year, report_count
"""

import pandas as pd
import requests
import os

RAW_PATH = "data/raw/311_2024.csv"
OUT_PATH = "data/processed/report_counts.csv"

# --- Step 1: Download 311 data if not already present ---
if not os.path.exists(RAW_PATH):
    print("Downloading 311 data...")
    url = "https://data.boston.gov/dataset/8048697b-ad64-4bfc-b090-ee00169f2323/resource/dff4d804-5031-443a-8409-8344efd0e5c8/download/lagan_311_open_data_2024_rvsd3.csv"
    print("Downloading 311 data (this may take 1-2 min, file is ~60MB)...")
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    os.makedirs("data/raw", exist_ok=True)
    with requests.get(url, headers=headers, stream=True, timeout=120) as r:
        r.raise_for_status()
        with open(RAW_PATH, "wb") as f:
            for chunk in r.iter_content(chunk_size=1024 * 1024):
                f.write(chunk)
    print(f"Saved to {RAW_PATH}")
else:
    print(f"Using cached file: {RAW_PATH}")

# --- Step 2: Load and clean ---
print("Loading CSV...")
df = pd.read_csv(RAW_PATH, low_memory=False)
print(f"Rows loaded: {len(df)}")

# Normalize column names to lowercase
df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]

# Find the date column (may vary by year)
date_col = next((c for c in df.columns if "open" in c and "dt" in c), None)
if date_col is None:
    date_col = next((c for c in df.columns if "date" in c), None)
print(f"Using date column: {date_col}")

# Find neighborhood column
nbhd_col = next((c for c in df.columns if "neighborhood" in c or "ward" in c), None)
if nbhd_col is None:
    nbhd_col = next((c for c in df.columns if "district" in c), None)
print(f"Using neighborhood column: {nbhd_col}")

# --- Step 3: Parse dates and group ---
df[date_col] = pd.to_datetime(df[date_col], errors="coerce")
df = df.dropna(subset=[date_col, nbhd_col])
df["month"] = df[date_col].dt.month
df["year"] = df[date_col].dt.year
df["neighborhood"] = df[nbhd_col].str.strip().str.title()

counts = (
    df.groupby(["neighborhood", "year", "month"])
    .size()
    .reset_index(name="report_count")
)

# --- Step 4: Save ---
os.makedirs("data/processed", exist_ok=True)
counts.to_csv(OUT_PATH, index=False)
print(f"\nDone! Saved {len(counts)} rows to {OUT_PATH}")
print(counts.head(10).to_string(index=False))
