# Utils/affiliates.py
# Description: This file contains functions for managing the affiliate/referral system.
# It includes functions for registering referrals, calculating commissions, 
# tracking referred users, and applying commissions.

import sqlite3
import logging
from datetime import datetime
from typing import Optional, List, Dict, Any
from Database.dbManager import USERS_DB
from Utils.utils import rial_to_toman, toman_to_rial

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Constants ---
# Default commission rate (as a percentage, e.g., 10 for 10%)
DEFAULT_COMMISSION_RATE_PERCENTAGE = 10

# --- Core Functions ---

def register_referral(referrer_id: int, referred_id: int, db_manager: Any = USERS_DB) -> bool:
    """
    Registers a referral relationship in the database.
    
    Args:
        referrer_id (int): The Telegram ID of the user who made the referral.
        referred_id (int): The Telegram ID of the user who was referred.
        db_manager (Any): The database manager instance (defaults to USERS_DB).
        
    Returns:
        bool: True if the referral was registered successfully, False otherwise.
    """
    try:
        logger.info(f"Registering referral: referrer={referrer_id}, referred={referred_id}")
        
        # Basic validation: A user cannot refer themselves
        if referrer_id == referred_id:
            logger.warning(f"User {referrer_id} attempted to refer themselves.")
            return False
            
        # Check if both users exist
        referrer = db_manager.find_user(telegram_id=referrer_id)
        referred = db_manager.find_user(telegram_id=referred_id)
        
        if not referrer:
            logger.error(f"Referrer user with telegram_id {referrer_id} not found.")
            return False
            
        if not referred:
            logger.error(f"Referred user with telegram_id {referred_id} not found.")
            return False
            
        # Check if this referral relationship already exists
        existing_referral = db_manager.find_referral(referrer_id=referrer_id, referred_id=referred_id)
        if existing_referral:
            logger.info(f"Referral relationship between {referrer_id} and {referred_id} already exists.")
            return True # Or False, depending on desired behavior for duplicates
            
        # Register the referral
        # Assuming db_manager has a method `add_referral` that takes referrer_id and referred_id
        # and optionally a commission field.
        # The commission will likely be calculated and set later, upon a successful purchase.
        referral_status = db_manager.add_referral(referrer_id=referrer_id, referred_id=referred_id)
        
        if referral_status:
            logger.info(f"Referral registered successfully: referrer={referrer_id}, referred={referred_id}")
            return True
        else:
            logger.error(f"Failed to register referral: referrer={referrer_id}, referred={referred_id}")
            return False
            
    except sqlite3.Error as e:
        logger.error(f"Database error registering referral {referrer_id} -> {referred_id}: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error registering referral {referrer_id} -> {referred_id}: {e}")
        return False

def calculate_commission(order_amount_rials: int, commission_rate_percentage: Optional[float] = None, db_manager: Any = USERS_DB) -> int:
    """
    Calculates the commission amount based on the order amount and commission rate.
    
    Args:
        order_amount_rials (int): The total amount of the order in Rials.
        commission_rate_percentage (float, optional): The commission rate as a percentage.
                                                      Defaults to system setting or DEFAULT_COMMISSION_RATE_PERCENTAGE.
        db_manager (Any): The database manager instance (defaults to USERS_DB).
        
    Returns:
        int: The calculated commission amount in Rials.
    """
    try:
        # Determine commission rate
        if commission_rate_percentage is None:
            # Try to get from system settings
            # This assumes a function or method to get system settings
            # For now, we'll use the default
            commission_rate_percentage = DEFAULT_COMMISSION_RATE_PERCENTAGE
            # In a real implementation, you might fetch this from db:
            # settings = db_manager.get_system_settings() # Hypothetical
            # commission_rate_percentage = settings.get('affiliate_commission_rate', DEFAULT_COMMISSION_RATE_PERCENTAGE)
            
        # Validate rate
        if not (0 <= commission_rate_percentage <= 100):
            logger.warning(f"Invalid commission rate {commission_rate_percentage}%. Using default {DEFAULT_COMMISSION_RATE_PERCENTAGE}%.")
            commission_rate_percentage = DEFAULT_COMMISSION_RATE_PERCENTAGE
            
        # Calculate commission
        commission_rials = int(order_amount_rials * (commission_rate_percentage / 100.0))
        logger.info(f"Calculated commission: {rial_to_toman(commission_rials)} Tomans ({commission_rate_percentage}% of {rial_to_toman(order_amount_rials)} Tomans)")
        return commission_rials
        
    except Exception as e:
        logger.error(f"Error calculating commission for amount {order_amount_rials} Rials: {e}")
        return 0

