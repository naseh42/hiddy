# config.py
# Description: This file contains the configuration loader and setter for the bot.
import os
import json
import logging
from urllib.parse import urlparse
import requests
from termcolor import colored
import datetime

# --- Constants ---
# Database location
USERS_DB_LOC = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'Database', 'hidyBot.db')

# Backup location
BACKUP_LOC = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'Backup')

# Receipts location
RECEIPT_LOC = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'UserBot', 'Receiptions')

# Logs location
LOG_LOC = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'Logs')

# Support ID (shown in case of errors)
HIDY_BOT_ID = "@HidyBotGroup"

# --- Global Variables ---
# These will be populated by load_config and set_config_variables
ADMINS_ID = []
TELEGRAM_TOKEN = ""
CLIENT_TOKEN = ""
PANEL_URL = ""
LANG = "FA" # Default language
PANEL_ADMIN_ID = "" # This might not be used with the new API structure
API_PATH = "" # This might not be used with the new API structure

# --- Hiddify API Configuration (New for v2.2.0) ---
# These will be populated from the database or user input
HIDDIFY_API_KEY = ""
HIDDIFY_PROXY_PATH = ""
HIDDIFY_BASE_URL = "" # e.g., https://yourdomain.com

# --- Version ---
try:
    from version import __version__
except ImportError:
    __version__ = "Unknown"

# --- Logging Configuration ---
if not os.path.exists(LOG_LOC):
    os.makedirs(LOG_LOC)

