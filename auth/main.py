from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from datetime import timedelta
from typing import List

from database import get_db, engine, Base
from schemas import (
    UserCreate, UserUpdate, UserResponse, LoginRequest, 
    TokenResponse, RefreshRequest, RoleResponse, RoleEnum
)
from models.models import User
import auth

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Auth Service")

security = HTTPBearer()


# Authentication endpoints
@app.post("/auth/register", response_model=UserResponse)
def register(user: UserCreate, db: Session = Depends(get_db)):
    existing_user = auth.get_user_by_email(db, user.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    db_user = auth.create_user(db, user)
    
    return UserResponse(
        id=str(db_user.id),
        name=db_user.name,
        email=db_user.email,
        role=db_user.role,
        createdAt=db_user.createdAt
    )


@app.post("/auth/login", response_model=TokenResponse)
def login(request: LoginRequest, db: Session = Depends(get_db)):
    user = auth.authenticate_user(db, request.email, request.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )
    
    access_token = auth.create_access_token(
        data={"sub": str(user.id), "email": user.email, "role": user.role.value}
    )
    refresh_token = auth.create_refresh_token(db, str(user.id))
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token
    )


@app.post("/auth/refresh", response_model=TokenResponse)
def refresh(request: RefreshRequest, db: Session = Depends(get_db)):
    payload = auth.verify_token(request.refresh_token, token_type="refresh")
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )
    
    db_token = auth.get_refresh_token(db, request.refresh_token)
    if not db_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token expired or revoked"
        )
    
    user_id = payload.get("sub")
    user = auth.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    
    access_token = auth.create_access_token(
        data={"sub": str(user.id), "email": user.email, "role": user.role.value}
    )
    new_refresh_token = auth.create_refresh_token(db, str(user.id))
    
    auth.revoke_refresh_token(db, request.refresh_token)
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=new_refresh_token
    )


@app.post("/auth/logout")
def logout(
    request: RefreshRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):

    payload = auth.verify_token(credentials.credentials, token_type="access")
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid access token"
        )
    
    auth.revoke_refresh_token(db, request.refresh_token)
    
    return {"message": "Successfully logged out"}


# User CRUD endpoints
@app.get("/auth/users/{user_id}", response_model=UserResponse)
def get_user(user_id: str, db: Session = Depends(get_db)):

    user = auth.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return UserResponse(
        id=str(user.id),
        name=user.name,
        email=user.email,
        role=user.role,
        createdAt=user.createdAt
    )


@app.put("/auth/users/{user_id}", response_model=UserResponse)
def update_user_endpoint(
    user_id: str,
    user_update: UserUpdate,
    db: Session = Depends(get_db)
):

    if user_update.email:
        existing_user = auth.get_user_by_email(db, user_update.email)
        if existing_user and str(existing_user.id) != user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
    
    updated_user = auth.update_user(
        db, user_id, user_update.name, user_update.email, user_update.password, user_update.role
    )
    
    if not updated_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return UserResponse(
        id=str(updated_user.id),
        name=updated_user.name,
        email=updated_user.email,
        role=updated_user.role,
        createdAt=updated_user.createdAt
    )


@app.delete("/auth/users/{user_id}")
def delete_user_endpoint(user_id: str, db: Session = Depends(get_db)):

    deleted_user = auth.delete_user(db, user_id)
    if not deleted_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return {"message": "User deleted successfully"}



@app.get("/auth/roles", response_model=RoleResponse)
def get_roles():

    return RoleResponse(roles=[role.value for role in RoleEnum])


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
