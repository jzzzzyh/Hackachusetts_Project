#!/usr/bin/env python3
"""
STEP 4 — Verify Neighborhood Coverage and Identify Gaps
========================================================
Checks that all neighborhoods are properly covered and identifies:
- Missing neighborhoods
- Data quality issues
- Coverage gaps
- Alignment with model training data

Run: python src/verify_neighborhoods.py

Inputs:
  data/processed/neighborhoods.csv
  data/processed/equity_check.csv
  src/train_xgboost.py (for expected neighborhoods)

Outputs:
  Coverage report to console
"""

import os
import pandas as pd
import sys


def get_expected_neighborhoods():
    """Extract expected neighborhoods from train_xgboost.py."""
    expected = {
        "Dorchester": (42.3021, -71.0707),
        "South Boston": (42.3388, -71.0468),
        "South End": (42.3398, -71.0786),
        "Roxbury": (42.3142, -71.0920),
        "East Boston": (42.3784, -71.0282),
        "Back Bay": (42.3503, -71.0810),
        "Jamaica Plain": (42.3100, -71.1148),
        "Charlestown": (42.3782, -71.0602),
        "Brighton": (42.3467, -71.1564),
        "Allston": (42.3534, -71.1312),
        "Fenway": (42.3467, -71.1003),
        "Beacon Hill": (42.3588, -71.0707),
        "Downtown": (42.3560, -71.0550),
        "North End": (42.3647, -71.0542),
        "West End": (42.3676, -71.0764),
        "Waterfront": (42.3628, -71.0480),
    }
    return expected


def fuzzy_match(needle, haystack, threshold=0.6):
    """Simple fuzzy matching for neighborhood names."""
    from difflib import SequenceMatcher
    
    needle_lower = needle.lower()
    matches = []
    
    for hay in haystack:
        hay_lower = hay.lower()
        ratio = SequenceMatcher(None, needle_lower, hay_lower).ratio()
        if ratio >= threshold:
            matches.append((hay, ratio))
    
    # Return best match if found
    if matches:
        return sorted(matches, key=lambda x: x[1], reverse=True)[0][0]
    return None


