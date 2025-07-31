import os
import smtplib
from email.message import EmailMessage
import logging

logger = logging.getLogger(__name__)

class EmailSender:
    def __init__(self):
        self.smtp_user = os.getenv("SMTP_USER")
        self.smtp_pass = os.getenv("SMTP_PASS")

    def send_report(self, recipient_email, report_content, report_name, language):
        # Build the message
        msg = EmailMessage()
        msg["Subject"] = f"{report_name} ({language.upper()})"
        msg["From"]    = self.smtp_user
        msg["To"]      = recipient_email
        html = report_content.get("html", "<p>Please find attached the report.</p>")
        msg.set_content("Please view this report in an HTML‑capable client.")
        msg.add_alternative(html, subtype="html")

        # Attach PDF if present
        pdf_bytes = report_content.get("pdf")
        if pdf_bytes:
            msg.add_attachment(
                pdf_bytes,
                maintype="application",
                subtype="pdf",
                filename=f"{report_name}.pdf"
            )

        # Send over SSL
        try:
            with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
                smtp.ehlo()
                smtp.login(self.smtp_user, self.smtp_pass)
                smtp.send_message(msg)
            logger.info(f"Email sent successfully to {recipient_email}")
            return True
        except Exception as e:
            logger.error(f"SMTP send error: {e}", exc_info=True)
            return False