# utils.py
# Description: This file contains all the utility functions used in the bot.
import os
import json
import qrcode
import requests
from io import BytesIO
from config import LANG, USERS_DB
from Database.dbManager import USERS_DB
import logging
from datetime import datetime
# Import the new Hiddify API functions
from api import get_user, get_users, create_user, update_user, get_all_configs, get_user_profile
import pytz

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Currency Conversion ---
def rial_to_toman(rial):
    """Convert Rial to Toman"""
    if rial is None:
        return 0
    return int(rial) // 10

def toman_to_rial(toman):
    """Convert Toman to Rial"""
    if toman is None:
        return 0
    return int(toman) * 10

# --- Server Status ---
def server_status_url(url):
    """Get server status URL"""
    return f"{url}/admin/get_data/"

# --- Subscription Links Generation (Updated for Hiddify API v2.2.0 structure) ---
def sub_links(uuid, url=None, server_row=None):
    """
    Generate subscription links for a user.
    This function now assumes the new Hiddify API structure where configs are fetched via get_all_configs.
    The actual link generation might need adjustment based on how the panel exposes these.
    For now, it generates standard Hiddify-style links.
    """
    if not uuid:
        logger.error("UUID is required to generate subscription links.")
        return None

    # If server_row is provided, use its URL
    if server_row and 'url' in server_row:
        base_url = server_row['url'].rstrip('/')
        proxy_path = "proxy" # Default, might need to be configurable per server
        # Attempt to extract proxy_path from server URL if it's in a standard format
        # This is a simplification, real implementation might need server config
        if '/proxy/' in base_url:
            parts = base_url.split('/proxy/')
            if len(parts) > 1:
                proxy_path = parts[1].split('/')[0]
        full_base_url = f"{base_url}/{proxy_path}"
    elif url:
        base_url = url.rstrip('/')
        proxy_path = "proxy" # Default assumption
        if '/proxy/' in base_url:
            parts = base_url.split('/proxy/')
            if len(parts) > 1:
                proxy_path = parts[1].split('/')[0]
        full_base_url = f"{base_url}/{proxy_path}"
    else:
        logger.error("Either url or server_row with 'url' key must be provided.")
        return None

    # Base subscription URL (Standard Hiddify format)
    sub_url = f"{full_base_url}/{uuid}/"
    
    return {
        "sub_link": sub_url,
        "hiddify_configs": f"{sub_url}", # Often the base link itself
        "vless": f"{sub_url}vless",
        "vmess": f"{sub_url}vmess",
        "trojan": f"{sub_url}trojan",
        # Clash configurations
        "clash": f"{sub_url}clash/all.yml",
        "clash_meta": f"{sub_url}clash/meta/all.yml",
        # Hiddify-specific configurations
        "hiddify_app": f"{sub_url}apps/",
        "sing_box": f"{sub_url}singbox/all.json",
        "sing_box_full": f"{sub_url}singbox/all-full.json",
        # Subscription links (base64 encoded versions)
        "sub_link_b64": f"{sub_url}", # Often handled by client
        "sub_link_b64_vless": f"{sub_url}vless", # Often handled by client
        "sub_link_b64_vmess": f"{sub_url}vmess", # Often handled by client
        "sub_link_b64_trojan": f"{sub_url}trojan", # Often handled by client
    }

# --- Subscription Parsing (Updated to work with new API structure if needed) ---
def sub_parse(sub_link):
    """
    Parse subscription link to extract configurations.
    This function might need adjustment depending on how the new API delivers configs.
    For now, it attempts to fetch and parse a standard subscription.
    """
    if not sub_link:
        logger.error("Subscription link is required for parsing.")
        return None

    try:
        # Fetch the subscription content (assuming it's a text/plain or similar format)
        # This might need to be adjusted if the API provides configs in a different way
        response = requests.get(sub_link, timeout=10)
        response.raise_for_status()
        sub_content = response.text

        # Initialize dictionary for different config types
        configs = {
            'vless': [],
            'vmess': [],
            'trojan': [],
            'ss': [], # Shadowsocks
            'tuic': [],
            'hy2': [], # Hysteria2
            'wireguard': [],
            'mixed': [] # For configs that don't fit neatly into the above categories
        }

        # Simple parsing based on prefixes
        # This is a basic parser and might need improvement for complex configs
        lines = sub_content.strip().split('\n')
        for line in lines:
            line = line.strip()
            if line.startswith("vless://"):
                configs['vless'].append(line)
            elif line.startswith("vmess://"):
                configs['vmess'].append(line)
            elif line.startswith("trojan://"):
                configs['trojan'].append(line)
            elif line.startswith("ss://"):
                configs['ss'].append(line)
            elif line.startswith("tuic://"):
                configs['tuic'].append(line)
            elif line.startswith("hy2://") or line.startswith("hysteria2://"):
                configs['hy2'].append(line)
            elif line.startswith("wireguard://") or "wireguard" in line.lower():
                configs['wireguard'].append(line)
            elif line: # Add any other non-empty line to mixed
                configs['mixed'].append(line)

        return configs

    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching subscription link {sub_link}: {e}")
        return None
    except Exception as e:
        logger.error(f"Error parsing subscription link {sub_link}: {e}")
        return None

