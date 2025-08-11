# Utils/payments_online.py
# Description: This file contains functions for managing online payments.
# It includes functions for integrating with payment gateways like ZarinPal, NextPay, Crypto, etc.
# It handles creating payment requests, verifying payments, and managing payment records.

import sqlite3
import logging
import requests
import uuid
from datetime import datetime
from typing import Optional, Dict, Any, Tuple
from Database.dbManager import USERS_DB
from Utils.utils import rial_to_toman, toman_to_rial

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Constants ---
# Payment Gateway Identifiers
GATEWAY_ZARINPAL = "zarinpal"
GATEWAY_NEXTPAY = "nextpay"
GATEWAY_CRYPTO = "crypto" # Generic placeholder for crypto payments

# Payment Statuses
PAYMENT_STATUS_PENDING = "pending"
PAYMENT_STATUS_COMPLETED = "completed"
PAYMENT_STATUS_FAILED = "failed"
PAYMENT_STATUS_CANCELLED = "cancelled"

# --- Core Functions ---

def initiate_payment(
    user_id: int,
    amount_rials: int,
    gateway: str,
    description: str = "Purchase",
    callback_url: str = "", # Should be provided by the bot
    db_manager: Any = USERS_DB
) -> Optional[Dict]:
    """
    Initiates an online payment request with the specified gateway.
    
    Args:
        user_id (int): The Telegram ID of the user making the payment.
        amount_rials (int): The payment amount in Rials.
        gateway (str): The payment gateway to use (e.g., 'zarinpal', 'nextpay', 'crypto').
        description (str): A description for the payment.
        callback_url (str): The URL the gateway should redirect to after payment.
        db_manager (Any): The database manager instance (defaults to USERS_DB).
        
    Returns:
        Optional[Dict]: A dictionary containing payment details including gateway-specific data
                       (like a transaction ID or redirect URL), or None on failure.
    """
    try:
        logger.info(f"Initiating payment: user={user_id}, amount={rial_to_toman(amount_rials)} Tomans, gateway={gateway}")
        
        # Validate gateway
        if gateway not in [GATEWAY_ZARINPAL, GATEWAY_NEXTPAY, GATEWAY_CRYPTO]:
            logger.error(f"Unsupported payment gateway: {gateway}")
            return None
            
        # Validate amount
        if amount_rials <= 0:
            logger.error(f"Invalid payment amount: {amount_rials} Rials")
            return None
            
        # --- Step 1: Create a local payment record in our database ---
        # This record tracks the payment attempt before redirecting to the gateway.
        payment_data = {
            'user_id': user_id,
            'amount': amount_rials,
            'gateway': gateway,
            'description': description,
            'status': PAYMENT_STATUS_PENDING,
            'created_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'updated_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            # transaction_id will be filled after gateway interaction
            # callback_url is stored if needed for reference
        }
        
        # Add payment record to database
        # Assuming db_manager has a method `add_payment` that returns the payment ID
        payment_id = db_manager.add_payment(**payment_data)
        
        if not payment_id:
            logger.error("Failed to create local payment record in database.")
            return None
            
        logger.info(f"Local payment record created with ID: {payment_id}")
        
        # --- Step 2: Interact with the specific payment gateway ---
        gateway_response = None
        if gateway == GATEWAY_ZARINPAL:
            gateway_response = _initiate_zarinpal_payment(payment_id, amount_rials, description, callback_url)
        elif gateway == GATEWAY_NEXTPAY:
            gateway_response = _initiate_nextpay_payment(payment_id, amount_rials, description, callback_url)
        elif gateway == GATEWAY_CRYPTO:
            # For crypto, we might generate a unique address or invoice
            # This is highly dependent on the specific crypto payment processor used
            gateway_response = _initiate_crypto_payment(payment_id, amount_rials, description)
            
        # --- Step 3: Handle gateway response ---
        if gateway_response and gateway_response.get('success'):
            # Update the local payment record with gateway-specific data
            transaction_id = gateway_response.get('transaction_id')
            redirect_url = gateway_response.get('redirect_url')
            
            update_data = {
                'transaction_id': transaction_id,
                'updated_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            if callback_url:
                update_data['callback_url'] = callback_url
                
            update_status = db_manager.edit_payment(id=payment_id, **update_data)
            
            if not update_status:
                logger.warning(f"Failed to update payment record {payment_id} with gateway data.")
                # Depending on policy, you might want to cancel the gateway transaction here
                # if possible, or flag this inconsistency.
                
            # Return successful initiation details
            return {
                'payment_id': payment_id,
                'transaction_id': transaction_id,
                'redirect_url': redirect_url,
                'gateway_data': gateway_response.get('gateway_data', {}) # Any extra data from gateway
            }
        else:
            # Payment initiation failed at the gateway level
            error_msg = gateway_response.get('error', 'Unknown gateway error') if gateway_response else 'No response from gateway'
            logger.error(f"Payment initiation failed for payment {payment_id} via {gateway}: {error_msg}")
            
            # Update local record to reflect failure
            db_manager.edit_payment(
                id=payment_id,
                status=PAYMENT_STATUS_FAILED,
                updated_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            )
            
            return None
            
    except sqlite3.Error as e:
        logger.error(f"Database error initiating payment for user {user_id}: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error initiating payment for user {user_id}: {e}")
        return None

def verify_payment(
    gateway: str,
    payment_id: int, # Our local payment ID
    gateway_ Dict[str, Any], # Data received from the gateway callback/resolver
    db_manager: Any = USERS_DB
) -> bool:
    """
    Verifies a payment with the specified gateway using data received from the gateway.
    
    Args:
        gateway (str): The payment gateway used (e.g., 'zarinpal', 'nextpay').
        payment_id (int): The ID of our local payment record.
        gateway_data (Dict[str, Any]): Data sent by the gateway (e.g., Authority, Status).
        db_manager (Any): The database manager instance (defaults to USERS_DB).
        
    Returns:
        bool: True if the payment is successfully verified and local record updated, False otherwise.
    """
    try:
        logger.info(f"Verifying payment: payment_id={payment_id}, gateway={gateway}")
        
        # 1. Retrieve local payment record
        local_payment = db_manager.find_payment(id=payment_id)
        if not local_payment:
            logger.error(f"Local payment record with ID {payment_id} not found.")
            return False
            
        local_payment = local_payment[0] # Assuming find_payment returns a list
        
        # 2. Basic validation
        if local_payment['status'] != PAYMENT_STATUS_PENDING:
            logger.warning(f"Attempting to verify non-pending payment {payment_id} (Status: {local_payment['status']}).")
            # Depending on requirements, you might want to reject or handle differently
            # For now, we'll proceed but log the state
            
        # 3. Verify with the specific gateway
        verification_result = None
        if gateway == GATEWAY_ZARINPAL:
            verification_result = _verify_zarinpal_payment(local_payment, gateway_data)
        elif gateway == GATEWAY_NEXTPAY:
            verification_result = _verify_nextpay_payment(local_payment, gateway_data)
        elif gateway == GATEWAY_CRYPTO:
            # Verification for crypto payments depends heavily on the processor
            # It might involve checking blockchain confirmations
            verification_result = _verify_crypto_payment(local_payment, gateway_data)
            
        # 4. Handle verification result
        if verification_result and verification_result.get('verified'):
            amount_verified = verification_result.get('amount', 0)
            transaction_id = verification_result.get('transaction_id')
            
            # Optional: Double-check amount matches expectation
            if amount_verified != local_payment['amount']:
                logger.warning(f"Amount mismatch for payment {payment_id}. Local: {local_payment['amount']}, Verified: {amount_verified}")
                # Policy decision: Accept/Reject/Flag?
                # For now, we'll proceed but log it
                
            # 5. Update local payment record
            update_status = db_manager.edit_payment(
                id=payment_id,
                status=PAYMENT_STATUS_COMPLETED,
                transaction_id=transaction_id, # Ensure it's set/updated
                updated_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                # Add any other relevant fields from verification_result if needed
            )
            
            if update_status:
                logger.info(f"Payment {payment_id} verified successfully via {gateway}. Transaction ID: {transaction_id}")
                return True
            else:
                logger.error(f"Payment {payment_id} verified but failed to update local database record.")
                # This is a critical inconsistency. The payment went through externally
                # but we couldn't record it internally. This needs manual intervention.
                # Consider alerting admins.
                return False # Indicate failure to caller
        else:
            # Verification failed
            error_msg = verification_result.get('error', 'Verification failed') if verification_result else 'No verification response'
            logger.info(f"Payment {payment_id} verification failed via {gateway}: {error_msg}")
            
            # Update local record
            db_manager.edit_payment(
                id=payment_id,
                status=PAYMENT_STATUS_FAILED,
                updated_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            )
            
            return False
            
    except sqlite3.Error as e:
        logger.error(f"Database error verifying payment {payment_id}: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error verifying payment {payment_id}: {e}")
        return False

def cancel_payment(payment_id: int, reason: str = "User cancelled", db_manager: Any = USERS_DB) -> bool:
    """
    Cancels a pending payment.
    
    Args:
        payment_id (int): The ID of the payment to cancel.
        reason (str): The reason for cancellation.
        db_manager (Any): The database manager instance (defaults to USERS_DB).
        
    Returns:
        bool: True if the payment was cancelled successfully, False otherwise.
    """
    try:
        logger.info(f"Cancelling payment: payment_id={payment_id}, reason={reason}")
        
        # Retrieve local payment record
        local_payment = db_manager.find_payment(id=payment_id)
        if not local_payment:
            logger.error(f"Local payment record with ID {payment_id} not found for cancellation.")
            return False
            
        local_payment = local_payment[0]
        
        # Check if payment is in a cancellable state (typically 'pending')
        if local_payment['status'] != PAYMENT_STATUS_PENDING:
            logger.warning(f"Cannot cancel payment {payment_id} with status {local_payment['status']}.")
            # Depending on policy, you might want to allow cancelling 'completed' payments
            # (e.g., refunds) which would be a different process.
            return False
            
        # Update local payment record status to 'cancelled'
        update_status = db_manager.edit_payment(
            id=payment_id,
            status=PAYMENT_STATUS_CANCELLED,
            updated_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            # Optionally store the cancellation reason
        )
        
        if update_status:
            logger.info(f"Payment {payment_id} cancelled successfully. Reason: {reason}")
            
            # --- Optional: Notify Gateway ---
            # Some gateways might require explicit cancellation notification
            # This would involve calling a gateway-specific cancel API
            # Example (conceptual):
            # if local_payment['gateway'] == GATEWAY_ZARINPAL:
            #     _notify_zarinpal_cancel(local_payment['transaction_id'])
            
            return True
        else:
            logger.error(f"Failed to update payment {payment_id} status to cancelled.")
            return False
            
    except sqlite3.Error as e:
        logger.error(f"Database error cancelling payment {payment_id}: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error cancelling payment {payment_id}: {e}")
        return False

def refund_payment(payment_id: int, reason: str = "Admin initiated refund", db_manager: Any = USERS_DB) -> bool:
    """
    Processes a refund for a completed payment.
    Note: Actual refund logic is highly gateway-dependent and often requires API calls to the gateway.
    This function primarily manages the local record state and triggers the gateway process.
    
    Args:
        payment_id (int): The ID of the completed payment to refund.
        reason (str): The reason for the refund.
        db_manager (Any): The database manager instance (defaults to USERS_DB).
        
    Returns:
        bool: True if the refund process was initiated successfully, False otherwise.
    """
    try:
        logger.info(f"Initiating refund for payment: payment_id={payment_id}, reason={reason}")
        
        # 1. Retrieve local payment record
        local_payment = db_manager.find_payment(id=payment_id)
        if not local_payment:
            logger.error(f"Local payment record with ID {payment_id} not found for refund.")
            return False
            
        local_payment = local_payment[0]
        
        # 2. Check if payment is eligible for refund (must be 'completed')
        if local_payment['status'] != PAYMENT_STATUS_COMPLETED:
            logger.warning(f"Cannot refund payment {payment_id} with status {local_payment['status']}. Only completed payments can be refunded.")
            return False
            
        # 3. Determine gateway and initiate refund process
        gateway = local_payment['gateway']
        refund_initiated = False
        refund_reference = None # Reference ID from the gateway for the refund
        
        if gateway == GATEWAY_ZARINPAL:
            # Call ZarinPal refund API (conceptual)
            # refund_result = _refund_zarinpal_payment(local_payment)
            # if refund_result['success']:
            #     refund_initiated = True
            #     refund_reference = refund_result.get('refund_id')
            # This is a placeholder as ZarinPal typically requires manual refund via panel
            logger.warning("ZarinPal refunds usually require manual processing via their panel.")
            refund_initiated = True # Assume initiated for local tracking
            refund_reference = f"manual_refund_{uuid.uuid4().hex[:8]}"
            
        elif gateway == GATEWAY_NEXTPAY:
            # Call NextPay refund API (conceptual)
            # refund_result = _refund_nextpay_payment(local_payment)
            # if refund_result['success']:
            #     refund_initiated = True
            #     refund_reference = refund_result.get('refund_id')
            logger.warning("NextPay refund process needs to be implemented based on their API documentation.")
            refund_initiated = True # Placeholder
            refund_reference = f"manual_refund_{uuid.uuid4().hex[:8]}"
            
        elif gateway == GATEWAY_CRYPTO:
            logger.warning("Crypto refunds require sending funds back to user's provided address. This needs custom logic.")
            # This is complex and requires user address management, wallet integration, etc.
            refund_initiated = False # Cannot automate easily
            refund_reference = None
            
        # 4. Update local record if refund was initiated
        if refund_initiated:
            update_status = db_manager.edit_payment(
                id=payment_id,
                # Status might stay 'completed' and a new 'refund_status' field might be better
                # Or add a note/description field
                # For simplicity, we'll add a note
                description=f"{local_payment.get('description', '')} | Refund Initiated: {reason} | Refund Ref: {refund_reference}",
                updated_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            )
            
            if update_status:
                logger.info(f"Refund initiated for payment {payment_id} via {gateway}. Reference: {refund_reference}")
                return True
            else:
                logger.error(f"Refund initiated for payment {payment_id} but failed to update local record.")
                # Critical: Refund initiated externally but not recorded locally.
                return False
        else:
            logger.error(f"Failed to initiate refund for payment {payment_id} via {gateway}.")
            return False
            
    except sqlite3.Error as e:
        logger.error(f"Database error processing refund for payment {payment_id}: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error processing refund for payment {payment_id}: {e}")
        return False

def get_payment_status(payment_id: int, db_manager: Any = USERS_DB) -> Optional[Dict]:
    """
    Retrieves the status of a payment.
    
    Args:
        payment_id (int): The ID of the payment.
        db_manager (Any): The database manager instance (defaults to USERS_DB).
        
    Returns:
        Optional[Dict]: A dictionary containing payment details, or None on error.
    """
    try:
        logger.info(f"Fetching payment status for payment_id: {payment_id}")
        
        payment = db_manager.find_payment(id=payment_id)
        if payment:
            logger.info(f"Payment status for {payment_id}: {payment[0]['status']}")
            return payment[0] # Assuming find_payment returns a list
        else:
            logger.info(f"Payment with ID {payment_id} not found.")
            return None
            
    except sqlite3.Error as e:
        logger.error(f"Database error fetching payment status for {payment_id}: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error fetching payment status for {payment_id}: {e}")
        return None

# --- Gateway-Specific Internal Functions ---

def _initiate_zarinpal_payment(payment_id: int, amount_rials: int, description: str, callback_url: str) -> Optional[Dict]:
    """
    Initiates a payment request with ZarinPal.
    Note: Requires ZARINPAL_MERCHANT_ID to be configured.
    """
    try:
        # Import ZarinPal merchant ID from config or environment
        # This should be securely stored (e.g., environment variable, encrypted config)
        from config import ZARINPAL_MERCHANT_ID # Or similar secure method
        
        if not ZARINPAL_MERCHANT_ID:
            logger.error("ZarinPal Merchant ID is not configured.")
            return None
            
        amount_tomans = int(rial_to_toman(amount_rials))
        
        # ZarinPal API endpoint for payment request
        url = "https://api.zarinpal.com/pg/v4/payment/request.json"
        
        payload = {
            "merchant_id": ZARINPAL_MERCHANT_ID,
            "amount": amount_tomans,
            "description": description,
            "callback_url": callback_url,
            # "metadata": { "mobile": "09123456789", "email": "user@domain.com" } # Optional
        }
        headers = {"Content-Type": "application/json"}
        
        logger.info(f"Sending ZarinPal payment request for payment ID {payment_id}")
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        logger.debug(f"ZarinPal response  {data}")
        
        # Check ZarinPal response
        if data.get("data", {}).get("code") == 100: # Success
            authority = data["data"]["authority"]
            redirect_url = f"https://www.zarinpal.com/pg/StartPay/{authority}"
            
            logger.info(f"ZarinPal payment request successful for payment ID {payment_id}. Authority: {authority}")
            return {
                'success': True,
                'transaction_id': authority, # ZarinPal uses 'Authority' as transaction ID
                'redirect_url': redirect_url,
                'gateway_data': data # Include full response if needed downstream
            }
        else:
            error_code = data.get("data", {}).get("code", "Unknown")
            error_message = data.get("errors", {}).get("message", "No message")
            logger.error(f"ZarinPal payment request failed for payment ID {payment_id}. Code: {error_code}, Message: {error_message}")
            return {
                'success': False,
                'error': f"ZarinPal Error {error_code}: {error_message}"
            }
            
    except requests.exceptions.RequestException as e:
        logger.error(f"Network error during ZarinPal payment request for payment ID {payment_id}: {e}")
        return {'success': False, 'error': f'Network error: {e}'}
    except Exception as e:
        logger.error(f"Unexpected error during ZarinPal payment request for payment ID {payment_id}: {e}")
        return {'success': False, 'error': f'Unexpected error: {e}'}

def _verify_zarinpal_payment(local_payment: Dict, gateway_ Dict) -> Optional[Dict]:
    """
    Verifies a ZarinPal payment using the Authority and Status received from the callback.
    """
    try:
        # Import ZarinPal merchant ID
        from config import ZARINPAL_MERCHANT_ID
        
        if not ZARINPAL_MERCHANT_ID:
            logger.error("ZarinPal Merchant ID is not configured for verification.")
            return None
            
        authority = gateway_data.get('Authority') or gateway_data.get('authority')
        status = gateway_data.get('Status') or gateway_data.get('status')
        
        if not authority or status != 'OK':
            logger.info(f"ZarinPal payment verification failed at callback level for payment ID {local_payment['id']}. Status: {status}")
            return {
                'verified': False,
                'error': f"Callback status not OK: {status}"
            }
            
        amount_tomans = int(rial_to_toman(local_payment['amount']))
        
        # ZarinPal API endpoint for payment verification
        url = "https://api.zarinpal.com/pg/v4/payment/verify.json"
        
        payload = {
            "merchant_id": ZARINPAL_MERCHANT_ID,
            "amount": amount_tomans,
            "authority": authority
        }
        headers = {"Content-Type": "application/json"}
        
        logger.info(f"Sending ZarinPal payment verification for payment ID {local_payment['id']}")
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        logger.debug(f"ZarinPal verification response data: {data}")
        
        # Check ZarinPal verification response
        if data.get("data", {}).get("code") == 100: # Successful verification
            ref_id = data["data"].get("ref_id")
            # Fee is also available in data['data']['fee']
            
            logger.info(f"ZarinPal payment verification successful for payment ID {local_payment['id']}. RefID: {ref_id}")
            return {
                'verified': True,
                'transaction_id': ref_id, # Use RefID as the final transaction ID
                'amount': local_payment['amount'], # Amount is confirmed by successful verification
                'gateway_data': data
            }
        else:
            error_code = data.get("data", {}).get("code", "Unknown")
            error_message = data.get("errors", {}).get("message", "No message")
            logger.error(f"ZarinPal payment verification failed for payment ID {local_payment['id']}. Code: {error_code}, Message: {error_message}")
            return {
                'verified': False,
                'error': f"ZarinPal Verification Error {error_code}: {error_message}"
            }
            
    except requests.exceptions.RequestException as e:
        logger.error(f"Network error during ZarinPal payment verification for payment ID {local_payment['id']}: {e}")
        return {'verified': False, 'error': f'Network error: {e}'}
    except Exception as e:
        logger.error(f"Unexpected error during ZarinPal payment verification for payment ID {local_payment['id']}: {e}")
        return {'verified': False, 'error': f'Unexpected error: {e}'}

def _initiate_nextpay_payment(payment_id: int, amount_rials: int, description: str, callback_url: str) -> Optional[Dict]:
    """
    Initiates a payment request with NextPay.
    Note: Requires NEXT_PAY_API_KEY to be configured.
    """
    try:
        # Import NextPay API key from config or environment
        from config import NEXT_PAY_API_KEY # Or similar secure method
        
        if not NEXT_PAY_API_KEY:
            logger.error("NextPay API Key is not configured.")
            return None
            
        amount_tomans = int(rial_to_toman(amount_rials))
        
        # NextPay API endpoint for payment request
        # This URL and parameters are based on typical NextPay integration docs
        # Please consult the official NextPay documentation for the exact endpoint and parameters
        url = "https://nextpay.org/nx/gateway/token"
        
        # Generate a unique order ID for NextPay (often based on your internal payment ID)
        order_id = f"order_{payment_id}_{uuid.uuid4().hex[:8]}"
        
        payload = {
            "api_key": NEXT_PAY_API_KEY,
            "amount": amount_tomans,
            "order_id": order_id,
            "callback_uri": callback_url,
            # "customer_phone": "+989123456789", # Optional
            # "custom_json_fields": "{\"product_id\":123, \"product_name\": \"Shoes\"}", # Optional
            # "payer_name": "Mohammad Reza", # Optional
            # "payer_desc": "Buying shoes", # Optional
        }
        
        logger.info(f"Sending NextPay payment request for payment ID {payment_id}")
        response = requests.post(url, data=payload, timeout=30) # NextPay often uses form data
        response.raise_for_status()
        
        # NextPay typically returns data in the response body directly (not JSON)
        # Or it might redirect. Check NextPay docs.
        # This is a simplified example assuming it returns JSON-like structure or specific codes
        # You will need to parse the actual response format from NextPay docs
        
        # Example parsing (this WILL need adjustment based on actual NextPay response)
        response_text = response.text
        logger.debug(f"NextPay response text: {response_text}")
        
        # A common pattern in NextPay is returning a trans_id on success
        if "trans_id" in response_text and "status=1" in response_text:
            # Extract trans_id (this parsing is illustrative, adapt to actual response)
            import re
            match = re.search(r"trans_id=([a-zA-Z0-9_\-]+)", response_text)
            if match:
                trans_id = match.group(1)
                redirect_url = f"https://nextpay.org/nx/gateway/payment/{trans_id}"
                
                logger.info(f"NextPay payment request successful for payment ID {payment_id}. TransID: {trans_id}")
                return {
                    'success': True,
                    'transaction_id': trans_id,
                    'redirect_url': redirect_url,
                    'gateway_data': {'raw_response': response_text, 'order_id': order_id} # Include relevant data
                }
            else:
                logger.error(f"Could not extract trans_id from NextPay response for payment ID {payment_id}.")
                return {
                    'success': False,
                    'error': 'Could not extract transaction ID from NextPay response.'
                }
        else:
            # Assume failure based on absence of success indicators
            # Extract error message if possible (adapt to NextPay's error reporting)
            logger.error(f"NextPay payment request failed for payment ID {payment_id}. Response: {response_text}")
            return {
                'success': False,
                'error': f'NextPay request failed. Response: {response_text[:100]}...' # Truncate long responses
            }
            
    except requests.exceptions.RequestException as e:
        logger.error(f"Network error during NextPay payment request for payment ID {payment_id}: {e}")
        return {'success': False, 'error': f'Network error: {e}'}
    except Exception as e:
        logger.error(f"Unexpected error during NextPay payment request for payment ID {payment_id}: {e}")
        return {'success': False, 'error': f'Unexpected error: {e}'}

def _verify_nextpay_payment(local_payment: Dict, gateway_ Dict) -> Optional[Dict]:
    """
    Verifies a NextPay payment using the trans_id and order_id received from the callback.
    """
    try:
        # Import NextPay API key
        from config import NEXT_PAY_API_KEY
        
        if not NEXT_PAY_API_KEY:
            logger.error("NextPay API Key is not configured for verification.")
            return None
            
        trans_id = gateway_data.get('trans_id')
        order_id = gateway_data.get('order_id') # This should have been stored or derived earlier
        
        # Validate required data
        if not trans_id:
            logger.error(f"Missing trans_id for NextPay verification of payment ID {local_payment['id']}.")
            return {
                'verified': False,
                'error': 'Missing transaction ID for verification.'
            }
            
        # Note: NextPay verification sometimes only requires checking if the callback reached your server
        # with the correct trans_id. The actual financial verification might happen automatically.
        # Consult NextPay docs. For this example, we'll assume a verification API call is needed.
        
        # NextPay API endpoint for payment verification (example, check docs)
        url = "https://nextpay.org/nx/gateway/verify"
        
        payload = {
            "api_key": NEXT_PAY_API_KEY,
            "trans_id": trans_id,
            # Amount might also be required for verification
            "amount": int(rial_to_toman(local_payment['amount'])) # Assuming NextPay expects Tomans
        }
        
        logger.info(f"Sending NextPay payment verification for payment ID {local_payment['id']}")
        response = requests.post(url, data=payload, timeout=30) # NextPay often uses form data
        response.raise_for_status()
        
        response_text = response.text
        logger.debug(f"NextPay verification response text: {response_text}")
        
        # Parse NextPay verification response (HIGHLY dependent on their docs)
        # Example: Looking for specific success/failure indicators
        if "OK" in response_text.upper() or "status=1" in response_text:
            # Assume verified. Extract final transaction reference if available.
            # NextPay might return the same trans_id or a different reference.
            final_trans_id = trans_id # Default to original
            # If NextPay provides a different confirmation ID, extract it here
            
            logger.info(f"NextPay payment verification successful for payment ID {local_payment['id']}.")
            return {
                'verified': True,
                'transaction_id': final_trans_id,
                'amount': local_payment['amount'], # Amount is assumed correct if callback reached
                'gateway_data': {'raw_response': response_text}
            }
        else:
            # Assume verification failed
            logger.error(f"NextPay payment verification failed for payment ID {local_payment['id']}. Response: {response_text}")
            return {
                'verified': False,
                'error': f'NextPay verification failed. Response: {response_text[:100]}...'
            }
            
    except requests.exceptions.RequestException as e:
        logger.error(f"Network error during NextPay payment verification for payment ID {local_payment['id']}: {e}")
        return {'verified': False, 'error': f'Network error: {e}'}
    except Exception as e:
        logger.error(f"Unexpected error during NextPay payment verification for payment ID {local_payment['id']}: {e}")
        return {'verified': False, 'error': f'Unexpected error: {e}'}

def _initiate_crypto_payment(payment_id: int, amount_rials: int, description: str) -> Optional[Dict]:
    """
    Initiates a crypto payment.
    Note: This is a conceptual placeholder. Implementation depends entirely on the
    chosen crypto payment processor (e.g., NOWPayments, CoinPayments, custom wallet integration).
    It might involve generating a unique wallet address or invoice for the user.
    """
    try:
        logger.info(f"Initiating Crypto payment request for payment ID {payment_id}")
        
        # --- Conceptual Steps for Crypto Payment Initiation ---
        # 1. Determine which cryptocurrency to use (BTC, ETH, USDT, etc.)
        #    This might be fixed or chosen by the user.
        currency = "USDT" # Example
        
        # 2. Convert IRR amount to crypto amount
        #    This requires getting the live exchange rate.
        #    Example using a hypothetical exchange rate function:
        #    exchange_rate = get_crypto_exchange_rate(currency, "IRR")
        #    if not exchange_rate:
        #        return {'success': False, 'error': 'Failed to get exchange rate'}
        #    amount_crypto = amount_rials / exchange_rate
        amount_crypto = 10.5 # Placeholder value
        
        # 3. Interact with crypto payment processor API
        #    This is highly specific to the processor.
        #    Example (conceptual):
        #    processor_api_key = get_crypto_processor_api_key() # Securely stored
        #    invoice_data = create_invoice_via_processor(processor_api_key, amount_crypto, currency, description)
        #    if not invoice_data['success']:
        #        return {'success': False, 'error': invoice_data['error']}
        #
        #    invoice_id = invoice_data['invoice_id']
        #    payment_address = invoice_data['payment_address'] # Address user sends to
        #    payment_url = invoice_data['payment_url'] # URL for user to pay via processor's page
        
        # 4. For this placeholder, we'll simulate a successful initiation
        simulated_invoice_id = f"crypto_invoice_{payment_id}_{uuid.uuid4().hex[:8]}"
        simulated_payment_address = f"T{uuid.uuid4().hex[:33]}" # Simulate a TRX/USDT address
        simulated_payment_url = f"https://example-crypto-processor.com/invoice/{simulated_invoice_id}"
        
        logger.info(f"Crypto payment request successful for payment ID {payment_id}. Invoice: {simulated_invoice_id}")
        return {
            'success': True,
            'transaction_id': simulated_invoice_id, # Use invoice ID as transaction ID
            'redirect_url': simulated_payment_url, # URL for user to complete payment
            'gateway_data': {
                'currency': currency,
                'amount_crypto': amount_crypto,
                'payment_address': simulated_payment_address,
                'invoice_id': simulated_invoice_id
            }
        }
        
    except Exception as e:
        logger.error(f"Unexpected error during Crypto payment request for payment ID {payment_id}: {e}")
        return {'success': False, 'error': f'Unexpected error: {e}'}

def _verify_crypto_payment(local_payment: Dict, gateway_ Dict) -> Optional[Dict]:
    """
    Verifies a crypto payment.
    Note: This is a conceptual placeholder. Verification depends on the processor.
    It often involves checking for blockchain confirmations or receiving a webhook/IPN notification.
    """
    try:
        logger.info(f"Verifying Crypto payment for payment ID {local_payment['id']}")
        
        # --- Conceptual Steps for Crypto Payment Verification ---
        # 1. Identify the processor/invoice from local payment data
        # invoice_id = local_payment.get('transaction_id') # Assuming transaction_id holds the invoice ID
        # processor_data = local_payment.get('gateway_data', {}) # Stored during initiation
        
        # 2. Interact with crypto payment processor API to check status
        #    This often happens via a webhook/IPN callback rather than主动 polling.
        #    Example (conceptual):
        #    processor_api_key = get_crypto_processor_api_key()
        #    status_data = check_invoice_status(processor_api_key, invoice_id)
        #    if not status_data['success']:
        #        return {'verified': False, 'error': status_data['error']}
        #
        #    if status_data['status'] == 'paid' or status_data['status'] == 'confirmed':
        #        # Get confirmed amount
        #        confirmed_amount_crypto = status_data['confirmed_amount']
        #        # Convert back to IRR if needed for local record consistency
        #        # exchange_rate = get_crypto_exchange_rate(status_data['currency'], "IRR")
        #        # confirmed_amount_irr = confirmed_amount_crypto * exchange_rate
        #        return {
        #            'verified': True,
        #            'transaction_id': invoice_id,
        #            'amount': confirmed_amount_irr, # Or original amount if fixed
        #            'gateway_data': status_data
        #        }
        #    else:
        #        return {
        #            'verified': False,
        #            'error': f"Invoice status is {status_data['status']}"
        #        }
        
        # 3. For this placeholder, we'll simulate a successful verification
        #    based on some condition in gateway_data (e.g., a secret key passed in a webhook)
        #    This is NOT how it works in reality for crypto.
        secret_verification_key = gateway_data.get('secret_key') # Simulate receiving a key
        expected_secret = "expected_secret_for_payment_" + str(local_payment['id']) # What we expect
        
        if secret_verification_key == expected_secret:
            logger.info(f"Crypto payment verification successful for payment ID {local_payment['id']} (simulated).")
            return {
                'verified': True,
                'transaction_id': local_payment['transaction_id'], # Re-use
                'amount': local_payment['amount'], # Assume correct
                'gateway_data': {'verification_source': 'webhook', 'note': 'Simulated verification'}
            }
        else:
            logger.info(f"Crypto payment verification failed for payment ID {local_payment['id']} (simulated). Invalid secret.")
            return {
                'verified': False,
                'error': 'Invalid verification secret (simulated).'
            }
            
    except Exception as e:
        logger.error(f"Unexpected error during Crypto payment verification for payment ID {local_payment['id']}: {e}")
        return {'verified': False, 'error': f'Unexpected error: {e}'}

# --- Helper Functions (if needed) ---

def generate_unique_order_id(base_id: int) -> str:
    """Generates a unique order ID, potentially incorporating a base ID."""
    return f"order_{base_id}_{uuid.uuid4().hex[:8]}"

# --- Example of how this might be used in a bot handler context (conceptual) ---
"""
def on_user_initiates_payment(user_id: int, amount_rials: int, gateway: str, bot_callback_url: str):
    # 1. Initiate payment
    payment_details = initiate_payment(
        user_id=user_id,
        amount_rials=amount_rials,
        gateway=gateway,
        description=f"Payment by user {user_id}",
        callback_url=bot_callback_url # URL the gateway redirects to after payment attempt
    )
    
    if payment_details:
        # 2. Redirect user to payment gateway
        redirect_url = payment_details.get('redirect_url')
        if redirect_url:
            # Send a message with a button linking to redirect_url
            # Or use a direct link if supported by the bot platform
            send_payment_redirect_message(user_id, redirect_url)
        else:
            send_message_to_user(user_id, "خطا در ایجاد لینک پرداخت.")
    else:
        send_message_to_user(user_id, "خطا در آماده‌سازی پرداخت. لطفاً دوباره تلاش کنید.")

def on_payment_callback_received(gateway: str, payment_id: int, gateway_ Dict):
    # This function is called when the gateway redirects back to your bot
    
    # 1. Verify the payment with the gateway
    verification_status = verify_payment(
        gateway=gateway,
        payment_id=payment_id,
        gateway_data=gateway_data # Contains Authority, Status, trans_id etc. from the gateway
    )
    
    # 2. Handle verification result
    if verification_status:
        # Payment is confirmed
        # Update user's wallet balance, extend subscription, send confirmation message etc.
        # apply_payment_to_user_account(payment_id)
        send_message_to_user(get_user_id_from_payment(payment_id), "پرداخت شما با موفقیت تأیید شد!")
    else:
        # Payment failed or was cancelled
        send_message_to_user(get_user_id_from_payment(payment_id), "پرداخت تأیید نشد یا لغو شد.")
"""
