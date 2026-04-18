import httpx
from typing import Type
from pydantic import BaseModel, ConfigDict, model_validator, Field

class LLMClient(BaseModel):
  model_config = ConfigDict(arbitrary_types_allowed=True)

  # Input parameters
  api_key: str = Field(exclude=True) 
  model: str
  name: str
  system_prompt: str
  format_schema: Type[BaseModel]
  prompt_key: str

  client: httpx.Client = None 
  base_url: str = "https://api.openai.com/v1/responses"

  @model_validator(mode="after")
  def assemble_client(self) -> "LLMClient":
    if not self.api_key:
      raise ValueError("api_key is required")
    
    self.client = httpx.Client(
      headers={
        "Authorization": f"Bearer {self.api_key}",
        "Content-Type": "application/json"
      },
      timeout=60.0
    )
    return self
