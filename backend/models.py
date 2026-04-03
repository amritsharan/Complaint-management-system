from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime
from enum import Enum

class UserRole(str, Enum):
    USER = "user"
    ADMIN = "admin"

class ComplaintStatus(str, Enum):
    PENDING = "Pending"
    IN_PROGRESS = "In Progress"
    RESOLVED = "Resolved"

# User Models
class UserBase(BaseModel):
    name: str
    email: str
    role: UserRole = UserRole.USER

class UserCreate(UserBase):
    password: str

class UserInDB(UserBase):
    id: Optional[str] = None
    hashed_password: str

class UserResponse(UserBase):
    id: str

# Complaint Models
class ComplaintBase(BaseModel):
    title: str
    description: str
    category: str
    file_url: Optional[str] = None

class ComplaintCreate(ComplaintBase):
    pass

class ComplaintUpdate(BaseModel):
    status: Optional[ComplaintStatus] = None
    admin_remarks: Optional[str] = None

class ComplaintInDB(ComplaintBase):
    id: Optional[str] = None
    user_id: str
    status: ComplaintStatus = ComplaintStatus.PENDING
    date_created: datetime = Field(default_factory=datetime.utcnow)
    admin_remarks: Optional[str] = ""

class ComplaintResponse(ComplaintBase):
    id: str
    user_id: str
    status: ComplaintStatus
    date_created: datetime
    admin_remarks: Optional[str] = ""
    priority_rank: Optional[int] = None
    priority_score: float = 0.0
    tfidf_score: float = 0.0
    bm25_score: float = 0.0

# Auth Models
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None
    role: Optional[str] = None
