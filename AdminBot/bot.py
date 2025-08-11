# AdminBot/bot.py
# Description: Main file for the admin bot
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
from api import get_user, create_user, update_user, delete_user, get_users, disable_user, enable_user, get_panel_info, get_admin_info, get_server_status, update_user_usage, ping_panel
from config import API_PATH, USERS_DB, VERSION, LANG, ADMINS_ID
from AdminBot.content import MESSAGES, KEY_MARKUP
from AdminBot.markups import *
from AdminBot.templates import *
# New imports for enhanced features
from Utils.utils import rial_to_toman, toman_to_rial, user_info, all_configs_settings, backup_json_bot, restore_json_bot, expired_users_list, users_to_dict, dict_process, sub_links, txt_to_qr, search_user_by_name, log_user_activity, select_best_server_for_user, get_user_statistics, get_order_statistics, verify_payment_internal, generate_payment_link, record_referral, calculate_referral_commission, validate_coupon, apply_coupon_discount
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import PyTelegramBotAPI
import telebot
from telebot.types import Message, CallbackQuery

# Initialize bot with token
bot = telebot.TeleBot(ADMINS_ID[0]) # Assuming first admin ID is used for admin bot token

# ... (rest of the imports and initial variable definitions remain the same) ...

# --- Main Menu Command ---
@bot.message_handler(commands=['start'])
def start(message: Message):
    """Handle the /start command for admin bot"""
    if message.chat.id not in ADMINS_ID:
        bot.send_message(message.chat.id, MESSAGES['ERROR_ACCESS_DENIED'])
        return

    # Log admin activity
    log_user_activity(message.chat.id, "ADMIN_LOGIN", "Admin accessed the bot")
    
    bot.send_message(message.chat.id, MESSAGES['WELCOME_ADMIN'], reply_markup=main_menu_keyboard_markup())
    
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
        
        # Log admin activity
        log_user_activity(call.message.chat.id, "ADMIN_CALLBACK", f"Key: {key}, Value: {value}")
        
        # --- Main Menu Navigation ---
        if key == "main_menu":
            bot.edit_message_text(MESSAGES['WELCOME_ADMIN'], call.message.chat.id, call.message.message_id, reply_markup=main_menu_keyboard_markup())
        
        # --- Users Management ---
        elif key == "users_management":
            bot.edit_message_text(KEY_MARKUP['USERS_MANAGEMENT'], call.message.chat.id, call.message.message_id, reply_markup=users_management_markup())
        
        elif key == "users_list":
            users = USERS_DB.select_users()
            if not users:
                bot.send_message(call.message.chat.id, MESSAGES['ERROR_USER_NOT_FOUND'])
                return
            # Process users with new API data (if needed)
            # users = dict_process(None, users_to_dict(users)) # Adjust URL if needed
            bot.edit_message_text(KEY_MARKUP['USERS_LIST'], call.message.chat.id, call.message.message_id, reply_markup=users_list_markup(users))
        
        elif key == "add_user":
            # Reset add_user_data
            global add_user_data
            add_user_data = {}
            bot.send_message(call.message.chat.id, MESSAGES['USERS_ADD_NAME'], reply_markup=while_edit_user_markup())
            bot.register_next_step_handler(call.message, add_user_name)
        
        elif key == "search_user":
            bot.send_message(call.message.chat.id, MESSAGES['USERS_SEARCH_CONTACT'], reply_markup=while_edit_user_markup())
            bot.register_next_step_handler(call.message, search_user)
        
        elif key == "edit_user":
            users = USERS_DB.select_users()
            if not users:
                bot.send_message(call.message.chat.id, MESSAGES['ERROR_USER_NOT_FOUND'])
                return
            bot.edit_message_text(KEY_MARKUP['USERS_LIST'], call.message.chat.id, call.message.message_id, reply_markup=users_list_markup(users, edit_mode=True))
        
        elif key == "user_item":
            if item_mode == "User":
                users = USERS_DB.find_user(telegram_id=int(value))
                if not users:
                    bot.send_message(call.message.chat.id, MESSAGES['ERROR_USER_NOT_FOUND'])
                    return
                user = users[0]
                msg = user_info_template(user['telegram_id'], user)
                bot.edit_message_text(msg, call.message.chat.id, call.message.message_id, reply_markup=user_info_markup(user['telegram_id']))
            elif item_mode == "Edit":
                users = USERS_DB.find_user(telegram_id=int(value))
                if not users:
                    bot.send_message(call.message.chat.id, MESSAGES['ERROR_USER_NOT_FOUND'])
                    return
                user = users[0]
                msg = user_info_template(user['telegram_id'], user, header=MESSAGES['USERS_EDIT_HEADER'])
                bot.edit_message_text(msg, call.message.chat.id, call.message.message_id, reply_markup=edit_user_markup(user['telegram_id']))
        
        elif key == "user_item_next":
            if list_mode == "Users_List":
                users = USERS_DB.select_users()
                if not users:
                    bot.send_message(call.message.chat.id, MESSAGES['ERROR_USER_NOT_FOUND'])
                    return
                bot.edit_message_text(KEY_MARKUP['USERS_LIST'], call.message.chat.id, call.message.message_id, reply_markup=users_list_markup(users))
            elif list_mode == "Search_User":
                # Implement search user list pagination if needed
                pass
        
        # --- User Actions (Edit, Delete, etc.) ---
        elif key == "user_edit_name":
            bot.send_message(call.message.chat.id, MESSAGES['USERS_EDIT_NAME'], reply_markup=while_edit_user_markup())
            bot.register_next_step_handler(call.message, edit_user_name, value)
        
        elif key == "user_edit_limit":
            bot.send_message(call.message.chat.id, MESSAGES['USERS_EDIT_LIMIT'], reply_markup=while_edit_user_markup())
            bot.register_next_step_handler(call.message, edit_user_limit, value)
        
        elif key == "user_edit_days":
            bot.send_message(call.message.chat.id, MESSAGES['USERS_EDIT_DAYS'], reply_markup=while_edit_user_markup())
            bot.register_next_step_handler(call.message, edit_user_days, value)
        
        elif key == "confirm_delete_user":
            bot.edit_message_text(MESSAGES['USERS_ASK_DELETE'], call.message.chat.id, call.message.message_id, reply_markup=confirm_delete_user_markup(value))
        
        elif key == "delete_user":
            # Delete user from Hiddify panel using new API
            users = USERS_DB.find_user(telegram_id=int(value))
            if not users:
                bot.send_message(call.message.chat.id, MESSAGES['ERROR_USER_NOT_FOUND'])
                return
            user = users[0]
            uuid = user.get('uuid') # Assuming UUID is stored in user data
            
            if uuid:
                delete_status = delete_user(uuid)
                if not delete_status:
                    bot.send_message(call.message.chat.id, MESSAGES['ERROR_UNKNOWN'])
                    return
            
            # Delete user from local database
            status = USERS_DB.delete_user(telegram_id=int(value))
            if not status:
                bot.send_message(call.message.chat.id, MESSAGES['ERROR_UNKNOWN'])
                return
            
            bot.edit_message_text(MESSAGES['SUCCESS_USER_DELETED'], call.message.chat.id, call.message.message_id, reply_markup=main_menu_keyboard_markup())
        
        # --- Servers Management ---
        elif key == "servers_management":
            servers = USERS_DB.select_servers()
            bot.edit_message_text(KEY_MARKUP['SERVERS_MANAGEMENT'], call.message.chat.id, call.message.message_id, reply_markup=servers_management_markup(servers))
        
        elif key == "add_server":
            # Reset add_server_data
            global add_server_data
            add_server_data = {}
            bot.send_message(call.message.chat.id, MESSAGES['SERVERS_ADD_NAME'], reply_markup=while_edit_user_markup())
            bot.register_next_step_handler(call.message, add_server_name)
        
        elif key == "edit_server":
            servers = USERS_DB.select_servers()
            if not servers:
                bot.send_message(call.message.chat.id, MESSAGES['ERROR_SERVER_NOT_FOUND'])
                return
            bot.edit_message_text(KEY_MARKUP['SERVERS_LIST'], call.message.chat.id, call.message.message_id, reply_markup=servers_list_markup(servers, edit_mode=True))
        
        elif key == "server_item":
            if item_mode == "Server":
                servers = USERS_DB.find_server(id=int(value))
                if not servers:
                    bot.send_message(call.message.chat.id, MESSAGES['ERROR_SERVER_NOT_FOUND'])
                    return
                server = servers[0]
                msg = server_info_template(server)
                bot.edit_message_text(msg, call.message.chat.id, call.message.message_id, reply_markup=server_info_markup(server['id']))
            elif item_mode == "Edit":
                servers = USERS_DB.find_server(id=int(value))
                if not servers:
                    bot.send_message(call.message.chat.id, MESSAGES['ERROR_SERVER_NOT_FOUND'])
                    return
                server = servers[0]
                msg = server_info_template(server, header=MESSAGES['SERVERS_EDIT_HEADER'])
                bot.edit_message_text(msg, call.message.chat.id, call.message.message_id, reply_markup=edit_server_markup(server['id']))
            elif item_mode == "Plans":
                plans_list = []
                plans = USERS_DB.select_plans()
                if plans:
                    for plan in plans:
                        if plan['status']:
                            if plan['server_id'] == int(value):
                                plans_list.append(plan)
                plans_markup = plans_list_markup(plans_list, value)
                bot.edit_message_text(KEY_MARKUP['PLANS_LIST'], call.message.chat.id, call.message.message_id, reply_markup=plans_markup)
        
        # --- Server Actions (Edit, Delete, etc.) ---
        elif key == "server_edit_title":
            bot.send_message(call.message.chat.id, MESSAGES['SERVERS_EDIT_TITLE'], reply_markup=while_edit_user_markup())
            bot.register_next_step_handler(call.message, edit_server_title, value)
        
        elif key == "server_edit_url":
            bot.send_message(call.message.chat.id, MESSAGES['SERVERS_EDIT_URL'], reply_markup=while_edit_user_markup())
            bot.register_next_step_handler(call.message, edit_server_url, value)
        
        elif key == "server_edit_user_limit":
            bot.send_message(call.message.chat.id, MESSAGES['SERVERS_EDIT_USER_LIMIT'], reply_markup=while_edit_user_markup())
            bot.register_next_step_handler(call.message, edit_server_user_limit, value)
        
        elif key == "confirm_delete_server":
            bot.edit_message_text(MESSAGES['SERVERS_ASK_DELETE'], call.message.chat.id, call.message.message_id, reply_markup=confirm_delete_server_markup(value))
        
        elif key == "delete_server":
            status = USERS_DB.delete_server(id=int(value))
            if not status:
                bot.send_message(call.message.chat.id, MESSAGES['ERROR_UNKNOWN'])
                return
            bot.edit_message_text(MESSAGES['SUCCESS_SERVER_DELETED'], call.message.chat.id, call.message.message_id, reply_markup=main_menu_keyboard_markup())
        
        # --- Plans Management ---
        elif key == "plans_management":
            plans = USERS_DB.select_plans()
            bot.edit_message_text(KEY_MARKUP['PLANS_MANAGEMENT'], call.message.chat.id, call.message.message_id, reply_markup=plans_management_markup(plans))
        
        elif key == "add_plan":
            # Reset add_plan_data
            global add_plan_data
            add_plan_data = {}
            servers = USERS_DB.select_servers()
            if not servers:
                bot.send_message(call.message.chat.id, MESSAGES['ERROR_SERVER_NOT_FOUND'])
                return
            bot.send_message(call.message.chat.id, MESSAGES['PLANS_ADD_SERVER'], reply_markup=while_edit_user_markup())
            bot.register_next_step_handler(call.message, add_plan_server, servers)
        
        elif key == "edit_plan":
            plans = USERS_DB.select_plans()
            if not plans:
                bot.send_message(call.message.chat.id, MESSAGES['ERROR_PLAN_NOT_FOUND'])
                return
            bot.edit_message_text(KEY_MARKUP['PLANS_LIST'], call.message.chat.id, call.message.message_id, reply_markup=plans_list_markup(plans, edit_mode=True))
        
        elif key == "plan_item":
            if item_mode == "Plan":
                plans = USERS_DB.find_plan(id=int(value))
                if not plans:
                    bot.send_message(call.message.chat.id, MESSAGES['ERROR_PLAN_NOT_FOUND'])
                    return
                plan = plans[0]
                msg = plan_info_template(plan)
                bot.edit_message_text(msg, call.message.chat.id, call.message.message_id, reply_markup=plan_info_markup(plan['id']))
            elif item_mode == "Edit":
                plans = USERS_DB.find_plan(id=int(value))
                if not plans:
                    bot.send_message(call.message.chat.id, MESSAGES['ERROR_PLAN_NOT_FOUND'])
                    return
                plan = plans[0]
                msg = plan_info_template(plan, header=MESSAGES['PLANS_EDIT_HEADER'])
                bot.edit_message_text(msg, call.message.chat.id, call.message.message_id, reply_markup=edit_plan_markup(plan['id']))
        
        # --- Plan Actions (Edit, Delete, etc.) ---
        elif key == "plan_edit_name":
            bot.send_message(call.message.chat.id, MESSAGES['PLANS_EDIT_NAME'], reply_markup=while_edit_user_markup())
            bot.register_next_step_handler(call.message, edit_plan_name, value)
        
        elif key == "plan_edit_size":
            bot.send_message(call.message.chat.id, MESSAGES['PLANS_EDIT_SIZE'], reply_markup=while_edit_user_markup())
            bot.register_next_step_handler(call.message, edit_plan_size, value)
        
        elif key == "plan_edit_days":
            bot.send_message(call.message.chat.id, MESSAGES['PLANS_EDIT_DAYS'], reply_markup=while_edit_user_markup())
            bot.register_next_step_handler(call.message, edit_plan_days, value)
        
        elif key == "plan_edit_price":
            bot.send_message(call.message.chat.id, MESSAGES['PLANS_EDIT_PRICE'], reply_markup=while_edit_user_markup())
            bot.register_next_step_handler(call.message, edit_plan_price, value)
        
        elif key == "confirm_delete_plan":
            bot.edit_message_text(MESSAGES['PLANS_ASK_DELETE'], call.message.chat.id, call.message.message_id, reply_markup=confirm_delete_plan_markup(value))
        
        elif key == "delete_plan":
            status = USERS_DB.delete_plan(id=int(value))
            if not status:
                bot.send_message(call.message.chat.id, MESSAGES['ERROR_UNKNOWN'])
                return
            bot.edit_message_text(MESSAGES['SUCCESS_PLAN_DELETED'], call.message.chat.id, call.message.message_id, reply_markup=main_menu_keyboard_markup())
        
        # --- Orders Management ---
        elif key == "orders_management":
            orders = USERS_DB.select_orders()
            bot.edit_message_text(KEY_MARKUP['ORDERS_MANAGEMENT'], call.message.chat.id, call.message.message_id, reply_markup=orders_management_markup(orders))
        
        elif key == "orders_list":
            orders = USERS_DB.select_orders()
            if not orders:
                bot.send_message(call.message.chat.id, MESSAGES['ERROR_ORDER_NOT_FOUND'])
                return
            bot.edit_message_text(KEY_MARKUP['ORDERS_LIST'], call.message.chat.id, call.message.message_id, reply_markup=orders_list_markup(orders))
        
        elif key == "search_order":
            bot.send_message(call.message.chat.id, MESSAGES['ORDERS_SEARCH'], reply_markup=while_edit_user_markup())
            bot.register_next_step_handler(call.message, search_order)
        
        elif key == "order_item":
            orders = USERS_DB.find_order(id=int(value))
            if not orders:
                bot.send_message(call.message.chat.id, MESSAGES['ERROR_ORDER_NOT_FOUND'])
                return
            order = orders[0]
            plans = USERS_DB.find_plan(id=order['plan_id'])
            if not plans:
                bot.send_message(call.message.chat.id, MESSAGES['ERROR_PLAN_NOT_FOUND'])
                return
            plan = plans[0]
            users = USERS_DB.find_user(telegram_id=order['telegram_id'])
            if not users:
                bot.send_message(call.message.chat.id, MESSAGES['ERROR_USER_NOT_FOUND'])
                return
            user = users[0]
            servers = USERS_DB.find_server(id=plan['server_id'])
            if not servers:
                bot.send_message(call.message.chat.id, MESSAGES['ERROR_SERVER_NOT_FOUND'])
                return
            server = servers[0]
            msg = bot_orders_info_template(order, plan, user, server)
            bot.edit_message_text(msg, call.message.chat.id, call.message.message_id, reply_markup=bot_order_info_markup(order['id']))
        
        # --- Payments Management ---
        elif key == "payments_management":
            payments = USERS_DB.select_payments()
            bot.edit_message_text(KEY_MARKUP['PAYMENTS_MANAGEMENT'], call.message.chat.id, call.message.message_id, reply_markup=payments_management_markup(payments))
        
        elif key == "payments_list":
            payments = USERS_DB.select_payments()
            if not payments:
                bot.send_message(call.message.chat.id, MESSAGES['ERROR_PAYMENT_NOT_FOUND'])
                return
            bot.edit_message_text(KEY_MARKUP['PAYMENTS_LIST'], call.message.chat.id, call.message.message_id, reply_markup=payments_list_markup(payments))
        
        elif key == "search_payment":
            bot.send_message(call.message.chat.id, MESSAGES['PAYMENTS_SEARCH'], reply_markup=while_edit_user_markup())
            bot.register_next_step_handler(call.message, search_payment)
        
        elif key == "payment_item":
            payments = USERS_DB.find_payment(id=int(value))
            if not payments:
                bot.send_message(call.message.chat.id, MESSAGES['ERROR_PAYMENT_NOT_FOUND'])
                return
            payment = payments[0]
            user_data = USERS_DB.find_user(telegram_id=payment['telegram_id'])
            if not user_data:
                bot.send_message(call.message.chat.id, MESSAGES['ERROR_USER_NOT_FOUND'])
                return
            user_data = user_data[0]
            msg = bot_payment_info_template(payment, user_data)
            photo_path = payment['photo_path']
            if os.path.exists(photo_path):
                bot.send_photo(call.message.chat.id, photo=open(photo_path, 'rb'), caption=msg, reply_markup=change_status_payment_by_admin(payment['id']))
            else:
                bot.send_message(call.message.chat.id, msg, reply_markup=change_status_payment_by_admin(payment['id']))
        
        # --- Payment Status Change ---
        elif key == "change_status_payment":
            payment_id = int(value)
            payments = USERS_DB.find_payment(id=payment_id)
            if not payments:
                bot.send_message(call.message.chat.id, MESSAGES['ERROR_PAYMENT_NOT_FOUND'])
                return
            payment = payments[0]
            bot.edit_message_text(MESSAGES['PAYMENTS_ASK_CHANGE_STATUS'], call.message.chat.id, call.message.message_id, reply_markup=confirm_change_status_payment_by_admin(payment_id))
        
        elif key == "confirm_change_status_payment":
            payment_id = int(value)
            payments = USERS_DB.find_payment(id=payment_id)
            if not payments:
                bot.send_message(call.message.chat.id, MESSAGES['ERROR_PAYMENT_NOT_FOUND'])
                return
            payment = payments[0]
            
            # Update payment status in database
            new_status = True if item_mode == "Confirm" else False
            status = USERS_DB.edit_payment(id=payment_id, approved=new_status)
            if not status:
                bot.send_message(call.message.chat.id, MESSAGES['ERROR_UNKNOWN'])
                return
            
            # If payment is confirmed, update user balance or create subscription
            if new_status:
                user_data = USERS_DB.find_user(telegram_id=payment['telegram_id'])
                if user_data:
                    user = user_data[0]
                    # Update user balance
                    new_balance = user['balance'] + payment['payment_amount']
                    USERS_DB.edit_user(telegram_id=payment['telegram_id'], balance=new_balance)
                    
                    # Log successful payment
                    log_user_activity(payment['telegram_id'], "PAYMENT_CONFIRMED", f"Payment ID: {payment_id}, Amount: {payment['payment_amount']}")
                    
                    # Notify user (optional)
                    try:
                        # Assuming user_bot is accessible or you have a way to send messages to users
                        # from AdminBot.content import user_bot
                        # user_bot().send_message(payment['telegram_id'], MESSAGES['PAYMENT_CONFIRMED_USER'])
                        pass
                    except Exception as e:
                        logger.error(f"Error notifying user {payment['telegram_id']} about payment confirmation: {e}")
            
            bot.edit_message_text(MESSAGES['SUCCESS_PAYMENT_STATUS_CHANGED'], call.message.chat.id, call.message.message_id, reply_markup=main_menu_keyboard_markup())
        
        # --- Users Bot Management ---
        elif key == "users_bot_management":
            settings = all_configs_settings()
            bot.edit_message_text(KEY_MARKUP['USERS_BOT_MANAGEMENT'], call.message.chat.id, call.message.message_id, reply_markup=users_bot_management_markup(settings))
        
        elif key == "users_bot_settings":
            settings = all_configs_settings()
            bot.edit_message_text(KEY_MARKUP['USERS_BOT_SETTINGS'], call.message.chat.id, call.message.message_id, reply_markup=users_bot_management_settings_markup(settings))
        
        elif key == "users_bot_settings_test_sub":
            settings = all_configs_settings()
            bot.edit_message_text(KEY_MARKUP['USERS_BOT_SETTINGS_TEST_SUB'], call.message.chat.id, call.message.message_id, reply_markup=users_bot_management_settings_test_sub_markup(settings))
        
        elif key == "users_bot_settings_notif_reminder":
            settings = all_configs_settings()
            bot.edit_message_text(KEY_MARKUP['USERS_BOT_SETTINGS_NOTIF_REMINDER'], call.message.chat.id, call.message.message_id, reply_markup=users_bot_management_settings_notif_reminder_markup(settings))
        
        elif key == "users_bot_settings_renewal_method":
            settings = all_configs_settings()
            bot.edit_message_text(KEY_MARKUP['USERS_BOT_SETTINGS_RENEWAL_METHOD'], call.message.chat.id, call.message.message_id, reply_markup=users_bot_management_settings_renewal_method_markup(settings))
        
        elif key == "users_bot_settings_visible_sub":
            settings = all_configs_settings()
            bot.edit_message_text(KEY_MARKUP['USERS_BOT_SETTINGS_VISIBLE_SUB'], call.message.chat.id, call.message.message_id, reply_markup=users_bot_management_settings_visible_sub_markup(settings))
        
        elif key == "users_bot_settings_panel_manual":
            settings = all_configs_settings()
            bot.edit_message_text(KEY_MARKUP['USERS_BOT_SETTINGS_PANEL_MANUAL'], call.message.chat.id, call.message.message_id, reply_markup=users_bot_management_settings_panel_manual_markup(settings))
        
        elif key == "users_bot_edit_owner_info":
            owner_info_data = USERS_DB.select_str_config()
            bot.edit_message_text(KEY_MARKUP['USERS_BOT_EDIT_OWNER_INFO'], call.message.chat.id, call.message.message_id, reply_markup=users_bot_edit_owner_info_markup(owner_info_data))
        
        # --- Owner Info Editing ---
        elif key == "users_bot_owner_info_edit_username":
            bot.send_message(call.message.chat.id, MESSAGES['USERS_BOT_OWNER_INFO_EDIT_USERNAME'], reply_markup=while_edit_user_markup())
            bot.register_next_step_handler(call.message, users_bot_owner_info_edit_username)
        
        elif key == "users_bot_owner_info_edit_card_number":
            bot.send_message(call.message.chat.id, MESSAGES['USERS_BOT_OWNER_INFO_EDIT_CARD_NUMBER'], reply_markup=while_edit_user_markup())
            bot.register_next_step_handler(call.message, users_bot_owner_info_edit_card_number)
        
        elif key == "users_bot_owner_info_edit_card_owner":
            bot.send_message(call.message.chat.id, MESSAGES['USERS_BOT_OWNER_INFO_EDIT_CARD_OWNER'], reply_markup=while_edit_user_markup())
            bot.register_next_step_handler(call.message, users_bot_owner_info_edit_card_owner)
        
        # --- Settings Toggles ---
        elif key == "users_bot_settings_hyperlink":
            new_value = not bool(int(value))
            status = USERS_DB.edit_bool_config("visible_hiddify_hyperlink", value=new_value)
            if not status:
                bot.send_message(call.message.chat.id, MESSAGES['ERROR_UNKNOWN'])
                return
            settings = all_configs_settings()
            bot.edit_message_text(KEY_MARKUP['USERS_BOT_SETTINGS'], call.message.chat.id, call.message.message_id, reply_markup=users_bot_management_settings_markup(settings))
        
        elif key == "users_bot_settings_three_rand_price":
            new_value = not bool(int(value))
            status = USERS_DB.edit_bool_config("three_random_num_price", value=new_value)
            if not status:
                bot.send_message(call.message.chat.id, MESSAGES['ERROR_UNKNOWN'])
                return
            settings = all_configs_settings()
            bot.edit_message_text(KEY_MARKUP['USERS_BOT_SETTINGS'], call.message.chat.id, call.message.message_id, reply_markup=users_bot_management_settings_markup(settings))
        
        elif key == "users_bot_settings_force_join":
            settings = all_configs_settings()
            if not settings['channel_id']:
                bot.send_message(call.message.chat.id, MESSAGES['ERROR_CHANNEL_ID_NOT_SET'])
                return
            new_value = not bool(int(value))
            status = USERS_DB.edit_bool_config("force_join_channel", value=new_value)
            if not status:
                bot.send_message(call.message.chat.id, MESSAGES['ERROR_UNKNOWN'])
                return
            if new_value:
                bot.send_message(call.message.chat.id, MESSAGES['USERS_BOT_SETTING_FORCE_JOIN_HELP'])
            settings = all_configs_settings()
            bot.edit_message_text(KEY_MARKUP['USERS_BOT_SETTINGS'], call.message.chat.id, call.message.message_id, reply_markup=users_bot_management_settings_markup(settings))
        
        elif key == "users_bot_settings_buy_sub":
            new_value = not bool(int(value))
            status = USERS_DB.edit_bool_config("buy_subscription_status", value=new_value)
            if not status:
                bot.send_message(call.message.chat.id, MESSAGES['ERROR_UNKNOWN'])
                return
            settings = all_configs_settings()
            bot.edit_message_text(KEY_MARKUP['USERS_BOT_SETTINGS'], call.message.chat.id, call.message.message_id, reply_markup=users_bot_management_settings_markup(settings))
        
        elif key == "users_bot_settings_renewal_sub":
            new_value = not bool(int(value))
            status = USERS_DB.edit_bool_config("renewal_subscription_status", value=new_value)
            if not status:
                bot.send_message(call.message.chat.id, MESSAGES['ERROR_UNKNOWN'])
                return
            settings = all_configs_settings()
            bot.edit_message_text(KEY_MARKUP['USERS_BOT_SETTINGS'], call.message.chat.id, call.message.message_id, reply_markup=users_bot_management_settings_markup(settings))
        
        elif key == "users_bot_settings_visible_conf_dir":
            new_value = not bool(int(value))
            status = USERS_DB.edit_bool_config("visible_conf_dir", value=new_value)
            if not status:
                bot.send_message(call.message.chat.id, MESSAGES['ERROR_UNKNOWN'])
                return
            settings = all_configs_settings()
            bot.edit_message_text(KEY_MARKUP['USERS_BOT_SETTINGS_VISIBLE_SUB'], call.message.chat.id, call.message.message_id, reply_markup=users_bot_management_settings_visible_sub_markup(settings))
        
        elif key == "users_bot_settings_visible_conf_sub_auto":
            new_value = not bool(int(value))
            status = USERS_DB.edit_bool_config("visible_conf_sub_auto", value=new_value)
            if not status:
                bot.send_message(call.message.chat.id, MESSAGES['ERROR_UNKNOWN'])
                return
            settings = all_configs_settings()
            bot.edit_message_text(KEY_MARKUP['USERS_BOT_SETTINGS_VISIBLE_SUB'], call.message.chat.id, call.message.message_id, reply_markup=users_bot_management_settings_visible_sub_markup(settings))
        
        elif key == "users_bot_settings_visible_conf_sub_url":
            new_value = not bool(int(value))
            status = USERS_DB.edit_bool_config("visible_conf_sub_url", value=new_value)
            if not status:
                bot.send_message(call.message.chat.id, MESSAGES['ERROR_UNKNOWN'])
                return
            settings = all_configs_settings()
            bot.edit_message_text(KEY_MARKUP['USERS_BOT_SETTINGS_VISIBLE_SUB'], call.message.chat.id, call.message.message_id, reply_markup=users_bot_management_settings_visible_sub_markup(settings))
        
        elif key == "users_bot_settings_visible_conf_sub_qr":
            new_value = not bool(int(value))
            status = USERS_DB.edit_bool_config("visible_conf_sub_qr", value=new_value)
            if not status:
                bot.send_message(call.message.chat.id, MESSAGES['ERROR_UNKNOWN'])
                return
            settings = all_configs_settings()
            bot.edit_message_text(KEY_MARKUP['USERS_BOT_SETTINGS_VISIBLE_SUB'], call.message.chat.id, call.message.message_id, reply_markup=users_bot_management_settings_visible_sub_markup(settings))
        
        elif key == "users_bot_settings_visible_conf_clash":
            new_value = not bool(int(value))
            status = USERS_DB.edit_bool_config("visible_conf_clash", value=new_value)
            if not status:
                bot.send_message(call.message.chat.id, MESSAGES['ERROR_UNKNOWN'])
                return
            settings = all_configs_settings()
            bot.edit_message_text(KEY_MARKUP['USERS_BOT_SETTINGS_VISIBLE_SUB'], call.message.chat.id, call.message.message_id, reply_markup=users_bot_management_settings_visible_sub_markup(settings))
        
        elif key == "users_bot_settings_visible_conf_hiddify":
            new_value = not bool(int(value))
            status = USERS_DB.edit_bool_config("visible_conf_hiddify", value=new_value)
            if not status:
                bot.send_message(call.message.chat.id, MESSAGES['ERROR_UNKNOWN'])
                return
            settings = all_configs_settings()
            bot.edit_message_text(KEY_MARKUP['USERS_BOT_SETTINGS_VISIBLE_SUB'], call.message.chat.id, call.message.message_id, reply_markup=users_bot_management_settings_visible_sub_markup(settings))
        
        elif key == "users_bot_settings_visible_conf_sub_sing_box":
            new_value = not bool(int(value))
            status = USERS_DB.edit_bool_config("visible_conf_sub_sing_box", value=new_value)
            if not status:
                bot.send_message(call.message.chat.id, MESSAGES['ERROR_UNKNOWN'])
                return
            settings = all_configs_settings()
            bot.edit_message_text(KEY_MARKUP['USERS_BOT_SETTINGS_VISIBLE_SUB'], call.message.chat.id, call.message.message_id, reply_markup=users_bot_management_settings_visible_sub_markup(settings))
        
        elif key == "users_bot_settings_visible_conf_sub_full_sing_box":
            new_value = not bool(int(value))
            status = USERS_DB.edit_bool_config("visible_conf_sub_full_sing_box", value=new_value)
            if not status:
                bot.send_message(call.message.chat.id, MESSAGES['ERROR_UNKNOWN'])
                return
            settings = all_configs_settings()
            bot.edit_message_text(KEY_MARKUP['USERS_BOT_SETTINGS_VISIBLE_SUB'], call.message.chat.id, call.message.message_id, reply_markup=users_bot_management_settings_visible_sub_markup(settings))
        
        # --- Settings Value Changes ---
        elif key == "users_bot_settings_min_depo":
            bot.send_message(call.message.chat.id, MESSAGES['USERS_BOT_SETTINGS_MIN_DEPO'], reply_markup=while_edit_user_markup())
            bot.register_next_step_handler(call.message, users_bot_settings_min_depo)
        
        elif key == "users_bot_settings_channel_id":
            bot.send_message(call.message.chat.id, MESSAGES['USERS_BOT_SETTINGS_CHANNEL_ID'], reply_markup=while_edit_user_markup())
            bot.register_next_step_handler(call.message, users_bot_settings_channel_id)
        
        elif key == "users_bot_settings_welcome_msg":
            bot.send_message(call.message.chat.id, MESSAGES['USERS_BOT_SETTINGS_WELCOME_MSG'], reply_markup=while_edit_user_markup())
            bot.register_next_step_handler(call.message, users_bot_settings_welcome_msg)
        
        elif key == "users_bot_settings_test_sub_days":
            bot.send_message(call.message.chat.id, MESSAGES['USERS_BOT_SETTINGS_TEST_SUB_DAYS'], reply_markup=while_edit_user_markup())
            bot.register_next_step_handler(call.message, users_bot_settings_test_sub_days)
        
        elif key == "users_bot_settings_test_sub_size":
            bot.send_message(call.message.chat.id, MESSAGES['USERS_BOT_SETTINGS_TEST_SUB_SIZE'], reply_markup=while_edit_user_markup())
            bot.register_next_step_handler(call.message, users_bot_settings_test_sub_size)
        
        elif key == "users_bot_settings_reminder_days":
            bot.send_message(call.message.chat.id, MESSAGES['USERS_BOT_SETTINGS_REMINDER_DAYS'], reply_markup=while_edit_user_markup())
            bot.register_next_step_handler(call.message, users_bot_settings_reminder_days)
        
        elif key == "users_bot_settings_reminder_usage":
            bot.send_message(call.message.chat.id, MESSAGES['USERS_BOT_SETTINGS_REMINDER_USAGE'], reply_markup=while_edit_user_markup())
            bot.register_next_step_handler(call.message, users_bot_settings_reminder_usage)
        
        elif key == "users_bot_settings_renewal_method_advanced_days":
            bot.send_message(call.message.chat.id, MESSAGES['USERS_BOT_SETTINGS_RENEWAL_METHOD_ADVANCED_DAYS'], reply_markup=while_edit_user_markup())
            bot.register_next_step_handler(call.message, users_bot_settings_renewal_method_advanced_days)
        
        elif key == "users_bot_settings_renewal_method_advanced_usage":
            bot.send_message(call.message.chat.id, MESSAGES['USERS_BOT_SETTINGS_RENEWAL_METHOD_ADVANCED_USAGE'], reply_markup=while_edit_user_markup())
            bot.register_next_step_handler(call.message, users_bot_settings_renewal_method_advanced_usage)
        
        elif key == "users_bot_settings_faq_msg":
            bot.send_message(call.message.chat.id, MESSAGES['USERS_BOT_SETTINGS_FAQ_MSG'], reply_markup=while_edit_user_markup())
            bot.register_next_step_handler(call.message, users_bot_settings_faq_msg)
        
        elif key == "users_bot_settings_help_msg":
            bot.send_message(call.message.chat.id, MESSAGES['USERS_BOT_SETTINGS_HELP_MSG'], reply_markup=while_edit_user_markup())
            bot.register_next_step_handler(call.message, users_bot_settings_help_msg)
        
        # --- Backup and Restore ---
        elif key == "backup_bot":
            file_name = backup_json_bot()
            if not file_name:
                bot.send_message(call.message.chat.id, MESSAGES['ERROR_UNKNOWN'])
                return
            bot.send_document(call.message.chat.id, open(file_name, 'rb'), caption="🤖Bot Backup")
        
        elif key == "backup_bot_restore":
            bot.send_message(call.message.chat.id, MESSAGES['BACKUP_BOT_RESTORE_ASK'], reply_markup=while_edit_user_markup())
            bot.register_next_step_handler(call.message, backup_bot_restore)
        
        # --- System Status ---
        elif key == "system_status":
            # Get panel info using new API
            panel_info = get_panel_info()
            if not panel_info:
                bot.send_message(call.message.chat.id, MESSAGES['ERROR_UNKNOWN'])
                return
            
            # Get admin info using new API
            admin_info = get_admin_info()
            if not admin_info:
                bot.send_message(call.message.chat.id, MESSAGES['ERROR_UNKNOWN'])
                return
            
            # Get server status using new API (for default server or all servers)
            servers = USERS_DB.select_servers()
            server_statuses = []
            if servers:
                for server in servers:
                    # This is a simplification, you might want to get status for each server
                    # status = get_server_status() # This might need server-specific URL
                    # For now, we'll just show basic server info
                    server_statuses.append(f"Server: {server['title']} - URL: {server['url']}")
            
            msg = system_status_template(panel_info, admin_info, server_statuses)
            bot.edit_message_text(msg, call.message.chat.id, call.message.message_id, reply_markup=main_menu_keyboard_markup())
        
        # --- Owner Info ---
        elif key == "owner_info":
            owner_info_data = USERS_DB.select_str_config()
            msg = owner_info_template(owner_info_data)
            bot.edit_message_text(msg, call.message.chat.id, call.message.message_id, reply_markup=users_bot_edit_owner_info_markup(owner_info_data))
        
        # --- About ---
        elif key == "about":
            msg = about_template(VERSION)
            bot.edit_message_text(msg, call.message.chat.id, call.message.message_id, reply_markup=main_menu_keyboard_markup())
        
        # --- Back Navigation ---
        elif key == "back_to_main":
            bot.edit_message_text(MESSAGES['WELCOME_ADMIN'], call.message.chat.id, call.message.message_id, reply_markup=main_menu_keyboard_markup())
        
        elif key == "back_to_users_management":
            bot.edit_message_text(KEY_MARKUP['USERS_MANAGEMENT'], call.message.chat.id, call.message.message_id, reply_markup=users_management_markup())
        
        elif key == "back_to_servers_management":
            servers = USERS_DB.select_servers()
            bot.edit_message_text(KEY_MARKUP['SERVERS_MANAGEMENT'], call.message.chat.id, call.message.message_id, reply_markup=servers_management_markup(servers))
        
        elif key == "back_to_plans_management":
            plans = USERS_DB.select_plans()
            bot.edit_message_text(KEY_MARKUP['PLANS_MANAGEMENT'], call.message.chat.id, call.message.message_id, reply_markup=plans_management_markup(plans))
        
        elif key == "back_to_orders_management":
            orders = USERS_DB.select_orders()
            bot.edit_message_text(KEY_MARKUP['ORDERS_MANAGEMENT'], call.message.chat.id, call.message.message_id, reply_markup=orders_management_markup(orders))
        
        elif key == "back_to_payments_management":
            payments = USERS_DB.select_payments()
            bot.edit_message_text(KEY_MARKUP['PAYMENTS_MANAGEMENT'], call.message.chat.id, call.message.message_id, reply_markup=payments_management_markup(payments))
        
        elif key == "back_to_users_bot_management":
            settings = all_configs_settings()
            bot.edit_message_text(KEY_MARKUP['USERS_BOT_MANAGEMENT'], call.message.chat.id, call.message.message_id, reply_markup=users_bot_management_markup(settings))
        
        elif key == "back_to_users_bot_settings":
            settings = all_configs_settings()
            bot.edit_message_text(KEY_MARKUP['USERS_BOT_SETTINGS'], call.message.chat.id, call.message.message_id, reply_markup=users_bot_management_settings_markup(settings))
        
        elif key == "back_to_server_list_of_plans":
            plans_list = []
            plans = USERS_DB.select_plans()
            if plans:
                for plan in plans:
                    if plan['status']:
                        if plan['server_id'] == int(value): # value should be server_id
                            plans_list.append(plan)
            plans_markup = plans_list_markup(plans_list, value)
            bot.edit_message_text(KEY_MARKUP['PLANS_LIST'], call.message.chat.id, call.message.message_id, reply_markup=plans_markup)
        
        # --- New Features Integration ---
        # --- Online Payment Gateway Integration (Placeholder) ---
        elif key == "online_payment_gateways":
            # This would show options for different payment gateways
            # For now, we'll just show a placeholder message
            bot.send_message(call.message.chat.id, "Online payment gateways integration is under development. This will allow users to pay via ZarinPal, NextPay, etc.")
            # You can add a markup here to show available gateways or configuration options
        
        # --- Affiliate/Referral System ---
        elif key == "affiliate_system":
            # Show affiliate system statistics or management options
            # For now, a placeholder
            total_referrals = 0 # Get from DB
            total_commission = 0.0 # Get from DB
            msg = f"""
👥 Affiliate/Referral System

Total Referrals: {total_referrals}
Total Commission Earned: {total_commission:.2f} Tomans

Configure referral commission rates and view detailed reports.
"""
            # Add markup for affiliate settings, reports, etc.
            bot.send_message(call.message.chat.id, msg)
        
        # --- Advanced Statistics ---
        elif key == "advanced_statistics":
            # Get user and order statistics using new utility functions
            user_stats = get_user_statistics()
            order_stats = get_order_statistics()
            
            msg = f"""
📊 Advanced Statistics

👥 User Statistics:
   - Total Users: {user_stats['total_users']}
   - Active Users: {user_stats['active_users']}
   - Expired Users: {user_stats['expired_users']}

💰 Order/Sales Statistics:
   - Total Orders: {order_stats['total_orders']}
   - Total Revenue: {rial_to_toman(order_stats['total_revenue'])} Tomans
"""
            bot.send_message(call.message.chat.id, msg, reply_markup=main_menu_keyboard_markup())
        
        # --- Coupon Management (Placeholder) ---
        elif key == "coupon_management":
            # Show coupon management options
            bot.send_message(call.message.chat.id, "Coupon management is under development. This will allow creating and managing discount coupons.")
            # Add markup for creating coupons, viewing coupon list, etc.
        
        # --- Multi-Server Load Balancing ---
        elif key == "load_balancing":
            # Show load balancing settings or status
            servers = USERS_DB.select_servers()
            if not servers:
                bot.send_message(call.message.chat.id, "No servers configured for load balancing.")
                return
            
            msg = "⚖️ Multi-Server Load Balancing\n\n"
            for server in servers:
                # This is a simplification. In reality, you'd get real-time load data.
                msg += f"Server: {server['title']}\n"
                msg += f"   Status: {'Active' if server.get('status', True) else 'Inactive'}\n"
                # Add more load metrics if available
                msg += "\n"
            
            bot.send_message(call.message.chat.id, msg)
        
        # --- Enhanced Logging/Debugging ---
        elif key == "enhanced_logging":
            # Show recent logs or log settings
            # For now, just a placeholder
            bot.send_message(call.message.chat.id, "Enhanced logging and debugging tools are available. Check logs for detailed activity tracking.")
            # You could implement sending last N lines of log file, or changing log level
        
        else:
            bot.answer_callback_query(call.id, MESSAGES['ERROR_INVALID_COMMAND'])

    except Exception as e:
        logger.error(f"Error in callback_query: {e}")
        bot.send_message(call.message.chat.id, MESSAGES['ERROR_UNKNOWN'])

