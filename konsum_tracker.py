import streamlit as st
import json
import pandas as pd
import datetime
import os

# --- Datei-Pfade ---
TASKS_FILE = "xp_tasks.json"
XP_LOG_FILE = "xp_log.json"
MISSIONS_FILE = "missions_done.json"
DAILY_LOG_FILE = "daily_log.json"
STATUS_FILE = "today_status.json"

# --- Utility-Funktionen ---
def load_json(path, default):
    if not os.path.exists(path):
        return default
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default

def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# --- Laden der Daten ---
tasks = load_json(TASKS_FILE, {})
xp_log = pd.DataFrame(load_json(XP_LOG_FILE, []))
missions_done = set(load_json(MISSIONS_FILE, []))
daily_logs = load_json(DAILY_LOG_FILE, [])

# --- Streamlit Page Setup ---
st.set_page_config("XP Tracker v3", page_icon="🧠", layout="wide")
st.title("🌈 XP-Tracker v3 – Stabil & Smart")

# --- Datumsauswahl ---
today = pd.Timestamp.today().normalize()
selected_date = st.date_input("Tag wählen:", value=today.date(), min_value=today.date() - pd.Timedelta(days=30), max_value=today.date())
selected_ts = pd.Timestamp(selected_date)
weekday_de = ["Montag","Dienstag","Mittwoch","Donnerstag","Freitag","Samstag","Sonntag"][selected_ts.weekday()]

# --- Session State für Checkboxen ---n
key = f"done_{selected_date}"
if "done" not in st.session_state:
    st.session_state["done"] = {}
if key not in st.session_state["done"]:
    st.session_state["done"][key] = set()

# --- Funktionen: Anzeige & Berechnung ---
def show_section(name, items, is_neben=False):
    st.subheader(name)
    for i, item in enumerate(items):
        if is_neben and item["task"] in missions_done:
            continue
        cb_key = f"{name}_{i}_{selected_date}"
        checked = cb_key in st.session_state["done"][key]
        if st.checkbox(f"{item['task']} (+{item['xp']} XP)", value=checked, key=cb_key):
            st.session_state["done"][key].add(cb_key)
        else:
            st.session_state["done"][key].discard(cb_key)

def calc_xp_for(date):
    dkey = f"done_{date.date()}"
    done = st.session_state["done"].get(dkey, set())
    total = 0
    for sec, lst in tasks.items():
        if sec == "Wochenplan":
            for itm in lst.get([weekday_de][0] if False else weekday_de, []):
                idx = f"Wochenplan_{lst.index(itm)}_{date.date()}"
                if idx in done:
                    total += itm["xp"]
        else:
            is_neb = (sec == "Nebenmissionen")
            for i,itm in enumerate(lst):
                idx = f"{sec}_{i}_{date.date()}"
                if idx in done and not (is_neb and itm['task'] in missions_done):
                    total += itm["xp"]
    return total

# --- Layout: Aufgaben anzeigen ---
cols = st.columns((1,1,1,1,1.5))
all_sections = [k for k in tasks.keys() if k != "Wochenplan"] + ["Wochenplan"]
# verteile auf Spalten
i = 0
for sec in all_sections:
    col = cols[i % len(cols)]
    with col:
        if sec == "Wochenplan":
            show_section(f"Wochenplan {weekday_de}", tasks.get(sec, {}).get(weekday_de, []))
        else:
            show_section(sec, tasks.get(sec, []), is_neben=(sec=="Nebenmissionen"))
    i += 1

# --- XP Heute & Speicherung ---
xp_today = calc_xp_for(pd.Timestamp(selected_date))
st.markdown(f"### 🎯 XP am {selected_date}: **{xp_today}**")
if st.button("🔄 Speichern XP & Status"):
    # Status-Datei
    save_json(STATUS_FILE, {"date": selected_date.isoformat(), "xp": xp_today})
    # xp_log
    xp_log_new = xp_log[xp_log['Datum'] != selected_date] if not xp_log.empty else xp_log
    xp_log_new = pd.concat([xp_log_new, pd.DataFrame([{"Datum": selected_date, "XP": xp_today}])], ignore_index=True)
    xp_log_new['Datum'] = pd.to_datetime(xp_log_new['Datum']).dt.normalize()
    xp_log_new = xp_log_new.drop_duplicates(subset=['Datum'], keep='last')
    save_json(XP_LOG_FILE, xp_log_new.to_dict(orient='records'))
    # daily log
    entry = {"date": selected_date.isoformat(), "tasks": sorted(list(st.session_state['done'][key]))}
    daily_logs = [e for e in daily_logs if e['date'] != selected_date.isoformat()] + [entry]
    save_json(DAILY_LOG_FILE, daily_logs)
    # missions_done
    for sec in tasks.get('Nebenmissionen', []):
        pass
    st.success("Gespeichert!")

# --- XP-Statistik Tabellen ---
# bereinige Log
xp_df = xp_log_new.copy()
if not xp_df.empty:
    xp_df['Datum'] = pd.to_datetime(xp_df['Datum']).dt.normalize()
    xp_df = xp_df.groupby('Datum').sum().sort_index()
else:
    xp_df = pd.DataFrame(columns=['XP'], index=pd.DatetimeIndex([]))

# letzte 7 Tage
last7_idx = pd.date_range(today - pd.Timedelta(days=6), today)
last7 = xp_df.reindex(last7_idx, fill_value=0)
# Monat
month_start = today.replace(day=1)
monat = xp_df[xp_df.index >= month_start]
# Gesamt
gesamt = xp_df

st.subheader("📊 XP-Statistik")
st.markdown("**Letzte 7 Tage**")
st.dataframe(last7.reset_index().rename(columns={'index':'Datum'}), use_container_width=True)
st.markdown("**Aktueller Monat**")
st.dataframe(monat.reset_index().rename(columns={'index':'Datum'}), use_container_width=True)
st.markdown("**Gesamt**")
st.dataframe(gesamt.reset_index().rename(columns={'index':'Datum'}), use_container_width=True)

# --- Editor für Aufgaben ---
st.markdown("---")
st.subheader("🛠 Aufgaben-Editor")
option = st.selectbox("Kategorie wählen:", list(tasks.keys()))
if option:
    with st.form(f"edit_{option}"):
        edited = st.text_area("JSON bearbeiten:", json.dumps(tasks[option], ensure_ascii=False, indent=2), height=300)
        if st.form_submit_button("Speichern"):
            try:
                tasks[option] = json.loads(edited)
                save_json(TASKS_FILE, tasks)
                st.success(f"{option} aktualisiert!")
            except Exception as e:
                st.error(f"Parsing-Fehler: {e}")
