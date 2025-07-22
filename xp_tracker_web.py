#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
XP‑Tracker Web Edition mit SQLite-Backend

Speichern als xp_tracker_web.py und starten mit:
    streamlit run xp_tracker_web.py
"""
import streamlit as st
import sqlite3
import os
import datetime
import pandas as pd

# —— Konstanten ——
DB_FILE = "xp_tracker.db"
TASKS_FILE = "tasks.json"
IMPORTANT_TASKS = {
    "Zähne putzen (morgens)",
    "Lisdexamphetamin nehmen",
    "Müll rausbringen",
}
REWARDS = [
    {"name": "🚬 Kleine Belohnung", "cost": 30},
    {"name": "🎮 Große Belohnung", "cost": 50},
    {"name": "💨 Bong erlaubt", "cost": 60},
]

# —— DB-Hilfsfunktionen ——
def init_db():
    with sqlite3.connect(DB_FILE) as conn:
        c = conn.cursor()
        c.execute("""
        CREATE TABLE IF NOT EXISTS tasks_done (
            date TEXT,
            task TEXT,
            xp INTEGER,
            PRIMARY KEY(date, task)
        )""")
        c.execute("""
        CREATE TABLE IF NOT EXISTS xp_log (
            date TEXT PRIMARY KEY,
            xp INTEGER
        )""")
        c.execute("""
        CREATE TABLE IF NOT EXISTS reminders (
            date TEXT,
            task TEXT,
            remind_at TEXT,
            PRIMARY KEY(date, task)
        )""")
        conn.commit()

def mark_task_done(date: str, task: str, xp: int):
    with sqlite3.connect(DB_FILE) as conn:
        conn.execute(
            "REPLACE INTO tasks_done(date, task, xp) VALUES (?,?,?)", (date, task, xp)
        )
        conn.commit()

def get_tasks_done(date: str):
    with sqlite3.connect(DB_FILE) as conn:
        rows = conn.execute(
            "SELECT task, xp FROM tasks_done WHERE date = ?", (date,)
        ).fetchall()
    return {task: xp for task, xp in rows}

def log_daily_xp(date: str, xp: int):
    with sqlite3.connect(DB_FILE) as conn:
        conn.execute(
            "REPLACE INTO xp_log(date, xp) VALUES (?,?)", (date, xp)
        )
        conn.commit()

def get_week_xp(end_date: str):
    sd = datetime.datetime.strptime(end_date, "%Y-%m-%d").date()
    start = sd - datetime.timedelta(days=6)
    with sqlite3.connect(DB_FILE) as conn:
        rows = conn.execute(
            "SELECT date, xp FROM xp_log WHERE date BETWEEN ? AND ? ORDER BY date", 
            (start.isoformat(), sd.isoformat())
        ).fetchall()
    data = {d.isoformat():0 for d in [start + datetime.timedelta(days=i) for i in range(7)]}
    for date_str, xp in rows:
        data[date_str] = xp
    return data

# —— Tasks laden ——
def load_tasks():
    import json
    with open(TASKS_FILE, encoding='utf-8') as f:
        return json.load(f)

# —— Streamlit App ———
init_db()
st.set_page_config("XP Tracker 🧠", layout="wide", page_icon="🧠")

st.markdown("""
<style>
  .important-label { color: #ff4b4b; font-weight: bold; display: block; margin-bottom: -4px; }
  .st-app { background: #1a1b1e; }
</style>
""", unsafe_allow_html=True)

st.title("XP‑Tracker 🚀 mit SQLite Backend")
# Seitenleiste für Datum
today = datetime.date.today()
selected_date = st.sidebar.date_input("Für welchen Tag?", today,
                                    min_value=today-datetime.timedelta(days=30),
                                    max_value=today)
date_key = selected_date.isoformat()

# Lade Tasks & erledigte Tasks aus DB
tasks = load_tasks()
done = get_tasks_done(date_key)

# Sitzungshalter initialisieren
if 'done' not in st.session_state:
    st.session_state.done = set(done.keys())

# Task-Rendering & DB-Schreibungen
def render_section(title, items, is_neben=False):
    st.header(title)
    for t in items:
        name, xp = t['task'], t['xp']
        checked = name in st.session_state.done
        label = f"{name} (+{xp} XP)"
        if name in IMPORTANT_TASKS:
            st.markdown(f"<span class='important-label'>❗ {label}</span>", unsafe_allow_html=True)
            cb = st.checkbox("", key=f"cb_{name}", value=checked)
        else:
            cb = st.checkbox(label, key=f"cb_{name}", value=checked)
        if cb and not checked:
            st.session_state.done.add(name)
            mark_task_done(date_key, name, xp)
        if not cb and checked:
            st.session_state.done.remove(name)
            # Optionally delete from DB here

# Abschnitte
render_section("🌅 Morgenroutine", tasks.get("Morgenroutine", []))
weekday = ["Montag","Dienstag","Mittwoch","Donnerstag","Freitag","Samstag","Sonntag"][selected_date.weekday()]
render_section(f"📆 Wochentags-Quests: {weekday}", tasks.get("Wochenplan", {}).get(weekday, []))
render_section("🌙 Abendroutine", tasks.get("Abendroutine", []))
render_section("🕹 Nebenmissionen", tasks.get("Nebenmissionen", []), is_neben=True)

# XP summieren & speichern
xp_today = sum(get_tasks_done(date_key).values())
st.sidebar.markdown(f"## Heutige XP: **{xp_today}**")
if st.sidebar.button("XP loggen"):
    log_daily_xp(date_key, xp_today)
    st.sidebar.success("Tages-XP gespeichert!")

# Wochen-Chart
st.header("📊 XP-Wochenübersicht")
week_data = get_week_xp(date_key)
chart_df = pd.DataFrame({'XP': list(week_data.values())},
                        index=pd.to_datetime(list(week_data.keys())))
st.bar_chart(chart_df, use_container_width=True)

st.caption("Datenbank: xp_tracker.db – Tasks und XP sicher gespeichert.")
