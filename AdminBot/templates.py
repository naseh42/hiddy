# AdminBot/templates.py
# Description: This file contains all the templates used in the admin bot.
from config import LANG
from AdminBot.content import MESSAGES
from Utils.utils import rial_to_toman, toman_to_rial, all_configs_settings
from Database.dbManager import USERS_DB

# User Info Template
def user_info_template(telegram_id, user, header=""):
    # user is now expected to be the data returned from the new Hiddify API
    # which might have a different structure
    return f"""
{header}
{MESSAGES['INFO_USER_NAME']} <b>{user.get('name', '-')}</b>
{MESSAGES['INFO_USER_ID']} <code>{telegram_id}</code>
{MESSAGES['INFO_USER_BALANCE']} {rial_to_toman(user.get('balance', 0))} {MESSAGES['TOMAN']}
{MESSAGES['INFO_USER_CREATED_AT']} {user.get('created_at', '-')}
{MESSAGES['INFO_USER_LAST_LOGIN']} {user.get('last_online', '-')}
{MESSAGES['INFO_USER_BANNED']} {MESSAGES['YES'] if user.get('banned', False) else MESSAGES['NO']}
{MESSAGES['INFO_USER_BUY_SUBSCRIPTION_STATUS']} {MESSAGES['YES'] if user.get('test_subscription', True) else MESSAGES['NO']}
{MESSAGES['INFO_USER_PHONE_NUMBER']} {user.get('phone_number', MESSAGES['NOT_SET'])}
{MESSAGES['INFO_USER_WALLET_BALANCE']} {rial_to_toman(user.get('balance', 0))} {MESSAGES['TOMAN']}
{MESSAGES['INFO_USER_COMMENT']} {user.get('comment', MESSAGES['NOT_SET'])}
"""

# Server Info Template
def server_info_template(server, header=""):
    return f"""
{header}
{MESSAGES['INFO_SERVER_NAME']} <b>{server.get('title', '-')}</b>
{MESSAGES['INFO_SERVER_URL']} {server.get('url', '-')}
{MESSAGES['INFO_SERVER_USER_LIMIT']} {server.get('user_limit', '-')}
{MESSAGES['INFO_SERVER_USER_COUNT']} {server.get('user_count', 0)}/{server.get('user_limit', '∞')}
{MESSAGES['INFO_SERVER_STATUS']} {MESSAGES['ACTIVE'] if server.get('status', True) else MESSAGES['INACTIVE']}
{MESSAGES['INFO_SERVER_COMMENT']} {server.get('comment', MESSAGES['NOT_SET'])}
"""

# Plan Info Template
def plan_info_template(plan, header=""):
    msg = f"""
{header}
{MESSAGES['INFO_PLAN_NAME']} <b>{plan.get('name', '-')}</b>
{MESSAGES['INFO_PLAN_SIZE']} {plan.get('size_gb', '-')} {MESSAGES['GB']}
{MESSAGES['INFO_PLAN_DAYS']} {plan.get('days', '-')} {MESSAGES['DAY_EXPIRE']}
{MESSAGES['INFO_PLAN_PRICE']} {rial_to_toman(plan.get('price', 0))} {MESSAGES['TOMAN']}
{MESSAGES['INFO_PLAN_SERVER']} {plan.get('server_title', MESSAGES['NOT_SET'])}
{MESSAGES['INFO_PLAN_STATUS']} {MESSAGES['ACTIVE'] if plan.get('status', True) else MESSAGES['INACTIVE']}
"""
    if plan.get('description'):
        msg += f"{MESSAGES['INFO_PLAN_DESCRIPTION']} {plan['description']}\n"
    return msg

