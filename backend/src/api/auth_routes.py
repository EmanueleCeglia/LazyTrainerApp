from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from src.database.connection import get_db
from src.database.models import UserProfile
from src.api.auth import get_password_hash, verify_password, create_access_token

router = APIRouter()

class RegisterRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    # bcrypt hashes at most 72 bytes and raises on anything longer, so cap it here.
    password: str = Field(..., min_length=6, max_length=72)

class Token(BaseModel):
    access_token: str
    token_type: str
    username: str

@router.post("/register", response_model=Token)
def register(user: RegisterRequest, db: Session = Depends(get_db)):
    username = user.username.strip()
    if not username:
        raise HTTPException(status_code=400, detail="Username cannot be blank")

    db_user = db.query(UserProfile).filter(UserProfile.username == username).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")

    hashed_password = get_password_hash(user.password)

    # Create the user with default empty values for the Questionnaire
    new_user = UserProfile(
        username=username,
        hashed_password=hashed_password,
        age=0,
        gender="Other",
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
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Incorrect username or password",
        headers={"WWW-Authenticate": "Bearer"},
    )

    user = db.query(UserProfile).filter(UserProfile.username == form_data.username.strip()).first()
    # A user row created before auth existed can have a NULL hash - treat it as no login.
    if not user or not user.hashed_password:
        raise credentials_exception
    if not verify_password(form_data.password, user.hashed_password):
        raise credentials_exception

    access_token = create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer", "username": user.username}
