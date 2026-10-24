"""
STEP 10 — Streamlit Dashboard
=============================
A real app (not a single HTML file) showing the Boston civic-risk
predictions: an interactive map, key stats, a top-issues table, and a
crew-dispatch recommendation list.

Run: python -m streamlit run app/dashboard.py

Reads: data/processed/predictions.csv
       data/processed/model_accuracy.csv
       data/processed/feature_importance*.csv
       data/processed/features.csv
"""

import calendar
import os

import folium
import pandas as pd
import streamlit as st
from streamlit_folium import st_folium

PRED_PATH = "data/processed/predictions.csv"
ACC_PATH  = "data/processed/model_accuracy.csv"
FEAT_PATH = "data/processed/features.csv"
IMP_PATHS = {
    "pothole":    "data/processed/feature_importance.csv",
    "everything": "data/processed/feature_importance_everything.csv",
}

RISK_COLORS = {"high": "#e03131", "medium": "#f59f00", "low": "#2f9e44"}

# plain-English names for the model inputs
FEATURE_NAMES = {
    "lag1": "Last month's count",
    "lag12": "Same month last year",
    "roll3": "3-month average",
    "month": "Month of year",
    "season": "Season",
    "nbhd_enc": "Neighborhood",
    "route_count": "MBTA routes",
    "rail_stops_near": "MBTA rail stops",
    "bus_stops_near": "MBTA bus stops",
    "tree_count": "Street trees",
    "equity_score": "Tree-equity score",
    "road_miles": "Road miles",
    "lane_miles": "Lane miles",
    "daily_vehicle_miles": "Daily traffic (vehicle-miles)",
    "population": "Population",
}

st.set_page_config(page_title="Boston Civic Risk", page_icon="🛠️", layout="wide")


@st.cache_data
def load_data():
    df = pd.read_csv(PRED_PATH)
    df["risk_level"] = df["risk_level"].str.lower()
    if "risk_level_pothole" in df.columns:
        df["risk_level_pothole"] = df["risk_level_pothole"].str.lower()
    return df


df = load_data()

if {"predict_year", "predict_month"} <= set(df.columns):
    period = f"{calendar.month_name[int(df['predict_month'].iloc[0])]} {int(df['predict_year'].iloc[0])}"
else:
    period = "this month"

# ---- Header ----
st.title("🛠️ Boston Civic Risk Predictor")
st.caption(
    f"Predicts where pothole reports will pile up in {period}, so crews can go there first. "
    "Model: XGBoost trained on Boston 311 pothole reports from 2015 to today, "
    "using each area's recent pothole history."
)

# ---- Prediction mode toggle: everything vs potholes only ----
has_pothole = "predicted_potholes" in df.columns
st.sidebar.header("What to predict")
mode = st.sidebar.radio(
    "Prediction mode",
    options=["Potholes only", "Everything (all 311)"],
    index=0 if has_pothole else 1,     # potholes is the main prediction
    help="Potholes only = just pothole reports (main model). "
         "Everything = every kind of 311 problem report.",
    disabled=not has_pothole,
)
pothole_mode = has_pothole and mode == "Potholes only"
mode_key = "pothole" if pothole_mode else "everything"

# pick the right columns for the chosen mode
value_col = "predicted_potholes" if pothole_mode else "predicted_reports"
risk_col  = "risk_level_pothole" if (pothole_mode and "risk_level_pothole" in df.columns) else "risk_level"
what_word = "potholes" if pothole_mode else "reports"
target_col = "pothole_count" if pothole_mode else "report_count"

df = df.sort_values(value_col, ascending=False)

# ---- Sidebar filter ----
st.sidebar.header("Filter")
levels = st.sidebar.multiselect(
    "Risk level", options=["high", "medium", "low"],
    default=["high", "medium", "low"],
)
view = df[df[risk_col].isin(levels)]

# ---- Top stats ----
c1, c2, c3 = st.columns(3)
c1.metric("Neighborhoods", len(df))
c2.metric("High-risk areas", int((df[risk_col] == "high").sum()))
c3.metric("Top hotspot", df.iloc[0]["neighborhood"])

st.info(f"Showing **{mode}** — predicted {what_word} per neighborhood for **{period}**.")

# ---- Map + table side by side ----
left, right = st.columns([3, 2])
max_val = max(float(df[value_col].max()), 1.0)

