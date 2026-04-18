import json
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict

class Resume(BaseModel):
  model_config = ConfigDict(extra='forbid')

  content: str = Field(
    default="", 
    description="The full text content of the resume or CV."
  )

  def save(self, path: Path = Path("data/cli/resume.json")):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
      f.write(self.model_dump_json(indent=2))

  @classmethod
  def load(cls, path: Path = Path("data/cli/resume.json")) -> "Resume":

    if not path.exists():
      return cls()

    try:
      with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
        if isinstance(data, str):
          return cls(content=data)
        return cls.model_validate(data)
    except (json.JSONDecodeError, ValueError):
      return cls()
