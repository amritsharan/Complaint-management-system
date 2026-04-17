import os
import asyncio
import json
import math
import re
from collections import Counter
from dotenv import load_dotenv

# Load .env file (works locally and is safely ignored on Render where env vars are set directly)
load_dotenv()

from fastapi import FastAPI, Depends, HTTPException, status, Body
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
from typing import List
from bson import ObjectId
from bson.errors import InvalidId
from fastapi.responses import StreamingResponse

from models import (
    UserCreate, UserResponse, Token, UserRole,
    ComplaintCreate, ComplaintResponse, ComplaintUpdate, ComplaintStatus
)
from database import get_db_sync, init_db_sync
from auth import get_password_hash, verify_password, create_access_token, ACCESS_TOKEN_EXPIRE_MINUTES, SECRET_KEY, ALGORITHM
from jose import JWTError, jwt
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

app = FastAPI(title="Complaint Management System API")

# Startup Event: Initialize Database
@app.on_event("startup")
async def startup():
    print("Startup: initializing database", flush=True)
    try:
        init_db_sync()
        print("Database initialized", flush=True)
    except Exception as e:
        print(f"Database initialization failed: {e}", flush=True)
        import traceback
        traceback.print_exc()

# Static Files & Frontend Serving
frontend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "frontend"))
app.mount("/js", StaticFiles(directory=os.path.join(frontend_path, "js")), name="js")

@app.get("/")
async def read_index():
    from fastapi.responses import FileResponse
    return FileResponse(os.path.join(frontend_path, "index.html"))

@app.get("/dashboard.html")
async def read_dashboard():
    from fastapi.responses import FileResponse
    return FileResponse(os.path.join(frontend_path, "dashboard.html"))

@app.get("/admin.html")
async def read_admin():
    from fastapi.responses import FileResponse
    return FileResponse(os.path.join(frontend_path, "admin.html"))

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
event_subscribers = []
TOKEN_PATTERN = re.compile(r"[a-z0-9]+")
STOP_WORDS = {
    "a", "an", "and", "are", "as", "at", "be", "because", "been", "but",
    "by", "can", "could", "did", "do", "does", "for", "from", "had", "has",
    "have", "having", "he", "her", "hers", "him", "his", "i", "if", "in",
    "is", "it", "its", "me", "my", "of", "on", "or", "our", "she", "so",
    "that", "the", "their", "them", "there", "they", "this", "to", "was",
    "we", "were", "what", "when", "where", "which", "who", "why", "will",
    "with", "you", "your"
}
STATUS_PRIORITY_WEIGHT = {
    ComplaintStatus.PENDING.value: 1.15,
    ComplaintStatus.IN_PROGRESS.value: 1.0,
    ComplaintStatus.RESOLVED.value: 0.65,
}


def get_user_from_token(token: str) -> dict:
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    email: str = payload.get("sub")
    if email is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    db = get_db_sync()
    user = db.users.find_one({"email": email})
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user["id"] = str(user.get("_id"))
    user["role"] = UserRole(user.get("role"))
    return user


def publish_complaint_event(event_type: str, complaint: dict):
    payload = {
        "type": event_type,
        "complaint_id": str(complaint["_id"]),
        "user_id": str(complaint["user_id"]),
        "status": complaint["status"],
    }

    for subscriber in list(event_subscribers):
        if subscriber["role"] == UserRole.ADMIN or subscriber["user_id"] == payload["user_id"]:
            try:
                subscriber["queue"].put_nowait(payload)
            except asyncio.QueueFull:
                pass


def tokenize_complaint_text(document: dict) -> list[str]:
    text = " ".join(
        str(document.get(field, "")) for field in ("title", "category", "description")
    )
    return [token for token in TOKEN_PATTERN.findall(text.lower()) if len(token) > 2 and token not in STOP_WORDS]


