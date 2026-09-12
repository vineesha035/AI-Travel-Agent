import os
from dotenv import load_dotenv
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

load_dotenv()

SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY")


def send_email(sender_email: str, receiver_email: str, subject: str, content: str):
    """
    Send an email via SendGrid. Returns a dict indicating success or failure.
    """
    message = Mail(
        from_email=sender_email,
        to_emails=receiver_email,
        subject=subject,
        html_content=content.replace("\n", "<br>"),
    )
    try:
        sg = SendGridAPIClient(SENDGRID_API_KEY)
        response = sg.send(message)
        return {"success": True, "status_code": response.status_code}
    except Exception as e:
        return {"success": False, "error": str(e)}