# --- Message Handlers ---
@bot.message_handler(func=lambda message: True)
def handle_all_messages(message: Message):
    """Handle all text messages that are not commands or part of a conversation flow"""
    # If the message is a command, it should be handled by command handlers
    if message.text and message.text.startswith('/'):
        # Commands are handled by @bot.message_handler(commands=[...])
        # If a command is not defined, this will catch it
        bot.send_message(message.chat.id, MESSAGES['ERROR_INVALID_COMMAND'])
        return

    # If the message is from an admin and not part of a specific flow, show main menu
    if message.chat.id in ADMINS_ID:
        bot.send_message(message.chat.id, MESSAGES['WELCOME_ADMIN'], reply_markup=main_menu_keyboard_markup())
    else:
        bot.send_message(message.chat.id, MESSAGES['ERROR_ACCESS_DENIED'])

# --- Helper Functions (Add User Flow) ---
add_user_data = {}

def add_user_name(message: Message):
    """Step 1 of adding a user: Get user name"""
    if is_it_cancel(message):
        return
    add_user_data['name'] = message.text
    bot.send_message(message.chat.id, MESSAGES['USERS_ADD_DAYS'], reply_markup=while_edit_user_markup())
    bot.register_next_step_handler(message, add_user_days)

def add_user_days(message: Message):
    """Step 2 of adding a user: Get package days"""
    if is_it_cancel(message):
        return
    if not is_it_digit(message, markup=while_edit_user_markup()):
        bot.register_next_step_handler(message, add_user_days)
        return
    add_user_data['usage_days'] = message.text
    bot.send_message(message.chat.id, MESSAGES['USERS_ADD_SIZE'], reply_markup=while_edit_user_markup())
    bot.register_next_step_handler(message, add_user_size)

