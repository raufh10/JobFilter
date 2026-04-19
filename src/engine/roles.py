import json
from pathlib import Path
from typing import List, Optional, Union
from pydantic import BaseModel, Field, ConfigDict

from src.jobspy import JobSpyClient

class Role(BaseModel):
  """Defines a specific job role and its search configuration."""
  model_config = ConfigDict(extra='forbid')

  name: str = Field(..., description="Unique name for the role, e.g., 'Data Analyst'")
  client: JobSpyClient

class Roles(BaseModel):
  """Container for managing multiple roles with shortcut support."""
  model_config = ConfigDict(extra='forbid')

  roles: List[Role] = Field(default_factory=list)

  def save(self, path: Path = Path("data/cli/roles.json")):
    """Saves the roles configuration to a JSON file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
      f.write(self.model_dump_json(indent=2))

  @classmethod
  def load(cls, path: Path = Path("data/cli/roles.json")) -> "Roles":
    """Loads the roles configuration. Returns empty container if not found."""
    if not path.exists():
      return cls()
    try:
      with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
        roles_list = data.get("roles", []) if isinstance(data, dict) else data
        return cls(roles=roles_list)
    except (json.JSONDecodeError, ValueError):
      return cls()

  def get_role(self, identifier: Union[str, int]) -> Optional[Role]:
    """
    Retrieves a role by its name (str) or its shortcut index (int).
    Indices start at 1 for user-friendliness.
    """
    if isinstance(identifier, int):
      # Adjusting to 1-based indexing for the CLI shortcut
      index = identifier - 1
      if 0 <= index < len(self.roles):
        return self.roles[index]
      return None

    for role in self.roles:
      if role.name.lower() == identifier.lower():
        return role
    return None

  def list_roles(self):
    """Prints roles with their associated shortcut indices."""
    if not self.roles:
      print("No roles configured.")
      return
    
    for i, role in enumerate(self.roles, 1):
      print(f"[{i}] {role.name}")

  def add_role(self, role: Role, overwrite: bool = True):
    """Adds a new role or replaces an existing one by name."""
    if overwrite:
      self.roles = [r for r in self.roles if r.name.lower() != role.name.lower()]
    self.roles.append(role)
