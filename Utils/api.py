import json
import logging
import requests
from typing import Optional, Dict, List, Any
from config import HIDDIFY_API_KEY, HIDDIFY_BASE_URL, HIDDIFY_PROXY_PATH

# Headers for API requests
API_HEADERS = {
    "Hiddify-API-Key": HIDDIFY_API_KEY,
    "Content-Type": "application/json"
}

# Base URL for admin API
ADMIN_BASE_URL = f"{HIDDIFY_BASE_URL}/{HIDDIFY_PROXY_PATH}/api/v2/admin"

def get_users() -> Optional[List[Dict]]:
    """
    Get all users of current admin
    GET /user/
    """
    try:
        url = f"{ADMIN_BASE_URL}/user/"
        response = requests.get(url, headers=API_HEADERS, timeout=30)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logging.error(f"API error in get_users: {e}")
        return None

def get_user(uuid: str) -> Optional[Dict]:
    """
    Get details of a user
    GET /user/{uuid}/
    """
    try:
        url = f"{ADMIN_BASE_URL}/user/{uuid}/"
        response = requests.get(url, headers=API_HEADERS, timeout=30)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logging.error(f"API error in get_user: {e}")
        return None

def create_user(name: str, usage_limit_GB: float, package_days: int, 
                telegram_id: Optional[int] = None, comment: Optional[str] = None,
                mode: str = "no_reset", lang: str = "en") -> Optional[str]:
    """
    Create a new user
    POST /user/
    
    Returns:
        str: UUID of created user or None if failed
    """
    try:
        # Prepare data according to PostUser schema
        data = {
            "name": name,
            "usage_limit_GB": usage_limit_GB,
            "package_days": package_days,
            "mode": mode,
            "lang": lang,
            "enable": True
        }
        
        # Add optional fields if provided
        if telegram_id is not None:
            data["telegram_id"] = telegram_id
        if comment is not None:
            data["comment"] = comment
            
        url = f"{ADMIN_BASE_URL}/user/"
        response = requests.post(url, headers=API_HEADERS, json=data, timeout=30)
        response.raise_for_status()
        
        result = response.json()
        return result.get("uuid")
    except Exception as e:
        logging.error(f"API error in create_user: {e}")
        return None

def update_user(uuid: str, **kwargs) -> Optional[bool]:
    """
    Update a user
    PATCH /user/{uuid}/
    
    Args:
        uuid: User UUID
        **kwargs: Fields to update (name, usage_limit_GB, package_days, etc.)
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        url = f"{ADMIN_BASE_URL}/user/{uuid}/"
        response = requests.patch(url, headers=API_HEADERS, json=kwargs, timeout=30)
        response.raise_for_status()
        return True
    except Exception as e:
        logging.error(f"API error in update_user: {e}")
        return False

def delete_user(uuid: str) -> Optional[bool]:
    """
    Delete a user
    DELETE /user/{uuid}/
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        url = f"{ADMIN_BASE_URL}/user/{uuid}/"
        response = requests.delete(url, headers=API_HEADERS, timeout=30)
        response.raise_for_status()
        return True
    except Exception as e:
        logging.error(f"API error in delete_user: {e}")
        return False

def disable_user(uuid: str) -> Optional[bool]:
    """
    Disable a user
    """
    return update_user(uuid, enable=False)

def enable_user(uuid: str) -> Optional[bool]:
    """
    Enable a user
    """
    return update_user(uuid, enable=True)

def get_all_configs(user_uuid: str) -> Optional[List[Dict]]:
    """
    Get all configs for a user
    GET /{proxy_path}/{secret_uuid}/api/v2/user/all-configs/
    """
    try:
        url = f"{HIDDIFY_BASE_URL}/{HIDDIFY_PROXY_PATH}/{user_uuid}/api/v2/user/all-configs/"
        headers = {"Hiddify-API-Key": HIDDIFY_API_KEY}  # Use user API key
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logging.error(f"API error in get_all_configs: {e}")
        return None

def get_user_profile(user_uuid: str) -> Optional[Dict]:
    """
    Get user profile information
    GET /{proxy_path}/{secret_uuid}/api/v2/user/me/
    """
    try:
        url = f"{HIDDIFY_BASE_URL}/{HIDDIFY_PROXY_PATH}/{user_uuid}/api/v2/user/me/"
        headers = {"Hiddify-API-Key": HIDDIFY_API_KEY}  # Use user API key
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logging.error(f"API error in get_user_profile: {e}")
        return None

def get_panel_info() -> Optional[Dict]:
    """
    Get panel information
    GET /{proxy_path}/api/v2/panel/info/
    """
    try:
        url = f"{HIDDIFY_BASE_URL}/{HIDDIFY_PROXY_PATH}/api/v2/panel/info/"
        response = requests.get(url, headers=API_HEADERS, timeout=30)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logging.error(f"API error in get_panel_info: {e}")
        return None

def ping_panel() -> Optional[Dict]:
    """
    Ping the panel
    GET /{proxy_path}/api/v2/panel/ping/
    """
    try:
        url = f"{HIDDIFY_BASE_URL}/{HIDDIFY_PROXY_PATH}/api/v2/panel/ping/"
        response = requests.get(url, headers=API_HEADERS, timeout=30)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logging.error(f"API error in ping_panel: {e}")
        return None

def get_admin_info() -> Optional[Dict]:
    """
    Get current admin information
    GET /{proxy_path}/api/v2/admin/me/
    """
    try:
        url = f"{ADMIN_BASE_URL}/me/"
        response = requests.get(url, headers=API_HEADERS, timeout=30)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logging.error(f"API error in get_admin_info: {e}")
        return None

def get_server_status() -> Optional[Dict]:
    """
    Get server status
    GET /{proxy_path}/api/v2/admin/server_status/
    """
    try:
        url = f"{ADMIN_BASE_URL}/server_status/"
        response = requests.get(url, headers=API_HEADERS, timeout=30)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logging.error(f"API error in get_server_status: {e}")
        return None

def update_user_usage() -> Optional[bool]:
    """
    Update user usage
    GET /{proxy_path}/api/v2/admin/update_user_usage/
    """
    try:
        url = f"{ADMIN_BASE_URL}/update_user_usage/"
        response = requests.get(url, headers=API_HEADERS, timeout=30)
        response.raise_for_status()
        return True
    except Exception as e:
        logging.error(f"API error in update_user_usage: {e}")
        return False