def score_complaints(documents: list[dict]) -> list[dict]:
    if not documents:
        return []

    tokenized_documents: list[list[str]] = []
    document_frequency = Counter()
    document_lengths: list[int] = []

    for document in documents:
        tokens = tokenize_complaint_text(document)
        tokenized_documents.append(tokens)
        document_lengths.append(max(len(tokens), 1))
        document_frequency.update(set(tokens))

    total_documents = len(documents)
    average_document_length = sum(document_lengths) / total_documents if total_documents else 1.0
    idf_values = {
        term: math.log((total_documents - frequency + 0.5) / (frequency + 0.5) + 1.0)
        for term, frequency in document_frequency.items()
    }

    corpus_terms = sorted(
        document_frequency.keys(),
        key=lambda term: (idf_values.get(term, 0.0) * document_frequency[term], document_frequency[term]),
        reverse=True,
    )[:8]

    tfidf_raw_scores: list[float] = []
    bm25_raw_scores: list[float] = []
    combined_raw_scores: list[float] = []
    k1 = 1.5
    b = 0.75

    for document, tokens in zip(documents, tokenized_documents):
        term_counts = Counter(tokens)
        document_length = max(len(tokens), 1)

        tfidf_raw = 0.0
        for term, frequency in term_counts.items():
            tfidf_raw += (frequency / document_length) * idf_values.get(term, 0.0)

        bm25_raw = 0.0
        for term in corpus_terms:
            frequency = term_counts.get(term, 0)
            if not frequency:
                continue
            term_idf = idf_values.get(term, 0.0)
            denominator = frequency + k1 * (1 - b + b * document_length / average_document_length)
            bm25_raw += term_idf * (frequency * (k1 + 1)) / denominator

        status_weight = STATUS_PRIORITY_WEIGHT.get(document.get("status"), 1.0)
        combined_raw = (0.55 * tfidf_raw + 0.45 * bm25_raw) * status_weight

        tfidf_raw_scores.append(tfidf_raw)
        bm25_raw_scores.append(bm25_raw)
        combined_raw_scores.append(combined_raw)

    max_tfidf = max(tfidf_raw_scores) if tfidf_raw_scores else 0.0
    max_bm25 = max(bm25_raw_scores) if bm25_raw_scores else 0.0
    max_combined = max(combined_raw_scores) if combined_raw_scores else 0.0

    scored_documents = []
    for index, document in enumerate(documents):
        annotated_document = dict(document)
        tfidf_score = (tfidf_raw_scores[index] / max_tfidf * 100.0) if max_tfidf else 0.0
        bm25_score = (bm25_raw_scores[index] / max_bm25 * 100.0) if max_bm25 else 0.0
        combined_score = (combined_raw_scores[index] / max_combined * 100.0) if max_combined else 0.0

        annotated_document["tfidf_score"] = round(tfidf_score, 2)
        annotated_document["bm25_score"] = round(bm25_score, 2)
        annotated_document["priority_score"] = round(combined_score, 2)
        scored_documents.append(annotated_document)

    scored_documents.sort(
        key=lambda document: (
            document.get("priority_score", 0.0),
            document.get("date_created"),
        ),
        reverse=True,
    )

    for rank, document in enumerate(scored_documents, start=1):
        document["priority_rank"] = rank

    return scored_documents


def serialize_complaint(document: dict) -> dict:
    return {
        "id": str(document["_id"]),
        "user_id": str(document["user_id"]),
        "title": document["title"],
        "category": document["category"],
        "description": document["description"],
        "file_url": document.get("file_url"),
        "status": document["status"],
        "date_created": document["date_created"],
        "admin_remarks": document.get("admin_remarks", ""),
        "priority_rank": document.get("priority_rank"),
        "priority_score": document.get("priority_score", 0.0),
        "tfidf_score": document.get("tfidf_score", 0.0),
        "bm25_score": document.get("bm25_score", 0.0),
    }

async def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        return get_user_from_token(token)
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

async def get_admin_user(current_user: dict = Depends(get_current_user)):
    if current_user["role"] != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    return current_user


@app.get("/events")
async def stream_events(token: str):
    try:
        current_user = get_user_from_token(token)
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
        )

    queue: asyncio.Queue = asyncio.Queue(maxsize=100)
    subscriber = {
        "queue": queue,
        "user_id": current_user["id"],
        "role": current_user["role"],
    }
    event_subscribers.append(subscriber)

    async def event_generator():
        try:
            yield ": connected\n\n"
            while True:
                try:
                    event = await asyncio.wait_for(queue.get(), timeout=25)
                    yield f"data: {json.dumps(event)}\n\n"
                except asyncio.TimeoutError:
                    yield ": keepalive\n\n"
        finally:
            if subscriber in event_subscribers:
                event_subscribers.remove(subscriber)

    return StreamingResponse(event_generator(), media_type="text/event-stream")