def add_user_size(message: Message):
    """Step 3 of adding a user: Get usage limit"""
    if is_it_cancel(message):
        return
    if not is_it_digit(message, markup=while_edit_user_markup()):
        bot.register_next_step_handler(message, add_user_size)
        return
    add_user_data['limit'] = message.text
    
    # Select best server using load balancing utility
    selected_server = select_best_server_for_user()
    if not selected_server:
        bot.send_message(message.chat.id, MESSAGES['ERROR_SERVER_NOT_FOUND'])
        return
    
    # Create user on Hiddify panel using new API
    uuid = create_user(
        name=add_user_data['name'],
        package_days=int(add_user_data['usage_days']),
        usage_limit_GB=int(add_user_data['limit']),
        # telegram_id=message.chat.id, # Not applicable for admin-created users
        comment=f"Created by admin {message.chat.id}"
    )
    
    if not uuid:
        bot.send_message(message.chat.id, MESSAGES['ERROR_UNKNOWN'])
        return
    
    # Add user to local database
    # Note: The original code used telegram_id as a unique identifier for users.
    # For admin-created users, we might need a different approach or a placeholder telegram_id.
    # For now, let's assume we generate a unique placeholder ID or use UUID.
    # This logic might need adjustment based on your database schema.
    telegram_id_placeholder = f"admin_created_{uuid[:8]}" # Example placeholder
    status = USERS_DB.add_user(telegram_id=telegram_id_placeholder, name=add_user_data['name'], uuid=uuid)
    if not status:
        # If adding to DB fails, we might want to delete the user from Hiddify panel to keep things consistent
        delete_user(uuid) # Attempt to rollback
        bot.send_message(message.chat.id, MESSAGES['ERROR_UNKNOWN'])
        return
    
    bot.send_message(message.chat.id, MESSAGES['SUCCESS_ADD_USER'], reply_markup=main_menu_keyboard_markup())

