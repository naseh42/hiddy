# AdminBot/markups.py
# Description: This file contains all the inline keyboards and reply markups used in the admin bot.
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from AdminBot.content import KEY_MARKUP
from Utils.utils import all_configs_settings

# Main Menu Keyboard
def main_menu_keyboard_markup():
    markup = InlineKeyboardMarkup()
    markup.row_width = 2
    markup.add(
        InlineKeyboardButton(KEY_MARKUP['USERS_MANAGEMENT'], callback_data="users_management"),
        InlineKeyboardButton(KEY_MARKUP['SERVERS_MANAGEMENT'], callback_data="servers_management"),
        InlineKeyboardButton(KEY_MARKUP['PLANS_MANAGEMENT'], callback_data="plans_management"),
        InlineKeyboardButton(KEY_MARKUP['ORDERS_MANAGEMENT'], callback_data="orders_management"),
        InlineKeyboardButton(KEY_MARKUP['PAYMENTS_MANAGEMENT'], callback_data="payments_management"),
        InlineKeyboardButton(KEY_MARKUP['USERS_BOT_MANAGEMENT'], callback_data="users_bot_management"),
        InlineKeyboardButton(KEY_MARKUP['USERS_BOT_SUBSCRIPTIONS'], callback_data="users_bot_subscriptions"),
        InlineKeyboardButton(KEY_MARKUP['USERS_BOT_ORDERS'], callback_data="users_bot_orders"),
        InlineKeyboardButton(KEY_MARKUP['USERS_BOT_PAYMENTS'], callback_data="users_bot_payments"),
        InlineKeyboardButton(KEY_MARKUP['USERS_BOT_USERS'], callback_data="users_bot_users"),
        InlineKeyboardButton(KEY_MARKUP['USERS_BOT_SEARCH'], callback_data="users_bot_search"),
        InlineKeyboardButton(KEY_MARKUP['USERS_BOT_TICKETS'], callback_data="users_bot_tickets"),
        InlineKeyboardButton(KEY_MARKUP['USERS_BOT_SEND_MESSAGE_TO_USERS'], callback_data="users_bot_send_message_to_users"),
        InlineKeyboardButton(KEY_MARKUP['USERS_BOT_SETTINGS'], callback_data="users_bot_settings"),
        InlineKeyboardButton(KEY_MARKUP['USERS_BOT_ABOUT'], callback_data="users_bot_about"),
        InlineKeyboardButton(KEY_MARKUP['BACKUP_BOT'], callback_data="backup_bot"),
        InlineKeyboardButton(KEY_MARKUP['RESTORE_BOT'], callback_data="backup_bot_restore"),
        InlineKeyboardButton(KEY_MARKUP['USERS_BOT_SYSTEM_STATUS'], callback_data="system_status"),
        InlineKeyboardButton(KEY_MARKUP['OWNER_INFO'], callback_data="owner_info"),
        InlineKeyboardButton(KEY_MARKUP['ABOUT'], callback_data="about"),
        # New features integration
        InlineKeyboardButton(KEY_MARKUP['ONLINE_PAYMENT_GATEWAYS'], callback_data="online_payment_gateways"),
        InlineKeyboardButton(KEY_MARKUP['AFFILIATE_SYSTEM'], callback_data="affiliate_system"),
        InlineKeyboardButton(KEY_MARKUP['ADVANCED_STATISTICS'], callback_data="advanced_statistics"),
        InlineKeyboardButton(KEY_MARKUP['COUPON_MANAGEMENT'], callback_data="coupon_management"),
        InlineKeyboardButton(KEY_MARKUP['LOAD_BALANCING'], callback_data="load_balancing"),
        InlineKeyboardButton(KEY_MARKUP['ENHANCED_LOGGING'], callback_data="enhanced_logging")
    )
    return markup

# Users Management Keyboard
def users_management_markup():
    markup = InlineKeyboardMarkup()
    markup.row_width = 2
    markup.add(
        InlineKeyboardButton(KEY_MARKUP['USERS_LIST'], callback_data="users_list"),
        InlineKeyboardButton(KEY_MARKUP['ADD_USER'], callback_data="add_user"),
        InlineKeyboardButton(KEY_MARKUP['SEARCH_USER'], callback_data="search_user"),
        InlineKeyboardButton(KEY_MARKUP['EDIT_USER'], callback_data="edit_user"),
        InlineKeyboardButton(KEY_MARKUP['BACK'], callback_data="back_to_main")
    )
    return markup

