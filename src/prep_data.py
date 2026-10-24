"""
PERSON 1 — Data Prep (multi-year)
=================================
Downloads Boston 311 data (2015 -> today) and outputs report_counts.csv
with one row per neighborhood + year + month.

Run: python src/prep_data.py

Output: data/processed/report_counts.csv
  columns: neighborhood, year, month,
           report_count       - every 311 report
           pothole_count      - pothole reports (resident + employee)
           pothole_resident   - pothole reports filed by residents (legacy system only)
           pothole_employee   - pothole reports logged by city staff (legacy system only)
           complete           - 1 if the month is fully in the past, 0 for the current month

Two sources:
  * Legacy yearly files (2015-2026). Boston moved potholes to a NEW 311 system
    on 2026-06-23, and other case types have been moving since mid-2025.
  * The NEW SYSTEM file (Aug 2025 ->). Its cases do not overlap the legacy
    file (different case IDs; legacy potholes end 2026-06-24, new-system
    potholes start 2026-06-23), so the two are added together.
    The new system has no "employee vs resident" source, so the resident /
    employee split is blank (NaN) for its rows -> the model uses pothole_count.

Neighborhood labels changed across years and between systems (e.g. "Allston",
"Brighton" and "Allston / Brighton" all exist). Every label is mapped to ONE
canonical area (NBHD_CANON) so no area is counted twice or split in half.

Memory-safe: each file is read in CHUNKS and reduced to monthly counts on the fly.
"""

import os
import time
from datetime import date

import pandas as pd
import requests

_BASE = "https://data.boston.gov/dataset/8048697b-ad64-4bfc-b090-ee00169f2323/resource/"

# Year -> download URL (from data.boston.gov). Add/remove years here.
YEAR_URLS = {
    2026: _BASE + "1a0b420d-99f1-4887-9851-990b2a5a6e17/download/tmpch36ak7j.csv",
    2025: _BASE + "9d7c2214-4709-478a-a2e8-fb2020a5bb94/download/lagan_311_open_data_2025_rvsd3.csv",
    2024: _BASE + "dff4d804-5031-443a-8409-8344efd0e5c8/download/lagan_311_open_data_2024_rvsd3.csv",
    2023: _BASE + "e6013a93-1321-4f2a-bf91-8d8a02f1e62f/download/lagan_311_open_data_2023_rvsd3.csv",
    2022: _BASE + "81a7b022-f8fc-4da5-80e4-b160058ca207/download/lagan_311_open_data_2022_rvsd3.csv",
    2021: _BASE + "f53ebccd-bc61-49f9-83db-625f209c95f5/download/lagan_311_open_data_2021_rvsd3.csv",
    2020: _BASE + "6ff6a6fd-3141-4440-a880-6f60a37fe789/download/lagan_311_open_data_2020_rvsd3.csv",
    2019: _BASE + "ea2e4696-4a2d-429c-9807-d02eb92e0222/download/lagan_311_open_data_2019_rvsd3.csv",
    2018: _BASE + "2be28d90-3a90-4af1-a3f6-f28c1e25880a/download/lagan_311_open_data_2018_rvsd3.csv",
    2017: _BASE + "30022137-709d-465e-baae-ca155b51927d/download/lagan_311_open_data_2017_rvsd3.csv",
    2016: _BASE + "b7ea6b1b-3ca4-4c5b-9713-6dc1db52379a/download/lagan_311_open_data_2016_rvsd3.csv",
    2015: _BASE + "c9509ab4-6f6d-4b97-979a-0cf2a10c922b/download/lagan_311_open_data_2015_rvsd3.csv",
}
NEW_SYSTEM_URL = _BASE + "254adca6-64ab-4c5c-9fc0-a6da622be185/download/tmp7o3lwr4m.csv"

RAW_DIR  = "data/raw"
OUT_PATH = "data/processed/report_counts.csv"
CHUNK    = 100_000      # rows per chunk when reading
FRESH_HOURS = 24        # live files (current year, new system) are re-downloaded after this

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

