# UserBot/templates.py
# Description: This file contains all the templates used in the user bot.
from config import LANG
from UserBot.content import MESSAGES
from Utils.utils import rial_to_toman, toman_to_rial, all_configs_settings
from Database.dbManager import USERS_DB

# User Subscription Info Template
def user_info_template(sub_id, server, usr, header=""):
    """
    Template for displaying user subscription information.
    usr is now expected to be the data returned from the new Hiddify API.
    """
    # Handle hyperlink visibility setting
    settings_result = USERS_DB.find_bool_config(key='visible_hiddify_hyperlink')
    show_hyperlink = False
    if settings_result:
        setting = settings_result[0]
        show_hyperlink = setting.get('value', False)
    
    if show_hyperlink and usr.get('link'):
        user_name = f"<a href='{usr['link']}'> {usr.get('name', 'Unknown')} </a>"
    else:
        user_name = usr.get('name', 'Unknown')
    
    # Format usage
    current_usage = usr.get('usage', {}).get('current_usage_GB', 0)
    usage_limit = usr.get('usage', {}).get('usage_limit_GB', 0)
    
    # Format remaining days
    remaining_days = usr.get('remaining_day', 0)
    if remaining_days == 0:
        remaining_days_str = MESSAGES['USER_TIME_EXPIRED']
    elif remaining_days == 1:
        remaining_days_str = MESSAGES['USER_LAST_DAY']
    else:
        remaining_days_str = f"{remaining_days} {MESSAGES['DAY_EXPIRE']}"
    
    return f"""
{header}
{MESSAGES['USER_NAME']} {user_name}
{MESSAGES['SERVER']} {server.get('title', 'Unknown')}
{MESSAGES['INFO_USAGE']} {current_usage} {MESSAGES['OF']} {usage_limit} {MESSAGES['GB']}
{MESSAGES['INFO_REMAINING_DAYS']} {remaining_days_str}
{MESSAGES['INFO_ID']} <code>{sub_id}</code>
"""

# Wallet Info Template
def wallet_info_template(balance):
    """Template for displaying wallet balance."""
    if balance is None:
        balance = 0
    if balance == 0:
        return MESSAGES['ZERO_BALANCE']
    else:
        return f"""
{MESSAGES['WALLET_INFO_PART_1']} {rial_to_toman(balance)} {MESSAGES['WALLET_INFO_PART_2']}
"""

# Plan Info Template
def plan_info_template(plan, header=""):
    """Template for displaying plan information."""
    if not plan:
        return MESSAGES['UNKNOWN_ERROR']
        
    msg = f"""
{header}
{MESSAGES['PLAN_INFO']}

{MESSAGES['PLAN_INFO_SIZE']} {plan.get('size_gb', 'N/A')} {MESSAGES['GB']}
{MESSAGES['PLAN_INFO_DAYS']} {plan.get('days', 'N/A')} {MESSAGES['DAY_EXPIRE']}
{MESSAGES['PLAN_INFO_PRICE']} {rial_to_toman(plan.get('price', 0))} {MESSAGES['TOMAN']}
"""
    if plan.get('description'):
        msg += f"{MESSAGES['PLAN_INFO_DESC']} {plan['description']}"
    return msg

# Owner Info Template (For Payment)
def owner_info_template(card_number, card_holder_name, price, header=""):
    """Template for displaying owner information for manual payment."""
    card_number = card_number if card_number else "-"
    card_holder_name = card_holder_name if card_holder_name else "-"
    price = price if price else 0

    if LANG == 'FA':
        return f"""
{header}

💰لطفا دقیقا مبلغ: <code>{price}</code> {MESSAGES['RIAL']}
💴معادل: {rial_to_toman(price)} {MESSAGES['TOMAN']}
💳را به شماره کارت: <code>{card_number}</code>
👤به نام <b>{card_holder_name}</b> واریز کنید.

❗️بعد از واریز مبلغ، اسکرین شات از تراکنش را برای ما ارسال کنید.
"""
    elif LANG == 'EN':
        return f"""
{header}

💰Please pay exactly: <code>{price}</code> {MESSAGES['RIAL']}
💴Equivalent: {rial_to_toman(price)} {MESSAGES['TOMAN']}
💳To card number: <code>{card_number}</code>
👤Card owner: <b>{card_holder_name}</b>

❗️After paying the amount, send us a screenshot of the transaction.
"""

