from pydantic import BaseModel, ConfigDict, Field, field_validator

from schemas.auth_schema import UserRole


class UserProfileUpdate(BaseModel):
	name: str = Field(min_length=1, max_length=100)
	bio: str | None = Field(default=None, max_length=500)

	@field_validator("name")
	@classmethod
	def validate_name(cls, value: str) -> str:
		value = value.strip()
		if not value:
			raise ValueError("Name cannot be blank")
		return value

	@field_validator("bio")
	@classmethod
	def normalize_bio(cls, value: str | None) -> str | None:
		return value.strip() or None if value is not None else None


class UserProfile(BaseModel):
	model_config = ConfigDict(from_attributes=True)

	id: int
	name: str
	email: str
	bio: str | None
	role: UserRole