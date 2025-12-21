#!/usr/bin/env python
"""
Africa's Talking API Key Validator
Tests which API key is valid for your account
"""

import os
from dotenv import load_dotenv
import warnings
warnings.filterwarnings('ignore')

import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

import requests

# Monkey-patch requests to disable SSL verification
original_post = requests.post
def patched_post(*args, **kwargs):
    kwargs['verify'] = False
    return original_post(*args, **kwargs)
requests.post = patched_post

import africastalking

# Load environment variables
load_dotenv()

print("=" * 70)
print("Africa's Talking API Key Validator")
print("=" * 70)

# Test the current API key from .env
API_KEY = os.getenv('AFRICAS_TALKING_API_KEY')
USERNAME = os.getenv('AFRICAS_TALKING_USERNAME', 'sandbox')

print(f"\n📋 Testing current credentials:")
print(f"   Username: {USERNAME}")
print(f"   API Key: {API_KEY[:50]}...***" if API_KEY else "   API Key: NOT SET")

if API_KEY:
    try:
        africastalking.initialize(USERNAME, API_KEY)
        sms = africastalking.SMS
        
        # Try to get account info or do a test that validates auth
        print("\n🔍 Validating API Key...")
        
        # Attempt to send a test message with detailed error handling
        response = sms.send(  # type: ignore
            "Test message",
            ["+254700000000"],  # dummy number
            sender_id="Sandbox"
        )
        print(f"✅ API Key is VALID! Response: {response}")
        
    except Exception as e:
        error_msg = str(e)
        print(f"\n❌ Authentication Error: {error_msg}")
        
        if "invalid" in error_msg.lower():
            print("\n⚠️  The API Key appears to be INVALID")
            print("\nPossible causes:")
            print("   1. API Key has expired")
            print("   2. API Key doesn't match the username")
            print("   3. API Key needs to be regenerated")
            print("\n📝 To fix:")
            print("   1. Go to https://africastalking.com/dashboard")
            print("   2. Log in with your account")
            print("   3. Go to Settings > API Keys")
            print("   4. Generate a new API key")
            print("   5. Copy the new key and update .env file")

else:
    print("\n❌ API Key not found in .env")

print("\n" + "=" * 70)