# Configure logging to write to a file
logging.basicConfig(
    filename=os.path.join(LOG_LOC, 'config.log'),
    filemode='a',
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# --- Database Manager Import ---
# We need to be careful about circular imports.
# The USERS_DB will be initialized after this config is loaded.
USERS_DB = None

def load_config(db):
    """
    Load configuration from the database.
    This function fetches settings from int_config, str_config, and bool_config tables.
    """
    logger.info("Loading configuration from database...")
    configs = {}

    try:
        # Load integer configs
        int_configs = db.select_int_config()
        if int_configs:
            for config in int_configs:
                configs[config['key']] = config['value']

        # Load string configs
        str_configs = db.select_str_config()
        if str_configs:
            for config in str_configs:
                configs[config['key']] = config['value']

        # Load boolean configs
        bool_configs = db.select_bool_config()
        if bool_configs:
            for config in bool_configs:
                configs[config['key']] = config['value']

        logger.info("Configuration loaded successfully.")
        return configs
    except Exception as e:
        logger.error(f"Error loading configuration from database: {e}")
        return {}

def load_server_url(db):
    """
    Load the Hiddify panel URL from the database.
    With the new API, we might need to load HIDDIFY_BASE_URL, HIDDIFY_PROXY_PATH, and HIDDIFY_API_KEY.
    For backward compatibility, we'll try to extract URL if stored in old format.
    """
    logger.info("Loading server URL from database...")
    try:
        # Try to get the new format configs first
        str_configs = db.select_str_config()
        base_url = None
        proxy_path = None
        api_key = None
        
        if str_configs:
            for config in str_configs:
                if config['key'] == 'hiddify_base_url':
                    base_url = config['value']
                elif config['key'] == 'hiddify_proxy_path':
                    proxy_path = config['value']
                elif config['key'] == 'hiddify_api_key':
                    api_key = config['value']
                # For backward compatibility, check for old 'url' key
                elif config['key'] == 'url' and not base_url:
                    # Try to parse the old URL format
                    old_url = config['value']
                    if old_url:
                        # Remove trailing slash
                        if old_url.endswith('/'):
                            old_url = old_url[:-1]
                        # Remove common suffixes
                        if old_url.endswith('/admin'):
                            old_url = old_url[:-6]
                        elif old_url.endswith('/admin/user'):
                            old_url = old_url[:-11]
                        base_url = old_url
                        proxy_path = "proxy" # Default assumption
                        # API key would need to be set separately

        if base_url:
            logger.info("Server URL loaded successfully (new format).")
            return {
                'base_url': base_url,
                'proxy_path': proxy_path or "proxy",
                'api_key': api_key or ""
            }
        else:
            logger.warning("Server URL not found in new format.")
            return None
    except Exception as e:
        logger.error(f"Error loading server URL from database: {e}")
        return None

def set_config_variables(configs, server_info):
    """
    Set global configuration variables from loaded configs and server URL.
    This function maps database config keys to global variables.
    """
    global ADMINS_ID, TELEGRAM_TOKEN, CLIENT_TOKEN, PANEL_URL, LANG, \
           HIDDIFY_API_KEY, HIDDIFY_PROXY_PATH, HIDDIFY_BASE_URL, PANEL_ADMIN_ID, API_PATH

    logger.info("Setting global configuration variables...")
    
    # Required configurations check
    required_configs = ['owners', 'telegram_token', 'lang']
    missing_configs = [key for key in required_configs if key not in configs]
    
    if missing_configs:
        logger.error(f"Missing required configurations: {missing_configs}")
        raise Exception(f"ConfigError: Missing required configurations: {missing_configs}")

    # Set basic configurations
    try:
        ADMINS_ID = [int(id.strip()) for id in configs['owners'].split(',')]
    except (ValueError, AttributeError):
        logger.error("Invalid format for 'owners' configuration.")
        raise Exception("ConfigError: Invalid format for 'owners' configuration.")
    
    TELEGRAM_TOKEN = configs.get('telegram_token', '')
    LANG = configs.get('lang', 'FA')
    
    # Client token (for user bot)
    CLIENT_TOKEN = configs.get('client_token', '')
    
    # Set Hiddify API configurations
    if server_info:
        HIDDIFY_BASE_URL = server_info.get('base_url', '')
        HIDDIFY_PROXY_PATH = server_info.get('proxy_path', 'proxy')
        HIDDIFY_API_KEY = server_info.get('api_key', '')
        # For backward compatibility
        PANEL_URL = HIDDIFY_BASE_URL
        API_PATH = f"/{HIDDIFY_PROXY_PATH}"
    else:
        # Fallback to old method if server_info is not available
        logger.warning("Server info not available, using old method for PANEL_URL.")
        # This part would need the old logic to extract URL from configs if stored that way
        # For now, we'll leave it empty and let the validation handle it
        PANEL_URL = configs.get('url', '') # Old way
        if PANEL_URL:
            # Process PANEL_URL similar to before
            if PANEL_URL.endswith("/"):
                PANEL_URL = PANEL_URL[:-1]
            if PANEL_URL.endswith("admin"):
                PANEL_URL = PANEL_URL.replace("/admin", "")
            if PANEL_URL.endswith("admin/user"):
                PANEL_URL = PANEL_URL.replace("/admin/user", "")
            # Set new variables based on old PANEL_URL if possible
            HIDDIFY_BASE_URL = PANEL_URL
            HIDDIFY_PROXY_PATH = "proxy" # Default assumption
        else:
            HIDDIFY_BASE_URL = ""
            HIDDIFY_PROXY_PATH = "proxy"
        HIDDIFY_API_KEY = configs.get('hiddify_api_key', '') # If stored separately
    
    # These might not be used with the new API but kept for compatibility
    PANEL_ADMIN_ID = configs.get('panel_admin_id', '')
    
    logger.info("Global configuration variables set successfully.")

def url_validator(url):
    """
    Validate the Hiddify panel URL.
    This function checks if the URL is accessible and valid for Hiddify panel.
    """
    print(colored("Checking URL...", "yellow"))
    
    if not url:
        print(colored("URL is empty!", "red"))
        return False
    
    # Basic URL format validation
    if not (url.startswith("http://") or url.startswith("https://")):
        print(colored("URL must start with http:// or https://", "red"))
        return False
    
    # Remove trailing slash
    if url.endswith("/"):
        url = url[:-1]
    
    # Remove common suffixes for cleaning
    if url.endswith("/admin"):
        url = url.replace("/admin", "")
    if url.endswith("/admin/user"):
        url = url.replace("/admin/user", "")
    
    # Test connection to the base URL
    try:
        # Test the root URL
        request = requests.get(f"{url}/", timeout=10)
    except requests.exceptions.ConnectionError as e:
        print(colored("URL is not valid! Error in connection", "red"))
        print(colored(f"Error: {e}", "red"))
        return False
    except requests.exceptions.Timeout:
        print(colored("URL is not valid! Request timed out", "red"))
        return False
    except Exception as e:
        print(colored("URL is not valid! Unexpected error", "red"))
        print(colored(f"Error: {e}", "red"))
        return False
    
    if request.status_code != 200:
        print(colored("URL is not valid!", "red"))
        print(colored(f"Error: {request.status_code}", "red"))
        return False
    else:
        print(colored("URL is valid!", "green"))
        return url

def bot_token_validator(token):
    """
    Validate the Telegram Bot Token.
    This function checks if the token is valid by calling Telegram's getMe API.
    """
    print(colored("Checking Bot Token...", "yellow"))
    
    if not token:
        print(colored("Bot Token is empty!", "red"))
        return False
    
    try:
        request = requests.get(f"https://api.telegram.org/bot{token}/getMe", timeout=10)
    except requests.exceptions.ConnectionError:
        print(colored("Bot Token is not valid! Error in connection", "red"))
        return False
    except requests.exceptions.Timeout:
        print(colored("Bot Token is not valid! Request timed out", "red"))
        return False
    except Exception as e:
        print(colored("Bot Token is not valid! Unexpected error", "red"))
        print(colored(f"Error: {e}", "red"))
        return False
    
    if request.status_code != 200:
        print(colored("Bot Token is not valid!", "red"))
        return False
    elif request.status_code == 200:
        print(colored("Bot Token is valid!", "green"))
        print(colored("Bot Username:", "green"), "@" + request.json()['result']['username'])
        return True

def set_by_user():
    """
    Get configuration from user input.
    This function prompts the user to enter configuration values.
    """
    print()
    print(colored(
        "Example: 123456789\n"
        "If you have more than one admin, split with comma(,)\n"
        "[get it from @userinfobot]", "yellow"))
    
    while True:
        admin_id = input("[+] Enter Telegram Admin Number IDs: ")
        admin_ids = admin_id.split(',')
        admin_ids = [admin_id.strip() for admin_id in admin_ids]
        if not all(admin_id.isdigit() for admin_id in admin_ids):
            print(colored("Invalid Admin ID(s)!", "red"))
        else:
            break
    
    while True:
        token = input("[+] Enter your Telegram Bot Token: ")
        if bot_token_validator(token):
            break
    
    client_token = input("[+] Enter your Telegram User Bot Token (Optional, press Enter to skip): ")
    
    while True:
        url = input("[+] Enter your Hiddify Panel URL (e.g., https://yourdomain.com): ")
        validated_url = url_validator(url)
        if validated_url:
            url = validated_url
            break
    
    while True:
        lang = input("[+] Enter your language (FA or EN, default is FA): ").upper()
        if lang in ["FA", "EN"]:
            break
        elif lang == "":
            lang = "FA"
            break
        else:
            print(colored("Invalid language!", "red"))
    
    return {
        "admin_ids": ",".join(admin_ids),
        "token": token,
        "client_token": client_token,
        "url": url,
        "lang": lang
    }

def set_config_in_db(db, admin_ids, token, url, lang, client_token=""):
    """
    Save configuration to the database.
    This function stores the configuration values in the appropriate config tables.
    """
    logger.info("Saving configuration to database...")
    
    try:
        # Save integer configs (none in this basic set_by_user, but could be extended)
        # Example: db.edit_int_config("some_int_key", some_int_value)
        
        # Save string configs
        db.edit_str_config("owners", admin_ids)
        db.edit_str_config("telegram_token", token)
        db.edit_str_config("client_token", client_token)
        db.edit_str_config("lang", lang)
        
        # For the URL, we'll save it in the new format if possible
        # Parse the URL to get base and proxy path
        parsed_url = urlparse(url)
        base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
        # Try to determine proxy path, defaulting to 'proxy'
        path_parts = [p for p in parsed_url.path.split('/') if p]
        proxy_path = path_parts[0] if path_parts else "proxy"
        
        db.edit_str_config("hiddify_base_url", base_url)
        db.edit_str_config("hiddify_proxy_path", proxy_path)
        # The API key would need to be entered separately or retrieved from panel
        # db.edit_str_config("hiddify_api_key", api_key) 
        
        # Also save the old format for backward compatibility
        db.edit_str_config("url", url)
        
        # Save boolean configs (none in this basic set_by_user, but could be extended)
        # Example: db.edit_bool_config("some_bool_key", some_bool_value)
        
        logger.info("Configuration saved to database successfully.")
        return True
    except Exception as e:
        logger.error(f"Error saving configuration to database: {e}")
        return False

def print_current_conf(conf, server_info):
    """
    Print the current configuration in a readable format.
    """
    print("\n" + "="*50)
    print(colored("Current Configuration:", "cyan"))
    print("="*50)
    
    # Print basic info
    print(f"{'Version':<25}: {__version__}")
    print(f"{'Language':<25}: {conf.get('lang', 'N/A')}")
    
    # Print Admin IDs
    try:
        admin_ids = [id.strip() for id in conf.get('owners', '').split(',')]
        print(f"{'Admin IDs':<25}: {', '.join(admin_ids)}")
    except:
        print(f"{'Admin IDs':<25}: {conf.get('owners', 'N/A')}")
    
    # Print Bot Tokens
    print(f"{'Admin Bot Token':<25}: {conf.get('telegram_token', 'N/A')[:10]}..." if conf.get('telegram_token') else f"{'Admin Bot Token':<25}: N/A")
    client_token_display = conf.get('client_token', 'N/A')
    if client_token_display and len(client_token_display) > 10:
        client_token_display = client_token_display[:10] + "..."
    print(f"{'User Bot Token':<25}: {client_token_display}")
    
    # Print Hiddify Panel Info
    if server_info:
        print(f"{'Hiddify Base URL':<25}: {server_info.get('base_url', 'N/A')}")
        print(f"{'Hiddify Proxy Path':<25}: {server_info.get('proxy_path', 'N/A')}")
        api_key_display = server_info.get('api_key', 'N/A')
        if api_key_display != 'N/A' and len(api_key_display) > 10:
            api_key_display = api_key_display[:10] + "..."
        print(f"{'Hiddify API Key':<25}: {api_key_display}")
    else:
        print(f"{'Panel URL':<25}: {conf.get('url', 'N/A')}")
    
    print("="*50)

# --- Main Execution ---
if __name__ == "__main__":
    # This block runs when the script is executed directly
    print(colored("Hiddify Telegram Bot Configuration", "green"))
    print(colored(f"Version: {__version__}", "yellow"))
    print(colored("https://github.com/B3H1Z/Hiddify-Telegram-Bot", "blue"))
    print()
    
    try:
        # Import the database manager
        # We do this inside the if block to avoid circular imports during normal operation
        from Database.dbManager import UserDBManager
        USERS_DB = UserDBManager(USERS_DB_LOC)
        
        if not USERS_DB.conn:
            print(colored("Failed to connect to database!", "red"))
            exit(1)
        
        # Load current configuration
        current_configs = load_config(USERS_DB)
        current_server_info = load_server_url(USERS_DB)
        
        # Check if configuration exists
        if current_configs and current_configs.get('owners') and current_configs.get('telegram_token'):
            print(colored("Configuration already exists!", "yellow"))
            print_current_conf(current_configs, current_server_info)
            
            # Ask user if they want to change the configuration
            while True:
                change_conf = input("[+] Do you want to change the configuration? (y/N): ").lower()
                if change_conf in ["y", "yes"]:
                    # Get new configuration from user
                    new_config = set_by_user()
                    # Save new configuration to database
                    if set_config_in_db(
                        USERS_DB, 
                        new_config["admin_ids"], 
                        new_config["token"], 
                        new_config["url"], 
                        new_config["lang"], 
                        new_config["client_token"]
                    ):
                        print(colored("Configuration updated successfully!", "green"))
                        # Reload and print new configuration
                        updated_configs = load_config(USERS_DB)
                        updated_server_info = load_server_url(USERS_DB)
                        print_current_conf(updated_configs, updated_server_info)
                    else:
                        print(colored("Failed to update configuration!", "red"))
                    break
                elif change_conf in ["n", "no", ""]:
                    print(colored("Using existing configuration.", "green"))
                    break
                else:
                    print(colored("Invalid input!", "red"))
        else:
            print(colored("No configuration found. Please configure the bot.", "yellow"))
            # Get configuration from user
            new_config = set_by_user()
            # Save configuration to database
            if set_config_in_db(
                USERS_DB, 
                new_config["admin_ids"], 
                new_config["token"], 
                new_config["url"], 
                new_config["lang"], 
                new_config["client_token"]
            ):
                print(colored("Configuration saved successfully!", "green"))
                # Print the new configuration
                saved_configs = load_config(USERS_DB)
                saved_server_info = load_server_url(USERS_DB)
                print_current_conf(saved_configs, saved_server_info)
            else:
                print(colored("Failed to save configuration!", "red"))
                
    except KeyboardInterrupt:
        print(colored("\n\nOperation cancelled by user.", "yellow"))
    except Exception as e:
        print(colored(f"\nAn error occurred: {e}", "red"))
        logging.error(f"Error in main execution: {e}")
    finally:
        # Close database connection if it was opened
        if 'USERS_DB' in locals() and USERS_DB and USERS_DB.conn:
            USERS_DB.close_connection()