# Users List Keyboard
def users_list_markup(users, edit_mode=False, search_mode=False):
    markup = InlineKeyboardMarkup()
    markup.row_width = 2
    for user in users:
        telegram_id = user['telegram_id']
        name = user.get('full_name', 'Unknown')
        callback_prefix = "user_item:Edit" if edit_mode else "user_item:User"
        markup.add(InlineKeyboardButton(name, callback_data=f"{callback_prefix}:{telegram_id}"))
    
    if search_mode:
        markup.add(InlineKeyboardButton(KEY_MARKUP['BACK'], callback_data="back_to_users_management"))
    else:
        markup.add(InlineKeyboardButton(KEY_MARKUP['BACK'], callback_data="back_to_users_management"))
    return markup

# User Info Keyboard
def user_info_markup(telegram_id):
    markup = InlineKeyboardMarkup()
    markup.row_width = 2
    markup.add(
        InlineKeyboardButton(KEY_MARKUP['EDIT_USER'], callback_data=f"user_item:Edit:{telegram_id}"),
        InlineKeyboardButton(KEY_MARKUP['DELETE_USER'], callback_data=f"confirm_delete_user:{telegram_id}"),
        InlineKeyboardButton(KEY_MARKUP['BACK'], callback_data="back_to_users_management")
    )
    return markup

# Edit User Keyboard
def edit_user_markup(telegram_id):
    markup = InlineKeyboardMarkup()
    markup.row_width = 2
    markup.add(
        InlineKeyboardButton(KEY_MARKUP['USERS_EDIT_NAME'], callback_data=f"user_edit_name:{telegram_id}"),
        InlineKeyboardButton(KEY_MARKUP['USERS_EDIT_LIMIT'], callback_data=f"user_edit_limit:{telegram_id}"),
        InlineKeyboardButton(KEY_MARKUP['USERS_EDIT_DAYS'], callback_data=f"user_edit_days:{telegram_id}"),
        InlineKeyboardButton(KEY_MARKUP['DELETE_USER'], callback_data=f"confirm_delete_user:{telegram_id}"),
        InlineKeyboardButton(KEY_MARKUP['BACK'], callback_data="back_to_users_management")
    )
    return markup

# Confirm Delete User Keyboard
def confirm_delete_user_markup(telegram_id):
    markup = InlineKeyboardMarkup()
    markup.row_width = 2
    markup.add(
        InlineKeyboardButton(KEY_MARKUP['YES'], callback_data=f"delete_user:{telegram_id}"),
        InlineKeyboardButton(KEY_MARKUP['NO'], callback_data="back_to_users_management")
    )
    return markup

# Servers Management Keyboard
def servers_management_markup(servers):
    markup = InlineKeyboardMarkup()
    markup.row_width = 2
    markup.add(
        InlineKeyboardButton(KEY_MARKUP['ADD_SERVER'], callback_data="add_server"),
        InlineKeyboardButton(KEY_MARKUP['EDIT_SERVER'], callback_data="edit_server"),
        InlineKeyboardButton(KEY_MARKUP['SERVERS_LIST'], callback_data="servers_list"),
        InlineKeyboardButton(KEY_MARKUP['BACK'], callback_data="back_to_main")
    )
    return markup

# Servers List Keyboard
def servers_list_markup(servers, edit_mode=False):
    markup = InlineKeyboardMarkup()
    markup.row_width = 2
    for server in servers:
        server_id = server['id']
        title = server['title']
        callback_prefix = "server_item:Edit" if edit_mode else "server_item:Server"
        markup.add(InlineKeyboardButton(title, callback_data=f"{callback_prefix}:{server_id}"))
    markup.add(InlineKeyboardButton(KEY_MARKUP['BACK'], callback_data="back_to_servers_management"))
    return markup

