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
        return pd.read_csv(XP_LOG, sep=";", parse_dates=["Datum"])
    except Exception:
        return pd.DataFrame(columns=["Datum","XP"])

def save_xp_log(logdf):
    logdf.to_csv(XP_LOG, sep=";", index=False)

# ---- Streamlit UI ----
st.set_page_config("XP Tracker", page_icon="🧠", layout="centered", initial_sidebar_state="collapsed")
st.markdown("""
    <style>
        body {background: #232323 !important;}
        .stApp {background: #232323;}
        .st-cg {background-color: #1a1b1e;}
    </style>
""", unsafe_allow_html=True)
st.title("🌑 XP-Tracker – Web Edition")
st.info("Bearbeite Aufgaben in `tasks.json`! (Im Editor öffnen und speichern)")

today = datetime.date.today()
tasks = load_tasks()
logdf = load_xp_log()

if "done" not in st.session_state:
    st.session_state.done = set()
if "today_xp" not in st.session_state:
    st.session_state.today_xp = 0
if "rewards_used" not in st.session_state:
    st.session_state.rewards_used = set()

def reset_day():
    if st.session_state.today_xp > 0:
        # Log XP
        new = pd.DataFrame([{"Datum": today, "XP": st.session_state.today_xp}])
        all_log = pd.concat([logdf, new], ignore_index=True)
        save_xp_log(all_log)
    st.session_state.done = set()
    st.session_state.today_xp = 0
    st.session_state.rewards_used = set()

def show_tasks(section, items):
    st.subheader(section)
    for i, t in enumerate(items):
        key = f"{section}_{i}"
        checked = st.checkbox(f"{t['task']} (+{t['xp']} XP)", key=key)
        if checked and key not in st.session_state.done:
            st.session_state.today_xp += t["xp"]
            st.session_state.done.add(key)
        if not checked and key in st.session_state.done:
            st.session_state.today_xp -= t["xp"]
            st.session_state.done.remove(key)

tage_de = ["Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag", "Samstag", "Sonntag"]
weekday_de = tage_de[today.weekday()]
st.header(f"Heutige XP: {st.session_state.today_xp}")
show_tasks("Morgenroutine", tasks.get("Morgenroutine", []))

# Wochentags-Fokusaufgaben anzeigen
wochenplan = tasks.get("Wochenplan", {})
if weekday_de in wochenplan:
    show_tasks(f"Fokusaufgaben am {weekday_de}", wochenplan[weekday_de])

show_tasks("Abendroutine", tasks.get("Abendroutine", []))
show_tasks("Nebenmissionen", tasks.get("Nebenmissionen", []))

st.subheader("💰 Belohnungen")
cols = st.columns(len(REWARDS))
for i, reward in enumerate(REWARDS):
    btn_key = f"reward_{i}"
    enabled = st.session_state.today_xp >= reward["cost"] and btn_key not in st.session_state.rewards_used
    if cols[i].button(f"{reward['name']} ({reward['cost']} XP)", key=btn_key, disabled=not enabled):
        st.session_state.rewards_used.add(btn_key)
        cols[i].success("Eingelöst! 🎉")

colA, colB = st.columns(2)
if colA.button("🔄 Reset Tag"):
    reset_day()
if colB.button("🔄 XP-Log aktualisieren"):
    logdf = load_xp_log()

st.subheader("📊 XP-Wochenübersicht")
all_log = pd.concat([logdf, pd.DataFrame([{"Datum": today, "XP": st.session_state.today_xp}])], ignore_index=True)
all_log = all_log.drop_duplicates(subset=["Datum"], keep="last")
week = all_log[
    all_log["Datum"] >= (today - datetime.timedelta(days=6))
].set_index("Datum").sort_index()
week.index = pd.to_datetime(week.index)
chart = week["XP"].reindex(
    pd.date_range(today - datetime.timedelta(days=6), today), fill_value=0
)
st.bar_chart(chart)

st.caption("Web-App für Felix (ChatGPT Custom 2024)")
