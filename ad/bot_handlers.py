import logging
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from ad_utils import get_user_by_phone, unlock_user, reset_user_password
from sms_utils import verification_codes, sms_attempts, blocked_users, send_verification_code, check_sms_limit, update_sms_limit

logger = logging.getLogger(__name__)


# Define the /help command handler with buttons
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    keyboard = [
        [
            InlineKeyboardButton("Unlock", callback_data='unlock'),
            InlineKeyboardButton("Reset", callback_data='reset')
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text('Choose an option for help:', reply_markup=reply_markup)   

# Define a callback query handler for the button presses
async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    
    if query.data == 'unlock':
        await query.edit_message_text(text="1. Send mobile number as : 994551234567.\n2. unlock mobile_number sms_code.\n3. unlock 994551234567 654321")
    elif query.data == 'reset':
        await query.edit_message_text(text="1. Send mobile number as : 994551234567.\n2. reset mobile_number sms_code new_password.\n3. For example: reset 994551234567 654321 NP963147!#246\nPassword requirment:\nPassword length: 11\nTwo digit\nTwo number\nTwo symbol\nTwo capital letter\nTwo small letter")     

async def get_username(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    username = update.effective_user
    phone_number = update.message.text.strip()

    if user_id in blocked_users and blocked_users[user_id] > datetime.now():
        block_time = blocked_users[user_id] - datetime.now()
        await update.message.reply_text(f'You are blocked from requesting SMS codes for {block_time.seconds // 60} minutes.')
        logger.warning(f"User {username.name}{user_id} is blocked from requesting SMS codes.")
        return

    if not check_sms_limit(str(user_id)) or not check_sms_limit(phone_number):
        await update.message.reply_text('You have reached the SMS limit. Please try again later.')
        logger.warning(f"User  {username.name} {user_id} or phone number {phone_number} reached the SMS limit.")
        return

    user = get_user_by_phone(phone_number)
    if user:
        response = send_verification_code(phone_number)
        if response.status_code == 200:
            update_sms_limit(str(user_id))
            update_sms_limit(phone_number)
            await update.message.reply_text(f'A verification code has been sent to {phone_number}. Please enter the code to proceed.')
            logger.info(f"Verification code sent to {phone_number}-{user.sAMAccountName.value} for Telegram user {username.name}.")
        else:
            await update.message.reply_text('Failed to send the verification code. Please try again later.')
            logger.error(f"Failed to send verification code to {phone_number}. Action {username.name}")
    else:
        await update.message.reply_text(f'No user found for phone number {phone_number}')
        logger.info(f"No user found for phone number {phone_number}. Action {username.name} .")

async def verify_code(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    username = update.effective_user
    message_text = update.message.text.strip()
    parts = message_text.split()

    if user_id in blocked_users and blocked_users[user_id] > datetime.now():
        block_time = blocked_users[user_id] - datetime.now()
        await update.message.reply_text(f'You are blocked from entering verification codes for {block_time.seconds // 60} minutes.')
        logger.warning(f"User {username.name}{user_id} is blocked from entering verification codes.")
        return

    if len(parts) == 3 and parts[0].lower() == "unlock":
        phone_number = parts[1]
        code = parts[2]

        if phone_number in verification_codes:
            verification_info = verification_codes[phone_number]
            if verification_info['expires'] < datetime.now():
                await update.message.reply_text('The verification code has expired. Please request a new code.')
                logger.warning(f"Verification code for {phone_number} has expired. Action {username.name}")
                return

            if verification_info['code'] == int(code):
                user = get_user_by_phone(phone_number)
                if user:
                    if 'lockoutTime' in user and user.lockoutTime.value:
                        lockout_time = user.lockoutTime.value
                        if isinstance(lockout_time, datetime):
                            lockout_time = int(lockout_time.timestamp())
                        if lockout_time > 0:
                            unlock_user(user.entry_dn)
                            await update.message.reply_text(f'The account for username {user.sAMAccountName.value} has been unlocked.')
                            logger.info(f"Account for {user.sAMAccountName.value} has been unlocked. Action {username.name}")
                        else:
                            await update.message.reply_text(f'The account for username {user.sAMAccountName.value} is not locked.')
                            logger.info(f"Account for {user.sAMAccountName.value} is not locked. Action {username.name}")
                    else:
                        await update.message.reply_text(f'The account for username {user.sAMAccountName.value} is not locked or lockoutTime attribute is not available.')
                        logger.info(f"Account for {user.sAMAccountName.value} is not locked or lockoutTime attribute is not available.")
                else:
                    await update.message.reply_text(f'No user found for phone number {phone_number}')
                    logger.info(f"No user found for phone number {phone_number}. Action {username.name}")
            else:
                if user_id in sms_attempts:
                    sms_attempts[user_id] += 1
                else:
                    sms_attempts[user_id] = 1

                if sms_attempts[user_id] >= 3:
                    blocked_users[user_id] = datetime.now() + timedelta(minutes=10)
                    await update.message.reply_text('You have been blocked due to multiple invalid code attempts. Please try again later.')
                    logger.warning(f"User  {user_id} has been blocked due to multiple invalid code attempts. Action {username.name}")
                else:
                    await update.message.reply_text('Invalid verification code. Please try again.')
                    logger.warning(f"User  {user_id} entered an invalid verification code. Action {username.name}")
        else:
            await update.message.reply_text('Invalid verification code or phone number. Please try again.')
            logger.warning(f"Invalid verification code or phone number entered by user {user_id}. Action {username.name}")
    else:
        await update.message.reply_text('Invalid format. Please enter the code using the format: "unlock PHONE_NUMBER CODE".')
        logger.info(f"Invalid format used by user  {user_id}. Action {username.name}")

async def reset_password(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    username = update.effective_user
    message_text = update.message.text.strip()
    parts = message_text.split()
    
    if len(parts) == 4 and parts[0].lower() == "reset":
        phone_number = parts[1]
        new_password = parts[3]
        code = parts[2]

        logger.info(f"Reset password requested by {username.name} for phone number {phone_number} with code {code}")

        if user_id in blocked_users and blocked_users[user_id] > datetime.now():
            block_time = blocked_users[user_id] - datetime.now()
            await update.message.reply_text(f'You are blocked from entering verification codes for {block_time.seconds // 60} minutes.')
            logger.warning(f"User {username.name}{user_id} is blocked from entering verification codes.")
            return

        if phone_number in verification_codes:
            verification_info = verification_codes[phone_number]
            if verification_info['expires'] < datetime.now():
                await update.message.reply_text('The verification code has expired. Please request a new code.')
                logger.warning(f"Verification code for {phone_number} has expired. Action {username.name}")
                return

            if verification_info['code'] == int(code):
                user = get_user_by_phone(phone_number)
                if user:
                    reset_user_password(user.entry_dn, new_password)
                    await update.message.reply_text(f'The password for username {user.sAMAccountName.value} has been reset.')
                    logger.info(f"Password for {user.sAMAccountName.value} has been reset. Action {username.name}")
                else:
                    await update.message.reply_text(f'No user found for phone number {phone_number}. Please check the phone number format.')
                    logger.info(f"No user found for phone number {phone_number}. Action {username.name}")
            else:
                if user_id in sms_attempts:
                    sms_attempts[user_id] += 1
                else:
                    sms_attempts[user_id] = 1

                if sms_attempts[user_id] >= 3:
                    blocked_users[user_id] = datetime.now() + timedelta(minutes=10)
                    await update.message.reply_text('You have been blocked due to multiple invalid code attempts. Please try again later.')
                    logger.warning(f"User  {user_id} has been blocked due to multiple invalid code attempts. Action {username.name}")
                else:
                    await update.message.reply_text('Invalid verification code. Please try again.')
                    logger.warning(f"User  {user_id} entered an invalid verification code. Action {username.name}")
        else:
            await update.message.reply_text('Invalid verification code or phone number. Please try again.')
            logger.warning(f"Invalid verification code or phone number entered by user {user_id}. Action {username.name}")
    else:
        await update.message.reply_text('Invalid format. Please enter the code using the format: "reset PHONE_NUMBER CODE NEW_PASSWORD".')
        logger.info(f"Invalid format used by user  {user_id}. Action {username.name}")
