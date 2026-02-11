from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, EmailStr

class AppConfig(BaseSettings):
    """
    Application Configuration using Pydantic Settings.
    Follows SRP: Responsible for loading and validating configuration.
    Fails fast if required environment variables are missing.
    """
    
    # MagangHub Credentials
    maganghub_email: EmailStr = Field(..., description="Email for MagangHub login")
    maganghub_password: str = Field(..., description="Password for MagangHub login")
    
    # AI Configuration
    openrouter_api_key: str = Field(..., description="API Key for OpenRouter")
    ai_model: str = Field("openai/gpt-4o-mini", description="AI Model to use")
    
    # Context
    aktivitas_konteks: str = Field("Mahasiswa Magang IT", description="Context for AI generation")
    
    # App Settings
    show_browser: bool = Field(True, validation_alias="SHOW_BROWSER", description="Show browser GUI")
    log_level: str = Field("INFO", description="Logging level")

    # Telegram Bot
    telegram_bot_token: str = Field(None, description="Token for Telegram Bot")
    allowed_telegram_id: str = Field(None, description="Allowed User ID for bot")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",  # Ignore extra fields in .env
        case_sensitive=False  # Allow MAGANGHUB_EMAIL or maganghub_email
    )

# Singleton instance
try:
    config = AppConfig()
except Exception as e:
    print(f"❌ Configuration Error: {e}")
    # We might want to exit here, but letting the caller handle it is more flexible
    config = None
