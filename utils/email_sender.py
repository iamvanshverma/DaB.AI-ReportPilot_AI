# utils/email_sender.py
import os
import requests
import base64
import logging
from datetime import datetime
from email.message import EmailMessage
import smtplib

logger = logging.getLogger(__name__)

class EmailSender:
    SENDGRID_URL = "https://api.sendgrid.com/v3/mail/send"

    def __init__(self):
        # SendGrid config
        self.sg_api_key = os.getenv("SENDGRID_API_KEY")
        self.from_email = os.getenv("SENDGRID_FROM_EMAIL") or os.getenv("RESEND_FROM_EMAIL")
        self.from_name = os.getenv("SENDGRID_FROM_NAME") or os.getenv("RESEND_FROM_NAME", "Report Bot")

        # Optional legacy SMTP config (fallback only)
        self.smtp_user = os.getenv("SMTP_USER")
        self.smtp_pass = os.getenv("SMTP_PASS")
        self.smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", 465))

        if not self.sg_api_key:
            logger.warning("SENDGRID_API_KEY not set. SendGrid disabled; will attempt SMTP fallback if configured.")
        if not self.from_email:
            logger.warning("From email not set (SENDGRID_FROM_EMAIL or RESEND_FROM_EMAIL). Emails may be rejected.")

    def _build_sendgrid_payload(self, recipient_email, subject, html_body, plain_body, attachments):
        personalizations = [{"to": [{"email": recipient_email}], "subject": subject}]
        content = []
        if html_body:
            content.append({"type": "text/html", "value": html_body})
        if plain_body:
            content.append({"type": "text/plain", "value": plain_body})
        if not content:
            content.append({"type": "text/plain", "value": "Please find attached report."})

        payload = {
            "personalizations": personalizations,
            "from": {"email": self.from_email, "name": self.from_name},
            "content": content
        }

        if attachments:
            payload["attachments"] = []
            for a in attachments:
                # a['content'] must be base64 string
                payload["attachments"].append({
                    "content": a["content"],
                    "type": a.get("type", "application/octet-stream"),
                    "filename": a.get("filename", "attachment")
                })
        return payload

    def _smtp_send(self, recipient_email, subject, html_body, plain_body, attachments):
        """
        Legacy SMTP fallback. Note: many hosts (Render free) block SMTP ports.
        """
        msg = EmailMessage()
        msg["Subject"] = subject
        msg["From"] = f"{self.from_name} <{self.from_email}>" if self.from_name else self.from_email
        msg["To"] = recipient_email
        if plain_body:
            msg.set_content(plain_body)
        else:
            msg.set_content("Please view this report in an HTML-capable client.")
        if html_body:
            msg.add_alternative(html_body, subtype="html")

        # Attach files
        for a in attachments or []:
            try:
                data = base64.b64decode(a["content"]) if isinstance(a["content"], str) else a["content"]
                maintype, subtype = (a.get("type") or "application/octet-stream").split("/", 1)
                msg.add_attachment(data, maintype=maintype, subtype=subtype, filename=a.get("filename"))
            except Exception:
                logger.exception("Failed to add attachment via SMTP, skipping attachment.")

        try:
            with smtplib.SMTP_SSL(self.smtp_host, self.smtp_port, timeout=30) as smtp:
                smtp.ehlo()
                if self.smtp_user and self.smtp_pass:
                    smtp.login(self.smtp_user, self.smtp_pass)
                smtp.send_message(msg)
            logger.info("Email sent successfully via SMTP to %s", recipient_email)
            return True
        except Exception as e:
            logger.exception("SMTP send error: %s", e)
            return False

    def send_report(self, recipient_email, report_content, report_name, language):
        """
        report_content expected: dict with keys:
           - 'html' (str) optional
           - 'text' (str) optional
           - 'pdf' (bytes) optional
        """
        date_str = datetime.now().strftime("%Y-%m-%d")
        subject = f"Data Analysis Report - {report_name} - {date_str}"

        html_body = None
        plain_body = None
        attachments = []

        if isinstance(report_content, dict):
            html_body = report_content.get("html")
            plain_body = report_content.get("text")
            pdf_bytes = report_content.get("pdf")
            if pdf_bytes:
                # ensure base64 string for SendGrid
                if isinstance(pdf_bytes, bytes):
                    pdf_b64 = base64.b64encode(pdf_bytes).decode("utf-8")
                else:
                    # if already base64 or string, try to use as-is (user must ensure proper encoding)
                    pdf_b64 = pdf_bytes
                attachments.append({
                    "filename": f"report_{datetime.now().strftime('%Y%m%d')}_{language}.pdf",
                    "content": pdf_b64,
                    "type": "application/pdf"
                })

        # Prefer SendGrid API
        if self.sg_api_key:
            payload = self._build_sendgrid_payload(recipient_email, subject, html_body, plain_body, attachments)
            headers = {"Authorization": f"Bearer {self.sg_api_key}", "Content-Type": "application/json"}
            try:
                resp = requests.post(self.SENDGRID_URL, json=payload, headers=headers, timeout=30)
                # SendGrid returns 202 on success
                if resp.status_code >= 400:
                    logger.error("SendGrid returned error %s: %s", resp.status_code, resp.text)
                    resp.raise_for_status()
                logger.info("Email sent successfully via SendGrid to %s", recipient_email)
                return True
            except Exception as e:
                logger.exception("SendGrid send error: %s", e)
                # fallthrough to SMTP fallback (if configured)
        else:
            logger.info("No SendGrid key, or SendGrid failed — attempting SMTP fallback (if configured).")

        # SMTP fallback (only if configured)
        if self.smtp_user and self.smtp_pass:
            return self._smtp_send(recipient_email, subject, html_body, plain_body, attachments)

        logger.error("No available email provider configured (SendGrid missing and SMTP not configured).")
        return False
