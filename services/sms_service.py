# services/sms_service.py
import logging
import os
import warnings
import ssl

# Set environment variables FIRST
os.environ['PYTHONWARNINGS'] = 'ignore:Unverified HTTPS request'
os.environ['REQUESTS_CA_BUNDLE'] = ''
os.environ['CURL_CA_BUNDLE'] = ''
warnings.filterwarnings('ignore')

# Disable SSL warnings from urllib3
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
urllib3.disable_warnings()

# Patch SSL context creation BEFORE importing requests
import urllib3.util.ssl_
_orig_create_context = urllib3.util.ssl_.create_urllib3_context

def create_insecure_context(ssl_version=None, cert_reqs=None, options=None, ciphers=None):
    """Create SSL context that doesn't verify certificates"""
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    return ctx

urllib3.util.ssl_.create_urllib3_context = create_insecure_context

# Import and configure requests
import requests
from requests.adapters import HTTPAdapter
from urllib3.poolmanager import PoolManager

class InsecureHTTPAdapter(HTTPAdapter):
    """HTTP adapter that uses insecure SSL context"""
    
    def init_poolmanager(self, *args, **kwargs):
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        kwargs['ssl_context'] = ctx
        return super().init_poolmanager(*args, **kwargs)

# Create global session with insecure adapter
_session = requests.Session()
_session.mount('https://', InsecureHTTPAdapter())
_session.mount('http://', HTTPAdapter())
_session.verify = False

# Monkey-patch requests module functions
_orig_request = requests.request
_orig_post = requests.post
_orig_get = requests.get

def patched_request(method, url, **kwargs):
    kwargs['verify'] = False
    return _session.request(method, url, **kwargs)

def patched_post(url, **kwargs):
    kwargs['verify'] = False
    return _session.post(url, **kwargs)

def patched_get(url, **kwargs):
    kwargs['verify'] = False
    return _session.get(url, **kwargs)

requests.request = patched_request
requests.post = patched_post
requests.get = patched_get

print("[SMS] 🔓 SSL verification disabled for sandbox")

# Import Africa's Talking after all patches
import africastalking
from django.conf import settings

logger = logging.getLogger(__name__)


def format_phone_number(phone_number):
    """
    Format phone number to international format (+254...)
    Handles various input formats:
    - 254718693484 -> +254718693484
    - +254718693484 -> +254718693484
    - 0718693484 -> +254718693484
    - 0112345678 -> +254112345678 (landline format)
    - 112345678 -> +254112345678
    """
    if not phone_number:
        return None
    
    # Convert to string and strip whitespace
    phone = str(phone_number).strip()
    
    # Remove any non-digit characters except +
    phone = ''.join(c for c in phone if c.isdigit() or c == '+')
    
    # Remove leading + if present (we'll add it back)
    if phone.startswith('+'):
        phone = phone[1:]
    
    # If starts with 0, replace with 254 (Kenya country code)
    # This handles both mobile (07x) and landline (011, 020, etc.) formats
    if phone.startswith('0'):
        phone = '254' + phone[1:]
    
    # If doesn't start with 254, add it
    if not phone.startswith('254'):
        phone = '254' + phone
    
    # Add + prefix
    phone = '+' + phone
    
    # Validate length (Kenya numbers are typically 12-13 digits with +254)
    if len(phone) < 12 or len(phone) > 13:
        logger.warning(f"⚠ Phone number {phone} may be invalid (length: {len(phone)})")
    
    return phone


