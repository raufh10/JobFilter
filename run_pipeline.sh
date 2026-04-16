#!/bin/bash

# Exit immediately if a command exits with a non-zero status
set -e

echo "🚀 Starting Job Filter Pipeline..."

echo "--- Step 1: Collecting Raw Data ---"
python3 scripts/01_collect_raw_data.py

echo "--- Step 2: Extracting Raw Skills ---"
python3 scripts/02_collect_raw_skills.py

echo "--- Step 3: Refining Skills (Circular Loop) ---"
python3 scripts/03_collect_skills.py

echo "✅ Pipeline complete! Results saved in data/ folder."
