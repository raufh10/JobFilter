from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class Settings(BaseSettings):
  model_config = SettingsConfigDict(
    env_file=".env",
    env_file_encoding="utf-8",
    case_sensitive=False,
  )

  # Environment
  environment: str
  debug: bool = True

  # Credentials
  openai_api_key: str
  proxy_url: Optional[str] = None

  @property
  def is_production(self) -> bool:
    return self.environment == "production"

settings = Settings()
