from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
  model_config = SettingsConfigDict(
    env_file=".env",
    env_file_encoding="utf-8",
    case_sensitive=False,
  )

  # Environment
  environment: str

  @property
  def is_production(self) -> bool:
    return self.environment == "production"

settings = Settings()
