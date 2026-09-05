from datetime import datetime, timedelta, timezone
from jose import jwt, JWTError
import bcrypt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from src.database.connection import get_db
from src.database.models import UserProfile
from src.config import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

def _to_bcrypt_bytes(password: str) -> bytes:
    # bcrypt refuses anything over 72 bytes. A 72-CHARACTER password can still be
    # longer than that in UTF-8, so clamp on the encoded length.
    return password.encode('utf-8')[:72]

def verify_password(plain_password, hashed_password):
    try:
        return bcrypt.checkpw(_to_bcrypt_bytes(plain_password), hashed_password.encode('utf-8'))
    except ValueError:
        # Malformed hash in the DB - treat as a failed login rather than a 500.
        return False

def get_password_hash(password):
    # bcrypt requires bytes, and we decode the resulting hash back to a string for the DB
    return bcrypt.hashpw(_to_bcrypt_bytes(password), bcrypt.gensalt()).decode('utf-8')

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
        
    user = db.query(UserProfile).filter(UserProfile.username == username).first()
    if user is None:
        raise credentials_exception
    return user