# --- Helper Functions (Add Server Flow) ---
add_server_data = {}

def add_server_name(message: Message):
    """Step 1 of adding a server: Get server name"""
    if is_it_cancel(message):
        return
    add_server_data['name'] = message.text
    bot.send_message(message.chat.id, MESSAGES['SERVERS_ADD_URL'], reply_markup=while_edit_user_markup())
    bot.register_next_step_handler(message, add_server_url)

def add_server_url(message: Message):
    """Step 2 of adding a server: Get server URL"""
    if is_it_cancel(message):
        return
    # Basic URL validation
    if not (message.text.startswith("http://") or message.text.startswith("https://")):
        bot.send_message(message.chat.id, MESSAGES['ERROR_INVALID_URL'], reply_markup=while_edit_user_markup())
        bot.register_next_step_handler(message, add_server_url)
        return
    add_server_data['url'] = message.text
    bot.send_message(message.chat.id, MESSAGES['SERVERS_ADD_USER_LIMIT'], reply_markup=while_edit_user_markup())
    bot.register_next_step_handler(message, add_server_user_limit)

def add_server_user_limit(message: Message):
    """Step 3 of adding a server: Get user limit"""
    if is_it_cancel(message):
        return
    if not is_it_digit(message, markup=while_edit_user_markup()):
        bot.register_next_step_handler(message, add_server_user_limit)
        return
    add_server_data['user_limit'] = int(message.text)
    
    # Add server to database
    status = USERS_DB.add_server(add_server_data['name'], add_server_data['url'], add_server_data['user_limit'])
    if not status:
        bot.send_message(message.chat.id, MESSAGES['ERROR_UNKNOWN'])
        return
    
    bot.send_message(message.chat.id, MESSAGES['SUCCESS_ADD_SERVER'], reply_markup=main_menu_keyboard_markup())

