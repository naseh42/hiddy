# Utils/gateways.py
# Description: This file contains functions for interacting directly with payment gateway APIs.
# It handles the low-level communication, request/response parsing, and error handling for each gateway.

import requests
import logging
import uuid
from datetime import datetime
from typing import Optional, Dict, Any
from config import ZARINPAL_MERCHANT_ID, NEXT_PAY_API_KEY # Import API keys from config
# from Utils.crypto_processor import initiate_crypto_invoice, verify_crypto_invoice # Example for crypto

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Constants ---
ZARINPAL_REQUEST_URL = "https://api.zarinpal.com/pg/v4/payment/request.json"
ZARINPAL_VERIFY_URL = "https://api.zarinpal.com/pg/v4/payment/verify.json"
ZARINPAL_REDIRECT_URL = "https://www.zarinpal.com/pg/StartPay/"
ZARINPAL_GATEWAY_URL = "https://www.zarinpal.com/pg/StartPay/"

NEXTPAY_REQUEST_URL = "https://nextpay.org/nx/gateway/token"
NEXTPAY_VERIFY_URL = "https://nextpay.org/nx/gateway/verify"
NEXTPAY_REDIRECT_URL = "https://nextpay.org/nx/gateway/payment/"

# --- ZarinPal Functions ---

def zarinpal_request_payment(amount_tomans: int, description: str, callback_url: str, 
                             mobile: Optional[str] = None, email: Optional[str] = None) -> Optional[Dict]:
    """
    Sends a payment request to ZarinPal.
    
    Args:
        amount_tomans (int): The payment amount in Tomans.
        description (str): A description for the payment.
        callback_url (str): The URL ZarinPal redirects to after payment.
        mobile (str, optional): Customer's mobile number.
        email (str, optional): Customer's email address.
        
    Returns:
        Optional[Dict]: A dictionary containing the response from ZarinPal, including
                       Authority (transaction ID) and redirect URL, or None on failure.
    """
    try:
        if not ZARINPAL_MERCHANT_ID:
            logger.error("ZarinPal Merchant ID is not configured.")
            return None

        payload = {
            "merchant_id": ZARINPAL_MERCHANT_ID,
            "amount": amount_tomans,
            "description": description,
            "callback_url": callback_url,
        }
        if mobile:
            payload["metadata"] = {"mobile": mobile}
        if email:
            if "metadata" in payload:
                payload["metadata"]["email"] = email
            else:
                payload["metadata"] = {"email": email}

        headers = {"Content-Type": "application/json"}

        logger.info(f"Sending ZarinPal payment request for {amount_tomans} Tomans")
        response = requests.post(ZARINPAL_REQUEST_URL, json=payload, headers=headers, timeout=30)
        response.raise_for_status()

        data = response.json()
        logger.debug(f"ZarinPal request response: {data}")

        if data.get("data", {}).get("code") == 100:
            authority = data["data"]["authority"]
            redirect_url = f"{ZARINPAL_REDIRECT_URL}{authority}"
            logger.info(f"ZarinPal payment request successful. Authority: {authority}")
            return {
                'success': True,
                'authority': authority,
                'redirect_url': redirect_url,
                'fee': data["data"].get("fee", 0)
            }
        else:
            error_code = data.get("data", {}).get("code", "Unknown")
            error_message = data.get("errors", {}).get("message", "No message")
            logger.error(f"ZarinPal payment request failed. Code: {error_code}, Message: {error_message}")
            return {
                'success': False,
                'error_code': error_code,
                'error_message': error_message
            }

    except requests.exceptions.RequestException as e:
        logger.error(f"Network error during ZarinPal payment request: {e}")
        return {'success': False, 'error': f'Network error: {e}'}
    except Exception as e:
        logger.error(f"Unexpected error during ZarinPal payment request: {e}")
        return {'success': False, 'error': f'Unexpected error: {e}'}


