import streamlit as st
import datetime, json, os
import pandas as pd

TRACKER_FILE = "consumption_log.json"
FORMS = ["Joint", "Bong", "Vape", "Edibles"]
WEED_COST_PER_G = 7.0  # € pro Gramm

def load_tracker():
    if os.path.exists(TRACKER_FILE):
        return json.load(open(TRACKER_FILE, encoding="utf-8"))
    return {}

def save_tracker(data):
    json.dump(data, open(TRACKER_FILE,"w",encoding="utf-8"), ensure_ascii=False, indent=2)

st.set_page_config("Konsum‑Tracker", page_icon="💊", layout="wide")
st.title("📅 Monatsübersicht & Statistik")

# --- Datum & Monatsliste ---
today = datetime.date.today()
start_month = today.replace(day=1)
dates = [start_month + datetime.timedelta(days=i) for i in range((today-start_month).days+1)]

# --- Daten laden und initialisieren ---
tracker = load_tracker()
for d in dates:
    key = d.isoformat()
    if key not in tracker:
        tracker[key] = {"weed":{f:0.0 for f in FORMS}, "coffee":0, "energy":0}

# --- Tag wählen & Eingabe ---
sel = st.date_input("Tag wählen", today, min_value=start_month, max_value=today)
sel_key = sel.isoformat()

col1, col2 = st.columns(2)
with col1:
    st.subheader("Weed (Gramm pro Form)")
    for form in FORMS:
        val = st.number_input(f"{form}", min_value=0.0, max_value=50.0, step=0.1,
                              value=tracker[sel_key]["weed"].get(form,0.0), key=f"{form}")
        tracker[sel_key]["weed"][form] = val
with col2:
    st.subheader("Koffein & Energy")
    tracker[sel_key]["coffee"] = st.number_input("☕ Kaffee/Tee (Becher)", min_value=0, max_value=20, step=1,
                                                  value=tracker[sel_key].get("coffee",0))
    tracker[sel_key]["energy"] = st.number_input("⚡ Energydrinks (Dosen)", min_value=0, max_value=10, step=1,
                                                  value=tracker[sel_key].get("energy",0))

if st.button("💾 Speichern"):
    save_tracker(tracker)
    st.success("Daten gespeichert!")

# --- Monatsdaten aufbereiten ---
hist = []
for d in dates:
    k = d.isoformat()
    wd = tracker[k]["weed"]
    coffee = tracker[k]["coffee"]
    energy = tracker[k]["energy"]
    total_weed = sum(wd.values())
    cost = total_weed * WEED_COST_PER_G
    row = [d.strftime("%d.%m."), *[wd[f] for f in FORMS], total_weed, cost, coffee, energy]
    hist.append(row)

columns = ["Tag", *[f"Weed_{f}" for f in FORMS], "Weed_total_g", "Weed_kosten_€", "Kaffee", "Energy"]
df = pd.DataFrame(hist, columns=columns).set_index("Tag")

# --- Gemeinsame Ansicht: Tabelle + Chart ---
st.subheader("Monatsübersicht")
st.dataframe(df, use_container_width=True)

st.subheader("Monatsstatistik")
# Charts nebeneinander
chart_cols = st.columns(3)
# Weed gesamt + Kosten
chart_cols[0].markdown("**Weed gesamt (g)**")
chart_cols[0].bar_chart(df["Weed_total_g"])
chart_cols[0].markdown("**Weed Kosten (€)**")
chart_cols[0].line_chart(df["Weed_kosten_€"])
# Kaffee vs Energy
chart_cols[1].markdown("**Kaffee (Becher)**")
chart_cols[1].bar_chart(df["Kaffee"])
chart_cols[1].markdown("**Energydrinks (Dosen)**")
chart_cols[1].bar_chart(df["Energy"])
# Detaillierte Weed-Formen
chart_cols[2].markdown("**Weed nach Form (g)**")
chart_cols[2].area_chart(df[[f"Weed_{f}" for f in FORMS]])

st.caption(f"Kostenberechnung: {WEED_COST_PER_G:.0f} € pro Gramm Weed")
