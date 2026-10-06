from datetime import date

from pydantic import BaseModel, Field


class BlogCreate(BaseModel):
	title: str
	description: str
	tags: list[str] = Field(default_factory=list)


class BlogUpdate(BaseModel):
	title: str | None = None
	description: str | None = None
	tags: list[str] | None = None


class BlogResponse(BaseModel):
	id: int
	title: str
	description: str
	created_at: date
	last_updated_at: date
	created_by: int
	is_public: bool
	author_name: str
	tags: list[str]
	like_count: int
	comment_count: int
	liked_by_me: bool

	model_config = {"from_attributes": True}


class BlogVisibilityUpdate(BaseModel):
	is_public: bool


class BlogLikeResponse(BaseModel):
	liked: bool
	like_count: int
