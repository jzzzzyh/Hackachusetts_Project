"""
PERSON 3 — Map Builder
======================
Reads predictions.csv and generates an interactive Folium heat map.

Run: python src/make_map.py

Input:  data/processed/predictions.csv
Output: data/processed/risk_map.html  ← open this in a browser for the demo

NOTE: A fake predictions.csv is already in data/processed/ so you can
      build and style the map immediately. Re-run once Person 2 delivers
      the real predictions.
"""

import pandas as pd
import folium
from folium.plugins import HeatMap
import os
import webbrowser

IN_PATH  = "data/processed/predictions.csv"
OUT_PATH = "data/processed/risk_map.html"

RISK_COLOR = {
    "high":   "#d7191c",
    "medium": "#fdae61",
    "low":    "#1a9641",
}

# --- Load ---
print("Loading predictions.csv ...")
df = pd.read_csv(IN_PATH)


def resolve_coords(frame):
    """Give each neighborhood its real centroid from the neighborhoods geojson.

    predictions.csv sometimes carries only the Boston-center fallback (every row
    the same point), which stacks all bubbles into one. We recompute centroids
    from data/raw/neighborhoods.geojson and match composite names like
    'Allston / Brighton' by averaging the centroids of their parts.
    """
    geo_path = "data/raw/neighborhoods.geojson"
    needs = ("lat" not in frame.columns or "lon" not in frame.columns
             or frame[["lat", "lon"]].drop_duplicates().shape[0] <= 1)
    if not (needs and os.path.exists(geo_path)):
        return frame
    try:
        import geopandas as gpd
    except ImportError:
        print("geopandas not available — leaving coordinates as-is.")
        return frame

    g = gpd.read_file(geo_path).to_crs(4326)
    name_col = "blockgr2020_ctr_neighb_name"
    cents = {str(r[name_col]).strip().lower(): (r.geometry.centroid.y, r.geometry.centroid.x)
             for _, r in g.iterrows() if r.geometry is not None}
    aliases = {"financial district": "downtown", "kenmore": "fenway",
               "audubon circle": "fenway", "greater mattapan": "mattapan"}

    def centroid_for(name):
        pts = []
        for part in str(name).split("/"):
            key = part.strip().lower()
            key = aliases.get(key, key)
            if key in cents:
                pts.append(cents[key])
        if not pts:
            return (None, None)
        return (sum(p[0] for p in pts) / len(pts), sum(p[1] for p in pts) / len(pts))

    lats, lons, missed = [], [], []
    for n in frame["neighborhood"]:
        la, lo = centroid_for(n)
        if la is None:
            missed.append(n)
        lats.append(la)
        lons.append(lo)
    frame = frame.copy()
    frame["lat"] = [la if la is not None else frame.get("lat", pd.Series([None])).iloc[0] for la in lats]
    frame["lon"] = [lo if lo is not None else frame.get("lon", pd.Series([None])).iloc[0] for lo in lons]
    matched = len(frame) - len(missed)
    print(f"Resolved centroids for {matched}/{len(frame)} neighborhoods from the geojson.")
    if missed:
        print(f"  Unmatched (left at fallback): {missed}")
    return frame


df = resolve_coords(df)


# Potholes are the main prediction; fall back to all-311 for old prediction files.
if "predicted_potholes" in df.columns:
    VALUE_COL, RISK_COL, WHAT, WHY_COL = "predicted_potholes", "risk_level_pothole", "potholes", "why_potholes"
else:
    VALUE_COL, RISK_COL, WHAT, WHY_COL = "predicted_reports", "risk_level", "reports", "why_reports"


def why_html(text):
    """One plain-language reason per line for the popup."""
    if not isinstance(text, str) or not text.strip():
        return ""
    return ("<br><br><b>Why:</b><br>"
            + "<br>".join(r.strip() for r in text.split(";") if r.strip()))


