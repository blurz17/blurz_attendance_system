from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Database
    DB_URL: str

    # JWT
    jwt_secret: str
    jwt_algorithm: str = "HS256"
    refresh_token_expiary: int = 7       # days
    access_token_expiary: int = 30       # minutes

    # Password hashing
    BCRYPT_ROUNDS: int = 14
     
    # HMAC secret for QR code token signing
    HMAC_SECRET: str

    # Redis
    Redis_Url: str

    # Mail
    MAIL_USERNAME: str
    MAIL_PASSWORD: str
    MAIL_FROM: str
    MAIL_PORT: int = 587
    MAIL_SERVER: str
    MAIL_FROM_NAME: str = "Smart Attendance"
    MAIL_STARTTLS: bool = True
    MAIL_SSL_TLS: bool = False
    USE_CREDENTIALS: bool = True
    VALIDATE_CERTS: bool = True

    # App
    domain: str
    frontend_url: str = "http://localhost:5173"
    password_secrete_reset: str

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


config = Settings()

# Celery configuration
broker_url = config.Redis_Url
result_backend = config.Redis_Url
broker_connection_retry_on_startup = True