# UserBot/bot.py
# Description: Main file for the user bot
import datetime
import json
import os
import random
import zipfile
from io import BytesIO
from urllib.parse import urlparse

import requests
from pytz import timezone
# Import the new Hiddify API functions
from api import get_user, create_user, update_user, delete_user, get_users, disable_user, enable_user, get_all_configs, get_user_profile
from config import API_PATH, USERS_DB, VERSION, LANG, CLIENT_TOKEN
from UserBot.content import MESSAGES, KEY_MARKUP
from UserBot.markups import *
from UserBot.templates import *
# New imports for enhanced features
from Utils.utils import rial_to_toman, toman_to_rial, user_info, all_configs_settings, expired_users_list, users_to_dict, dict_process, sub_links, txt_to_qr, log_user_activity, select_best_server_for_user, verify_payment_internal, generate_payment_link, record_referral, calculate_referral_commission, validate_coupon, apply_coupon_discount
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import PyTelegramBotAPI
import telebot
from telebot.types import Message, CallbackQuery

# Initialize bot with token
bot = telebot.TeleBot(CLIENT_TOKEN)

# Global dictionaries to store temporary data during multi-step processes
renew_subscription_dict = {}
buy_subscription_dict = {}
increase_wallet_amount = {}

# --- Start Command ---
@bot.message_handler(commands=['start'])
def start(message: Message):
    """Handle the /start command for user bot"""
    # Log user activity
    log_user_activity(message.chat.id, "USER_START", "User started the bot")
    
    # Check if user exists in database, if not, add them
    user = USERS_DB.find_user(telegram_id=message.chat.id)
    if not user:
        status = USERS_DB.add_user(telegram_id=message.chat.id, username=message.from_user.username,
                                   full_name=message.from_user.full_name)
        if not status:
            bot.send_message(message.chat.id, MESSAGES['UNKNOWN_ERROR'])
            return
        # Log new user registration
        log_user_activity(message.chat.id, "USER_REGISTERED", "New user registered")
    else:
        user = user[0]
        # Update user info if it has changed
        USERS_DB.edit_user(telegram_id=message.chat.id, username=message.from_user.username,
                           full_name=message.from_user.full_name)

    # Check if user is banned
    if user and user[0]['banned']:
        bot.send_message(message.chat.id, MESSAGES['BANNED_USER'])
        return

    # Check if force join channel is enabled
    settings = all_configs_settings()
    if settings['force_join_channel'] and settings['channel_id']:
        if not settings['channel_id'].startswith('@'):
            bot.send_message(message.chat.id, MESSAGES['UNKNOWN_ERROR'])
            return
        try:
            user_is_member = bot.get_chat_member(settings['channel_id'], message.chat.id)
            if user_is_member.status in ['left', 'kicked']:
                # User is not a member, send join request
                join_msg = MESSAGES['REQUEST_JOIN_CHANNEL']
                if settings['msg_force_join_channel']:
                    join_msg = settings['msg_force_join_channel']
                bot.send_message(message.chat.id, join_msg,
                                 reply_markup=force_join_channel_markup(settings['channel_id']))
                return
        except telebot.apihelper.ApiException as e:
            # If bot is not admin in the channel or other API errors
            logger.error(f"Error checking channel membership: {e}")

    # Send welcome message
    welcome_msg = MESSAGES['WELCOME']
    if settings['msg_user_start']:
        welcome_msg = settings['msg_user_start']
    bot.send_message(message.chat.id, welcome_msg, reply_markup=main_menu_keyboard_markup(), parse_mode='HTML')
    
    # Send a welcome sticker (optional)
    # bot.send_sticker(message.chat.id, "YOUR_STICKER_ID_HERE")

