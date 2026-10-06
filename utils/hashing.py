from passlib.context import CryptContext


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class Hasher:
	@staticmethod
	def get_password_hash(password: str) -> str:
		return pwd_context.hash(password)


	@staticmethod
	def verify_password(plain_password: str, hashed_password: str) -> bool:
		return pwd_context.verify(plain_password, hashed_password)


def hash_password(password: str) -> str:
	return Hasher.get_password_hash(password)


def verify_password(password: str, stored_password: str) -> bool:
	return Hasher.verify_password(password, stored_password)