# Auth Routes
@app.post("/register", response_model=UserResponse)
async def register(user: UserCreate):
    print(f"Registration attempt for: {user.email}", flush=True)
    try:
        db = get_db_sync()
        # Check if user exists
        if db.users.find_one({"email": user.email}):
            print("Email already exists", flush=True)
            raise HTTPException(status_code=400, detail="Email already registered")

        # Determine role (First user is ADMIN)
        user_count = db.users.count_documents({})
        role = UserRole.ADMIN if user_count == 0 else UserRole.USER

        hashed_password = get_password_hash(user.password)

        user_doc = {
            "name": user.name,
            "email": user.email,
            "hashed_password": hashed_password,
            "role": role.value
        }
        result = db.users.insert_one(user_doc)
        print(f"User created with ID: {result.inserted_id}", flush=True)
        return {
            "id": str(result.inserted_id),
            "name": user.name,
            "email": user.email,
            "role": role.value
        }
    except Exception as e:
        print(f"Error during registration: {e}", flush=True)
        import traceback
        traceback.print_exc()
        raise e

@app.post("/token", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    print(f"Login attempt for: {form_data.username}", flush=True)
    try:
        db = get_db_sync()
        user = db.users.find_one({"email": form_data.username})
        if not user:
            print("User not found", flush=True)
            raise HTTPException(status_code=401, detail="Incorrect email or password")

        if not verify_password(form_data.password, user["hashed_password"]):
            print("Password mismatch", flush=True)
            raise HTTPException(status_code=401, detail="Incorrect email or password")

        access_token = create_access_token(data={"sub": user["email"], "role": user["role"]})
        print("Login successful", flush=True)
        return {"access_token": access_token, "token_type": "bearer"}
    except Exception as e:
        print(f"Error during login: {e}", flush=True)
        import traceback
        traceback.print_exc()
        raise e

# Complaint Routes
@app.post("/complaints", response_model=ComplaintResponse)
async def create_complaint(complaint: ComplaintCreate, current_user: dict = Depends(get_current_user)):
    db = get_db_sync()
    date_now = datetime.utcnow()
    complaint_doc = {
        "user_id": current_user["id"],
        "title": complaint.title,
        "category": complaint.category,
        "description": complaint.description,
        "file_url": complaint.file_url,
        "status": ComplaintStatus.PENDING.value,
        "date_created": date_now,
        "admin_remarks": ""
    }
    result = db.complaints.insert_one(complaint_doc)
    complaint_doc["_id"] = result.inserted_id
    publish_complaint_event("complaint_created", complaint_doc)
    return serialize_complaint(complaint_doc)

@app.get("/complaints", response_model=List[ComplaintResponse])
async def get_my_complaints(current_user: dict = Depends(get_current_user)):
    db = get_db_sync()
    complaints = db.complaints.find({"user_id": current_user["id"]}).sort("date_created", -1)
    return [serialize_complaint(document) for document in complaints]

# Admin Routes
@app.get("/admin/complaints", response_model=List[ComplaintResponse])
async def get_all_complaints(admin: dict = Depends(get_admin_user)):
    db = get_db_sync()
    complaints = list(db.complaints.find())
    scored_complaints = score_complaints(complaints)
    return [serialize_complaint(document) for document in scored_complaints]     

@app.patch("/admin/complaints/{complaint_id}", response_model=ComplaintResponse)
async def update_complaint_status(
    complaint_id: str, 
    update: ComplaintUpdate, 
    admin: dict = Depends(get_admin_user)
):
    try:
        complaint_object_id = ObjectId(complaint_id)
    except (InvalidId, TypeError):
        raise HTTPException(status_code=400, detail="Invalid complaint id")

    db = get_db_sync()
    existing = db.complaints.find_one({"_id": complaint_object_id})
    if not existing:
        raise HTTPException(status_code=404, detail="Complaint not found")

    updates = {}
    if update.status is not None:
        updates["status"] = update.status.value
    if update.admin_remarks is not None:
        updates["admin_remarks"] = update.admin_remarks

    if updates:
        db.complaints.update_one({"_id": complaint_object_id}, {"$set": updates})

    updated = db.complaints.find_one({"_id": complaint_object_id})
    publish_complaint_event("complaint_updated", updated)
    return serialize_complaint(updated)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002, reload=False)
