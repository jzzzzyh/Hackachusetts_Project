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
else:
    st.info("Run `python src/train_xgboost.py` to generate the proof chart.")

st.caption(
    "Early model — more live data feeds (weather is live now) will sharpen "
    "predictions before the hackathon ends."
)
