import smtplib
import ssl
from email.message import EmailMessage


def send_email(recipient: str, subject: str, body: str) -> bool:
    """
    Sends an email with a simple (and unsecure) SMTP connection.

    Returns a boolean representing whether the email sent correctly.
    """

    sender = "Breeze <uclauctionsite2024g27@gmail.com>"  # uses an existing account
    username = "uclauctionsite2024g27@gmail.com"
    password = "fbat vjrj ouqj ykcr"
    server = "smtp.gmail.com"
    port = "465"

    try:
        # Create message
        message = EmailMessage()
        message.set_content(body)
        message["Subject"] = subject
        message["From"] = sender
        message["To"] = recipient

        # Start email connection
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL(server, port, context=context) as server:
            server.login(username, password)
            server.send_message(message)

        return True
    except Exception:
        # Return False as email was not sent
        return False
