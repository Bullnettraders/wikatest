### bot.py

import discord
from discord.ext import commands
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from dotenv import load_dotenv
import os
from calendar_utils import post_today_events, check_for_actual_updates

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")
GUILD_ID = int(os.getenv("GUILD_ID"))
CHANNEL_EVENTS = int(os.getenv("DISCORD_CHANNEL_ID_EVENTS"))
CHANNEL_CONTROL = int(os.getenv("DISCORD_CHANNEL_ID_CONTROL"))

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

scheduler = AsyncIOScheduler()

@bot.event
async def on_ready():
    print(f"✅ Bot ist online als {bot.user}")
    scheduler.add_job(lambda: post_today_events(bot, CHANNEL_EVENTS), 'cron', hour=0, minute=0)
    scheduler.add_job(lambda: check_for_actual_updates(bot, CHANNEL_EVENTS), 'interval', seconds=60)
    scheduler.start()
    try:
        await bot.tree.sync(guild=discord.Object(id=GUILD_ID))
        print("🔁 Slash-Commands synchronisiert")
    except Exception as e:
        print(f"⚠️ Fehler beim Slash-Sync: {e}")

@bot.tree.command(name="testkalender", description="Tagesübersicht posten (Test)", guild=discord.Object(id=GUILD_ID))
async def testkalender(interaction: discord.Interaction):
    await interaction.response.send_message("🧪 Test: Sende Tagesübersicht...", ephemeral=True)
    await post_today_events(bot, CHANNEL_CONTROL, test_mode=True)

@bot.tree.command(name="testdaten", description="Backtest: poste veröffentlichte Zahlen", guild=discord.Object(id=GUILD_ID))
async def testdaten(interaction: discord.Interaction):
    await interaction.response.send_message("📈 Testdaten werden gesendet...", ephemeral=True)
    await check_for_actual_updates(bot, CHANNEL_CONTROL, backtest=True)

bot.run(TOKEN)


### ai_utils.py

def extract_macro_event_time(title, country):
    return "14:30" if country == "united states" else "08:00"


### requirements.txt

discord.py==2.3.2
apscheduler==3.10.4
python-dotenv==1.0.1
requests
beautifulsoup4
lxml


### posted_events.json

[]


### .env (Beispiel)

DISCORD_TOKEN=dein_bot_token
GUILD_ID=123456789012345678
DISCORD_CHANNEL_ID_EVENTS=123456789012345678
DISCORD_CHANNEL_ID_CONTROL=123456789012345678


### calendar_utils.py

import json
import os
from datetime import datetime, timedelta
from ai_utils import extract_macro_event_time
import discord
import requests
from bs4 import BeautifulSoup

POSTED_EVENTS_FILE = "posted_events.json"

if not os.path.exists(POSTED_EVENTS_FILE):
    with open(POSTED_EVENTS_FILE, "w") as f:
        json.dump([], f)

def load_posted():
    with open(POSTED_EVENTS_FILE, "r") as f:
        return set(tuple(x) for x in json.load(f))

def save_posted(posted_events):
    with open(POSTED_EVENTS_FILE, "w") as f:
        json.dump(list(posted_events), f)

posted_events = load_posted()

def add_posted_event(identifier):
    posted_events.add(identifier)
    save_posted(posted_events)

