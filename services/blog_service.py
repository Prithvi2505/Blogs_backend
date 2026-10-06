from datetime import date

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from models import Blog, BlogLike, Comment, Tag, User
from schemas.blog_schema import BlogCreate, BlogUpdate
from utils.permissions import has_role, require_role


def blog_response(blog: Blog, db: Session, current_user: User | None = None):
	author = db.query(User).filter(User.id == blog.created_by).first()
	like_count = db.query(BlogLike).filter(BlogLike.blog_id == blog.id).count()
	comment_count = db.query(Comment).filter(
		Comment.blog_id == blog.id,
		Comment.parent_comment_id.is_(None),
	).count()
	liked_by_me = current_user is not None and db.query(BlogLike).filter(
		BlogLike.blog_id == blog.id,
		BlogLike.user_id == current_user.id,
	).first() is not None
	return {
		"id": blog.id,
		"title": blog.title,
		"description": blog.description,
		"created_at": blog.created_at,
		"last_updated_at": blog.last_updated_at,
		"created_by": blog.created_by,
		"is_public": blog.is_public,
		"author_name": author.name if author else "Unknown author",
		"tags": [tag.name for tag in blog.tags],
		"like_count": like_count,
		"comment_count": comment_count,
		"liked_by_me": liked_by_me,
	}


def _get_or_create_tags(names: list[str], db: Session) -> list[Tag]:
	tags = []
	seen = set()
	for name in names:
		normalized_name = name.strip().lower()
		if not normalized_name or normalized_name in seen:
			continue
		seen.add(normalized_name)
		tag = db.query(Tag).filter(Tag.name == normalized_name).first()
		if tag is None:
			tag = Tag(name=normalized_name)
			db.add(tag)
		tags.append(tag)
	return tags


def get_all_blogs(db: Session, current_user: User | None = None):
	query = db.query(Blog)
	if current_user is None or not has_role(current_user, "admin"):
		query = query.filter(Blog.is_public.is_(True))
	blogs = query.all()
	return [blog_response(blog, db, current_user) for blog in blogs]


def get_my_blogs(current_user: User, db: Session):
	require_role(current_user, "author")
	blogs = db.query(Blog).filter(Blog.created_by == current_user.id).all()
	return [blog_response(blog, db, current_user) for blog in blogs]


def create_blog(blog_data: BlogCreate, current_user: User, db: Session):
	require_role(current_user, "author")
	blog = Blog(
		title=blog_data.title,
		description=blog_data.description,
		created_at=date.today(),
		last_updated_at=date.today(),
		created_by=current_user.id,
		tags=_get_or_create_tags(blog_data.tags, db),
	)
	db.add(blog)
	db.commit()
	db.refresh(blog)
	return blog_response(blog, db, current_user)


def get_blog(blog_id: int, db: Session, current_user: User | None = None):
	blog = db.query(Blog).filter(Blog.id == blog_id).first()
	if blog is None or (
		not blog.is_public
		and (current_user is None or (blog.created_by != current_user.id and not has_role(current_user, "admin")))
	):
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Blog not found")
	return blog


def update_blog(blog_id: int, blog_data: BlogUpdate, current_user: User, db: Session):
	require_role(current_user, "author")
	blog = get_blog(blog_id, db, current_user)
	if blog.created_by != current_user.id:
		raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your blog")

	changes = blog_data.model_dump(exclude_unset=True)
	if not changes:
		raise HTTPException(
			status_code=status.HTTP_400_BAD_REQUEST,
			detail="Provide title or description to update",
		)

	tag_names = changes.pop("tags", None)
	if tag_names is not None:
		blog.tags = _get_or_create_tags(tag_names, db)
	for field, value in changes.items():
		setattr(blog, field, value)
	blog.last_updated_at = date.today()
	db.commit()
	db.refresh(blog)
	return blog_response(blog, db, current_user)


def update_blog_visibility(blog_id: int, is_public: bool, current_user: User, db: Session):
	blog = db.query(Blog).filter(Blog.id == blog_id).first()
	if blog is None:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Blog not found")
	if not has_role(current_user, "admin") and (not has_role(current_user, "author") or blog.created_by != current_user.id):
		raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your blog")

	blog.is_public = is_public
	db.commit()
	db.refresh(blog)
	return blog_response(blog, db, current_user)


def set_blog_like(blog_id: int, current_user: User, liked: bool, db: Session):
	get_blog(blog_id, db, current_user)
	like = db.query(BlogLike).filter(
		BlogLike.blog_id == blog_id,
		BlogLike.user_id == current_user.id,
	).first()

	if liked and like is None:
		db.add(BlogLike(blog_id=blog_id, user_id=current_user.id))
		try:
			db.commit()
		except IntegrityError:
			db.rollback()
	elif not liked and like is not None:
		db.delete(like)
		db.commit()

	return {
		"liked": db.query(BlogLike).filter(
			BlogLike.blog_id == blog_id,
			BlogLike.user_id == current_user.id,
		).first() is not None,
		"like_count": db.query(BlogLike).filter(BlogLike.blog_id == blog_id).count(),
	}


def delete_blog(blog_id: int, current_user: User, db: Session):
	blog = get_blog(blog_id, db, current_user)
	if not has_role(current_user, "admin") and (not has_role(current_user, "author") or blog.created_by != current_user.id):
		raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your blog")

	db.delete(blog)
	db.commit()
	return {"message": "Blog deleted successfully"}
