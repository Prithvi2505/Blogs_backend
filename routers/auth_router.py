from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from starlette import status

from models import User
from services.auth_service import login_user, register_user, update_user_profile
from database import get_db
from schemas.auth_schema import UserCreate, UserLogin
from schemas.user_schema import UserProfile, UserProfileUpdate
from utils.auth_utils import get_current_user


router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", status_code=status.HTTP_201_CREATED)
def register(user_data: UserCreate, db: Session = Depends(get_db)):
	return register_user(user_data, db)


@router.post("/login")
def login(credentials: UserLogin, db: Session = Depends(get_db)):
	return login_user(credentials, db)


@router.get("/me", response_model=UserProfile)
def get_profile(current_user: User = Depends(get_current_user)):
	return current_user


@router.patch("/me", response_model=UserProfile)
def update_profile(
	profile_data: UserProfileUpdate,
	current_user: User = Depends(get_current_user),
	db: Session = Depends(get_db),
):
	return update_user_profile(current_user, profile_data, db)
