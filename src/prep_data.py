"""
PERSON 1 — Data Prep (multi-year)
=================================
Downloads several years of Boston 311 data and outputs report_counts.csv
with one row per neighborhood + year + month. More years = more rows for
the model to learn from.

Run: python src/prep_data.py

Output: data/processed/report_counts.csv
  columns: neighborhood, year, month, report_count

Memory-safe: each yearly CSV (~150-180 MB) is read in CHUNKS and reduced to
monthly counts on the fly, so the whole file is never held in RAM at once.
"""

import pandas as pd
import requests
import os

# Year -> download URL (from data.boston.gov). Add/remove years here.
YEAR_URLS = {
    2024: "https://data.boston.gov/dataset/8048697b-ad64-4bfc-b090-ee00169f2323/resource/dff4d804-5031-443a-8409-8344efd0e5c8/download/lagan_311_open_data_2024_rvsd3.csv",
    2023: "https://data.boston.gov/dataset/8048697b-ad64-4bfc-b090-ee00169f2323/resource/e6013a93-1321-4f2a-bf91-8d8a02f1e62f/download/lagan_311_open_data_2023_rvsd3.csv",
    2022: "https://data.boston.gov/dataset/8048697b-ad64-4bfc-b090-ee00169f2323/resource/81a7b022-f8fc-4da5-80e4-b160058ca207/download/lagan_311_open_data_2022_rvsd3.csv",
}

RAW_DIR  = "data/raw"
OUT_PATH = "data/processed/report_counts.csv"
CHUNK    = 100_000  # rows per chunk when reading

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}


def download_year(year: int, url: str) -> str:
    path = os.path.join(RAW_DIR, f"311_{year}.csv")
    if os.path.exists(path):
        print(f"Using cached {year}: {path}")
        return path
    os.makedirs(RAW_DIR, exist_ok=True)
    print(f"Downloading {year} (this may take 1-2 min) ...")
    with requests.get(url, headers=HEADERS, stream=True, timeout=300) as r:
        r.raise_for_status()
        with open(path, "wb") as f:
            for chunk in r.iter_content(chunk_size=1024 * 1024):
                f.write(chunk)
    print(f"Saved {path}")
    return path


def counts_for_file(path: str) -> pd.DataFrame:
    """Read one yearly CSV in chunks, return monthly counts per neighborhood."""
    parts = []
    date_col = nbhd_col = None

    for chunk in pd.read_csv(path, low_memory=False, chunksize=CHUNK):
        chunk.columns = [c.strip().lower().replace(" ", "_") for c in chunk.columns]

        if date_col is None:
            date_col = next((c for c in chunk.columns if "open" in c and "dt" in c), None) \
                       or next((c for c in chunk.columns if "date" in c), None)
            nbhd_col = next((c for c in chunk.columns if "neighborhood" in c or "ward" in c), None) \
                       or next((c for c in chunk.columns if "district" in c), None)

        c = chunk[[date_col, nbhd_col]].copy()
        c[date_col] = pd.to_datetime(c[date_col], errors="coerce")
        c = c.dropna(subset=[date_col, nbhd_col])
        c["year"] = c[date_col].dt.year
        c["month"] = c[date_col].dt.month
        c["neighborhood"] = c[nbhd_col].astype(str).str.strip().str.title()

        g = c.groupby(["neighborhood", "year", "month"]).size().reset_index(name="report_count")
        parts.append(g)

    # combine the per-chunk counts
    allc = pd.concat(parts, ignore_index=True)
    return allc.groupby(["neighborhood", "year", "month"], as_index=False)["report_count"].sum()


def main():
    all_counts = []
    for year, url in YEAR_URLS.items():
        path = download_year(year, url)
        print(f"Aggregating {year} ...")
        yc = counts_for_file(path)
        # keep only rows whose date actually falls in that year (guards stray dates)
        yc = yc[yc["year"] == year]
        all_counts.append(yc)
        print(f"  {year}: {len(yc)} neighborhood-months")

    counts = pd.concat(all_counts, ignore_index=True)
    counts = counts.sort_values(["year", "month", "neighborhood"])

    os.makedirs("data/processed", exist_ok=True)
    counts.to_csv(OUT_PATH, index=False)

    print(f"\nDone! Saved {len(counts)} rows to {OUT_PATH}")
    print(f"Years: {sorted(counts['year'].unique())}")
    print(counts.head(10).to_string(index=False))


if __name__ == "__main__":
    main()
