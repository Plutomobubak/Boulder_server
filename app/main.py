import uuid
from typing import Optional, List
from fastapi import FastAPI, File, UploadFile, Depends, HTTPException, status, Body, Form, Query, Request
from fastapi.staticfiles import StaticFiles
from fastapi_proxiedheadersmiddleware import ProxiedHeadersMiddleware
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_
from fastapi.security import OAuth2PasswordRequestForm
import auth
import schemas
import shutil
import os
import models
import json
import schemas
from models import Boulder, User
from schemas import *
from db import engine, Base
from datetime import datetime

from util import get_db
app = FastAPI()
app.add_middleware(ProxiedHeadersMiddleware)

@app.on_event("startup")
def create_tables():
    Base.metadata.create_all(bind=engine)


UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

app.mount("/images", StaticFiles(directory="uploads"), name="images")

@app.post("/publish", response_model=BoulderResponse)
async def publish(
    name: str = Form(...),
    grade: int = Form(...),
    location: str = Form(...),
    comment: str = Form(...),
    points: str = Form(...),  # 🆕 this will be JSON stringified list from client
    timestamp: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(auth.get_current_user),
):
    # Generate unique filename
    ext = os.path.splitext(file.filename)[1]
    random_filename = f"{uuid.uuid4().hex}{ext}"
    filepath = os.path.join(UPLOAD_DIR, random_filename)

    # Save image
    with open(filepath, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # 🧠 Parse points JSON
    try:
        parsed_points = json.loads(points)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON in points")
    try:
        parsed_timestamp = datetime.fromisoformat(timestamp)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid timestamp format. Use ISO 8601.")
    # Create boulder object
    new_boulder = Boulder(
        name=name,
        grade=grade,
        location=location,
        comment=comment,
        image_path=random_filename,
        points=parsed_points,  # ✅ store parsed points
        author_id=current_user.id,
        created_at=parsed_timestamp,
    )

    db.add(new_boulder)
    db.commit()
    db.refresh(new_boulder)

    return new_boulder


@app.get("/search", response_model=List[BoulderResponse])
def search_boulders(
    request: Request,
    name: Optional[str] = Query(None),
    location: Optional[str] = Query(None),
    min_grade: Optional[int] = Query(None),
    max_grade: Optional[int] = Query(None),
    username: Optional[str] = Query(None),
    timestamp: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    query = db.query(Boulder).join(User)

    if name:
        query = query.filter(Boulder.name.ilike(f"%{name}%"))
    if location:
        query = query.filter(Boulder.location.ilike(f"%{location}%"))

    if min_grade is not None:
        query = query.filter(Boulder.grade >= min_grade)
    if max_grade is not None:
        query = query.filter(Boulder.grade <= max_grade)

    if username:
        query = query.filter(User.username.ilike(f"%{username}%"))

    if timestamp:
        try:
            parsed_timestamp = datetime.fromisoformat(timestamp)
            query = query.filter(Boulder.timestamp >= parsed_timestamp)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid timestamp format. Use ISO 8601.")

    results = query.all()

    base_url = str(request.base_url)
    return [
        {
            "id": b.id,
            "name": b.name,
            "grade": b.grade,
            "location": b.location,
            "comment": b.comment,
            "image_path": f"{base_url}images/{b.image_path}",
            "points": b.points,
            "author": b.author,
            "timestamp": b.timestamp,
        }
        for b in results
    ]

@app.post("/register", response_model=UserResponse)
def register(user: UserCreate, db: Session = Depends(get_db)):
    db_user = auth.get_user(db, user.username)
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")

    hashed_password = auth.get_password_hash(user.password)
    new_user = User(username=user.username, hashed_password=hashed_password)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@app.post("/token", response_model=RefreshTokenResponse)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = auth.authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    access_token = auth.create_access_token(data={"sub": user.username})
    refresh_token = auth.create_refresh_token(data={"sub": user.username})
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }

@app.post("/refresh", response_model=RefreshTokenResponse)
def refresh_token(refresh_token: str = Body(...), db: Session = Depends(get_db)):
    username = auth.verify_refresh_token(refresh_token)
    if not username:
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    # Optionally, verify user still exists and is active
    user = auth.get_user(db, username)
    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    # Issue new tokens (rotation)
    new_access_token = auth.create_access_token(data={"sub": username})
    new_refresh_token = auth.create_refresh_token(data={"sub": username})

    # TODO: Invalidate the old refresh token if storing them (optional, requires DB)

    return {
        "access_token": new_access_token,
        "refresh_token": new_refresh_token,
        "token_type": "bearer"
    }