# Payment Received Template - Send to Admin
def payment_received_template(payment, user, header="", footer=""):
    """Template for notifying admin about a payment request."""
    username = f"@{user.get('username', '')}" if user.get('username') else MESSAGES['NOT_SET']
    name = user.get('full_name', user.get('telegram_id', 'Unknown'))

    if LANG == 'FA':
        return f"""
{header}

شناسه تراکنش: <code>{payment.get('id', 'N/A')}</code>
مبلغ تراکنش: <b>{rial_to_toman(payment.get('payment_amount', 0))}</b> {MESSAGES['TOMAN']}
{MESSAGES['INFO_USER_NAME']} <b>{name}</b>
{MESSAGES['INFO_USER_USERNAME']} {username}
{MESSAGES['INFO_USER_NUM_ID']} {user.get('telegram_id', 'N/A')}
---------------------
⬇️درخواست افزایش موجودی کیف پول⬇️

{footer}
"""
    elif LANG == 'EN':
        return f"""
{header}

Transaction ID: <code>{payment.get('id', 'N/A')}</code>
Transaction amount: <b>{rial_to_toman(payment.get('payment_amount', 0))}</b> {MESSAGES['TOMAN']}
{MESSAGES['INFO_USER_NAME']} <b>{name}</b>
{MESSAGES['INFO_USER_USERNAME']} {username}
{MESSAGES['INFO_USER_NUM_ID']} {user.get('telegram_id', 'N/A')}
---------------------
⬇️Request to increase wallet balance⬇️

{footer}
"""

# Help Guide Template
def connection_help_template(header=""):
    """Template for displaying connection help/software links."""
    if LANG == 'FA':
        return f"""
{header}

⭕️ نرم افزار های مورد نیاز برای اتصال به کانفیگ
    
📥اندروید:
<a href='https://play.google.com/store/apps/details?id=com.v2ray.ang'>V2RayNG</a>
<a href='https://play.google.com/store/apps/details?id=ang.hiddify.com'>HiddifyNG</a>

📥آی او اس:
<a href='https://apps.apple.com/us/app/streisand/id6450534064'>Streisand</a>
<a href='https://apps.apple.com/us/app/foxray/id6448898396'>Foxray</a>
<a href='https://apps.apple.com/us/app/v2box-v2ray-client/id6446814690'>V2box</a>

📥ویندوز:
<a href='https://github.com/MatsuriDayo/nekoray/releases'>Nekoray</a>
<a href='https://github.com/2dust/v2rayN/releases'>V2rayN</a>
<a href='https://github.com/hiddify/HiddifyN/releases'>HiddifyN</a>

📥مک و لینوکس:
<a href='https://github.com/MatsuriDayo/nekoray/releases'>Nekoray</a>
"""
    elif LANG == 'EN':
        return f"""
{header}

⭕️Required software for connecting to config

📥Android:
<a href='https://play.google.com/store/apps/details?id=com.v2ray.ang'>V2RayNG</a>
<a href='https://play.google.com/store/apps/details?id=ang.hiddify.com'>HiddifyNG</a>

📥iOS:
<a href='https://apps.apple.com/us/app/streisand/id6450534064'>Streisand</a>
<a href='https://apps.apple.com/us/app/foxray/id6448898396'>Foxray</a>
<a href='https://apps.apple.com/us/app/v2box-v2ray-client/id6446814690'>V2box</a>

📥Windows:
<a href='https://github.com/MatsuriDayo/nekoray/releases'>Nekoray</a>
<a href='https://github.com/2dust/v2rayN/releases'>V2rayN</a>
<a href='https://github.com/hiddify/HiddifyN/releases'>HiddifyN</a>

📥Mac and Linux:
<a href='https://github.com/MatsuriDayo/nekoray/releases'>Nekoray</a>
"""

# Alert Package Days Template
def package_days_expire_soon_template(sub_id, remaining_days):
    """Template for alerting user about expiring package days."""
    if LANG == 'FA':
        return f"""
تنها {remaining_days} روز تا اتمام اعتبار پکیج شما باقی مانده است.
لطفا برای تمدید پکیج اقدام کنید.
شناسه پکیج شما: <code>{sub_id}</code>
"""
    elif LANG == 'EN':
        return f"""
Only {remaining_days} days left until your package expires.
Please renew your package.
Your package ID: <code>{sub_id}</code>
"""

# Alert Package Size Template
def package_size_end_soon_template(sub_id, remaining_size):
    """Template for alerting user about low package data."""
    if LANG == 'FA':
        return f"""
تنها {remaining_size:.2f} گیگابایت تا اتمام اعتبار پکیج شما باقی مانده است.
لطفا برای تمدید پکیج اقدام کنید.

شناسه پکیج شما: <code>{sub_id}</code>
"""
    elif LANG == 'EN':
        return f"""
Only {remaining_size:.2f} GB left until your package expires.
Please renew your package.
Your package ID: <code>{sub_id}</code>
"""

# Renewal Unavailable Template
def renewal_unvalable_template(settings):
    """Template for informing user that renewal is not available yet."""
    if not settings:
        settings = {}
        
    advanced_renewal_days = settings.get('advanced_renewal_days', 0)
    advanced_renewal_usage = settings.get('advanced_renewal_usage', 0)
    
    if LANG == 'FA':
        return f"""
🛑در حال حاضر شما امکان تمدید اشتراک خود را ندارید.
جهت تمدید اشتراک باید یکی از شروط زیر برقرار باشد:
1- کمتر از {advanced_renewal_days} روز تا اتمام اشتراک شما باقی مانده باشد.
2- حجم باقی مانده اشتراک شما کمتر از {advanced_renewal_usage} گیگابایت باشد.
"""
    elif LANG == 'EN':
        return f"""
🛑You cannot renew your subscription at this time.
To renew your subscription, one of the following conditions must be met:
1- Less than {advanced_renewal_days} days left until your subscription expires.
2- The remaining volume of your subscription is less than {advanced_renewal_usage} GB.
"""

