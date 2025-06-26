import json
import os
from datetime import datetime, time, timezone, timedelta
import discord
from discord.ext import tasks, commands
import requests
from bs4 import BeautifulSoup

# === Konfiguration ===
# Füge hier den Token deines Discord-Bots ein.
TOKEN = "DEIN_DISCORD_BOT_TOKEN" 
# Füge hier die ID des Kanals ein, in dem die Nachrichten gepostet werden sollen.
CHANNEL_ID = 123456789012345678  

# Dateinamen für die Speicherung der bereits geposteten Events
ANNOUNCEMENTS_FILE = "posted_announcements.json"
UPDATES_FILE = "posted_updates.json"
# ======================

# --- Hilfsfunktionen zum Laden und Speichern der Event-IDs ---

def initialize_json_file(filename):
    """Erstellt eine leere JSON-Datei, falls sie nicht existiert."""
    if not os.path.exists(filename):
        with open(filename, "w") as f:
            json.dump([], f)

def load_posted_ids(filename):
    """Lädt die Liste der geposteten Event-IDs aus einer Datei."""
    with open(filename, "r") as f:
        # Wir speichern die IDs als Tupel in einem Set für schnellen Zugriff.
        return set(tuple(item) for item in json.load(f))

def save_posted_ids(filename, ids_set):
    """Speichert die aktualisierte Liste der IDs zurück in die Datei."""
    with open(filename, "w") as f:
        json.dump(list(ids_set), f)

# Initialisierung beim Start
initialize_json_file(ANNOUNCEMENTS_FILE)
initialize_json_file(UPDATES_FILE)

posted_announcements = load_posted_ids(ANNOUNCEMENTS_FILE)
posted_updates = load_posted_ids(UPDATES_FILE)

def add_to_posted(identifier, type='announcement'):
    """Fügt eine Event-ID zur entsprechenden Liste hinzu und speichert sie."""
    if type == 'announcement':
        posted_announcements.add(identifier)
        save_posted_ids(ANNOUNCEMENTS_FILE, posted_announcements)
    elif type == 'update':
        posted_updates.add(identifier)
        save_posted_ids(UPDATES_FILE, posted_updates)

# --- Kernlogik: Abrufen der Wirtschaftsdaten ---

def get_investing_calendar(target_date):
    """
    Ruft Wirtschaftstermine von Investing.com für ein bestimmtes Datum ab.
    Filtert die Ergebnisse direkt bei der Anfrage nur für Deutschland und die USA.
    """
    url = f"https://de.investing.com/economic-calendar/Service/getCalendarFilteredData"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'X-Requested-With': 'XMLHttpRequest',
        'Accept': 'text/html, */*; q=0.01',
        'Referer': 'https://de.investing.com/economic-calendar/'
    }
    
    # Nutzdaten (Payload) für die Anfrage: Hier filtern wir nach Ländern und Wichtigkeit.
    # country[]: 5 (Deutschland), 25 (USA)
    # importance[]: 2 (2 Sterne), 3 (3 Sterne)
    payload = {
        'country[]': ['5', '25'],
        'importance[]': ['2', '3'],
        'dateFrom': target_date.strftime('%Y-%m-%d'),
        'dateTo': target_date.strftime('%Y-%m-%d'),
        'timeZone': '58' # GMT+2 (Berlin/CEST)
    }

    try:
        resp = requests.post(url, headers=headers, data=payload)
        resp.raise_for_status() # Löst einen Fehler bei schlechtem Status-Code aus
        soup = BeautifulSoup(resp.json()['data'], "lxml")
    except requests.exceptions.RequestException as e:
        print(f"Fehler beim Abrufen der Daten: {e}")
        return []

    events = []
    for row in soup.select("tr.js-event-item"):
        importance = len(row.select(".grayFullBullishIcon"))
        time_str = row.select_one("td.time").get_text(strip=True)
        country_element = row.select_one("span.ceFlags")
        country = country_element['title'].lower() if country_element else ""
        title = row.select_one("td.event a").get_text(strip=True)
        actual = row.select_one("td.actual").get_text(strip=True) or "–"
        forecast = row.select_one("td.forecast").get_text(strip=True) or "–"
        previous = row.select_one("td.previous").get_text(strip=True) or "–"
        identifier = (title, target_date.strftime('%d.%m.%Y'), country)

        events.append({
            "id": identifier,
            "date": target_date.strftime("%d.%m.%Y"),
            "time": time_str,
            "country": country,
            "title": title,
            "importance": importance,
            "actual": actual,
            "forecast": forecast,
            "previous": previous,
        })
    return events

# ===== Discord Bot Setup =====
intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    """Wird ausgeführt, wenn der Bot erfolgreich mit Discord verbunden ist."""
    print(f"✅ Bot ist eingeloggt als {bot.user}")
    print("----- Start der Tasks -----")
    post_todays_summary.start()
    check_for_actuals.start()
    post_tomorrows_preview.start()

# --- Geplante Aufgaben (Tasks) ---
BERLIN_TZ = timezone(timedelta(hours=2)) # Zeitzone für Deutschland (CEST)

