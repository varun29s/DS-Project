from fastapi import APIRouter, Depends, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.api import deps
from app.crud import post as crud_post
from app.crud import social as crud_social
from app.crud import user as crud_user
from app.models.user import User
from app.schemas.post import PostOut
from app.schemas.user import UserBrief, UserOut, UserProfile, UserUpdate
from app.services import storage

router = APIRouter()


def _build_profile(db: Session, user: User, viewer: User) -> UserProfile:
    is_me = user.id == viewer.id
    return UserProfile(
        id=user.id,
        username=user.username,
        full_name=user.full_name,
        bio=user.bio,
        avatar_url=user.avatar_url,
        created_at=user.created_at,
        post_count=crud_post.count_user_posts(db, user.id),
        follower_count=crud_social.follower_count(db, user.id),
        following_count=crud_social.following_count(db, user.id),
        is_following=False if is_me else crud_social.is_following(db, viewer.id, user.id),
        is_me=is_me,
    )


@router.get("/me", response_model=UserProfile)
def read_my_profile(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
) -> UserProfile:
    return _build_profile(db, current_user, current_user)


@router.put("/me", response_model=UserOut)
def update_my_profile(
    updates: UserUpdate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
) -> User:
    return crud_user.update(db, current_user, updates)


@router.post("/me/avatar", response_model=UserOut)
async def upload_my_avatar(
    file: UploadFile,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
) -> User:
    url = await storage.upload_media(
        file, folder=f"avatars/{current_user.id}", allowed_types=storage.ALLOWED_IMAGE_TYPES
    )
    return crud_user.set_avatar(db, current_user, url)


@router.get("/{username}", response_model=UserProfile)
def get_profile(
    username: str,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
) -> UserProfile:
    user = crud_user.get_by_username(db, username)
    if user is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found")
    return _build_profile(db, user, current_user)


@router.get("/{username}/posts", response_model=list[PostOut])
def get_user_posts(
    username: str,
    skip: int = 0,
    limit: int = 30,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
) -> list:
    user = crud_user.get_by_username(db, username)
    if user is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found")
    posts = crud_post.get_user_posts(db, user.id, skip=skip, limit=limit)
    return crud_post.attach_meta(posts, current_user.id)


@router.get("/{username}/followers", response_model=list[UserBrief])
def get_user_followers(
    username: str,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
) -> list:
    user = crud_user.get_by_username(db, username)
    if user is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found")
    return crud_social.get_followers(db, user.id)


@router.get("/{username}/following", response_model=list[UserBrief])
def get_user_following(
    username: str,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
) -> list:
    user = crud_user.get_by_username(db, username)
    if user is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found")
    return crud_social.get_following(db, user.id)


@router.post("/{user_id}/follow", status_code=status.HTTP_204_NO_CONTENT)
def follow_user(
    user_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
) -> None:
    if user_id == current_user.id:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "You cannot follow yourself")
    if crud_user.get(db, user_id) is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found")
    crud_social.follow(db, current_user.id, user_id)


@router.delete("/{user_id}/follow", status_code=status.HTTP_204_NO_CONTENT)
def unfollow_user(
    user_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
) -> None:
    crud_social.unfollow(db, current_user.id, user_id)