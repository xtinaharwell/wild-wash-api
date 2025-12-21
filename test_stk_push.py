#!/usr/bin/env python
"""
Test script to verify M-Pesa STK Push functionality
"""
import os
import sys
import django
import requests
import base64
from datetime import datetime

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'api.settings')
sys.path.insert(0, os.path.dirname(__file__))
django.setup()

from django.conf import settings

def test_credentials():
    """Test if M-Pesa credentials are configured."""
    print("=" * 60)
    print("Testing M-Pesa Credentials Configuration")
    print("=" * 60)
    
    configs = {
        'MPESA_CONSUMER_KEY': settings.MPESA_CONSUMER_KEY,
        'MPESA_CONSUMER_SECRET': settings.MPESA_CONSUMER_SECRET,
        'MPESA_BUSINESS_SHORTCODE': settings.MPESA_BUSINESS_SHORTCODE,
        'MPESA_PASSKEY': settings.MPESA_PASSKEY,
        'MPESA_CALLBACK_URL': settings.MPESA_CALLBACK_URL,
    }
    
    for key, value in configs.items():
        if value:
            masked = value[:10] + '...' if len(str(value)) > 10 else value
            print(f"✓ {key}: {masked}")
        else:
            print(f"✗ {key}: NOT SET - Required!")
    
    missing = [k for k, v in configs.items() if not v]
    return len(missing) == 0

def test_access_token():
    """Test getting access token from Daraja API."""
    print("\n" + "=" * 60)
    print("Testing Access Token Generation")
    print("=" * 60)
    
    try:
        url = "https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials"
        response = requests.get(
            url,
            auth=(settings.MPESA_CONSUMER_KEY, settings.MPESA_CONSUMER_SECRET),
            timeout=10
        )
        
        if response.status_code == 200:
            token = response.json().get('access_token')
            print(f"✓ Access token obtained successfully")
            print(f"  Token: {token[:20]}...")
            return token
        else:
            print(f"✗ Failed to get token. Status: {response.status_code}")
            print(f"  Response: {response.text}")
            return None
            
    except Exception as e:
        print(f"✗ Error getting access token: {str(e)}")
        return None

def encode_password(shortcode, passkey, timestamp):
    """Encode password for M-Pesa."""
    password_string = f"{shortcode}{passkey}{timestamp}"
    return base64.b64encode(password_string.encode()).decode()

def test_stk_push(access_token, phone_number, amount=1):
    """Test STK Push request."""
    print("\n" + "=" * 60)
    print("Testing STK Push Request")
    print("=" * 60)
    
    url = "https://sandbox.safaricom.co.ke/mpesa/stkpush/v1/processrequest"
    
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    password = encode_password(
        settings.MPESA_BUSINESS_SHORTCODE,
        settings.MPESA_PASSKEY,
        timestamp
    )
    
    # Format phone number to 254 format
    formatted_phone = phone_number.replace('0', '254', 1) if phone_number.startswith('0') else phone_number
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "BusinessShortCode": settings.MPESA_BUSINESS_SHORTCODE,
        "Password": password,
        "Timestamp": timestamp,
        "TransactionType": "CustomerPayBillOnline",
        "Amount": int(amount),
        "PartyA": formatted_phone,
        "PartyB": settings.MPESA_BUSINESS_SHORTCODE,
        "PhoneNumber": formatted_phone,
        "CallBackURL": settings.MPESA_CALLBACK_URL,
        "AccountReference": "TEST-ORDER-001",
        "TransactionDesc": "Test STK Push"
    }
    
    print(f"Sending STK Push to: {formatted_phone}")
    print(f"Amount: {amount} KES")
    print(f"Callback URL: {settings.MPESA_CALLBACK_URL}")
    
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        
        print(f"\nResponse Status: {response.status_code}")
        print(f"Response Body:")
        print(response.text)
        
        if response.status_code == 200:
            result = response.json()
            if result.get('ResponseCode') == '0':
                print(f"\n✓ STK Push successful!")
                print(f"  CheckoutRequestID: {result.get('CheckoutRequestID')}")
                return True
            else:
                print(f"\n✗ STK Push failed")
                print(f"  Response Code: {result.get('ResponseCode')}")
                print(f"  Message: {result.get('ResponseDescription')}")
                return False
        else:
            print(f"\n✗ Request failed with status {response.status_code}")
            return False
            
    except Exception as e:
        print(f"✗ Error sending STK Push: {str(e)}")
        return False

def main():
    print("\n")
    print("╔" + "=" * 58 + "╗")
    print("║" + " " * 10 + "M-Pesa STK Push Configuration Tester" + " " * 12 + "║")
    print("╚" + "=" * 58 + "╝")
    
    # Test credentials
    if not test_credentials():
        print("\n⚠️  Missing M-Pesa credentials. Please update your .env file.")
        return
    
    # Test access token
    token = test_access_token()
    if not token:
        print("\n⚠️  Could not obtain access token. Check your credentials.")
        return
    
    # Test STK Push
    print("\nTo test STK Push, you need a valid Safaricom test phone number.")
    print("Default test number: 254708374149")
    phone = input("\nEnter phone number to test (or press Enter for default): ").strip()
    if not phone:
        phone = "254708374149"
    
    amount = input("Enter amount to test (or press Enter for 1 KES): ").strip()
    if not amount:
        amount = "1"
    
    test_stk_push(token, phone, amount)
    
    print("\n" + "=" * 60)
    print("Test completed!")
    print("=" * 60 + "\n")

if __name__ == '__main__':
    main()
