from ipaddress import ip_address
from pathlib import Path
from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.engine import make_url
from urllib.parse import urlsplit


class Settings(BaseSettings):
    APP_NAME: str = "Gadget Store OS"
    APP_VERSION: str = "1.0.0"
    API_V1_PREFIX: str = "/api"
    ENVIRONMENT: str = "development"
    SECRET_KEY: str = "phase25-development-secret-change-me"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    # A fresh process must resolve the same local development database no
    # matter which directory it was started from. Deployment environments
    # always provide DATABASE_URL explicitly.
    DATABASE_URL: str = ""
    CORS_ORIGINS: str = "http://localhost:3000,http://127.0.0.1:3000"
    WEBAUTHN_RP_NAME: str = "Gadget Store OS"
    WEBAUTHN_RP_ID: str = "localhost"
    WEBAUTHN_ORIGIN: str = "http://localhost:3000"
    PAYSTACK_MODE: str = "disabled"
    PAYSTACK_SECRET_KEY: str = ""

    model_config = SettingsConfigDict(
        env_file=str(Path(__file__).resolve().parents[2] / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @model_validator(mode="after")
    def validate_production_settings(self):
        environment = self.ENVIRONMENT.strip().lower()
        if environment not in {"development", "test", "staging", "production"}:
            raise ValueError("ENVIRONMENT must be development, test, staging, or production")

        payment_mode = self.PAYSTACK_MODE.strip().lower()
        if payment_mode not in {"disabled", "test", "live"}:
            raise ValueError("PAYSTACK_MODE must be disabled, test, or live")
        if payment_mode != "disabled":
            expected_prefix = "sk_live_" if payment_mode == "live" else "sk_test_"
            if not self.PAYSTACK_SECRET_KEY.startswith(expected_prefix):
                raise ValueError(f"PAYSTACK_SECRET_KEY must match {payment_mode} mode")
            if environment == "production" and payment_mode != "live":
                raise ValueError("Production cannot use Paystack test mode")
            if environment in {"development", "test", "staging"} and payment_mode == "live":
                raise ValueError(f"{environment.title()} cannot use Paystack live mode")

        if not self.DATABASE_URL:
            if environment in {"staging", "production"}:
                raise ValueError(f"{environment.title()} requires DATABASE_URL")
            if environment == "development":
                self.DATABASE_URL = f"sqlite:///{(Path(__file__).resolve().parents[2] / 'gsos_local.db').as_posix()}"
            return self

        url = make_url(self.DATABASE_URL)
        database_name = (url.database or "").lower()
        host_name = (url.host or "").lower()
        is_postgres = url.get_backend_name() == "postgresql"

        if environment in {"staging", "production"}:
            if not is_postgres:
                raise ValueError(f"{environment.title()} requires a PostgreSQL DATABASE_URL")
            normalized_secret = self.SECRET_KEY.strip().lower()
            if (
                len(self.SECRET_KEY) < 32
                or normalized_secret == "phase25-development-secret-change-me"
                or any(marker in normalized_secret for marker in ("generate_a_unique", "change_me", "changeme"))
            ):
                raise ValueError(f"{environment.title()} requires a unique SECRET_KEY of at least 32 characters")
            if not self.CORS_ORIGINS.strip():
                raise ValueError(f"{environment.title()} requires explicit CORS_ORIGINS")
            if not self.WEBAUTHN_RP_ID.strip() or not self.WEBAUTHN_ORIGIN.startswith("https://"):
                raise ValueError(f"{environment.title()} requires an HTTPS WebAuthn origin and RP ID")
            origins = [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]
            for origin in origins:
                parsed_origin = urlsplit(origin)
                hostname = (parsed_origin.hostname or "").lower()
                try:
                    is_loopback = ip_address(hostname).is_loopback
                except ValueError:
                    is_loopback = hostname == "localhost" or hostname.endswith(".localhost")
                if (
                    origin == "*"
                    or parsed_origin.scheme != "https"
                    or not hostname
                    or is_loopback
                    or parsed_origin.path not in {"", "/"}
                    or parsed_origin.query
                    or parsed_origin.fragment
                ):
                    raise ValueError(f"{environment.title()} CORS_ORIGINS must contain only public HTTPS origins")
            rp_id = self.WEBAUTHN_RP_ID.strip().lower()
            webauthn_host = (urlsplit(self.WEBAUTHN_ORIGIN).hostname or "").lower()
            if rp_id in {"localhost", "127.0.0.1", "::1"} or (
                webauthn_host != rp_id and not webauthn_host.endswith(f".{rp_id}")
            ):
                raise ValueError(f"{environment.title()} WebAuthn origin host must match its public RP ID")

        if environment == "staging":
            if "staging" not in database_name:
                raise ValueError("Staging DATABASE_URL must target a separately named staging database")
            if any(marker in host_name for marker in ("production", "prod")):
                raise ValueError("Staging DATABASE_URL cannot target a production host")
        if environment == "production":
            if any(marker in database_name or marker in host_name for marker in ("test", "staging")):
                raise ValueError("Production DATABASE_URL cannot target a test or staging database or host")
            if "production" not in database_name and "prod" not in database_name:
                raise ValueError("Production DATABASE_URL must target a production-named database")

        if environment == "test":
            if any(marker in database_name or marker in host_name for marker in ("production", "prod", "staging")):
                raise ValueError("Test DATABASE_URL cannot target production or staging data")
            if not is_postgres and url.get_backend_name() != "sqlite":
                raise ValueError("Test DATABASE_URL must use SQLite or PostgreSQL")
        return self

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip().rstrip("/") for origin in self.CORS_ORIGINS.split(",") if origin.strip()]


settings = Settings()