# Server Info Keyboard
def server_info_markup(server_id):
    markup = InlineKeyboardMarkup()
    markup.row_width = 2
    markup.add(
        InlineKeyboardButton(KEY_MARKUP['EDIT_SERVER'], callback_data=f"server_item:Edit:{server_id}"),
        InlineKeyboardButton(KEY_MARKUP['DELETE_SERVER'], callback_data=f"confirm_delete_server:{server_id}"),
        InlineKeyboardButton(KEY_MARKUP['SERVERS_PLANS_LIST'], callback_data=f"server_item:Plans:{server_id}"),
        InlineKeyboardButton(KEY_MARKUP['BACK'], callback_data="back_to_servers_management")
    )
    return markup

# Edit Server Keyboard
def edit_server_markup(server_id):
    markup = InlineKeyboardMarkup()
    markup.row_width = 2
    markup.add(
        InlineKeyboardButton(KEY_MARKUP['SERVERS_EDIT_TITLE'], callback_data=f"server_edit_title:{server_id}"),
        InlineKeyboardButton(KEY_MARKUP['SERVERS_EDIT_URL'], callback_data=f"server_edit_url:{server_id}"),
        InlineKeyboardButton(KEY_MARKUP['SERVERS_EDIT_USER_LIMIT'], callback_data=f"server_edit_user_limit:{server_id}"),
        InlineKeyboardButton(KEY_MARKUP['DELETE_SERVER'], callback_data=f"confirm_delete_server:{server_id}"),
        InlineKeyboardButton(KEY_MARKUP['BACK'], callback_data="back_to_servers_management")
    )
    return markup

# Confirm Delete Server Keyboard
def confirm_delete_server_markup(server_id):
    markup = InlineKeyboardMarkup()
    markup.row_width = 2
    markup.add(
        InlineKeyboardButton(KEY_MARKUP['YES'], callback_data=f"delete_server:{server_id}"),
        InlineKeyboardButton(KEY_MARKUP['NO'], callback_data="back_to_servers_management")
    )
    return markup

# Plans Management Keyboard
def plans_management_markup(plans):
    markup = InlineKeyboardMarkup()
    markup.row_width = 2
    markup.add(
        InlineKeyboardButton(KEY_MARKUP['ADD_PLAN'], callback_data="add_plan"),
        InlineKeyboardButton(KEY_MARKUP['EDIT_PLAN'], callback_data="edit_plan"),
        InlineKeyboardButton(KEY_MARKUP['PLANS_LIST'], callback_data="plans_list"),
        InlineKeyboardButton(KEY_MARKUP['BACK'], callback_data="back_to_main")
    )
    return markup

# Plans List Keyboard
def plans_list_markup(plans, server_id=None, edit_mode=False):
    markup = InlineKeyboardMarkup()
    markup.row_width = 2
    for plan in plans:
        plan_id = plan['id']
        name = plan['name']
        callback_prefix = "plan_item:Edit" if edit_mode else "plan_item:Plan"
        markup.add(InlineKeyboardButton(name, callback_data=f"{callback_prefix}:{plan_id}"))
    
    if server_id:
        markup.add(InlineKeyboardButton(KEY_MARKUP['BACK'], callback_data=f"back_to_server_list_of_plans:{server_id}"))
    else:
        markup.add(InlineKeyboardButton(KEY_MARKUP['BACK'], callback_data="back_to_plans_management"))
    return markup

# Plan Info Keyboard
def plan_info_markup(plan_id):
    markup = InlineKeyboardMarkup()
    markup.row_width = 2
    markup.add(
        InlineKeyboardButton(KEY_MARKUP['EDIT_PLAN'], callback_data=f"plan_item:Edit:{plan_id}"),
        InlineKeyboardButton(KEY_MARKUP['DELETE_PLAN'], callback_data=f"confirm_delete_plan:{plan_id}"),
        InlineKeyboardButton(KEY_MARKUP['BACK'], callback_data="back_to_plans_management")
    )
    return markup

