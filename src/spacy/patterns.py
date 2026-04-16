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
    if not path.exists():
      raise FileNotFoundError(f"Pattern file not found at: {path}")
      
    with path.open("r", encoding="utf-8") as f:
      data = json.load(f)
      if isinstance(data, list):
        return cls(rules=data)

      rules_data = data.get("rules") or data.get("patterns") or data
      return cls(rules=rules_data)

def extract_patterns_to_flat_list(entity_patterns: EntityPatterns) -> List[str]:
  """
  Extracts all patterns into a flat list of strings for autocomplete.
  """
  flat_list = []
  
  for rule in entity_patterns.rules:
    if isinstance(rule.pattern, str):
      flat_list.append(rule.pattern)

    else:
      tokens = []
      for token in rule.pattern:
        val = token.get("LOWER") or token.get("TEXT") or token.get("LEMMA")
        if val:
          tokens.append(str(val))
      
      if tokens:
        flat_list.append(" ".join(tokens))
        
  return sorted(list(set(flat_list)))

def get_autocomplete_suggestions(file_path: Union[str, Path]) -> List[str]:
  """
  Loads JSON, parses model, and returns flat string list.
  """
  try:
    patterns_container = EntityPatterns.from_json(file_path)    
    return extract_patterns_to_flat_list(patterns_container)
    
  except Exception as e:
    print(f"❌ Error generating autocomplete list: {e}")
    return []
