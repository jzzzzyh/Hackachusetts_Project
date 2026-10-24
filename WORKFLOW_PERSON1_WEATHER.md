# Workflow — Person 1: Prove Weather Trains the Model, Show It on the Page

Your job, start to end: make sure weather is really used to train the
model, then show the proof on the software page, right below the map.

"Proof" = the model prints how much each input mattered. If the weather
inputs matter more than 0, weather is being used. You will put that number
on the page so anyone can see it.

---

## First, every time

```bash
git pull origin dev
pip install -r requirements.txt
```

---

## Step 1 — Make the weather data

```bash
python src/fetch_weather.py
```

Makes `data/processed/weather_monthly.csv`
(columns: `year, month, avg_temp_c, total_precip_mm, total_snow_cm, max_wind_kmh`).

---

## Step 2 — Put weather into the model's data

```bash
python src/merge_weather.py
```

Makes `data/processed/features.csv`. It now has the weather columns.

---

## Step 3 — Save the proof when the model trains

The model already uses weather. But it only *prints* the proof to the
screen. You need to *save* it to a file so the page can read it.

Open `src/train_xgboost.py`. Find this line:

```python
    imp = dict(zip(feature_cols, model.feature_importances_.round(3)))
    print("Feature importance:", imp)
```

Add right after it:

```python
    # --- save proof that weather trained the model ---
    imp_df = pd.DataFrame(
        {"feature": list(imp.keys()), "importance": list(imp.values())}
    ).sort_values("importance", ascending=False)
    imp_df.to_csv("data/processed/feature_importance.csv", index=False)
    print("Saved proof to data/processed/feature_importance.csv")
```

Then train:

```bash
python src/train_xgboost.py
```

Makes `data/processed/feature_importance.csv`
(columns: `feature, importance`).

Check it: the weather rows (`avg_temp_c`, `total_precip_mm`,
`total_snow_cm`, `max_wind_kmh`) should have importance above 0.
If they do, weather is training the model.

---

## Step 4 — Show the proof on the page, below the map

Open `app/dashboard.py`. Find the last caption, near the bottom:

```python
st.caption(
    "Early model — more live data feeds (weather is live now) will sharpen "
    "predictions before the hackathon ends."
)
```

Add this **right above** that caption (so it sits below the map):

```python
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
```

---

## Step 5 — Look at it

```bash
python -m streamlit run app/dashboard.py
```

Open the page (port 8501). Scroll below the map. You should see:

| On the page | What it proves |
|---|---|
| "Weather inputs account for X%" | weather really trains the model |
| Bar chart | each input's influence, side by side |
| Table | the exact numbers |

If the weather bars are above 0, you are done.

---

## When you finish

```bash
git add src/train_xgboost.py app/dashboard.py data/processed/feature_importance.csv data/processed/weather_monthly.csv data/processed/features.csv
git commit -m "Prove weather trains model; show feature importance below map"
git push origin dev
```

**Risk:** only one person trains the model at a time. Two trainers at once
may run the machine out of memory.
