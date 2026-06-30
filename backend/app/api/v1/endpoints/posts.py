from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.api import deps
from app.crud import post as crud_post
from app.crud import social as crud_social
from app.models.user import User
from app.schemas.comment import CommentCreate, CommentOut
from app.schemas.post import PostOut
from app.services import storage

router = APIRouter()


def _post_or_404(db: Session, post_id: int):
    post = crud_post.get(db, post_id)
    if post is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Post not found")
    return post


@router.post("", response_model=PostOut, status_code=status.HTTP_201_CREATED)
async def create_post(
    caption: str | None = Form(default=None),
    file: UploadFile = File(...),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
) -> object:
    image_url = await storage.upload_media(
        file, folder=f"posts/{current_user.id}", allowed_types=storage.ALLOWED_IMAGE_TYPES
    )
    post = crud_post.create(db, current_user.id, image_url, caption)
    return crud_post.attach_meta([post], current_user.id)[0]


@router.get("/feed", response_model=list[PostOut])
def home_feed(
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
) -> list:
    posts = crud_post.get_feed(db, current_user.id, skip=skip, limit=limit)
    return crud_post.attach_meta(posts, current_user.id)


@router.get("/{post_id}", response_model=PostOut)
def get_post(
    post_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
) -> object:
    post = _post_or_404(db, post_id)
    return crud_post.attach_meta([post], current_user.id)[0]


@router.delete("/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_post(
    post_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
) -> None:
    post = _post_or_404(db, post_id)
    if post.user_id != current_user.id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Not your post")
    crud_post.delete(db, post)


@router.post("/{post_id}/like", status_code=status.HTTP_204_NO_CONTENT)
def like_post(
    post_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
) -> None:
    _post_or_404(db, post_id)
    crud_social.like_post(db, current_user.id, post_id)


@router.delete("/{post_id}/like", status_code=status.HTTP_204_NO_CONTENT)
def unlike_post(
    post_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
) -> None:
    crud_social.unlike_post(db, current_user.id, post_id)


@router.get("/{post_id}/comments", response_model=list[CommentOut])
def list_comments(
    post_id: int,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
) -> list:
    _post_or_404(db, post_id)
    return crud_social.get_comments(db, post_id, skip=skip, limit=limit)


@router.post(
    "/{post_id}/comments", response_model=CommentOut, status_code=status.HTTP_201_CREATED
)
def create_comment(
    post_id: int,
    comment_in: CommentCreate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
) -> object:
    _post_or_404(db, post_id)
    return crud_social.add_comment(db, current_user.id, post_id, comment_in.text)