def apply_commission(referrer_id: int, commission_amount_rials: int, referred_id: Optional[int] = None, order_id: Optional[int] = None, db_manager: Any = USERS_DB) -> bool:
    """
    Applies the calculated commission to the referrer's wallet or records it.
    
    Args:
        referrer_id (int): The Telegram ID of the referrer.
        commission_amount_rials (int): The commission amount in Rials.
        referred_id (int, optional): The Telegram ID of the referred user (for record keeping).
        order_id (int, optional): The ID of the order that generated the commission.
        db_manager (Any): The database manager instance (defaults to USERS_DB).
        
    Returns:
        bool: True if the commission was applied successfully, False otherwise.
    """
    try:
        logger.info(f"Applying commission of {rial_to_toman(commission_amount_rials)} Tomans to referrer {referrer_id}")
        
        # Option 1: Add directly to wallet balance
        referrer = db_manager.find_user(telegram_id=referrer_id)
        if not referrer:
            logger.error(f"Referrer user with telegram_id {referrer_id} not found for commission.")
            return False
            
        current_balance = referrer[0].get('balance', 0)
        new_balance = current_balance + commission_amount_rials
        
        # Update user's wallet balance
        update_status = db_manager.edit_user(telegram_id=referrer_id, balance=new_balance)
        if not update_status:
            logger.error(f"Failed to update wallet balance for referrer {referrer_id}")
            return False
            
        # Option 2: Record the commission in a dedicated table for tracking/history
        # This assumes a table `affiliate_commissions` exists
        commission_record_status = db_manager.add_affiliate_commission(
            referrer_id=referrer_id,
            referred_id=referred_id,
            order_id=order_id,
            commission_amount=commission_amount_rials,
            status='credited', # Or 'pending', 'paid_out'
            created_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )
        
        if not commission_record_status:
            logger.warning(f"Commission applied to wallet but failed to record in affiliate_commissions table for referrer {referrer_id}")
            # Depending on requirements, you might want to roll back the wallet update here
            # However, it's often better to have the money in the wallet and deal with the record issue separately
            # For now, we'll consider the main action (adding to wallet) successful
            pass 
            
        logger.info(f"Commission of {rial_to_toman(commission_amount_rials)} Tomans successfully applied to referrer {referrer_id}'s wallet. New balance: {rial_to_toman(new_balance)} Tomans")
        return True
        
    except sqlite3.Error as e:
        logger.error(f"Database error applying commission to referrer {referrer_id}: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error applying commission to referrer {referrer_id}: {e}")
        return False

def get_referrals_list(referrer_id: int, db_manager: Any = USERS_DB) -> Optional[List[Dict]]:
    """
    Gets the list of users referred by a specific user.
    
    Args:
        referrer_id (int): The Telegram ID of the referrer.
        db_manager (Any): The database manager instance (defaults to USERS_DB).
        
    Returns:
        Optional[List[Dict]]: A list of dictionaries containing referred user information, or None on error.
    """
    try:
        logger.info(f"Fetching referrals list for referrer {referrer_id}")
        
        # Get list of referred IDs from the referrals table
        referrals_data = db_manager.get_referrals_by_referrer(referrer_id)
        if not referrals_data:
            logger.info(f"No referrals found for referrer {referrer_id}")
            return [] # Return empty list instead of None for consistency
            
        referred_ids = [referral['referred_id'] for referral in referrals_data]
        
        # Get full user details for each referred ID
        referred_users = []
        for referred_id in referred_ids:
            user_data = db_manager.find_user(telegram_id=referred_id)
            if user_data:
                # Add referral-specific data like commission earned from this user, date, etc.
                # This would require joining with the affiliate_commissions table or calculating
                user_info = user_data[0] # Assuming find_user returns a list
                
                # Example of adding referral metadata (this data would come from your tables)
                # You'd need to adjust this based on your actual schema
                referral_metadata = next((r for r in referrals_data if r['referred_id'] == referred_id), {})
                user_info['referral_date'] = referral_metadata.get('created_at', 'N/A')
                user_info['commission_from_this_user'] = referral_metadata.get('commission', 0) # This might need a separate query
                
                referred_users.append(user_info)
            else:
                # This shouldn't happen if data integrity is maintained, but good to handle
                logger.warning(f"Referred user with ID {referred_id} not found, but exists in referrals table for referrer {referrer_id}")
                
        logger.info(f"Found {len(referred_users)} referrals for referrer {referrer_id}")
        return referred_users
        
    except sqlite3.Error as e:
        logger.error(f"Database error fetching referrals list for {referrer_id}: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error fetching referrals list for {referrer_id}: {e}")
        return None

