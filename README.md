# JobFilter

A CLI tool to fetch, score, and filter job listings using **JobSpy** and **LLM-driven rubric analysis**.

---

## 🚀 Installation

1. **Clone the repo**:

```bash
git clone https://github.com/raufh10/job_filter
cd job_filter
```

2. **Setup Environment**:

```bash
# Recommendation: Use a virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install in editable mode with dev tools
pip install -e ".[dev]"
```

3. **Configure Environment Variables**:

Create a `.env` file in the root (managed via `src/common/settings.py`):

```env
OPENAI_API_KEY=your_sk_key_here
```

---

## 🖥️ Usage

The tool is organized into three main pillars: **Resume**, **Roles**, and **Scoring**.

### 1. Resume Management

Store your CV as plain text for the LLM to analyze.

```bash
# Overwrite your resume text
python3 main.py resume-set "I am a Data Engineer with experience in Python and AWS..."

# View current resume
python3 main.py resume-show
```

### 2. Role Configuration

Create specific search profiles with customized JobSpy parameters.

```bash
python3 main.py role-add   # Interactive role setup
python3 main.py role-list  # List configured roles
```

### 3. Fetch & Score

Scrape jobs and score them against your resume using an AI recruiter rubric.

```bash
# Fetch and filter (Min score 70%)
python3 main.py fetch "Data Analyst" --min-score 70
```

---

## 🗂️ Monorepo Structure

```text
job_filter/
│
├── src/
│   ├── common/             # Global settings & config
│   ├── engine/             # Scoring rubrics & prompts
│   ├── jobspy/             # Scraper wrapper & models
│   └── llm/                # Structured LLM response logic
│
├── main.py                 # Primary CLI entry point
├── pyproject.toml          # PEP 621 configuration
└── README.md
```

---

## ⚖️ Scoring Rubric

The tool uses a strictly defined LLM rubric:

| Score | Match Level | Description |
|-------|-------------|-------------|
| 90–100 | Perfect | Core tech + Experience aligned |
| 70–89 | Strong | Most core tech present |
| 50–69 | Fair | Foundation present, niche gaps |
| <50 | Poor | Significant gaps |

---

## 📦 Requirements

- **Python 3.11+**
- **JobSpy**: Jobs scraping
- **Pydantic v2**: Data validation & Settings
- **Typer & Rich**: CLI UI
- **HTTPX**: LLM inference (rubric-based scoring)
