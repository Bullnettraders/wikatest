import json
import os
from datetime import datetime
import discord
from discord.ext import tasks, commands
import requests
from bs4 import BeautifulSoup

# === Konfiguration ===
TOKEN = "DEIN_DISCORD_BOT_TOKEN"
CHANNEL_EVENTS = 123456789012345678  # Deine Channel-ID
POSTED_EVENTS_FILE = "posted_events.json"
# ======================

# posted_events.json anlegen, falls nicht vorhanden
if not os.path.exists(POSTED_EVENTS_FILE):
    with open(POSTED_EVENTS_FILE, "w") as f:
        json.dump([], f)

def load_posted():
    with open(POSTED_EVENTS_FILE, "r") as f:
        return set(tuple(x) for x in json.load(f))

def save_posted(posted):
    with open(POSTED_EVENTS_FILE, "w") as f:
        json.dump(list(posted), f)

posted_events = load_posted()
def add_posted(ident):
    posted_events.add(ident)
    save_posted(posted_events)

def get_investing_calendar():
    today = datetime.today()
    url = f"https://www.investing.com/economic-calendar/{today.strftime('%Y-%m-%d')}"
    headers = {"User-Agent":"Mozilla/5.0","Accept-Language":"de-DE,en;q=0.9"}
    resp = requests.get(url, headers=headers)
    soup = BeautifulSoup(resp.text, "lxml")
    tbl = soup.find("table", id="economicCalendarData")
    if not tbl:
        return []

    events = []
    for row in tbl.select("tr.js-event-item"):
        imp = len(row.select(".grayFullBullishIcon"))
        if imp < 2:
            continue

        time    = row.select_one("td[data-test='event-time']").get_text(strip=True)
        country = row.select_one("td[data-test='event-country']").get_text(strip=True).lower()
        title   = row.select_one("td[data-test='event-name']").get_text(strip=True)
        prev    = row.select_one("td[data-test='event-previous']").get_text(strip=True) or ""
        fcst    = row.select_one("td[data-test='event-forecast']").get_text(strip=True) or ""
        actual  = row.select_one("td[data-test='event-actual']").get_text(strip=True) or ""

        events.append({
            "id":         (title, today.strftime("%d.%m.%Y"), country),
            "date":       today.strftime("%d.%m.%Y"),
            "time":       time,
            "country":    country,
            "title":      title,
            "importance": imp,
            "previous":   prev,
            "forecast":   fcst,
            "actual":     actual,
        })
    return events

# ===== Bot und Tasks =====
intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"✅ Eingeloggt als {bot.user}")
    if not daily_events.is_running():
        daily_events.start()
    if not actual_updates.is_running():
        actual_updates.start()

@tasks.loop(minutes=5)
async def daily_events():
    """Poste alle 5 Minuten die heutigen Wirtschaftstermine."""
    events = sorted(get_investing_calendar(), key=lambda e: e["time"])
    if not events:
        return

    embed = discord.Embed(
        title=f"📅 Wirtschaftstermine ({events[0]['date']})",
        color=discord.Color.blue()
    )
    flags = {"germany":"🇩🇪","united states":"🇺🇸"}
    for ev in events:
        if ev["id"] in posted_events:
            continue
        emoji = flags.get(ev["country"], "🌍")
        stars = "⭐" * ev["importance"]
        warn  = " 🚨" if ev["importance"] == 3 else ""
        name  = f"{emoji} {ev['time']} – {ev['title']} {stars}{warn}"
        val   = f"🔹 Prognose: {ev['forecast'] or '–'} | 🔸 Vorher: {ev['previous'] or '–'}"
        embed.add_field(name=name, value=val, inline=False)
        add_posted(ev["id"])

    channel = bot.get_channel(CHANNEL_EVENTS)
    await channel.send(embed=embed)

@tasks.loop(seconds=60)
async def actual_updates():
    """Checke jede Minute auf veröffentlichte Actual-Werte."""
    events = get_investing_calendar()
    flags = {"germany":"🇩🇪","united states":"🇺🇸"}
    NEG = ["inflation","arbeitslosen","vpi","verbraucherpreisindex"]
    POS = ["payroll","bip","beschäftigung","wachstum"]

    for ev in events:
        if not ev["actual"] or ev["id"] in posted_events:
            continue

        # Werte parsen
        try:
            a = float(ev["actual"].replace("%","").replace("k",""))
            f = float(ev["forecast"].replace("%","").replace("k",""))
        except:
            label, color = "⚖️ Neutral", discord.Color.orange()
        else:
            t = ev["title"].lower()
            if any(k in t for k in NEG):
                label, color = ("✅ Positiv", discord.Color.green()) if a < f else ("❌ Negativ", discord.Color.red())
            elif any(k in t for k in POS):
                label, color = ("✅ Positiv", discord.Color.green()) if a > f else ("❌ Negativ", discord.Color.red())
            else:
                label, color = "⚖️ Neutral", discord.Color.orange()

        embed = discord.Embed(
            title=f"{label} Zahlen veröffentlicht: {ev['title']} ({flags.get(ev['country'],'🌍')})",
            color=color
        )
        embed.add_field(name="Ergebnis",   value=ev["actual"],   inline=True)
        embed.add_field(name="Prognose",   value=ev["forecast"], inline=True)
        embed.add_field(name="Vorher",     value=ev["previous"], inline=True)

        channel = bot.get_channel(CHANNEL_EVENTS)
        await channel.send(embed=embed)
        add_posted(ev["id"])

# ===== Bot starten =====
bot.run(TOKEN)
