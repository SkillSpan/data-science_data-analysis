# SkillBridge Data Science and Analytics

Data science and analytics service for the SkillBridge platform.

## Current Features

- FastAPI application
- Health-check endpoint
- Automatic API documentation

## Local Setup

Create the virtual environment:

```bash
python -m venv .venv
```

Activate it on Windows:

```bash
.venv\Scripts\activate
```

Install dependencies:

```bash
python -m pip install -r requirements.txt
```

Run the service:

```bash
uvicorn app.main:app --reload --host 127.0.0.1 --port 8001
```

## API URLs

- Health: `http://127.0.0.1:8001/health`
- Documentation: `http://127.0.0.1:8001/docs`