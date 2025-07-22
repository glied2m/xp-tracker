# xp_tracker_web.py
import streamlit as st
import json
import pandas as pd
import datetime
from pathlib import Path

# Dateien
XP_LOG_FILE = "xp_log.json"
TODAY_STATUS = "today_status.json"
TASKS_FILE = "xp_tasks.json"
MISSIONS_DONE_FILE = "missions_done.json"

# Hilfsfunktionen
def load_tasks():
    with open(TASKS_FILE, encoding="utf-8") as f:
        return json.load(f)

def load_xp_log():
    try:
        with open(XP_LOG_FILE, encoding="utf-8") as f:
            data = json.load(f)
            df = pd.DataFrame(data)
            if "Datum" in df.columns:
                df["Datum"] = pd.to_datetime(df["Datum"], errors="coerce").dt.normalize()
            return df.dropna(subset=["Datum"])
    except Exception:
        return pd.DataFrame(columns=["Datum", "XP"])

def save_xp_log(df):
    try:
        df["Datum"] = pd.to_datetime(df["Datum"], errors="coerce").dt.strftime("%Y-%m-%d")
        with open(XP_LOG_FILE, "w", encoding="utf-8") as f:
            json.dump(df.to_dict(orient="records"), f, ensure_ascii=False, indent=2)
    except Exception as e:
        st.error(f"Fehler beim Speichern: {e}")

def load_missions_done():
    try:
        with open(MISSIONS_DONE_FILE, encoding="utf-8") as f:
            return set(json.load(f))
    except Exception:
        return set()

def save_missions_done(done):
    with open(MISSIONS_DONE_FILE, "w", encoding="utf-8") as f:
        json.dump(list(done), f, ensure_ascii=False)

def save_today_status(xp):
    today = datetime.date.today().isoformat()
    with open(TODAY_STATUS, "w", encoding="utf-8") as f:
        json.dump({"date": today, "xp": xp}, f, ensure_ascii=False, indent=2)

# Layout
st.set_page_config("XP Tracker", page_icon="🧠", layout="wide")
st.title("📅 XP-Tracker")
tasks = load_tasks()
logdf = load_xp_log()
missions_done = load_missions_done()
tage_de = ["Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag", "Samstag", "Sonntag"]

# Datum
selected_date = st.date_input("Für welchen Tag Aufgaben bearbeiten?", value=datetime.date.today())
weekday = tage_de[selected_date.weekday()]
state_key = f"done_{selected_date.isoformat()}"
if state_key not in st.session_state:
    st.session_state[state_key] = set()

# Aufgaben anzeigen
def show_tasks(label, task_list, is_neben=False):
    st.subheader(label)
    for i, task in enumerate(task_list):
        key = f"{label}_{i}_{selected_date}"
        if is_neben and task["task"] in missions_done:
            continue
        checked = key in st.session_state[state_key]
        if st.checkbox(f"{task['task']} (+{task['xp']} XP)", value=checked, key=key):
            st.session_state[state_key].add(key)
        else:
            st.session_state[state_key].discard(key)

# XP berechnen
def calc_xp():
    xp = 0
    keys = st.session_state[state_key]
    for label, tasklist, is_neben in [
        ("Morgenroutine", tasks.get("Morgenroutine", []), False),
        (f"Wochentags ({weekday})", tasks.get("Wochenplan", {}).get(weekday, []), False),
        ("Abendroutine", tasks.get("Abendroutine", []), False),
        ("Nebenmissionen", tasks.get("Nebenmissionen", []), True),
    ]:
        for i, task in enumerate(tasklist):
            key = f"{label}_{i}_{selected_date}"
            if key in keys and not (is_neben and task["task"] in missions_done):
                xp += task["xp"]
    return xp

# Layout anzeigen
col1, col2, col3, col4 = st.columns([1.2,1.2,1.2,1])
with col1:
    show_tasks("Morgenroutine", tasks.get("Morgenroutine", []))
with col2:
    show_tasks(f"Wochentags ({weekday})", tasks.get("Wochenplan", {}).get(weekday, []))
with col3:
    show_tasks("Abendroutine", tasks.get("Abendroutine", []))
with col4:
    show_tasks("Nebenmissionen", tasks.get("Nebenmissionen", []), is_neben=True)

# XP & Speichern
xp_today = calc_xp()
st.success(f"🔹 XP für {selected_date.strftime('%d.%m.%Y')}: {xp_today}")
if st.button("✅ XP speichern"):
    new_df = logdf[logdf["Datum"] != pd.to_datetime(selected_date)] if not logdf.empty else logdf
    new_df = pd.concat([new_df, pd.DataFrame([{"Datum": selected_date, "XP": xp_today}])], ignore_index=True)
    save_xp_log(new_df)
    save_today_status(xp_today)
    for i, t in enumerate(tasks.get("Nebenmissionen", [])):
        key = f"Nebenmissionen_{i}_{selected_date}"
        if key in st.session_state[state_key]:
            missions_done.add(t["task"])
    save_missions_done(missions_done)
    st.success("✅ Gespeichert und heute_status.json aktualisiert!")

# Wochenübersicht
if not logdf.empty:
    st.markdown("---")
    st.markdown("### 📊 XP-Verlauf (letzte 7 Tage)")
    week = logdf.set_index("Datum").resample("D").sum().reindex(
        pd.date_range(datetime.date.today() - datetime.timedelta(days=6), datetime.date.today()),
        fill_value=0
    )
    st.bar_chart(week["XP"])

# Reset
if st.button("🔁 Nebenmissionen zurücksetzen"):
    missions_done.clear()
    save_missions_done(missions_done)
    st.warning("Nebenmissionen zurückgesetzt.")
