# UserBot/markups.py
# Description: This file contains all the inline keyboards and reply markups used in the user bot.
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from UserBot.content import KEY_MARKUP
from Utils.utils import all_configs_settings

# Main Menu Keyboard
def main_menu_keyboard_markup():
    markup = InlineKeyboardMarkup()
    markup.row_width = 2
    markup.add(
        InlineKeyboardButton(KEY_MARKUP['SUBSCRIPTION_STATUS'], callback_data="users_bot_my_subscriptions"),
        InlineKeyboardButton(KEY_MARKUP['BUY_SUBSCRIPTION'], callback_data="users_bot_buy_subscription"),
        InlineKeyboardButton(KEY_MARKUP['FREE_TEST'], callback_data="users_bot_free_test"),
        InlineKeyboardButton(KEY_MARKUP['WALLET'], callback_data="users_bot_wallet"),
        InlineKeyboardButton(KEY_MARKUP['SEND_TICKET'], callback_data="users_bot_send_ticket_to_support"),
        InlineKeyboardButton(KEY_MARKUP['MANUAL'], callback_data="users_bot_help"),
        InlineKeyboardButton(KEY_MARKUP['FAQ'], callback_data="users_bot_faq"),
        InlineKeyboardButton(KEY_MARKUP['SUPPORT'], callback_data="users_bot_support")
    )
    return markup

# Users Bot Subscription URL User List Keyboard
def users_bot_sub_url_user_list_markup(subscriptions, renewal_mode=False):
    markup = InlineKeyboardMarkup()
    markup.row_width = 1
    for sub in subscriptions:
        sub_id = sub.get('sub_id') or sub.get('uuid') # Use sub_id or uuid
        name = sub.get('name', 'Unknown')
        callback_data = f"users_bot_sub_url_user_list:{sub_id}"
        if renewal_mode:
            callback_data += ":renewal"
        markup.add(InlineKeyboardButton(name, callback_data=callback_data))
    markup.add(InlineKeyboardButton(KEY_MARKUP['BACK'], callback_data="back_to_main"))
    return markup

# Users Bot Subscription Info Keyboard
def users_bot_sub_info_markup(uuid):
    markup = InlineKeyboardMarkup()
    markup.row_width = 2
    markup.add(
        InlineKeyboardButton(KEY_MARKUP['CONFIGS_LIST'], callback_data=f"users_bot_config_server_info:{uuid}"),
        InlineKeyboardButton(KEY_MARKUP['RENEWAL_SUBSCRIPTION'], callback_data=f"renewal_subscription:{uuid}"),
        InlineKeyboardButton(KEY_MARKUP['UPDATE_SUBSCRIPTION_INFO'], callback_data=f"users_bot_sub_info:{uuid}"),
        InlineKeyboardButton(KEY_MARKUP['BACK'], callback_data="back_to_subscriptions_list")
    )
    return markup

# Users Bot Config Server Info Keyboard
def users_bot_config_server_info_markup(uuid):
    markup = InlineKeyboardMarkup()
    markup.row_width = 2
    # These buttons will be dynamically shown/hidden based on settings
    settings = all_configs_settings()
    
    buttons = []
    if settings.get('visible_conf_dir', True):
        buttons.append(InlineKeyboardButton(KEY_MARKUP['CONFIGS_DIR'], callback_data=f"users_bot_config_dir:{uuid}"))
    if settings.get('visible_conf_sub_auto', True):
        buttons.append(InlineKeyboardButton(KEY_MARKUP['CONFIGS_SUB_AUTO'], callback_data=f"users_bot_config_sub_auto:{uuid}"))
    if settings.get('visible_conf_sub_url', True):
        buttons.append(InlineKeyboardButton(KEY_MARKUP['CONFIGS_SUB'], callback_data=f"users_bot_config_sub:{uuid}"))
    if settings.get('visible_conf_sub_b64', True):
        buttons.append(InlineKeyboardButton(KEY_MARKUP['CONFIGS_SUB_B64'], callback_data=f"users_bot_config_sub_b64:{uuid}"))
    if settings.get('visible_conf_clash', True):
        buttons.append(InlineKeyboardButton(KEY_MARKUP['CONFIGS_CLASH'], callback_data=f"users_bot_config_clash:{uuid}"))
    if settings.get('visible_conf_hiddify', True):
        buttons.append(InlineKeyboardButton(KEY_MARKUP['CONFIGS_HIDDIFY'], callback_data=f"users_bot_config_hiddify:{uuid}"))
    if settings.get('visible_conf_sing_box', True):
        buttons.append(InlineKeyboardButton(KEY_MARKUP['CONFIGS_SING_BOX'], callback_data=f"users_bot_config_sing_box:{uuid}"))
    if settings.get('visible_conf_full_sing_box', True):
        buttons.append(InlineKeyboardButton(KEY_MARKUP['CONFIGS_FULL_SING_BOX'], callback_data=f"users_bot_config_full_sing_box:{uuid}"))
    
    # Add QR button
    buttons.append(InlineKeyboardButton(KEY_MARKUP['TO_QR'], callback_data=f"users_bot_config_to_qr:{uuid}"))
    
    # Add buttons to markup (2 per row)
    for i in range(0, len(buttons), 2):
        if i+1 < len(buttons):
            markup.add(buttons[i], buttons[i+1])
        else:
            markup.add(buttons[i])
            
    markup.add(InlineKeyboardButton(KEY_MARKUP['BACK'], callback_data=f"users_bot_sub_info:{uuid}"))
    return markup