# --- Callback Query Handler ---
@bot.callback_query_handler(func=lambda call: True)
def callback_query(call: CallbackQuery):
    """Handle all callback queries from inline keyboards"""
    try:
        # Extract data from callback
        data = call.data.split(':')
        key = data[0]
        value = data[1] if len(data) > 1 else None
        item_mode = data[2] if len(data) > 2 else None
        list_mode = data[3] if len(data) > 3 else None
        selected_telegram_id = data[4] if len(data) > 4 else None
        
        # Log user activity
        log_user_activity(call.message.chat.id, "USER_CALLBACK", f"Key: {key}, Value: {value}")
        
        # --- Main Menu Navigation ---
        if key == "main_menu":
            bot.edit_message_text(MESSAGES['WELCOME'], call.message.chat.id, call.message.message_id, reply_markup=main_menu_keyboard_markup())
        
        # --- Subscription Management ---
        elif key == "users_bot_my_subscriptions":
            # Get non-order subscriptions
            non_order_subs = utils.non_order_user_info(call.message.chat.id)
            # Get order subscriptions
            order_subs = utils.order_user_info(call.message.chat.id)
            
            if not non_order_subs and not order_subs:
                bot.send_message(call.message.chat.id, MESSAGES['SUBSCRIPTION_NOT_FOUND'])
                return
            
            # Combine subscriptions
            all_subs = non_order_subs + order_subs
            bot.edit_message_text(KEY_MARKUP['USERS_BOT_SUBSCRIPTIONS_LIST'], call.message.chat.id, call.message.message_id, reply_markup=users_bot_sub_url_user_list_markup(all_subs))
        
        elif key == "users_bot_sub_url_user_list":
            sub_id = value
            # Determine if it's a non-order or order subscription
            # This logic might need adjustment based on how sub_id is structured
            # For now, let's assume non-order subs have UUID as sub_id and order subs have numeric ID
            if sub_id.replace('-', '').isalnum() and len(sub_id) > 10: # Likely a UUID
                subs = utils.non_order_user_info(call.message.chat.id)
                sub_type = "non_order"
            else: # Likely an order ID
                subs = utils.order_user_info(call.message.chat.id)
                sub_type = "order"
            
            target_sub = None
            for sub in subs:
                if str(sub.get('sub_id' if sub_type == "order" else 'uuid')) == sub_id:
                    target_sub = sub
                    break
            
            if not target_sub:
                bot.send_message(call.message.chat.id, MESSAGES['SUBSCRIPTION_NOT_FOUND'])
                return
            
            # Get server info
            server_id = target_sub.get('server_id')
            if not server_id:
                bot.send_message(call.message.chat.id, MESSAGES['UNKNOWN_ERROR'])
                return
            server = USERS_DB.find_server(id=server_id)
            if not server:
                bot.send_message(call.message.chat.id, MESSAGES['UNKNOWN_ERROR'])
                return
            server = server[0]
            
            # Get user info from Hiddify panel using new API
            uuid = target_sub.get('uuid')
            if not uuid:
                bot.send_message(call.message.chat.id, MESSAGES['UNKNOWN_ERROR'])
                return
            
            user_data = user_info(uuid, server)
            if not user_data:
                bot.send_message(call.message.chat.id, MESSAGES['UNKNOWN_ERROR'])
                return
            
            msg = user_info_template(sub_id, server, user_data)
            bot.edit_message_text(msg, call.message.chat.id, call.message.message_id, reply_markup=users_bot_sub_info_markup(uuid))
        
        elif key == "users_bot_sub_info":
            uuid = value
            # Get user info from Hiddify panel using new API
            # We need to find the server for this UUID
            # This might require looking up in the database
            # For now, let's assume we can get it from the user's subscriptions
            # A more robust way would be to store server_id with the subscription
            user_subs = utils.non_order_user_info(call.message.chat.id) + utils.order_user_info(call.message.chat.id)
            target_sub = None
            server = None
            for sub in user_subs:
                if sub.get('uuid') == uuid:
                    target_sub = sub
                    server_id = sub.get('server_id')
                    if server_id:
                        server_data = USERS_DB.find_server(id=server_id)
                        if server_data:
                            server = server_data[0]
                    break
            
            if not target_sub or not server:
                bot.send_message(call.message.chat.id, MESSAGES['UNKNOWN_ERROR'])
                return
            
            user_data = user_info(uuid, server)
            if not user_data:
                bot.send_message(call.message.chat.id, MESSAGES['UNKNOWN_ERROR'])
                return
            
            msg = user_info_template(uuid, server, user_data) # Using uuid as sub_id for now
            bot.edit_message_text(msg, call.message.chat.id, call.message.message_id, reply_markup=users_bot_sub_info_markup(uuid))
        
        # --- Configs ---
        elif key == "users_bot_config_server_info":
            uuid = value
            # Find the subscription and server
            user_subs = utils.non_order_user_info(call.message.chat.id) + utils.order_user_info(call.message.chat.id)
            target_sub = None
            server = None
            for sub in user_subs:
                if sub.get('uuid') == uuid:
                    target_sub = sub
                    server_id = sub.get('server_id')
                    if server_id:
                        server_data = USERS_DB.find_server(id=server_id)
                        if server_data:
                            server = server_data[0]
                    break
            
            if not target_sub or not server:
                bot.send_message(call.message.chat.id, MESSAGES['UNKNOWN_ERROR'])
                return
            
            # Generate subscription links using the new utility function
            links = sub_links(uuid, server_row=server)
            if not links:
                bot.send_message(call.message.chat.id, MESSAGES['UNKNOWN_ERROR'])
                return
            
            msg = configs_template(links)
            bot.edit_message_text(msg, call.message.chat.id, call.message.message_id, reply_markup=users_bot_config_server_info_markup(uuid), parse_mode='HTML')
        
        elif key == "users_bot_config_to_qr":
            uuid = value
            # Find the subscription and server
            user_subs = utils.non_order_user_info(call.message.chat.id) + utils.order_user_info(call.message.chat.id)
            target_sub = None
            server = None
            for sub in user_subs:
                if sub.get('uuid') == uuid:
                    target_sub = sub
                    server_id = sub.get('server_id')
                    if server_id:
                        server_data = USERS_DB.find_server(id=server_id)
                        if server_data:
                            server = server_data[0]
                    break
            
            if not target_sub or not server:
                bot.send_message(call.message.chat.id, MESSAGES['UNKNOWN_ERROR'])
                return
            
            # Generate subscription link
            links = sub_links(uuid, server_row=server)
            if not links:
                bot.send_message(call.message.chat.id, MESSAGES['UNKNOWN_ERROR'])
                return
            sub_link = links.get('sub_link')
            
            if not sub_link:
                bot.send_message(call.message.chat.id, MESSAGES['UNKNOWN_ERROR'])
                return
            
            # Generate QR code
            qr_image = txt_to_qr(sub_link)
            if not qr_image:
                bot.send_message(call.message.chat.id, MESSAGES['UNKNOWN_ERROR'])
                return
            
            # Send QR code
            bot.send_photo(call.message.chat.id, qr_image, caption=MESSAGES['CONFIGS_TO_QR_CAPTION'], reply_markup=users_bot_config_server_info_markup(uuid))
            # Edit the previous message to remove the button press effect
            bot.edit_message_text(MESSAGES['CONFIGS_LIST'], call.message.chat.id, call.message.message_id, reply_markup=users_bot_config_server_info_markup(uuid))
        
        # --- Buy Subscription ---
        elif key == "users_bot_buy_subscription":
            # Check if buy subscription is enabled
            settings = all_configs_settings()
            if not settings['buy_subscription_status']:
                bot.send_message(call.message.chat.id, MESSAGES['FEATUR_UNAVAILABLE'])
                return
            
            # Select best server using load balancing utility
            selected_server = select_best_server_for_user()
            if not selected_server:
                bot.send_message(call.message.chat.id, MESSAGES['SERVER_IS_FULL'])
                return
            
            # Store selected server in a global dict for this user
            buy_subscription_dict[call.message.chat.id] = {'server_id': selected_server['id']}
            
            # Get plans for the selected server
            plans = USERS_DB.find_plan(server_id=selected_server['id'])
            if not plans:
                bot.send_message(call.message.chat.id, MESSAGES['PLANS_NOT_FOUND'])
                return
            
            # Filter active plans
            active_plans = [plan for plan in plans if plan['status']]
            if not active_plans:
                bot.send_message(call.message.chat.id, MESSAGES['PLANS_NOT_FOUND'])
                return
            
            bot.edit_message_text(KEY_MARKUP['USERS_BOT_PLANS_LIST'], call.message.chat.id, call.message.message_id, reply_markup=users_bot_list_plans_markup(active_plans))
        
        elif key == "users_bot_list_plans":
            plan_id = value
            plans = USERS_DB.find_plan(id=plan_id)
            if not plans:
                bot.send_message(call.message.chat.id, MESSAGES['PLAN_NOT_FOUND'])
                return
            plan = plans[0]
            msg = plan_info_template(plan)
            bot.edit_message_text(msg, call.message.chat.id, call.message.message_id, reply_markup=users_bot_plan_info_markup(plan_id))
        
        elif key == "users_bot_plan_info":
            plan_id = value
            # Store plan_id for this user
            if call.message.chat.id not in buy_subscription_dict:
                buy_subscription_dict[call.message.chat.id] = {}
            buy_subscription_dict[call.message.chat.id]['plan_id'] = plan_id
            
            bot.edit_message_text(MESSAGES['BUY_SUBSCRIPTION_CONFIRM'], call.message.chat.id, call.message.message_id, reply_markup=confirm_buy_plan_markup(plan_id))
        
        elif key == "confirm_buy_plan":
            plan_id = value
            # Retrieve stored data
            user_data = buy_subscription_dict.get(call.message.chat.id, {})
            server_id = user_data.get('server_id')
            plan_id_stored = user_data.get('plan_id')
            
            if not server_id or not plan_id_stored or plan_id_stored != plan_id:
                bot.send_message(call.message.chat.id, MESSAGES['UNKNOWN_ERROR'])
                return
            
            # Get plan and server info
            plans = USERS_DB.find_plan(id=plan_id)
            if not plans:
                bot.send_message(call.message.chat.id, MESSAGES['PLAN_NOT_FOUND'])
                return
            plan = plans[0]
            
            servers = USERS_DB.find_server(id=server_id)
            if not servers:
                bot.send_message(call.message.chat.id, MESSAGES['SERVER_NOT_FOUND'])
                return
            server = servers[0]
            
            # Check user balance
            user = USERS_DB.find_user(telegram_id=call.message.chat.id)
            if not user:
                bot.send_message(call.message.chat.id, MESSAGES['UNKNOWN_ERROR'])
                return
            user = user[0]
            user_balance = user['balance']
            
            plan_price = plan['price']
            
            # Check if user has enough balance
            if user_balance < plan_price:
                # Not enough balance, offer to pay difference or use other methods
                needed_amount = plan_price - user_balance
                msg = f"{MESSAGES['NOT_ENOUGH_BALANCE']}\n{MESSAGES['NEEDED_AMOUNT']}: {rial_to_toman(needed_amount)} {MESSAGES['TOMAN']}"
                bot.edit_message_text(msg, call.message.chat.id, call.message.message_id, reply_markup=not_enough_balance_markup(needed_amount))
                return
            else:
                # Enough balance, proceed with purchase from wallet
                bot.edit_message_text(MESSAGES['WAIT'], call.message.chat.id, call.message.message_id)
                
                # Deduct balance
                new_balance = user_balance - plan_price
                USERS_DB.edit_user(telegram_id=call.message.chat.id, balance=new_balance)
                
                # Create user on Hiddify panel using new API
                uuid = create_user(
                    name=f"User_{call.message.chat.id}",
                    package_days=plan['days'],
                    usage_limit_GB=plan['size_gb'],
                    telegram_id=call.message.chat.id,
                    comment=f"Paid by wallet. Plan: {plan['name']}"
                )
                
                if not uuid:
                    # Rollback balance deduction
                    USERS_DB.edit_user(telegram_id=call.message.chat.id, balance=user_balance)
                    bot.send_message(call.message.chat.id, MESSAGES['UNKNOWN_ERROR'])
                    return
                
                # Add order to database
                order_status = USERS_DB.add_order(
                    telegram_id=call.message.chat.id,
                    plan_id=plan['id'],
                    server_id=server['id'],
                    uuid=uuid,
                    price=plan_price
                )
                
                if not order_status:
                    # Rollback: delete user from panel and restore balance
                    delete_user(uuid)
                    USERS_DB.edit_user(telegram_id=call.message.chat.id, balance=user_balance)
                    bot.send_message(call.message.chat.id, MESSAGES['UNKNOWN_ERROR'])
                    return
                
                # Send success message
                bot.edit_message_text(MESSAGES['SUCCESSFUL_PURCHASE'], call.message.chat.id, call.message.message_id, reply_markup=main_menu_keyboard_markup())
                
                # Notify admin (optional)
                try:
                    from config import ADMINS_ID
                    for admin_id in ADMINS_ID:
                        bot.send_message(admin_id, f"{MESSAGES['ADMIN_NOTIFY_NEW_SUB']} {user['full_name']} ({user['telegram_id']}) {MESSAGES['ADMIN_NOTIFY_CONFIRM']}")
                except Exception as e:
                    logger.error(f"Error notifying admin: {e}")
                
                # Clear user data
                if call.message.chat.id in buy_subscription_dict:
                    del buy_subscription_dict[call.message.chat.id]
        
        elif key == "confirm_buy_from_wallet":
            # This is handled in the "confirm_buy_plan" section above when balance is sufficient
            # This callback might be used in other scenarios, but for now, it's redundant
            # We can redirect to the main buy flow
            callback_query(call) # Re-process the call with updated data
        
        # --- Wallet ---
        elif key == "users_bot_wallet":
            user = USERS_DB.find_user(telegram_id=call.message.chat.id)
            if not user:
                bot.send_message(call.message.chat.id, MESSAGES['UNKNOWN_ERROR'])
                return
            user = user[0]
            balance = user['balance']
            msg = wallet_info_template(balance)
            bot.edit_message_text(msg, call.message.chat.id, call.message.message_id, reply_markup=users_bot_wallet_markup())
        
        elif key == "users_bot_balance_increase":
            bot.edit_message_text(MESSAGES['INCREASE_WALLET_BALANCE_AMOUNT'], call.message.chat.id, call.message.message_id, reply_markup=cancel_markup())
            bot.register_next_step_handler(call.message, users_bot_balance_increase_wallet_amount)
        
        elif key == "users_bot_balance_increase_wallet":
            # This might be for a specific payment method, but we'll handle it in the amount input
            bot.edit_message_text(MESSAGES['INCREASE_WALLET_BALANCE_AMOUNT'], call.message.chat.id, call.message.message_id, reply_markup=cancel_markup())
            bot.register_next_step_handler(call.message, users_bot_balance_increase_wallet_amount)
        
        # --- Profile ---
        elif key == "users_bot_my_profile":
            user = USERS_DB.find_user(telegram_id=call.message.chat.id)
            if not user:
                bot.send_message(call.message.chat.id, MESSAGES['UNKNOWN_ERROR'])
                return
            user = user[0]
            # Get user subscriptions count
            non_order_count = len(utils.non_order_user_info(call.message.chat.id))
            order_count = len(utils.order_user_info(call.message.chat.id))
            total_subs = non_order_count + order_count
            
            msg = f"""
{MESSAGES['YOUR_PROFILE']}

{MESSAGES['NAME']}: {user['full_name']}
{MESSAGES['USERNAME']}: @{user['username'] if user['username'] else MESSAGES['NOT_SET']}
{MESSAGES['ACCOUNT_BALANCE']}: {rial_to_toman(user['balance'])} {MESSAGES['TOMAN']}
{MESSAGES['TOTAL_SUBSCRIPTIONS']}: {total_subs}
"""
            bot.edit_message_text(msg, call.message.chat.id, call.message.message_id, reply_markup=users_bot_user_info_markup())
        
        # --- Help and Support ---
        elif key == "users_bot_help":
            settings = all_configs_settings()
            help_msg = MESSAGES['HELP_MESSAGE']
            if settings['msg_help']:
                help_msg = settings['msg_help']
            bot.edit_message_text(help_msg, call.message.chat.id, call.message.message_id, reply_markup=users_bot_help_markup(), parse_mode='HTML')
        
        elif key == "users_bot_faq":
            settings = all_configs_settings()
            faq_msg = MESSAGES['FAQ_MESSAGE']
            if settings['msg_faq']:
                faq_msg = settings['msg_faq']
            bot.edit_message_text(faq_msg, call.message.chat.id, call.message.message_id, reply_markup=users_bot_faq_markup(), parse_mode='HTML')
        
        elif key == "users_bot_support":
            # This could open a ticketing system or show support info
            owner_info_data = utils.owner_info()
            msg = f"""
{MESSAGES['SUPPORT']}

{MESSAGES['SUPPORT_USERNAME']}: {owner_info_data.get('username', '-') if owner_info_data.get('username') else '-'}
"""
            bot.edit_message_text(msg, call.message.chat.id, call.message.message_id, reply_markup=users_bot_support_markup())
        
        # --- Free Test ---
        elif key == "users_bot_free_test":
            settings = all_configs_settings()
            if not settings['test_subscription']:
                bot.send_message(call.message.chat.id, MESSAGES['FEATUR_UNAVAILABLE'])
                return
            
            # Check if user already got a test
            test_subs = USERS_DB.find_test_subscription(telegram_id=call.message.chat.id)
            if test_subs:
                bot.send_message(call.message.chat.id, MESSAGES['ALREADY_RECEIVED_FREE_TEST'])
                return
            
            # Check if server has capacity for test users
            # This is a simplification, you might want to check per-server limits
            # For now, we'll just proceed
            
            # Select best server for test user
            selected_server = select_best_server_for_user()
            if not selected_server:
                bot.send_message(call.message.chat.id, MESSAGES['SERVER_IS_FULL'])
                return
            
            # Create test user on Hiddify panel using new API
            uuid = create_user(
                name=f"TestUser_{call.message.chat.id}",
                package_days=settings['test_sub_days'],
                usage_limit_GB=settings['test_sub_size_gb'],
                telegram_id=call.message.chat.id,
                comment="Free test subscription"
            )
            
            if not uuid:
                bot.send_message(call.message.chat.id, MESSAGES['UNKNOWN_ERROR'])
                return
            
            # Add test subscription to database
            test_status = USERS_DB.add_test_subscription(
                telegram_id=call.message.chat.id,
                uuid=uuid,
                server_id=selected_server['id']
            )
            
            if not test_status:
                # Rollback: delete user from panel
                delete_user(uuid)
                bot.send_message(call.message.chat.id, MESSAGES['UNKNOWN_ERROR'])
                return
            
            # Send success message
            bot.send_message(call.message.chat.id, MESSAGES['GET_FREE_CONFIRMED'], reply_markup=main_menu_keyboard_markup())
            
            # Notify admin (optional)
            try:
                from config import ADMINS_ID
                user = USERS_DB.find_user(telegram_id=call.message.chat.id)
                if user:
                    user = user[0]
                    for admin_id in ADMINS_ID:
                        bot.send_message(admin_id, f"{MESSAGES['ADMIN_NOTIFY_NEW_FREE_TEST']} {user['full_name']} ({user['telegram_id']}) {MESSAGES['ADMIN_NOTIFY_CONFIRM']}")
            except Exception as e:
                logger.error(f"Error notifying admin: {e}")
        
        # --- Renewal Subscription ---
        elif key == "users_bot_renewal_subscription":
            # Check if renewal subscription is enabled
            settings = all_configs_settings()
            if not settings['renewal_subscription_status']:
                bot.send_message(call.message.chat.id, MESSAGES['FEATUR_UNAVAILABLE'])
                return
            
            # Show user's subscriptions to select one for renewal
            non_order_subs = utils.non_order_user_info(call.message.chat.id)
            order_subs = utils.order_user_info(call.message.chat.id)
            
            if not non_order_subs and not order_subs:
                bot.send_message(call.message.chat.id, MESSAGES['SUBSCRIPTION_NOT_FOUND'])
                return
            
            # Combine subscriptions
            all_subs = non_order_subs + order_subs
            bot.edit_message_text(KEY_MARKUP['USERS_BOT_RENEWAL_SUBSCRIPTIONS_LIST'], call.message.chat.id, call.message.message_id, reply_markup=users_bot_sub_url_user_list_markup(all_subs, renewal_mode=True))
        
        elif key == "renewal_subscription":
            uuid = value
            # Store uuid for this user
            renew_subscription_dict[call.message.chat.id] = {'uuid': uuid}
            
            # Find the subscription and server
            user_subs = utils.non_order_user_info(call.message.chat.id) + utils.order_user_info(call.message.chat.id)
            target_sub = None
            server = None
            for sub in user_subs:
                if sub.get('uuid') == uuid:
                    target_sub = sub
                    server_id = sub.get('server_id')
                    if server_id:
                        server_data = USERS_DB.find_server(id=server_id)
                        if server_data:
                            server = server_data[0]
                    break
            
            if not target_sub or not server:
                bot.send_message(call.message.chat.id, MESSAGES['UNKNOWN_ERROR'])
                return
            
            # Get user info from Hiddify panel using new API
            user_data = user_info(uuid, server)
            if not user_data:
                bot.send_message(call.message.chat.id, MESSAGES['UNKNOWN_ERROR'])
                return
            
            # Check renewal conditions based on settings
            if settings['renewal_method'] == 2: # Advanced renewal
                remaining_days = user_data.get('remaining_day', 0)
                remaining_usage = user_data.get('usage', {}).get('remaining_usage_GB', 0)
                if remaining_days > settings['advanced_renewal_days'] and remaining_usage > settings['advanced_renewal_usage']:
                    msg = renewal_unvalable_template(settings)
                    bot.send_message(call.message.chat.id, msg, reply_markup=main_menu_keyboard_markup())
                    return
            
            # Get plans for the server
            plans = USERS_DB.find_plan(server_id=server['id'])
            if not plans:
                bot.send_message(call.message.chat.id, MESSAGES['PLANS_NOT_FOUND'])
                return
            
            # Filter active plans
            active_plans = [plan for plan in plans if plan['status']]
            if not active_plans:
                bot.send_message(call.message.chat.id, MESSAGES['PLANS_NOT_FOUND'])
                return
            
            bot.edit_message_text(KEY_MARKUP['USERS_BOT_RENEWAL_PLANS_LIST'], call.message.chat.id, call.message.message_id, reply_markup=users_bot_list_plans_markup(active_plans, renewal_mode=True, uuid=uuid))
        
        elif key == "users_bot_list_renewal_plans":
            plan_id = value
            uuid = item_mode # item_mode contains uuid in this case
            plans = USERS_DB.find_plan(id=plan_id)
            if not plans:
                bot.send_message(call.message.chat.id, MESSAGES['PLAN_NOT_FOUND'])
                return
            plan = plans[0]
            msg = plan_info_template(plan, header=MESSAGES['RENEWAL_PLAN_INFO_HEADER'])
            bot.edit_message_text(msg, call.message.chat.id, call.message.message_id, reply_markup=confirm_buy_plan_markup(plan_id, renewal=True, uuid=uuid))
        
        elif key == "confirm_renewal_from_wallet":
            plan_id = value.split('_')[0] # Extract plan_id from "plan_id_uuid"
            uuid_with_plan = value
            # Extract uuid (everything after the first underscore)
            uuid = "_".join(value.split('_')[1:]) if '_' in value else ""
            
            # Retrieve stored data
            # For renewal, we should have the uuid stored
            # renew_subscription_dict should contain {'uuid': uuid}
            stored_data = renew_subscription_dict.get(call.message.chat.id, {})
            stored_uuid = stored_data.get('uuid')
            
            # Verify uuid matches
            if stored_uuid != uuid:
                bot.send_message(call.message.chat.id, MESSAGES['UNKNOWN_ERROR'])
                return
            
            # Get plan info
            plans = USERS_DB.find_plan(id=plan_id)
            if not plans:
                bot.send_message(call.message.chat.id, MESSAGES['PLAN_NOT_FOUND'])
                return
            plan = plans[0]
            
            # Get user info from Hiddify panel using new API
            # We need to find the server for this UUID
            user_subs = utils.non_order_user_info(call.message.chat.id) + utils.order_user_info(call.message.chat.id)
            target_sub = None
            server = None
            for sub in user_subs:
                if sub.get('uuid') == uuid:
                    target_sub = sub
                    server_id = sub.get('server_id')
                    if server_id:
                        server_data = USERS_DB.find_server(id=server_id)
                        if server_data:
                            server = server_data[0]
                    break
            
            if not target_sub or not server:
                bot.send_message(call.message.chat.id, MESSAGES['UNKNOWN_ERROR'])
                return
            
            user_data = user_info(uuid, server)
            if not user_data:
                bot.send_message(call.message.chat.id, MESSAGES['UNKNOWN_ERROR'])
                return
            
            # Check user balance
            user = USERS_DB.find_user(telegram_id=call.message.chat.id)
            if not user:
                bot.send_message(call.message.chat.id, MESSAGES['UNKNOWN_ERROR'])
                return
            user = user[0]
            user_balance = user['balance']
            
            plan_price = plan['price']
            
            # Check if user has enough balance
            if user_balance < plan_price:
                # Not enough balance, offer to pay difference or use other methods
                needed_amount = plan_price - user_balance
                msg = f"{MESSAGES['NOT_ENOUGH_BALANCE']}\n{MESSAGES['NEEDED_AMOUNT']}: {rial_to_toman(needed_amount)} {MESSAGES['TOMAN']}"
                bot.edit_message_text(msg, call.message.chat.id, call.message.message_id, reply_markup=not_enough_balance_markup(needed_amount))
                return
            else:
                # Enough balance, proceed with renewal from wallet
                bot.edit_message_text(MESSAGES['WAIT'], call.message.chat.id, call.message.message_id)
                
                # Deduct balance
                new_balance = user_balance - plan_price
                USERS_DB.edit_user(telegram_id=call.message.chat.id, balance=new_balance)
                
                # Renew subscription based on renewal method
                renewal_success = False
                if settings['renewal_method'] == 1: # Default renewal
                    if user_data['remaining_day'] <= 0 or user_data['usage']['remaining_usage_GB'] <= 0:
                        new_usage_limit = plan['size_gb']
                        new_package_days = plan['days']
                        current_usage_GB = 0
                        # Use new API to update user
                        update_status = update_user(
                            uuid,
                            usage_limit_GB=new_usage_limit,
                            package_days=new_package_days,
                            current_usage_GB=current_usage_GB,
                            comment=f"HidyBot:Renewal-{target_sub.get('sub_id', 'N/A')}"
                        )
                    else:
                        new_usage_limit = user_data['usage']['usage_limit_GB'] + plan['size_gb']
                        new_package_days = plan['days'] + (user_data['package_days'] - user_data['remaining_day'])
                        # Use new API to update user
                        update_status = update_user(
                            uuid,
                            usage_limit_GB=new_usage_limit,
                            package_days=new_package_days,
                            comment=f"HidyBot:Renewal-{target_sub.get('sub_id', 'N/A')}"
                        )
                    renewal_success = update_status
                
                elif settings['renewal_method'] == 2: # Advanced renewal
                    new_usage_limit = plan['size_gb']
                    new_package_days = plan['days']
                    current_usage_GB = 0
                    # Use new API to update user
                    update_status = update_user(
                        uuid,
                        usage_limit_GB=new_usage_limit,
                        package_days=new_package_days,
                        current_usage_GB=current_usage_GB,
                        comment=f"HidyBot:Renewal-{target_sub.get('sub_id', 'N/A')}"
                    )
                    renewal_success = update_status
                
                elif settings['renewal_method'] == 3: # Fair renewal
                    if user_data['remaining_day'] <= 0 or user_data['usage']['remaining_usage_GB'] <= 0:
                        new_usage_limit = plan['size_gb']
                        new_package_days = plan['days']
                        current_usage_GB = 0
                        # Use new API to update user
                        update_status = update_user(
                            uuid,
                            usage_limit_GB=new_usage_limit,
                            package_days=new_package_days,
                            current_usage_GB=current_usage_GB,
                            comment=f"HidyBot:Renewal-{target_sub.get('sub_id', 'N/A')}"
                        )
                    else:
                        new_usage_limit = user_data['usage']['usage_limit_GB'] + plan['size_gb']
                        new_package_days = plan['days'] + user_data['package_days']
                        # Use new API to update user
                        update_status = update_user(
                            uuid,
                            usage_limit_GB=new_usage_limit,
                            package_days=new_package_days,
                            comment=f"HidyBot:Renewal-{target_sub.get('sub_id', 'N/A')}"
                        )
                    renewal_success = update_status
                
                if not renewal_success:
                    # Rollback balance deduction
                    USERS_DB.edit_user(telegram_id=call.message.chat.id, balance=user_balance)
                    bot.send_message(call.message.chat.id, MESSAGES['UNKNOWN_ERROR'])
                    return
                
                # Send success message
                bot.edit_message_text(MESSAGES['SUCCESSFUL_RENEWAL'], call.message.chat.id, call.message.message_id, reply_markup=main_menu_keyboard_markup())
                
                # Notify admin (optional)
                try:
                    from config import ADMINS_ID
                    for admin_id in ADMINS_ID:
                        bot.send_message(admin_id, f"{MESSAGES['ADMIN_NOTIFY_NEW_RENEWAL']} {user['full_name']} ({user['telegram_id']}) {MESSAGES['ADMIN_NOTIFY_NEW_RENEWAL_2']}")
                except Exception as e:
                    logger.error(f"Error notifying admin: {e}")
                
                # Clear user data
                if call.message.chat.id in renew_subscription_dict:
                    del renew_subscription_dict[call.message.chat.id]
        
        # --- Settings ---
        elif key == "users_bot_settings_renewal_method":
            # This would show options for renewal method
            # For now, just acknowledge
            bot.answer_callback_query(call.id, "Renewal method settings would be here")
        
        # --- Back Navigation ---
        elif key == "back_to_main":
            bot.edit_message_text(MESSAGES['WELCOME'], call.message.chat.id, call.message.message_id, reply_markup=main_menu_keyboard_markup())
        
        elif key == "back_to_subscriptions_list":
            # Get non-order subscriptions
            non_order_subs = utils.non_order_user_info(call.message.chat.id)
            # Get order subscriptions
            order_subs = utils.order_user_info(call.message.chat.id)
            
            if not non_order_subs and not order_subs:
                bot.send_message(call.message.chat.id, MESSAGES['SUBSCRIPTION_NOT_FOUND'])
                return
            
            # Combine subscriptions
            all_subs = non_order_subs + order_subs
            bot.edit_message_text(KEY_MARKUP['USERS_BOT_SUBSCRIPTIONS_LIST'], call.message.chat.id, call.message.message_id, reply_markup=users_bot_sub_url_user_list_markup(all_subs))
        
        elif key == "back_to_renewal_plans":
            uuid = value
            # Find the subscription and server
            user_subs = utils.non_order_user_info(call.message.chat.id) + utils.order_user_info(call.message.chat.id)
            target_sub = None
            server = None
            for sub in user_subs:
                if sub.get('uuid') == uuid:
                    target_sub = sub
                    server_id = sub.get('server_id')
                    if server_id:
                        server_data = USERS_DB.find_server(id=server_id)
                        if server_data:
                            server = server_data[0]
                    break
            
            if not target_sub or not server:
                bot.send_message(call.message.chat.id, MESSAGES['UNKNOWN_ERROR'])
                return
            
            # Get plans for the server
            plans = USERS_DB.find_plan(server_id=server['id'])
            if not plans:
                bot.send_message(call.message.chat.id, MESSAGES['PLANS_NOT_FOUND'])
                return
            
            # Filter active plans
            active_plans = [plan for plan in plans if plan['status']]
            if not active_plans:
                bot.send_message(call.message.chat.id, MESSAGES['PLANS_NOT_FOUND'])
                return
            
            bot.edit_message_text(KEY_MARKUP['USERS_BOT_RENEWAL_PLANS_LIST'], call.message.chat.id, call.message.message_id, reply_markup=users_bot_list_plans_markup(active_plans, renewal_mode=True, uuid=uuid))
        
        # --- New Features Integration ---
        # --- Online Payment Gateway Integration (Placeholder) ---
        elif key == "online_payment_gateway":
            # Show options for online payment
            amount = value # Assuming value contains the amount to pay
            if not amount or not amount.isdigit():
                bot.send_message(call.message.chat.id, MESSAGES['UNKNOWN_ERROR'])
                return
            amount = int(amount)
            
            # Generate payment link using utility function
            payment_link = generate_payment_link(amount, call.message.chat.id, "Wallet Top-up")
            if not payment_link:
                bot.send_message(call.message.chat.id, MESSAGES['UNKNOWN_ERROR'])
                return
            
            # Store payment info in DB (simplified)
            # In a real implementation, you'd store more details and handle callbacks
            payment_status = USERS_DB.add_payment(
                telegram_id=call.message.chat.id,
                amount=amount,
                authority="TEMP_AUTH", # This would be from the payment gateway
                payment_method="online" # or specific gateway name
            )
            
            if not payment_status:
                bot.send_message(call.message.chat.id, MESSAGES['UNKNOWN_ERROR'])
                return
            
            msg = f"""
{MESSAGES['ONLINE_PAYMENT_REQUEST']}

{MESSAGES['AMOUNT']}: {rial_to_toman(amount)} {MESSAGES['TOMAN']}

{MESSAGES['CLICK_TO_PAY']}:
"""
            bot.edit_message_text(msg, call.message.chat.id, call.message.message_id, reply_markup=online_payment_markup(payment_link))
        
        # --- Affiliate/Referral System ---
        elif key == "affiliate_system":
            # Show referral link and stats
            # Referral link would be something like: https://t.me/YourBotUsername?start=ref_{user_id}
            from config import CLIENT_TOKEN # Assuming bot username is somehow accessible or hardcoded
            # This is a simplification. You might need to get the bot username dynamically
            bot_username = "YourBotUsername" # Replace with actual bot username
            referral_link = f"https://t.me/{bot_username}?start=ref_{call.message.chat.id}"
            
            # Get referral stats
            # This would require DB queries to count referrals and calculate commission
            referral_count = 0 # Get from DB
            earned_commission = 0.0 # Get from DB
            
            msg = f"""
{MESSAGES['AFFILIATE_SYSTEM_HEADER']}

{MESSAGES['YOUR_REFERRAL_LINK']}:
<code>{referral_link}</code>

{MESSAGES['REFERRALS_COUNT']}: {referral_count}
{MESSAGES['EARNED_COMMISSION']}: {earned_commission} {MESSAGES['TOMAN']}
"""
            bot.edit_message_text(msg, call.message.chat.id, call.message.message_id, reply_markup=affiliate_system_markup(), parse_mode='HTML')
        
        # --- Coupon Code Application (Placeholder) ---
        elif key == "apply_coupon":
            bot.send_message(call.message.chat.id, MESSAGES['ENTER_COUPON_CODE'], reply_markup=cancel_markup())
            bot.register_next_step_handler(call.message, apply_coupon_code)
        
        else:
            bot.answer_callback_query(call.id, MESSAGES['ERROR_INVALID_COMMAND'])

    except Exception as e:
        logger.error(f"Error in callback_query: {e}")
        bot.send_message(call.message.chat.id, MESSAGES['UNKNOWN_ERROR'])