def get_total_commission_earned(referrer_id: int, db_manager: Any = USERS_DB) -> int:
    """
    Calculates the total commission earned by a referrer.
    
    Args:
        referrer_id (int): The Telegram ID of the referrer.
        db_manager (Any): The database manager instance (defaults to USERS_DB).
        
    Returns:
        int: The total commission earned in Rials.
    """
    try:
        logger.info(f"Calculating total commission earned for referrer {referrer_id}")
        
        # Get all commissions associated with this referrer
        # This assumes a table `affiliate_commissions` with a `referrer_id` column
        commissions_data = db_manager.get_affiliate_commissions(referrer_id=referrer_id)
        
        if not commissions_data:
            logger.info(f"No commissions found for referrer {referrer_id}")
            return 0
            
        total_commission = sum(commission.get('commission_amount', 0) for commission in commissions_data)
        
        logger.info(f"Total commission earned by referrer {referrer_id}: {rial_to_toman(total_commission)} Tomans")
        return total_commission
        
    except sqlite3.Error as e:
        logger.error(f"Database error calculating total commission for {referrer_id}: {e}")
        return 0 # Return 0 on error to avoid disrupting calculations
    except Exception as e:
        logger.error(f"Unexpected error calculating total commission for {referrer_id}: {e}")
        return 0

def generate_referral_link(user_id: int, base_bot_url: str) -> str:
    """
    Generates a referral link for a user.
    Note: This usually involves the bot's username or a deep-linking mechanism.
    For simplicity, we'll construct a deep-linking start parameter.
    
    Args:
        user_id (int): The Telegram ID of the user.
        base_bot_url (str): The base URL where the bot is hosted (for web-based referrals, though less common for Telegram bots).
                          This might be used if you have a web interface or landing page.
        
    Returns:
        str: The referral link/deep-link.
    """
    # For Telegram bots, referral is usually done via deep-linking with start parameter
    # Replace 'YOUR_BOT_USERNAME' with your actual bot username (without @)
    # This should ideally be fetched from a config or settings
    YOUR_BOT_USERNAME = "YourBotUsername" 
    
    # Deep linking format: https://t.me/YOUR_BOT_USERNAME?start=ref_USERID
    # Or if using commands: https://t.me/YOUR_BOT_USERNAME?start=referral_USERID
    referral_link = f"https://t.me/{YOUR_BOT_USERNAME}?start=ref_{user_id}"
    
    logger.info(f"Generated referral link for user {user_id}: {referral_link}")
    return referral_link

# --- Helper Functions (if needed) ---

def is_valid_referral(referrer_id: int, referred_id: int) -> bool:
    """
    Checks if a referral is valid (e.g., not self-referral, not duplicate in business logic).
    This can contain additional checks beyond what's in `register_referral`.
    
    Args:
        referrer_id (int): The Telegram ID of the referrer.
        referred_id (int): The Telegram ID of the referred user.
        
    Returns:
        bool: True if the referral is considered valid, False otherwise.
    """
    # Basic check: Not self-referral
    if referrer_id == referred_id:
        return False
        
    # Add more checks here if needed, e.g.:
    # - Check if referred user is already a customer (depends on business rules)
    # - Check if referrer is eligible for referrals
    # - Check against fraud patterns
    
    # For now, if it passes the self-check, it's considered valid by this helper
    return True

# Example of how this might be used in a bot handler context (conceptual)
"""
def on_user_purchase(user_id: int, order_amount: int):
    # After a successful purchase...
    
    # 1. Check if this user was referred
    user = USERS_DB.find_user(telegram_id=user_id)
    if user and user[0].get('referred_by'): # Assuming user table has a 'referred_by' field
        referrer_id = user[0]['referred_by']
        
        # 2. Calculate commission
        commission = calculate_commission(order_amount)
        
        # 3. Apply commission
        if apply_commission(referrer_id, commission, referred_id=user_id):
            # 4. Notify referrer (optional)
            # send_message_to_user(referrer_id, f"You earned {rial_to_toman(commission)} Tomans from {user[0]['full_name']}'s purchase!")
            pass
    elif user: 
        # If user was not referred through the 'referred_by' field but perhaps through a session/link
        # You would need to retrieve the referrer_id from where it was stored (e.g., user session, temporary link data)
        # For example, if stored in a temporary table or passed through the purchase flow
        # referrer_id = get_referrer_from_session_or_link_data(user_id) 
        # if referrer_id:
        #     commission = calculate_commission(order_amount)
        #     apply_commission(referrer_id, commission, referred_id=user_id)
        pass
"""
