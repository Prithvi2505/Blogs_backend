import os
from datetime import datetime, timedelta, timezone

from dotenv import load_dotenv
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session
from starlette import status

from database import get_db
from models import User


load_dotenv()
SECRET_KEY = os.getenv("JWT_SECRET_KEY")
if not SECRET_KEY:
	raise RuntimeError("JWT_SECRET_KEY is missing from the environment")

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60
bearer_scheme = HTTPBearer()
optional_bearer_scheme = HTTPBearer(auto_error=False)


def create_access_token(email: str, user_id: int) -> str:
	expires_at = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
	return jwt.encode(
		{"sub": email, "id": user_id, "exp": expires_at},
		SECRET_KEY,
		algorithm=ALGORITHM,
	)


def decode_access_token(token: str) -> dict:
	try:
		return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
	except JWTError:
		raise HTTPException(
			status_code=status.HTTP_401_UNAUTHORIZED,
			detail="Invalid or expired authentication token",
			headers={"WWW-Authenticate": "Bearer"},
		)


def get_current_user(
	credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
	db: Session = Depends(get_db),
) -> User:
	return _resolve_current_user(credentials, db)


def get_optional_current_user(
	credentials: HTTPAuthorizationCredentials | None = Depends(optional_bearer_scheme),
	db: Session = Depends(get_db),
) -> User | None:
	return _resolve_current_user(credentials, db) if credentials else None


def _resolve_current_user(credentials: HTTPAuthorizationCredentials, db: Session) -> User:
	payload = decode_access_token(credentials.credentials)
	try:
		email = payload["sub"]
		user_id = int(payload["id"])
	except (KeyError, TypeError, ValueError) as error:
		raise HTTPException(
			status_code=status.HTTP_401_UNAUTHORIZED,
			detail="Invalid authentication token",
			headers={"WWW-Authenticate": "Bearer"},
		) from error

	user = db.query(User).filter(User.id == user_id, User.email == email).first()
	if not user:
		raise HTTPException(
			status_code=status.HTTP_401_UNAUTHORIZED,
			detail="User not found",
			headers={"WWW-Authenticate": "Bearer"},
		)
	return user
