# Utils/serverInfo.py
# Description: This file contains functions to get server status information from Hiddify panel.
# Thanks to https://github.com/m-mjd/hiddybot_info_severs  

import sqlite3
from urllib.parse import urlparse
import requests
from Database.dbManager import USERS_DB
import logging
from config import HIDDIFY_API_KEY, HIDDIFY_BASE_URL, HIDDIFY_PROXY_PATH

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Headers for API requests
API_HEADERS = {
    "Hiddify-API-Key": HIDDIFY_API_KEY,
    "Content-Type": "application/json"
}

def scrape_data_from_json_url(url):
    """
    Scrape data from a JSON URL.
    This function is kept for backward compatibility, but it's recommended to use the new API functions.
    """
    try:
        logger.info(f"Scraping data from JSON URL: {url}")
        response = requests.get(url, timeout=30)
        response.raise_for_status()

        # Parse JSON data
        json_data = response.json()

        # Extract information from JSON using the shared function
        extracted_data = json_template(json_data)

        return extracted_data

    except requests.exceptions.RequestException as e:
        logger.error(f"Error scraping data from JSON URL {url}: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error scraping data from JSON URL {url}: {e}")
        return None


def json_template(data):
    """
    Extract relevant data from the JSON response.
    This function is kept for backward compatibility with the old scraping method.
    """
    try:
        system_stats = data.get('stats', {}).get('system', {})
        top5_stats = data.get('stats', {}).get('top5', {})
        usage_history = data.get('usage_history', {})
        
        # Extract system stats
        bytes_recv = system_stats.get('bytes_recv')
        bytes_recv_cumulative = system_stats.get('bytes_recv_cumulative')
        bytes_sent = system_stats.get('bytes_sent')
        bytes_sent_cumulative = system_stats.get('bytes_sent_cumulative')
        cpu_percent = system_stats.get('cpu_percent')
        number_of_cores = system_stats.get('num_cpus')
        disk_total = system_stats.get('disk_total')
        disk_used = system_stats.get('disk_used')
        ram_total = system_stats.get('ram_total')
        ram_used = system_stats.get('ram_used')
        total_upload_server = system_stats.get('net_sent_cumulative_GB')
        total_download_server = system_stats.get('net_total_cumulative_GB')
        hiddify_used = system_stats.get('hiddify_used')
        load_avg_15min = system_stats.get('load_avg_15min')
        load_avg_1min = system_stats.get('load_avg_1min')
        load_avg_5min = system_stats.get('load_avg_5min')
        total_connections = system_stats.get('total_connections')
        total_unique_ips = system_stats.get('total_unique_ips')
        
        # Extract top5 stats
        cpu_top5 = top5_stats.get('cpu', [])
        memory_top5 = top5_stats.get('memory', [])
        ram_top5 = top5_stats.get('ram', [])
        
        # Extract usage history
        online_last_24h = usage_history.get('h24', {}).get('online')
        usage_last_24h = usage_history.get('h24', {}).get('usage')
        online_last_30_days = usage_history.get('last_30_days', {}).get('online')
        usage_last_30_days = usage_history.get('last_30_days', {}).get('usage')
        online_last_5min = usage_history.get('m5', {}).get('online')
        usage_last_5min = usage_history.get('m5', {}).get('usage')
        online_today = usage_history.get('today', {}).get('online')
        usage_today = usage_history.get('today', {}).get('usage')
        online_total = usage_history.get('total', {}).get('online')
        usage_total = usage_history.get('total', {}).get('usage')
        total_users = usage_history.get('total', {}).get('users')
        online_yesterday = usage_history.get('yesterday', {}).get('online')
        usage_yesterday = usage_history.get('yesterday', {}).get('usage')

        return {
            'bytes_recv': bytes_recv,
            'bytes_recv_cumulative': bytes_recv_cumulative,
            'bytes_sent': bytes_sent,
            'bytes_sent_cumulative': bytes_sent_cumulative,
            'cpu_percent': cpu_percent,
            'number_of_cores': number_of_cores,
            'disk_total': disk_total,
            'disk_used': disk_used,
            'ram_total': ram_total,
            'ram_used': ram_used,
            'total_upload_server': total_upload_server,
            'total_download_server': total_download_server,
            'hiddify_used': hiddify_used,
            'load_avg_15min': load_avg_15min,
            'load_avg_1min': load_avg_1min,
            'load_avg_5min': load_avg_5min,
            'total_connections': total_connections,
            'total_unique_ips': total_unique_ips,
            'cpu_top5': cpu_top5,
            'memory_top5': memory_top5,
            'ram_top5': ram_top5,
            'online_last_24h': online_last_24h,
            'usage_last_24h': usage_last_24h,
            'online_last_30_days': online_last_30_days,
            'usage_last_30_days': usage_last_30_days,
            'online_last_5min': online_last_5min,
            'usage_last_5min': usage_last_5min,
            'online_today': online_today,
            'usage_today': usage_today,
            'online_total': online_total,
            'usage_total': usage_total,
            'total_users': total_users,
            'online_yesterday': online_yesterday,
            'usage_yesterday': usage_yesterday,
        }
    except Exception as e:
        logger.error(f"Error processing JSON template: {e}")
        return None


