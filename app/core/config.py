from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    APP_NAME: str = "Finance Dashboard API"
    APP_VERSION: str = "1.0.0"
    SECRET_KEY: str = "super-secret-key-change-in-production-min-32-chars"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24

    # MongoDB
    MONGODB_URL: str = "mongodb://localhost:27017"
    MONGODB_DB_NAME: str = "finance_db"

    # Admin seed credentials — override in production via .env
    ADMIN_NAME: str = "Super Admin"
    ADMIN_EMAIL: str = "admin@finance.dev"
    ADMIN_PASSWORD: str = "Admin@123"

    class Config:
        env_file = ".env"

settings = Settings()
