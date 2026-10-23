import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import User
from ..schemas import LoginRequest, TokenResponse, UserProfileResponse, ChangePasswordRequest
from ..auth import verify_password, create_token, current_user, hash_password

logger = logging.getLogger("fleetflow.auth")

router = APIRouter(prefix="/api/auth", tags=["Authentication"])

@router.post("/login", response_model=TokenResponse)
def login(data: LoginRequest, db: Session = Depends(get_db)):
    try:
        user = db.query(User).filter(User.email == data.email).first()
    except Exception as e:
        logger.error(f"Database query error during login: {e}")
        raise HTTPException(
            status_code=503,
            detail="Database service is temporarily unavailable. Please verify database connection."
        )

    if not user or not verify_password(data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    return TokenResponse(access_token=create_token(user), role=user.role, email=user.email, user_id=user.id)


@router.get("/me", response_model=UserProfileResponse)
def get_current_user_profile(user: User = Depends(current_user)):
    """
    Returns the authenticated user's profile metadata and role.
    """
    return user


@router.put("/change-password")
def change_password(
    data: ChangePasswordRequest,
    db: Session = Depends(get_db),
    user: User = Depends(current_user)
):
    """
    Secure password management for authenticated users.
    """
    if not verify_password(data.current_password, user.password_hash):
        raise HTTPException(status_code=400, detail="Current password is incorrect")
    
    user.password_hash = hash_password(data.new_password)
    db.commit()
    return {"status": "success", "message": "Password updated successfully"}

