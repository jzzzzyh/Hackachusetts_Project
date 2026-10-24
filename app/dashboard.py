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
    "so_far": "Reported so far this month",
    "pace": "This month's pace (projected)",
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


def why_html(text):
    """'vs a typical 59: ▲ a (+5%); ▼ b (-3%)' -> one reason per line for map popups."""
    if not isinstance(text, str):
        return ""
    head, _, rest = text.partition(": ")
    return head + ":<br>" + "<br>".join(rest.split("; "))

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
why_col = "why_potholes" if pothole_mode else "why_reports"

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

st.info(f"Showing **{mode}** — predicted {what_word} "
        f"{'per street (map) and neighborhood' if pothole_mode else 'per neighborhood'} for **{period}**.")

# ---- Map + table side by side ----
STREET_GEO = "data/processed/street_predictions.geojson"
STREET_ACC = "data/processed/street_accuracy.csv"
has_streets = pothole_mode and os.path.exists(STREET_GEO)
detail = st.sidebar.radio(
    "Map detail", ["Streets", "Neighborhoods"], index=0 if has_streets else 1,
    disabled=not has_streets,
    help="Streets = predicted potholes per street (pothole mode only).",
)
street_view = has_streets and detail == "Streets"
@st.cache_data
def load_streets():
    import geopandas as gpd
    return gpd.read_file(STREET_GEO)


if street_view:
    n_streets = len(load_streets())
    top_n = st.sidebar.slider("Streets to show", 10, max(n_streets, 10), min(100, n_streets), step=5)


left, right = st.columns([3, 2])
max_val = max(float(df[value_col].max()), 1.0)

with left:
    st.subheader("Risk map")
    # CARTO public tiles (same as make_map.py): no key, embedding allowed
    m = folium.Map(location=[42.3301, -71.0789], zoom_start=12, tiles=None)
    folium.TileLayer(
        tiles="https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png",
        attr='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> '
             'contributors &copy; <a href="https://carto.com/attributions">CARTO</a>',
        subdomains="abcd", max_zoom=20,
    ).add_to(m)
    if street_view:
        streets = load_streets()
        sv = streets[streets["risk"].isin(levels)].nsmallest(top_n, "rank")
        smax = max(float(sv["predicted_potholes"].max()), 1.0) if len(sv) else 1.0
        for _, r in sv.iterrows():
            color = RISK_COLORS.get(r["risk"], "#888")
            folium.GeoJson(
                r["geometry"].__geo_interface__,
                style_function=lambda _, c=color, w=3 + 7 * r["predicted_potholes"] / smax:
                    {"color": c, "weight": w, "opacity": 0.85},
                tooltip=f"#{int(r['rank'])} {r['street']} ({r['neighborhood']}) — "
                        f"{r['predicted_potholes']:.1f} predicted",
                popup=folium.Popup(
                    f"<b>#{int(r['rank'])} {r['street']}</b><br>{r['neighborhood']}<br>"
                    f"Predicted potholes this month: <b>{r['predicted_potholes']:.1f}</b><br>"
                    f"Already reported: {int(r['potholes_so_far'])}<br>"
                    f"Risk: {r['risk'].title()}<br><br><b>Why:</b> "
                    + str(r["why"]).replace("; ", "<br>"),
                    max_width=340,
                ),
            ).add_to(m)
    else:
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
                    f"Risk: {str(row[risk_col]).title()}"
                    + (f"<br><br><b>Why:</b> {why_html(row[why_col])}" if why_col in row else ""),
                    max_width=320,
                ),
            ).add_to(m)
    st_folium(m, height=520, use_container_width=True)

with right:
    if street_view:
        st.subheader("Priority list — streets to check first")
        t = sv[["rank", "street", "neighborhood", "predicted_potholes", "potholes_so_far",
                "past_12_months", "risk", "worst_block", "why"]].copy()
        t.columns = ["#", "Street", "Neighborhood", "Predicted this month", "Reported so far",
                     "Last 12 months", "Risk", "Worst block", "Why"]
        st.dataframe(t, hide_index=True, width="stretch", height=520)
    else:
        st.subheader("Priority list — send crews here first")
        cols = ["neighborhood", value_col, risk_col]
        names = ["Neighborhood", f"Predicted {what_word} (month total)", "Risk"]
        if pothole_mode and "potholes_so_far" in view.columns:
            day = int(view["data_through_day"].iloc[0]) if "data_through_day" in view.columns else 0
            cols.insert(2, "potholes_so_far")
            names.insert(2, f"Reported so far (days 1-{day})")
        if why_col in view.columns:
            cols.append(why_col)
            names.append("Why")
        show = view[cols].copy()
        show.columns = names
        st.dataframe(show, hide_index=True, width="stretch", height=520)

