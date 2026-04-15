from typing import Type
from pydantic import BaseModel, ConfigDict, model_validator, Field
from openai import OpenAI

class LLMClient(BaseModel):

  """
  Unified model for OpenAI client and request configuration.
  """

  model_config = ConfigDict(arbitrary_types_allowed=True)

  # Input parameters
  api_key: str = Field(exclude=True) 
  model: str
  system_prompt: str
  format_schema: Type[BaseModel]

  # Populated automatically after initialization
  client: OpenAI = None 

  @model_validator(mode="after")
  def assemble_client(self) -> "LLMClient":
    if not self.api_key:
      raise ValueError("api_key is required")
    self.client = OpenAI(api_key=self.api_key)
    return self
