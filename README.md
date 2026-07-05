# SkillSwap API

Flask REST API for the Community Skill-Swap platform.

## Setup

1. Create a MySQL database:
   ```sql
   CREATE DATABASE skillswap CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
   ```

2. Copy environment file and configure:
   ```bash
   cp .env.example .env
   ```

3. Create virtual environment and install dependencies:
   ```bash
   python -m venv .venv
   .venv\Scripts\activate   # Windows
   pip install -r requirements.txt
   ```

4. Run the API:
   ```bash
   python run.py
   ```

5. Seed demo data:
   ```bash
   python seed.py
   ```

## Demo Accounts

| Role   | Email                  | Password    |
|--------|------------------------|-------------|
| Admin  | admin@skillswap.test   | Admin123    |
| Alice  | alice@skillswap.test   | ChangeMe123 |
| Bob    | bob@skillswap.test     | ChangeMe123 |

## Production (Railway)

Set environment variables: `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_NAME`, `JWT_SECRET_KEY`, `FLASK_DEBUG=False`

Start command: `gunicorn run:app --bind 0.0.0.0:$PORT`