class AfricasTalkingSMSService:
    """
    Service to handle SMS sending via Africa's Talking API
    Includes SSL verification bypass for sandbox environments
    """
    
    def __init__(self):
        """Initialize Africa's Talking API client with SSL bypass"""
        self.api_key = settings.AFRICAS_TALKING_API_KEY
        self.username = settings.AFRICAS_TALKING_USERNAME
        self.sender_id = settings.AFRICAS_TALKING_SENDER_ID
        
        # Initialize the Africa's Talking SDK
        try:
            africastalking.initialize(self.username, self.api_key)
            self.sms = africastalking.SMS
            logger.info(f"✓ Africa's Talking SMS Service initialized (User: {self.username})")
        except Exception as e:
            logger.error(f"❌ Failed to initialize Africa's Talking: {e}")
            raise
    
    def send_sms(self, phone_number, message, sender_id=None):
        """
        Send an SMS message
        
        Args:
            phone_number (str): Recipient phone number (any format)
            message (str): SMS message content
            sender_id (str, optional): Sender ID (use default if not provided)
        
        Returns:
            dict: Response from Africa's Talking API with success/error info
        """
        try:
            # Format phone number to international format
            formatted_phone = format_phone_number(phone_number)
            
            if not formatted_phone:
                return {
                    'status': 'error',
                    'message': f'Invalid phone number: {phone_number}',
                    'error': 'Phone number cannot be empty or invalid'
                }
            
            # Ensure SSL verification is disabled for all requests
            os.environ['REQUESTS_CA_BUNDLE'] = ''
            os.environ['CURL_CA_BUNDLE'] = ''
            
            # Set sender ID if provided
            if sender_id is None:
                sender_id = settings.AFRICAS_TALKING_SENDER_ID
            
            # If sender_id is empty, fall back to username
            if not sender_id or sender_id.strip() == '':
                sender_id = settings.AFRICAS_TALKING_USERNAME
                logger.info(f"No sender ID configured, using username: {sender_id}")
            
            logger.info(f"📤 Sending SMS to {formatted_phone} with sender_id: {sender_id}")
            
            try:
                # Try to send SMS with custom patched requests
                response = self.sms.send(message, [formatted_phone], sender_id=sender_id)  # type: ignore
                
                logger.info(f"✅ SMS sent successfully to {formatted_phone}. Response: {response}")
                return {
                    'status': 'success',
                    'message': 'SMS sent successfully',
                    'response': response
                }
            except Exception as ssl_error:
                # If SSL error occurs, try making a raw request using our insecure session
                if 'SSL' in str(ssl_error) or 'CERTIFICATE' in str(ssl_error).upper():
                    logger.warning(f"⚠ SSL error on first attempt, retrying with direct session: {str(ssl_error)}")
                    
                    try:
                        # Use the patched session directly with the Africa's Talking API
                        url = "https://api.sandbox.africastalking.com/version1/messaging"
                        payload = {
                            'username': self.username,
                            'APIkey': self.api_key,
                            'recipients': formatted_phone,
                            'message': message,
                            'senderID': sender_id
                        }
                        
                        response_obj = _session.post(url, data=payload, verify=False, timeout=30)
                        response_obj.raise_for_status()
                        
                        response = response_obj.json()
                        logger.info(f"✅ SMS sent (retry) successfully to {formatted_phone}")
                        return {
                            'status': 'success',
                            'message': 'SMS sent successfully (retry)',
                            'response': response
                        }
                    except Exception as retry_error:
                        logger.error(f"❌ Retry failed: {str(retry_error)}")
                        raise
                else:
                    # Not an SSL error, re-raise
                    raise
        
        except Exception as e:
            logger.error(f"❌ Failed to send SMS to {phone_number}: {str(e)}")
            import traceback
            traceback.print_exc()
            return {
                'status': 'error',
                'message': f'Failed to send SMS: {str(e)}',
                'error': str(e)
            }
    
    def send_bulk_sms(self, recipients, message, sender_id=None):
        """
        Send SMS to multiple recipients
        
        Args:
            recipients (list): List of phone numbers (any format)
            message (str): SMS message content
            sender_id (str, optional): Sender ID
        
        Returns:
            dict: Response from Africa's Talking API
        """
        try:
            # Format all phone numbers
            formatted_recipients = [format_phone_number(phone) for phone in recipients]
            # Remove None values from invalid phones
            formatted_recipients = [phone for phone in formatted_recipients if phone]
            
            if not formatted_recipients:
                return {
                    'status': 'error',
                    'message': 'No valid phone numbers provided',
                    'error': 'All phone numbers were invalid'
                }
            
            # Ensure SSL verification is disabled for all requests
            os.environ['REQUESTS_CA_BUNDLE'] = ''
            os.environ['CURL_CA_BUNDLE'] = ''
            
            if sender_id is None:
                sender_id = settings.AFRICAS_TALKING_SENDER_ID
            
            # If sender_id is empty, fall back to username
            if not sender_id or sender_id.strip() == '':
                sender_id = settings.AFRICAS_TALKING_USERNAME
            
            logger.info(f"📤 Sending bulk SMS to {len(formatted_recipients)} recipients")
            response = self.sms.send(message, formatted_recipients, sender_id=sender_id)  # type: ignore
            
            logger.info(f"✅ Bulk SMS sent to {len(formatted_recipients)} recipients. Response: {response}")
            return {
                'status': 'success',
                'message': f'SMS sent to {len(formatted_recipients)} recipients',
                'response': response
            }
        except Exception as e:
            logger.error(f"❌ Failed to send bulk SMS: {str(e)}")
            import traceback
            traceback.print_exc()
            return {
                'status': 'error',
                'message': f'Failed to send bulk SMS: {str(e)}',
                'error': str(e)
            }
    def send_order_ready_notification(self, rider_phone, order, rider_name=None):
        """
        Send notification to rider when order is ready for delivery
        
        Args:
            rider_phone (str): Rider's phone number
            order: Order object
            rider_name (str, optional): Rider's name
        
        Returns:
            dict: Result of SMS sending
        """
        try:
            # Ensure SSL verification is disabled for all requests
            os.environ['REQUESTS_CA_BUNDLE'] = ''
            os.environ['CURL_CA_BUNDLE'] = ''
            
            rider_info = f" {rider_name}" if rider_name else ""
            services = ', '.join([s.name for s in order.services.all()]) if order.services.exists() else 'N/A'
            weight_info = f"\nWeight: {order.weight_kg}kg" if order.weight_kg else ""
            
            rider_url = f"https://www.wildwash.co.ke/rider/orders/{order.code}"
            message = (
                f"Order Ready for Delivery{rider_info}!\n"
                f"Order: {order.code}\n"
                f"Service: {services}\n"
                f"Pickup: {order.pickup_address}\n"
                f"Dropoff: {order.dropoff_address}"
                f"{weight_info}\n"
                f"Items: {order.quantity or order.items}\n"
                f"Price: KES {order.actual_price or order.price or 'TBD'}\n"
                f"View: {rider_url}\n"
                f"Please pick up the package. Thank you!"
            )
            
            result = self.send_sms(rider_phone, message)
            logger.info(f"✓ Order ready notification sent to rider for order {order.code}")
            return result
        
        except Exception as e:
            logger.error(f"❌ Failed to send order ready notification for order {order.code}: {e}")
            return {
                'status': 'error',
                'message': f'Failed to send notification: {str(e)}',
                'error': str(e),
                'order_code': order.code if hasattr(order, 'code') else None
            }
    
    def send_order_confirmation(self, customer_phone, order):
        """
        Send order confirmation SMS to customer
        
        Args:
            customer_phone (str): Customer's phone number
            order: Order object
        
        Returns:
            dict: Result of SMS sending
        """
        try:
            # Ensure SSL verification is disabled for all requests
            os.environ['REQUESTS_CA_BUNDLE'] = ''
            os.environ['CURL_CA_BUNDLE'] = ''
            
            services = ', '.join([s.name for s in order.services.all()]) if order.services.exists() else 'N/A'
            order_url = f"https://www.wildwash.co.ke/orders/{order.code}"
            
            message = (
                f"Order Confirmed!\n"
                f"Order #: {order.code}\n"
                f"Service: {services}\n"
                f"Pickup: {order.pickup_address}\n"
                f"Dropoff: {order.dropoff_address}\n"
                f"Price: KES {order.price or 'TBD'}\n"
                f"Status: {order.get_status_display()}\n"
                f"View: {order_url}\n"
                f"Thank you for choosing WildWash!"
            )
            
            result = self.send_sms(customer_phone, message)
            logger.info(f"✓ Order confirmation sent to customer for order {order.code}")
            return result
        
        except Exception as e:
            logger.error(f"❌ Failed to send order confirmation for order {order.code}: {e}")
            return {
                'status': 'error',
                'message': f'Failed to send confirmation: {str(e)}',
                'error': str(e),
                'order_code': order.code if hasattr(order, 'code') else None
            }
    
    def send_delivery_confirmation(self, customer_phone, order):
        """
        Send delivery confirmation SMS to customer
        
        Args:
            customer_phone (str): Customer's phone number
            order: Order object
        
        Returns:
            dict: Result of SMS sending
        """
        try:
            # Ensure SSL verification is disabled for all requests
            os.environ['REQUESTS_CA_BUNDLE'] = ''
            os.environ['CURL_CA_BUNDLE'] = ''
            
            order_url = f"https://www.wildwash.co.ke/orders/{order.code}"
            message = (
                f"Your Order #{order.code} Delivered!\n"
                f"Thank you for using WildWash.\n"
                f"View order: {order_url}\n"
                f"Rate us: wildwash.co.ke"
            )
            
            result = self.send_sms(customer_phone, message)
            logger.info(f"✓ Delivery confirmation sent to customer for order {order.code}")
            return result
        
        except Exception as e:
            logger.error(f"❌ Failed to send delivery confirmation for order {order.code}: {e}")
            return {
                'status': 'error',
                'message': f'Failed to send confirmation: {str(e)}',
                'error': str(e),
                'order_code': order.code if hasattr(order, 'code') else None
            }
    
    def send_order_ready_for_customer(self, customer_phone, order):
        """
        Send order ready notification with invoice to customer
        Notifies that order is ready for delivery or pickup
        
        Args:
            customer_phone (str): Customer's phone number
            order: Order object
        
        Returns:
            dict: Result of SMS sending
        """
        try:
            # Ensure SSL verification is disabled for all requests
            os.environ['REQUESTS_CA_BUNDLE'] = ''
            os.environ['CURL_CA_BUNDLE'] = ''
            
            services = ', '.join([s.name for s in order.services.all()]) if order.services.exists() else 'N/A'
            pickup_address = order.pickup_address if order.pickup_address else 'TBD'
            dropoff_address = order.dropoff_address if order.dropoff_address else 'TBD'
            quantity = order.quantity or order.items or 'N/A'
            weight_info = f"\nWeight: {order.weight_kg}kg" if order.weight_kg else ""
            price = order.actual_price or order.price or 'TBD'
            
            # Format delivery/pickup info
            delivery_text = "ready for delivery" if dropoff_address.lower() != 'to be assigned' else "ready for pickup"
            
            order_url = f"https://www.wildwash.co.ke/orders/{order.code}"
            message = (
                f"Your Order is Ready!\n"
                f"Order #: {order.code}\n"
                f"Service: {services}\n"
                f"Pickup: {pickup_address}\n"
                f"Dropoff: {dropoff_address}\n"
                f"Items: {quantity}"
                f"{weight_info}\n"
                f"Amount: KES {price}\n"
                f"Your order is {delivery_text}!\n"
                f"View: {order_url}\n"
                f"Thank you for choosing WildWash!"
            )
            
            result = self.send_sms(customer_phone, message)
            logger.info(f"✓ Order ready notification sent to customer for order {order.code}")
            return result
        
        except Exception as e:
            logger.error(f"❌ Failed to send order ready notification for order {order.code}: {e}")
            return {
                'status': 'error',
                'message': f'Failed to send notification: {str(e)}',
                'error': str(e),
                'order_code': order.code if hasattr(order, 'code') else None
            }


def send_order_notification_sms(order, admin_phone_number):
    """
    Send SMS notification to admin when a new order is created
    
    Args:
        order: Order object
        admin_phone_number (str): Admin's phone number in international format
    
    Returns:
        dict: Result of SMS sending
    """
    try:
        sms_service = AfricasTalkingSMSService()
        
        # Format the order message
        message = (
            f"New Order Alert!\n"
            f"Order Code: {order.code}\n"
            f"Customer: {order.user.get_full_name() or order.user.username}\n"
            f"Phone: {order.user.phone}\n"
            f"Pickup: {order.pickup_address}\n"
            f"Dropoff: {order.dropoff_address}\n"
            f"Status: {order.get_status_display()}"
        )
        
        result = sms_service.send_sms(admin_phone_number, message)
        return result
    
    except Exception as e:
        logger.error(f"Error sending order notification SMS: {str(e)}")
        return {
            'status': 'error',
            'message': f'Error sending notification: {str(e)}',
            'error': str(e)
        }
