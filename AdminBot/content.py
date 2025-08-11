# AdminBot/content.py
# Description: This file loads the content (messages, buttons, commands) for the admin bot from JSON files.

import os
import json
from config import LANG

# --- Constants ---
# Folder containing JSON files
FOLDER = "Json"

# JSON file names
MSG_FILE = "messages.json"
BTN_FILE = "buttons.json"
CMD_FILE = "commands.json"

# --- Load Messages ---
try:
    with open(os.path.join(os.path.dirname(__file__), FOLDER, MSG_FILE), encoding='utf-8') as f:
        MESSAGES = json.load(f)
    # Select messages based on the configured language
    MESSAGES = MESSAGES.get(LANG, MESSAGES.get("EN", {})) # Fallback to EN if LANG not found
except FileNotFoundError:
    print(f"Error: Messages file '{MSG_FILE}' not found in '{os.path.join(os.path.dirname(__file__), FOLDER)}'")
    MESSAGES = {}
except json.JSONDecodeError as e:
    print(f"Error: Failed to decode JSON in '{MSG_FILE}': {e}")
    MESSAGES = {}
except Exception as e:
    print(f"Error: An unexpected error occurred while loading messages: {e}")
    MESSAGES = {}

# --- Load Button Markups ---
try:
    with open(os.path.join(os.path.dirname(__file__), FOLDER, BTN_FILE), encoding='utf-8') as f:
        KEY_MARKUP = json.load(f)
    # Select button markups based on the configured language
    KEY_MARKUP = KEY_MARKUP.get(LANG, KEY_MARKUP.get("EN", {})) # Fallback to EN if LANG not found
except FileNotFoundError:
    print(f"Error: Buttons file '{BTN_FILE}' not found in '{os.path.join(os.path.dirname(__file__), FOLDER)}'")
    KEY_MARKUP = {}
except json.JSONDecodeError as e:
    print(f"Error: Failed to decode JSON in '{BTN_FILE}': {e}")
    KEY_MARKUP = {}
except Exception as e:
    print(f"Error: An unexpected error occurred while loading buttons: {e}")
    KEY_MARKUP = {}

# --- Load Bot Commands ---
try:
    with open(os.path.join(os.path.dirname(__file__), FOLDER, CMD_FILE), encoding='utf-8') as f:
        BOT_COMMANDS = json.load(f)
    # Select commands based on the configured language
    BOT_COMMANDS = BOT_COMMANDS.get(LANG, BOT_COMMANDS.get("EN", {})) # Fallback to EN if LANG not found
except FileNotFoundError:
    print(f"Error: Commands file '{CMD_FILE}' not found in '{os.path.join(os.path.dirname(__file__), FOLDER)}'")
    BOT_COMMANDS = {}
except json.JSONDecodeError as e:
    print(f"Error: Failed to decode JSON in '{CMD_FILE}': {e}")
    BOT_COMMANDS = {}
except Exception as e:
    print(f"Error: An unexpected error occurred while loading commands: {e}")
    BOT_COMMANDS = {}

# --- Additional Content for New Features (Optional Placeholders) ---
# If you need to define any additional constants or content specific to the admin bot
# that are not in the JSON files, you can do so here.
# For example, messages or keys that are dynamically generated or constants used in logic.

# ADMIN_BOT_SPECIFIC_CONSTANT = "Some Value"
