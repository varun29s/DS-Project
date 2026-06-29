from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.api import deps
from app.crud import reel as crud_reel
from app.crud import user as crud_user
from app.models.user import User
from app.schemas.reel import ReelOut
from app.services import recommender_client, storage

router = APIRouter()


def _reel_or_404(db: Session, reel_id: int):
    reel = crud_reel.get(db, reel_id)
    if reel is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Reel not found")
    return reel


@router.post("", response_model=ReelOut, status_code=status.HTTP_201_CREATED)
async def create_reel(
    caption: str | None = Form(default=None),
    video: UploadFile = File(...),
    thumbnail: UploadFile | None = File(default=None),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
) -> object:
    video_url = await storage.upload_media(
        video, folder=f"reels/{current_user.id}", allowed_types=storage.ALLOWED_VIDEO_TYPES
    )
    thumbnail_url = None
    if thumbnail is not None:
        thumbnail_url = await storage.upload_media(
            thumbnail,
            folder=f"reels/{current_user.id}/thumbs",
            allowed_types=storage.ALLOWED_IMAGE_TYPES,
        )
    reel = crud_reel.create(db, current_user.id, video_url, thumbnail_url, caption)
    return crud_reel.attach_counts(db, [reel], current_user.id)[0]


@router.get("/recommended", response_model=list[ReelOut])
def recommended_reels(
    limit: int = 20,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
) -> list:
    """Personalized reel suggestions from the ML microservice, falling back to chronological."""
    ranked = recommender_client.get_recommendations(current_user.id, limit)
    if ranked is None:
        reels = crud_reel.get_feed(db, limit=limit)
        return crud_reel.attach_counts(db, reels, current_user.id)

    reasons = {item["reel_id"]: item.get("reason") for item in ranked}
    reels_by_id = {r.id: r for r in crud_reel.get_by_ids(db, list(reasons.keys()))}
    ordered = [reels_by_id[item["reel_id"]] for item in ranked if item["reel_id"] in reels_by_id]
    crud_reel.attach_counts(db, ordered, current_user.id)
    for reel in ordered:
        reel.reason = reasons.get(reel.id)
    return ordered


@router.get("", response_model=list[ReelOut])
def reels_feed(
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
) -> list:
    reels = crud_reel.get_feed(db, skip=skip, limit=limit)
    return crud_reel.attach_counts(db, reels, current_user.id)


@router.get("/user/{username}", response_model=list[ReelOut])
def user_reels(
    username: str,
    skip: int = 0,
    limit: int = 30,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
) -> list:
    user = crud_user.get_by_username(db, username)
    if user is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found")
    reels = crud_reel.get_user_reels(db, user.id, skip=skip, limit=limit)
    return crud_reel.attach_counts(db, reels, current_user.id)


@router.post("/{reel_id}/like", status_code=status.HTTP_204_NO_CONTENT)
def like_reel(
    reel_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
) -> None:
    _reel_or_404(db, reel_id)
    crud_reel.like(db, current_user.id, reel_id)


@router.delete("/{reel_id}/like", status_code=status.HTTP_204_NO_CONTENT)
def unlike_reel(
    reel_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
) -> None:
    crud_reel.unlike(db, current_user.id, reel_id)


@router.post("/{reel_id}/view", status_code=status.HTTP_204_NO_CONTENT)
def view_reel(
    reel_id: int,
    watch_ms: int = 0,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
) -> None:
    """Record a watch event — the primary implicit-feedback signal for recs."""
    _reel_or_404(db, reel_id)
    crud_reel.record_view(db, current_user.id, reel_id, watch_ms=watch_ms)