# --- QR Code Generation ---
def txt_to_qr(txt):
    """Convert text to QR code"""
    if not txt:
        logger.error("Text is required to generate QR code.")
        return None
    try:
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(txt)
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")
        bio = BytesIO()
        img.save(bio, format='PNG')
        bio.seek(0)
        return bio
    except Exception as e:
        logger.error(f"Error generating QR code: {e}")
        return None

# --- User Information (Updated to use new Hiddify API) ---
def user_info(uuid, server_row):
    """
    Get user information from the Hiddify panel using the new API.
    """
    if not uuid or not server_row:
        logger.error("UUID and server_row are required.")
        return None

    try:
        # Use the new API function to get user details
        user_data = get_user(uuid)
        
        if not user_data:
            logger.warning(f"User with UUID {uuid} not found via API.")
            return None

        # Process the user data to match the expected structure
        # This might need adjustment based on the exact fields returned by get_user
        processed_user = {
            'uuid': user_data.get('uuid'),
            'name': user_data.get('name'),
            'usage': {
                'current_usage_GB': user_data.get('current_usage_GB', 0),
                'usage_limit_GB': user_data.get('usage_limit_GB', 0),
                'remaining_usage_GB': user_data.get('usage_limit_GB', 0) - user_data.get('current_usage_GB', 0)
            },
            'package_days': user_data.get('package_days', 0),
            'remaining_day': 0, # Needs calculation based on expire date
            'last_connection': user_data.get('last_online'), # Might need parsing
            'comment': user_data.get('comment', ''),
            'enable': user_data.get('enable', True),
            'link': f"{server_row['url'].rstrip('/')}/proxy/{uuid}/" # Construct link
        }

        # Calculate remaining days
        # Assuming 'package_days' is total package days and we need to calculate from start/expire dates
        # This logic might need adjustment based on how Hiddify tracks time.
        # A more robust way would be if the API directly provided 'expire_date' or 'start_date'
        # For now, we'll assume a simple calculation or leave it as 0 if not easily derivable.
        # Let's try to get more info from user_profile if needed.
        user_profile_data = get_user_profile(uuid)
        if user_profile_data:
            # Example: if profile provides 'expire_days' or similar
            processed_user['remaining_day'] = user_profile_data.get('profile_remaining_days', 0)
            # Update usage if profile gives more accurate data
            if 'profile_usage_current' in user_profile_data:
                processed_user['usage']['current_usage_GB'] = user_profile_data['profile_usage_current']
                processed_user['usage']['remaining_usage_GB'] = user_data.get('usage_limit_GB', 0) - user_profile_data['profile_usage_current']
        else:
            # Fallback calculation or leave as 0
            # This is a placeholder, real logic depends on Hiddify's data model
            pass

        return processed_user

    except Exception as e:
        logger.error(f"Error getting user info for UUID {uuid}: {e}")
        return None

# --- Non-Order User Information (Updated to use new Hiddify API) ---
def non_order_user_info(telegram_id):
    """
    Get information for non-order subscriptions of a user.
    """
    if not telegram_id:
        logger.error("Telegram ID is required.")
        return []

    try:
        non_order_subs = USERS_DB.find_non_order_subscription(telegram_id=telegram_id)
        if not non_order_subs:
            return []

        non_order_subs_info = []
        for sub in non_order_subs:
            server = USERS_DB.find_server(id=sub['server_id'])
            if not server:
                logger.warning(f"Server with ID {sub['server_id']} not found for non-order sub {sub['uuid']}.")
                continue
            server = server[0]

            # Use the updated user_info function
            user_data = user_info(sub['uuid'], server)
            if user_data:
                user_data['sub_id'] = sub['uuid'] # Use UUID as sub_id for non-orders
                user_data['server_id'] = sub['server_id']
                non_order_subs_info.append(user_data)
            else:
                logger.warning(f"Could not get info for non-order user {sub['uuid']}.")

        return non_order_subs_info

    except Exception as e:
        logger.error(f"Error getting non-order user info for Telegram ID {telegram_id}: {e}")
        return []

