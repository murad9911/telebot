import json
import requests
import random
from datetime import datetime, timedelta
from config import SMS_API_TOKEN, SMS_LIMIT_FILE, SMS_SENDER, SMS_URL

verification_codes = {}
sms_attempts = {}
blocked_users = {}

def send_sms(phone_number, message):
    sms_payload = {
        "Sender": SMS_SENDER,
        "Telnumber": phone_number,
        "Textforsend": message
    }
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {SMS_API_TOKEN}"
    }
    response = requests.post(SMS_URL, json=sms_payload, headers=headers)
    return response.status_code == 200

def check_sms_limit(user_id, phone_number):
    current_time = datetime.now()
    
    # Check SMS limit for user ID
    if str(user_id) in sms_limits:
        # Remove SMS timestamps older than 1 hour
        sms_limits[str(user_id)] = [timestamp for timestamp in sms_limits[str(user_id)] if datetime.fromisoformat(timestamp) > current_time - timedelta(hours=1)]
        if len(sms_limits[str(user_id)]) >= 3:
            return False, 'You have reached the limit of 3 SMS per hour for your Telegram ID. Please try again later.'
    else:
        sms_limits[str(user_id)] = []

    # Check SMS limit for phone number
    if phone_number in sms_limits:
        # Remove SMS timestamps older than 1 hour
        sms_limits[phone_number] = [timestamp for timestamp in sms_limits[phone_number] if datetime.fromisoformat(timestamp) > current_time - timedelta(hours=1)]
        if len(sms_limits[phone_number]) >= 3:
            return False, 'This phone number has reached the limit of 3 SMS per hour. Please try again later.'
    else:
        sms_limits[phone_number] = []

    return True, None

def update_sms_limits(user_id, phone_number):
    current_time = datetime.now()
    sms_limits[str(user_id)].append(current_time.isoformat())
    sms_limits[phone_number].append(current_time.isoformat())
    with open(SMS_LIMIT_FILE, 'w') as file:
        json.dump(sms_limits, file)

def generate_verification_code(phone_number):
    code = random.randint(100000, 999999)
    verification_codes[phone_number] = {'code': code, 'expires': datetime.now() + timedelta(minutes=3)}
    return code

def verify_code(phone_number, code):
    if phone_number in verification_codes:
        verification_info = verification_codes[phone_number]
        if verification_info['expires'] < datetime.now():
            return False, 'The verification code has expired. Please request a new code.'
        if verification_info['code'] == int(code):
            return True, None
    return False, 'Invalid verification code. Please try again.'

def track_sms_attempts(user_id):
    if user_id in sms_attempts:
        sms_attempts[user_id] += 1
    else:
        sms_attempts[user_id] = 1

    if sms_attempts[user_id] >= 3:
        blocked_users[user_id] = datetime.now() + timedelta(minutes=3)
        return False, 'You have been blocked due to multiple invalid code attempts. Please try again later.'
    return True, None

def is_user_blocked(user_id):
    if user_id in blocked_users and blocked_users[user_id] > datetime.now():
        block_time = blocked_users[user_id] - datetime.now()
        return True, f'You are blocked from requesting SMS codes for {block_time.seconds // 60} minutes.'
    return False, None