def get_investing_calendar(for_tomorrow=False, backtest=False):
    target_date = datetime.today() + timedelta(days=1 if for_tomorrow else 0)
    url = f"https://www.investing.com/economic-calendar/{target_date.strftime('%Y-%m-%d')}"
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept-Language": "de-DE,de;q=0.9,en-US;q=0.8,en;q=0.7",
    }

    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, "lxml")

    table = soup.find("table", id="economicCalendarData")
    if not table:
        return []

    rows = table.find_all("tr", class_="js-event-item")

    events = []
    for row in rows:
        country = row.get("data-country", "unknown").lower()
        time_raw = row.get("data-event-datetime")
        time = datetime.fromisoformat(time_raw).strftime("%H:%M") if time_raw else ""
        importance = len(row.select(".grayFullBullishIcon"))
        if importance < 2:
            continue

        event = {
            "country": country,
            "time": time,
            "title": row.get("data-event-name", "").strip(),
            "forecast": row.get("data-event-forecast") or "",
            "previous": row.get("data-event-previous") or "",
            "actual": row.get("data-event-actual") or "",
            "importance": importance,
            "date": target_date.strftime("%d.%m.%Y")
        }
        events.append(event)

    return events

async def post_today_events(bot, channel_id, test_mode=False):
    events = get_investing_calendar()
    events.sort(key=lambda e: e['time'])

    date_str = events[0]['date'] if events else "Heute"
    embed = discord.Embed(
        title=f"📅 Wirtschaftstermine ({date_str})",
        color=discord.Color.blue()
    )

    flag_map = {
        'germany': '🇩🇪',
        'united states': '🇺🇸'
    }

    for event in events:
        identifier = (event['title'], event['date'], event['country'])

        if test_mode or identifier not in posted_events:
            emoji = flag_map.get(event['country'].lower(), '🌍')
            stars = "⭐" * event.get("importance", 1)
            warn = " 🚨" if event.get("importance", 0) == 3 else ""
            name = f"{emoji} {event['time']} – {event['title']} {stars}{warn}"
            value = f"🔹 Prognose: {event['forecast']} | 🔸 Vorher: {event['previous']}"
            embed.add_field(name=name, value=value, inline=False)

            if not test_mode:
                add_posted_event(identifier)

    if embed.fields:
        channel = bot.get_channel(channel_id)
        await channel.send(embed=embed)

async def check_for_actual_updates(bot, channel_id, backtest=False):
    events = get_investing_calendar(backtest=backtest)
    channel = bot.get_channel(channel_id)

    NEGATIVE_GOOD_KEYWORDS = ["inflation", "arbeitslosen", "vpi", "verbraucherpreisindex"]
    POSITIVE_GOOD_KEYWORDS = ["payroll", "bip", "beschäftigung", "wachstum"]

    def interpret_event(event):
        actual = event["actual"]
        forecast = event["forecast"]
        try:
            actual_val = float(actual.replace("%", "").replace("k", "").strip())
            forecast_val = float(forecast.replace("%", "").replace("k", "").strip())
        except:
            return "⚖️ Neutral", discord.Color.orange()

        title = event["title"].lower()
        if any(k in title for k in NEGATIVE_GOOD_KEYWORDS):
            if actual_val < forecast_val:
                return "✅ Positiv", discord.Color.green()
            elif actual_val > forecast_val:
                return "❌ Negativ", discord.Color.red()
        elif any(k in title for k in POSITIVE_GOOD_KEYWORDS):
            if actual_val > forecast_val:
                return "✅ Positiv", discord.Color.green()
            elif actual_val < forecast_val:
                return "❌ Negativ", discord.Color.red()

        return "⚖️ Neutral", discord.Color.orange()

    for event in events:
        identifier = (event['title'], event['date'], event['country'])

        if event['actual'] and (backtest or identifier not in posted_events):
            flag = {
                'germany': '🇩🇪',
                'united states': '🇺🇸'
            }.get(event['country'].lower(), '🌍')

            bewertung, farbe = interpret_event(event)

            embed = discord.Embed(
                title=f"{bewertung} Zahlen veröffentlicht: {event['title']} ({flag})",
                color=farbe
            )
            embed.add_field(name="Ergebnis", value=event['actual'], inline=True)
            embed.add_field(name="Prognose", value=event['forecast'], inline=True)
            embed.add_field(name="Vorher", value=event['previous'], inline=True)

            await channel.send(embed=embed)
            if not backtest:
                add_posted_event(identifier)