# --- Message Handlers ---
@bot.message_handler(func=lambda message: True)
def handle_all_messages(message: Message):
    """Handle all text messages that are not commands or part of a conversation flow"""
    # If the message is a command, it should be handled by command handlers
    if message.text and message.text.startswith('/'):
        # Handle referral links in start command
        if message.text.startswith('/start ref_'):
            try:
                referrer_id = int(message.text.split('_')[1])
                if referrer_id != message.chat.id: # Prevent self-referral
                    # Record referral
                    record_referral(referrer_id, message.chat.id)
                    # Optionally reward referrer
                    # This would depend on your referral policy
                    bot.send_message(message.chat.id, MESSAGES['REFERRAL_SUCCESS'])
                else:
                    bot.send_message(message.chat.id, MESSAGES['SELF_REFERRAL_ERROR'])
            except (ValueError, IndexError):
                pass # Invalid referral link, proceed normally
            # Then call start function
            start(message)
            return
        else:
            # Other commands are handled by @bot.message_handler(commands=[...])
            # If a command is not defined, this will catch it
            bot.send_message(message.chat.id, MESSAGES['ERROR_INVALID_COMMAND'])
            return

    # If the message is not part of a specific flow, show main menu
    bot.send_message(message.chat.id, MESSAGES['WELCOME'], reply_markup=main_menu_keyboard_markup())

