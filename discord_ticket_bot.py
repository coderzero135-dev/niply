"""
Discord Ticket Auto-Responder Bot

This bot detects when a new ticket channel is created and automatically
sends a welcome message, a checker command, and asks for a screenshot.

Setup:
1. Create a bot at https://discord.com/developers/applications
2. Enable "Message Content Intent" and "Server Members Intent" in the Bot tab
3. Copy the bot token and paste it below
4. Invite the bot to your server with permissions:
   - View Channels
   - Send Messages
   - Read Message History
   - Manage Channels (optional)
"""

import discord
from discord.ext import commands
import asyncio

import config

# ==================== CONFIG ====================
BOT_TOKEN = config.BOT_TOKEN
TICKET_CHANNEL_PREFIXES = config.TICKET_CHANNEL_PREFIXES
TICKET_CATEGORY_ID = config.TICKET_CATEGORY_ID
WELCOME_MESSAGE = config.WELCOME_MESSAGE
CHECKER_COMMAND = config.CHECKER_COMMAND
SCREENSHOT_REQUEST = config.SCREENSHOT_REQUEST
MESSAGE_DELAY = config.MESSAGE_DELAY
# =================================================


intents = discord.Intents.default()
intents.guilds = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)


def is_ticket_channel(channel: discord.TextChannel) -> bool:
    """Check if a channel looks like a ticket channel."""
    # Check by category ID
    if TICKET_CATEGORY_ID is not None:
        if channel.category_id == TICKET_CATEGORY_ID:
            return True

    # Check by channel name prefix
    channel_name = channel.name.lower()
    for prefix in TICKET_CHANNEL_PREFIXES:
        if channel_name.startswith(prefix.lower()):
            return True

    return False


@bot.event
async def on_ready():
    print(f"Bot is online as {bot.user}")
    print(f"Connected to {len(bot.guilds)} server(s)")


@bot.event
async def on_guild_channel_create(channel):
    """Triggered when a new channel is created in any server."""
    # Only handle text channels
    if not isinstance(channel, discord.TextChannel):
        return

    # Check if this is a ticket channel
    if not is_ticket_channel(channel):
        return

    # Small delay to make sure channel is fully created
    await asyncio.sleep(1)

    try:
        await channel.send(WELCOME_MESSAGE)
        await asyncio.sleep(MESSAGE_DELAY)

        await channel.send(CHECKER_COMMAND)
        await asyncio.sleep(MESSAGE_DELAY)

        await channel.send(SCREENSHOT_REQUEST)

        print(f"Auto-responded in ticket channel: {channel.name}")
    except discord.Forbidden:
        print(f"Error: Bot does not have permission to send messages in {channel.name}")
    except Exception as e:
        print(f"Error sending message in {channel.name}: {e}")


@bot.command()
async def ping(ctx):
    """Simple test command."""
    await ctx.send("Pong!")


@bot.command()
async def testticket(ctx, channel_name: str = "ticket-test"):
    """Test command: creates a test ticket channel and triggers auto-reply."""
    guild = ctx.guild
    try:
        channel = await guild.create_text_channel(channel_name)
        await ctx.send(f"Created test ticket channel: {channel.mention}")
    except discord.Forbidden:
        await ctx.send("I don't have permission to create channels.")
    except Exception as e:
        await ctx.send(f"Error: {e}")


def main():
    if BOT_TOKEN == "YOUR_BOT_TOKEN_HERE" or not BOT_TOKEN:
        print("ERROR: Please set your BOT_TOKEN in the script first!")
        return

    bot.run(BOT_TOKEN)


if __name__ == "__main__":
    main()
