🌍 Automated Translation & PDF Report System
 
[![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)](https://fastapi.tiangolo.com/)
[![Celery](https://img.shields.io/badge/Celery-37814A?style=for-the-badge&logo=celery)](https://docs.celeryq.dev/)
[![Redis](https://img.shields.io/badge/redis-%23DD0031.svg?style=for-the-badge&logo=redis&logoColor=white)](https://redis.io/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-316192?style=for-the-badge&logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![Typst](https://img.shields.io/badge/Typst-239120?style=for-the-badge)](https://typst.app/docs/)
A professional microservice designed for high-performance text translation and automated PDF report generation. This system uses a **distributed asynchronous architecture** to handle heavy workloads without blocking the user experience.
 
---
 
## 🏗️ System Architecture
 
The system follows a **Producer-Consumer** pattern to ensure scalability:
 
1. **FastAPI (Producer):** Receives requests, validates data, and initializes a database record with a `pending` status. It then dispatches the task to the message broker.
2. **Redis (Message Broker):** Acts as the intermediary buffer, holding tasks in a queue.
3. **Celery Worker (Consumer):** Independently processes the translation via the Google Translate engine and triggers the **Typst** document generator.
4. **Typst Engine:** Renders high-fidelity PDFs directly in memory (RAM) for maximum speed.
 
---
 
## 📂 Project Structure
 
```text
BE-TRANSLATE-APLICATION/
├── alembic/                          # Database migrations
├── app/
│   ├── api/
│   │   └── endpoints/
│   │       └── translations.py       # REST API routes (GET, POST, PDF)
│   ├── db/
│   │   ├── base_class.py             # SQLAlchemy Base class
│   │   └── session.py                # Session & Engine management
│   ├── models/
│   │   └── translation.py            # SQLAlchemy Database Models
│   ├── schemas/
│   │   └── translation.py            # Pydantic validation schemas
│   ├── services/
│   │   └── pdf_service.py            # Typst PDF generation service
│   ├── templates/
│   │   ├── lang.toml                 # Multi-language dictionary (i18n)
│   │   └── template.typ              # Typst layout design
│   └── worker/
│       ├── main.py                   # Celery app configuration
│       └── tasks.py                  # Async translation & PDF tasks
├── main.py                           # FastAPI entry point
├── docker-compose.yml                # Infrastructure (Postgres + Redis)
└── requirements.txt                  # Project dependencies
```
 
---
 
## 🔗 API Endpoints
 
| Method | Endpoint                  | Description                                               |
|--------|---------------------------|-----------------------------------------------------------|
| POST   | `/translations`           | Primary entry point. Enqueues a new translation task.     |
| GET    | `/translations`           | Returns the full translation history.                     |
| GET    | `/translations/{id}`      | Checks the current status (`pending`, `completed`, `error`). |
| GET    | `/translations/{id}/pdf`  | Smart download. Returns the PDF stream or a specific error. |
 
---
 
## 🚦 HTTP Status Codes
 
| Code | Meaning |
|------|---------|
| **200 OK** | PDF is ready and starts downloading. |
| **202 Accepted** | Translation is still in progress — the frontend should poll again. |
| **400 Bad Request** | Translation failed (e.g., text too long). |
 
---
 
## 🛠️ Tech Stack
 
| Layer | Technology |
|-------|-----------|
| Backend | FastAPI (Python 3.10+) |
| Database | PostgreSQL & SQLAlchemy ORM |
| Background Tasks | Celery & Redis |
| Document Engine | Typst (in-memory generation) |
| Translation | deep-translator (Google Translate) |
| Internationalization | Linguify (`lang.toml`) |
 
---
 
## ⚙️ Installation & Setup
 
### 1. Infrastructure
 
Spin up the database and message broker using Docker:
 
```bash
docker-compose up -d
```
 
### 2. Environment Setup
 
Create a virtual environment and install the required Python packages:
 
```bash
python -m venv venv
source venv/bin/activate       # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```
 
### 3. Running the System
 
Open two separate terminals and run the following commands:
 
**Terminal 1 — FastAPI Server:**
 
```bash
uvicorn app.main:app --reload --port 8000
```
 
**Terminal 2 — Celery Worker:**
 
```bash
# Use -P solo on Windows environments
celery -A app.worker.main.celery_app worker --loglevel=info -P solo
```