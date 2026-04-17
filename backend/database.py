from pymongo import MongoClient
from pymongo.errors import ServerSelectionTimeoutError
import os

# MongoDB connection URI
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
DB_NAME = os.getenv("MONGO_DB_NAME", "complaint_management")

print(f"Connecting to MongoDB... DB={DB_NAME}", flush=True)
print(f"MONGO_URI starts with: {MONGO_URI[:30]}...", flush=True)

client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=10000)
db = client[DB_NAME]

def init_db_sync():
    try:
        # Test ping first
        client.admin.command("ping")
        print("MongoDB ping successful.", flush=True)
    except ServerSelectionTimeoutError as e:
        print(f"[CRITICAL] MongoDB connection FAILED: {e}", flush=True)
        raise RuntimeError(f"Cannot connect to MongoDB: {e}")
    except Exception as e:
        print(f"[CRITICAL] Unexpected MongoDB error: {e}", flush=True)
        raise

    # Create indexes
    try:
        db.users.create_index("email", unique=True)
        db.complaints.create_index("title")
        db.complaints.create_index("user_id")
        db.complaints.create_index("status")
        print("MongoDB indexes created successfully.", flush=True)
    except Exception as e:
        print(f"Warning: Index creation issue: {e}", flush=True)

def get_db_sync():
    return db