# --- Helper Functions (Wallet Balance Increase) ---
def users_bot_balance_increase_wallet_amount(message: Message):
    """Step 1 of increasing wallet balance: Get amount"""
    if is_it_cancel(message):
        return
    if not is_it_digit(message, markup=cancel_markup()):
        bot.register_next_step_handler(message, users_bot_balance_increase_wallet_amount)
        return
    
    amount = int(message.text)
    # Store amount for this user
    increase_wallet_amount[message.chat.id] = amount
    
    # Offer payment methods
    # For now, we'll offer online payment and card payment
    # Card payment would show owner info
    settings = all_configs_settings()
    owner_info_data = utils.owner_info()
    
    msg = f"""
{MESSAGES['INCREASE_WALLET_BALANCE_CONFIRMATION']}

{MESSAGES['AMOUNT']}: {rial_to_toman(amount)} {MESSAGES['TOMAN']}

{MESSAGES['SELECT_PAYMENT_METHOD']}:
"""
    bot.send_message(message.chat.id, msg, reply_markup=users_bot_balance_increase_markup(amount))

def apply_coupon_code(message: Message):
    """Apply a coupon code to a payment or purchase"""
    if is_it_cancel(message):
        return
    
    coupon_code = message.text.strip()
    # Validate coupon using utility function
    coupon_data = validate_coupon(coupon_code)
    
    if not coupon_data or not coupon_data.get('valid'):
        bot.send_message(message.chat.id, MESSAGES['INVALID_COUPON'], reply_markup=main_menu_keyboard_markup())
        return
    
    # Apply coupon (this is a placeholder, logic depends on where it's applied)
    # For example, if it's for wallet top-up:
    user_amount = increase_wallet_amount.get(message.chat.id, 0)
    if user_amount > 0:
        discounted_amount = apply_coupon_discount(user_amount, coupon_data)
        # Update the stored amount
        increase_wallet_amount[message.chat.id] = discounted_amount
        bot.send_message(message.chat.id, f"{MESSAGES['COUPON_APPLIED']}. {MESSAGES['NEW_AMOUNT']}: {rial_to_toman(discounted_amount)} {MESSAGES['TOMAN']}", reply_markup=main_menu_keyboard_markup())
    else:
        bot.send_message(message.chat.id, MESSAGES['COUPON_APPLIED'], reply_markup=main_menu_keyboard_markup())