# Edit Plan Keyboard
def edit_plan_markup(plan_id):
    markup = InlineKeyboardMarkup()
    markup.row_width = 2
    markup.add(
        InlineKeyboardButton(KEY_MARKUP['PLANS_EDIT_NAME'], callback_data=f"plan_edit_name:{plan_id}"),
        InlineKeyboardButton(KEY_MARKUP['PLANS_EDIT_SIZE'], callback_data=f"plan_edit_size:{plan_id}"),
        InlineKeyboardButton(KEY_MARKUP['PLANS_EDIT_DAYS'], callback_data=f"plan_edit_days:{plan_id}"),
        InlineKeyboardButton(KEY_MARKUP['PLANS_EDIT_PRICE'], callback_data=f"plan_edit_price:{plan_id}"),
        InlineKeyboardButton(KEY_MARKUP['DELETE_PLAN'], callback_data=f"confirm_delete_plan:{plan_id}"),
        InlineKeyboardButton(KEY_MARKUP['BACK'], callback_data="back_to_plans_management")
    )
    return markup

# Confirm Delete Plan Keyboard
def confirm_delete_plan_markup(plan_id):
    markup = InlineKeyboardMarkup()
    markup.row_width = 2
    markup.add(
        InlineKeyboardButton(KEY_MARKUP['YES'], callback_data=f"delete_plan:{plan_id}"),
        InlineKeyboardButton(KEY_MARKUP['NO'], callback_data="back_to_plans_management")
    )
    return markup

# Orders Management Keyboard
def orders_management_markup(orders):
    markup = InlineKeyboardMarkup()
    markup.row_width = 2
    markup.add(
        InlineKeyboardButton(KEY_MARKUP['ORDERS_LIST'], callback_data="orders_list"),
        InlineKeyboardButton(KEY_MARKUP['SEARCH_ORDER'], callback_data="search_order"),
        InlineKeyboardButton(KEY_MARKUP['BACK'], callback_data="back_to_main")
    )
    return markup

# Orders List Keyboard
def orders_list_markup(orders):
    markup = InlineKeyboardMarkup()
    markup.row_width = 2
    for order in orders:
        order_id = order['id']
        # You might want to show more details about the order
        markup.add(InlineKeyboardButton(f"Order {order_id}", callback_data=f"order_item:{order_id}"))
    markup.add(InlineKeyboardButton(KEY_MARKUP['BACK'], callback_data="back_to_orders_management"))
    return markup

# Order Info Keyboard
def bot_order_info_markup(order_id):
    markup = InlineKeyboardMarkup()
    markup.row_width = 2
    markup.add(
        InlineKeyboardButton(KEY_MARKUP['BACK'], callback_data="back_to_orders_management")
    )
    return markup

# Payments Management Keyboard
def payments_management_markup(payments):
    markup = InlineKeyboardMarkup()
    markup.row_width = 2
    markup.add(
        InlineKeyboardButton(KEY_MARKUP['PAYMENTS_LIST'], callback_data="payments_list"),
        InlineKeyboardButton(KEY_MARKUP['SEARCH_PAYMENT'], callback_data="search_payment"),
        InlineKeyboardButton(KEY_MARKUP['CONFIRMED_PAYMENTS'], callback_data="confirmed_payments"),
        InlineKeyboardButton(KEY_MARKUP['UNCONFIRMED_PAYMENTS'], callback_data="unconfirmed_payments"),
        InlineKeyboardButton(KEY_MARKUP['PENDING_PAYMENTS'], callback_data="pending_payments"),
        InlineKeyboardButton(KEY_MARKUP['CARD_PAYMENTS'], callback_data="card_payments"),
        InlineKeyboardButton(KEY_MARKUP['DIGITAL_PAYMENTS'], callback_data="digital_payments"),
        InlineKeyboardButton(KEY_MARKUP['BACK'], callback_data="back_to_main")
    )
    return markup

# Payments List Keyboard
def payments_list_markup(payments):
    markup = InlineKeyboardMarkup()
    markup.row_width = 2
    for payment in payments:
        payment_id = payment['id']
        # You might want to show more details about the payment
        markup.add(InlineKeyboardButton(f"Payment {payment_id}", callback_data=f"payment_item:{payment_id}"))
    markup.add(InlineKeyboardButton(KEY_MARKUP['BACK'], callback_data="back_to_payments_management"))
    return markup

