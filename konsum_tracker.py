import streamlit as st
import datetime
import json
import pandas as pd

TRACKER_FILE = "consumption_log.json"
FORMS = ["Joint", "Bong", "Vape", "Edibles"]

def load_tracker():
    try:
        with open(TRACKER_FILE, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}

def save_tracker(data):
    with open(TRACKER_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# --- Streamlit Setup ---
st.set_page_config("Konsum- & Einnahmetracker", page_icon="💊", layout="wide")
st.title("💊📝 Konsum- & Einnahme-Tracker (Gramm pro Konsumform + Koffein)")

# --- Datum & Monatsliste ---
today = datetime.date.today()
start_month = today.replace(day=1)
dates_month = [
    start_month + datetime.timedelta(days=i)
    for i in range((today - start_month).days + 1)
]

# --- Daten laden ---
tracker = load_tracker()

# --- Tag Auswahl ---
sel_date = st.date_input(
    "Tag wählen:",
    value=today,
    min_value=start_month,
    max_value=today
)
sel_str = sel_date.isoformat()

# --- Initialisierung für den Tag ---
if sel_str not in tracker:
    tracker[sel_str] = {
        "denicit": 0,
        "cigs": 0,
        "weed": {form: 0.0 for form in FORMS},
        "coffee": 0,
        "energy": 0
    }

# --- Eingabe-Formulare ---
col1, col2, col3 = st.columns(3)

with col1:
    st.subheader("Denicit‑Tabletten")
    tracker[sel_str]["denicit"] = st.number_input(
        "Tabletten heute",
        min_value=0, max_value=20, step=1,
        value=tracker[sel_str]["denicit"]
    )

    st.subheader("Zigaretten")
    tracker[sel_str]["cigs"] = st.number_input(
        "Zigaretten heute",
        min_value=0, max_value=60, step=1,
        value=tracker[sel_str]["cigs"]
    )

with col2:
    st.subheader("Weed‑Konsum nach Form (g)")
    for form in FORMS:
        tracker[sel_str]["weed"][form] = st.number_input(
            f"{form} (g)",
            min_value=0.0, max_value=10.0, step=0.05,
            value=float(tracker[sel_str]["weed"].get(form, 0.0)),
            key=f"weed_{form}"
        )

with col3:
    st.subheader("☕ Kaffee/Tee (Becher)")
    tracker[sel_str]["coffee"] = st.number_input(
        "Becher heute",
        min_value=0, max_value=20, step=1,
        value=tracker[sel_str].get("coffee", 0)
    )

    st.subheader("⚡ Energydrinks (Dosen)")
    tracker[sel_str]["energy"] = st.number_input(
        "Dosen heute",
        min_value=0, max_value=10, step=1,
        value=tracker[sel_str].get("energy", 0)
    )

if st.button("💾 Speichern"):
    save_tracker(tracker)
    st.success(f"Daten für {sel_date.strftime('%d.%m.%Y')} gespeichert.")

# --- Monatsdaten aufbereiten ---
hist = []
for d in dates_month:
    key = d.isoformat()
    entry = tracker.get(key, {
        "denicit": 0, "cigs": 0,
        "weed": {form: 0.0 for form in FORMS},
        "coffee": 0, "energy": 0
    })
    row = [
        d.strftime("%d.%m."),
        entry["denicit"],
        entry["cigs"],
        entry["coffee"],
        entry["energy"]
    ]
    for form in FORMS:
        row.append(entry["weed"].get(form, 0.0))
    hist.append(row)

cols = ["Tag", "Denicit", "Zigaretten", "Kaffee/Tee", "Energydrink"] + [f"Weed: {f}" for f in FORMS]
df = pd.DataFrame(hist, columns=cols).set_index("Tag")

st.subheader("📅 Monatsübersicht (Tabelle)")
st.dataframe(df, use_container_width=True)

# --- Chart-Fix: sicherstellen, dass alle Spalten numeric sind ---
df["Denicit"] = pd.to_numeric(df["Denicit"], errors="coerce").fillna(0).astype(int)
df["Zigaretten"] = pd.to_numeric(df["Zigaretten"], errors="coerce").fillna(0).astype(int)
df["Kaffee/Tee"] = pd.to_numeric(df["Kaffee/Tee"], errors="coerce").fillna(0).astype(int)
df["Energydrink"] = pd.to_numeric(df["Energydrink"], errors="coerce").fillna(0).astype(int)
for form in FORMS:
    col_name = f"Weed: {form}"
    df[col_name] = pd.to_numeric(df[col_name], errors="coerce").fillna(0).astype(float)

# --- Monatsstatistik (Charts) ---
st.subheader("📈 Monatsstatistik")
chart_cols = st.columns(5 + len(FORMS))
chart_cols[0].markdown("**Denicit**")
chart_cols[0].bar_chart(df["Denicit"])
chart_cols[1].markdown("**Zigaretten**")
chart_cols[1].bar_chart(df["Zigaretten"])
chart_cols[2].markdown("**Kaffee/Tee**")
chart_cols[2].bar_chart(df["Kaffee/Tee"])
chart_cols[3].markdown("**Energydrink**")
chart_cols[3].bar_chart(df["Energydrink"])
for idx, form in enumerate(FORMS):
    col_idx = 4 + idx
    chart_cols[col_idx].markdown(f"**Weed ({form})**")
    chart_cols[col_idx].bar_chart(df[f"Weed: {form}"])

st.caption("Alle Daten lokal in 'consumption_log.json' – Gramm pro Form & Koffein-Tracker.")
