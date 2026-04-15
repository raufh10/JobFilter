from pydantic import BaseModel, Field

class TokenCount(BaseModel):
  text: str
  token_count: int = Field(..., description="The number of tokens in the provided text")

class BatchTokenCount(BaseModel):
  counts: list[TokenCount]
  total_tokens: int = Field(..., description="Sum of all tokens in the batch")