# Change Status Payment By Admin Keyboard
def change_status_payment_by_admin(payment_id):
    markup = InlineKeyboardMarkup()
    markup.row_width = 2
    markup.add(
        InlineKeyboardButton(KEY_MARKUP['CONFIRM_PAYMENT'], callback_data=f"change_status_payment:{payment_id}:Confirm"),
        InlineKeyboardButton(KEY_MARKUP['CANCEL_PAYMENT'], callback_data=f"change_status_payment:{payment_id}:Cancel"),
        InlineKeyboardButton(KEY_MARKUP['BACK'], callback_data="back_to_payments_management")
    )
    return markup

# Confirm Change Status Payment By Admin Keyboard
def confirm_change_status_payment_by_admin(payment_id):
    markup = InlineKeyboardMarkup()
    markup.row_width = 2
    markup.add(
        InlineKeyboardButton(KEY_MARKUP['YES'], callback_data=f"confirm_change_status_payment:{payment_id}"),
        InlineKeyboardButton(KEY_MARKUP['NO'], callback_data="back_to_payments_management")
    )
    return markup

# Search User Keyboard
def search_user_markup():
    markup = InlineKeyboardMarkup()
    markup.row_width = 2
    markup.add(
        InlineKeyboardButton(KEY_MARKUP['SEARCH_USER_BY_NAME'], callback_data="search_user_by_name"),
        InlineKeyboardButton(KEY_MARKUP['SEARCH_USER_BY_TELEGRAM_ID'], callback_data="search_user_by_telegram_id"),
        InlineKeyboardButton(KEY_MARKUP['SEARCH_USER_BY_UUID'], callback_data="search_user_by_uuid"),
        InlineKeyboardButton(KEY_MARKUP['SEARCH_USER_BY_CONFIG'], callback_data="search_user_by_config"),
        InlineKeyboardButton(KEY_MARKUP['BACK'], callback_data="back_to_users_management")
    )
    return markup

# Sub Search Info Keyboard
def sub_search_info_markup(uuid, bot_user):
    markup = InlineKeyboardMarkup()
    markup.row_width = 2
    markup.add(
        InlineKeyboardButton(KEY_MARKUP['BACK'], callback_data="back_to_main")
    )
    return markup

# Users Bot Management Keyboard
def users_bot_management_markup(settings):
    markup = InlineKeyboardMarkup()
    markup.row_width = 2
    markup.add(
        InlineKeyboardButton(KEY_MARKUP['USERS_BOT_SETTINGS'], callback_data="users_bot_settings"),
        InlineKeyboardButton(KEY_MARKUP['USERS_BOT_SETTINGS_TEST_SUB'], callback_data="users_bot_settings_test_sub"),
        InlineKeyboardButton(KEY_MARKUP['USERS_BOT_SETTINGS_NOTIF_REMINDER'], callback_data="users_bot_settings_notif_reminder"),
        InlineKeyboardButton(KEY_MARKUP['USERS_BOT_SETTINGS_RENEWAL_METHOD'], callback_data="users_bot_settings_renewal_method"),
        InlineKeyboardButton(KEY_MARKUP['USERS_BOT_SETTINGS_VISIBLE_SUB'], callback_data="users_bot_settings_visible_sub"),
        InlineKeyboardButton(KEY_MARKUP['USERS_BOT_SETTINGS_PANEL_MANUAL'], callback_data="users_bot_settings_panel_manual"),
        InlineKeyboardButton(KEY_MARKUP['USERS_BOT_EDIT_OWNER_INFO'], callback_data="users_bot_edit_owner_info"),
        InlineKeyboardButton(KEY_MARKUP['BACK'], callback_data="back_to_main")
    )
    return markup