def zarinpal_verify_payment(authority: str, amount_tomans: int) -> Optional[Dict]:
    """
    Verifies a payment with ZarinPal.
    
    Args:
        authority (str): The Authority (transaction ID) received from ZarinPal callback.
        amount_tomans (int): The original payment amount in Tomans.
        
    Returns:
        Optional[Dict]: A dictionary containing the verification result, including
                       RefID on success, or None on failure.
    """
    try:
        if not ZARINPAL_MERCHANT_ID:
            logger.error("ZarinPal Merchant ID is not configured for verification.")
            return None

        payload = {
            "merchant_id": ZARINPAL_MERCHANT_ID,
            "amount": amount_tomans,
            "authority": authority
        }
        headers = {"Content-Type": "application/json"}

        logger.info(f"Sending ZarinPal payment verification for authority {authority}")
        response = requests.post(ZARINPAL_VERIFY_URL, json=payload, headers=headers, timeout=30)
        response.raise_for_status()

        data = response.json()
        logger.debug(f"ZarinPal verification response: {data}")

        if data.get("data", {}).get("code") == 100:
            ref_id = data["data"].get("ref_id")
            fee = data["data"].get("fee", 0)
            logger.info(f"ZarinPal payment verification successful. RefID: {ref_id}")
            return {
                'verified': True,
                'ref_id': ref_id,
                'fee': fee
            }
        else:
            error_code = data.get("data", {}).get("code", "Unknown")
            error_message = data.get("errors", {}).get("message", "No message")
            logger.error(f"ZarinPal payment verification failed. Code: {error_code}, Message: {error_message}")
            return {
                'verified': False,
                'error_code': error_code,
                'error_message': error_message
            }

    except requests.exceptions.RequestException as e:
        logger.error(f"Network error during ZarinPal payment verification: {e}")
        return {'verified': False, 'error': f'Network error: {e}'}
    except Exception as e:
        logger.error(f"Unexpected error during ZarinPal payment verification: {e}")
        return {'verified': False, 'error': f'Unexpected error: {e}'}

# --- NextPay Functions ---

def nextpay_request_payment(amount_tomans: int, description: str, callback_url: str,
                            customer_phone: Optional[str] = None) -> Optional[Dict]:
    """
    Sends a payment request to NextPay.
    
    Args:
        amount_tomans (int): The payment amount in Tomans.
        description (str): A description for the payment.
        callback_url (str): The URL NextPay redirects to after payment.
        customer_phone (str, optional): Customer's phone number.
        
    Returns:
        Optional[Dict]: A dictionary containing the response from NextPay, including
                       trans_id and redirect URL, or None on failure.
    """
    try:
        if not NEXT_PAY_API_KEY:
            logger.error("NextPay API Key is not configured.")
            return None

        # Generate a unique order ID
        order_id = f"order_{uuid.uuid4().hex[:16]}"

        payload = {
            "api_key": NEXT_PAY_API_KEY,
            "amount": amount_tomans,
            "order_id": order_id,
            "callback_uri": callback_url,
        }
        if customer_phone:
            payload["customer_phone"] = customer_phone

        logger.info(f"Sending NextPay payment request for {amount_tomans} Tomans")
        response = requests.post(NEXTPAY_REQUEST_URL, data=payload, timeout=30)
        response.raise_for_status()

        # NextPay often returns data in the response body directly
        response_text = response.text
        logger.debug(f"NextPay request response text: {response_text}")

        # Parse NextPay response (this is highly dependent on their actual format)
        # Example: Looking for specific success indicators in the text response
        if "trans_id" in response_text and "status=1" in response_text:
            # Extract trans_id (this parsing is illustrative, adapt to actual response)
            import re
            match = re.search(r"trans_id=([a-zA-Z0-9_\-]+)", response_text)
            if match:
                trans_id = match.group(1)
                redirect_url = f"{NEXTPAY_REDIRECT_URL}{trans_id}"
                
                logger.info(f"NextPay payment request successful. TransID: {trans_id}")
                return {
                    'success': True,
                    'trans_id': trans_id,
                    'order_id': order_id, # Return order_id for later verification
                    'redirect_url': redirect_url
                }
            else:
                logger.error(f"Could not extract trans_id from NextPay response.")
                return {
                    'success': False,
                    'error': 'Could not extract transaction ID from NextPay response.'
                }
        else:
            # Assume failure based on absence of success indicators
            logger.error(f"NextPay payment request failed. Response: {response_text}")
            return {
                'success': False,
                'error': f'NextPay request failed. Response: {response_text[:100]}...' # Truncate long responses
            }

    except requests.exceptions.RequestException as e:
        logger.error(f"Network error during NextPay payment request: {e}")
        return {'success': False, 'error': f'Network error: {e}'}
    except Exception as e:
        logger.error(f"Unexpected error during NextPay payment request: {e}")
        return {'success': False, 'error': f'Unexpected error: {e}'}


