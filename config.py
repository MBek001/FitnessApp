import os
from dotenv import load_dotenv

load_dotenv()

DB_NAME = os.environ.get('DB_NAME')
DB_USER = os.environ.get('DB_USER')
DB_PASSWORD = os.environ.get('DB_PASSWORD')
DB_HOST = os.environ.get('DB_HOST')
DB_PORT = os.environ.get('DB_PORT')
SECRET = os.environ.get('SECRET')
MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
MAIL_FROM = os.environ.get('MAIL_FROM')
MAIL_PORT = os.environ.get('MAIL_PORT')
MAIL_SERVER = os.environ.get('MAIL_SERVER')
MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
RESET_PASSWORD_REDIRECT_URL: str = 'reset-password'
RESET_PASSWORD_EXPIRY_MINUTES: int = 60 * 12
REDIS_HOST = os.environ.get('REDIS_HOST')
REDIS_PORT = os.environ.get('REDIS_PORT')
GOOGLE_CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID')
GOOGLE_CLIENT_SECRET_KEY = os.environ.get('GOOGLE_CLIENT_SECRET_KEY')
GOOGLE_REDIRECT_URL = os.environ.get('GOOGLE_REDIRECT_URL')

SMTP_USER = os.environ.get('SMTP_USER')
SMTP_PASSWORD = os.environ.get('SMTP_PASSWORD')