if street_view:
    st.caption(
        "How streets are predicted: each neighborhood's predicted total is split across its "
        "streets by where potholes were reported recently (newer reports count more), plus "
        "the reports already filed this month. Reports are matched to the nearest street "
        "within 60 m. Rank 1-50 = high, 51-200 = medium."
    )
    if os.path.exists(STREET_ACC):
        sa = pd.read_csv(STREET_ACC)
        s0 = sa[(sa["known"] == "start of month") & (sa["method"] == "history split")]
        s1 = sa[(sa["known"] == "start of month") & (sa["method"] == "road-length split")]
        if len(s0) and len(s1):
            st.caption(
                f"Back-test (last 12 months, before any reports that month): the top 200 streets "
                f"caught **{s0['share_in_top200'].iloc[0]:.0%}** of the next month's potholes "
                f"(splitting by road length instead: {s1['share_in_top200'].iloc[0]:.0%}); "
                f"**{s0['top50_hit'].iloc[0]:.0%}** of the real top-50 streets were in the "
                f"predicted top 50 ({s1['top50_hit'].iloc[0]:.0%} by road length)."
            )

# ---- Why: per-area explanation ----
REASONS_PATH = "data/processed/prediction_reasons.csv"
st.subheader("🔍 Why this prediction?")
if os.path.exists(REASONS_PATH):
    reasons = pd.read_csv(REASONS_PATH)
    reasons = reasons[reasons["mode"] == mode_key]
    pick = st.selectbox("Neighborhood", df["neighborhood"].tolist())
    r = reasons[reasons["neighborhood"] == pick].sort_values("rank")
    if len(r):
        row = df[df["neighborhood"] == pick].iloc[0]
        unit = r["effect_unit"].iloc[0]
        st.write(
            f"The model starts from a typical neighborhood-month (**{r['baseline'].iloc[0]:,.0f}** "
            f"{what_word}) and each input pushes it up or down. For **{pick}** it lands on "
            f"**{int(row[value_col])}**. The biggest pushes:"
        )
        for _, x in r.iterrows():
            arrow = "🔺" if x["effect"] > 0 else "🔻"
            eff = f"{x['effect']:+.0f}%" if unit == "%" else f"{x['effect']:+,.0f} {unit}"
            st.markdown(f"- {arrow} **{x['reason']}** — {eff}")
        chart = r.assign(Input=r["reason"]).set_index("Input")["effect"]
        st.bar_chart(chart, horizontal=True)
        st.caption(
            ("Effects are % changes and multiply together (pothole model uses a count-based loss). "
             if unit == "%" else "Effects are in reports and add together. ")
            + "Computed with SHAP contributions built into XGBoost; they add up exactly to the "
            "model's prediction. They explain the model, not proven causes."
            + (" If the model's number was below the reports already filed, it is raised to that count."
               if pothole_mode else "")
        )
else:
    st.info("Run `python src/train_xgboost.py` to generate the explanations.")

# ---- Accuracy: model vs simple guesses ----
st.subheader(f"📊 How accurate is it? ({mode})")
if os.path.exists(ACC_PATH):
    acc = pd.read_csv(ACC_PATH).set_index("mode")
    if mode_key in acc.index:
        a = acc.loc[mode_key]
        a1, a2, a3 = st.columns(3)
        a1.metric("Model — avg error", f"{a['mae']:.0f} {what_word}",
                  help="Average miss per neighborhood per month (lower is better).")
        day = int(a.get("data_through_day", 0) or 0)
        straight = a.get("mae_straight_line", float("nan"))
        if day and pd.notna(straight):
            # part of the month is known -> compare with the fair simple guess
            a2.metric(f"Straight-line from days 1-{day}", f"{straight:.0f}",
                      delta=f"{straight - a['mae']:+.0f} better", delta_color="normal",
                      help="Reports so far, scaled up to a full month.")
            a3.metric("Guess 'same month last year'", f"{a['mae_last_year']:.0f}",
                      delta=f"{a['mae_last_year'] - a['mae']:+.0f} better", delta_color="normal")
        elif "mae_last_month" in a:
            a2.metric("Guess 'same as last month'", f"{a['mae_last_month']:.0f}",
                      delta=f"{a['mae_last_month'] - a['mae']:+.0f} better", delta_color="normal")
            a3.metric("Guess 'same month last year'", f"{a['mae_last_year']:.0f}",
                      delta=f"{a['mae_last_year'] - a['mae']:+.0f} better", delta_color="normal")
        known = (f" Each test month was scored as if only its first {day} days were known, "
                 "same as today." if day else "")
        st.write(
            f"Tested on **{a.get('test_period', 'the last 12 months')}**, months the model never saw "
            f"while training. A neighborhood averages **{a.get('mean_actual', float('nan')):.0f}** "
            f"{what_word} a month; the model is off by **{a['mae']:.0f}** on average "
            f"(**{a['success_pct']:.0f}%** success).{known} The green numbers show how much better "
            "it is than the simple guesses."
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
    now_share = imp[imp["feature"].isin(["so_far", "pace"])]["importance"].sum()
    if now_share > 0:
        st.write(
            f"Reports already filed this month carry **{now_share:.0%}** of the model's attention, "
            f"and past months another **{past_share:.0%}**. Knowing how the month is going is what "
            "lets it catch the spring pothole spike on time. Bigger bars = more influence."
        )
    else:
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
