# Utils/coupons.py
# Description: This file contains functions for managing discount coupons.
# It includes functions for creating, retrieving, validating, applying coupons,
# and tracking coupon usage.

import sqlite3
import logging
import secrets
import string
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from Database.dbManager import USERS_DB

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Constants ---
# Default length for auto-generated coupon codes
DEFAULT_CODE_LENGTH = 8

# --- Core Functions ---

def generate_coupon_code(length: int = DEFAULT_CODE_LENGTH) -> str:
    """
    Generates a random, unique coupon code.
    
    Args:
        length (int): The length of the generated code. Defaults to DEFAULT_CODE_LENGTH.
        
    Returns:
        str: The generated coupon code.
    """
    alphabet = string.ascii_uppercase + string.digits
    # Exclude ambiguous characters like 0/O, 1/I/l
    alphabet = alphabet.replace('0', '').replace('O', '').replace('1', '').replace('I', '').replace('l', '')
    
    code = ''.join(secrets.choice(alphabet) for _ in range(length))
    logger.info(f"Generated new coupon code: {code}")
    return code

def create_coupon(
    discount_type: str, 
    discount_value: int, 
    code: Optional[str] = None,
    usage_limit: Optional[int] = None,
    expiry_date: Optional[str] = None, # Expected format: "YYYY-MM-DD" or "YYYY-MM-DD HH:MM:SS"
    is_active: bool = True,
    db_manager: Any = USERS_DB
) -> Optional[Dict]:
    """
    Creates a new coupon in the database.
    
    Args:
        discount_type (str): The type of discount ('percentage' or 'fixed').
        discount_value (int): The discount value (percentage 0-100 or fixed amount in Rials).
        code (str, optional): The coupon code. If None, a random code will be generated.
        usage_limit (int, optional): Maximum number of times the coupon can be used. None for unlimited.
        expiry_date (str, optional): Expiry date/time of the coupon. None for no expiry.
        is_active (bool): Whether the coupon is active upon creation. Defaults to True.
        db_manager (Any): The database manager instance (defaults to USERS_DB).
        
    Returns:
        Optional[Dict]: A dictionary containing the created coupon details, or None on failure.
    """
    try:
        logger.info(f"Creating new coupon: type={discount_type}, value={discount_value}")
        
        # Validate discount type
        if discount_type not in ['percentage', 'fixed']:
            logger.error(f"Invalid discount type: {discount_type}")
            return None
            
        # Validate discount value
        if discount_type == 'percentage':
            if not (0 <= discount_value <= 100):
                logger.error(f"Invalid percentage discount value: {discount_value}. Must be between 0 and 100.")
                return None
        elif discount_type == 'fixed':
            if discount_value < 0:
                logger.error(f"Invalid fixed discount value: {discount_value}. Must be non-negative.")
                return None
                
        # Generate code if not provided
        if not code:
            # Ensure uniqueness - try up to 5 times
            for _ in range(5):
                code = generate_coupon_code()
                existing = db_manager.find_coupon(code=code)
                if not existing:
                    break
            else:
                logger.error("Failed to generate a unique coupon code after 5 attempts.")
                return None
        else:
            # Check if provided code already exists
            existing = db_manager.find_coupon(code=code)
            if existing:
                logger.error(f"Coupon code '{code}' already exists.")
                return None
                
        # Validate expiry date format if provided
        if expiry_date:
            try:
                # This will raise ValueError if format is incorrect
                datetime.strptime(expiry_date, "%Y-%m-%d") # Accept date only
                # Or for datetime: datetime.strptime(expiry_date, "%Y-%m-%d %H:%M:%S")
            except ValueError:
                logger.error(f"Invalid expiry date format: {expiry_date}. Expected YYYY-MM-DD.")
                return None
                
        # Create coupon data dictionary
        coupon_data = {
            'code': code,
            'discount_type': discount_type,
            'discount_value': discount_value,
            'usage_limit': usage_limit,
            'used_count': 0, # Initially 0
            'expiry_date': expiry_date,
            'is_active': is_active,
            'created_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'updated_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        # Add coupon to database
        # Assuming db_manager has a method `add_coupon` that takes keyword arguments
        coupon_id = db_manager.add_coupon(**coupon_data)
        
        if coupon_id:
            logger.info(f"Coupon '{code}' created successfully with ID {coupon_id}.")
            # Fetch and return the created coupon
            created_coupon = db_manager.find_coupon(id=coupon_id)
            if created_coupon:
                return created_coupon[0] # Assuming find_coupon returns a list
        else:
            logger.error(f"Failed to create coupon '{code}'.")
            
        return None
        
    except sqlite3.Error as e:
        logger.error(f"Database error creating coupon: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error creating coupon: {e}")
        return None

def find_coupon_by_code(code: str, db_manager: Any = USERS_DB) -> Optional[Dict]:
    """
    Finds a coupon by its code.
    
    Args:
        code (str): The coupon code.
        db_manager (Any): The database manager instance (defaults to USERS_DB).
        
    Returns:
        Optional[Dict]: A dictionary containing the coupon details, or None if not found.
    """
    try:
        logger.info(f"Finding coupon by code: {code}")
        
        coupon = db_manager.find_coupon(code=code)
        if coupon:
            logger.info(f"Coupon '{code}' found.")
            return coupon[0] # Assuming find_coupon returns a list
        else:
            logger.info(f"Coupon '{code}' not found.")
            return None
            
    except sqlite3.Error as e:
        logger.error(f"Database error finding coupon {code}: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error finding coupon {code}: {e}")
        return None

def validate_coupon(code: str, user_id: Optional[int] = None, db_manager: Any = USERS_DB) -> Dict[str, Any]:
    """
    Validates a coupon code for a specific user (optional).
    
    Args:
        code (str): The coupon code to validate.
        user_id (int, optional): The Telegram ID of the user trying to use the coupon.
        db_manager (Any): The database manager instance (defaults to USERS_DB).
        
    Returns:
        Dict[str, Any]: A dictionary with validation results.
            {
                'valid': bool,
                'coupon': Optional[Dict], # The coupon data if valid
                'error': Optional[str]     # Error message if not valid
            }
    """
    try:
        logger.info(f"Validating coupon: {code} for user: {user_id}")
        
        # 1. Find the coupon
        coupon = find_coupon_by_code(code, db_manager)
        if not coupon:
            return {
                'valid': False,
                'coupon': None,
                'error': 'Coupon not found.'
            }
            
        # 2. Check if coupon is active
        if not coupon.get('is_active', False):
            return {
                'valid': False,
                'coupon': coupon,
                'error': 'Coupon is not active.'
            }
            
        # 3. Check expiry date
        expiry_str = coupon.get('expiry_date')
        if expiry_str:
            try:
                # Handle both date-only and datetime formats
                if len(expiry_str) == 10: # YYYY-MM-DD
                    expiry_datetime = datetime.strptime(expiry_str, "%Y-%m-%d")
                    # Consider the whole day as valid, so compare with end of day
                    expiry_datetime = expiry_datetime.replace(hour=23, minute=59, second=59)
                else: # Assume YYYY-MM-DD HH:MM:SS
                    expiry_datetime = datetime.strptime(expiry_str, "%Y-%m-%d %H:%M:%S")
                    
                if datetime.now() > expiry_datetime:
                    return {
                        'valid': False,
                        'coupon': coupon,
                        'error': 'Coupon has expired.'
                    }
            except ValueError:
                logger.warning(f"Invalid expiry date format in database for coupon {code}: {expiry_str}")
                # Depending on policy, you might want to reject or ignore
                # For now, we'll warn and proceed (assuming no expiry if format is bad)
                pass
                
        # 4. Check usage limit
        usage_limit = coupon.get('usage_limit')
        used_count = coupon.get('used_count', 0)
        if usage_limit is not None and used_count >= usage_limit:
            return {
                'valid': False,
                'coupon': coupon,
                'error': 'Coupon usage limit exceeded.'
            }
            
        # 5. Check if user has already used this coupon (if user_id is provided)
        if user_id is not None:
            usage_record = db_manager.find_coupon_usage(coupon_id=coupon['id'], user_id=user_id)
            if usage_record:
                return {
                    'valid': False,
                    'coupon': coupon,
                    'error': 'You have already used this coupon.'
                }
                
        # If all checks pass
        logger.info(f"Coupon '{code}' is valid.")
        return {
            'valid': True,
            'coupon': coupon,
            'error': None
        }
        
    except sqlite3.Error as e:
        logger.error(f"Database error validating coupon {code}: {e}")
        return {
            'valid': False,
            'coupon': None,
            'error': 'Database error during validation.'
        }
    except Exception as e:
        logger.error(f"Unexpected error validating coupon {code}: {e}")
        return {
            'valid': False,
            'coupon': None,
            'error': 'Unexpected error during validation.'
        }

def apply_coupon_discount(original_amount_rials: int, coupon: Dict) -> int:
    """
    Calculates the discounted amount based on the coupon.
    
    Args:
        original_amount_rials (int): The original amount in Rials.
        coupon (Dict): The validated coupon data.
        
    Returns:
        int: The discounted amount in Rials.
    """
    try:
        logger.info(f"Applying coupon discount: type={coupon['discount_type']}, value={coupon['discount_value']} to amount={original_amount_rials}")
        
        discount_type = coupon['discount_type']
        discount_value = coupon['discount_value']
        discounted_amount = original_amount_rials
        
        if discount_type == 'percentage':
            discount_amount = int(original_amount_rials * (discount_value / 100.0))
            discounted_amount = max(0, original_amount_rials - discount_amount) # Ensure non-negative
            logger.info(f"Applied {discount_value}% discount. Discount amount: {discount_amount} Rials. Final amount: {discounted_amount} Rials")
            
        elif discount_type == 'fixed':
            # Ensure discount doesn't exceed original amount
            discount_amount = min(discount_value, original_amount_rials)
            discounted_amount = original_amount_rials - discount_amount
            logger.info(f"Applied fixed discount of {discount_amount} Rials. Final amount: {discounted_amount} Rials")
            
        return discounted_amount
        
    except Exception as e:
        logger.error(f"Error applying coupon discount: {e}")
        # In case of error, return original amount (no discount)
        return original_amount_rials

def use_coupon(coupon_id: int, user_id: int, db_manager: Any = USERS_DB) -> bool:
    """
    Records the usage of a coupon by a user and updates the coupon's used count.
    
    Args:
        coupon_id (int): The ID of the coupon.
        user_id (int): The Telegram ID of the user who used the coupon.
        db_manager (Any): The database manager instance (defaults to USERS_DB).
        
    Returns:
        bool: True if usage was recorded successfully, False otherwise.
    """
    try:
        logger.info(f"Recording coupon usage: coupon_id={coupon_id}, user_id={user_id}")
        
        # 1. Record usage in coupon_usage table
        usage_data = {
            'coupon_id': coupon_id,
            'user_id': user_id,
            'used_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        usage_status = db_manager.add_coupon_usage(**usage_data)
        
        if not usage_status:
            logger.error(f"Failed to record coupon usage in database for coupon_id {coupon_id}, user_id {user_id}")
            return False
            
        # 2. Increment used_count in coupons table
        # First, get current used_count
        coupon = db_manager.find_coupon(id=coupon_id)
        if not coupon:
            logger.error(f"Coupon with ID {coupon_id} not found for updating used count.")
            # Even though usage was recorded, we couldn't update the count.
            # This is a data inconsistency risk. 
            # Depending on requirements, you might want to delete the usage record or flag it.
            return False # Consider it a failure
            
        current_used_count = coupon[0].get('used_count', 0)
        new_used_count = current_used_count + 1
        
        update_status = db_manager.edit_coupon(id=coupon_id, used_count=new_used_count)
        if not update_status:
            logger.error(f"Failed to update used_count for coupon_id {coupon_id}")
            # Again, potential data inconsistency.
            return False
            
        logger.info(f"Coupon usage recorded successfully for coupon_id {coupon_id}, user_id {user_id}. New used count: {new_used_count}")
        return True
        
    except sqlite3.Error as e:
        logger.error(f"Database error recording coupon usage: coupon_id {coupon_id}, user_id {user_id}: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error recording coupon usage: coupon_id {coupon_id}, user_id {user_id}: {e}")
        return False

def get_all_coupons(db_manager: Any = USERS_DB) -> Optional[List[Dict]]:
    """
    Retrieves a list of all coupons.
    
    Args:
        db_manager (Any): The database manager instance (defaults to USERS_DB).
        
    Returns:
        Optional[List[Dict]]: A list of dictionaries containing coupon details, or None on error.
    """
    try:
        logger.info("Fetching list of all coupons")
        
        coupons = db_manager.select_coupons() # Assuming this method exists
        if coupons is not None:
            logger.info(f"Fetched {len(coupons)} coupons")
            return coupons
        else:
            logger.info("No coupons found or error fetching coupons")
            return [] # Return empty list for consistency
            
    except sqlite3.Error as e:
        logger.error(f"Database error fetching all coupons: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error fetching all coupons: {e}")
        return None

def deactivate_coupon(coupon_id: int, db_manager: Any = USERS_DB) -> bool:
    """
    Deactivates a coupon.
    
    Args:
        coupon_id (int): The ID of the coupon to deactivate.
        db_manager (Any): The database manager instance (defaults to USERS_DB).
        
    Returns:
        bool: True if deactivated successfully, False otherwise.
    """
    try:
        logger.info(f"Deactivating coupon ID: {coupon_id}")
        
        status = db_manager.edit_coupon(id=coupon_id, is_active=False)
        if status:
            logger.info(f"Coupon ID {coupon_id} deactivated successfully.")
        else:
            logger.error(f"Failed to deactivate coupon ID {coupon_id}")
        return status
        
    except sqlite3.Error as e:
        logger.error(f"Database error deactivating coupon {coupon_id}: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error deactivating coupon {coupon_id}: {e}")
        return False

def activate_coupon(coupon_id: int, db_manager: Any = USERS_DB) -> bool:
    """
    Activates a coupon.
    
    Args:
        coupon_id (int): The ID of the coupon to activate.
        db_manager (Any): The database manager instance (defaults to USERS_DB).
        
    Returns:
        bool: True if activated successfully, False otherwise.
    """
    try:
        logger.info(f"Activating coupon ID: {coupon_id}")
        
        status = db_manager.edit_coupon(id=coupon_id, is_active=True)
        if status:
            logger.info(f"Coupon ID {coupon_id} activated successfully.")
        else:
            logger.error(f"Failed to activate coupon ID {coupon_id}")
        return status
        
    except sqlite3.Error as e:
        logger.error(f"Database error activating coupon {coupon_id}: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error activating coupon {coupon_id}: {e}")
        return False

def delete_coupon(coupon_id: int, db_manager: Any = USERS_DB) -> bool:
    """
    Deletes a coupon permanently. Use with caution.
    Consider deactivating instead of deleting.
    
    Args:
        coupon_id (int): The ID of the coupon to delete.
        db_manager (Any): The database manager instance (defaults to USERS_DB).
        
    Returns:
        bool: True if deleted successfully, False otherwise.
    """
    try:
        logger.warning(f"Deleting coupon ID: {coupon_id} (Use with caution!)")
        
        # Optional: Check if coupon has been used
        # usage_records = db_manager.find_coupon_usage(coupon_id=coupon_id)
        # if usage_records:
        #     logger.warning(f"Coupon ID {coupon_id} has usage records. Deleting anyway.")
        
        status = db_manager.delete_coupon(id=coupon_id) # Assuming this method exists
        if status:
            logger.info(f"Coupon ID {coupon_id} deleted successfully.")
        else:
            logger.error(f"Failed to delete coupon ID {coupon_id}")
        return status
        
    except sqlite3.Error as e:
        logger.error(f"Database error deleting coupon {coupon_id}: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error deleting coupon {coupon_id}: {e}")
        return False

# --- Helper Functions (if needed) ---

def rial_to_toman(rial: int) -> float:
    """Convert Rial to Toman."""
    return rial / 10.0

def toman_to_rial(toman: float) -> int:
    """Convert Toman to Rial."""
    return int(toman * 10)

# Example of how this might be used in a bot handler context (conceptual)
"""
def on_user_requests_coupon_info(user_id: int, coupon_code: str):
    validation_result = validate_coupon(coupon_code, user_id=user_id)
    if validation_result['valid']:
        coupon = validation_result['coupon']
        message = f"کوپن '{coupon['code']}' معتبر است!\n"
        if coupon['discount_type'] == 'percentage':
            message += f"تخفیف: {coupon['discount_value']}%\n"
        else: # fixed
            message += f"تخفیف: {rial_to_toman(coupon['discount_value'])} تومان\n"
        # Add expiry, usage info etc.
        send_message_to_user(user_id, message)
    else:
        send_message_to_user(user_id, f"کوپن نامعتبر: {validation_result['error']}")

def on_user_applies_coupon_to_order(user_id: int, order_amount: int, coupon_code: str):
    validation_result = validate_coupon(coupon_code, user_id=user_id)
    if validation_result['valid']:
        coupon = validation_result['coupon']
        discounted_amount = apply_coupon_discount(order_amount, coupon)
        # Record usage
        if use_coupon(coupon['id'], user_id):
            # Proceed with discounted order
            process_order_with_discount(user_id, discounted_amount, coupon['code'])
        else:
            # Handle failure to record usage
            send_message_to_user(user_id, "خطا در اعمال کوپن. لطفاً دوباره تلاش کنید.")
    else:
        send_message_to_user(user_id, f"کوپن نامعتبر: {validation_result['error']}")
"""
