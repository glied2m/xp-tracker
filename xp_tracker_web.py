import streamlit as st
import json
import pandas as pd
import datetime
import os
from github import Github
from fastapi import FastAPI, Request
import uvicorn
import threading



# --- Datei-Pfade ---
TASKS_FILE = "xp_tasks.json"
XP_LOG_JSON = "xp_log.json"
MISSIONS_DONE_FILE = "missions_done.json"
STATUS_FILE = "today_status.json"
DAILY_LOG_FILE = "daily_log.json"

# --- GitHub Upload-Konfiguration ---
GITHUB_TOKEN = st.secrets["github_token"]  # In Streamlit Secrets speichern
GITHUB_REPO = "glied2m/xp-tracker"

# --- Belohnungen ---
REWARDS = [
    {"name": "🚬 Kleine Belohnung", "cost": 30},
    {"name": "🎮 Große Belohnung", "cost": 50},
    {"name": "💨 Bong erlaubt", "cost": 60}
]

# --- Datei-Funktionen ---
def load_tasks():
    if not os.path.exists(TASKS_FILE):
        return {}
    with open(TASKS_FILE, encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return {}

def save_tasks(data):
    with open(TASKS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    save_file_and_upload(TASKS_FILE)

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

def save_file_and_upload(file_path):
    g = Github(GITHUB_TOKEN)
    repo = g.get_repo(GITHUB_REPO)
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()
    try:
        contents = repo.get_contents(file_path)
        repo.update_file(contents.path, f"Update {file_path}", content, contents.sha)
    except:
        repo.create_file(file_path, f"Create {file_path}", content)

def save_xp_log(df):
    try:
        df = df[["Datum", "XP"]].copy()
        df["Datum"] = df["Datum"].astype(str)
        with open(XP_LOG_JSON, "w", encoding="utf-8") as f:
            json.dump(df.to_dict(orient="records"), f, ensure_ascii=False, indent=2)
        save_file_and_upload(XP_LOG_JSON)
    except Exception as e:
        st.error(f"Fehler beim Speichern der XP: {e}")

def load_missions_done():
    if not os.path.exists(MISSIONS_DONE_FILE): return set()
    with open(MISSIONS_DONE_FILE, encoding="utf-8") as f:
        try:
            return set(json.load(f))
        except json.JSONDecodeError:
            return set()

def save_missions_done(done):
    with open(MISSIONS_DONE_FILE, "w", encoding="utf-8") as f:
        json.dump(list(done), f, ensure_ascii=False)
    save_file_and_upload(MISSIONS_DONE_FILE)

def save_status_json(date, xp):
    status = {
        "date": date.isoformat(),
        "xp": xp
    }
    with open(STATUS_FILE, "w", encoding="utf-8") as f:
        json.dump(status, f, ensure_ascii=False, indent=2)
    save_file_and_upload(STATUS_FILE)

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
                all_logs = []
    all_logs = [entry for entry in all_logs if entry.get("date") != date.isoformat()]
    all_logs.append(log_entry)
    with open(DAILY_LOG_FILE, "w", encoding="utf-8") as f:
        json.dump(all_logs, f, ensure_ascii=False, indent=2)
    save_file_and_upload(DAILY_LOG_FILE)

# --- Start Streamlit App ---
st.set_page_config("XP Tracker", page_icon="🧐", layout="wide")
st.title(" XP-Tracker ")
st.caption("Web-App für Felix | API + XP-Statistik")

tasks = load_tasks()
logdf = load_xp_log()
missions_done = load_missions_done()

# --- Auswahl Tag ---
tage_de = ["Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag", "Samstag", "Sonntag"]
selected_date = st.date_input("Für welchen Tag Aufgaben & XP bearbeiten?", value=datetime.date.today())
weekday_de = tage_de[selected_date.weekday()]
key_day = f"done_{selected_date.isoformat()}"

if "daily_state" not in st.session_state:
    st.session_state.daily_state = {}
if key_day not in st.session_state.daily_state:
    st.session_state.daily_state[key_day] = set()

# --- Aufgabenanzeige ---
def show_tasks(section, items, is_neben=False):
    st.markdown(f"<b>{section}</b>", unsafe_allow_html=True)
    for i, t in enumerate(items):
        if is_neben and t['task'] in missions_done:
            continue
        key = f"{section}_{i}_{selected_date}"
        checked = key in st.session_state.daily_state[key_day]
        box = st.checkbox(f"{t['task']} (+{t['xp']} XP)", key=key, value=checked)
        if box and not checked:
            st.session_state.daily_state[key_day].add(key)
        elif not box and checked:
            st.session_state.daily_state[key_day].remove(key)

# --- XP berechnen ---
def calc_xp(date):
    xp = 0
    keys = st.session_state.daily_state.get(f"done_{date.isoformat()}", set())
    for section, items, is_neben in [
        ("Morgenroutine", tasks.get("Morgenroutine", []), False),
        (f"Wochenplan {weekday_de}", tasks.get("Wochenplan", {}).get(weekday_de, []), False),
        ("Abendroutine", tasks.get("Abendroutine", []), False),
        ("Nebenmissionen", tasks.get("Nebenmissionen", []), True)
    ]:
        for i, t in enumerate(items):
            key = f"{section}_{i}_{date}"
            if key in keys:
                xp += t['xp']
    return xp

# --- Layout mit Aufgaben ---
col1, col2, col3, col4, col5 = st.columns([1,1,1,1,1.5])
with col1:
    show_tasks("Morgenroutine", tasks.get("Morgenroutine", []))
with col2:
    show_tasks(f"Wochenplan {weekday_de}", tasks.get("Wochenplan", {}).get(weekday_de, []))
with col3:
    show_tasks("Abendroutine", tasks.get("Abendroutine", []))
with col4:
    show_tasks("Nebenmissionen", tasks.get("Nebenmissionen", []), is_neben=True)
with col5:
    xp_today = calc_xp(selected_date)
    st.markdown(f"**XP heute:** {xp_today}")
    for reward in REWARDS:
        if st.button(f"{reward['name']} ({reward['cost']} XP)", disabled=(xp_today < reward['cost'])):
            st.success("Belohnung eingelöst!")
    if st.button("🔄 Speichern"):
        logdf_new = logdf[logdf["Datum"] != pd.to_datetime(selected_date)] if not logdf.empty else logdf
        logdf_new = pd.concat([logdf_new, pd.DataFrame([{"Datum": selected_date, "XP": xp_today}])], ignore_index=True)
        logdf_new["Datum"] = pd.to_datetime(logdf_new["Datum"], errors="coerce").dt.normalize()
        logdf_new = logdf_new.dropna(subset=["Datum"]).drop_duplicates(subset=["Datum"], keep="last")
        save_xp_log(logdf_new)
        save_status_json(selected_date, xp_today)
        save_daily_log(selected_date, st.session_state.daily_state[key_day])
        for i, t in enumerate(tasks.get("Nebenmissionen", [])):
            key = f"Nebenmissionen_{i}_{selected_date}"
            if key in st.session_state.daily_state[key_day]:
                missions_done.add(t['task'])
        save_missions_done(missions_done)
        st.success(f"XP für {selected_date:%d.%m.%Y} gespeichert!")

# --- XP-Tabelle ---
all_log = pd.concat([logdf, pd.DataFrame([{"Datum": selected_date, "XP": xp_today}])], ignore_index=True)
all_log["Datum"] = pd.to_datetime(all_log["Datum"], errors="coerce").dt.normalize()
all_log = all_log.dropna(subset=["Datum"])
all_log = all_log.groupby("Datum").sum().sort_index()

last7 = all_log[all_log.index >= datetime.date.today() - datetime.timedelta(days=6)]
monat = all_log[all_log.index >= datetime.date.today().replace(day=1)]
gesamt = all_log

st.markdown("### XP-Tabelle")
st.dataframe(last7.reset_index(), use_container_width=True)
st.markdown(f"XP Ø letzte 7 Tage: **{last7['XP'].mean():.2f}**, Monat: **{monat['XP'].sum()}**, Gesamt: **{gesamt['XP'].sum()}**")

# --- Reset ---
if st.button("🔁 Nebenmissionen zurücksetzen"):
    missions_done.clear()
    save_missions_done(missions_done)
    st.success("Alle Nebenmissionen wurden zurückgesetzt.")

# --- Mini-API für GPT ---
app = FastAPI()

@app.post("/update_task")
async def update_task(req: Request):
    data = await req.json()
    tasks = load_tasks()
    section = data.get("section")
    new_task = data.get("task")
    xp = data.get("xp", 1)
    if section in tasks:
        tasks[section].append({"task": new_task, "xp": xp})
    else:
        tasks[section] = [{"task": new_task, "xp": xp}]
    save_tasks(tasks)
    return {"status": "ok", "message": f"Task hinzugefügt in {section}"}

def run_api():
    uvicorn.run(app, host="0.0.0.0", port=8000)

threading.Thread(target=run_api).start()