def nextpay_verify_payment(trans_id: str, order_id: str, amount_tomans: int) -> Optional[Dict]:
    """
    Verifies a payment with NextPay.
    
    Args:
        trans_id (str): The trans_id received from NextPay callback.
        order_id (str): The order_id used in the request.
        amount_tomans (int): The original payment amount in Tomans.
        
    Returns:
        Optional[Dict]: A dictionary containing the verification result, or None on failure.
    """
    try:
        if not NEXT_PAY_API_KEY:
            logger.error("NextPay API Key is not configured for verification.")
            return None

        payload = {
            "api_key": NEXT_PAY_API_KEY,
            "trans_id": trans_id,
            "amount": amount_tomans
            # Note: NextPay verification sometimes only requires checking if the callback reached your server
            # with the correct trans_id. The actual financial verification might happen automatically.
            # Consult NextPay docs. For this example, we'll assume a verification API call is needed.
        }

        logger.info(f"Sending NextPay payment verification for trans_id {trans_id}")
        response = requests.post(NEXTPAY_VERIFY_URL, data=payload, timeout=30)
        response.raise_for_status()

        response_text = response.text
        logger.debug(f"NextPay verification response text: {response_text}")

        # Parse NextPay verification response (HIGHLY dependent on their docs)
        # Example: Looking for specific success/failure indicators
        if "OK" in response_text.upper() or "status=1" in response_text:
            # Assume verified. Extract final transaction reference if available.
            final_trans_id = trans_id # Default to original
            # If NextPay provides a different confirmation ID, extract it here
            
            logger.info(f"NextPay payment verification successful.")
            return {
                'verified': True,
                'trans_id': final_trans_id,
                'amount': amount_tomans # Amount is assumed correct if callback reached
            }
        else:
            # Assume verification failed
            logger.error(f"NextPay payment verification failed. Response: {response_text}")
            return {
                'verified': False,
                'error': f'NextPay verification failed. Response: {response_text[:100]}...'
            }

    except requests.exceptions.RequestException as e:
        logger.error(f"Network error during NextPay payment verification: {e}")
        return {'verified': False, 'error': f'Network error: {e}'}
    except Exception as e:
        logger.error(f"Unexpected error during NextPay payment verification: {e}")
        return {'verified': False, 'error': f'Unexpected error: {e}'}

# --- Crypto Payment Functions (Conceptual Placeholder) ---

