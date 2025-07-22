import streamlit as st
import pandas as pd
import datetime
import json
import os

# --- Datei-Pfade ---
TASKS_FILE = "tasks.json"
LOG_FILE = "xp_log.csv"
STATUS_FILE = "today_status.json"
MISSIONS_DONE_FILE = "missions_done.json"

# --- Laden ---
def load_tasks():
    with open(TASKS_FILE, encoding="utf-8") as f:
        return json.load(f)

def load_xp_log():
    try:
        df = pd.read_csv(LOG_FILE, sep=";", parse_dates=["Datum"])
        df["Datum"] = pd.to_datetime(df["Datum"]).dt.normalize()
        return df
    except Exception:
        return pd.DataFrame(columns=["Datum", "XP"])

def save_xp_log(df):
    df.to_csv(LOG_FILE, sep=";", index=False)

def load_missions_done():
    if os.path.exists(MISSIONS_DONE_FILE):
        with open(MISSIONS_DONE_FILE, encoding="utf-8") as f:
            return set(json.load(f))
    return set()

def save_missions_done(data):
    with open(MISSIONS_DONE_FILE, "w", encoding="utf-8") as f:
        json.dump(list(data), f, ensure_ascii=False)

def save_today_status(xp):
    with open(STATUS_FILE, "w", encoding="utf-8") as f:
        json.dump({"date": str(datetime.date.today()), "xp": xp}, f, ensure_ascii=False)

# --- Initialisieren ---
st.set_page_config("XP Tracker", page_icon="💠", layout="wide")
st.title("🧠 XP-Tracker für Felix")

# --- Daten laden ---
tasks = load_tasks()
log = load_xp_log()
missions_done = load_missions_done()

today = datetime.date.today()
selected_date = st.date_input("📅 Wähle ein Datum", value=today, min_value=today - datetime.timedelta(days=30), max_value=today)
state_key = f"checked_{selected_date}"

if state_key not in st.session_state:
    st.session_state[state_key] = {}

def show_section(title, items, section_name, is_neben=False):
    st.subheader(title)
    for i, task in enumerate(items):
        task_id = f"{section_name}_{i}_{selected_date}"
        if is_neben and task["task"] in missions_done:
            continue
        done = st.session_state[state_key].get(task_id, False)
        check = st.checkbox(f"{task['task']} (+{task['xp']} XP)", key=task_id, value=done)
        st.session_state[state_key][task_id] = check

# --- Layout ---
col1, col2, col3, col4 = st.columns(4)
with col1:
    show_section("🌅 Morgenroutine", tasks.get("Morgenroutine", []), "morning")
with col2:
    weekday = selected_date.strftime("%A")
    show_section(f"📆 {weekday}-Quests", tasks.get("Wochenplan", {}).get(weekday, []), "wochenplan")
with col3:
    show_section("🌙 Abendroutine", tasks.get("Abendroutine", []), "abend")
with col4:
    show_section("📦 Nebenmissionen", tasks.get("Nebenmissionen", []), "neben", is_neben=True)

# --- XP berechnen ---
def calculate_xp():
    total = 0
    for section, items in [
        ("morning", tasks.get("Morgenroutine", [])),
        ("wochenplan", tasks.get("Wochenplan", {}).get(weekday, [])),
        ("abend", tasks.get("Abendroutine", [])),
        ("neben", tasks.get("Nebenmissionen", []))
    ]:
        for i, t in enumerate(items):
            task_id = f"{section}_{i}_{selected_date}"
            if st.session_state[state_key].get(task_id, False):
                if section == "neben":
                    missions_done.add(t["task"])
                total += t["xp"]
    return total

xp = calculate_xp()
st.success(f"📈 XP am {selected_date}: {xp}")

if st.button("💾 Speichern"):
    log = log[log["Datum"] != pd.to_datetime(selected_date)]
    log = pd.concat([log, pd.DataFrame([{"Datum": selected_date, "XP": xp}])], ignore_index=True)
    log["Datum"] = pd.to_datetime(log["Datum"]).dt.normalize()
    log = log.drop_duplicates(subset="Datum", keep="last")
    save_xp_log(log)
    save_missions_done(missions_done)
    if selected_date == today:
        save_today_status(xp)
    st.success("✅ Fortschritt gespeichert!")

# --- Wochenchart ---
st.divider()
st.subheader("📊 Wochenübersicht")
df_chart = log.set_index("Datum").resample("D").sum().reindex(
    pd.date_range(today - datetime.timedelta(days=6), today), fill_value=0)
st.bar_chart(df_chart["XP"], use_container_width=True)

# --- Reset Nebenmissionen ---
if st.button("🔁 Nebenmissionen zurücksetzen"):
    missions_done.clear()
    save_missions_done(missions_done)
    st.success("Alle Nebenmissionen sind wieder sichtbar!")
# Dein XP-Tracker Streamlit Frontend-Code
