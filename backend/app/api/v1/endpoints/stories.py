from fastapi import APIRouter, Depends, File, UploadFile, status
from sqlalchemy.orm import Session

from app.api import deps
from app.crud import story as crud_story
from app.models.user import User
from app.schemas.story import StoryOut, StoryTray
from app.schemas.user import UserBrief
from app.services import storage

router = APIRouter()


@router.post("", response_model=StoryOut, status_code=status.HTTP_201_CREATED)
async def create_story(
    file: UploadFile = File(...),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
) -> object:
    allowed = storage.ALLOWED_IMAGE_TYPES | storage.ALLOWED_VIDEO_TYPES
    media_url = await storage.upload_media(
        file, folder=f"stories/{current_user.id}", allowed_types=allowed
    )
    media_type = "video" if (file.content_type or "").startswith("video") else "image"
    return crud_story.create(db, current_user.id, media_url, media_type)


@router.get("", response_model=list[StoryTray])
def story_tray(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
) -> list[StoryTray]:
    """Active stories from followed users + self, grouped by author for the home tray."""
    stories = crud_story.get_active_feed(db, current_user.id)

    groups: dict[int, StoryTray] = {}
    for story in stories:
        tray = groups.get(story.user_id)
        if tray is None:
            tray = StoryTray(user=UserBrief.model_validate(story.owner), stories=[])
            groups[story.user_id] = tray
        tray.stories.append(StoryOut.model_validate(story))
    return list(groups.values())
