"""
DataService (saa-core-data-v2)
Purpose: Sole owner of PostgreSQL database. All other services access data via REST.
Protocol: AGENT3_HANDSHAKE v30
"""
import os
import time
import uuid
from datetime import datetime
from typing import Optional, List
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Depends, Header, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
from sqlalchemy import create_engine, Column, String, Integer, Boolean, DateTime, JSON, ForeignKey, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session

# Configuration
DATABASE_URL = os.environ.get("DATABASE_URL", "")
API_KEY = os.environ.get("DATASERVICE_API_KEY", "")
PORT = int(os.environ.get("PORT", 5000))
START_TIME = time.time()
VERSION = "2.0.0"

# Database setup
Base = declarative_base()
engine = create_engine(DATABASE_URL) if DATABASE_URL else None
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine) if engine else None


# Models
class User(Base):
    __tablename__ = "users_v2"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String, unique=True, nullable=False)
    is_ferpa_covered = Column(Boolean, default=False)
    do_not_sell = Column(Boolean, default=False)
    age = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class Provider(Base):
    __tablename__ = "providers_v2"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    org = Column(String, nullable=False)
    contact = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class Scholarship(Base):
    __tablename__ = "scholarships_v2"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(String, nullable=False)
    amount = Column(Integer, nullable=False)
    deadline = Column(DateTime, nullable=True)
    tags = Column(JSON, default=list)
    description = Column(Text, nullable=True)


class Purchase(Base):
    __tablename__ = "purchases_v2"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    student_id = Column(String, ForeignKey("users_v2.id"), nullable=False)
    credits = Column(Integer, nullable=False)
    status = Column(String, default="created")
    created_at = Column(DateTime, default=datetime.utcnow)


# Pydantic schemas
class StudentSignupRequest(BaseModel):
    email: EmailStr
    age: Optional[int] = None


class StudentSignupResponse(BaseModel):
    student_id: str
    email: str
    is_ferpa_covered: bool
    do_not_sell: bool
    created_at: datetime


class ProviderOnboardRequest(BaseModel):
    org: str
    contact: str


class ProviderOnboardResponse(BaseModel):
    provider_id: str
    org: str
    contact: str
    created_at: datetime


class ScholarshipMatch(BaseModel):
    id: str
    title: str
    amount: int
    deadline: Optional[datetime]
    tags: List[str]


class CreditsPurchaseRequest(BaseModel):
    student_id: str
    credits: int


class CreditsPurchaseResponse(BaseModel):
    id: str
    student_id: str
    credits: int
    status: str


class HealthResponse(BaseModel):
    service: str
    version: str
    uptime_s: float
    status: str


# Dependencies
def get_db():
    if SessionLocal is None:
        raise HTTPException(status_code=503, detail="Database not configured")
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


async def verify_api_key(x_api_key: str = Header(None)):
    if not API_KEY:
        return True
    if x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return True


# Lifespan
@asynccontextmanager
async def lifespan(app: FastAPI):
    if engine:
        Base.metadata.create_all(bind=engine)
    yield


# App
app = FastAPI(
    title="DataService (saa-core-data-v2)",
    version=VERSION,
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Endpoints
@app.get("/health", response_model=HealthResponse)
async def health():
    return HealthResponse(
        service="saa-core-data-v2",
        version=VERSION,
        uptime_s=round(time.time() - START_TIME, 2),
        status="healthy"
    )


@app.post("/student/signup", response_model=StudentSignupResponse, dependencies=[Depends(verify_api_key)])
async def student_signup(request: StudentSignupRequest, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == request.email).first()
    if existing:
        raise HTTPException(status_code=409, detail="Email already registered")
    
    do_not_sell = request.age is not None and request.age < 18
    
    user = User(
        email=request.email,
        is_ferpa_covered=False,
        do_not_sell=do_not_sell,
        age=request.age
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    
    return StudentSignupResponse(
        student_id=user.id,
        email=user.email,
        is_ferpa_covered=user.is_ferpa_covered,
        do_not_sell=user.do_not_sell,
        created_at=user.created_at
    )


@app.post("/provider/onboard", response_model=ProviderOnboardResponse, dependencies=[Depends(verify_api_key)])
async def provider_onboard(request: ProviderOnboardRequest, db: Session = Depends(get_db)):
    provider = Provider(org=request.org, contact=request.contact)
    db.add(provider)
    db.commit()
    db.refresh(provider)
    
    return ProviderOnboardResponse(
        provider_id=provider.id,
        org=provider.org,
        contact=provider.contact,
        created_at=provider.created_at
    )


@app.get("/scholarships/match", response_model=List[ScholarshipMatch], dependencies=[Depends(verify_api_key)])
async def scholarships_match(query: str = "", limit: int = 20, db: Session = Depends(get_db)):
    q = db.query(Scholarship)
    if query:
        q = q.filter(Scholarship.title.ilike(f"%{query}%"))
    results = q.limit(limit).all()
    
    return [
        ScholarshipMatch(
            id=s.id,
            title=s.title,
            amount=s.amount,
            deadline=s.deadline,
            tags=s.tags or []
        )
        for s in results
    ]


@app.post("/credits/purchase", response_model=CreditsPurchaseResponse, dependencies=[Depends(verify_api_key)])
async def credits_purchase(request: CreditsPurchaseRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == request.student_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Student not found")
    
    purchase = Purchase(
        student_id=request.student_id,
        credits=request.credits,
        status="created"
    )
    db.add(purchase)
    db.commit()
    db.refresh(purchase)
    
    return CreditsPurchaseResponse(
        id=purchase.id,
        student_id=purchase.student_id,
        credits=purchase.credits,
        status=purchase.status
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=PORT, reload=False)
