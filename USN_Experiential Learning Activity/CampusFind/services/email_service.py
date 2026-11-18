import smtplib, sys
from email.message import EmailMessage
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

class EmailService:
    def __init__(self):
        self._sent = set()  # (to_email, subject) for dedup
    
    def send_email(self, to_email: str, subject: str, body: str) -> bool:
        try:
            from config import SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD, SMTP_FROM, EMAIL_ENABLED
            if not EMAIL_ENABLED:
                print(f"[EmailService] Email not configured. Would send to {to_email}: {subject}")
                return False
            
            key = (to_email, subject)
            if key in self._sent:
                return True  # already sent
            
            msg = EmailMessage()
            msg['Subject'] = subject
            msg['From'] = SMTP_FROM or SMTP_USER
            msg['To'] = to_email
            msg.set_content(body)
            
            if SMTP_PORT == 465:
                with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT) as s:
                    s.login(SMTP_USER, SMTP_PASSWORD)
                    s.send_message(msg)
            else:
                with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as s:
                    s.ehlo()
                    s.starttls()
                    s.login(SMTP_USER, SMTP_PASSWORD)
                    s.send_message(msg)
            
            self._sent.add(key)
            return True
        except Exception as e:
            print(f"[EmailService] Failed to send email: {e}")
            return False
    
    def send_match_notification(self, user_email, user_name, lost_item, found_item, score) -> bool:
        subject = "CampusFind: Possible Match Found!"
        body = f"""Dear {user_name},

Good news! We found a possible match for your lost item.

Lost Item: {lost_item}
Found Item: {found_item}
Match Score: {score:.0f}%

Please log in to CampusFind to review the match and submit a claim if appropriate.

Best regards,
CampusFind Team"""
        return self.send_email(user_email, subject, body)
    
    def send_claim_submitted(self, admin_email, claimant_name, item_name, claim_id) -> bool:
        subject = f"CampusFind: New Claim #{claim_id} Submitted"
        body = f"""A new ownership claim has been submitted.

Claimant: {claimant_name}
Item: {item_name}
Claim ID: #{claim_id}

Please log in to the CampusFind admin panel to review this claim.

CampusFind System"""
        return self.send_email(admin_email, subject, body)
    
    def send_claim_status_update(self, user_email, user_name, item_name, new_status, remarks="") -> bool:
        subject = f"CampusFind: Your Claim has been {new_status.title()}"
        body = f"""Dear {user_name},

Your ownership claim for "{item_name}" has been updated.

Status: {new_status.upper()}
{f'Admin Remarks: {remarks}' if remarks else ''}

Please log in to CampusFind for more details.

Best regards,
CampusFind Team"""
        return self.send_email(user_email, subject, body)
    
    def send_item_returned(self, user_email, user_name, item_name) -> bool:
        subject = "CampusFind: Your Item is Ready for Pickup"
        body = f"""Dear {user_name},

Great news! Your item "{item_name}" has been confirmed as returned.

Please contact the administrator to arrange pickup.

Best regards,
CampusFind Team"""
        return self.send_email(user_email, subject, body)

email_service = EmailService()
