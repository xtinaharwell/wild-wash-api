#!/usr/bin/env python
"""Test M-Pesa credentials and debug the 400 error"""
import os
import sys
import django
import requests
import base64
from requests.auth import HTTPBasicAuth

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'api.settings')
sys.path.insert(0, os.path.dirname(__file__))
django.setup()

from django.conf import settings

def test_mpesa_credentials():
    """Test M-Pesa credentials"""
    print("=" * 70)
    print("Testing M-Pesa Credentials")
    print("=" * 70)
    
    # Display credentials (masked)
    print(f"\nCredentials configured:")
    print(f"  Consumer Key: {settings.MPESA_CONSUMER_KEY[:20]}...")
    print(f"  Consumer Secret: {settings.MPESA_CONSUMER_SECRET[:20]}...")
    print(f"  Business Shortcode: {settings.MPESA_BUSINESS_SHORTCODE}")
    print(f"  Passkey: {settings.MPESA_PASSKEY[:20]}...")
    
    # Test 1: Basic connectivity
    print(f"\n{'='*70}")
    print("Test 1: Testing OAuth endpoint connectivity")
    print(f"{'='*70}")
    
    url = "https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials"
    
    try:
        # Try with HTTPBasicAuth
        print(f"\nAttempting to get access token...")
        print(f"URL: {url}")
        
        response = requests.get(
            url,
            auth=HTTPBasicAuth(settings.MPESA_CONSUMER_KEY, settings.MPESA_CONSUMER_SECRET),
            timeout=10
        )
        
        print(f"Response Status: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        print(f"Response Body: {response.text}")
        
        if response.status_code == 200:
            print("\n✅ SUCCESS! Access token obtained")
            token = response.json().get('access_token')
            print(f"Token: {token[:20]}...")
            return True
        else:
            print(f"\n❌ FAILED! Status {response.status_code}")
            
            # Try to parse error details
            try:
                error_data = response.json()
                print(f"Error Details: {error_data}")
            except:
                pass
            
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Request Error: {str(e)}")
        return False

def test_credentials_format():
    """Verify credentials format"""
    print(f"\n{'='*70}")
    print("Test 2: Verifying Credentials Format")
    print(f"{'='*70}")
    
    key = settings.MPESA_CONSUMER_KEY
    secret = settings.MPESA_CONSUMER_SECRET
    
    checks = {
        "Consumer Key length": (len(key), 50),  # Should be around 50 chars
        "Consumer Secret length": (len(secret), 50),  # Should be around 50 chars
        "Shortcode": (settings.MPESA_BUSINESS_SHORTCODE, "174379"),
        "Passkey length": (len(settings.MPESA_PASSKEY), 64),  # Usually 64 hex chars
    }
    
    for check_name, (actual, expected) in checks.items():
        if isinstance(expected, int):
            status = "✓" if actual == expected else "⚠"
            print(f"{status} {check_name}: {actual} (expected {expected})")
        else:
            status = "✓" if str(actual) == str(expected) else "✗"
            print(f"{status} {check_name}: {actual} (expected {expected})")

def main():
    print("\n")
    print("╔" + "=" * 68 + "╗")
    print("║" + " " * 15 + "M-Pesa Credentials Diagnostic Tool" + " " * 18 + "║")
    print("╚" + "=" * 68 + "╝")
    
    test_credentials_format()
    
    success = test_mpesa_credentials()
    
    print(f"\n{'='*70}")
    print("Diagnostic Summary")
    print(f"{'='*70}")
    
    if success:
        print("✅ M-Pesa credentials are valid and working!")
    else:
        print("❌ M-Pesa credentials are NOT working")
        print("\nPossible solutions:")
        print("1. Check that credentials are correct from Safaricom Daraja portal")
        print("2. Verify credentials have 'sandbox' status (not production)")
        print("3. Check that the account hasn't been deactivated")
        print("4. Try regenerating credentials from Daraja portal")
        print("5. Ensure network connectivity to https://sandbox.safaricom.co.ke")

if __name__ == '__main__':
    main()
