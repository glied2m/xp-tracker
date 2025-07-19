import streamlit as st
import json, os
import pandas as pd
import datetime

# ——— Konfiguration ———
TASKS_FILE = "tasks.json"
XP_LOG = "xp_log.csv"
MISSIONS_DONE_FILE = "missions_done.json"

# Hier trägst du die Tasks ein, die du als „wichtig“ markieren willst:
IMPORTANT_TASKS = {
    "Zähne putzen (morgens)",
    "Lisdexamphetamin nehmen",
    "Müll rausbringen",
    # …weitere Task-Namen exakt wie in tasks.json
}

# Rewards etc.
REWARDS = [
    {"name":"🚬 Kleine Belohnung","cost":30},
    {"name":"🎮 Große Belohnung","cost":50},
    {"name":"💨 Bong erlaubt","cost":60},
]

# ——— Hilfsfunktionen ———
def load_tasks():
    with open(TASKS_FILE, encoding="utf-8") as f:
        return json.load(f)

def load_xp_log():
    if not os.path.exists(XP_LOG):
        return pd.DataFrame(columns=["Datum","XP"])
    df = pd.read_csv(XP_LOG, sep=";", parse_dates=["Datum"])
    df["Datum"] = pd.to_datetime(df["Datum"]).dt.normalize()
    return df

def save_xp_log(df):
    df.to_csv(XP_LOG, sep=";", index=False)

def load_missions_done():
    if not os.path.exists(MISSIONS_DONE_FILE):
        return set()
    return set(json.load(open(MISSIONS_DONE_FILE, encoding="utf-8")))

def save_missions_done(s):
    json.dump(list(s), open(MISSIONS_DONE_FILE,"w",encoding="utf-8"), ensure_ascii=False)

# ——— UI Setup ———
st.set_page_config("XP Tracker 🧠", layout="wide", page_icon="🧠")
st.markdown("""
    <style>
      body, .stApp {background:#1a1b1e;}
      .block-container {padding:1rem;}
      h1, h2, h3, h4 {color:#e6e6e6;}
      .checkbox-label {color:#e6e6e6;}
      .important {color:#ff4b4b; font-weight:bold;}
    </style>
""", unsafe_allow_html=True)

st.title("XP‑Tracker 🚀")
st.caption("Struktur für Morgen / Abend / Nebenmissionen mit Hervorhebungen & Remindern")

# ——— Daten laden ———
tasks = load_tasks()
logdf = load_xp_log()
missions_done = load_missions_done()

# ——— Datumsauswahl ———
today = datetime.date.today()
selected_date = st.sidebar.date_input("Tag auswählen", today,
                                      min_value=today-datetime.timedelta(days=30),
                                      max_value=today)
weekday = ["Montag","Dienstag","Mittwoch","Donnerstag","Freitag","Samstag","Sonntag"][selected_date.weekday()]

# Checkbox‑State pro Tag
state_key = f"done_{selected_date.isoformat()}"
if state_key not in st.session_state:
    st.session_state[state_key] = set()

# Reminder‑State (Zeitangaben) pro Task+Datum
reminder_key = f"reminders_{selected_date.isoformat()}"
if reminder_key not in st.session_state:
    st.session_state[reminder_key] = {}

# ——— Helper: Anzeige einer Task mit Hervorhebung & Reminder ———
def task_item(task, xp, is_neben=False):
    name = task
    # Wenn Nebenmission und erledigt → skip
    if is_neben and name in missions_done:
        return 0

    # Label mit Farbe, wenn wichtig
    label = name
    if name in IMPORTANT_TASKS:
        label = f"<span class='important'>❗ {name}</span>"
    label_html = f"{label} (+{xp} XP)"

    # Checkbox
    checked = name in st.session_state[state_key]
    if st.checkbox(label_html, key=f"{name}_{selected_date}", value=checked, unsafe_allow_html=True):
        st.session_state[state_key].add(name)
    elif checked and not st.session_state.get(f"{name}_{selected_date}", False):
        st.session_state[state_key].remove(name)

    # Reminder-Input für wichtige Tasks
    if (name in IMPORTANT_TASKS) and (name not in st.session_state[state_key]):
        rem = st.session_state[reminder_key].get(name, None)
        t = st.time_input(f"⏰ Erinnerung für '{name}'", value=rem or datetime.time(hour=8), key=f"tm_{name}")
        st.session_state[reminder_key][name] = t
        # Wenn Zeit erreicht und noch nicht erledigt → Hinweis
        now = datetime.datetime.now().time()
        if now >= t:
            st.warning(f"🕒 Erinnerung: '{name}' jetzt erledigen!", icon="⚠️")

    return xp if name in st.session_state[state_key] else 0

# ——— Tabs für Morgen / Abend / Nebenmissionen ———
tabs = st.tabs(["Morgenroutine", "Abendroutine", "Nebenmissionen"])
# Morgen
with tabs[0]:
    st.header("🌅 Morgenroutine")
    xp_m = 0
    for t in tasks.get("Morgenroutine", []):
        xp_m += task_item(t["task"], t["xp"], is_neben=False)
# Abend
with tabs[1]:
    st.header("🌙 Abendroutine")
    xp_e = 0
    for t in tasks.get("Abendroutine", []):
        xp_e += task_item(t["task"], t["xp"], is_neben=False)
# Nebenmissionen
with tabs[2]:
    st.header("🕹 Nebenmissionen")
    xp_n = 0
    for t in tasks.get("Nebenmissionen", []):
        xp_n += task_item(t["task"], t["xp"], is_neben=True)
    # Nebenmissionen clear button
    if st.button("🔁 Alle Nebenmissionen zurücksetzen"):
        missions_done.clear()
        save_missions_done(missions_done)
        st.experimental_rerun()

# ——— Gesamt‑XP und speichern ———
total_xp = xp_m + xp_e + xp_n
st.sidebar.markdown(f"## Heutige XP: **{total_xp}**")
if st.sidebar.button("💾 Speichern & Loggen"):
    # Log schreiben
    new = logdf[logdf["Datum"]!=pd.to_datetime(selected_date)]
    new = pd.concat([new, pd.DataFrame([{"Datum":selected_date,"XP":total_xp}])])
    save_xp_log(new)
    # Erledigte Nebenmissionen persistieren
    for t in tasks.get("Nebenmissionen", []):
        if t["task"] in st.session_state[state_key]:
            missions_done.add(t["task"])
    save_missions_done(missions_done)
    st.sidebar.success("✓ Gespeichert!")

# ——— Wochenübersicht ———
st.header("📊 XP‑Wochenübersicht")
# prepare week data
all_log = load_xp_log()
all_log = all_log.set_index("Datum").resample("D").sum().reindex(
    pd.date_range(today-datetime.timedelta(days=6), today), fill_value=0
)
st.bar_chart(all_log["XP"])
