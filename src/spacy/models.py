from pydantic import BaseModel

class ExtractedEntity(BaseModel):
  text: str
  label: str
  start_char: int
  end_char: int

