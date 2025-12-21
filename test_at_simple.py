#!/usr/bin/env python
"""
Simple Africa's Talking API Test
Tests basic connectivity and SMS sending without Django dependencies
"""

import os
import sys
from dotenv import load_dotenv

# Disable SSL verification for testing (set before importing africastalking)
os.environ['PYTHONWARNINGS'] = 'ignore:Unverified HTTPS request'

import warnings
warnings.filterwarnings('ignore')

import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Monkey-patch requests to disable SSL verification
import requests

# Store original post function
original_post = requests.post

def patched_post(*args, **kwargs):
    kwargs['verify'] = False
    return original_post(*args, **kwargs)

requests.post = patched_post

import africastalking

# Load environment variables
load_dotenv()

# Get credentials from .env
API_KEY = os.getenv('AFRICAS_TALKING_API_KEY')
USERNAME = os.getenv('AFRICAS_TALKING_USERNAME', 'sandbox')
SENDER_ID = os.getenv('AFRICAS_TALKING_SENDER_ID', 'WILDWASH')
PHONE_NUMBER = os.getenv('ADMIN_PHONE_NUMBER', '+254718693484')

print("=" * 70)
print("Africa's Talking API - Simple Test")
print("=" * 70)

# Check configuration
print("\n📋 Configuration Check:")
print(f"  API Key: {API_KEY[:30]}...***" if API_KEY else "  API Key: NOT SET ❌")
print(f"  Username: {USERNAME}")
print(f"  Sender ID: {SENDER_ID}")
print(f"  Phone Number: {PHONE_NUMBER}")

if not API_KEY:
    print("\n❌ ERROR: AFRICAS_TALKING_API_KEY not found in .env")
    exit(1)

print("\n✓ Configuration loaded successfully\n")

# Initialize Africa's Talking
print("🔌 Initializing Africa's Talking SDK...")
try:
    africastalking.initialize(USERNAME, API_KEY)
    print("✓ SDK initialized successfully")
except Exception as e:
    print(f"❌ Failed to initialize: {e}")
    exit(1)

# Get SMS service
print("\n📞 Getting SMS Service...")
try:
    sms = africastalking.SMS
    print("✓ SMS Service obtained")
except Exception as e:
    print(f"❌ Failed to get SMS service: {e}")
    exit(1)

# Send test SMS
print(f"\n📤 Sending test SMS to {PHONE_NUMBER}...")
print(f"   Sender ID: {SENDER_ID}")

message = "🎉 WILDWASH TEST: Africa's Talking SMS API is working! This is a test message."

try:
    response = sms.send(message, [PHONE_NUMBER], sender_id=SENDER_ID)  # type: ignore
    
    print("\n✅ SMS SENT SUCCESSFULLY!")
    print(f"\nResponse Details:")
    print(f"  Status: {response}")
    
except Exception as e:
    print(f"\n❌ Failed to send SMS:")
    print(f"  Error Type: {type(e).__name__}")
    print(f"  Error Message: {str(e)}")
    
    # Print detailed error info
    import traceback
    print("\n📋 Full Traceback:")
    traceback.print_exc()

print("\n" + "=" * 70)
print("Test Complete")
print("=" * 70)