def main():
    """Verify neighborhood coverage and identify gaps."""
    
    print("="*70)
    print("NEIGHBORHOOD COVERAGE VERIFICATION")
    print("="*70)
    
    # Load data
    print("\nLoading data...")
    try:
        nbhd_df = pd.read_csv("data/processed/neighborhoods.csv")
        equity_df = pd.read_csv("data/processed/equity_check.csv")
        print(f"✓ Neighborhoods: {len(nbhd_df)}")
        print(f"✓ Equity check: {len(equity_df)} neighborhoods with reports")
    except Exception as e:
        print(f"ERROR loading files: {e}")
        return False
    
    # Get expected neighborhoods
    expected = get_expected_neighborhoods()
    print(f"✓ Expected (from model): {len(expected)} neighborhoods")
    
    # Normalize loaded neighborhoods
    loaded_lower = {n.lower(): n for n in nbhd_df["neighborhood"].unique()}
    expected_lower = {n.lower(): n for n in expected.keys()}
    equity_lower = {n.lower(): n for n in equity_df["neighborhood"].unique()}
    
    # Check 1: Expected neighborhoods coverage
    print("\n" + "-"*70)
    print("CHECK 1: Expected Neighborhoods Coverage")
    print("-"*70)
    
    matched = {}
    missing = []
    partial = {}
    
    for exp_lower, exp_name in expected_lower.items():
        # Exact match
        if exp_lower in loaded_lower:
            matched[exp_name] = loaded_lower[exp_lower]
        else:
            # Try fuzzy match
            fuzzy = fuzzy_match(exp_name, list(loaded_lower.values()), threshold=0.65)
            if fuzzy:
                partial[exp_name] = fuzzy
                matched[exp_name] = fuzzy
            else:
                missing.append(exp_name)
    
    print(f"\nExpected neighborhoods: {len(expected)}")
    print(f"  ✓ Exact matches: {len(matched) - len(partial)}")
    print(f"  ~ Fuzzy matches: {len(partial)}")
    print(f"  ✗ Missing: {len(missing)}")
    
    if partial:
        print(f"\nFuzzy matches (possible aliases):")
        for exp, loaded in sorted(partial.items()):
            print(f"  '{exp}' → '{loaded}'")
    
    if missing:
        print(f"\n⚠ MISSING NEIGHBORHOODS:")
        for m in sorted(missing):
            print(f"  - {m}")
    else:
        print(f"\n✓ All expected neighborhoods found!")
    
    # Check 2: Equity data coverage
    print("\n" + "-"*70)
    print("CHECK 2: Equity Data Coverage")
    print("-"*70)
    
    equity_in_loaded = 0
    equity_missing = []
    
    for eq_lower, eq_name in equity_lower.items():
        if eq_lower in loaded_lower:
            equity_in_loaded += 1
        else:
            equity_missing.append(eq_name)
    
    print(f"\nEquity data neighborhoods: {len(equity_df)}")
    print(f"  ✓ Found in loaded neighborhoods: {equity_in_loaded}")
    print(f"  ✗ Not in loaded neighborhoods: {len(equity_missing)}")
    
    if equity_missing:
        print(f"\n⚠ Equity neighborhoods not in main list:")
        for em in sorted(equity_missing):
            count = equity_df[equity_df["neighborhood"] == em]["report_count"].values
            if len(count) > 0:
                print(f"  - {em}: {count[0]:,} reports")
    
    # Check 3: Coordinate coverage
    print("\n" + "-"*70)
    print("CHECK 3: Coordinate Coverage")
    print("-"*70)
    
    missing_coords = nbhd_df[nbhd_df["lat"].isna() | nbhd_df["lon"].isna()]
    if len(missing_coords) > 0:
        print(f"\n⚠ {len(missing_coords)} neighborhoods missing coordinates:")
        print(missing_coords[["neighborhood"]].to_string(index=False))
    else:
        print(f"\n✓ All neighborhoods have valid coordinates")
        print(f"  Range: ({nbhd_df['lat'].min():.4f}, {nbhd_df['lon'].min():.4f}) to ({nbhd_df['lat'].max():.4f}, {nbhd_df['lon'].max():.4f})")
    
    # Check 4: Area coverage
    print("\n" + "-"*70)
    print("CHECK 4: Area Coverage")
    print("-"*70)
    
    missing_area = nbhd_df[nbhd_df["area_sqm"].isna()]
    if len(missing_area) > 0:
        print(f"\n⚠ {len(missing_area)} neighborhoods missing area data")
    else:
        print(f"\n✓ All neighborhoods have area data")
        print(f"  Total area: {nbhd_df['area_sqm'].sum():,.0f} sq meters")
        print(f"  Avg area: {nbhd_df['area_sqm'].mean():,.0f} sq meters")
        print(f"  Largest: {nbhd_df.loc[nbhd_df['area_sqm'].idxmax(), 'neighborhood']} ({nbhd_df['area_sqm'].max():,.0f})")
        print(f"  Smallest: {nbhd_df.loc[nbhd_df['area_sqm'].idxmin(), 'neighborhood']} ({nbhd_df['area_sqm'].min():,.0f})")
    
    # Check 5: Data quality
    print("\n" + "-"*70)
    print("CHECK 5: Data Quality")
    print("-"*70)
    
    duplicates = nbhd_df[nbhd_df.duplicated(subset=["neighborhood"], keep=False)]
    if len(duplicates) > 0:
        print(f"\n⚠ {len(duplicates)} duplicate neighborhood names:")
        for dup in duplicates["neighborhood"].unique():
            count = len(nbhd_df[nbhd_df["neighborhood"] == dup])
            print(f"  - {dup}: {count} entries")
    else:
        print(f"\n✓ No duplicate neighborhoods")
    
    # Check coordinate reasonableness (Boston area)
    boston_lat_min, boston_lat_max = 42.23, 42.40  # Approximate Boston bounds
    boston_lon_min, boston_lon_max = -71.25, -70.98
    
    out_of_bounds = nbhd_df[
        (nbhd_df["lat"] < boston_lat_min) | (nbhd_df["lat"] > boston_lat_max) |
        (nbhd_df["lon"] < boston_lon_min) | (nbhd_df["lon"] > boston_lon_max)
    ]
    
    if len(out_of_bounds) > 0:
        print(f"\n⚠ {len(out_of_bounds)} neighborhoods outside Boston bounds:")
        for _, row in out_of_bounds.iterrows():
            print(f"  - {row['neighborhood']}: ({row['lat']:.4f}, {row['lon']:.4f})")
    else:
        print(f"✓ All neighborhoods within Boston geographic bounds")
    
    # Summary
    print("\n" + "="*70)
    print("SUMMARY")
    print("="*70)
    
    total_checks = 5
    passed_checks = 0
    
    if len(missing) == 0:
        passed_checks += 1
        print("✓ CHECK 1: Expected neighborhoods - PASS")
    else:
        print(f"✗ CHECK 1: Expected neighborhoods - {len(missing)} missing")
    
    if len(equity_missing) == 0:
        passed_checks += 1
        print("✓ CHECK 2: Equity data coverage - PASS")
    else:
        print(f"⚠ CHECK 2: Equity data coverage - {len(equity_missing)} not in main list")
    
    if len(missing_coords) == 0:
        passed_checks += 1
        print("✓ CHECK 3: Coordinate coverage - PASS")
    else:
        print(f"✗ CHECK 3: Coordinate coverage - {len(missing_coords)} missing")
    
    if len(missing_area) == 0:
        passed_checks += 1
        print("✓ CHECK 4: Area coverage - PASS")
    else:
        print(f"✗ CHECK 4: Area coverage - {len(missing_area)} missing")
    
    if len(duplicates) == 0 and len(out_of_bounds) == 0:
        passed_checks += 1
        print("✓ CHECK 5: Data quality - PASS")
    else:
        print(f"⚠ CHECK 5: Data quality - {len(duplicates)} duplicates, {len(out_of_bounds)} out of bounds")
    
    print(f"\nOverall: {passed_checks}/{total_checks} checks passed")
    
    if passed_checks == total_checks:
        print("\n✓ VERIFICATION COMPLETE - All checks passed!")
        return True
    else:
        print(f"\n⚠ VERIFICATION COMPLETE - {total_checks - passed_checks} issues found")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
