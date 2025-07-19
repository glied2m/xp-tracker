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

st.set_page_config("Konsum- & Einnahmetracker", page_icon="💊", layout="wide")
st.title("💊📝 Konsum- & Einnahme-Tracker (Gramm pro Konsumform + Koffein)")

today = datetime.date.today()
start_month = today.replace(day=1)
dates_month = [start_month + datetime.timedelta(days=i) for i in range(0, (today - start_month).days + 1)]

tracker = load_tracker()

# Tag wählen
sel_date = st.date_input("Tag wählen:", value=today, min_value=start_month, max_value=today)
sel_str = sel_date.isoformat()

# --- Init Struktur für den Tag ---
if sel_str not in tracker:
    tracker[sel_str] = {
        "denicit": 0,
        "cigs": 0,
        "weed": {form: 0.0 for form in FORMS},
        "coffee": 0,
        "energy": 0
    }

col1, col2, col3 = st.columns(3)
with col1:
    st.subheader("Denicit-Tabletten")
    deni = st.number_input("Tabletten heute", min_value=0, max_value=20, step=1, value=tracker[sel_str]["denicit"])
    tracker[sel_str]["denicit"] = deni

    st.subheader("Zigaretten")
    cigs = st.number_input("Zigaretten heute", min_value=0, max_value=60, step=1, value=tracker[sel_str]["cigs"])
    tracker[sel_str]["cigs"] = cigs

with col2:
    st.subheader("Weed-Konsum nach Form (Gramm)")
    for form in FORMS:
        old = tracker[sel_str]["weed"].get(form, 0.0)
        val = st.number_input(f"{form} (g)", min_value=0.0, max_value=10.0, step=0.05, value=float(old), key=f"weed_{form}")
        tracker[sel_str]["weed"][form] = val

with col3:
    st.subheader("☕ Kaffee/Tee")
    coffee = st.number_input("Tassen/Becher heute", min_value=0, max_value=20, step=1, value=tracker[sel_str].get("coffee", 0))
    tracker[sel_str]["coffee"] = coffee

    st.subheader("⚡ Energydrinks")
    energy = st.number_input("Dosen heute", min_value=0, max_value=10, step=1, value=tracker[sel_str].get("energy", 0))
    tracker[sel_str]["energy"] = energy

if st.button("💾 Speichern"):
    save_tracker(tracker)
    st.success(f"Daten für {sel_date.strftime('%d.%m.%Y')} gespeichert.")

# --- Monats-Tabelle ---
hist = []
for d in dates_month:
    key = d.isoformat()
    entry = tracker.get(key, {
        "denicit":0,"cigs":0,
        "weed":{form:0.0 for form in FORMS},
        "coffee":0,"energy":0
    })
    row = [
        d.strftime("%d.%m."),
        entry["denicit"],
        entry["cigs"],
        entry.get("coffee", 0),
        entry.get("energy", 0)
    ]
    for form in FORMS:
        row.append(entry["weed"].get(form, 0.0))
    hist.append(row)

cols = ["Tag", "Denicit", "Zigaretten", "Kaffee/Tee", "Energydrink"] + [f"Weed: {form}" for form in FORMS]
df = pd.DataFrame(hist, columns=cols).set_index("Tag")

st.subheader("📅 Monatsübersicht (Tabelle)")
st.dataframe(df, use_container_width=True)

st.subheader("📈 Monatsstatistik")
colA, colB, colC, colD, colE, colF, colG = st.columns(7)
with colA:
    st.markdown("**Denicit (Tabletten)**")
    st.bar_chart(df["Denicit"])
with colB:
    st.markdown("**Zigaretten**")
    st.bar_chart(df["Zigaretten"])
with colC:
    st.markdown("**Kaffee/Tee**")
    st.bar_chart(df["Kaffee/Tee"])
with colD:
    st.markdown("**Energydrink**")
    st.bar_chart(df["Energydrink"])
for i, form in enumerate(FORMS):
    with [colE, colF, colG, colA][i]:
        st.markdown(f"**Weed ({form})**")
        st.bar_chart(df[f"Weed: {form}"])

st.caption("Alle Daten bleiben lokal/cloud im Repo – Übersicht für Denicit, Nikotin, Weed, Koffein.")
