import streamlit as st
import json
import pandas as pd
import datetime
import os

# --- Datei-Pfade ---
TASKS_FILE = "tasks.json"
XP_LOG_JSON = "xp_log.json"
MISSIONS_DONE_FILE = "missions_done.json"
STATUS_FILE = "today_status.json"
DAILY_LOG_FILE = "daily_log.json"

# --- Belohnungen ---
REWARDS = [
    {"name": "🚬 Kleine Belohnung", "cost": 30},
    {"name": "🎮 Große Belohnung", "cost": 50},
    {"name": "💨 Bong erlaubt", "cost": 60}
]

# --- Laden & Speichern ---
def load_tasks():
    if not os.path.exists(TASKS_FILE): return {}
    with open(TASKS_FILE, encoding="utf-8") as f:
        return json.load(f)

def load_xp_log():
    if not os.path.exists(XP_LOG_JSON):
        return pd.DataFrame(columns=["Datum", "XP"])
    with open(XP_LOG_JSON, encoding="utf-8") as f:
        try:
            data = json.load(f)
            if not data:
                return pd.DataFrame(columns=["Datum", "XP"])
            df = pd.DataFrame(data)
            if "Datum" not in df.columns or "XP" not in df.columns:
                return pd.DataFrame(columns=["Datum", "XP"])
            df["Datum"] = pd.to_datetime(df["Datum"], errors="coerce").dt.normalize()
            return df.dropna(subset=["Datum"])
        except json.JSONDecodeError:
            return pd.DataFrame(columns=["Datum", "XP"])


def save_xp_log(df):
    df_copy = df.copy()
    df_copy["Datum"] = df_copy["Datum"].dt.strftime("%Y-%m-%d")
    with open(XP_LOG_JSON, "w", encoding="utf-8") as f:
        json.dump(df_copy.to_dict(orient="records"), f, ensure_ascii=False, indent=2)

def load_missions_done():
    if not os.path.exists(MISSIONS_DONE_FILE): return set()
    with open(MISSIONS_DONE_FILE, encoding="utf-8") as f:
        return set(json.load(f))

def save_missions_done(done):
    with open(MISSIONS_DONE_FILE, "w", encoding="utf-8") as f:
        json.dump(list(done), f, ensure_ascii=False)

def save_status_json(date, xp):
    status = {
        "date": date.isoformat(),
        "xp": xp
    }
    with open(STATUS_FILE, "w", encoding="utf-8") as f:
        json.dump(status, f, ensure_ascii=False)

def save_daily_log(date, checked_tasks):
    log_entry = {
        "date": date.isoformat(),
        "tasks": sorted(list(checked_tasks))
    }
    all_logs = []
    if os.path.exists(DAILY_LOG_FILE):
        with open(DAILY_LOG_FILE, encoding="utf-8") as f:
            try:
                all_logs = json.load(f)
            except json.JSONDecodeError:
                pass
    all_logs = [entry for entry in all_logs if entry["date"] != date.isoformat()]
    all_logs.append(log_entry)
    with open(DAILY_LOG_FILE, "w", encoding="utf-8") as f:
        json.dump(all_logs, f, ensure_ascii=False, indent=2)

# --- Streamlit Setup ---
st.set_page_config("XP Tracker", page_icon="🧠", layout="wide")

st.title(" XP-Tracker ")
st.caption("Web-App für Felix | Automatisch einmalige Nebenmissionen ausblenden")

# --- Daten einladen ---
tasks = load_tasks()
logdf = load_xp_log()
missions_done = load_missions_done()

for key in ["Morgenroutine", "Abendroutine", "Nebenmissionen", "Wochenplan"]:
    if key not in tasks:
        tasks[key] = [] if key != "Wochenplan" else {}

tage_de = ["Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag", "Samstag", "Sonntag"]

selected_date = st.date_input("Für welchen Tag Aufgaben & XP bearbeiten?", value=datetime.date.today(), min_value=datetime.date.today() - datetime.timedelta(days=30), max_value=datetime.date.today())
weekday_de = tage_de[selected_date.weekday()]

if "daily_state" not in st.session_state:
    st.session_state.daily_state = {}

key_day = f"done_{selected_date.isoformat()}"
if key_day not in st.session_state.daily_state:
    st.session_state.daily_state[key_day] = set()