# Bot Payment Info Template
def bot_payment_info_template(payment, user_data, header=""):
    username = f"@{user_data.get('username', '')}" if user_data.get('username') else MESSAGES['NOT_SET']
    return f"""
{header}
{MESSAGES['INFO_PAYMENT_ID']} <b>{payment.get('id', '-')}</b>
{MESSAGES['INFO_PAYMENT_AMOUNT']} {rial_to_toman(payment.get('payment_amount', 0))} {MESSAGES['TOMAN']}
{MESSAGES['INFO_USER_NAME']} {user_data.get('full_name', MESSAGES['NOT_SET'])}
{MESSAGES['INFO_USER_USERNAME']} {username}
{MESSAGES['INFO_USER_NUM_ID']} {payment.get('telegram_id', MESSAGES['NOT_SET'])}
{MESSAGES['INFO_PAYMENT_STATUS']} {MESSAGES['CONFIRMED'] if payment.get('approved', False) else MESSAGES['NOT_CONFIRMED'] if payment.get('approved') is False else MESSAGES['PENDING']}
{MESSAGES['INFO_PAYMENT_DATE']} {payment.get('created_at', MESSAGES['NOT_SET'])}
{MESSAGES['INFO_PAYMENT_METHOD']} {payment.get('payment_method', MESSAGES['NOT_SET'])}
"""

# Bot Orders Info Template
def bot_orders_info_template(order, plan, user, server, header=""):
    username = f"@{user.get('username', '')}" if user.get('username') else MESSAGES['NOT_SET']
    return f"""
{header}
{MESSAGES['INFO_ORDER_ID']} <b>{order.get('id', '-')}</b>
{MESSAGES['INFO_USER_NAME']} {user.get('full_name', MESSAGES['NOT_SET'])}
{MESSAGES['INFO_USER_USERNAME']} {username}
{MESSAGES['INFO_USER_NUM_ID']} {order.get('telegram_id', MESSAGES['NOT_SET'])}
{MESSAGES['INFO_ORDER_PLAN_NAME']} {plan.get('name', MESSAGES['NOT_SET'])}
{MESSAGES['INFO_ORDER_PLAN_SIZE']} {plan.get('size_gb', MESSAGES['NOT_SET'])} {MESSAGES['GB']}
{MESSAGES['INFO_ORDER_PLAN_DAYS']} {plan.get('days', MESSAGES['NOT_SET'])} {MESSAGES['DAY_EXPIRE']}
{MESSAGES['INFO_ORDER_PLAN_PRICE']} {rial_to_toman(plan.get('price', 0))} {MESSAGES['TOMAN']}
{MESSAGES['INFO_ORDER_SERVER_NAME']} {server.get('title', MESSAGES['NOT_SET'])}
{MESSAGES['INFO_ORDER_SERVER_URL']} {server.get('url', MESSAGES['NOT_SET'])}
{MESSAGES['INFO_ORDER_DATE']} {order.get('created_at', MESSAGES['NOT_SET'])}
{MESSAGES['INFO_ORDER_STATUS']} {MESSAGES['ACTIVE'] if order.get('status', True) else MESSAGES['INACTIVE']}
"""

# Users List Template
def users_list_template(users, header=""):
    if not users:
        return f"{header}\n{MESSAGES['ERROR_USER_NOT_FOUND']}"
    
    msg = f"{header}\n"
    for user in users:
        username = f"@{user.get('username', '')}" if user.get('username') else MESSAGES['NOT_SET']
        msg += f"👤 {user.get('full_name', MESSAGES['NOT_SET'])} ({username}) - ID: <code>{user.get('telegram_id', MESSAGES['NOT_SET'])}</code>\n"
    return msg

# Bot Users List Template
def bot_users_list_template(users, header=""):
    # This might be similar to users_list_template or have different data
    return users_list_template(users, header)

# Bot Payments List Template
def bot_payments_list_template(payments, header=""):
    if not payments:
        return f"{header}\n{MESSAGES['ERROR_PAYMENT_NOT_FOUND']}"
    
    msg = f"{header}\n"
    for payment in payments:
        status_text = MESSAGES['CONFIRMED'] if payment.get('approved', False) else MESSAGES['NOT_CONFIRMED'] if payment.get('approved') is False else MESSAGES['PENDING']
        msg += f"💰 Payment {payment.get('id', MESSAGES['NOT_SET'])} - {rial_to_toman(payment.get('payment_amount', 0))} {MESSAGES['TOMAN']} - {status_text}\n"
    return msg

# Bot Orders List Template
def bot_orders_list_template(orders, header=""):
    if not orders:
        return f"{header}\n{MESSAGES['ERROR_ORDER_NOT_FOUND']}"
    
    msg = f"{header}\n"
    for order in orders:
        msg += f"📦 Order {order.get('id', MESSAGES['NOT_SET'])} - Plan ID: {order.get('plan_id', MESSAGES['NOT_SET'])} - User ID: {order.get('telegram_id', MESSAGES['NOT_SET'])}\n"
    return msg