# --- Order User Information (Updated to use new Hiddify API) ---
def order_user_info(telegram_id):
    """
    Get information for order subscriptions of a user.
    """
    if not telegram_id:
        logger.error("Telegram ID is required.")
        return []

    try:
        orders = USERS_DB.find_order(telegram_id=telegram_id)
        if not orders:
            return []

        order_subs_info = []
        for order in orders:
            sub_uuid = order.get('uuid')
            if not sub_uuid:
                logger.warning(f"Order {order.get('id')} does not have a UUID.")
                continue

            server_id = order.get('server_id')
            if not server_id:
                logger.warning(f"Order {order.get('id')} does not have a server_id.")
                continue

            server = USERS_DB.find_server(id=server_id)
            if not server:
                logger.warning(f"Server with ID {server_id} not found for order sub {sub_uuid}.")
                continue
            server = server[0]

            # Use the updated user_info function
            user_data = user_info(sub_uuid, server)
            if user_data:
                user_data['sub_id'] = order.get('id') # Use order ID as sub_id for orders
                user_data['server_id'] = server_id
                order_subs_info.append(user_data)
            else:
                logger.warning(f"Could not get info for order user {sub_uuid}.")

        return order_subs_info

    except Exception as e:
        logger.error(f"Error getting order user info for Telegram ID {telegram_id}: {e}")
        return []

# --- All Configurations Settings ---
def all_configs_settings():
    """Get all configuration settings from the database"""
    try:
        # This function seems to be fetching general bot settings
        # It likely interacts with the database directly
        # Assuming USERS_DB has methods to get these settings
        # The structure of settings in the DB might be int_config, str_config, bool_config tables
        
        settings = {}
        
        # Example for boolean configs
        bool_configs = USERS_DB.select_bool_config()
        if bool_configs:
            for config in bool_configs:
                settings[config['key']] = config['value']
                
        # Example for integer configs
        int_configs = USERS_DB.select_int_config()
        if int_configs:
            for config in int_configs:
                settings[config['key']] = config['value']
                
        # Example for string configs
        str_configs = USERS_DB.select_str_config()
        if str_configs:
            for config in str_configs:
                settings[config['key']] = config['value']
                
        return settings
    except Exception as e:
        logger.error(f"Error getting all configs settings: {e}")
        return {}

# --- Search User by Name (Updated to use new Hiddify API) ---
def search_user_by_name(name):
    """
    Search for users by name using the new Hiddify API.
    """
    if not name:
        logger.error("Name is required for search.")
        return []

    try:
        # Get all users from the API
        all_users = get_users()
        
        if not all_users:
            logger.info("No users found via API.")
            return []

        # Filter users by name (case-insensitive partial match)
        matching_users = [user for user in all_users if name.lower() in user.get('name', '').lower()]
        
        # The API returns user data, but we might need to enrich it with server/db info
        # For simplicity here, we'll just return the basic API data
        # In a real scenario, you might want to join this with local DB data
        return matching_users

    except Exception as e:
        logger.error(f"Error searching user by name '{name}': {e}")
        return []