# --- Helper Functions (Edit User) ---
def edit_user_name(message: Message, user_id):
    """Edit user's name"""
    if is_it_cancel(message):
        return
    status = USERS_DB.edit_user(telegram_id=int(user_id), full_name=message.text)
    if not status:
        bot.send_message(message.chat.id, MESSAGES['ERROR_UNKNOWN'], reply_markup=main_menu_keyboard_markup())
        return
    bot.send_message(message.chat.id, MESSAGES['SUCCESS_USER_NAME_EDITED'], reply_markup=main_menu_keyboard_markup())

def edit_user_limit(message: Message, user_id):
    """Edit user's usage limit"""
    if is_it_cancel(message):
        return
    if not is_it_digit(message, markup=while_edit_user_markup()):
        bot.register_next_step_handler(message, edit_user_limit, user_id)
        return
    
    # Find user to get UUID for Hiddify API update
    users = USERS_DB.find_user(telegram_id=int(user_id))
    if not users:
        bot.send_message(message.chat.id, MESSAGES['ERROR_USER_NOT_FOUND'])
        return
    user = users[0]
    uuid = user.get('uuid')
    
    if uuid:
        # Update user on Hiddify panel using new API
        update_status = update_user(uuid, usage_limit_GB=int(message.text))
        if not update_status:
            bot.send_message(message.chat.id, MESSAGES['ERROR_UNKNOWN'])
            return
    
    # Update user in local database
    status = USERS_DB.edit_user(telegram_id=int(user_id), balance=int(message.text))
    if not status:
        bot.send_message(message.chat.id, MESSAGES['ERROR_UNKNOWN'], reply_markup=main_menu_keyboard_markup())
        return
    bot.send_message(message.chat.id, f"{MESSAGES['SUCCESS_USER_LIMIT_EDITED']} {message.text} {MESSAGES['GB']}", reply_markup=main_menu_keyboard_markup())

