import streamlit as st
import json
import pandas as pd
import datetime

TASKS_FILE = "tasks.json"
XP_LOG = "xp_log.csv"
REWARDS = [
    {"name": "🚬 Kleine Belohnung", "cost": 30},
    {"name": "🎮 Große Belohnung", "cost": 50},
    {"name": "💨 Bong erlaubt", "cost": 60}
]

def load_tasks():
    with open(TASKS_FILE, encoding="utf-8") as f:
        return json.load(f)

def load_xp_log():
    try:
        df = pd.read_csv(XP_LOG, sep=";", parse_dates=["Datum"])
        df["Datum"] = pd.to_datetime(df["Datum"], errors="coerce").dt.normalize()
        return df.dropna(subset=["Datum"])
    except Exception:
        return pd.DataFrame(columns=["Datum","XP"])

def save_xp_log(logdf):
    logdf.to_csv(XP_LOG, sep=";", index=False)

# --- Streamlit UI ---
st.set_page_config(
    "XP Tracker", 
    page_icon="🧠", 
    layout="wide"
)

st.markdown("""
    <style>
        body {background: #232323 !important;}
        .stApp {background: #232323;}
        .block-container {padding-left:1vw;padding-right:1vw;}
        section.main {max-width:1800px}
        h1, h2, h3, h4, h5, h6 { color: #e6e6e6 !important;}
        .stButton>button {font-size:1em;padding:0.3em 1.2em;}
        .stCheckbox>label {font-size:0.98em;}
    </style>
""", unsafe_allow_html=True)

st.title("🌑 XP-Tracker – Desktop Ansicht")
st.caption("Web-App für Felix | Mit Datumsauswahl & stabilem XP-Chart")

tasks = load_tasks()
logdf = load_xp_log()

tage_de = ["Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag", "Samstag", "Sonntag"]

# --- Datumsauswahl (Standard heute, beliebig zurück) ---
selected_date = st.date_input(
    "Für welchen Tag Aufgaben & XP bearbeiten?",
    value=datetime.date.today(),
    min_value=datetime.date.today() - datetime.timedelta(days=30),
    max_value=datetime.date.today()
)
weekday_de = tage_de[selected_date.weekday()]

# --- Eigener Checkbox-State pro Tag ---
if "daily_state" not in st.session_state:
    st.session_state.daily_state = {}

def get_state_key(d):
    return f"done_{d.isoformat()}"

if get_state_key(selected_date) not in st.session_state.daily_state:
    st.session_state.daily_state[get_state_key(selected_date)] = set()

def show_tasks(section, items):
    st.markdown(f"<div style='font-weight:600;font-size:1.1em;margin-bottom:2px;color:#e6e6e6'>{section}</div>", unsafe_allow_html=True)
    for i, t in enumerate(items):
        key = f"{section}_{i}_{selected_date}"
        checked = key in st.session_state.daily_state[get_state_key(selected_date)]
        check = st.checkbox(f"{t['task']} (+{t['xp']} XP)", key=key, value=checked)
        if check and not checked:
            st.session_state.daily_state[get_state_key(selected_date)].add(key)
        if not check and checked:
            st.session_state.daily_state[get_state_key(selected_date)].remove(key)

def calc_xp(date):
    xp = 0
    keys = st.session_state.daily_state.get(get_state_key(date), set())
    for section, items in [
        ("Morgenroutine", tasks.get("Morgenroutine", [])),
        (f"Wochentags-Quests ({tage_de[date.weekday()]})", tasks.get("Wochenplan", {}).get(tage_de[date.weekday()], [])),
        ("Abendroutine", tasks.get("Abendroutine", [])),
        ("Nebenmissionen", tasks.get("Nebenmissionen", [])),
    ]:
        for i, t in enumerate(items):
            key = f"{section}_{i}_{date}"
            if key in keys:
                xp += t['xp']
    return xp

# --- 4 Spalten Layout ---
col1, col2, col3, col4, col5 = st.columns([1.1,1.1,1.1,1.1,1.5], gap="small")
with col1:
    show_tasks("Morgenroutine", tasks.get("Morgenroutine", []))
with col2:
    wochenplan = tasks.get("Wochenplan", {})
    if weekday_de in wochenplan:
        show_tasks(f"Wochentags-Quests ({weekday_de})", wochenplan[weekday_de])
with col3:
    show_tasks("Abendroutine", tasks.get("Abendroutine", []))
with col4:
    show_tasks("Nebenmissionen", tasks.get("Nebenmissionen", []))
with col5:
    xp_today = calc_xp(selected_date)
    st.markdown(f"<div style='font-size:1.15em;font-weight:600;margin-bottom:10px;color:#f3e564'>XP am {selected_date:%d.%m.%Y}: {xp_today}</div>", unsafe_allow_html=True)
    st.subheader("💰 Belohnungen", divider="gray")
    cols = st.columns(len(REWARDS))
    for i, reward in enumerate(REWARDS):
        btn_key = f"reward_{i}_{selected_date}"
        enabled = xp_today >= reward["cost"]
        if cols[i].button(f"{reward['name']} ({reward['cost']} XP)", key=btn_key, disabled=not enabled):
            st.success("Eingelöst! 🎉")
    if st.button("🔄 XP für diesen Tag speichern/aktualisieren"):
        # Nur EIN Eintrag pro Tag im Log!
        logdf_new = logdf[logdf["Datum"] != pd.to_datetime(selected_date)] if not logdf.empty else logdf
        logdf_new = pd.concat([logdf_new, pd.DataFrame([{"Datum": selected_date, "XP": xp_today}])], ignore_index=True)
        logdf_new["Datum"] = pd.to_datetime(logdf_new["Datum"], errors="coerce").dt.normalize()
        logdf_new = logdf_new.dropna(subset=["Datum"]).drop_duplicates(subset=["Datum"], keep="last")
        save_xp_log(logdf_new)
        st.success(f"XP für {selected_date:%d.%m.%Y} gespeichert!")
    st.divider()
    st.markdown("<b>📊 XP-Wochenübersicht</b>", unsafe_allow_html=True)
    # --- Chart-Block (ohne Duplikate!) ---
    all_log = pd.concat([logdf, pd.DataFrame([{"Datum": selected_date, "XP": xp_today}])], ignore_index=True)
    all_log["Datum"] = pd.to_datetime(all_log["Datum"], errors="coerce").dt.normalize()
    all_log = all_log.dropna(subset=["Datum"]).drop_duplicates(subset=["Datum"], keep="last")
    # Chart für letzte 7 Tage:
    week = all_log[
        all_log["Datum"] >= (pd.to_datetime(datetime.date.today() - datetime.timedelta(days=6)))
    ].set_index("Datum").sort_index()
    date_range = pd.date_range(datetime.date.today() - datetime.timedelta(days=6), datetime.date.today())
    chart = week["XP"].reindex(date_range, fill_value=0)
    st.bar_chart(chart, use_container_width=True)