def get_server_status_via_api(server_url):
    """
    Get server status using the new Hiddify API v2.2.0.
    GET /{proxy_path}/api/v2/panel/ping/
    """
    try:
        # Construct the URL for the ping endpoint
        url = f"{server_url.rstrip('/')}/{HIDDIFY_PROXY_PATH}/api/v2/panel/ping/"
        logger.info(f"Getting server status via API: {url}")
        
        response = requests.get(url, headers=API_HEADERS, timeout=30)
        response.raise_for_status()
        
        result = response.json()
        logger.info(f"Server status retrieved successfully: {result}")
        return result
    except requests.exceptions.RequestException as e:
        logger.error(f"Error getting server status via API {url}: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error getting server status via API {url}: {e}")
        return None


def get_detailed_server_info_via_api(server_url):
    """
    Get detailed server information using the new Hiddify API v2.2.0.
    GET /{proxy_path}/api/v2/panel/info/
    """
    try:
        # Construct the URL for the info endpoint
        url = f"{server_url.rstrip('/')}/{HIDDIFY_PROXY_PATH}/api/v2/panel/info/"
        logger.info(f"Getting detailed server info via API: {url}")
        
        response = requests.get(url, headers=API_HEADERS, timeout=30)
        response.raise_for_status()
        
        result = response.json()
        logger.info(f"Detailed server info retrieved successfully")
        return result
    except requests.exceptions.RequestException as e:
        logger.error(f"Error getting detailed server info via API {url}: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error getting detailed server info via API {url}: {e}")
        return None


def get_server_stats_via_api(server_url):
    """
    Get server statistics using the new Hiddify API v2.2.0.
    GET /{proxy_path}/api/v2/admin/server_status/
    """
    try:
        # Construct the URL for the server_status endpoint
        url = f"{server_url.rstrip('/')}/{HIDDIFY_PROXY_PATH}/api/v2/admin/server_status/"
        logger.info(f"Getting server stats via API: {url}")
        
        response = requests.get(url, headers=API_HEADERS, timeout=30)
        response.raise_for_status()
        
        result = response.json()
        logger.info(f"Server stats retrieved successfully")
        return result
    except requests.exceptions.RequestException as e:
        logger.error(f"Error getting server stats via API {url}: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error getting server stats via API {url}: {e}")
        return None