def edit_user_days(message: Message, user_id):
    """Edit user's package days"""
    if is_it_cancel(message):
        return
    if not is_it_digit(message, markup=while_edit_user_markup()):
        bot.register_next_step_handler(message, edit_user_days, user_id)
        return
    
    # Find user to get UUID for Hiddify API update
    users = USERS_DB.find_user(telegram_id=int(user_id))
    if not users:
        bot.send_message(message.chat.id, MESSAGES['ERROR_USER_NOT_FOUND'])
        return
    user = users[0]
    uuid = user.get('uuid')
    
    if uuid:
        # Update user on Hiddify panel using new API
        update_status = update_user(uuid, package_days=int(message.text))
        if not update_status:
            bot.send_message(message.chat.id, MESSAGES['ERROR_UNKNOWN'])
            return
    
    bot.send_message(message.chat.id, f"{MESSAGES['SUCCESS_USER_DAYS_EDITED']} {message.text} {MESSAGES['DAY_EXPIRE']} ", reply_markup=main_menu_keyboard_markup())

# --- Helper Functions (Edit Server) ---
def edit_server_title(message: Message, server_id):
    """Edit server's title"""
    if is_it_cancel(message):
        return
    status = USERS_DB.edit_server(id=int(server_id), title=message.text)
    if not status:
        bot.send_message(message.chat.id, MESSAGES['ERROR_UNKNOWN'], reply_markup=main_menu_keyboard_markup())
        return
    bot.send_message(message.chat.id, MESSAGES['SUCCESS_SERVER_TITLE_EDITED'], reply_markup=main_menu_keyboard_markup())

def edit_server_url(message: Message, server_id):
    """Edit server's URL"""
    if is_it_cancel(message):
        return
    # Basic URL validation
    if not (message.text.startswith("http://") or message.text.startswith("https://")):
        bot.send_message(message.chat.id, MESSAGES['ERROR_INVALID_URL'], reply_markup=while_edit_user_markup())
        bot.register_next_step_handler(message, edit_server_url, server_id)
        return
    status = USERS_DB.edit_server(id=int(server_id), url=message.text)
    if not status:
        bot.send_message(message.chat.id, MESSAGES['ERROR_UNKNOWN'], reply_markup=main_menu_keyboard_markup())
        return
    bot.send_message(message.chat.id, MESSAGES['SUCCESS_SERVER_URL_EDITED'], reply_markup=main_menu_keyboard_markup())

def edit_server_user_limit(message: Message, server_id):
    """Edit server's user limit"""
    if is_it_cancel(message):
        return
    if not is_it_digit(message, markup=while_edit_user_markup()):
        bot.register_next_step_handler(message, edit_server_user_limit, server_id)
        return
    status = USERS_DB.edit_server(id=int(server_id), user_limit=int(message.text))
    if not status:
        bot.send_message(message.chat.id, MESSAGES['ERROR_UNKNOWN'], reply_markup=main_menu_keyboard_markup())
        return
    bot.send_message(message.chat.id, MESSAGES['SUCCESS_SERVER_USER_LIMIT_EDITED'], reply_markup=main_menu_keyboard_markup())

# --- Helper Functions (Add Plan Flow) ---
add_plan_data = {}

def add_plan_server(message: Message, servers):
    """Step 1 of adding a plan: Select server"""
    if is_it_cancel(message):
        return
    # Check if message text is a number and corresponds to a server
    if not is_it_digit(message, markup=while_edit_user_markup()):
        bot.register_next_step_handler(message, add_plan_server, servers)
        return
    
    server_id = int(message.text)
    server_found = False
    for server in servers:
        if server['id'] == server_id:
            server_found = True
            break
    
    if not server_found:
        bot.send_message(message.chat.id, MESSAGES['ERROR_SERVER_NOT_FOUND'], reply_markup=while_edit_user_markup())
        bot.register_next_step_handler(message, add_plan_server, servers)
        return
    
    add_plan_data['server_id'] = server_id
    bot.send_message(message.chat.id, MESSAGES['PLANS_ADD_NAME'], reply_markup=while_edit_user_markup())
    bot.register_next_step_handler(message, add_plan_name)

def add_plan_name(message: Message):
    """Step 2 of adding a plan: Get plan name"""
    if is_it_cancel(message):
        return
    add_plan_data['name'] = message.text
    bot.send_message(message.chat.id, MESSAGES['PLANS_ADD_SIZE'], reply_markup=while_edit_user_markup())
    bot.register_next_step_handler(message, add_plan_size)

def add_plan_size(message: Message):
    """Step 3 of adding a plan: Get plan size"""
    if is_it_cancel(message):
        return
    if not is_it_digit(message, markup=while_edit_user_markup()):
        bot.register_next_step_handler(message, add_plan_size)
        return
    add_plan_data['size_gb'] = int(message.text)
    bot.send_message(message.chat.id, MESSAGES['PLANS_ADD_DAYS'], reply_markup=while_edit_user_markup())
    bot.register_next_step_handler(message, add_plan_days)

