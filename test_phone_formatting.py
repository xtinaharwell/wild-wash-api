#!/usr/bin/env python
"""
Test phone number formatting for Africa's Talking SMS integration
"""

import os
import sys
import django
from pathlib import Path

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'api.settings')
sys.path.insert(0, str(Path(__file__).parent))

django.setup()

from services.sms_service import format_phone_number

print("=" * 70)
print("Testing Phone Number Formatting")
print("=" * 70)

# Test cases
test_cases = [
    # (input, expected_output)
    ("+254718693484", "+254718693484"),  # Already formatted
    ("254718693484", "+254718693484"),    # Without +
    ("0718693484", "+254718693484"),      # With leading 0
    ("+254 718 693 484", "+254718693484"),  # With spaces
    ("254-718-693-484", "+254718693484"),   # With dashes
    ("718693484", "+254718693484"),        # Missing country code
    ("", None),                             # Empty string
    (None, None),                           # None
]

print("\n📱 Testing Various Phone Number Formats:\n")

all_pass = True
for input_phone, expected in test_cases:
    result = format_phone_number(input_phone)
    status = "✅" if result == expected else "❌"
    
    if result != expected:
        all_pass = False
        print(f"{status} Input: {input_phone!r}")
        print(f"   Expected: {expected}")
        print(f"   Got:      {result}\n")
    else:
        print(f"{status} {input_phone!r} → {result}")

print("\n" + "=" * 70)
if all_pass:
    print("✅ All phone formatting tests passed!")
else:
    print("❌ Some phone formatting tests failed!")
print("=" * 70)

# Now test SMS sending with formatted numbers
print("\n\n" + "=" * 70)
print("Testing SMS Sending with Formatted Phone Numbers")
print("=" * 70)

try:
    from services.sms_service import AfricasTalkingSMSService
    
    sms_service = AfricasTalkingSMSService()
    print("\n✓ SMS Service initialized successfully")
    
    # Test with various phone number formats
    test_phones = [
        "+254718693484",
        "254718693484",
        "0718693484"
    ]
    
    for phone in test_phones:
        print(f"\n📤 Testing SMS with phone: {phone}")
        message = f"Test message from wildwash - phone format: {phone}"
        
        result = sms_service.send_sms(phone, message)
        
        if result and result.get('status') == 'success':
            print(f"✅ SMS sent successfully!")
        else:
            error_msg = result.get('message', 'Unknown error') if result else 'No response'
            print(f"⚠ SMS sending failed: {error_msg}")

except Exception as e:
    print(f"❌ Error testing SMS: {str(e)}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 70)
print("Phone formatting test complete!")
print("=" * 70)
