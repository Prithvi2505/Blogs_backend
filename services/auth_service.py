from fastapi import HTTPException
from sqlalchemy.orm import Session
from starlette import status

from models import User
from schemas.auth_schema import UserCreate, UserLogin
from schemas.user_schema import UserProfileUpdate
from utils.auth_utils import create_access_token
from utils.hashing import Hasher


def register_user(user_data: UserCreate, db: Session):
	existing_user = db.query(User).filter(User.email == user_data.email).first()
	if existing_user:
		raise HTTPException(
			status_code=status.HTTP_409_CONFLICT,
			detail="A user with this email already exists",
		)

	user = User(
		name=user_data.name,
		email=user_data.email,
		password=Hasher.get_password_hash(user_data.password),
		role=user_data.role,
	)
	db.add(user)
	db.commit()
	db.refresh(user)

	return {"id": user.id, "name": user.name, "email": user.email, "role": user.role}


def login_user(credentials: UserLogin, db: Session):
	user = db.query(User).filter(User.email == credentials.email).first()
	if not user or not Hasher.verify_password(credentials.password, user.password):
		raise HTTPException(
			status_code=status.HTTP_401_UNAUTHORIZED,
			detail="Invalid email or password",
			headers={"WWW-Authenticate": "Bearer"},
		)

	return {
		"access_token": create_access_token(user.email, user.id),
		"token_type": "bearer",
		"user": {
			"id": user.id,
			"name": user.name,
			"email": user.email,
			"bio": user.bio,
			"role": user.role,
		},
	}


def update_user_profile(user: User, profile_data: UserProfileUpdate, db: Session):
	user.name = profile_data.name
	user.bio = profile_data.bio
	db.commit()
	db.refresh(user)
	return user