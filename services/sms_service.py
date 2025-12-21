# services/sms_service.py
import logging
import africastalking
import requests
from django.conf import settings
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logger = logging.getLogger(__name__)


class AfricasTalkingSMSService:
    """
    Service to handle SMS sending via Africa's Talking API
    """
    
    def __init__(self):
        """Initialize Africa's Talking API client"""
        self.api_key = settings.AFRICAS_TALKING_API_KEY
        self.username = settings.AFRICAS_TALKING_USERNAME
        
        # Initialize the Africa's Talking SDK
        africastalking.initialize(self.username, self.api_key)
        self.sms = africastalking.SMS
    
    def send_sms(self, phone_number, message, sender_id=None):
        """
        Send an SMS message
        
        Args:
            phone_number (str): Recipient phone number in international format (e.g., +254712345678)
            message (str): SMS message content
            sender_id (str, optional): Sender ID (use default if not provided)
        
        Returns:
            dict: Response from Africa's Talking API with success/error info
        """
        try:
            # Set sender ID if provided
            if sender_id is None:
                sender_id = settings.AFRICAS_TALKING_SENDER_ID
            
            # Send the SMS
            response = self.sms.send(message, [phone_number], sender_id=sender_id)
            
            logger.info(f"SMS sent successfully to {phone_number}. Response: {response}")
            return {
                'status': 'success',
                'message': 'SMS sent successfully',
                'response': response
            }
        except Exception as e:
            logger.error(f"Failed to send SMS to {phone_number}: {str(e)}")
            return {
                'status': 'error',
                'message': f'Failed to send SMS: {str(e)}',
                'error': str(e)
            }
    
    def send_bulk_sms(self, recipients, message, sender_id=None):
        """
        Send SMS to multiple recipients
        
        Args:
            recipients (list): List of phone numbers
            message (str): SMS message content
            sender_id (str, optional): Sender ID
        
        Returns:
            dict: Response from Africa's Talking API
        """
        try:
            if sender_id is None:
                sender_id = settings.AFRICAS_TALKING_SENDER_ID
            
            response = self.sms.send(message, recipients, sender_id=sender_id)
            
            logger.info(f"Bulk SMS sent to {len(recipients)} recipients. Response: {response}")
            return {
                'status': 'success',
                'message': f'SMS sent to {len(recipients)} recipients',
                'response': response
            }
        except Exception as e:
            logger.error(f"Failed to send bulk SMS: {str(e)}")
            return {
                'status': 'error',
                'message': f'Failed to send bulk SMS: {str(e)}',
                'error': str(e)
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
            f"Urgency: {order.urgency}/5\n"
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
