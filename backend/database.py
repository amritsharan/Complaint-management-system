from pymongo import MongoClient
import os

# MongoDB connection URI (update as needed)
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
DB_NAME = os.getenv("MONGO_DB_NAME", "complaint_management")

client = MongoClient(MONGO_URI)
db = client[DB_NAME]

def init_db_sync():
    # Ensure collections exist, optionally create indexes
    db.users.create_index("email", unique=True)
    db.complaints.create_index("title")
    db.complaints.create_index("user_id")
    db.complaints.create_index("status")
    # Optionally, insert initial data or check connection
    try:
        db.command("ping")
        print("MongoDB connection successful.")
    except Exception as e:
        print(f"MongoDB connection failed: {e}")

def get_db_sync():
    return db