# Users Bot Management Settings Keyboard
def users_bot_management_settings_markup(settings):
    markup = InlineKeyboardMarkup()
    markup.row_width = 2
    
    # Status indicators
    status_hyperlink = "✅" if settings.get('visible_hiddify_hyperlink', False) else "❌"
    status_three_rand = "✅" if settings.get('three_random_num_price', False) else "❌"
    status_force_join = "✅" if settings.get('force_join_channel', False) else "❌"
    status_buy_sub = "✅" if settings.get('buy_subscription_status', False) else "❌"
    status_renewal_sub = "✅" if settings.get('renewal_subscription_status', False) else "❌"
    
    markup.add(
        InlineKeyboardButton(f"{KEY_MARKUP['USERS_BOT_SETTINGS_SHOW_HIDI_LINK']}| {status_hyperlink}",
                             callback_data=f"users_bot_settings_hyperlink:{int(settings.get('visible_hiddify_hyperlink', False))}"),
        InlineKeyboardButton(f"{KEY_MARKUP['USERS_BOT_SETTINGS_SHOW_THREE_RAND']}| {status_three_rand}",
                             callback_data=f"users_bot_settings_three_rand_price:{int(settings.get('three_random_num_price', False))}"),
        InlineKeyboardButton(f"{KEY_MARKUP['USERS_BOT_SETTINGS_FORCE_JOIN_CHANNEL']}| {status_force_join}",
                             callback_data=f"users_bot_settings_force_join:{int(settings.get('force_join_channel', False))}"),
        InlineKeyboardButton(f"{KEY_MARKUP['USERS_BOT_SETTINGS_BUY_SUBSCRIPTION']}| {status_buy_sub}",
                             callback_data=f"users_bot_settings_buy_sub:{int(settings.get('buy_subscription_status', False))}"),
        InlineKeyboardButton(f"{KEY_MARKUP['USERS_BOT_SETTINGS_RENEWAL_SUBSCRIPTION']}| {status_renewal_sub}",
                             callback_data=f"users_bot_settings_renewal_sub:{int(settings.get('renewal_subscription_status', False))}"),
        InlineKeyboardButton(KEY_MARKUP['USERS_BOT_SETTINGS_MIN_DEPO'], callback_data="users_bot_settings_min_depo"),
        InlineKeyboardButton(KEY_MARKUP['USERS_BOT_SETTINGS_CHANNEL_ID'], callback_data="users_bot_settings_channel_id"),
        InlineKeyboardButton(KEY_MARKUP['USERS_BOT_SETTINGS_WELCOME_MSG'], callback_data="users_bot_settings_welcome_msg"),
        InlineKeyboardButton(KEY_MARKUP['BACK'], callback_data="back_to_users_bot_management")
    )
    return markup

# Users Bot Management Settings Test Sub Keyboard
def users_bot_management_settings_test_sub_markup(settings):
    markup = InlineKeyboardMarkup()
    markup.row_width = 2
    markup.add(
        InlineKeyboardButton(KEY_MARKUP['USERS_BOT_SETTINGS_TEST_SUB_DAYS'], callback_data="users_bot_settings_test_sub_days"),
        InlineKeyboardButton(KEY_MARKUP['USERS_BOT_SETTINGS_TEST_SUB_SIZE'], callback_data="users_bot_settings_test_sub_size"),
        InlineKeyboardButton(KEY_MARKUP['BACK'], callback_data="back_to_users_bot_settings")
    )
    return markup

# Users Bot Management Settings Notif Reminder Keyboard
def users_bot_management_settings_notif_reminder_markup(settings):
    markup = InlineKeyboardMarkup()
    markup.row_width = 2
    markup.add(
        InlineKeyboardButton(KEY_MARKUP['USERS_BOT_SETTINGS_REMINDER_DAYS'], callback_data="users_bot_settings_reminder_days"),
        InlineKeyboardButton(KEY_MARKUP['USERS_BOT_SETTINGS_REMINDER_USAGE'], callback_data="users_bot_settings_reminder_usage"),
        InlineKeyboardButton(KEY_MARKUP['BACK'], callback_data="back_to_users_bot_settings")
    )
    return markup

# Users Bot Management Settings Renewal Method Keyboard
def users_bot_management_settings_renewal_method_markup(settings):
    markup = InlineKeyboardMarkup()
    markup.row_width = 2
    markup.add(
        InlineKeyboardButton(KEY_MARKUP['USERS_BOT_SETTINGS_RENEWAL_METHOD_ADVANCED_DAYS'], callback_data="users_bot_settings_renewal_method_advanced_days"),
        InlineKeyboardButton(KEY_MARKUP['USERS_BOT_SETTINGS_RENEWAL_METHOD_ADVANCED_USAGE'], callback_data="users_bot_settings_renewal_method_advanced_usage"),
        InlineKeyboardButton(KEY_MARKUP['BACK'], callback_data="back_to_users_bot_settings")
    )
    return markup

