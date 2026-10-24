"""
STEP — Street Trees feature
===========================
Counts street trees per neighborhood from data/bprd_trees.csv and saves a
small file the model can join on. Tree roots crack sidewalks, so more trees
may mean more sidewalk-damage reports.

Run: python src/trees_feature.py

Output: data/processed/trees.csv
  columns: neighborhood, tree_count
"""

import pandas as pd
import os

IN_PATH  = "data/bprd_trees.csv"
OUT_PATH = "data/processed/trees.csv"


def main():
    print("Loading street trees ...")
    df = pd.read_csv(IN_PATH, low_memory=False, usecols=["neighborhood", "park"])

    # street trees only (park is blank)
    df = df[df["park"].isna() | (df["park"].astype(str).str.strip() == "")]

    counts = (
        df.groupby("neighborhood")
        .size()
        .reset_index(name="tree_count")
        .sort_values("tree_count", ascending=False)
    )

    os.makedirs("data/processed", exist_ok=True)
    counts.to_csv(OUT_PATH, index=False)

    print(f"Done! Saved {len(counts)} neighborhoods to {OUT_PATH}")
    print(counts.head(10).to_string(index=False))


if __name__ == "__main__":
    main()
