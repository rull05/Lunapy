# This file contains the configuration for the bot

import os
from dotenv import load_dotenv

load_dotenv()

BOT_NAME = os.environ.get("BOT_NAME", "anv")
DIR_COMMANDS = os.environ.get("DIR_COMMANDS", "commands")
BOT_PREFIX = os.environ.get("PREFIX", "!")
DIR_SESSION = os.environ.get("DIR_SESSION", "sessions")
OWNERS_NUMBER = [num.strip() + "@s.whatsapp.net" for num in os.environ.get("OWNERS_NUMBER", "").split(",") if num]

__all__ = ["BOT_NAME", "DIR_COMMANDS", "BOT_PREFIX"]