from fastapi import APIRouter

from app.api.v1.endpoints import auth, posts, reels, stories, user

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["Auth"])
api_router.include_router(user.router, prefix="/users", tags=["Users"])
api_router.include_router(posts.router, prefix="/posts", tags=["Posts"])
api_router.include_router(stories.router, prefix="/stories", tags=["Stories"])
api_router.include_router(reels.router, prefix="/reels", tags=["Reels"])
