import os
import discord
from discord.ext import commands, tasks
from datetime import datetime, time
from zoneinfo import ZoneInfo
from investing_scraper import (
    get_investing_calendar,
    get_earnings_calendar,
    posted_events,
    posted_earnings,
    add_posted_event,
    add_posted_earning
)
from ai_utils import extract_macro_event_time, extract_earnings_time

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
CHANNEL_ID_CALENDAR = int(os.getenv("CHANNEL_ID_CALENDAR"))
CHANNEL_ID_EARNINGS = int(os.getenv("CHANNEL_ID_EARNINGS"))

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# 📊 Makrodaten-Interpretation
def interpret_macro_event(event):
    try:
        actual = float(event["actual"].replace("%", "").replace(",", "."))
        forecast = float(event["forecast"].replace("%", "").replace(",", "."))
        if actual > forecast:
            return "🟢 Positiv – Besser als erwartet."
        elif actual < forecast:
            return "🔴 Negativ – Schlechter als erwartet."
        else:
            return "🟡 Neutral – Entspricht den Erwartungen."
    except:
        return "❓ Keine Bewertung möglich."

# 💰 Earnings-Interpretation
def interpret_earnings(event):
    try:
        eps_actual = float(event['eps_actual'].replace(',', '.'))
        eps_est = float(event['eps_estimate'].replace(',', '.'))
        rev_actual = float(event['revenue_actual'].replace(',', '.'))
        rev_est = float(event['revenue_estimate'].replace(',', '.'))

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

# ✅ Startup
@bot.event
async def on_ready():
    print(f"✅ Bot online als {bot.user}")
    daily_summary.start()
    live_updates.start()
    live_earnings.start()
    remind_important_events.start()

# 📅 Tägliche Zusammenfassung
@tasks.loop(time=time(hour=22, minute=0, tzinfo=ZoneInfo("Europe/Berlin")))
async def daily_summary():
    channel = bot.get_channel(CHANNEL_ID_CALENDAR)
    events = get_investing_calendar(for_tomorrow=True)

    if not events:
        await channel.send("📅 Für morgen sind keine Termine geplant.")
        return

    date_str = events[0]['date']
    embed = discord.Embed(
        title=f"📅 Übersicht für den {date_str}",
        description="Mit Uhrzeit und KI-Auswertung",
        color=0x3498db
    )

    germany = [e for e in events if e['country'].lower() == "germany"]
    usa = [e for e in events if e['country'].lower() == "united states"]

    def format_event(e):
        base = f"🕐 {e['time']} – {e['title']}"
        if e.get("actual") and e.get("forecast"):
            return f"{base}\n📊 {interpret_macro_event(e)}"
        return base

    if germany:
        embed.add_field(name="🇩🇪 Deutschland", value="\n".join([format_event(e) for e in germany]), inline=False)
    if usa:
        embed.add_field(name="🇺🇸 USA", value="\n".join([format_event(e) for e in usa]), inline=False)

    await channel.send(embed=embed, delete_after=604800)

# 🔴 Live-Makro-Updates
@tasks.loop(minutes=1)
async def live_updates():
    now = datetime.now(ZoneInfo("Europe/Berlin"))
    if now.hour < 7 or now.hour >= 22 or now.weekday() >= 5:
        return

    channel = bot.get_channel(CHANNEL_ID_CALENDAR)
    events = get_investing_calendar(for_tomorrow=False)

    for event in events:
        identifier = (event['time'], event['title'])
        if event['actual'] and identifier not in posted_events:
            flag = "🇩🇪" if event['country'].lower() == "germany" else "🇺🇸"
            embed = discord.Embed(
                title=f"📢 Neue Veröffentlichung! {flag}",
                description=f"📅 {event['date']} – 🕐 {event['time']} – {event['title']}",
                color=0xe67e22
            )
            embed.add_field(name="Ergebnis", value=f"Ist: {event['actual']} | Erwartet: {event['forecast']} | Vorher: {event['previous']}", inline=False)
            embed.add_field(name="📊 KI-Einschätzung", value=interpret_macro_event(event), inline=False)
            await channel.send(embed=embed, delete_after=604800)
            add_posted_event(identifier)

# 💰 Live-Earnings – EINMAL pro Ticker/Tag
@tasks.loop(minutes=1)
async def live_earnings():
    now = datetime.now(ZoneInfo("Europe/Berlin"))
    if now.hour < 7 or now.hour >= 22 or now.weekday() >= 5:
        return

    channel = bot.get_channel(CHANNEL_ID_EARNINGS)
    events = get_earnings_calendar()

    for event in events:
        identifier = (event['date'], event['ticker'])  # stabil & eindeutig
        if event.get('eps_actual') and identifier not in posted_earnings:
            embed = discord.Embed(
                title=f"💰 Earnings: {event['ticker']}",
                description=f"📅 {event['date']} – 🕐 {event['time']} – {event['company']}",
                color=0x1abc9c
            )
            embed.add_field(name="Ergebnis", value=f"EPS: {event['eps_actual']} vs {event['eps_estimate']}", inline=False)
            embed.add_field(name="Umsatz", value=f"{event['revenue_actual']} vs {event['revenue_estimate']}", inline=False)
            embed.add_field(name="📊 KI-Einschätzung", value=interpret_earnings(event), inline=False)
            await channel.send(embed=embed, delete_after=604800)
            add_posted_earning(identifier)

# ⏰ Erinnerungen vor Events mit hoher Wichtigkeit
@tasks.loop(minutes=1)
async def remind_important_events():
    now = datetime.now(ZoneInfo("Europe/Berlin"))
    events = get_investing_calendar(for_tomorrow=False)

    for event in events:
        if event.get("importance") != "high":
            continue

        try:
            event_time = datetime.strptime(f"{event['date']} {event['time']}", "%d.%m.%Y %H:%M").replace(tzinfo=ZoneInfo("Europe/Berlin"))
        except:
            continue

        diff = (event_time - now).total_seconds()
        identifier = ("reminder", event['time'], event['title'])

        if 240 <= diff <= 360 and identifier not in posted_events:
            channel = bot.get_channel(CHANNEL_ID_CALENDAR)
            msg = f"⏰ **In 5 Minuten:** {event['title']} ({event['country'].title()}) um {event['time']} Uhr!"
            await channel.send(msg, delete_after=604800)
            add_posted_event(identifier)

# 🧹 Cleanup-Befehl: Löscht alle Bot-Nachrichten
async def cleanup_channel(channel):
    def is_bot_message(msg):
        return msg.author == bot.user
    deleted = await channel.purge(limit=500, check=is_bot_message)
    return len(deleted)

@bot.command(name="cleanup")
@commands.has_permissions(administrator=True)
async def cleanup(ctx):
    await ctx.send("🧹 Lösche alte Bot-Nachrichten...", delete_after=5)
    deleted_calendar = await cleanup_channel(bot.get_channel(CHANNEL_ID_CALENDAR))
    deleted_earnings = await cleanup_channel(bot.get_channel(CHANNEL_ID_EARNINGS))
    await ctx.send(f"✅ {deleted_calendar + deleted_earnings} Nachrichten gelöscht.", delete_after=10)

@cleanup.error
async def cleanup_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("❌ Du hast keine Berechtigung für diesen Befehl.", delete_after=10)

# Test-Befehl
@bot.command(name="ping")
async def ping(ctx):
    await ctx.send("🏓 Pong!")

# 🔁 Bot starten
if __name__ == "__main__":
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except:
        pass

    if not DISCORD_TOKEN:
        raise ValueError("❌ DISCORD_TOKEN fehlt!")
    bot.run(DISCORD_TOKEN)
