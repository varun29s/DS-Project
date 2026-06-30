from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.crud import user as crud_user
from app.schemas.token import Token, TokenWithUser
from app.schemas.user import UserCreate, UserOut

router = APIRouter()


@router.post("/signup", response_model=TokenWithUser, status_code=status.HTTP_201_CREATED)
def signup(user_in: UserCreate, db: Session = Depends(deps.get_db)) -> TokenWithUser:
    if crud_user.get_by_email(db, user_in.email):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Email already registered")
    if crud_user.get_by_username(db, user_in.username):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Username already taken")

    user = crud_user.create(db, user_in)
    token = security.create_access_token(user.id)
    return TokenWithUser(access_token=token, user=UserOut.model_validate(user))


@router.post("/login", response_model=Token)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(deps.get_db),
) -> Token:
    """OAuth2 password flow. The ``username`` field accepts a username or email."""
    user = crud_user.get_by_login(db, form_data.username)
    if not user or not security.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = security.create_access_token(user.id)
    return Token(access_token=token)