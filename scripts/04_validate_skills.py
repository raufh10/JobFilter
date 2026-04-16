import json
import logging
from pathlib import Path
from rapidfuzz import fuzz, process

# Fix pathing
project_root = Path(__file__).resolve().parent.parent

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
logger = logging.getLogger(__name__)

def load_json(path: Path):
  with open(path, "r", encoding="utf-8") as f:
    return json.load(f)

def load_jsonl_patterns(path: Path):
  patterns = []
  with open(path, "r", encoding="utf-8") as f:
    for line in f:
      patterns.append(json.loads(line))
  return patterns

def get_text_from_pattern(pattern_val):
  """Extracts a searchable string from either a string or a list of TokenPatterns."""
  if isinstance(pattern_val, str):
    return pattern_val
  # For token patterns, join the 'LOWER', 'TEXT', or 'LEMMA' fields
  tokens = []
  for token in pattern_val:
    val = token.get("LOWER") or token.get("TEXT") or token.get("LEMMA") or ""
    if val: tokens.append(val)
  return " ".join(tokens)

def main():
  # 1. Paths
  extracted_skills_path = project_root / "data" / "extracted_skills.json"
  spacy_patterns_path = project_root / "data" / "spacy_patterns.jsonl"

  if not extracted_skills_path.exists() or not spacy_patterns_path.exists():
    logger.error("Required data files missing (extracted_skills.json or spacy_patterns.jsonl)")
    return

  # 2. Load Data
  extracted_data = load_json(extracted_skills_path)
  spacy_patterns = load_jsonl_patterns(spacy_patterns_path)

  # Prepare lists for comparison
  # We flatten all extracted skills from script 02
  ground_truth_skills = []
  for job in extracted_data.get("data", []):
    for category, items in job.get("extracted_data", {}).items():
      ground_truth_skills.extend(items)
  
  # Prepare final generated strings from script 03
  generated_skills = [get_text_from_pattern(p["pattern"]) for p in spacy_patterns]

  logger.info(f"📊 Comparing {len(ground_truth_skills)} raw skills vs {len(generated_skills)} generated patterns...")

  # 3. Fuzzy Matching Validation
  matches = []
  missing = []
  threshold = 85 # Adjust similarity threshold (0-100)

  for raw in set(ground_truth_skills):
    # Find the best match in the generated patterns
    best_match = process.extractOne(raw, generated_skills, scorer=fuzz.token_sort_ratio)
    
    if best_match and best_match[1] >= threshold:
      matches.append({
        "raw": raw,
        "matched_pattern": best_match[0],
        "score": round(best_match[1], 2)
      })
    else:
      missing.append(raw)

  # 4. Reporting
  accuracy = (len(matches) / len(set(ground_truth_skills))) * 100 if ground_truth_skills else 0
  
  print("\n" + "="*40)
  print(f"       VALIDATION REPORT")
  print("="*40)
  print(f"Total Unique Raw Skills:  {len(set(ground_truth_skills))}")
  print(f"Matched Patterns:         {len(matches)}")
  print(f"Missing/Poor Matches:     {len(missing)}")
  print(f"Fuzzy Accuracy Score:     {accuracy:.2f}%")
  print("="*40)

  if missing:
    print("\n⚠️  Top Missing or Low-Similarity Skills:")
    for item in missing[:10]:
      print(f" - {item}")

  # Optional: Save validation log
  val_log_path = project_root / "data" / "validation_report.json"
  with open(val_log_path, "w") as f:
    json.dump({"matches": matches, "missing": missing, "accuracy": accuracy}, f, indent=2)
  
  logger.info(f"Report saved to {val_log_path}")

if __name__ == "__main__":
  main()

