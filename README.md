# job_filter

A CLI tool to fetch and filter job listings from Indeed using [JobSpy](https://github.com/speedyapply/JobSpy).

---

## 🚀 Installation

1. Clone the repo:
```bash
git clone https://github.com/raufh10/job_filter
cd job_filter
```

2. Install dependencies:
```bash
pip install -e .
```

---

## 🖥️ Usage

```bash
job_filter create    # Create client.json config
job_filter adjust    # Edit existing client.json config
job_filter fetch     # Fetch and print jobs to terminal
```

---

## 🗂️ Project Structure

```
job_filter/
├── src/
│   └── job_filter/
│       ├── cli/
│       │   ├── __init__.py
│       │   └── commands.py
│       ├── client/
│       │   ├── __init__.py
│       │   ├── fetch.py
│       │   └── models.py
│       ├── core/
│       │   ├── __init__.py
│       │   ├── client.json
│       │   ├── config.py
│       │   └── logging.py
│       ├── __init__.py
│       └── main.py
├── .gitignore
├── pyproject.toml
└── README.md
```

---

## 🌐 Supported Job Boards

- Indeed

---

## 📦 Requirements

- Python 3.11+
- jobspy
- pydantic
- typer
