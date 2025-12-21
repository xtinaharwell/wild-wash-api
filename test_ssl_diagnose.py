#!/usr/bin/env python
"""
Diagnose SSL and Network Issues
"""

import ssl
import socket
import requests
from urllib.parse import urlparse

print("=" * 70)
print("SSL/Network Diagnostic Test")
print("=" * 70)

# Test 1: Check SSL certificate of the endpoint
print("\n1️⃣  Checking Africa's Talking Sandbox SSL Certificate...")
host = "api.sandbox.africastalking.com"
port = 443

try:
    context = ssl.create_default_context()
    with socket.create_connection((host, port), timeout=5) as sock:
        with context.wrap_socket(sock, server_hostname=host) as ssock:
            cert = ssock.getpeercert()
            print(f"✅ Certificate retrieved successfully")
            print(f"   Subject: {cert.get('subject', 'N/A')}")
            print(f"   Issuer: {cert.get('issuer', 'N/A')}")
except Exception as e:
    print(f"❌ Failed to retrieve certificate: {e}")

# Test 2: Try HTTP request with verify=False
print("\n2️⃣  Testing HTTP request with SSL verification disabled...")
try:
    response = requests.get(f"https://{host}/", verify=False, timeout=5)
    print(f"✅ Request succeeded! Status: {response.status_code}")
except Exception as e:
    print(f"❌ Request failed: {e}")

# Test 3: Check network connectivity
print("\n3️⃣  Checking basic network connectivity...")
try:
    response = requests.get("https://www.google.com", timeout=5)
    print(f"✅ Internet connection OK! Status: {response.status_code}")
except Exception as e:
    print(f"❌ Internet connection issue: {e}")

# Test 4: Check if using a proxy
print("\n4️⃣  Checking for proxy configuration...")
import os
proxy = os.environ.get('HTTP_PROXY') or os.environ.get('http_proxy')
if proxy:
    print(f"⚠️  HTTP_PROXY is set to: {proxy}")
else:
    print(f"✅ No HTTP_PROXY environment variable found")

proxy = os.environ.get('HTTPS_PROXY') or os.environ.get('https_proxy')
if proxy:
    print(f"⚠️  HTTPS_PROXY is set to: {proxy}")
else:
    print(f"✅ No HTTPS_PROXY environment variable found")

print("\n" + "=" * 70)
print("Diagnostic Complete")
print("=" * 70)