def crypto_request_payment(amount_crypto: float, currency: str, description: str) -> Optional[Dict]:
    """
    Requests a crypto payment invoice/address.
    Note: This is a conceptual placeholder. Implementation depends entirely on the
    chosen crypto payment processor (e.g., NOWPayments, CoinPayments, custom wallet integration).
    
    Args:
        amount_crypto (float): The amount of cryptocurrency.
        currency (str): The cryptocurrency type (e.g., 'BTC', 'ETH', 'USDT').
        description (str): A description for the payment.
        
    Returns:
        Optional[Dict]: A dictionary containing payment details like invoice ID, address, QR code, etc.
    """
    try:
        logger.info(f"Initiating Crypto payment request for {amount_crypto} {currency}")
        
        # --- Conceptual Steps for Crypto Payment Initiation ---
        # 1. Interact with crypto payment processor API
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
        #    qr_code_data = invoice_data.get('qr_code_data') # Data for generating QR code
        
        # 2. For this placeholder, we'll simulate a successful initiation
        simulated_invoice_id = f"crypto_invoice_{uuid.uuid4().hex[:16]}"
        simulated_payment_address = f"T{uuid.uuid4().hex[:33]}" # Simulate a TRX/USDT address
        simulated_payment_url = f"https://example-crypto-processor.com/invoice/{simulated_invoice_id}"
        simulated_qr_code_data = f"crypto:{currency}?amount={amount_crypto}&address={simulated_payment_address}"
        
        logger.info(f"Crypto payment request successful. Invoice: {simulated_invoice_id}")
        return {
            'success': True,
            'invoice_id': simulated_invoice_id,
            'payment_address': simulated_payment_address,
            'payment_url': simulated_payment_url,
            'qr_code_data': simulated_qr_code_data,
            'currency': currency,
            'amount_crypto': amount_crypto
        }
        
    except Exception as e:
        logger.error(f"Unexpected error during Crypto payment request: {e}")
        return {'success': False, 'error': f'Unexpected error: {e}'}


def crypto_verify_payment(invoice_id: str, expected_amount_crypto: float, currency: str) -> Optional[Dict]:
    """
    Verifies a crypto payment.
    Note: This is a conceptual placeholder. Verification depends on the processor.
    It often involves checking for blockchain confirmations or receiving a webhook/IPN notification.
    
    Args:
        invoice_id (str): The ID of the crypto invoice.
        expected_amount_crypto (float): The expected amount of cryptocurrency.
        currency (str): The cryptocurrency type.
        
    Returns:
        Optional[Dict]: A dictionary containing verification details.
    """
    try:
        logger.info(f"Verifying Crypto payment for invoice {invoice_id}")
        
        # --- Conceptual Steps for Crypto Payment Verification ---
        # 1. Interact with crypto payment processor API to check status
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
        #        return {
        #            'verified': True,
        #            'invoice_id': invoice_id,
        #            'confirmed_amount': confirmed_amount_crypto,
        #            'currency': currency,
        #            'gateway_data': status_data
        #        }
        #    else:
        #        return {
        #            'verified': False,
        #            'error': f"Invoice status is {status_data['status']}"
        #        }
        
        # 2. For this placeholder, we'll simulate a successful verification
        #    based on some condition (e.g., a secret key passed in a webhook)
        #    This is NOT how it works in reality for crypto.
        # For simulation, we'll just return success
        logger.info(f"Crypto payment verification successful for invoice {invoice_id} (simulated).")
        return {
            'verified': True,
            'invoice_id': invoice_id,
            'confirmed_amount': expected_amount_crypto, # Simulate confirmed amount
            'currency': currency
        }
            
    except Exception as e:
        logger.error(f"Unexpected error during Crypto payment verification for invoice {invoice_id}: {e}")
        return {'verified': False, 'error': f'Unexpected error: {e}'}

# --- Helper Functions (if needed) ---

def get_crypto_exchange_rate(currency: str, fiat_currency: str = "IRR") -> Optional[float]:
    """
    Gets the exchange rate for a cryptocurrency to a fiat currency.
    Note: This is a conceptual placeholder. Implementation depends on the exchange rate provider.
    
    Args:
        currency (str): The cryptocurrency (e.g., 'BTC', 'ETH').
        fiat_currency (str): The fiat currency (default: 'IRR').
        
    Returns:
        Optional[float]: The exchange rate, or None on failure.
    """
    # Example: Using a third-party API like CoinGecko, CryptoCompare, etc.
    # This would require an API key and network request.
    # For now, return a placeholder or mock value.
    logger.warning("get_crypto_exchange_rate is a placeholder. Returning mock value.")
    # Mock exchange rates (these are not real!)
    mock_rates = {
        "BTC": {"IRR": 2000000000}, # 2 Billion IRR per BTC
        "ETH": {"IRR": 100000000},  # 100 Million IRR per ETH
        "USDT": {"IRR": 50000}      # 50,000 IRR per USDT
    }
    return mock_rates.get(currency, {}).get(fiat_currency)