# Configs List Template
def configs_template(configs):
    """Template for displaying user configs."""
    if not configs:
        return MESSAGES['ERROR_CONFIG_NOT_FOUND']
    
    msg = f"{MESSAGES['USER_CONFIGS_LIST']}\n\n"
    
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
    
    # Individual Configs (VLESS, Vmess, Trojan)
    if configs.get('vless') and isinstance(configs['vless'], list):
        msg += f"📡 <b>VLESS:</b>\n"
        for i, config in enumerate(configs['vless'], 1):
            msg += f"{i}. <code>{config}</code>\n"
        msg += "\n"
    
    if configs.get('vmess') and isinstance(configs['vmess'], list):
        msg += f"📡 <b>VMess:</b>\n"
        for i, config in enumerate(configs['vmess'], 1):
            msg += f"{i}. <code>{config}</code>\n"
        msg += "\n"
    
    if configs.get('trojan') and isinstance(configs['trojan'], list):
        msg += f"📡 <b>Trojan:</b>\n"
        for i, config in enumerate(configs['trojan'], 1):
            msg += f"{i}. <code>{config}</code>\n"
        msg += "\n"
    
    return msg

# New Template: Profile Info Template
def profile_info_template(user_data, subscription_count):
    """Template for displaying user profile information."""
    if not user_
        return MESSAGES['UNKNOWN_ERROR']
    
    balance = user_data.get('balance', 0)
    
    if LANG == 'FA':
        return f"""
👤 <b>پروفایل شما</b>

📛 نام: {user_data.get('full_name', MESSAGES['NOT_SET'])}
📱 نام کاربری: @{user_data.get('username', MESSAGES['NOT_SET'])}
💰 موجودی کیف پول: {rial_to_toman(balance)} {MESSAGES['TOMAN']}
📊 تعداد اشتراک‌ها: {subscription_count}
"""
    elif LANG == 'EN':
        return f"""
👤 <b>Your Profile</b>

📛 Name: {user_data.get('full_name', MESSAGES['NOT_SET'])}
📱 Username: @{user_data.get('username', MESSAGES['NOT_SET'])}
💰 Wallet Balance: {rial_to_toman(balance)} {MESSAGES['TOMAN']}
📊 Number of Subscriptions: {subscription_count}
"""

# New Template: Online Payment Request Template
def online_payment_request_template(amount, payment_link):
    """Template for displaying online payment request."""
    if LANG == 'FA':
        return f"""
💳 <b>درخواست پرداخت آنلاین</b>

💰 مبلغ قابل پرداخت: {rial_to_toman(amount)} {MESSAGES['TOMAN']}

لطفاً برای پرداخت آنلاین روی دکمه زیر کلیک کنید:
"""
    elif LANG == 'EN':
        return f"""
💳 <b>Online Payment Request</b>

💰 Amount to pay: {rial_to_toman(amount)} {MESSAGES['TOMAN']}

Please click the button below to pay online:
"""

# New Template: Affiliate System Info Template
def affiliate_system_info_template(referral_link, referral_count, earned_commission):
    """Template for displaying affiliate system information."""
    if LANG == 'FA':
        return f"""
👥 <b>سیستم نمایندگی</b>

لینک دعوت شما:
<code>{referral_link}</code>

📊 آمار دعوت:
   تعداد دعوت‌شده‌ها: {referral_count}
   کمیسیون دریافتی: {rial_to_toman(earned_commission)} {MESSAGES['TOMAN']}

با دعوت از دوستان خود، کمیسیون دریافت کنید!
"""
    elif LANG == 'EN':
        return f"""
👥 <b>Affiliate System</b>

Your referral link:
<code>{referral_link}</code>

📊 Referral Statistics:
   Number of referrals: {referral_count}
   Earned commission: {rial_to_toman(earned_commission)} {MESSAGES['TOMAN']}

Earn commission by inviting your friends!
"""

# New Template: Coupon Applied Template
def coupon_applied_template(original_amount, discounted_amount, coupon_code):
    """Template for displaying coupon application result."""
    discount_amount = original_amount - discounted_amount
    
    if LANG == 'FA':
        return f"""
🎫 <b>کوپن تخفیف اعمال شد</b>

کد کوپن: <code>{coupon_code}</code>
مبلغ تخفیف: {rial_to_toman(discount_amount)} {MESSAGES['TOMAN']}
مبلغ جدید: {rial_to_toman(discounted_amount)} {MESSAGES['TOMAN']}
"""
    elif LANG == 'EN':
        return f"""
🎫 <b>Coupon Applied</b>

Coupon code: <code>{coupon_code}</code>
Discount amount: {rial_to_toman(discount_amount)} {MESSAGES['TOMAN']}
New amount: {rial_to_toman(discounted_amount)} {MESSAGES['TOMAN']}
"""
