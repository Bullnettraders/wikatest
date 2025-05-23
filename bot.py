import discord
from discord.ext import commands
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from dotenv import load_dotenv
import os
from calendar_utils import get_investing_calendar, post_today_events, check_for_actual_updates

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
    print(f"✅ Bot ist eingeloggt als {bot.user}")
    scheduler.add_job(lambda: post_today_events(bot, CHANNEL_EVENTS), 'cron', hour=0, minute=0)
    scheduler.add_job(lambda: check_for_actual_updates(bot, CHANNEL_EVENTS), 'interval', minutes=5)
    scheduler.start()

@bot.slash_command(guild_ids=[GUILD_ID], name="testkalender", description="Kontrolliere den Wirtschaftskalender")
async def testkalender(ctx):
    events = get_investing_calendar()
    for event in events:
        msg = f"🧪 TEST: {event['title']} ({event['country'].capitalize()})\n" \
              f"Zeit: {event['time']} | Prognose: {event['forecast']} | Vorher: {event['previous']}"
        await ctx.send(msg)

bot.run(TOKEN)
