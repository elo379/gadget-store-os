from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str = "Gadget Store OS"
    APP_VERSION: str = "1.0.0"
    API_V1_PREFIX: str = "/api"
    SECRET_KEY: str = "phase25-development-secret-change-me"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    DATABASE_URL: str = ""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