# --- Math breakdown: the per-input numbers behind each prediction ---
# Written by train_xgboost.py (one row per neighborhood/feature). Optional:
# the map still builds without it (older runs won't have the file).
REASONS_PATH = "data/processed/prediction_reasons.csv"
MODE = "pothole" if WHAT == "potholes" else "everything"
reasons = None
if os.path.exists(REASONS_PATH):
    _r = pd.read_csv(REASONS_PATH)
    if "mode" in _r.columns:
        _r = _r[_r["mode"] == MODE]
    reasons = _r
    print(f"Loaded prediction_reasons.csv ({len(reasons)} rows for mode '{MODE}').")
else:
    print("No prediction_reasons.csv — popups show the plain-language 'Why' only.")


def math_html(neighborhood):
    """A scroll-down table showing the math: baseline + each input's effect."""
    if reasons is None:
        return ""
    sub = reasons[reasons["neighborhood"] == neighborhood].sort_values("rank")
    if sub.empty:
        return ""
    baseline = float(sub["baseline"].iloc[0])
    unit = str(sub["effect_unit"].iloc[0])
    is_pct = unit == "%"
    op = "×" if is_pct else "+"
    rows = [
        f"<tr><td style='padding:2px 8px;'>Typical area-month</td>"
        f"<td style='padding:2px 8px;text-align:right;'><b>{baseline:,.1f}</b></td></tr>"
    ]
    for _, r in sub.iterrows():
        eff = float(r["effect"])
        shown = (f"{op} {eff:+.0f}%" if is_pct else f"{op} {eff:+,.1f}")
        arrow = "▲" if eff > 0 else "▼"
        rows.append(
            f"<tr><td style='padding:2px 8px;'>{arrow} {r['reason']}</td>"
            f"<td style='padding:2px 8px;text-align:right;'>{shown}</td></tr>"
        )
    unit_note = ("percent changes multiply together" if is_pct
                 else f"effects add, in {unit}")
    return (
        "<br><br><details><summary style='cursor:pointer;'><b>Show the math</b></summary>"
        "<table style='border-collapse:collapse;font-size:12px;margin-top:6px;'>"
        "<tr><th style='padding:2px 8px;text-align:left;'>Input</th>"
        "<th style='padding:2px 8px;text-align:right;'>Effect</th></tr>"
        + "".join(rows)
        + "</table>"
        f"<div style='font-size:11px;color:#667;margin-top:4px;'>"
        f"Starts from the typical area-month, then each input above ({unit_note}) "
        f"to reach the prediction.</div></details>"
    )


df[VALUE_COL] = pd.to_numeric(df[VALUE_COL], errors="coerce").fillna(0)
df[RISK_COL] = df[RISK_COL].astype(str).str.lower()
max_val = max(float(df[VALUE_COL].max()), 1.0)
print(f"{len(df)} neighborhoods loaded (mapping predicted {WHAT}).")

# --- Build map ---
boston_center = [42.3601, -71.0589]
# CARTO Voyager basemap. Uses a CARTO API key (set CARTO_KEY env var; falls back
# to the project key). The key is embedded in the generated public HTML, so it is
# visible to anyone who views the map -- rotate it in the CARTO dashboard if leaked.
CARTO_KEY = os.environ.get("CARTO_KEY", "cb1_4tul_1_b72914a49091b720352c5251")
m = folium.Map(location=boston_center, zoom_start=12, tiles=None)
folium.TileLayer(
    tiles=f"https://basemaps.cartocdn.com/rastertiles/light_all/{{z}}/{{x}}/{{y}}.png?key={CARTO_KEY}",
    attr='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>',
    name="Light",
    max_zoom=20,
).add_to(m)

