
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.types import JSON
from db import Base
from datetime import datetime

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)

    boulders = relationship("Boulder", back_populates="author")  # One-to-many

class Boulder(Base):
    __tablename__ = 'boulders'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    grade = Column(Integer)
    location = Column(String)
    comment = Column(String)
    image_path = Column(String)

    # You can store points as JSON if your DB supports it
    points = Column(JSON, nullable=True)  

    created_at = Column(DateTime, default=datetime.utcnow)

    author_id = Column(Integer, ForeignKey("users.id"))
    author = relationship("User", back_populates="boulders")
