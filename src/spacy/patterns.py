import json
from pathlib import Path
from typing import List, Dict, Any, Union
from pydantic import BaseModel

class EntityPattern(BaseModel):
  label: str
  pattern: Union[str, List[Dict[str, Any]]]

class EntityPatterns(BaseModel):
  """Container for a collection of entity rules."""
  rules: List[EntityPattern]

  @classmethod
  def from_json(cls, file_path: Union[str, Path]) -> "EntityPatterns":
    path = Path(file_path)
    with path.open("r", encoding="utf-8") as f:
      data = json.load(f)
      if isinstance(data, list):
        return cls(rules=data)
      return cls(**data)