# Configs Template
def configs_template(configs):
    # configs is expected to be a dictionary with different config types as keys
    # This structure might change based on how get_all_configs returns data
    if not configs:
        return MESSAGES['ERROR_CONFIG_NOT_FOUND']
    
    msg = f"{MESSAGES['USER_CONFIGS_LIST']}\n\n"
    
    # VLESS Configs
    if configs.get('vless'):
        msg += f"📡 <b>VLESS:</b>\n"
        for i, config in enumerate(configs['vless'], 1):
            msg += f"{i}. <code>{config}</code>\n"
        msg += "\n"
    
    # Vmess Configs
    if configs.get('vmess'):
        msg += f"📡 <b>VMess:</b>\n"
        for i, config in enumerate(configs['vmess'], 1):
            msg += f"{i}. <code>{config}</code>\n"
        msg += "\n"
    
    # Trojan Configs
    if configs.get('trojan'):
        msg += f"📡 <b>Trojan:</b>\n"
        for i, config in enumerate(configs['trojan'], 1):
            msg += f"{i}. <code>{config}</code>\n"
        msg += "\n"
    
    # Subscription Links
    if configs.get('sub_link'):
        msg += f"🔗 <b>{MESSAGES['CONFIGS_SUB']}:</b>\n"
        msg += f"<code>{configs['sub_link']}</code>\n\n"
    
    if configs.get('sub_link_b64'):
        msg += f"🔗 <b>{MESSAGES['CONFIGS_SUB_B64']}:</b>\n"
        msg += f"<code>{configs['sub_link_b64']}</code>\n\n"
    
    # Clash Configs
    if configs.get('clash'):
        msg += f"⚔️ <b>{MESSAGES['CONFIGS_CLASH']}:</b>\n"
        msg += f"<code>{configs['clash']}</code>\n\n"
    
    if configs.get('clash_meta'):
        msg += f"⚔️ <b>Clash Meta:</b>\n"
        msg += f"<code>{configs['clash_meta']}</code>\n\n"
    
    # Hiddify Configs
    if configs.get('hiddify_app'):
        msg += f"🚀 <b>{MESSAGES['CONFIGS_HIDDIFY']}:</b>\n"
        msg += f"<code>{configs['hiddify_app']}</code>\n\n"
    
    # Sing-Box Configs
    if configs.get('sing_box'):
        msg += f"📦 <b>{MESSAGES['CONFIGS_SING_BOX']}:</b>\n"
        msg += f"<code>{configs['sing_box']}</code>\n\n"
    
    if configs.get('sing_box_full'):
        msg += f"📦 <b>{MESSAGES['CONFIGS_FULL_SING_BOX']}:</b>\n"
        msg += f"<code>{configs['sing_box_full']}</code>\n\n"
    
    return msg

# System Status Template
def system_status_template(panel_info, admin_info, server_statuses, header=""):
    # panel_info and admin_info are data returned from the new Hiddify API
    msg = f"{header}\n"
    msg += f"📊 <b>{MESSAGES['SYSTEM_STATUS']}</b>\n\n"
    
    if panel_info:
        msg += f"🎛 <b>{MESSAGES['PANEL_INFO']}:</b>\n"
        msg += f"   {MESSAGES['PANEL_VERSION']}: {panel_info.get('version', '-')}\n"
        msg += f"   {MESSAGES['PANEL_UPTIME']}: {panel_info.get('uptime', '-')}\n"
        # Add more panel info fields as needed
        msg += "\n"
    
    if admin_info:
        msg += f"👤 <b>{MESSAGES['ADMIN_INFO']}:</b>\n"
        msg += f"   {MESSAGES['ADMIN_NAME']}: {admin_info.get('name', '-')}\n"
        msg += f"   {MESSAGES['ADMIN_UUID']}: <code>{admin_info.get('uuid', '-')}</code>\n"
        # Add more admin info fields as needed
        msg += "\n"
    
    if server_statuses:
        msg += f"🖥 <b>{MESSAGES['SERVERS_INFO']}:</b>\n"
        for status in server_statuses:
            msg += f"   {status}\n"
    
    return msg