# Users Bot List Plans Keyboard
def users_bot_list_plans_markup(plans, renewal_mode=False, uuid=None):
    markup = InlineKeyboardMarkup()
    markup.row_width = 1
    for plan in plans:
        plan_id = plan['id']
        name = plan['name']
        size_gb = plan['size_gb']
        days = plan['days']
        price = plan['price']
        # Format price using utils function if needed
        from Utils.utils import rial_to_toman
        price_str = f"{rial_to_toman(price)} {KEY_MARKUP['TOMAN']}"
        button_text = f"{name} - {size_gb}GB - {days}{KEY_MARKUP['DAY_EXPIRE']} - {price_str}"
        callback_data = f"users_bot_list_plans:{plan_id}"
        if renewal_mode and uuid:
            callback_data += f":{uuid}" # Pass uuid for renewal
        markup.add(InlineKeyboardButton(button_text, callback_data=callback_data))
    back_callback = "back_to_subscriptions_list" if renewal_mode else "back_to_main"
    markup.add(InlineKeyboardButton(KEY_MARKUP['BACK'], callback_data=back_callback))
    return markup

# Users Bot Plan Info Keyboard
def users_bot_plan_info_markup(plan_id):
    markup = InlineKeyboardMarkup()
    markup.row_width = 2
    markup.add(
        InlineKeyboardButton(KEY_MARKUP['BUY_PLAN'], callback_data=f"users_bot_plan_info:{plan_id}"),
        InlineKeyboardButton(KEY_MARKUP['BACK'], callback_data="back_to_main") # This should go back to plans list
    )
    return markup

# Confirm Buy Plan Keyboard
def confirm_buy_plan_markup(plan_id, renewal=False, uuid=None):
    markup = InlineKeyboardMarkup()
    markup.row_width = 2
    if renewal and uuid:
        # For renewal, pass both plan_id and uuid
        callback_data = f"confirm_renewal_from_wallet:{plan_id}_{uuid}"
        markup.add(InlineKeyboardButton(KEY_MARKUP['BUY_FROM_WALLET'], callback_data=callback_data))
    else:
        markup.add(InlineKeyboardButton(KEY_MARKUP['BUY_FROM_WALLET'], callback_data=f"confirm_buy_plan:{plan_id}"))
    markup.add(InlineKeyboardButton(KEY_MARKUP['BACK'], callback_data="back_to_main")) # Adjust back callback as needed
    return markup

# Users Bot Wallet Keyboard
def users_bot_wallet_markup():
    markup = InlineKeyboardMarkup()
    markup.row_width = 2
    markup.add(
        InlineKeyboardButton(KEY_MARKUP['INCREASE_WALLET_BALANCE'], callback_data="users_bot_balance_increase"),
        InlineKeyboardButton(KEY_MARKUP['BACK'], callback_data="back_to_main")
    )
    return markup

