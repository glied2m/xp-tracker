#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
XP‑Tracker für ADHS – optimiertes Layout mit Tabs, Farb‑Hervorhebung wichtiger Tasks & Reminder‑Funktion
Speichern als xp_tracker_web.py und starten mit: streamlit run xp_tracker_web.py
"""

import streamlit as st
import json, os
import pandas as pd
import datetime

# ——— Konfiguration ———
TASKS_FILE = "tasks.json"
XP_LOG = "xp_log.csv"
MISSIONS_DONE_FILE = "missions_done.json"

# Trage hier die Task‑Namen ein, die Du als wichtig markieren willst:
IMPORTANT_TASKS = {
    "Zähne putzen (morgens)",
    "Lisdexamphetamin nehmen",
    "Müll rausbringen",
    # …
}

REWARDS = [
    {"name": "🚬 Kleine Belohnung", "cost": 30},
    {"name": "🎮 Große Belohnung", "cost": 50},
    {"name": "💨 Bong erlaubt", "cost": 60},
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

# ——— Streamlit UI Setup ———
st.set_page_config("XP Tracker 🧠", layout="wide", page_icon="🧠")

# CSS für wichtige Labels
st.markdown("""
    <style>
      .important-label {
        color: #ff4b4b;
        font-weight: bold;
        display: block;
        margin-bottom: -8px;
      }
      .block-container { padding: 1rem; background: #1a1b1e; }
      h1, h2, h3, h4 { color: #e6e6e6; }
    </style>
""", unsafe_allow_html=True)

st.title("XP‑Tracker 🚀")
st.caption("Morgen / Abend / Nebenmissionen · Wichtige Tasks & Erinnerungen")

# ——— Daten laden ———
tasks = load_tasks()
logdf = load_xp_log()
missions_done = load_missions_done()

# ——— Datumsauswahl ———
today = datetime.date.today()
selected_date = st.sidebar.date_input(
    "Für welchen Tag?",
    today,
    min_value=today - datetime.timedelta(days=30),
    max_value=today
)
weekday = ["Montag","Dienstag","Mittwoch","Donnerstag","Freitag","Samstag","Sonntag"][selected_date.weekday()]

# State‑Keys
state_key = f"done_{selected_date.isoformat()}"
if state_key not in st.session_state:
    st.session_state[state_key] = set()

reminder_key = f"rem_{selected_date.isoformat()}"
if reminder_key not in st.session_state:
    st.session_state[reminder_key] = {}

# ——— Task‑Renderer mit Hervorhebung & Reminder ———
def task_item(name, xp, is_neben=False):
    # nebenmissionen, die dauerhaft erledigt sind, überspringen
    if is_neben and name in missions_done:
        return 0

    checked = name in st.session_state[state_key]

    # wichtig‑Label
    if name in IMPORTANT_TASKS:
        st.markdown(f"<span class='important-label'>❗ {name} (+{xp} XP)</span>", unsafe_allow_html=True)
        cb = st.checkbox("", key=f"{name}_{selected_date}", value=checked)
    else:
        cb = st.checkbox(f"{name} (+{xp} XP)", key=f"{name}_{selected_date}", value=checked)

    # state update
    if cb and not checked:
        st.session_state[state_key].add(name)
    if not cb and checked:
        st.session_state[state_key].remove(name)

    # reminder‑Input & Hinweis für wichtige tasks
    if name in IMPORTANT_TASKS and name not in st.session_state[state_key]:
        prev = st.session_state[reminder_key].get(name, datetime.time(hour=8))
        t = st.time_input(f"⏰ Erinnerung für '{name}'", value=prev, key=f"t_{name}")
        st.session_state[reminder_key][name] = t
        now = datetime.datetime.now().time()
        if now >= t:
            st.warning(f"🕒 Jetzt: '{name}' erledigen!", icon="⚠️")

    return xp if cb else 0

# ——— Tabs für Morgen / Abend / Nebenmissionen ———
tabs = st.tabs(["Morgenroutine", "Abendroutine", "Nebenmissionen"])
# Morgen
with tabs[0]:
    st.header("🌅 Morgenroutine")
    xp_m = sum(task_item(t["task"], t["xp"]) for t in tasks.get("Morgenroutine", []))
# Abend
with tabs[1]:
    st.header("🌙 Abendroutine")
    xp_e = sum(task_item(t["task"], t["xp"]) for t in tasks.get("Abendroutine", []))
# Nebenmissionen
with tabs[2]:
    st.header("🕹 Nebenmissionen")
    xp_n = sum(task_item(t["task"], t["xp"], is_neben=True) for t in tasks.get("Nebenmissionen", []))
    if st.button("🔁 Nebenmissionen zurücksetzen"):
        missions_done.clear()
        save_missions_done(missions_done)
        st.experimental_rerun()

# ——— XP‑Übersicht & Speichern ———
total_xp = xp_m + xp_e + xp_n
st.sidebar.markdown(f"## Heutige XP: **{total_xp}**")
if st.sidebar.button("💾 Speichern & Loggen"):
    # XP-Log aktualisieren
    new_df = logdf[logdf["Datum"] != pd.to_datetime(selected_date)]
    new_df = pd.concat([new_df, pd.DataFrame([{"Datum": selected_date, "XP": total_xp}])])
    save_xp_log(new_df)
    # Nebenmissionen persistieren
    for t in tasks.get("Nebenmissionen", []):
        if t["task"] in st.session_state[state_key]:
            missions_done.add(t["task"])
    save_missions_done(missions_done)
    st.sidebar.success("✓ Gespeichert!")

# ——— Wochen‑Chart ———
st.header("📊 XP‑Wochenübersicht")
all_log = load_xp_log().set_index("Datum").resample("D").sum().reindex(
    pd.date_range(today - datetime.timedelta(days=6), today), fill_value=0
)
st.bar_chart(all_log["XP"])
