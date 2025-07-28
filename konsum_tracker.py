import streamlit as st
import datetime
import json
import pandas as pd

TRACKER_FILE = "consumption_log.json"

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
st.title("💊📝 Konsum- & Einnahme-Tracker (nüchtern, lokal)")

# Zeitraumwahl
today = datetime.date.today()
start_month = today.replace(day=1)
dates_month = [start_month + datetime.timedelta(days=i) for i in range(0, (today - start_month).days + 1)]

# Lade Daten
tracker = load_tracker()

# Tag wählen
sel_date = st.date_input("Tag wählen:", value=today, min_value=start_month, max_value=today)
sel_str = sel_date.isoformat()
if sel_str not in tracker:
    tracker[sel_str] = {
        "denicit": 0, "cigs": 0, "weed_g": 0, "weed_form": []
    }

col1, col2 = st.columns(2)
with col1:
    st.subheader("Denicit-Tabletten")
    deni = st.number_input("Tabletten heute", min_value=0, max_value=20, step=1, value=tracker[sel_str]["denicit"])
    tracker[sel_str]["denicit"] = deni

    st.subheader("Zigaretten")
    cigs = st.number_input("Zigaretten heute", min_value=0, max_value=60, step=1, value=tracker[sel_str]["cigs"])
    tracker[sel_str]["cigs"] = cigs

with col2:
    st.subheader("Weed-Konsum (Gramm)")
    weed_g = st.number_input("Gramm heute", min_value=0.0, max_value=10.0, step=0.1, value=float(tracker[sel_str]["weed_g"]))
    tracker[sel_str]["weed_g"] = weed_g

    st.subheader("Konsumform")
    forms = ["Joint", "Bong", "Vape", "Edibles"]
    selected_forms = st.multiselect("Welche Konsumformen heute?", forms, default=tracker[sel_str].get("weed_form", []))
    tracker[sel_str]["weed_form"] = selected_forms

if st.button("💾 Speichern"):
    save_tracker(tracker)
    st.success(f"Daten für {sel_date.strftime('%d.%m.%Y')} gespeichert.")

# Monats-Data zusammenbauen
hist = []
for d in dates_month:
    key = d.isoformat()
    entry = tracker.get(key, {"denicit":0,"cigs":0,"weed_g":0,"weed_form":[]})
    hist.append([
        d.strftime("%d.%m."),
        entry["denicit"],
        entry["cigs"],
        entry["weed_g"],
        ", ".join(entry["weed_form"])
    ])
df = pd.DataFrame(hist, columns=["Tag", "Denicit", "Zigaretten", "Weed (g)", "Form"]).set_index("Tag")

st.subheader("📅 Monatsübersicht (Tabelle)")
st.dataframe(df, use_container_width=True)

st.subheader("📈 Monatsstatistik")
colA, colB, colC = st.columns(3)
with colA:
    st.markdown("**Denicit (Tabletten)**")
    st.bar_chart(df["Denicit"])
with colB:
    st.markdown("**Zigaretten**")
    st.bar_chart(df["Zigaretten"])
with colC:
    st.markdown("**Weed (g)**")
    st.bar_chart(df["Weed (g)"])

st.caption("Alle Daten bleiben lokal in 'consumption_log.json'. Nüchtern, minimalistisch, ehrlich.")