# Users Bot Balance Increase Keyboard
def users_bot_balance_increase_markup(amount):
    markup = InlineKeyboardMarkup()
    markup.row_width = 2
    # This would typically show options like "Pay Online" and "Card Payment"
    # For now, we'll just show "Card Payment" which shows owner info
    markup.add(
        InlineKeyboardButton(KEY_MARKUP['BUY_PLAN'], callback_data=f"users_bot_balance_increase_wallet:{amount}"), # Card payment
        InlineKeyboardButton(KEY_MARKUP['ONLINE_PAYMENT'], callback_data=f"online_payment_gateway:{amount}"), # Online payment
        InlineKeyboardButton(KEY_MARKUP['APPLY_COUPON'], callback_data="apply_coupon"), # Apply coupon
        InlineKeyboardButton(KEY_MARKUP['BACK'], callback_data="back_to_main")
    )
    return markup

# Users Bot User Info Keyboard
def users_bot_user_info_markup():
    markup = InlineKeyboardMarkup()
    markup.row_width = 2
    markup.add(
        InlineKeyboardButton(KEY_MARKUP['BACK'], callback_data="back_to_main")
    )
    return markup

# Users Bot Help Keyboard
def users_bot_help_markup():
    markup = InlineKeyboardMarkup()
    markup.row_width = 2
    markup.add(
        InlineKeyboardButton(KEY_MARKUP['MANUAL_ANDROID'], callback_data="users_bot_help:android"),
        InlineKeyboardButton(KEY_MARKUP['MANUAL_IOS'], callback_data="users_bot_help:ios"),
        InlineKeyboardButton(KEY_MARKUP['MANUAL_WIN'], callback_data="users_bot_help:win"),
        InlineKeyboardButton(KEY_MARKUP['MANUAL_MAC'], callback_data="users_bot_help:mac"),
        InlineKeyboardButton(KEY_MARKUP['MANUAL_LIN'], callback_data="users_bot_help:linux"),
        InlineKeyboardButton(KEY_MARKUP['BACK'], callback_data="back_to_main")
    )
    return markup

# Users Bot FAQ Keyboard
def users_bot_faq_markup():
    markup = InlineKeyboardMarkup()
    markup.row_width = 1
    markup.add(
        InlineKeyboardButton(KEY_MARKUP['BACK'], callback_data="back_to_main")
    )
    return markup

# Users Bot Support Keyboard
def users_bot_support_markup():
    markup = InlineKeyboardMarkup()
    markup.row_width = 1
    markup.add(
        InlineKeyboardButton(KEY_MARKUP['SEND_TICKET_TO_SUPPORT'], callback_data="users_bot_send_ticket_to_support"),
        InlineKeyboardButton(KEY_MARKUP['BACK'], callback_data="back_to_main")
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
    # Remove @ from channel_id if present
    channel_url = channel_id[1:] if channel_id.startswith('@') else channel_id
    markup.add(
        InlineKeyboardButton(KEY_MARKUP['JOIN_CHANNEL'], url=f"https://t.me/{channel_url}"),
        InlineKeyboardButton(KEY_MARKUP['FORCE_JOIN_CHANNEL_ACCEPTED'], callback_data="force_join_channel_accepted")
    )
    return markup

# Send Ticket To Admin Keyboard (Placeholder - might not be used in user bot)
def send_ticket_to_admin(user_id):
    markup = InlineKeyboardMarkup()
    markup.row_width = 2
    # This is more relevant for admin bot
    markup.add(
        InlineKeyboardButton(KEY_MARKUP['ANSWER'], callback_data=f"answer_to_user:{user_id}"),
        InlineKeyboardButton(KEY_MARKUP['SEND_MESSAGE'], callback_data=f"send_message_to_user:{user_id}"),
        InlineKeyboardButton(KEY_MARKUP['BACK'], callback_data="back_to_main")
    )
    return markup

# Answer To User Keyboard (Placeholder - might not be used in user bot)
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

# Not Enough Balance Markup (Placeholder)
def not_enough_balance_markup(needed_amount):
    markup = InlineKeyboardMarkup()
    markup.row_width = 1
    # This would typically offer options like "Pay difference online" or "Choose another plan"
    markup.add(
        InlineKeyboardButton(KEY_MARKUP['ONLINE_PAYMENT'], callback_data=f"online_payment_gateway:{needed_amount}"),
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
