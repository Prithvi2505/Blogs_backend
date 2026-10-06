from fastapi import HTTPException, status

from models import User


def has_role(user: User, *roles: str) -> bool:
	return user.role in roles


def require_role(user: User, *roles: str) -> None:
	if not has_role(user, *roles):
		raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")