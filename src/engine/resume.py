import orjson
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict

class Resume(BaseModel):
  model_config = ConfigDict(
    extra='forbid',
    populate_by_name=True 
  )

  content: str = Field(
    default="", 
    description="The full text content of the resume or CV."
  )

  def save(self, path: Path = Path("data/cli/resume.json")):
    """Saves the resume using orjson for fast serialization."""
    path.parent.mkdir(parents=True, exist_ok=True)
    
    binary_data = orjson.dumps(
      self.model_dump(), 
      option=orjson.OPT_INDENT_2 | orjson.OPT_APPEND_NEWLINE
    )
    
    with path.open("wb") as f:
      f.write(binary_data)

  @classmethod
  def load(cls, path: Path = Path("data/cli/resume.json")) -> "Resume":
    """Loads the resume using orjson for fast parsing."""
    if not path.exists():
      return cls()

    try:
      binary_data = path.read_bytes()
      if not binary_data:
        return cls()
        
      data = orjson.loads(binary_data)
      
      if isinstance(data, str):
        return cls(content=data)
      return cls.model_validate(data)
      
    except (orjson.JSONDecodeError, ValueError):
      return cls()
