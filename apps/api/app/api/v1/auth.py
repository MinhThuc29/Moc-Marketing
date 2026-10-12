import uuid
from datetime import datetime, timezone, timedelta
from typing import List
import jwt
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select, update
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.core.rate_limit import enforce_auth_rate_limit
from app.core.security import (
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token,
)
from app.models.auth import User, Role, RefreshToken
from app.schemas.auth import (
    LoginRequest,
    TokenResponse,
    RefreshTokenRequest,
    UserResponse,
    LogoutResponse,
)
from app.api.deps import get_current_user, require_permission

router = APIRouter(prefix="/auth", tags=["Authentication & RBAC"])


def extract_user_roles_and_perms(user: User):
    roles = [r.name for r in user.roles]
    permissions = set()
    for r in user.roles:
        for p in r.permissions:
            permissions.add(p.name)
    return roles, list(permissions)


@router.post(
    "/login",
    response_model=TokenResponse,
    dependencies=[Depends(enforce_auth_rate_limit)],
    summary="Đăng nhập hệ thống và lấy cặp access/refresh token",
)
async def login(
    payload: LoginRequest,
    db: AsyncSession = Depends(get_db),
):
    # Query user by email with eager loading of roles and permissions
    result = await db.execute(
        select(User)
        .options(selectinload(User.roles).selectinload(Role.permissions))
        .where(User.email == payload.email.lower().strip())
    )
    user = result.scalar_one_or_none()

    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email hoặc mật khẩu không chính xác",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tài khoản đang bị vô hiệu hóa",
        )

    roles, permissions = extract_user_roles_and_perms(user)

    # Generate tokens
    access_token = create_access_token(
        user_id=user.id,
        email=user.email,
        roles=roles,
        permissions=permissions,
    )

    refresh_jti = str(uuid.uuid4())
    refresh_expires_at = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    refresh_token = create_refresh_token(user_id=user.id, jti=refresh_jti)

    # Persist refresh token session in DB for rotation & revocation tracking
    db_refresh = RefreshToken(
        user_id=user.id,
        token_jti=refresh_jti,
        expires_at=refresh_expires_at,
        is_revoked=False,
    )
    db.add(db_refresh)
    await db.commit()

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


@router.post(
    "/refresh",
    response_model=TokenResponse,
    summary="Làm mới access token và xoay vòng refresh token",
)
async def refresh_token(
    payload: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db),
):
    try:
        decoded = decode_token(payload.refresh_token)
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token đã hết hạn",
        )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token không hợp lệ",
        )

    if decoded.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token gửi lên không phải là refresh token",
        )

    user_id = decoded.get("sub")
    jti = decoded.get("jti")

    # Find token record in DB
    result = await db.execute(select(RefreshToken).where(RefreshToken.token_jti == jti))
    db_token = result.scalar_one_or_none()

    if not db_token or db_token.is_revoked:
        # Detected possible token reuse attempt! Revoke all tokens for user as security measure
        if db_token and db_token.is_revoked:
            await db.execute(
                update(RefreshToken)
                .where(RefreshToken.user_id == user_id)
                .values(is_revoked=True)
            )
            await db.commit()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token đã bị thu hồi hoặc không hợp lệ",
        )

    # Check user existence and status with eager loading
    user_res = await db.execute(
        select(User)
        .options(selectinload(User.roles).selectinload(Role.permissions))
        .where(User.id == user_id)
    )
    user = user_res.scalar_one_or_none()
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Người dùng không hợp lệ hoặc bị khóa",
        )

    roles, permissions = extract_user_roles_and_perms(user)

    # Token rotation: mark old jti as replaced and generate new pair
    new_jti = str(uuid.uuid4())
    db_token.is_revoked = True
    db_token.replaced_by_jti = new_jti

    new_access_token = create_access_token(
        user_id=user.id,
        email=user.email,
        roles=roles,
        permissions=permissions,
    )
    new_refresh_token = create_refresh_token(user_id=user.id, jti=new_jti)
    new_expires_at = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

    new_db_refresh = RefreshToken(
        user_id=user.id,
        token_jti=new_jti,
        expires_at=new_expires_at,
        is_revoked=False,
    )
    db.add(new_db_refresh)
    await db.commit()

    return TokenResponse(
        access_token=new_access_token,
        refresh_token=new_refresh_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


@router.post(
    "/logout",
    response_model=LogoutResponse,
    summary="Đăng xuất và thu hồi phiên làm việc",
)
async def logout(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # Revoke all active refresh tokens of the current user
    await db.execute(
        update(RefreshToken)
        .where(RefreshToken.user_id == current_user.id)
        .values(is_revoked=True)
    )
    await db.commit()

    return LogoutResponse(
        success=True,
        message="Đăng xuất thành công, phiên làm việc đã được thu hồi",
    )


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Lấy thông tin tài khoản đang đăng nhập, vai trò và quyền hạn",
)
async def get_me(
    current_user: User = Depends(get_current_user),
):
    roles, permissions = extract_user_roles_and_perms(current_user)
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        full_name=current_user.full_name,
        is_active=current_user.is_active,
        is_superuser=current_user.is_superuser,
        roles=roles,
        permissions=permissions,
    )


@router.get(
    "/protected-action",
    summary="Endpoint kiểm tra thực thi quyền hạn (Ví dụ: product.write)",
    dependencies=[Depends(require_permission("product.write"))],
)
async def protected_action(current_user: User = Depends(get_current_user)):
    return {
        "success": True,
        "message": "Bạn có quyền hạn 'product.write' hợp lệ để thực hiện thao tác này",
        "user_email": current_user.email,
    }
