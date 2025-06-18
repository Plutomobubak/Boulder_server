from pydantic import BaseModel
from typing import Optional, List, Dict, Any

class UserBase(BaseModel):
    username: str

class UserCreate(UserBase):
    password: str

class UserResponse(UserBase):
    id: int
    username: str

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

class RefreshTokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class BoulderBase(BaseModel):
    name: str
    grade: int
    location: str
    comment: str
    image_path: str
    author: UserResponse
    points: Optional[List[Dict[str, Any]]] = None

class BoulderCreate(BoulderBase):
    pass

class BoulderResponse(BoulderBase):
    id: int

    class Config:
        from_attributes = True
