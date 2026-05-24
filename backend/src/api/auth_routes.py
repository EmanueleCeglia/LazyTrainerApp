from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional

from src.database.connection import get_db
from src.database.models import UserProfile
from src.api.auth import get_password_hash, verify_password, create_access_token

router = APIRouter()

class RegisterRequest(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str
    username: str

@router.post("/register")
def register(user: RegisterRequest, db: Session = Depends(get_db)):
    db_user = db.query(UserProfile).filter(UserProfile.username == user.username).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")
        
    hashed_password = get_password_hash(user.password)
    
    # Create the user with default empty values for the Questionnaire
    new_user = UserProfile(
        username=user.username,
        hashed_password=hashed_password,
        age=0,
        weight=0,
        height=0,
        location="Gym",
        experience_level="Beginner",
        equipment_available=[],
        goals=[]
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    # Automatically log them in by returning a token
    access_token = create_access_token(data={"sub": new_user.username})
    return {"access_token": access_token, "token_type": "bearer", "username": new_user.username}


@router.post("/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(UserProfile).filter(UserProfile.username == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    access_token = create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer", "username": user.username}
