import os
import requests
import base64
from datetime import datetime
import logging
from dotenv import load_dotenv
import json

load_dotenv()
logger = logging.getLogger(__name__)

class EmailSender:
    def __init__(self):
        self.api_key = os.getenv('RESEND_API_KEY')
        self.from_email = os.getenv('RESEND_FROM_EMAIL')
        self.from_name = os.getenv('RESEND_FROM_NAME')
    
    def send_report(self, recipient_email, report_content, report_name, language):
        """Send report via email"""
        try:
            # Create safe subject without unicode characters
            date_str = datetime.now().strftime('%Y-%m-%d')
            subject = f"Data Analysis Report - {report_name} - {date_str}"
            
            # Prepare attachments
            attachments = []
            if 'pdf' in report_content:
                pdf_base64 = base64.b64encode(report_content['pdf']).decode('utf-8')
                attachments.append({
                    "filename": f"report_{datetime.now().strftime('%Y%m%d')}_{language}.pdf",
                    "content": pdf_base64,
                    "type": "application/pdf"
                })
            
            # Email data with proper encoding
            email_data = {
                "from": f"{self.from_name} <{self.from_email}>",
                "to": [recipient_email],
                "subject": subject,
                "html": report_content.get('html', '<p>Please find attached report.</p>'),
                "attachments": attachments
            }
            
            # Send via Resend
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            response = requests.post(
                "https://api.resend.com/emails",
                json=email_data,
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                logger.info(f"Email sent successfully to {recipient_email}")
                return True
            else:
                logger.error(f"Failed to send email: {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Email error: {str(e)}")
            return False