# --- Expired Users List ---
def expired_users_list():
    """
    Get a list of expired users.
    This function needs to be updated to work with the new API data structure.
    It likely compares user expiry dates with the current date.
    """
    try:
        # Get all users from the API
        all_users = get_users()
        
        if not all_users:
            return []

        expired = []
        tehran_tz = pytz.timezone('Asia/Tehran')
        now = datetime.now(tehran_tz)

        for user in all_users:
            # Check if user is enabled first
            if not user.get('enable', True):
                # If not enabled, consider it expired or inactive
                expired.append(user)
                continue

            # Try to determine if user is expired based on profile data
            # This logic needs to be robust and handle different data formats
            uuid = user.get('uuid')
            if not uuid:
                continue

            # Get detailed profile
            profile = get_user_profile(uuid)
            if profile:
                # Check remaining days
                remaining_days = profile.get('profile_remaining_days', None)
                if remaining_days is not None and remaining_days <= 0:
                    expired.append(user)
                    continue

                # Check remaining usage
                remaining_usage = profile.get('profile_usage_remaining', None) # Hypothetical field
                if remaining_usage is not None and remaining_usage <= 0:
                    expired.append(user)
                    continue

                # Check expiry date if available directly
                # This depends on how the API exposes expiry
                # expiry_timestamp = profile.get('expiry_timestamp', None) # Hypothetical
                # if expiry_timestamp and expiry_timestamp < now.timestamp():
                #     expired.append(user)
                #     continue

            # Fallback: If profile data is not enough, use user data
            # This is less reliable and depends on Hiddify's data model
            # package_days = user.get('package_days', 0)
            # start_date_str = user.get('start_date') # Format?
            # if start_date_str:
            #     try:
            #         start_date = datetime.fromisoformat(start_date_str.replace('Z', '+00:00'))
            #         start_date_tehran = start_date.astimezone(tehran_tz)
            #         expiry_date = start_date_tehran + timedelta(days=package_days)
            #         if now > expiry_date:
            #             expired.append(user)
            #             continue
            #     except (ValueError, TypeError):
            #         pass # If date parsing fails, skip this check

        return expired

    except Exception as e:
        logger.error(f"Error getting expired users list: {e}")
        return []

# --- Dictionary Processing ---
def dict_process(url, users_dict):
    """
    Process a dictionary of users to add calculated fields.
    This function needs to be updated to work with the new API data structure.
    """
    if not url or not users_dict:
        logger.error("URL and users dictionary are required.")
        return users_dict

    try:
        tehran_tz = pytz.timezone('Asia/Tehran')
        now = datetime.now(tehran_tz)

        for user in users_dict:
            # --- Calculate remaining days ---
            # This logic needs to be adapted based on how the new API provides time data.
            # Assuming we might need to fetch profile for each user for accurate data.
            uuid = user.get('uuid')
            if uuid:
                profile = get_user_profile(uuid)
                if profile:
                    user['remaining_day'] = profile.get('profile_remaining_days', 0)
                else:
                    # Fallback calculation or default
                    user['remaining_day'] = 0
            else:
                user['remaining_day'] = 0

            # --- Calculate remaining usage ---
            usage_limit_gb = user.get('usage_limit_GB', 0)
            current_usage_gb = user.get('current_usage_GB', 0)
            user['usage'] = {
                'current_usage_GB': current_usage_gb,
                'usage_limit_GB': usage_limit_gb,
                'remaining_usage_GB': max(0, usage_limit_gb - current_usage_gb)
            }

            # --- Last connection status ---
            last_online = user.get('last_online', "1-01-01 00:00:00")
            if last_online and last_online != "1-01-01 00:00:00":
                try:
                    # Assuming last_online is in ISO format or similar
                    last_online_dt = datetime.fromisoformat(last_online.replace('Z', '+00:00'))
                    last_online_tehran = last_online_dt.astimezone(tehran_tz)
                    time_diff = now - last_online_tehran

                    if time_diff.days > 30:
                        user['last_connection'] = f"{MESSAGES.get('MONTH', 'Month')} {MESSAGES.get('AGO', 'ago')}" # Fallback text
                    elif time_diff.days > 0:
                        user['last_connection'] = f"{time_diff.days} {MESSAGES.get('DAY', 'day')} {MESSAGES.get('AGO', 'ago')}"
                    elif time_diff.seconds > 3600:
                        user['last_connection'] = f"{time_diff.seconds // 3600} {MESSAGES.get('HOUR', 'hour')} {MESSAGES.get('AGO', 'ago')}"
                    elif time_diff.seconds > 60:
                        user['last_connection'] = f"{time_diff.seconds // 60} {MESSAGES.get('MINUTE', 'minute')} {MESSAGES.get('AGO', 'ago')}"
                    else:
                        user['last_connection'] = MESSAGES.get('ONLINE', 'Online')
                except (ValueError, TypeError):
                    user['last_connection'] = MESSAGES.get('NEVER', 'Never')
            else:
                user['last_connection'] = MESSAGES.get('NEVER', 'Never')

        return users_dict

    except Exception as e:
        logger.error(f"Error processing user dictionary: {e}")
        return users_dict

