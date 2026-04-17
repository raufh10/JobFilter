import sys
import json
from pathlib import Path

# --- Path Fixing ---
project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))

from src.spacy.patterns import EntityPattern

# --- Configuration ---
INPUT_SKILLS_JSON = project_root / "data" / "skills.json"
OUTPUT_PATTERNS_JSONL = project_root / "data" / "patterns" / "data_analyst.jsonl"

def generate_spacy_patterns():
  """
  Converts a structured JSON of skills into a JSONL file of spaCy EntityRuler patterns.
  """
  if not INPUT_SKILLS_JSON.exists():
    print(f"❌ Input file not found: {INPUT_SKILLS_JSON}")
    return

  # 1. Load the raw skills JSON
  with open(INPUT_SKILLS_JSON, "r", encoding="utf-8") as f:
    skills_data = json.load(f)

  # 2. Iterate through categories and build rules
  all_rules = []
  
  for category, skills in skills_data.items():
    if not isinstance(skills, list):
      continue

    # Standardize label (e.g., 'languages' -> 'LANGUAGES')
    label = category.upper()
    
    for skill in skills:
      # Create validated EntityPattern
      rule = EntityPattern(
        label=label,
        pattern=skill
      )
      all_rules.append(rule)

  # 3. Save as JSONL
  OUTPUT_PATTERNS_JSONL.parent.mkdir(parents=True, exist_ok=True)
  
  with open(OUTPUT_PATTERNS_JSONL, "w", encoding="utf-8") as f:
    for rule in all_rules:
      # model_dump(exclude_none=True) ensures spaCy doesn't get nulls
      f.write(json.dumps(rule.model_dump(exclude_none=True)) + "\n")

  print(f"✅ Successfully converted {len(all_rules)} skills to spaCy patterns.")
  print(f"📁 Output: {OUTPUT_PATTERNS_JSONL}")

if __name__ == "__main__":
  generate_spacy_patterns()

