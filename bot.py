import os
import discord
from discord.ext import commands
from investing_scraper import get_investing_calendar
from ai_utils import extract_macro_event_time

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"✅ Bot online als {bot.user}")

@bot.command()
async def ping(ctx):
    await ctx.send("Pong!")

if __name__ == "__main__":
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except:
        pass

    if not DISCORD_TOKEN:
        raise ValueError("❌ DISCORD_TOKEN nicht gesetzt!")

    bot.run(DISCORD_TOKEN)