@tasks.loop(time=time(7, 0, tzinfo=BERLIN_TZ))
async def post_todays_summary():
    """Postet jeden Morgen um 7:00 Uhr eine Zusammenfassung der heutigen Termine."""
    print(f"[{datetime.now()}] Starte tägliche Zusammenfassung...")
    today = datetime.now(BERLIN_TZ).date()
    events = sorted(get_investing_calendar(today), key=lambda e: e["time"])
    
    if not events:
        print("Keine Termine für heute gefunden.")
        return

    channel = bot.get_channel(CHANNEL_ID)
    embed = discord.Embed(
        title=f"📅 Wirtschaftstermine für Heute ({today.strftime('%d.%m.%Y')})",
        color=discord.Color.blue()
    )
    flags = {"germany": "🇩🇪", "united states": "🇺🇸"}
    
    for ev in events:
        if ev["id"] not in posted_announcements:
            emoji = flags.get(ev["country"], "🌍")
            stars = "⭐" * ev["importance"]
            warn = " 🚨" if ev["importance"] == 3 else ""
            name = f"{emoji} {ev['time']} – {ev['title']} {stars}{warn}"
            val = f"Prognose: **{ev['forecast']}** | Vorher: *{ev['previous']}*"
            embed.add_field(name=name, value=val, inline=False)
            add_to_posted(ev['id'], type='announcement')
    
    if embed.fields:
        await channel.send(embed=embed)
        print("Tägliche Zusammenfassung gesendet.")

@tasks.loop(time=time(22, 0, tzinfo=BERLIN_TZ))
async def post_tomorrows_preview():
    """Postet jeden Abend um 22:00 Uhr eine Vorschau auf die Termine des nächsten Tages."""
    print(f"[{datetime.now()}] Starte Vorschau für morgen...")
    tomorrow = datetime.now(BERLIN_TZ).date() + timedelta(days=1)
    events = sorted(get_investing_calendar(tomorrow), key=lambda e: e["time"])
    
    if not events:
        print(f"Keine Termine für morgen ({tomorrow.strftime('%d.%m.%Y')}) gefunden.")
        return

    channel = bot.get_channel(CHANNEL_ID)
    embed = discord.Embed(
        title=f"🗓️ Vorschau: Termine am {tomorrow.strftime('%d.%m.%Y')}",
        color=discord.Color.purple()
    )
    flags = {"germany": "🇩🇪", "united states": "🇺🇸"}

    for ev in events:
        emoji = flags.get(ev["country"], "🌍")
        stars = "⭐" * ev["importance"]
        name = f"{emoji} {ev['time']} – {ev['title']} {stars}"
        val = f"Prognose: **{ev['forecast']}** | Vorher: *{ev['previous']}*"
        embed.add_field(name=name, value=val, inline=False)
    
    if embed.fields:
        await channel.send(embed=embed)
        print("Vorschau für morgen gesendet.")

@tasks.loop(minutes=1)
async def check_for_actuals():
    """Prüft jede Minute, ob neue "Actual"-Werte für heutige Termine veröffentlicht wurden."""
    today = datetime.now(BERLIN_TZ).date()
    events = get_investing_calendar(today)
    
    if not events: return

    channel = bot.get_channel(CHANNEL_ID)
    flags = {"germany": "🇩🇪", "united states": "🇺🇸"}
    NEG_IS_GOOD = ["inflation", "arbeitslosen", "vpi", "verbraucherpreisindex"]
    POS_IS_GOOD = ["payroll", "bip", "beschäftigung", "wachstum", "einkaufsmanagerindex"]

    for ev in events:
        if ev["actual"] != "–" and ev["id"] not in posted_updates:
            label, color = "⚖️ Neutral", discord.Color.orange()
            try:
                a = float(ev["actual"].replace("%", "").replace("K", "e3").replace("M", "e6").replace(",", "."))
                f = float(ev["forecast"].replace("%", "").replace("K", "e3").replace("M", "e6").replace(",", "."))
                title_lower = ev["title"].lower()
                if any(k in title_lower for k in NEG_IS_GOOD):
                    if a < f: label, color = "✅ Positiv", discord.Color.green()
                    elif a > f: label, color = "❌ Negativ", discord.Color.red()
                elif any(k in title_lower for k in POS_IS_GOOD):
                    if a > f: label, color = "✅ Positiv", discord.Color.green()
                    elif a < f: label, color = "❌ Negativ", discord.Color.red()
            except (ValueError, TypeError):
                pass

            emoji = flags.get(ev["country"], "🌍")
            embed = discord.Embed(
                title=f"{label} Ergebnis: {ev['title']} {emoji}",
                description=f"Ein neuer Wert wurde um **{ev['time']}** veröffentlicht.",
                color=color
            )
            embed.add_field(name="Ergebnis", value=f"**{ev['actual']}**", inline=True)
            embed.add_field(name="Prognose", value=ev['forecast'], inline=True)
            embed.add_field(name="Vorher", value=ev['previous'], inline=True)

            await channel.send(embed=embed)
            print(f"Update für '{ev['title']}' gesendet.")
            add_to_posted(ev['id'], type='update')

@post_todays_summary.before_loop
@check_for_actuals.before_loop
@post_tomorrows_preview.before_loop
async def before_tasks():
    await bot.wait_until_ready()

bot.run(TOKEN)
