from datetime import datetime

from pydantic import BaseModel, Field, field_validator


class CommentCreate(BaseModel):
	content: str = Field(min_length=1, max_length=5000)
	parent_comment_id: int | None = None

	@field_validator("content")
	@classmethod
	def trim_content(cls, value: str) -> str:
		value = value.strip()
		if not value:
			raise ValueError("Comment cannot be empty")
		return value


class CommentUpdate(BaseModel):
	content: str = Field(min_length=1, max_length=5000)

	@field_validator("content")
	@classmethod
	def trim_content(cls, value: str) -> str:
		value = value.strip()
		if not value:
			raise ValueError("Comment cannot be empty")
		return value


class CommentResponse(BaseModel):
	id: int
	blog_id: int
	user_id: int
	parent_comment_id: int | None
	author_name: str
	content: str
	created_at: datetime
	updated_at: datetime
	replies: list["CommentResponse"] = Field(default_factory=list)

	model_config = {"from_attributes": True}


class CommentPageResponse(BaseModel):
	items: list[CommentResponse]
	total: int
	comment_count: int
	offset: int
	limit: int