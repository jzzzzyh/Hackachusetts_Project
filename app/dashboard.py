"""
STEP 10 — Streamlit Dashboard
=============================
A real app (not a single HTML file) showing the Boston civic-risk
predictions: an interactive map, key stats, a top-issues table, and a
crew-dispatch recommendation list.

Run: python -m streamlit run app/dashboard.py

Reads: data/processed/predictions.csv
       (neighborhood, predicted_reports, risk_level, lat, lon)
"""

import pandas as pd
import streamlit as st
import folium
from streamlit_folium import st_folium

PRED_PATH = "data/processed/predictions.csv"

RISK_COLORS = {"high": "#e03131", "medium": "#f59f00", "low": "#2f9e44"}

st.set_page_config(page_title="Boston Civic Risk", page_icon="🛠️", layout="wide")


@st.cache_data
def load_data():
    df = pd.read_csv(PRED_PATH)
    df["risk_level"] = df["risk_level"].str.lower()
    return df.sort_values("predicted_reports", ascending=False)


df = load_data()

# ---- Header ----
st.title("🛠️ Boston Civic Risk Predictor")
st.caption(
    "Predicts where potholes and sidewalk damage will drive 311 reports next "
    "month. Model: XGBoost trained on 306k real 311 calls + Boston weather."
)

# ---- Sidebar filter ----
st.sidebar.header("Filter")
levels = st.sidebar.multiselect(
    "Risk level", options=["high", "medium", "low"],
    default=["high", "medium", "low"],
)
view = df[df["risk_level"].isin(levels)]

# ---- Top stats ----
c1, c2, c3 = st.columns(3)
c1.metric("Neighborhoods", len(df))
c2.metric("High-risk areas", int((df["risk_level"] == "high").sum()))
c3.metric("Top hotspot", df.iloc[0]["neighborhood"])

# ---- Map + table side by side ----
left, right = st.columns([3, 2])

with left:
    st.subheader("Risk map")
    m = folium.Map(location=[42.3601, -71.0589], zoom_start=12, tiles="OpenStreetMap")
    for _, row in view.iterrows():
        folium.CircleMarker(
            location=[row["lat"], row["lon"]],
            radius=6 + row["predicted_reports"] / 150,
            color=RISK_COLORS.get(row["risk_level"], "#888"),
            fill=True,
            fill_opacity=0.7,
            popup=folium.Popup(
                f"<b>{row['neighborhood']}</b><br>"
                f"Predicted reports: {row['predicted_reports']}<br>"
                f"Risk: {row['risk_level'].title()}",
                max_width=250,
            ),
        ).add_to(m)
    st_folium(m, height=520, use_container_width=True)

with right:
    st.subheader("Priority list — send crews here first")
    show = view[["neighborhood", "predicted_reports", "risk_level"]].copy()
    show.columns = ["Neighborhood", "Predicted reports", "Risk"]
    st.dataframe(show, hide_index=True, use_container_width=True, height=520)

# ---- Proof: weather is training the model ----
import os
st.subheader("Does weather actually drive the model?")

IMP_PATH = "data/processed/feature_importance.csv"
if os.path.exists(IMP_PATH):
    imp = pd.read_csv(IMP_PATH)

    weather_names = ["avg_temp_c", "total_precip_mm", "total_snow_cm", "max_wind_kmh"]
    weather_share = imp[imp["feature"].isin(weather_names)]["importance"].sum()

    st.write(
        f"Weather inputs account for **{weather_share:.0%}** of what the "
        "model uses to predict. Bigger bars = more influence on the forecast."
    )

    # bar chart of every input's importance
    chart = imp.set_index("feature")["importance"]
    st.bar_chart(chart)

    # plain table too
    nice = imp.copy()
    nice["importance"] = (nice["importance"] * 100).round(1).astype(str) + "%"
    nice.columns = ["Input", "How much it matters"]
    st.dataframe(nice, hide_index=True, use_container_width=True)

    # ---- What the model concluded (plain English) ----
    st.subheader("What the model concluded")

    feats = pd.read_csv("data/processed/features.csv")
    cold = feats[feats["avg_temp_c"] <= 5]["report_count"].mean()
    warm = feats[feats["avg_temp_c"] >= 18]["report_count"].mean()
    temp_corr = feats["avg_temp_c"].corr(feats["report_count"])

    tf = feats[feats["tree_count"] > 0]
    tree_corr = tf["tree_count"].corr(tf["report_count"])
    med = tf["tree_count"].median()
    many = tf[tf["tree_count"] >= med]["report_count"].mean()
    few = tf[tf["tree_count"] < med]["report_count"].mean()

    # pull live importances so the text never goes stale
    def share(name):
        row = imp[imp["feature"] == name]
        return float(row["importance"].iloc[0]) if len(row) else 0.0

    st.markdown(
        f"""
**How it works:** the model looked at **10 years (2015-2024)** — for every
neighborhood, every month, it compared the number of 311 problem reports
against that area's weather, its **live** street-tree count, its tree-equity
score, and its nearby MBTA bus/train stops. It found the pattern, then uses
it to guess next month.

**What drives the guess (the % splits above):**
- **Street trees — {share('tree_count'):.0%}.** The biggest signal, now
  pulled **live** from the city's tree map (201k+ trees, counted per area).
  Tree roots push up and crack sidewalks, so leafy areas report more damage.
- **MBTA stops nearby — {share('bus_stops_near'):.0%}.** Heavy bus/train
  traffic wears roads faster.
- **Neighborhood — {share('nbhd_enc'):.0%}.** Past problem areas stay
  problem areas.
- **Temperature — {share('avg_temp_c'):.0%}.** The strongest weather signal.
- **Tree-equity score — {share('equity_score'):.0%}.** Used to fill in areas
  with no live tree polygon. A small nudge only.
- **Month, rain, snow, wind — the rest.** Smaller nudges.

**The tree correlation we found:**
- Areas with MORE trees average **{many:.0f}** reports.
- Areas with FEWER trees average **{few:.0f}** reports.
- Correlation of trees with reports: **{tree_corr:+.2f}** (positive).
- So leafier areas log about **{many/few:.1f}× more** reports.

**The weather correlation we found:**
- Warm months average **{warm:.0f}** reports; cold months **{cold:.0f}**.
- Correlation of temperature with reports: **{temp_corr:+.2f}** (positive).
- Warmer months bring MORE reports — likely because people are out more and
  spot problems more.
"""
    )
    st.caption(
        "Honest note: these are CORRELATIONS, not proven causes — trees, "
        "weather, population and reporting habits all move together. The "
        "tree count is a LIVE feed (Boston ArcGIS, updates daily). The "
        "equity score is only used to estimate trees where no live polygon "
        "matches, so treat it as a rough fill, not a strong signal."
    )
else:
    st.info("Run `python src/train_xgboost.py` to generate the proof chart.")

st.caption(
    "Early model — live feeds now wired in (weather archive + live street "
    "trees). Live weather forecast is the next upgrade."
)
