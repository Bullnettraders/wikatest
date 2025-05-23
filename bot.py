import discord
from discord.ext import commands
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from dotenv import load_dotenv
import os
from calendar_utils import get_investing_calendar, post_today_events, check_for_actual_updates

# ENV laden
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
    print(f"✅ Bot eingeloggt als {bot.user}")
    scheduler.add_job(lambda: post_today_events(bot, CHANNEL_EVENTS), 'cron', hour=0, minute=0)
    scheduler.add_job(lambda: check_for_actual_updates(bot, CHANNEL_EVENTS), 'interval', minutes=5)
    scheduler.start()
    try:
        synced = await bot.tree.sync(guild=discord.Object(id=GUILD_ID))
        print(f"🔁 Slash-Commands synchronisiert: {[cmd.name for cmd in synced]}")
    except Exception as e:
        print(f"⚠️ Fehler beim Slash-Command-Sync: {e}")

@bot.tree.command(name="testkalender", description="Test: Vorschau auf alle heutigen Wirtschaftstermine", guild=discord.Object(id=GUILD_ID))
async def testkalender(interaction: discord.Interaction):
    await interaction.response.send_message("🧪 Sende Test-Übersicht...", ephemeral=True)
    await post_today_events(bot, CHANNEL_CONTROL, test_mode=True)

bot.run(TOKEN)
