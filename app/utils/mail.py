from fastapi import HTTPException
import smtplib
from app.config.envconfig import settings
import string
import secrets
import smtplib
from email.message import EmailMessage
from fastapi import HTTPException
from app.config import settings

# from app.database.models import User

# def sendmail(to_email: str, message: str):
#     try:
#         with smtplib.SMTP_SSL(
#             settings.EMAIL_HOST, settings.EMAIL_PORT, timeout=10
#         ) as server:
#             # with smtplib.SMTP(settings.EMAIL_HOST, settings.EMAIL_PORT) as server:
#             # server.starttls()
#             server.login(settings.EMAIL_USER, settings.EMAIL_PASSWORD)

#             server.sendmail(
#                 f"{settings.APP_NAME} <{settings.EMAIL_USER}>", to_email, message
#             )
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Error sending email: {str(e)}")

def send_mail(to_email: str, subject: str, body: str):
    try:
        msg = EmailMessage()
        msg["From"] = f"{settings.APP_NAME} <{settings.EMAIL_USER}>"
        msg["To"] = to_email
        msg["Subject"] = subject
        msg.set_content(body)

        with smtplib.SMTP(settings.EMAIL_HOST, settings.EMAIL_PORT, timeout=10) as server:
            server.starttls()
            server.login(settings.EMAIL_USER, settings.EMAIL_PASSWORD)
            server.send_message(msg)

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Email sending failed: {str(e)}"
        )

    
def send_account_verification_email(to_email: str, token: str):
    subject = f"{settings.APP_NAME} – Account Verification"
    body = (
        f"Hello,\n\n"
        f"Your account verification code is:\n\n"
        f"{token}\n\n"
        f"This code will expire in 15 minutes.\n\n"
        f"If you did not request this, please ignore this email.\n\n"
        f"{settings.APP_NAME} Team"
    )

    send_mail(to_email, subject, body)



def send_reset_email(to_email: str, token: str):
    subject = f"{settings.APP_NAME} – Password Reset"
    body = (
        f"Hello,\n\n"
        f"Your password reset code is:\n\n"
        f"{token}\n\n"
        f"This code will expire in 15 minutes.\n\n"
        f"If you did not request this, please secure your account.\n\n"
        f"{settings.APP_NAME} Team"
    )

    send_mail(to_email, subject, body)



def admin_send_reset_email(to_email: str, temp_password: str):
    subject = f"{settings.APP_NAME} – Temporary Password Issued"
    body = (
        f"Hello,\n\n"
        f"A temporary password has been created for your account.\n\n"
        f"Temporary Password:\n{temp_password}\n\n"
        f"Please log in and change your password immediately.\n\n"
        f"If this was not requested by you, contact support right away.\n\n"
        f"Best regards,\n"
        f"{settings.APP_NAME} Team"
    )

    send_mail(to_email, subject, body)
