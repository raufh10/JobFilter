from pydantic import BaseModel

class SkillExtraction(BaseModel):
    skills: list[str]
    tools: list[str]
    languages: list[str]

import sys
import json
from pathlib import Path

# Fix pathing for local src imports
project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))

from src.llm import LLMClient, generate_structured_response
from src.llm.schema import SkillExtraction

def main():
    # 1. Setup Paths
    input_file = project_root / "data" / "raw_jobs.json"
    output_file = project_root / "data" / "raw_skills.json"

    if not input_file.exists():
        print(f"❌ Input file not found: {input_file}")
        return

    # 2. Load Job Data
    with open(input_file, "r", encoding="utf-8") as f:
        data = json.load(f)
        jobs = data.get("jobs", [])

    # 3. Initialize LLM Client
    # In production, use: os.getenv("OPENAI_API_KEY")
    llm = LLMClient(
        api_key="your-api-key-here", 
        model="gpt-4o-mini",
        system_prompt="Extract technical skills, tools, and programming languages from the job description.",
        format_schema=SkillExtraction
    )

    extracted_results = []

    print(f"🧠 Processing {len(jobs)} jobs for skill extraction...")

    for job in jobs:
        description = job.get("description")
        job_id = job.get("id")

        if not description:
            continue

        try:
            print(f"  - Extracting skills for: {job.get('title')}...")
            
            # Generate structured response
            skills_data = generate_structured_response(llm, description)
            
            # Combine job metadata with extracted skills
            extracted_results.append({
                "job_id": job_id,
                "title": job.get("title"),
                "extracted_data": skills_data.model_dump()
            })
        except Exception as e:
            print(f"  ⚠️ Failed to process job {job_id}: {e}")

    # 4. Save Results
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(extracted_results, f, indent=2)

    print(f"✅ Extraction complete. Results saved to {output_file}")

if __name__ == "__main__":
    main()

