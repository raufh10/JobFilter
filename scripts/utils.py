from pathlib import Path

def get_file(project_root, override):
  base = project_root / "data"

  path_parts = override.get("path")
  filename = override.get("filename")

  if path_parts:
    return base / Path(*path_parts) / filename
  else:
    return base / filename