# Street layer (from street_hotspots.py): predicted potholes per street
STREET_GEO = "data/processed/street_predictions.geojson"
if WHAT == "potholes" and os.path.exists(STREET_GEO):
    import geopandas as gpd
    streets = gpd.read_file(STREET_GEO)
    smax = max(float(streets["predicted_potholes"].max()), 1.0)
    street_layer = folium.FeatureGroup(name="Streets (predicted potholes)", show=True)
    for _, r in streets.iterrows():
        color = RISK_COLOR.get(r["risk"], "gray")
        folium.GeoJson(
            r["geometry"].__geo_interface__,
            style_function=lambda _, c=color, w=3 + 7 * r["predicted_potholes"] / smax:
                {"color": c, "weight": w, "opacity": 0.85},
            tooltip=f"#{int(r['rank'])} {r['street']} ({r['neighborhood']})",
            popup=folium.Popup(
                f"<b>#{int(r['rank'])} {r['street']}</b><br>{r['neighborhood']}<br>"
                f"Predicted potholes: <b>{r['predicted_potholes']:.1f}</b><br>"
                f"Already reported: {int(r['potholes_so_far'])}<br>"
                f"Risk: <b>{r['risk'].upper()}</b><br><br><b>Why:</b> "
                + str(r["why"]).replace("; ", "<br>"),
                max_width=340,
            ),
        ).add_to(street_layer)
    street_layer.add_to(m)
    print(f"Added {len(streets)} streets.")
else:
    print("No street_predictions.geojson (run src/street_hotspots.py) — neighborhoods only.")
HAS_STREETS = WHAT == "potholes" and os.path.exists(STREET_GEO)
# neighborhoods stay available as layers you can switch on (top-right control)
area_layer = folium.FeatureGroup(name="Neighborhoods", show=not HAS_STREETS)
heat_layer = folium.FeatureGroup(name="Neighborhood heat", show=not HAS_STREETS)

# Heat map layer (weight = predicted report count)
heat_data = df[["lat", "lon", VALUE_COL]].values.tolist()
HeatMap(
    heat_data,
    radius=30,
    blur=20,
    max_zoom=13,
    gradient={"0.3": "#1a9641", "0.6": "#fdae61", "1.0": "#d7191c"},
).add_to(heat_layer)
heat_layer.add_to(m)

# Markers with popups
for _, row in df.iterrows():
    color = RISK_COLOR.get(row[RISK_COL], "gray")
    folium.CircleMarker(
        location=[row["lat"], row["lon"]],
        radius=4 + 9 * row[VALUE_COL] / max_val,      # slightly smaller orbs
        color=color,
        fill=True,
        fill_color=color,
        fill_opacity=0.55,
        weight=1,
        opacity=0.6,
        popup=folium.Popup(
            f"<b>{row['neighborhood']}</b><br>"
            f"Predicted {WHAT}: {int(row[VALUE_COL])}<br>"
            f"Risk: <b>{row[RISK_COL].upper()}</b>"
            + why_html(row.get(WHY_COL))
            + math_html(row["neighborhood"]),
            max_width=360,
        ),
        tooltip=f"{row['neighborhood']} — {row[RISK_COL].upper()}",
    ).add_to(area_layer)
area_layer.add_to(m)
folium.LayerControl(position="bottomright", collapsed=False).add_to(m)

# Legend (top-right)
legend_html = """
<div style="
    position: fixed; top: 20px; right: 20px; z-index: 1000;
    background: white; padding: 14px 18px; border-radius: 8px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.25); font-family: sans-serif;
    font-size: 13px; line-height: 1.8;">
  <b>Predicted Pothole Risk</b><br>
  <span style="color:#d7191c;">&#9632;</span> High<br>
  <span style="color:#fdae61;">&#9632;</span> Medium<br>
  <span style="color:#1a9641;">&#9632;</span> Low<br>
  <hr style="margin:6px 0;">
  <small>Click a street (or circle) for details<br>Thicker line = more predicted</small>
</div>
"""
m.get_root().html.add_child(folium.Element(legend_html))

# Title
title_html = """
<div style="
    position: fixed; top: 20px; left: 50%; transform: translateX(-50%);
    z-index: 1000; background: white; padding: 10px 20px;
    border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.25);
    font-family: sans-serif; font-size: 15px; font-weight: bold;">
  Boston Pothole Predictor — This Month
</div>
"""
m.get_root().html.add_child(folium.Element(title_html))

# --- Save ---
os.makedirs("data/processed", exist_ok=True)
m.save(OUT_PATH)
print(f"\nDone! Map saved to {OUT_PATH}")
if os.environ.get("NO_BROWSER") != "1":
    print("Opening in browser ...")
    webbrowser.open(os.path.abspath(OUT_PATH))