def add_plan_days(message: Message):
    """Step 4 of adding a plan: Get plan days"""
    if is_it_cancel(message):
        return
    if not is_it_digit(message, markup=while_edit_user_markup()):
        bot.register_next_step_handler(message, add_plan_days)
        return
    add_plan_data['days'] = int(message.text)
    bot.send_message(message.chat.id, MESSAGES['PLANS_ADD_PRICE'], reply_markup=while_edit_user_markup())
    bot.register_next_step_handler(message, add_plan_price)

def add_plan_price(message: Message):
    """Step 5 of adding a plan: Get plan price"""
    if is_it_cancel(message):
        return
    if not is_it_digit(message, markup=while_edit_user_markup()):
        bot.register_next_step_handler(message, add_plan_price)
        return
    add_plan_data['price'] = toman_to_rial(message.text)
    
    # Add plan to database
    status = USERS_DB.add_plan(
        add_plan_data['name'],
        add_plan_data['size_gb'],
        add_plan_data['days'],
        add_plan_data['price'],
        add_plan_data['server_id']
    )
    if not status:
        bot.send_message(message.chat.id, MESSAGES['ERROR_UNKNOWN'])
        return
    
    bot.send_message(message.chat.id, MESSAGES['SUCCESS_ADD_PLAN'], reply_markup=main_menu_keyboard_markup())

# --- Helper Functions (Edit Plan) ---
def edit_plan_name(message: Message, plan_id):
    """Edit plan's name"""
    if is_it_cancel(message):
        return
    status = USERS_DB.edit_plan(id=int(plan_id), name=message.text)
    if not status:
        bot.send_message(message.chat.id, MESSAGES['ERROR_UNKNOWN'], reply_markup=main_menu_keyboard_markup())
        return
    bot.send_message(message.chat.id, MESSAGES['SUCCESS_PLAN_NAME_EDITED'], reply_markup=main_menu_keyboard_markup())

def edit_plan_size(message: Message, plan_id):
    """Edit plan's size"""
    if is_it_cancel(message):
        return
    if not is_it_digit(message, markup=while_edit_user_markup()):
        bot.register_next_step_handler(message, edit_plan_size, plan_id)
        return
    status = USERS_DB.edit_plan(id=int(plan_id), size_gb=int(message.text))
    if not status:
        bot.send_message(message.chat.id, MESSAGES['ERROR_UNKNOWN'], reply_markup=main_menu_keyboard_markup())
        return
    bot.send_message(message.chat.id, f"{MESSAGES['SUCCESS_PLAN_SIZE_EDITED']} {message.text} {MESSAGES['GB']}", reply_markup=main_menu_keyboard_markup())

def edit_plan_days(message: Message, plan_id):
    """Edit plan's days"""
    if is_it_cancel(message):
        return
    if not is_it_digit(message, markup=while_edit_user_markup()):
        bot.register_next_step_handler(message, edit_plan_days, plan_id)
        return
    status = USERS_DB.edit_plan(id=int(plan_id), days=int(message.text))
    if not status:
        bot.send_message(message.chat.id, MESSAGES['ERROR_UNKNOWN'], reply_markup=main_menu_keyboard_markup())
        return
    bot.send_message(message.chat.id, f"{MESSAGES['SUCCESS_PLAN_DAYS_EDITED']} {message.text} {MESSAGES['DAY_EXPIRE']}", reply_markup=main_menu_keyboard_markup())

def edit_plan_price(message: Message, plan_id):
    """Edit plan's price"""
    if is_it_cancel(message):
        return
    if not is_it_digit(message, markup=while_edit_user_markup()):
        bot.register_next_step_handler(message, edit_plan_price, plan_id)
        return
    new_price = toman_to_rial(message.text)
    status = USERS_DB.edit_plan(id=int(plan_id), price=new_price)
    if not status:
        bot.send_message(message.chat.id, MESSAGES['ERROR_UNKNOWN'], reply_markup=main_menu_keyboard_markup())
        return
    bot.send_message(message.chat.id, f"{MESSAGES['SUCCESS_PLAN_PRICE_EDITED']} {message.text} {MESSAGES['TOMAN']}", reply_markup=main_menu_keyboard_markup())

# --- Helper Functions (Search) ---
def search_user(message: Message):
    """Search for a user by name or Telegram ID"""
    if is_it_cancel(message):
        return
    
    search_term = message.text
    found_users = []
    
    # Try to search by Telegram ID first if it's a number
    if search_term.isdigit():
        users = USERS_DB.find_user(telegram_id=int(search_term))
        if users:
            found_users.extend(users)
    
    # Search by name using new API function
    if not found_users:
        api_users = search_user_by_name(search_term)
        if api_users:
            # Convert API user data to match DB structure if needed
            # This is a simplification, real implementation might be more complex
            found_users.extend(api_users)
    
    if not found_users:
        bot.send_message(message.chat.id, MESSAGES['ERROR_USER_NOT_FOUND'], reply_markup=main_menu_keyboard_markup())
        return
    
    # Display found users
    bot.send_message(message.chat.id, KEY_MARKUP['USERS_LIST'], reply_markup=users_list_markup(found_users, search_mode=True))

def search_order(message: Message):
    """Search for an order by ID"""
    if is_it_cancel(message):
        return
    if not is_it_digit(message, markup=while_edit_user_markup()):
        bot.register_next_step_handler(message, search_order)
        return
    
    orders = USERS_DB.find_order(id=int(message.text))
    if not orders:
        bot.send_message(message.chat.id, MESSAGES['ERROR_ORDER_NOT_FOUND'], reply_markup=main_menu_keyboard_markup())
        return
    
    order = orders[0]
    plans = USERS_DB.find_plan(id=order['plan_id'])
    if not plans:
        bot.send_message(message.chat.id, MESSAGES['ERROR_PLAN_NOT_FOUND'])
        return
    plan = plans[0]
    users = USERS_DB.find_user(telegram_id=order['telegram_id'])
    if not users:
        bot.send_message(message.chat.id, MESSAGES['ERROR_USER_NOT_FOUND'])
        return
    user = users[0]
    servers = USERS_DB.find_server(id=plan['server_id'])
    if not servers:
        bot.send_message(message.chat.id, MESSAGES['ERROR_SERVER_NOT_FOUND'])
        return
    server = servers[0]
    msg = bot_orders_info_template(order, plan, user, server)
    bot.send_message(message.chat.id, msg, reply_markup=bot_order_info_markup(order['id']))

def search_payment(message: Message):
    """Search for a payment by ID"""
    if is_it_cancel(message):
        return
    if not is_it_digit(message, markup=while_edit_user_markup()):
        bot.register_next_step_handler(message, search_payment)
        return
    
    payments = USERS_DB.find_payment(id=int(message.text))
    if not payments:
        bot.send_message(message.chat.id, MESSAGES['ERROR_PAYMENT_NOT_FOUND'], reply_markup=main_menu_keyboard_markup())
        return
    
    payment = payments[0]
    user_data = USERS_DB.find_user(telegram_id=payment['telegram_id'])
    if not user_data:
        bot.send_message(message.chat.id, MESSAGES['ERROR_USER_NOT_FOUND'])
        return
    user_data = user_data[0]
    msg = bot_payment_info_template(payment, user_data)
    photo_path = payment['photo_path']
    if os.path.exists(photo_path):
        bot.send_photo(message.chat.id, photo=open(photo_path, 'rb'), caption=msg, reply_markup=change_status_payment_by_admin(payment['id']))
    else:
        bot.send_message(message.chat.id, msg, reply_markup=change_status_payment_by_admin(payment['id']))

# --- Helper Functions (Settings Updates) ---
def users_bot_settings_min_depo(message: Message):
    """Update minimum deposit amount setting"""
    if is_it_cancel(message):
        return
    if not is_it_digit(message, markup=while_edit_user_markup()):
        bot.register_next_step_handler(message, users_bot_settings_min_depo)
        return
    new_min_depo = toman_to_rial(message.text)
    new_min_depo = int(new_min_depo)
    status = USERS_DB.edit_int_config("min_deposit_amount", value=new_min_depo)
    if not status:
        bot.send_message(message.chat.id, MESSAGES['ERROR_UNKNOWN'], reply_markup=main_menu_keyboard_markup())
        return
    bot.send_message(message.chat.id, MESSAGES['SUCCESS_UPDATE_DATA'], reply_markup=main_menu_keyboard_markup())

def users_bot_settings_channel_id(message: Message):
    """Update channel ID setting"""
    if is_it_cancel(message):
        return
    if not message.text.startswith('@'):
        bot.send_message(message.chat.id, MESSAGES['ERROR_INVALID_USERNAME'], reply_markup=main_menu_keyboard_markup())
        return
    status = USERS_DB.edit_str_config("channel_id", value=message.text)
    if not status:
        bot.send_message(message.chat.id, MESSAGES['ERROR_UNKNOWN'], reply_markup=main_menu_keyboard_markup())
        return
    bot.send_message(message.chat.id, MESSAGES['SUCCESS_UPDATE_DATA'], reply_markup=main_menu_keyboard_markup())

def users_bot_settings_welcome_msg(message: Message):
    """Update welcome message setting"""
    if is_it_cancel(message):
        return
    status = USERS_DB.edit_str_config("msg_user_start", value=message.text)
    if not status:
        bot.send_message(message.chat.id, MESSAGES['ERROR_UNKNOWN'], reply_markup=main_menu_keyboard_markup())
        return
    bot.send_message(message.chat.id, MESSAGES['SUCCESS_UPDATE_DATA'], reply_markup=main_menu_keyboard_markup())