# Every label seen in either system -> one canonical area.
# Canonical names match the legacy combined labels (longest history).
NBHD_CANON = {
    "Allston": "Allston / Brighton",
    "Brighton": "Allston / Brighton",
    "Allston / Brighton": "Allston / Brighton",
    "South Boston": "South Boston / South Boston Waterfront",
    "South Boston Waterfront": "South Boston / South Boston Waterfront",
    "South Boston / South Boston Waterfront": "South Boston / South Boston Waterfront",
    "Mattapan": "Greater Mattapan",
    "Greater Mattapan": "Greater Mattapan",
    "Fenway": "Fenway / Kenmore / Audubon Circle / Longwood",
    "Longwood": "Fenway / Kenmore / Audubon Circle / Longwood",
    "Fenway / Kenmore / Audubon Circle / Longwood": "Fenway / Kenmore / Audubon Circle / Longwood",
    # legacy "Boston" is a catch-all centered on downtown; the new system splits
    # downtown into several small areas -> fold them all into one.
    "Boston": "Downtown / Financial District",
    "Downtown": "Downtown / Financial District",
    "Downtown / Financial District": "Downtown / Financial District",
    "Chinatown": "Downtown / Financial District",
    "Leather District": "Downtown / Financial District",
    "Bay Village": "Downtown / Financial District",
    "North End": "Downtown / Financial District",
    "West End": "Downtown / Financial District",
    "Back Bay": "Back Bay",
    "Beacon Hill": "Beacon Hill",
    "Charlestown": "Charlestown",
    "Dorchester": "Dorchester",
    "East Boston": "East Boston",
    "Hyde Park": "Hyde Park",
    "Jamaica Plain": "Jamaica Plain",
    "Mission Hill": "Mission Hill",
    "Roslindale": "Roslindale",
    "Roxbury": "Roxbury",
    "South End": "South End",
    "West Roxbury": "West Roxbury",
    # "Chestnut Hill" (1-2 potholes a year, missing most months) is dropped.
}

EMPLOYEE_SOURCES = ("employee", "city worker", "internal", "maximo")


def canon_neighborhood(name) -> str | None:
    """Map any 311 / MBTA / tree label to its canonical area (None = drop)."""
    return NBHD_CANON.get(str(name).strip())


def download(url: str, path: str, max_age_hours: float | None = None) -> str:
    """Download url to path. Reuse the cached file unless it is older than max_age_hours."""
    if os.path.exists(path):
        age_h = (time.time() - os.path.getmtime(path)) / 3600
        if max_age_hours is None or age_h < max_age_hours:
            print(f"Using cached {path}")
            return path
        print(f"{path} is {age_h:.0f}h old, refreshing ...")
    os.makedirs(RAW_DIR, exist_ok=True)
    print(f"Downloading {path} (this may take 1-2 min) ...")
    tmp = path + ".part"
    with requests.get(url, headers=HEADERS, stream=True, timeout=300) as r:
        r.raise_for_status()
        with open(tmp, "wb") as f:
            for chunk in r.iter_content(chunk_size=1024 * 1024):
                f.write(chunk)
    os.replace(tmp, path)     # only replace the cache once the download finished
    print(f"Saved {path}")
    return path


def download_year(year: int, url: str) -> str:
    live = year >= date.today().year
    return download(url, os.path.join(RAW_DIR, f"311_{year}.csv"),
                    FRESH_HOURS if live else None)


def _aggregate(c: pd.DataFrame) -> pd.DataFrame:
    """c has columns dt, nbhd, is_pothole, is_employee (NaN = unknown)."""
    c = c.dropna(subset=["dt"])
    c["neighborhood"] = c["nbhd"].map(canon_neighborhood)
    c = c.dropna(subset=["neighborhood"])
    c["year"] = c["dt"].dt.year
    c["month"] = c["dt"].dt.month
    pot = c["is_pothole"] == 1
    c["pothole_employee"] = (pot & (c["is_employee"] == 1)).astype(float)
    c["pothole_resident"] = (pot & (c["is_employee"] == 0)).astype(float)
    unknown = c["is_employee"].isna()
    c.loc[unknown, ["pothole_employee", "pothole_resident"]] = float("nan")
    monthly = c.groupby(["neighborhood", "year", "month"]).agg(
        report_count=("is_pothole", "size"),
        pothole_count=("is_pothole", "sum"),
        pothole_resident=("pothole_resident", lambda s: s.sum(min_count=1)),
        pothole_employee=("pothole_employee", lambda s: s.sum(min_count=1)),
    ).reset_index()
    # pothole reports per DAY, so the model can see how a month is going so far
    p = c[pot]
    daily = (p.groupby(["neighborhood", "year", "month", p["dt"].dt.day.rename("day")])
             .size().rename("potholes").reset_index())
    return monthly, daily


