# sms_utils.py

import random
import requests
import json
from datetime import datetime, timedelta
from config import SMS_API_TOKEN, SMS_LIMIT_FILE, SMS_URL, SMS_SENDER

verification_codes = {}
sms_attempts = {}
blocked_users = {}

try:
    with open(SMS_LIMIT_FILE, 'r') as file:
        sms_limits = json.load(file)
except FileNotFoundError:
    sms_limits = {}

def send_verification_code(phone_number):
    verification_code = random.randint(100000, 999999)
    verification_codes[phone_number] = {'code': verification_code, 'expires': datetime.now() + timedelta(minutes=3)}

    sms_payload = {
        "Sender": SMS_SENDER,
        "Telnumber": phone_number,
        "Textforsend": f"Your verification code is {verification_code}"
    }
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {SMS_API_TOKEN}"
    }
    response = requests.post(SMS_URL, json=sms_payload, headers=headers)
    return response

def check_sms_limit(identifier):
    current_time = datetime.now()
    if identifier in sms_limits:
        sms_limits[identifier] = [timestamp for timestamp in sms_limits[identifier] if datetime.fromisoformat(timestamp) > current_time - timedelta(hours=1)]
        if len(sms_limits[identifier]) >= 3:
            return False
    else:
        sms_limits[identifier] = []
    return True

def update_sms_limit(identifier):
    current_time = datetime.now()
    sms_limits[identifier].append(current_time.isoformat())
    with open(SMS_LIMIT_FILE, 'w') as file:
        json.dump(sms_limits, file)
