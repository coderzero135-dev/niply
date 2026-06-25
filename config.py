"""
Configuration for the Discord Ticket Auto-Responder Bot.

You can edit these values instead of editing the main bot file.
"""

# Paste your Discord bot token here
BOT_TOKEN = "YOUR_BOT_TOKEN_HERE"

# How to detect ticket channels:
# Channel name prefixes that indicate a ticket channel
TICKET_CHANNEL_PREFIXES = ["ticket-", "t-", "support-"]

# Category ID where ticket channels are created (set to None if not used)
TICKET_CATEGORY_ID = None

# Messages the bot will send
WELCOME_MESSAGE = "hey whats the issue"
CHECKER_COMMAND = "*checker"
SCREENSHOT_REQUEST = "please send ss of checker tool"

# Delay between messages in seconds
MESSAGE_DELAY = 1.0
