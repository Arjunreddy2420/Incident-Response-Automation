from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    DATABASE_URL: str = (
        "postgresql://incidents_user:incidents_password@localhost:5432/incidents"
    )
    SLACK_WEBHOOK_URL: str = ""
    LOG_LEVEL: str = "INFO"
    PORT: int = 8000
    ALERT_CORRELATION_WINDOW_MINUTES: int = 15
    ESCALATION_CHECK_INTERVAL_SECONDS: int = 60

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
