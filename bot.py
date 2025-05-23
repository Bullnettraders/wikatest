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
    scheduler.add_job(lambda: check_for_actual_updates(bot, CHANNEL_EVENTS), 'interval', minutes=5)
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