with left:
    st.subheader("Risk map")
    m = folium.Map(location=[42.3601, -71.0589], zoom_start=12, tiles="OpenStreetMap")
    for _, row in view.iterrows():
        folium.CircleMarker(
            location=[row["lat"], row["lon"]],
            radius=6 + 20 * row[value_col] / max_val,   # same scale for both modes
            color=RISK_COLORS.get(row[risk_col], "#888"),
            fill=True,
            fill_opacity=0.7,
            popup=folium.Popup(
                f"<b>{row['neighborhood']}</b><br>"
                f"Predicted {what_word}: {int(row[value_col])}<br>"
                f"Risk: {str(row[risk_col]).title()}",
                max_width=250,
            ),
        ).add_to(m)
    st_folium(m, height=520, use_container_width=True)

with right:
    st.subheader("Priority list — send crews here first")
    show = view[["neighborhood", value_col, risk_col]].copy()
    show.columns = ["Neighborhood", f"Predicted {what_word}", "Risk"]
    st.dataframe(show, hide_index=True, width="stretch", height=520)

# ---- Accuracy: model vs simple guesses ----
st.subheader(f"📊 How accurate is it? ({mode})")
if os.path.exists(ACC_PATH):
    acc = pd.read_csv(ACC_PATH).set_index("mode")
    if mode_key in acc.index:
        a = acc.loc[mode_key]
        a1, a2, a3 = st.columns(3)
        a1.metric("Model — avg error", f"{a['mae']:.0f} {what_word}",
                  help="Average miss per neighborhood per month (lower is better).")
        if "mae_last_month" in a:
            a2.metric("Guess 'same as last month'", f"{a['mae_last_month']:.0f}",
                      delta=f"{a['mae_last_month'] - a['mae']:+.0f} better", delta_color="normal")
            a3.metric("Guess 'same month last year'", f"{a['mae_last_year']:.0f}",
                      delta=f"{a['mae_last_year'] - a['mae']:+.0f} better", delta_color="normal")
        st.write(
            f"Tested on **{a.get('test_period', 'the last 12 months')}**, months the model never saw "
            f"while training. A neighborhood averages **{a.get('mean_actual', float('nan')):.0f}** "
            f"{what_word} a month; the model is off by **{a['mae']:.0f}** on average "
            f"(**{a['success_pct']:.0f}%** success). The green numbers show how much better it is "
            "than the simple guesses."
        )
    st.bar_chart(acc.set_index("label")["success_pct"])
    st.caption("Success % = 1 − average error ÷ average true value (100% = perfect).")
else:
    st.info("Run `python src/train_xgboost.py` to generate the accuracy check.")

# ---- What drives the prediction ----
st.subheader("What drives the prediction?")
imp_path = IMP_PATHS[mode_key]
if os.path.exists(imp_path):
    imp = pd.read_csv(imp_path)
    imp["Input"] = imp["feature"].map(FEATURE_NAMES).fillna(imp["feature"])
    past_share = imp[imp["feature"].isin(["lag1", "lag12", "roll3"])]["importance"].sum()
    st.write(
        f"Recent history carries **{past_share:.0%}** of the model's attention: an area that had "
        f"many {what_word} recently tends to keep having them. Bigger bars = more influence."
    )
    st.bar_chart(imp.set_index("Input")["importance"])
else:
    st.info("Run `python src/train_xgboost.py` to generate the feature chart.")

# ---- What the data shows (plain English) ----
st.subheader("What the data shows")
if os.path.exists(FEAT_PATH):
    feats = pd.read_csv(FEAT_PATH)
    feats = feats[feats["complete"] == 1] if "complete" in feats.columns else feats
    by_month = feats.groupby("month")[target_col].mean()
    peak, low = int(by_month.idxmax()), int(by_month.idxmin())
    lines = [
        f"- **Seasons:** {what_word} peak in **{calendar.month_name[peak]}** "
        f"(avg {by_month.max():.0f} per area) and bottom out in **{calendar.month_name[low]}** "
        f"(avg {by_month.min():.0f}).",
    ]
    if "tree_count" in feats.columns:
        per_area = feats.groupby("neighborhood").agg(trees=("tree_count", "first"), val=(target_col, "mean"))
        corr = per_area["trees"].corr(per_area["val"])
        lines.append(f"- **Street trees:** areas with more trees log {'more' if corr > 0 else 'fewer'} "
                     f"{what_word} (correlation **{corr:+.2f}** across {len(per_area)} areas). "
                     "Bigger areas have both more trees and more streets, so this is partly size.")
    st.markdown("\n".join(lines) + """
- **Weather is not a model input.** We tested it on 6 held-out years: it made the
  all-311 model worse every year and helped potholes in only half of them. Pothole
  reports do peak about two months after snowfall, but the month and last year's
  count already capture that. The big jumps after snowy winters come mostly from
  city crews logging their own repairs, not from residents.
""")
    st.caption(
        "These are correlations, not proven causes. Street trees are a live feed "
        "(Boston ArcGIS); the tree-equity score only fills gaps."
    )