# --- Helper Functions (Utility) ---
def is_it_cancel(message: Message) -> bool:
    """Check if the message is a cancel command"""
    if message.text == KEY_MARKUP['CANCEL']:
        bot.send_message(message.chat.id, MESSAGES['CANCELED'], reply_markup=main_menu_keyboard_markup())
        # Clear any temporary data for this user
        if message.chat.id in buy_subscription_dict:
            del buy_subscription_dict[message.chat.id]
        if message.chat.id in renew_subscription_dict:
            del renew_subscription_dict[message.chat.id]
        if message.chat.id in increase_wallet_amount:
            del increase_wallet_amount[message.chat.id]
        return True
    return False

def is_it_digit(message: Message, allow_float=False, markup=None) -> bool:
    """Check if the message text is a digit (or float if allowed)"""
    if not message.text:
        bot.send_message(message.chat.id, MESSAGES['ERROR_INVALID_NUMBER'], reply_markup=markup or main_menu_keyboard_markup())
        return False
    
    try:
        if allow_float:
            float(message.text)
        else:
            int(message.text)
        return True
    except ValueError:
        bot.send_message(message.chat.id, MESSAGES['ERROR_INVALID_NUMBER'], reply_markup=markup or main_menu_keyboard_markup())
        return False

# --- Start the bot ---
def start():
    """Start the user bot"""
    logger.info("Starting User Bot...")
    try:
        bot.remove_webhook() # Remove any existing webhook
    except:
        pass
    bot.polling(none_stop=True)

if __name__ == "__main__":
    start()
