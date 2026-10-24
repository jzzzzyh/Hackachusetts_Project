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
    2021: "https://data.boston.gov/dataset/8048697b-ad64-4bfc-b090-ee00169f2323/resource/f53ebccd-bc61-49f9-83db-625f209c95f5/download/lagan_311_open_data_2021_rvsd3.csv",
    2020: "https://data.boston.gov/dataset/8048697b-ad64-4bfc-b090-ee00169f2323/resource/6ff6a6fd-3141-4440-a880-6f60a37fe789/download/lagan_311_open_data_2020_rvsd3.csv",
    2019: "https://data.boston.gov/dataset/8048697b-ad64-4bfc-b090-ee00169f2323/resource/ea2e4696-4a2d-429c-9807-d02eb92e0222/download/lagan_311_open_data_2019_rvsd3.csv",
    2018: "https://data.boston.gov/dataset/8048697b-ad64-4bfc-b090-ee00169f2323/resource/2be28d90-3a90-4af1-a3f6-f28c1e25880a/download/lagan_311_open_data_2018_rvsd3.csv",
    2017: "https://data.boston.gov/dataset/8048697b-ad64-4bfc-b090-ee00169f2323/resource/30022137-709d-465e-baae-ca155b51927d/download/lagan_311_open_data_2017_rvsd3.csv",
    2016: "https://data.boston.gov/dataset/8048697b-ad64-4bfc-b090-ee00169f2323/resource/b7ea6b1b-3ca4-4c5b-9713-6dc1db52379a/download/lagan_311_open_data_2016_rvsd3.csv",
    2015: "https://data.boston.gov/dataset/8048697b-ad64-4bfc-b090-ee00169f2323/resource/c9509ab4-6f6d-4b97-979a-0cf2a10c922b/download/lagan_311_open_data_2015_rvsd3.csv",
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
    date_col = nbhd_col = type_col = None

    for chunk in pd.read_csv(path, low_memory=False, chunksize=CHUNK):
        chunk.columns = [c.strip().lower().replace(" ", "_") for c in chunk.columns]

        if date_col is None:
            date_col = next((c for c in chunk.columns if "open" in c and "dt" in c), None) \
                       or next((c for c in chunk.columns if "date" in c), None)
            nbhd_col = next((c for c in chunk.columns if "neighborhood" in c or "ward" in c), None) \
                       or next((c for c in chunk.columns if "district" in c), None)
            type_col = "type" if "type" in chunk.columns else None

        cols = [date_col, nbhd_col] + ([type_col] if type_col else [])
        c = chunk[cols].copy()
        c[date_col] = pd.to_datetime(c[date_col], errors="coerce")
        c = c.dropna(subset=[date_col, nbhd_col])
        c["year"] = c[date_col].dt.year
        c["month"] = c[date_col].dt.month
        c["neighborhood"] = c[nbhd_col].astype(str).str.strip().str.title()

        # flag pothole-type reports so we can count them separately
        if type_col:
            t = c[type_col].astype(str).str.lower()
            c["is_pothole"] = t.str.contains("pothole").astype(int)
        else:
            c["is_pothole"] = 0

        g = c.groupby(["neighborhood", "year", "month"]).agg(
            report_count=("is_pothole", "size"),
            pothole_count=("is_pothole", "sum"),
        ).reset_index()
        parts.append(g)

    # combine the per-chunk counts
    allc = pd.concat(parts, ignore_index=True)
    return allc.groupby(["neighborhood", "year", "month"], as_index=False)[
        ["report_count", "pothole_count"]
    ].sum()


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