def server_status_template(result, server_name):
    """
    Template for displaying server status information.
    This function now handles both old scraped data and new API data.
    """
    try:
        lline = (32 * "-")
        
        # Handle different data structures (old vs new API)
        if 'system' in result and 'usage_history' in result:
            # Old scraped data structure
            return _old_server_status_template(result, server_name)
        else:
            # New API data structure or combined data
            # We'll need to adapt this based on the actual API response
            # For now, let's assume a simplified version
            version = result.get('version', 'N/A')
            hiddify_used = result.get('hiddify_used', 'N/A')
            total_users = result.get('total_users', 'N/A')
            
            # If we have more detailed stats from the new API, we can use them
            # This is a placeholder - you'd need to map the actual API fields
            cpu_percent = result.get('cpu', {}).get('percent', 'N/A') if 'cpu' in result else 'N/A'
            ram_total = result.get('ram', {}).get('total', 'N/A') if 'ram' in result else 'N/A'
            ram_used = result.get('ram', {}).get('used', 'N/A') if 'ram' in result else 'N/A'
            disk_total = result.get('disk', {}).get('total', 'N/A') if 'disk' in result else 'N/A'
            disk_used = result.get('disk', {}).get('used', 'N/A') if 'disk' in result else 'N/A'
            
            # Calculate percentages
            ram_percent = (ram_used / ram_total) * 100 if ram_total and ram_total != 'N/A' and ram_total != 0 else 'N/A'
            disk_percent = (disk_used / disk_total) * 100 if disk_total and disk_total != 'N/A' and disk_total != 0 else 'N/A'
            
            # Format values
            formatted_ram_total = f"{ram_total:.2f} GB" if ram_total != 'N/A' else 'N/A'
            formatted_ram_used = f"{ram_used:.2f} GB" if ram_used != 'N/A' else 'N/A'
            formatted_disk_total = f"{disk_total:.2f} GB" if disk_total != 'N/A' else 'N/A'
            formatted_disk_used = f"{disk_used:.2f} GB" if disk_used != 'N/A' else 'N/A'
            
            return f"<b>Server: {server_name}</b>\n{lline}\n" \
                           f"<b>SYSTEM INFO</b>\n"\
                           f"Version: {version}\n" \
                           f"CPU: {cpu_percent}%\n" \
                           f"RAM: {formatted_ram_used} / {formatted_ram_total} ({ram_percent:.2f}%)\n" \
                           f"DISK: {formatted_disk_used} / {formatted_disk_total} ({disk_percent:.2f}%)\n\n" \
                           f"<b>USAGE INFO</b>\n"\
                           f"Total Users: {total_users} User\n" \
                           f"Hiddify Used: {hiddify_used}\n"
                           
    except Exception as e:
        logger.error(f"Error creating server status template: {e}")
        return f"<b>Error creating server status for: {server_name}</b>"