def counts_for_legacy(path: str) -> pd.DataFrame:
    """Read one legacy yearly CSV in chunks, return monthly counts per area."""
    parts = []
    cols = ["open_dt", "neighborhood", "type", "source"]
    for chunk in pd.read_csv(path, usecols=cols, low_memory=False, chunksize=CHUNK):
        c = pd.DataFrame({
            "dt": pd.to_datetime(chunk["open_dt"], errors="coerce", format="mixed"),
            "nbhd": chunk["neighborhood"],
            "is_pothole": chunk["type"].astype(str).str.lower().str.contains("pothole").astype(int),
            "is_employee": chunk["source"].astype(str).str.lower()
                           .str.contains("|".join(EMPLOYEE_SOURCES)).astype(int),
        })
        parts.append(_aggregate(c))
    return _sum_parts([m for m, _ in parts]), _sum_daily([d for _, d in parts])


def counts_for_new_system(path: str) -> pd.DataFrame:
    """Read the NEW 311 system export (different column names, UTC timestamps)."""
    parts = []
    cols = ["open_date", "neighborhood", "service_name"]
    for chunk in pd.read_csv(path, usecols=cols, low_memory=False, chunksize=CHUNK):
        dt = pd.to_datetime(chunk["open_date"], errors="coerce", utc=True, format="mixed")
        c = pd.DataFrame({
            "dt": dt.dt.tz_convert("America/New_York").dt.tz_localize(None),
            "nbhd": chunk["neighborhood"],
            "is_pothole": chunk["service_name"].astype(str).str.lower().str.contains("pothole").astype(int),
            "is_employee": float("nan"),   # not recorded in the new system
        })
        parts.append(_aggregate(c))
    return _sum_parts([m for m, _ in parts]), _sum_daily([d for _, d in parts])


def _sum_daily(parts) -> pd.DataFrame:
    return (pd.concat(parts, ignore_index=True)
            .groupby(["neighborhood", "year", "month", "day"], as_index=False)["potholes"].sum())


def _sum_parts(parts) -> pd.DataFrame:
    allc = pd.concat(parts, ignore_index=True)
    return allc.groupby(["neighborhood", "year", "month"], as_index=False).agg(
        report_count=("report_count", "sum"),
        pothole_count=("pothole_count", "sum"),
        pothole_resident=("pothole_resident", lambda s: s.sum(min_count=1)),
        pothole_employee=("pothole_employee", lambda s: s.sum(min_count=1)),
    )


def main():
    all_counts = []
    for year, url in sorted(YEAR_URLS.items()):
        path = download_year(year, url)
        print(f"Aggregating {year} ...")
        yc = counts_for_legacy(path)
        yc = yc[yc["year"] == year]       # guards stray dates
        all_counts.append(yc)
        print(f"  {year}: {len(yc)} area-months, {int(yc.pothole_count.sum())} potholes")

    path = download(NEW_SYSTEM_URL, os.path.join(RAW_DIR, "311_new_system.csv"), FRESH_HOURS)
    print("Aggregating new 311 system ...")
    nc = counts_for_new_system(path)
    nc = nc[nc["year"] >= min(YEAR_URLS)]
    all_counts.append(nc)
    print(f"  new system: {len(nc)} area-months, {int(nc.pothole_count.sum())} potholes")

    counts = _sum_parts(all_counts)

    # Fill every area x month with 0 so "last month" always means last month.
    today = date.today()
    months = pd.period_range(f"{min(YEAR_URLS)}-01", f"{today.year}-{today.month:02d}", freq="M")
    grid = pd.DataFrame(
        [(n, p.year, p.month) for n in sorted(counts["neighborhood"].unique()) for p in months],
        columns=["neighborhood", "year", "month"])
    counts = grid.merge(counts, on=["neighborhood", "year", "month"], how="left")
    counts[["report_count", "pothole_count"]] = counts[["report_count", "pothole_count"]].fillna(0).astype(int)
    # resident/employee only known while potholes were in the legacy system
    legacy = (counts["year"] < 2026) | ((counts["year"] == 2026) & (counts["month"] <= 5))
    for col in ("pothole_resident", "pothole_employee"):
        counts.loc[legacy, col] = counts.loc[legacy, col].fillna(0)
        counts.loc[~legacy, col] = float("nan")

    # The current month is still in progress -> flag it so the model never trains on it.
    counts["complete"] = ((counts["year"] < today.year) |
                          ((counts["year"] == today.year) & (counts["month"] < today.month))).astype(int)

    counts = counts.sort_values(["year", "month", "neighborhood"])
    os.makedirs("data/processed", exist_ok=True)
    counts.to_csv(OUT_PATH, index=False)

    print(f"\nDone! Saved {len(counts)} rows ({counts.neighborhood.nunique()} areas) to {OUT_PATH}")
    print(f"Months: {months[0]} -> {months[-1]} (current month flagged incomplete)")
    print(counts.tail(5).to_string(index=False))


if __name__ == "__main__":
    main()