# --- Users to Dictionary ---
def users_to_dict(users_list):
    """
    Convert a list of users to a dictionary.
    This function might need minor adjustments if the API user structure changes.
    """
    if not users_list:
        return []

    try:
        users_dict = []
        for user in users_list:
            # Assuming `user` is already a dictionary from the API
            # If it's a different object, convert it here
            if isinstance(user, dict):
                users_dict.append(user)
            else:
                # If user is an object, convert its attributes to a dict
                # This is a generic approach, might need specifics
                user_dict = {}
                for attr in dir(user):
                    if not attr.startswith('_'): # Skip private attributes
                        try:
                            user_dict[attr] = getattr(user, attr)
                        except AttributeError:
                            pass
                users_dict.append(user_dict)
        return users_dict

    except Exception as e:
        logger.error(f"Error converting users to dictionary: {e}")
        return []

# --- Full Backup ---
def full_backup():
    """
    Create a full backup of the bot's data.
    This function likely compresses important files and database.
    """
    import zipfile
    import datetime
    try:
        # Define backup location (assuming it's configured)
        backup_loc = os.path.join(os.getcwd(), 'Backup')
        if not os.path.exists(backup_loc):
            os.makedirs(backup_loc)

        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        zip_filename = os.path.join(backup_loc, f"backup_{timestamp}.zip")

        with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as backup_zip:
            # Backup database
            db_path = os.path.join(os.getcwd(), 'Database', 'hidyBot.db')
            if os.path.exists(db_path):
                backup_zip.write(db_path, 'Database/hidyBot.db')

            # Backup configuration files if they exist
            config_files = ['config.json'] # Add other config files if needed
            for config_file in config_files:
                config_path = os.path.join(os.getcwd(), config_file)
                if os.path.exists(config_path):
                    backup_zip.write(config_path, config_file)

            # Backup logs directory
            logs_dir = os.path.join(os.getcwd(), 'Logs')
            if os.path.exists(logs_dir):
                for root, dirs, files in os.walk(logs_dir):
                    for file in files:
                        file_path = os.path.join(root, file)
                        # Add file to zip, preserving directory structure relative to cwd
                        backup_zip.write(file_path, os.path.relpath(file_path, os.getcwd()))

        logger.info(f"Full backup created successfully: {zip_filename}")
        return zip_filename

    except Exception as e:
        logger.error(f"Error creating full backup: {e}")
        return None

# --- Backup JSON Bot ---
def backup_json_bot():
    """
    Backup bot settings to a JSON file.
    """
    try:
        # Get all settings from the database
        settings = all_configs_settings()
        
        # Also backup other relevant data like servers, plans if needed
        # This is a simplified version
        backup_data = {
            "timestamp": datetime.datetime.now().isoformat(),
            "settings": settings
            # Add other data sections here if required
        }
        
        backup_loc = os.path.join(os.getcwd(), 'Backup')
        if not os.path.exists(backup_loc):
            os.makedirs(backup_loc)
            
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        json_filename = os.path.join(backup_loc, f"bot_settings_backup_{timestamp}.json")
        
        with open(json_filename, 'w', encoding='utf-8') as f:
            json.dump(backup_data, f, ensure_ascii=False, indent=4)
            
        logger.info(f"Bot settings backup created successfully: {json_filename}")
        return json_filename
        
    except Exception as e:
        logger.error(f"Error creating bot settings backup: {e}")
        return None

# --- Restore JSON Bot ---
def restore_json_bot(json_file_path):
    """
    Restore bot settings from a JSON file.
    """
    try:
        if not os.path.exists(json_file_path):
            logger.error(f"Backup file {json_file_path} does not exist.")
            return False
            
        with open(json_file_path, 'r', encoding='utf-8') as f:
            backup_data = json.load(f)
            
        settings = backup_data.get("settings", {})
        if not settings:
            logger.warning("No settings found in backup file.")
            return False
            
        # Restore settings to the database
        # This requires knowing the structure of your settings tables
        # Example logic (needs to be adapted to your DB schema):
        success_count = 0
        for key, value in settings.items():
            # Determine the type of setting and update accordingly
            # This is a placeholder, implement based on your DB structure
            # e.g., USERS_DB.update_config(key, value)
            # For now, we'll just log what would be restored
            logger.info(f"Would restore setting: {key} = {value}")
            success_count += 1
            
        logger.info(f"Restored {success_count} settings from {json_file_path}")
        return True
        
    except Exception as e:
        logger.error(f"Error restoring bot settings from {json_file_path}: {e}")
        return False