def _old_server_status_template(result, server_name):
    """Helper function to handle old scraped data structure."""
    try:
        lline = (32 * "-")
        
        bytes_recv = result.get('bytes_recv', 'N/A')
        bytes_recv_cumulative = result.get('bytes_recv_cumulative', 'N/A')
        bytes_sent = result.get('bytes_sent', 'N/A')
        bytes_sent_cumulative = result.get('bytes_sent_cumulative', 'N/A')
        cpu_percent = result.get('cpu_percent', 'N/A')
        number_of_cores = result.get('number_of_cores', 'N/A')
        disk_total = result.get('disk_total', 'N/A')
        disk_used = result.get('disk_used', 'N/A')
        ram_total = result.get('ram_total', 'N/A')
        ram_used = result.get('ram_used', 'N/A')
        total_upload_server = result.get('total_upload_server', 'N/A')
        total_download_server = result.get('total_download_server', 'N/A')
        online_last_24h = result.get('online_last_24h', 'N/A')
        usage_last_24h = result.get('usage_last_24h', 'N/A')
        usage_last_24h = f"{usage_last_24h / (1024 ** 3):.2f} GB" if usage_last_24h != 'N/A' else 'N/A'
        online_last_30_days = result.get('online_last_30_days', 'N/A')
        usage_last_30_days = result.get('usage_last_30_days', 'N/A')
        usage_last_30_days = f"{usage_last_30_days / (1024 ** 3):.2f} GB" if usage_last_30_days != 'N/A' else 'N/A'
        online_last_5min = result.get('online_last_5min', 'N/A')
        usage_last_5min = result.get('usage_last_5min', 'N/A')
        online_today = result.get('online_today', 'N/A')
        usage_today = result.get('usage_today', 'N/A')
        usage_today = f"{usage_today / (1024 ** 3):.2f} GB" if usage_today != 'N/A' else 'N/A'
        online_total = result.get('online_total', 'N/A')
        usage_total = result.get('usage_total', 'N/A')
        usage_total = f"{usage_total / (1024 ** 3):.2f} GB" if usage_total != 'N/A' else 'N/A'
        total_users = result.get('total_users', 'N/A')
        online_yesterday = result.get('online_yesterday', 'N/A')
        usage_yesterday = result.get('usage_yesterday', 'N/A')
        hiddify_used = result.get('hiddify_used', 'N/A')
        load_avg_15min = result.get('load_avg_15min', 'N/A')
        load_avg_1min = result.get('load_avg_1min', 'N/A')
        load_avg_5min = result.get('load_avg_5min', 'N/A')
        total_connections = result.get('total_connections', 'N/A')
        total_unique_ips = result.get('total_unique_ips', 'N/A')
        cpu_top5 = result.get('cpu_top5', 'N/A')
        memory_top5 = result.get('memory_top5', 'N/A')
        ram_top5 = result.get('ram_top5', 'N/A')
        
        # Calculate percentage for RAM and Disk
        ram_percent = (ram_used / ram_total) * \
            100 if ram_total != 'N/A' and ram_total != 0 else 'N/A'
        disk_percent = (disk_used / disk_total) * \
            100 if disk_total != 'N/A' and disk_total != 0 else 'N/A'
        
        # Format bytes with appropriate units
        formatted_bytes_recv = f"{bytes_recv / (1024 ** 2):.2f} MB" if bytes_recv != 'N/A' else 'N/A'
        formatted_bytes_sent = f"{bytes_sent / (1024 ** 2):.2f} MB" if bytes_sent != 'N/A' else 'N/A'
        
        # Add information for all servers
        return f"<b>Server: {server_name}</b>\n{lline}\n" \
                           f"<b>SYSTEM INFO</b>\n"\
                           f"CPU: {cpu_percent}% - {number_of_cores} CORE\n" \
                           f"RAM: {ram_used:.2f} GB / {ram_total:.2f} GB ({ram_percent:.2f}%)\n" \
                           f"DISK: {disk_used:.2f} GB / {disk_total:.2f} GB  ({disk_percent:.2f}%)\n\n" \
                           f"<b>NETWORK INFO</b>\n"\
                           f"Total Users: {total_users} User\n" \
                           f"Usage (Today): {usage_today}\n" \
                           f"Online (Now): {online_last_5min} User\n" \
                           f"Now Network Received: {formatted_bytes_recv}\n" \
                           f"Now Network Sent: {formatted_bytes_sent}\n" \
                           f"Online (Today): {online_today} User\n" \
                           f"Online(30 Days): {online_last_30_days} User\n" \
                           f"Usage(30 Days): {usage_last_30_days}\n"\
                           f"Total Download (Server): {total_download_server:.2f} GB\n" \
                           f"Total Upload (Server): {total_upload_server:.2f} GB\n"
    except Exception as e:
        logger.error(f"Error creating old server status template: {e}")
        return f"<b>Error creating server status for: {server_name}</b>"


def get_server_status(server_row):
    """
    Get server status - tries new API first, falls back to old scraping method.
    """
    try:
        server_name = server_row['title']
        server_url = server_row['url']
        
        logger.info(f"Getting status for server: {server_name} ({server_url})")
        
        # Try new API method first
        api_status = get_server_stats_via_api(server_url)
        if api_status:
            logger.info(f"Successfully got status via new API for server: {server_name}")
            txt = server_status_template(api_status, server_name)
            return txt
        
        # Fallback to old scraping method
        logger.warning(f"Falling back to old scraping method for server: {server_name}")
        scraped_data = scrape_data_from_json_url(f"{server_url}/admin/get_data/")
        if scraped_data:
            logger.info(f"Successfully got status via old scraping for server: {server_name}")
            txt = server_status_template(scraped_data, server_name)
            return txt
            
        logger.error(f"Failed to get status for server: {server_name}")
        return False
        
    except Exception as e:
        logger.error(f"Error getting server status for {server_row.get('title', 'Unknown')}: {e}")
        return False
