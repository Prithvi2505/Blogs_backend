from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from models import Blog, Comment, User
from schemas.comment_schema import CommentCreate, CommentUpdate
from utils.permissions import has_role, require_role


def _get_blog(blog_id: int, db: Session, current_user: User | None = None) -> Blog:
	blog = db.query(Blog).filter(Blog.id == blog_id).first()
	if blog is None or (
		not blog.is_public
		and (current_user is None or (blog.created_by != current_user.id and not has_role(current_user, "admin")))
	):
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Blog not found")
	return blog


def _comment_response(comment: Comment, author_name: str) -> dict:
	return {
		"id": comment.id,
		"blog_id": comment.blog_id,
		"user_id": comment.user_id,
		"parent_comment_id": comment.parent_comment_id,
		"author_name": author_name,
		"content": comment.content,
		"created_at": comment.created_at,
		"updated_at": comment.updated_at,
		"replies": [],
	}


def get_comments(
	blog_id: int,
	db: Session,
	offset: int = 0,
	limit: int = 5,
	current_user: User | None = None,
) -> dict:
	_get_blog(blog_id, db, current_user)
	root_query = (
		db.query(Comment, User.name)
		.join(User, User.id == Comment.user_id)
		.filter(Comment.blog_id == blog_id, Comment.parent_comment_id.is_(None))
		.order_by(Comment.created_at, Comment.id)
	)
	total = db.query(Comment).filter(
		Comment.blog_id == blog_id,
		Comment.parent_comment_id.is_(None),
	).count()
	comment_count = total
	rows = root_query.offset(offset).limit(limit).all()

	comments = {}
	roots = []
	for comment, author_name in rows:
		response = _comment_response(comment, author_name or "Unknown author")
		comments[comment.id] = response
		roots.append(response)

	parent_ids = [comment.id for comment, _ in rows]
	while parent_ids:
		reply_rows = (
			db.query(Comment, User.name)
			.join(User, User.id == Comment.user_id)
			.filter(
				Comment.blog_id == blog_id,
				Comment.parent_comment_id.in_(parent_ids),
			)
			.order_by(Comment.created_at, Comment.id)
			.all()
		)
		parent_ids = []
		for reply, author_name in reply_rows:
			response = _comment_response(reply, author_name or "Unknown author")
			comments[reply.id] = response
			comments[reply.parent_comment_id]["replies"].append(response)
			parent_ids.append(reply.id)

	return {
		"items": roots,
		"total": total,
		"comment_count": comment_count,
		"offset": offset,
		"limit": limit,
	}


def create_comment(
	blog_id: int,
	comment_data: CommentCreate,
	current_user: User,
	db: Session,
) -> dict:
	require_role(current_user, "reader", "author")
	_get_blog(blog_id, db, current_user)
	if comment_data.parent_comment_id is not None:
		parent = db.query(Comment).filter(
			Comment.id == comment_data.parent_comment_id,
			Comment.blog_id == blog_id,
		).first()
		if parent is None:
			raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Parent comment not found")

	comment = Comment(
		blog_id=blog_id,
		user_id=current_user.id,
		parent_comment_id=comment_data.parent_comment_id,
		content=comment_data.content,
	)
	db.add(comment)
	db.commit()
	db.refresh(comment)
	return _comment_response(comment, current_user.name or "Unknown author")


def update_comment(
	comment_id: int,
	comment_data: CommentUpdate,
	current_user: User,
	db: Session,
) -> dict:
	require_role(current_user, "author")
	comment = db.query(Comment).filter(Comment.id == comment_id).first()
	if comment is None:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Comment not found")
	_get_blog(comment.blog_id, db, current_user)
	if comment.user_id != current_user.id:
		raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your comment")

	comment.content = comment_data.content
	db.commit()
	db.refresh(comment)
	return _comment_response(comment, current_user.name or "Unknown author")


def delete_comment(comment_id: int, current_user: User, db: Session) -> dict:
	comment = db.query(Comment).filter(Comment.id == comment_id).first()
	if comment is None:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Comment not found")
	_get_blog(comment.blog_id, db, current_user)
	if not has_role(current_user, "admin") and comment.user_id != current_user.id:
		raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your comment")

	db.delete(comment)
	db.commit()
	return {"message": "Comment deleted successfully"}