# Users Bot Management Settings Visible Sub Keyboard
def users_bot_management_settings_visible_sub_markup(settings):
    markup = InlineKeyboardMarkup()
    markup.row_width = 2
    
    # Status indicators for visibility settings
    status_conf_dir = "✅" if settings.get('visible_conf_dir', False) else "❌"
    status_conf_sub_auto = "✅" if settings.get('visible_conf_sub_auto', False) else "❌"
    status_conf_sub_url = "✅" if settings.get('visible_conf_sub_url', False) else "❌"
    status_conf_sub_qr = "✅" if settings.get('visible_conf_sub_qr', False) else "❌"
    status_conf_clash = "✅" if settings.get('visible_conf_clash', False) else "❌"
    status_conf_hiddify = "✅" if settings.get('visible_conf_hiddify', False) else "❌"
    status_conf_sub_sing_box = "✅" if settings.get('visible_conf_sub_sing_box', False) else "❌"
    status_conf_sub_full_sing_box = "✅" if settings.get('visible_conf_sub_full_sing_box', False) else "❌"
    
    markup.add(
        InlineKeyboardButton(f"{KEY_MARKUP['USERS_BOT_SETTINGS_VISIBLE_CONF_DIR']}| {status_conf_dir}",
                             callback_data=f"users_bot_settings_visible_conf_dir:{int(settings.get('visible_conf_dir', False))}"),
        InlineKeyboardButton(f"{KEY_MARKUP['USERS_BOT_SETTINGS_VISIBLE_CONF_SUB_AUTO']}| {status_conf_sub_auto}",
                             callback_data=f"users_bot_settings_visible_conf_sub_auto:{int(settings.get('visible_conf_sub_auto', False))}"),
        InlineKeyboardButton(f"{KEY_MARKUP['USERS_BOT_SETTINGS_VISIBLE_CONF_SUB_URL']}| {status_conf_sub_url}",
                             callback_data=f"users_bot_settings_visible_conf_sub_url:{int(settings.get('visible_conf_sub_url', False))}"),
        InlineKeyboardButton(f"{KEY_MARKUP['USERS_BOT_SETTINGS_VISIBLE_CONF_SUB_QR']}| {status_conf_sub_qr}",
                             callback_data=f"users_bot_settings_visible_conf_sub_qr:{int(settings.get('visible_conf_sub_qr', False))}"),
        InlineKeyboardButton(f"{KEY_MARKUP['USERS_BOT_SETTINGS_VISIBLE_CONF_CLASH']}| {status_conf_clash}",
                             callback_data=f"users_bot_settings_visible_conf_clash:{int(settings.get('visible_conf_clash', False))}"),
        InlineKeyboardButton(f"{KEY_MARKUP['USERS_BOT_SETTINGS_VISIBLE_CONF_HIDDIFY']}| {status_conf_hiddify}",
                             callback_data=f"users_bot_settings_visible_conf_hiddify:{int(settings.get('visible_conf_hiddify', False))}"),
        InlineKeyboardButton(f"{KEY_MARKUP['USERS_BOT_SETTINGS_VISIBLE_CONF_SUB_SING_BOX']}| {status_conf_sub_sing_box}",
                             callback_data=f"users_bot_settings_visible_conf_sub_sing_box:{int(settings.get('visible_conf_sub_sing_box', False))}"),
        InlineKeyboardButton(f"{KEY_MARKUP['USERS_BOT_SETTINGS_VISIBLE_CONF_SUB_FULL_SING_BOX']}| {status_conf_sub_full_sing_box}",
                             callback_data=f"users_bot_settings_visible_conf_sub_full_sing_box:{int(settings.get('visible_conf_sub_full_sing_box', False))}"),
        InlineKeyboardButton(KEY_MARKUP['BACK'], callback_data="back_to_users_bot_settings")
    )
    return markup

