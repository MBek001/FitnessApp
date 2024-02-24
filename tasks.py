import smtplib

from celery import Celery
from email.message import EmailMessage

from config import MAIL_USERNAME, RESET_PASSWORD_REDIRECT_URL, SECRET, RESET_PASSWORD_EXPIRY_MINUTES, MAIL_SERVER, \
    MAIL_PASSWORD, MAIL_PORT, REDIS_HOST, REDIS_PORT, SMTP_USER, SMTP_PASSWORD


celery = Celery(
    "tasks",
    broker=f"redis://{REDIS_HOST}:{REDIS_PORT}/0",
    backend=f"redis://{REDIS_HOST}:{REDIS_PORT}/0"
)


def get_email_template_dashboard(user_email, code):
    email = EmailMessage()
    email['Subject'] = f'Verify email'
    email['From'] = MAIL_USERNAME
    email['To'] = user_email

    email.set_content(
        f"""
        <div>
            <h1 style="color: black;"> Hi!😊 </h1>
            <h1 style="color: black;"> Thank you for joining Fitness </h1>
            <h1 style="color: black;">Enter the verification code below to activate your account: </h1>
            <h1 style="margin: 0; padding-right: 2px; width: 90px ; background-color: green; color: white;"> {code} </h1>
        </div>
        """,
        subtype='html'
    )
    return email


@celery.task
def send_mail_for_forget_password(email: str, code: int):
    email = get_email_template_dashboard(email, code)
    with smtplib.SMTP_SSL(MAIL_SERVER, MAIL_PORT) as server:
        server.login(SMTP_USER, SMTP_PASSWORD)
        server.send_message(email)
