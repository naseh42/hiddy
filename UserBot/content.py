# UserBot/content.py
# Description: This file loads the content (messages, buttons, commands) for the user bot from JSON files.

import os
import json
from config import LANG

# Import the database manager to load settings
# We need to be careful about circular imports.
# We import it inside functions if needed, or ensure the import order is correct.
try:
    from Database.dbManager import USERS_DB
    HAS_DB = True
except ImportError:
    # If database manager is not available, we can't load dynamic settings
    HAS_DB = False
    print("Warning: Database manager not available. Using default settings.")

# --- Constants ---
# Folder containing JSON files
FOLDER = "Json"

# JSON file names
MSG_FILE = "messages.json"
BTN_FILE = "buttons.json"
CMD_FILE = "commands.json"

# --- Helper Function to Load JSON with Error Handling ---
def _load_json_file(file_path, file_description):
    """Helper function to load a JSON file with error handling."""
    try:
        with open(file_path, encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Error: {file_description} file '{os.path.basename(file_path)}' not found in '{os.path.dirname(file_path)}'")
        return {}
    except json.JSONDecodeError as e:
        print(f"Error: Failed to decode JSON in '{os.path.basename(file_path)}': {e}")
        return {}
    except Exception as e:
        print(f"Error: An unexpected error occurred while loading {file_description}: {e}")
        return {}

# --- Load Messages ---
MESSAGES = {}
try:
    MSG_FILE_PATH = os.path.join(os.path.dirname(__file__), FOLDER, MSG_FILE)
    MESSAGES_DATA = _load_json_file(MSG_FILE_PATH, "Messages")
    # Select messages based on the configured language
    MESSAGES = MESSAGES_DATA.get(LANG, MESSAGES_DATA.get("EN", {})) # Fallback to EN if LANG not found
    
    # Override welcome message with dynamic setting if available
    if HAS_DB:
        try:
            # Load string configs from the database
            str_configs = USERS_DB.select_str_config()
            if str_configs:
                # Convert list of dicts to a single dict for easier access
                str_config_dict = {item['key']: item['value'] for item in str_configs}
                # Override welcome message if it exists in the database
                if str_config_dict.get('msg_user_start'):
                    MESSAGES['WELCOME'] = str_config_dict['msg_user_start']
        except Exception as e:
            print(f"Warning: Could not load dynamic welcome message from database: {e}")
            
except Exception as e:
    print(f"Error loading messages: {e}")
    MESSAGES = {}

# --- Load Button Markups ---
KEY_MARKUP = {}
try:
    BTN_FILE_PATH = os.path.join(os.path.dirname(__file__), FOLDER, BTN_FILE)
    KEY_MARKUP_DATA = _load_json_file(BTN_FILE_PATH, "Buttons")
    # Select button markups based on the configured language
    KEY_MARKUP = KEY_MARKUP_DATA.get(LANG, KEY_MARKUP_DATA.get("EN", {})) # Fallback to EN if LANG not found
except Exception as e:
    print(f"Error loading button markups: {e}")
    KEY_MARKUP = {}

# --- Load Bot Commands ---
BOT_COMMANDS = {}
try:
    CMD_FILE_PATH = os.path.join(os.path.dirname(__file__), FOLDER, CMD_FILE)
    BOT_COMMANDS_DATA = _load_json_file(CMD_FILE_PATH, "Commands")
    # Select commands based on the configured language
    BOT_COMMANDS = BOT_COMMANDS_DATA.get(LANG, BOT_COMMANDS_DATA.get("EN", {})) # Fallback to EN if LANG not found
except Exception as e:
    print(f"Error loading bot commands: {e}")
    BOT_COMMANDS = {}

# --- Additional Content for New Features (Optional Placeholders) ---
# If you need to define any additional constants or content specific to the user bot
# that are not in the JSON files, you can do so here.
# For example, messages or keys that are dynamically generated or constants used in logic.

# USER_BOT_SPECIFIC_CONSTANT = "Some Value"