def show_tasks(section, items, is_neben=False):
    st.markdown(f"<div style='font-weight:600;font-size:1.1em;margin-bottom:2px;color:#e6e6e6'>{section}</div>", unsafe_allow_html=True)
    for i, t in enumerate(items):
        if is_neben and t['task'] in missions_done:
            continue
        key = f"{section}_{i}_{selected_date}"
        checked = key in st.session_state.daily_state[key_day]
        check = st.checkbox(f"{t['task']} (+{t['xp']} XP)", key=key, value=checked)
        if check:
            st.session_state.daily_state[key_day].add(key)
        else:
            st.session_state.daily_state[key_day].discard(key)

def calc_xp(date):
    xp = 0
    keys = st.session_state.daily_state.get(f"done_{date.isoformat()}", set())
    for section, items, is_neben in [
        ("Morgenroutine", tasks.get("Morgenroutine", []), False),
        (f"Wochentags-Quests ({tage_de[date.weekday()]})", tasks.get("Wochenplan", {}).get(tage_de[date.weekday()], []), False),
        ("Abendroutine", tasks.get("Abendroutine", []), False),
        ("Nebenmissionen", tasks.get("Nebenmissionen", []), True),
    ]:
        for i, t in enumerate(items):
            if is_neben and t['task'] in missions_done:
                continue
            key = f"{section}_{i}_{date}"
            if key in keys:
                xp += t['xp']
    return xp

col1, col2, col3, col4, col5 = st.columns([1.1,1.1,1.1,1.1,1.5], gap="small")
with col1:
    show_tasks("Morgenroutine", tasks.get("Morgenroutine", []))
with col2:
    show_tasks(f"Wochentags-Quests ({weekday_de})", tasks.get("Wochenplan", {}).get(weekday_de, []))
with col3:
    show_tasks("Abendroutine", tasks.get("Abendroutine", []))
with col4:
    show_tasks("Nebenmissionen", tasks.get("Nebenmissionen", []), is_neben=True)
with col5:
    xp_today = calc_xp(selected_date)
    st.markdown(f"<div style='font-size:1.15em;font-weight:600;margin-bottom:10px;color:#f3e564'>XP am {selected_date:%d.%m.%Y}: {xp_today}</div>", unsafe_allow_html=True)
    st.subheader("💰 Belohnungen", divider="gray")
    for i, reward in enumerate(REWARDS):
        if st.button(f"{reward['name']} ({reward['cost']} XP)", key=f"reward_{i}_{selected_date}", disabled=xp_today < reward["cost"]):
            st.success("Eingelöst! 🎉")

    if st.button("🔄 XP für diesen Tag speichern/aktualisieren"):
        logdf_new = logdf[logdf["Datum"] != pd.to_datetime(selected_date)] if not logdf.empty else logdf
        logdf_new = pd.concat([logdf_new, pd.DataFrame([{"Datum": selected_date, "XP": xp_today}])], ignore_index=True)
        logdf_new["Datum"] = pd.to_datetime(logdf_new["Datum"], errors="coerce").dt.normalize()
        logdf_new = logdf_new.dropna(subset=["Datum"]).drop_duplicates(subset=["Datum"], keep="last")
        save_xp_log(logdf_new)
        neben_keys = st.session_state.daily_state[key_day]
        for i, t in enumerate(tasks.get("Nebenmissionen", [])):
            if f"Nebenmissionen_{i}_{selected_date}" in neben_keys:
                missions_done.add(t['task'])
        save_missions_done(missions_done)
        save_status_json(selected_date, xp_today)
        save_daily_log(selected_date, st.session_state.daily_state[key_day])
        st.success(f"XP & Nebenmissionen für {selected_date:%d.%m.%Y} gespeichert!")

    st.divider()
    st.markdown("<b>📊 XP-Wochenübersicht</b>", unsafe_allow_html=True)
    all_log = pd.concat([logdf, pd.DataFrame([{"Datum": selected_date, "XP": xp_today}])], ignore_index=True)
    all_log["Datum"] = pd.to_datetime(all_log["Datum"], errors="coerce").dt.normalize()
    all_log = all_log.dropna(subset=["Datum"]).drop_duplicates(subset=["Datum"], keep="last")
    week = all_log[all_log["Datum"] >= pd.to_datetime(datetime.date.today() - datetime.timedelta(days=6))].set_index("Datum").sort_index()
    chart = week["XP"].reindex(pd.date_range(datetime.date.today() - datetime.timedelta(days=6), datetime.date.today()), fill_value=0)
    st.bar_chart(chart, use_container_width=True)

if st.button("🔁 Erledigte Nebenmissionen zurücksetzen"):
    missions_done.clear()
    save_missions_done(missions_done)
    st.success("Alle Nebenmissionen wieder sichtbar!")
