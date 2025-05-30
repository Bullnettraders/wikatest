import json
import os
from datetime import datetime, timedelta
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

    resp = requests.get(url, headers=headers)
    soup = BeautifulSoup(resp.text, "lxml")
    table = soup.find("table", id="economicCalendarData")
    if not table:
        return []

    events = []
    for row in table.select("tr.js-event-item"):
        # Zeit, Land, Name, Wichtigkeit
        time = row.select_one("td[data-test='event-time']").get_text(strip=True)
        country = row.select_one("td[data-test='event-country']").get_text(strip=True).lower()
        title = row.select_one("td[data-test='event-name']").get_text(strip=True)
        importance = len(row.select(".grayFullBullishIcon"))

        # Forecast, Previous, Actual
        previous = row.select_one("td[data-test='event-previous']").get_text(strip=True) or ""
        forecast = row.select_one("td[data-test='event-forecast']").get_text(strip=True) or ""
        actual   = row.select_one("td[data-test='event-actual']").get_text(strip=True) or ""

        if importance < 2:
            continue

        events.append({
            "date":       target_date.strftime("%d.%m.%Y"),
            "time":       time,
            "country":    country,
            "title":      title,
            "importance": importance,
            "previous":   previous,
            "forecast":   forecast,
            "actual":     actual,
        })
    return events

# --- Discord-Post-Logik bleibt unverändert ---
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
            emoji = flag_map.get(event['country'], '🌍')
            stars = "⭐" * event.get("importance", 1)
            warn = " 🚨" if event.get("importance", 0) == 3 else ""
            name = f"{emoji} {event['time']} – {event['title']} {stars}{warn}"
            value = (
                f"🔹 Prognose: {event['forecast'] or '–'} | "
                f"🔸 Vorher: {event['previous'] or '–'}"
            )
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
            }.get(event['country'], '🌍')

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
