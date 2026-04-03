# Complaint Management System

A full-stack complaint management platform with role-based access for users and administrators.

## What Is Implemented

- User registration and login with JWT authentication
- First registered account is auto-assigned as Admin
- Complaint submission by users (title, category, description, optional evidence URL)
- Admin panel to review and update complaint status and remarks
- Live updates using Server-Sent Events (SSE)
  - New complaints appear instantly in Admin view
  - Status updates reflect instantly in User dashboard
- Complaint prioritization and ranking for admin queue
  - TF-IDF score
  - BM25 score
  - Combined priority score and rank

## Tech Stack

- Backend: FastAPI, PyMongo, JWT (python-jose), Passlib
- Database: MongoDB
- Frontend: HTML, TailwindCSS, Vanilla JavaScript
- Real-time updates: SSE

## Project Structure

- backend/
  - main.py: API routes, auth, SSE, ranking logic
  - models.py: Pydantic models
  - database.py: MongoDB connection and indexes
  - auth.py: hashing and token utilities
  - requirements.txt: backend dependencies
- frontend/
  - index.html: login/register
  - dashboard.html: user dashboard
  - admin.html: admin dashboard
  - js/
    - auth.js
    - dashboard.js
    - admin.js

## How Priority Ranking Works

For each complaint, text is built from:

- title
- category
- description

Then:

1. Tokenization + basic stop-word removal
2. TF-IDF score per complaint
3. BM25 score per complaint (using top corpus terms)
4. Combined score:

priority_score = (0.55 * tfidf_score + 0.45 * bm25_score) * status_weight

Status weights:

- Pending: 1.15
- In Progress: 1.00
- Resolved: 0.65

Complaints are sorted by priority_score descending and assigned priority_rank.

## Local Setup

### Prerequisites

- Python 3.10+
- MongoDB running locally (or remote MongoDB URI)

### 1) Backend setup

From backend folder:

- python -m venv .venv
- .\.venv\Scripts\Activate.ps1
- pip install -r requirements.txt

Optional environment variables (backend/.env):

- MONGO_URI (default: mongodb://localhost:27017)
- MONGO_DB_NAME (default: complaint_management)
- SECRET_KEY
- ALGORITHM (default: HS256)
- ACCESS_TOKEN_EXPIRE_MINUTES (default: 30)

Run backend:

- uvicorn main:app --reload --host 127.0.0.1 --port 8002

### 2) Open app

- http://127.0.0.1:8002/

The backend serves frontend files directly.

## Core API Endpoints

- POST /register
- POST /token
- POST /complaints
- GET /complaints
- GET /admin/complaints
- PATCH /admin/complaints/{complaint_id}
- GET /events?token=... (SSE stream)

## Deployment Guide

### Option A: Deploy as one service (recommended first)

Deploy the backend service (FastAPI). Since backend serves frontend assets, one deployment is enough.

Typical production startup command:

- uvicorn main:app --host 0.0.0.0 --port 8000

Set production environment variables:

- MONGO_URI
- MONGO_DB_NAME
- SECRET_KEY
- ALGORITHM
- ACCESS_TOKEN_EXPIRE_MINUTES

### Option B: Container deployment

Create a Docker image for backend and expose the service port.

At minimum, configure:

- PORT binding
- MongoDB connection via MONGO_URI
- Secret key via environment variable

## Notes and Recommendations

- Current SSE endpoint uses token in query string for EventSource compatibility.
- For production hardening, prefer cookie-based auth for SSE or move to WebSocket with header-based auth.
- Add rate limiting and stricter CORS before public deployment.
- Consider logging and monitoring for complaint volume and resolution SLAs.

## Quick Validation Checklist

- Register first account -> should become Admin
- Login as Admin -> open Admin panel
- Register second account -> normal User
- User submits complaint -> appears instantly in Admin panel
- Admin updates status to Resolved -> updates instantly in User dashboard
- Admin view shows TF-IDF, BM25, Priority score, and rank

## License

Internal project for academic/product demonstration. Add your preferred license before public release.
