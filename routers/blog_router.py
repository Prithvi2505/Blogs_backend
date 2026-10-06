from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from services import blog_service, comment_service
from database import get_db
from models import User
from schemas.comment_schema import CommentCreate, CommentPageResponse, CommentResponse, CommentUpdate
from schemas.blog_schema import BlogCreate, BlogLikeResponse, BlogResponse, BlogUpdate, BlogVisibilityUpdate
from utils.auth_utils import get_current_user, get_optional_current_user


router = APIRouter(prefix="/blogs", tags=["blogs"])


@router.get("", response_model=list[BlogResponse])
def get_all(
	db: Session = Depends(get_db),
	current_user: User | None = Depends(get_optional_current_user),
):
	return blog_service.get_all_blogs(db, current_user)


@router.get("/me", response_model=list[BlogResponse])
def get_mine(
	current_user: User = Depends(get_current_user),
	db: Session = Depends(get_db),
):
	return blog_service.get_my_blogs(current_user, db)


@router.post("", response_model=BlogResponse, status_code=status.HTTP_201_CREATED)
def create(
	blog_data: BlogCreate,
	current_user: User = Depends(get_current_user),
	db: Session = Depends(get_db),
):
	return blog_service.create_blog(blog_data, current_user, db)


@router.get("/{blog_id}/comments", response_model=CommentPageResponse)
def get_comments(
	blog_id: int,
	offset: int = Query(default=0, ge=0),
	limit: int = Query(default=5, ge=1, le=50),
	db: Session = Depends(get_db),
	current_user: User | None = Depends(get_optional_current_user),
):
	return comment_service.get_comments(blog_id, db, offset, limit, current_user)


@router.post(
	"/{blog_id}/comments",
	response_model=CommentResponse,
	status_code=status.HTTP_201_CREATED,
)
def create_comment(
	blog_id: int,
	comment_data: CommentCreate,
	current_user: User = Depends(get_current_user),
	db: Session = Depends(get_db),
):
	return comment_service.create_comment(blog_id, comment_data, current_user, db)


@router.put("/comments/{comment_id}", response_model=CommentResponse)
def update_comment(
	comment_id: int,
	comment_data: CommentUpdate,
	current_user: User = Depends(get_current_user),
	db: Session = Depends(get_db),
):
	return comment_service.update_comment(comment_id, comment_data, current_user, db)


@router.delete("/comments/{comment_id}")
def delete_comment(
	comment_id: int,
	current_user: User = Depends(get_current_user),
	db: Session = Depends(get_db),
):
	return comment_service.delete_comment(comment_id, current_user, db)


@router.put("/{blog_id}/visibility", response_model=BlogResponse)
def update_visibility(
	blog_id: int,
	visibility: BlogVisibilityUpdate,
	current_user: User = Depends(get_current_user),
	db: Session = Depends(get_db),
):
	return blog_service.update_blog_visibility(blog_id, visibility.is_public, current_user, db)


@router.get("/{blog_id}", response_model=BlogResponse)
def get_one(
	blog_id: int,
	db: Session = Depends(get_db),
	current_user: User | None = Depends(get_optional_current_user),
):
	blog = blog_service.get_blog(blog_id, db, current_user)
	return blog_service.blog_response(blog, db, current_user)


@router.put("/{blog_id}/like", response_model=BlogLikeResponse)
def like_blog(
	blog_id: int,
	current_user: User = Depends(get_current_user),
	db: Session = Depends(get_db),
):
	return blog_service.set_blog_like(blog_id, current_user, True, db)


@router.delete("/{blog_id}/like", response_model=BlogLikeResponse)
def unlike_blog(
	blog_id: int,
	current_user: User = Depends(get_current_user),
	db: Session = Depends(get_db),
):
	return blog_service.set_blog_like(blog_id, current_user, False, db)


@router.put("/{blog_id}", response_model=BlogResponse)
def update(
	blog_id: int,
	blog_data: BlogUpdate,
	current_user: User = Depends(get_current_user),
	db: Session = Depends(get_db),
):
	return blog_service.update_blog(blog_id, blog_data, current_user, db)


@router.delete("/{blog_id}")
def delete(
	blog_id: int,
	current_user: User = Depends(get_current_user),
	db: Session = Depends(get_db),
):
	return blog_service.delete_blog(blog_id, current_user, db)