# Users Bot Management Settings Panel Manual Keyboard
def users_bot_management_settings_panel_manual_markup(settings):
    markup = InlineKeyboardMarkup()
    markup.row_width = 2
    markup.add(
        InlineKeyboardButton(KEY_MARKUP['USERS_BOT_SETTINGS_FAQ_MSG'], callback_data="users_bot_settings_faq_msg"),
        InlineKeyboardButton(KEY_MARKUP['USERS_BOT_SETTINGS_HELP_MSG'], callback_data="users_bot_settings_help_msg"),
        InlineKeyboardButton(KEY_MARKUP['BACK'], callback_data="back_to_users_bot_settings")
    )
    return markup

# Users Bot Edit Owner Info Keyboard
def users_bot_edit_owner_info_markup(owner_info_data):
    markup = InlineKeyboardMarkup()
    markup.row_width = 2
    markup.add(
        InlineKeyboardButton(KEY_MARKUP['USERS_BOT_OWNER_INFO_EDIT_USERNAME'], callback_data="users_bot_owner_info_edit_username"),
        InlineKeyboardButton(KEY_MARKUP['USERS_BOT_OWNER_INFO_EDIT_CARD_NUMBER'], callback_data="users_bot_owner_info_edit_card_number"),
        InlineKeyboardButton(KEY_MARKUP['USERS_BOT_OWNER_INFO_EDIT_CARD_OWNER'], callback_data="users_bot_owner_info_edit_card_owner"),
        InlineKeyboardButton(KEY_MARKUP['BACK'], callback_data="back_to_users_bot_management")
    )
    return markup

# While Edit User Keyboard
def while_edit_user_markup():
    markup = InlineKeyboardMarkup()
    markup.row_width = 1
    markup.add(InlineKeyboardButton(KEY_MARKUP['CANCEL'], callback_data="cancel"))
    return markup

# Cancel Keyboard
def cancel_markup():
    markup = InlineKeyboardMarkup()
    markup.row_width = 1
    markup.add(InlineKeyboardButton(KEY_MARKUP['CANCEL'], callback_data="cancel"))
    return markup

# Force Join Channel Keyboard
def force_join_channel_markup(channel_id):
    markup = InlineKeyboardMarkup()
    markup.row_width = 1
    markup.add(
        InlineKeyboardButton(KEY_MARKUP['JOIN_CHANNEL'], url=f"https://t.me/{channel_id[1:]}"), # Remove @
        InlineKeyboardButton(KEY_MARKUP['FORCE_JOIN_CHANNEL_ACCEPTED'], callback_data="force_join_channel_accepted")
    )
    return markup

# Send Ticket To Admin Keyboard
def send_ticket_to_admin(user_id):
    markup = InlineKeyboardMarkup()
    markup.row_width = 2
    markup.add(
        InlineKeyboardButton(KEY_MARKUP['ANSWER'], callback_data=f"answer_to_user:{user_id}"),
        InlineKeyboardButton(KEY_MARKUP['SEND_MESSAGE'], callback_data=f"send_message_to_user:{user_id}"),
        InlineKeyboardButton(KEY_MARKUP['BACK'], callback_data="back_to_main")
    )
    return markup

# Answer To User Keyboard
def answer_to_user_markup(user_id):
    markup = InlineKeyboardMarkup()
    markup.row_width = 1
    markup.add(InlineKeyboardButton(KEY_MARKUP['BACK'], callback_data="back_to_main"))
    return markup

# Online Payment Markup (Placeholder)
def online_payment_markup(payment_link):
    markup = InlineKeyboardMarkup()
    markup.row_width = 1
    markup.add(
        InlineKeyboardButton(KEY_MARKUP['PAY_ONLINE'], url=payment_link),
        InlineKeyboardButton(KEY_MARKUP['BACK'], callback_data="back_to_main")
    )
    return markup

# Affiliate System Markup (Placeholder)
def affiliate_system_markup():
    markup = InlineKeyboardMarkup()
    markup.row_width = 1
    markup.add(
        InlineKeyboardButton(KEY_MARKUP['BACK'], callback_data="back_to_main")
    )
    return markup

# Not Enough Balance Markup (Placeholder)
def not_enough_balance_markup(needed_amount):
    markup = InlineKeyboardMarkup()
    markup.row_width = 1
    # This would typically offer options like "Pay difference" or "Choose another plan"
    markup.add(
        InlineKeyboardButton(KEY_MARKUP['BACK'], callback_data="back_to_main")
    )
    return markup