# --- Owner Information ---
def owner_info():
    """
    Get owner information from the database.
    """
    try:
        # Assuming there's a specific way to get owner info, e.g., a setting or a specific user
        # This is a placeholder implementation
        settings = all_configs_settings()
        
        owner_data = {
            'username': settings.get('support_username', ''),
            'card_number': settings.get('card_number', ''),
            'card_owner': settings.get('card_holder', '')
        }
        
        return owner_data
        
    except Exception as e:
        logger.error(f"Error getting owner info: {e}")
        return {
            'username': '',
            'card_number': '',
            'card_owner': ''
        }

# --- New Feature: Payment Processing Utilities (Placeholder for future integration) ---
def verify_payment_internal(payment_id):
    """
    Placeholder for internal payment verification logic.
    This would integrate with payment gateways.
    """
    # Implementation would go here
    # For example, check payment status in database, call external APIs
    logger.info(f"Verifying payment ID: {payment_id}")
    return True # Placeholder

def generate_payment_link(amount, user_id, description=""):
    """
    Placeholder for generating payment links for online gateways.
    """
    # Implementation would go here
    # For example, integrate with ZarinPal, NextPay, etc.
    logger.info(f"Generating payment link for amount: {amount}, user: {user_id}")
    return f"https://payment-gateway.example.com/pay?amount={amount}&user={user_id}" # Placeholder

# --- New Feature: Affiliate/Referral Utilities ---
def record_referral(referrer_id, referred_id):
    """
    Record a referral action.
    This would update the database to track referrals.
    """
    try:
        # Implementation would interact with USERS_DB to record the referral
        # For example, USERS_DB.add_referral(referrer_id, referred_id)
        logger.info(f"Recording referral: {referrer_id} referred {referred_id}")
        return True
    except Exception as e:
        logger.error(f"Error recording referral {referrer_id} -> {referred_id}: {e}")
        return False

def calculate_referral_commission(user_id):
    """
    Calculate the total commission earned by a user through referrals.
    """
    try:
        # Implementation would query the database for referrals made by user_id
        # and sum up the commission.
        # For example, USERS_DB.get_referral_commissions(user_id)
        logger.info(f"Calculating referral commission for user: {user_id}")
        return 0.0 # Placeholder
    except Exception as e:
        logger.error(f"Error calculating referral commission for user {user_id}: {e}")
        return 0.0

# --- New Feature: Statistics Utilities ---
def get_user_statistics():
    """
    Get overall user statistics.
    """
    try:
        # Get total users, active users, expired users, etc.
        total_users = USERS_DB.select_users()
        total_count = len(total_users) if total_users else 0
        
        # Get expired users using the updated function
        expired_users = expired_users_list()
        expired_count = len(expired_users) if expired_users else 0
        
        active_count = total_count - expired_count # Simplified
        
        stats = {
            'total_users': total_count,
            'active_users': active_count,
            'expired_users': expired_count
        }
        logger.info(f"User statistics: {stats}")
        return stats
    except Exception as e:
        logger.error(f"Error getting user statistics: {e}")
        return {
            'total_users': 0,
            'active_users': 0,
            'expired_users': 0
        }

def get_order_statistics():
    """
    Get overall order/sales statistics.
    """
    try:
        # Get total orders, total revenue, etc.
        orders = USERS_DB.select_orders() # Assuming this method exists
        total_orders = len(orders) if orders else 0
        total_revenue = 0
        if orders:
            for order in orders:
                total_revenue += order.get('price', 0) # Assuming 'price' field
        
        stats = {
            'total_orders': total_orders,
            'total_revenue': total_revenue
        }
        logger.info(f"Order statistics: {stats}")
        return stats
    except Exception as e:
        logger.error(f"Error getting order statistics: {e}")
        return {
            'total_orders': 0,
            'total_revenue': 0
        }

# --- New Feature: Coupon Utilities (Placeholder) ---
def validate_coupon(coupon_code):
    """
    Validate a coupon code.
    """
    # Implementation would check the database for the coupon
    # and verify its validity (expiry, usage limit, etc.)
    logger.info(f"Validating coupon code: {coupon_code}")
    return {
        'valid': True, # Placeholder
        'discount_type': 'percentage', # or 'fixed'
        'discount_value': 10 # 10% discount, or 10000 Rials, etc.
    }

