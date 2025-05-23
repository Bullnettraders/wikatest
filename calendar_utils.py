import json
import os
from datetime import date, timedelta
from ai_utils import extract_macro_event_time
import discord

POSTED_EVENTS_FILE = "posted_events.json"

# 🔧 Sicherstellen, dass Datei existiert
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
    dummy_data = [
        {
            'title': 'Verbraucherpreisindex (VPI)',
            'country': 'germany',
            'time': '08:00',
            'actual': '6.3%' if backtest else '',
            'forecast': '6.1%',
            'previous': '6.5%',
            'importance': 3
        },
        {
            'title': 'Non-Farm Payrolls',
            'country': 'united states',
            'time': '14:30',
            'actual': '190k' if backtest else '',
            'forecast': '180k',
            'previous': '175k',
            'importance': 2
        },
        {
            'title': 'Test-Event Unwichtig',
            'country': 'germany',
            'time': '11:00',
            'actual': '',
            'forecast': '1.0%',
            'previous': '1.1%',
            'importance': 1  # wird herausgefiltert
        }
    ]

    # 🔍 Nur Events mit 2 oder mehr Sternen
    dummy_data = [e for e in dummy_data if e.get('importance', 1) >= 2]

    target_date = date.today() + timedelta(days=1 if for_tomorrow else 0)
    date_str = target_date.strftime("%d.%m.%Y")

    for event in dummy_data:
        event['date'] = date_str
        if not event['time']:
            event['time'] = extract_macro_event_time(event['title'], country=event['country'])

    return dummy_data

async def post_today_events(bot, channel_id, test_mode=False):
    events = get_investing_calendar()

    def parse_time(e):
        try:
            h, m = map(int, e['time'].split(":"))
            return h * 60 + m
        except:
            return 9999
    events.sort(key=parse_time)

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
