import sys
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import ValidationError
from typing import Optional

class Settings(BaseSettings):
  model_config = SettingsConfigDict(
    env_file=".env",
    env_file_encoding="utf-8",
    case_sensitive=False,
    extra="ignore"
  )

  # Environment
  environment: str = "development"
  debug: bool = True

  # Credentials
  openai_api_key: str
  proxy_url: Optional[str] = None

  @property
  def is_production(self) -> bool:
    return self.environment == "production"

try:
  settings = Settings()
except ValidationError as e:
  if not Path(".env").exists():
    print("\n[!] ERROR: '.env' file not found.")
    print("Please create a '.env' file in the root directory with the following keys:")
    print("ENVIRONMENT, OPENAI_API_KEY")
  else:
    print(f"\n[!] ERROR: Configuration is invalid or missing fields in .env")
    print(f"Details: {e}")
  
  sys.exit(1)