# Owner Info Template
def owner_info_template(owner_info_data, header=""):
    # owner_info_data is expected to be a list of config entries from the database
    # We need to extract the relevant ones
    username = "-"
    card_number = "-"
    card_holder = "-"
    
    if owner_info_data:
        for item in owner_info_data:
            if item.get('key') == 'support_username':
                username = item.get('value', '-')
            elif item.get('key') == 'card_number':
                card_number = item.get('value', '-')
            elif item.get('key') == 'card_holder':
                card_holder = item.get('value', '-')
    
    return f"""
{header}
{MESSAGES['OWNER_INFO_USERNAME']} {username}
{MESSAGES['OWNER_INFO_CARD_NUMBER']} <code>{card_number}</code>
{MESSAGES['OWNER_INFO_CARD_OWNER']} {card_holder}
"""

# About Template
def about_template(version, header=""):
    return f"""
{header}
🤖 <b>{MESSAGES['ABOUT_BOT']}</b>
{lngg['VERSION']}: <code>{version}</code>

{lngg['CREATED_BY']}: HiddyBotGroup
{lngg['GITHUB_REPO']}: https://github.com/B3H1Z/Hiddify-Telegram-Bot
{lngg['LICENSE']}: GNU General Public License v3.0
"""

# New Template: Advanced Statistics
def advanced_statistics_template(user_stats, order_stats, header=""):
    return f"""
{header}
👥 <b>{MESSAGES['USER_STATISTICS']}</b>
   {MESSAGES['TOTAL_USERS']}: {user_stats.get('total_users', 0)}
   {MESSAGES['ACTIVE_USERS']}: {user_stats.get('active_users', 0)}
   {MESSAGES['EXPIRED_USERS']}: {user_stats.get('expired_users', 0)}

💰 <b>{MESSAGES['ORDER_STATISTICS']}</b>
   {MESSAGES['TOTAL_ORDERS']}: {order_stats.get('total_orders', 0)}
   {MESSAGES['TOTAL_REVENUE']}: {rial_to_toman(order_stats.get('total_revenue', 0))} {MESSAGES['TOMAN']}
"""

# New Template: Affiliate System Info
def affiliate_system_info_template(total_referrals, total_commission, header=""):
    return f"""
{header}
👥 <b>{MESSAGES['AFFILIATE_SYSTEM']}</b>
   {MESSAGES['TOTAL_REFERRALS']}: {total_referrals}
   {MESSAGES['TOTAL_COMMISSION']}: {rial_to_toman(total_commission)} {MESSAGES['TOMAN']}
"""

# New Template: Coupon Info
def coupon_info_template(coupon_data, header=""):
    if not coupon_data or not coupon_data.get('valid'):
        return f"{header}\n{MESSAGES['INVALID_COUPON']}"
    
    discount_type = coupon_data.get('discount_type', 'percentage')
    discount_value = coupon_data.get('discount_value', 0)
    if discount_type == 'percentage':
        discount_text = f"{discount_value}%"
    else:
        discount_text = f"{rial_to_toman(discount_value)} {MESSAGES['TOMAN']}"
        
    return f"""
{header}
🎫 <b>{MESSAGES['COUPON_INFO']}</b>
   {MESSAGES['COUPON_CODE']}: <code>{coupon_data.get('code', '-')}</code>
   {MESSAGES['COUPON_DISCOUNT']}: {discount_text}
   {MESSAGES['COUPON_EXPIRY']}: {coupon_data.get('expiry_date', MESSAGES['NOT_SET'])}
"""

# New Template: Load Balancing Status
def load_balancing_status_template(servers, header=""):
    msg = f"{header}\n"
    msg += f"⚖️ <b>{MESSAGES['LOAD_BALANCING_STATUS']}</b>\n\n"
    
    for server in servers:
        status_text = MESSAGES['ACTIVE'] if server.get('status', True) else MESSAGES['INACTIVE']
        msg += f"🖥 <b>{server.get('title', MESSAGES['NOT_SET'])}</b>\n"
        msg += f"   URL: {server.get('url', MESSAGES['NOT_SET'])}\n"
        msg += f"   Status: {status_text}\n"
        # Add more server load metrics if available
        msg += "\n"
        
    return msg