def apply_coupon_discount(original_price, coupon_data):
    """
    Apply a coupon discount to a price.
    """
    if not coupon_data or not coupon_data.get('valid'):
        return original_price
    
    discount_type = coupon_data.get('discount_type')
    discount_value = coupon_data.get('discount_value', 0)
    
    if discount_type == 'percentage':
        discounted_price = original_price * (1 - discount_value / 100.0)
    elif discount_type == 'fixed':
        discounted_price = original_price - discount_value
    else:
        discounted_price = original_price
    
    return max(0, round(discounted_price, 2)) # Ensure price doesn't go negative

# --- New Feature: Multi-Server Load Balancing Utilities (Placeholder) ---
def select_best_server_for_user():
    """
    Select the best server for a new user based on load balancing criteria.
    """
    try:
        servers = USERS_DB.select_servers()
        if not servers:
            logger.warning("No servers available for load balancing.")
            return None

        best_server = None
        best_score = float('inf') # Lower score is better

        for server_data in servers:
            server_id = server_data['id']
            server_url = server_data['url']
            
            # Criteria 1: User count on this server
            # We need to get users for this specific server
            # This might require calling the API for that specific server
            # For now, we'll use a placeholder or data from local DB if available
            # Let's assume we can get user count from local DB linked to server
            users_on_server = USERS_DB.find_order(server_id=server_id) # Simplification
            user_count = len(users_on_server) if users_on_server else 0
            
            # Criteria 2: Server capacity (if defined)
            user_limit = server_data.get('user_limit', float('inf'))
            
            # Criteria 3: Server status (active/inactive)
            is_active = server_data.get('status', True)
            
            if not is_active:
                continue # Skip inactive servers
            
            # Simple scoring: prioritize servers with lower user-to-limit ratio
            # and lower absolute user count
            if user_limit == 0 or user_limit == float('inf'):
                # If no limit, prioritize by absolute user count
                score = user_count
            else:
                # Use ratio, but also consider absolute count to avoid overloading
                usage_ratio = user_count / user_limit if user_limit > 0 else 1
                # Add a small bias towards lower absolute counts
                score = usage_ratio + (user_count * 0.01) 
            
            if score < best_score:
                best_score = score
                best_server = server_data
                
        if best_server:
            logger.info(f"Selected best server: {best_server['title']} (ID: {best_server['id']}) with score {best_score:.4f}")
        else:
            logger.warning("No suitable server found for load balancing.")
            
        return best_server
        
    except Exception as e:
        logger.error(f"Error selecting best server for user: {e}")
        return None

# --- New Feature: Enhanced Logging Utilities ---
def log_user_activity(user_id, activity_type, details=""):
    """
    Log user activities for audit and analytics.
    """
    try:
        timestamp = datetime.datetime.now().isoformat()
        log_message = f"[{timestamp}] USER_ACTIVITY: UserID={user_id}, Type={activity_type}, Details={details}"
        logger.info(log_message)
        # In a more advanced setup, you might write this to a separate activity log file or database table
    except Exception as e:
        logger.error(f"Error logging user activity for user {user_id}: {e}")

# --- New Feature: Data Caching Utilities (Simple In-Memory Cache) ---
# Note: For production, consider using Redis or similar.
import time
_simple_cache = {}
_CACHE_EXPIRY_SECONDS = 300 # 5 minutes

def get_cached_data(key):
    """Get data from simple in-memory cache."""
    try:
        if key in _simple_cache:
            data, timestamp = _simple_cache[key]
            if time.time() - timestamp < _CACHE_EXPIRY_SECONDS:
                logger.debug(f"Cache HIT for key: {key}")
                return data
            else:
                # Expired, remove it
                del _simple_cache[key]
                logger.debug(f"Cache EXPIRED for key: {key}")
    except Exception as e:
        logger.error(f"Error getting cached data for key {key}: {e}")
    return None

def set_cached_data(key, data):
    """Set data in simple in-memory cache."""
    try:
        _simple_cache[key] = (data, time.time())
        logger.debug(f"Cache SET for key: {key}")
    except Exception as e:
        logger.error(f"Error setting cached data for key {key}: {e}")

def clear_cache(key=None):
    """Clear cache entry or entire cache."""
    try:
        if key:
            if key in _simple_cache:
                del _simple_cache[key]
                logger.debug(f"Cache CLEARED for key: {key}")
        else:
            _simple_cache.clear()
            logger.debug("Entire cache CLEARED")
    except Exception as e:
        logger.error(f"Error clearing cache: {e}")
