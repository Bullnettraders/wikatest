import os
import discord
from discord.ext import commands, tasks
from datetime import datetime, time, date, timedelta
from zoneinfo import ZoneInfo
from investing_scraper import get_investing_calendar, get_earnings_calendar, posted_events, posted_earnings
from ai_utils import extract_macro_event_time, extract_earnings_time

# Load Tokens from Railway ENV
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
CHANNEL_ID_CALENDAR = int(os.getenv("CHANNEL_ID_CALENDAR"))
CHANNEL_ID_EARNINGS = int(os.getenv("CHANNEL_ID_EARNINGS"))

# Discord Setup
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# AI-Auswertung für Makro-Events
def interpret_macro_event(event):
    try:
        actual_val = float(event['actual'].replace('%', '').replace(',', '.'))
        forecast_val = float(event['forecast'].replace('%', '').replace(',', '.'))
        if actual_val > forecast_val:
            return "🟢 Positiv – Besser als erwartet."
        elif actual_val < forecast_val:
            return "🔴 Negativ – Schlechter als erwartet."
        else:
            return "🟡 Neutral – Entspricht den Erwartungen."
    except:
        return "❓ Keine Bewertung möglich."

# AI-Auswertung für Earnings
def interpret_earnings(event):
    try:
        eps_actual = float(event['eps_actual'].replace(',', '.'))
        eps_est = float(event['eps_estimate'].replace(',', '.'))
        rev_actual = float(event['revenue_actual'].replace(',', '.').replace(' Mrd', ''))
        rev_est = float(event['revenue_estimate'].replace(',', '.').replace(' Mrd', ''))

        eps_diff = eps_actual - eps_est
        rev_diff = rev_actual - rev_est

        if eps_diff > 0 and rev_diff > 0:
            return "🟢 Positiv – Gewinn und Umsatz über den Erwartungen."
        elif eps_diff < 0 and rev_diff < 0:
            return "🔴 Negativ – Gewinn und Umsatz unter den Erwartungen."
        else:
            return "🟡 Gemischt – Ergebnis uneinheitlich."
    except:
        return "❓ Keine Bewertung möglich."

@bot.event
async def on_ready():
    print(f"✅ Bot online als {bot.user}")
    daily_summary.start()
    live_updates.start()
    live_earnings.start()

# 📅 Wirtschaftskalender täglich um 22:00
@tasks.loop(time=time(hour=22, minute=0, tzinfo=ZoneInfo("Europe/Berlin")))
async def daily_summary():
    channel = bot.get_channel(CHANNEL_ID_CALENDAR)
    events = get_investing_calendar(for_tomorrow=True)

    embed = discord.Embed(
        title="📅 Wirtschaftskalender für Morgen",
        description="Mit Veröffentlichungszeit & Datum",
        color=0x3498db
    )

    germany = [e for e in events if e['country'] == "germany"]
    usa = [e for e in events if e['country'] == "united states"]

    def format_event(e):
        return f"📅 {e['date']} – 🕐 {e['time']} – {e['title']}"

    if germany:
        text = "\n".join([format_event(e) for e in germany])
        embed.add_field(name="🇩🇪 Deutschland", value=text, inline=False)
    else:
        embed.add_field(name="🇩🇪 Deutschland", value="🔔 Keine Termine.", inline=False)

    if usa:
        text = "\n".join([format_event(e) for e in usa])
        embed.add_field(name="🇺🇸 USA", value=text, inline=False)
    else:
        embed.add_field(name="🇺🇸 USA", value="🔔 Keine Termine.", inline=False)

    await channel.send(embed=embed)

# 📡 Live-Wirtschaftsveröffentlichungen
@tasks.loop(minutes=1)
async def live_updates():
    now = datetime.now(ZoneInfo("Europe/Berlin"))
    if now.hour < 7 or now.hour >= 22 or now.weekday() >= 5:
        return

    channel = bot.get_channel(CHANNEL_ID_CALENDAR)
    today_events = get_investing_calendar(for_tomorrow=False)

    for event in today_events:
        identifier = (event['time'], event['title'])
        if event['actual'] and identifier not in posted_events:
            flag = "🇩🇪" if event['country'] == "germany" else "🇺🇸" if event['country'] == "united states" else ""
            sentiment = interpret_macro_event(event)

            embed = discord.Embed(
                title=f"📢 Neue Veröffentlichung! {flag}",
                description=f"📅 {event['date']} – 🕐 {event['time']} – {event['title']}",
                color=0xe67e22
            )
            embed.add_field(
                name="Ergebnis",
                value=f"**Ist:** {event['actual']} | **Erwartet:** {event['forecast']} | **Vorher:** {event['previous']}",
                inline=False
            )
            embed.add_field(name="📊 KI-Einschätzung", value=sentiment, inline=False)

            await channel.send(embed=embed)
            posted_events.add(identifier)

# 💰 Live Earnings
@tasks.loop(minutes=1)
async def live_earnings():
    now = datetime.now(ZoneInfo("Europe/Berlin"))
    if now.hour < 7 or now.hour >= 22 or now.weekday() >= 5:
        return

    channel = bot.get_channel(CHANNEL_ID_EARNINGS)
    earnings_today = get_earnings_calendar()

    for event in earnings_today:
        identifier = (event['time'], event['ticker'])
        if identifier not in posted_earnings:
            sentiment = interpret_earnings(event)

            embed = discord.Embed(
                title=f"💰 Earnings Report: {event['ticker']}",
                description=f"📅 {event['date']} – 🕐 {event['time']} – {event['company']}",
                color=0x1abc9c
            )
            embed.add_field(
                name="Ergebnis",
                value=f"**EPS (Ist):** {event['eps_actual']} | **Erwartet:** {event['eps_estimate']}",
                inline=False
            )
            embed.add_field(
                name="Umsatz",
                value=f"**Ist:** {event['revenue_actual']} | **Erwartet:** {event['revenue_estimate']}",
                inline=False
            )
            embed.add_field(
                name="📊 KI-Einschätzung",
                value=sentiment,
                inline=False
            )
            await channel.send(embed=embed)
            posted_earnings.add(identifier)

# 🧪 Optionaler Ping-Befehl
@bot.command(name="ping")
async def ping(ctx):
    await ctx.send("🏓 Pong!")

# Lokale Umgebung laden, wenn vorhanden
if __name__ == "__main__":
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except:
        pass

    if not DISCORD_TOKEN:
        raise ValueError("❌ DISCORD_TOKEN fehlt!")

    bot.run(DISCORD_TOKEN)