def users_bot_settings_test_sub_days(message: Message):
    """Update test subscription days setting"""
    if is_it_cancel(message):
        return
    if not is_it_digit(message, markup=while_edit_user_markup()):
        bot.register_next_step_handler(message, users_bot_settings_test_sub_days)
        return
    status = USERS_DB.edit_int_config("test_sub_days", value=int(message.text))
    if not status:
        bot.send_message(message.chat.id, MESSAGES['ERROR_UNKNOWN'], reply_markup=main_menu_keyboard_markup())
        return
    bot.send_message(message.chat.id, MESSAGES['SUCCESS_UPDATE_DATA'], reply_markup=main_menu_keyboard_markup())

def users_bot_settings_test_sub_size(message: Message):
    """Update test subscription size setting"""
    if is_it_cancel(message):
        return
    if not is_it_digit(message, allow_float=True, markup=while_edit_user_markup()):
        bot.register_next_step_handler(message, users_bot_settings_test_sub_size)
        return
    # if float convert float else convert int
    if '.' in message.text:
        new_test_sub_size = float(message.text)
    else:
        new_test_sub_size = int(message.text)
    status = USERS_DB.edit_int_config("test_sub_size_gb", value=new_test_sub_size)
    if not status:
        bot.send_message(message.chat.id, MESSAGES['ERROR_UNKNOWN'], reply_markup=main_menu_keyboard_markup())
        return
    bot.send_message(message.chat.id, MESSAGES['SUCCESS_UPDATE_DATA'], reply_markup=main_menu_keyboard_markup())

def users_bot_settings_reminder_days(message: Message):
    """Update reminder days setting"""
    if is_it_cancel(message):
        return
    if not is_it_digit(message, markup=while_edit_user_markup()):
        bot.register_next_step_handler(message, users_bot_settings_reminder_days)
        return
    status = USERS_DB.edit_int_config("reminder_notification_days", value=int(message.text))
    if not status:
        bot.send_message(message.chat.id, MESSAGES['ERROR_UNKNOWN'], reply_markup=main_menu_keyboard_markup())
        return
    bot.send_message(message.chat.id, MESSAGES['SUCCESS_UPDATE_DATA'], reply_markup=main_menu_keyboard_markup())

def users_bot_settings_reminder_usage(message: Message):
    """Update reminder usage setting"""
    if is_it_cancel(message):
        return
    if not is_it_digit(message, markup=while_edit_user_markup()):
        bot.register_next_step_handler(message, users_bot_settings_reminder_usage)
        return
    status = USERS_DB.edit_int_config("reminder_notification_usage", value=int(message.text))
    if not status:
        bot.send_message(message.chat.id, MESSAGES['ERROR_UNKNOWN'], reply_markup=main_menu_keyboard_markup())
        return
    bot.send_message(message.chat.id, MESSAGES['SUCCESS_UPDATE_DATA'], reply_markup=main_menu_keyboard_markup())

def users_bot_settings_renewal_method_advanced_days(message: Message):
    """Update renewal method advanced days setting"""
    if is_it_cancel(message):
        return
    if not is_it_digit(message, markup=while_edit_user_markup()):
        bot.register_next_step_handler(message, users_bot_settings_renewal_method_advanced_days)
        return
    status = USERS_DB.edit_int_config("advanced_renewal_days", value=int(message.text))
    if not status:
        bot.send_message(message.chat.id, MESSAGES['ERROR_UNKNOWN'], reply_markup=main_menu_keyboard_markup())
        return
    bot.send_message(message.chat.id, MESSAGES['SUCCESS_UPDATE_DATA'], reply_markup=main_menu_keyboard_markup())

def users_bot_settings_renewal_method_advanced_usage(message: Message):
    """Update renewal method advanced usage setting"""
    if is_it_cancel(message):
        return
    if not is_it_digit(message, markup=while_edit_user_markup()):
        bot.register_next_step_handler(message, users_bot_settings_renewal_method_advanced_usage)
        return
    status = USERS_DB.edit_int_config("advanced_renewal_usage", value=int(message.text))
    if not status:
        bot.send_message(message.chat.id, MESSAGES['ERROR_UNKNOWN'], reply_markup=main_menu_keyboard_markup())
        return
    bot.send_message(message.chat.id, MESSAGES['SUCCESS_UPDATE_DATA'], reply_markup=main_menu_keyboard_markup())

def users_bot_settings_faq_msg(message: Message):
    """Update FAQ message setting"""
    if is_it_cancel(message):
        return
    status = USERS_DB.edit_str_config("msg_faq", value=message.text)
    if not status:
        bot.send_message(message.chat.id, MESSAGES['ERROR_UNKNOWN'], reply_markup=main_menu_keyboard_markup())
        return
    bot.send_message(message.chat.id, MESSAGES['SUCCESS_UPDATE_DATA'], reply_markup=main_menu_keyboard_markup())

def users_bot_settings_help_msg(message: Message):
    """Update help message setting"""
    if is_it_cancel(message):
        return
    status = USERS_DB.edit_str_config("msg_help", value=message.text)
    if not status:
        bot.send_message(message.chat.id, MESSAGES['ERROR_UNKNOWN'], reply_markup=main_menu_keyboard_markup())
        return
    bot.send_message(message.chat.id, MESSAGES['SUCCESS_UPDATE_DATA'], reply_markup=main_menu_keyboard_markup())

# --- Helper Functions (Owner Info Updates) ---
def users_bot_owner_info_edit_username(message: Message):
    """Update owner's Telegram username"""
    if is_it_cancel(message):
        return
    if not message.text.startswith('@'):
        bot.send_message(message.chat.id, MESSAGES['ERROR_INVALID_USERNAME'], reply_markup=while_edit_user_markup())
        bot.register_next_step_handler(message, users_bot_owner_info_edit_username)
        return
    status = USERS_DB.edit_str_config("support_username", value=message.text)
    if not status:
        bot.send_message(message.chat.id, MESSAGES['ERROR_UNKNOWN'], reply_markup=main_menu_keyboard_markup())
        return
    bot.send_message(message.chat.id, MESSAGES['SUCCESS_UPDATE_DATA'], reply_markup=main_menu_keyboard_markup())

def users_bot_owner_info_edit_card_number(message: Message):
    """Update owner's card number"""
    if is_it_cancel(message):
        return
    if not is_it_digit(message, markup=while_edit_user_markup()):
        bot.register_next_step_handler(message, users_bot_owner_info_edit_card_number)
        return
    status = USERS_DB.edit_str_config("card_number", value=message.text)
    if not status:
        bot.send_message(message.chat.id, MESSAGES['ERROR_UNKNOWN'], reply_markup=main_menu_keyboard_markup())
        return
    bot.send_message(message.chat.id, MESSAGES['SUCCESS_UPDATE_DATA'], reply_markup=main_menu_keyboard_markup())

def users_bot_owner_info_edit_card_owner(message: Message):
    """Update owner's card owner name"""
    if is_it_cancel(message):
        return
    status = USERS_DB.edit_str_config("card_holder", value=message.text)
    if not status:
        bot.send_message(message.chat.id, MESSAGES['ERROR_UNKNOWN'], reply_markup=main_menu_keyboard_markup())
        return
    bot.send_message(message.chat.id, MESSAGES['SUCCESS_UPDATE_DATA'], reply_markup=main_menu_keyboard_markup())

# --- Helper Functions (Backup Restore) ---
def backup_bot_restore(message: Message):
    """Restore bot settings from a backup file"""
    if is_it_cancel(message):
        return
    # Check if message contains a document
    if not message.document:
        bot.send_message(message.chat.id, MESSAGES['ERROR_INVALID_FILE'], reply_markup=main_menu_keyboard_markup())
        return
    
    # Download the document
    file_info = bot.get_file(message.document.file_id)
    downloaded_file = bot.download_file(file_info.file_path)
    
    # Save to a temporary location
    temp_file_path = f"temp_backup_{message.document.file_id}.json"
    with open(temp_file_path, 'wb') as new_file:
        new_file.write(downloaded_file)
    
    # Restore from the file using the new utility function
    restore_status = restore_json_bot(temp_file_path)
    
    # Clean up temp file
    try:
        os.remove(temp_file_path)
    except:
        pass
    
    if not restore_status:
        bot.send_message(message.chat.id, MESSAGES['ERROR_UNKNOWN'], reply_markup=main_menu_keyboard_markup())
        return
    
    bot.send_message(message.chat.id, MESSAGES['SUCCESS_RESTORE_BOT'], reply_markup=main_menu_keyboard_markup())

# --- Helper Functions (Utility) ---
def is_it_cancel(message: Message) -> bool:
    """Check if the message is a cancel command"""
    if message.text == KEY_MARKUP['CANCEL']:
        bot.send_message(message.chat.id, MESSAGES['CANCELED'], reply_markup=main_menu_keyboard_markup())
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
    """Start the admin bot"""
    logger.info("Starting Admin Bot...")
    try:
        bot.remove_webhook() # Remove any existing webhook
    except:
        pass
    bot.polling(none_stop=True)

if __name__ == "__main__":
    start()
