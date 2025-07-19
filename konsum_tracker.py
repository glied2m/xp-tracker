import streamlit as st
import datetime, json, os
import pandas as pd

TRACKER_FILE = "consumption_log.json"
FORMS = ["Joint", "Bong", "Vape", "Edibles"]
WEED_COST_PER_G = 7.0  # € pro Gramm Weed

# --- Funktionen zum Laden/Speichern ---
def load_tracker():
    if os.path.exists(TRACKER_FILE):
        return json.load(open(TRACKER_FILE, encoding="utf-8"))
    return {}

def save_tracker(data):
    json.dump(data, open(TRACKER_FILE, "w", encoding="utf-8"), ensure_ascii=False, indent=2)

# --- Streamlit Setup ---
st.set_page_config("Konsum‑Tracker", page_icon="💊", layout="wide")
st.title("📅 Monatsübersicht & Statistik")

# --- Datumsbereich für den aktuellen Monat ---
today = datetime.date.today()
start_month = today.replace(day=1)
dates = [start_month + datetime.timedelta(days=i) for i in range((today - start_month).days + 1)]

# --- Tracker-Daten laden und Struktur sicherstellen ---
tracker = load_tracker()
# vorhandene Einträge auf Vollständigkeit prüfen
for key, entry in tracker.items():
    # Weed-Formen
    if not isinstance(entry.get("weed"), dict):
        entry["weed"] = {f: 0.0 for f in FORMS}
    else:
        for f in FORMS:
            entry["weed"].setdefault(f, 0.0)
    # Kaffee
    entry.setdefault("coffee", 0)
    # Energydrinks
    entry.setdefault("energy", 0)
    # Evanse
    entry.setdefault("evanse", 0)
# fehlende Tage hinzufügen
for d in dates:
    k = d.isoformat()
    if k not in tracker:
        tracker[k] = {
            "weed": {f: 0.0 for f in FORMS},
            "coffee": 0,
            "energy": 0,
            "evanse": 0
        }

# --- Tagesauswahl & Eingabe ---
sel = st.date_input("Tag wählen", today, min_value=start_month, max_value=today)
sel_key = sel.isoformat()

col1, col2 = st.columns(2)
with col1:
    st.subheader("Weed (Gramm pro Form)")
    for form in FORMS:
        val = st.number_input(
            f"{form}", min_value=0.0, max_value=50.0, step=0.1,
            value=float(tracker[sel_key]["weed"].get(form, 0.0)), key=f"weed_{form}"
        )
        tracker[sel_key]["weed"][form] = val

with col2:
    st.subheader("Koffein, Energy & Medikamente")
    tracker[sel_key]["coffee"] = st.number_input(
        "☕ Kaffee/Tee (Becher)", min_value=0, max_value=20, step=1,
        value=int(tracker[sel_key].get("coffee", 0)), key="coffee"
    )
    tracker[sel_key]["energy"] = st.number_input(
        "⚡ Energydrinks (Dosen)", min_value=0, max_value=10, step=1,
        value=int(tracker[sel_key].get("energy", 0)), key="energy"
    )
    tracker[sel_key]["evanse"] = st.number_input(
        "💊 Evanse (Tabletten)", min_value=0, max_value=10, step=1,
        value=int(tracker[sel_key].get("evanse", 0)), key="evanse"
    )

if st.button("💾 Speichern"):
    save_tracker(tracker)
    st.success("Daten gespeichert!")

# --- Monatsdaten zusammenstellen ---
hist = []
for d in dates:
    k = d.isoformat()
    entry = tracker[k]
    wd = entry["weed"]
    coffee = entry.get("coffee", 0)
    energy = entry.get("energy", 0)
    evanse = entry.get("evanse", 0)
    total_weed = sum(wd.values())
    cost = total_weed * WEED_COST_PER_G
    row = [
        d.strftime("%d.%m."),
        *[wd[f] for f in FORMS],
        total_weed,
        cost,
        coffee,
        energy,
        evanse
    ]
    hist.append(row)

columns = [
    "Tag",
    *[f"Weed_{f}" for f in FORMS],
    "Weed_total_g",
    "Weed_kosten_€",
    "Kaffee",
    "Energy",
    "Evanse"
]
df = pd.DataFrame(hist, columns=columns).set_index("Tag")

# --- Gemeinsame Ansicht: Tabelle + Charts ---
st.subheader("Monatsübersicht")
st.dataframe(df, use_container_width=True)

st.subheader("Monatsstatistik")
chart_cols = st.columns(4)

# Weed gesamt + Kosten
tot = df["Weed_total_g"].astype(float)
chart_cols[0].markdown("**Weed gesamt (g)**")
chart_cols[0].bar_chart(tot)
chart_cols[0].markdown("**Weed Kosten (€)**")
chart_cols[0].line_chart(df["Weed_kosten_€"].astype(float))

# Kaffee vs Energy
chart_cols[1].markdown("**Kaffee (Becher)**")
chart_cols[1].bar_chart(df["Kaffee"].astype(int))
chart_cols[1].markdown("**Energydrinks (Dosen)**")
chart_cols[1].bar_chart(df["Energy"].astype(int))

# Evanse-Tabletten
chart_cols[2].markdown("**Evanse (Tabletten)**")
chart_cols[2].bar_chart(df["Evanse"].astype(int))

# Detaillierte Weed-Formen
chart_cols[3].markdown("**Weed nach Form (g)**")
chart_cols[3].area_chart(df[[f"Weed_{f}" for f in FORMS]].astype(float))

st.caption(f"Kostenberechnung: {WEED_COST_PER_G:.0f}€ pro Gramm Weed")
