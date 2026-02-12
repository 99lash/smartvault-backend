from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status, Request
from starlette.concurrency import run_in_threadpool

from app.api.deps.users import get_create_user_uc, get_authenticate_user_uc
from app.api.deps.auth import (
    get_email_service, get_otp_ticket_service, get_rate_limiter, get_token_service,
    get_request_password_reset_uc, get_confirm_password_reset_uc
)
from app.application.use_cases.create_user import CreateUser, CreateUserInput, DuplicateEmailError
from app.application.use_cases.authenticate_user import AuthenticateUser, LoginInput, InvalidCredentialsError
from app.application.use_cases.reset_password import RequestPasswordReset, RequestPasswordResetInput, ConfirmPasswordReset, ConfirmPasswordResetInput
from app.application.services.token_service import TokenService
from app.infrastructure.notifications.email_service import EmailService
from app.infrastructure.services.otp_ticket_service import OTPTicketService, OTPInvalidError, TicketInvalidError
from app.infrastructure.security.rate_limiter import RateLimiter
from app.core.settings import settings
# Updated imports
from app.schemas.auth import (
    OTPRequest, OTPVerifyRequest, OTPVerifyResponse, SignupRequest, 
    LoginRequest, Token, RefreshRequest, LogoutRequest,
    PasswordResetRequest, PasswordResetConfirm
)
from app.schemas.users import UserResponse

router = APIRouter(prefix="/auth", tags=["auth"])

# ... (Keep request-otp, verify-otp, signup unchanged) ...
@router.post("/request-otp", status_code=status.HTTP_204_NO_CONTENT)
async def request_otp(  
    request: Request,
    payload: OTPRequest,
    otp_svc: OTPTicketService = Depends(get_otp_ticket_service),
    email_svc: EmailService = Depends(get_email_service),
    limiter: RateLimiter = Depends(get_rate_limiter),
) -> None:
    client_ip = request.client.host if request.client else "unknown"
    await limiter.allow_request(
        key=f"otp_req:{client_ip}",
        limit=settings.RATE_LIMIT_OTP_REQ_PER_MIN,
        window_seconds=60
    )
    result = await otp_svc.issue_otp(payload.email)
    await email_svc.send_otp(payload.email, result.otp)

@router.post("/verify-otp", response_model=OTPVerifyResponse)
async def verify_otp(
    payload: OTPVerifyRequest,
    otp_svc: OTPTicketService = Depends(get_otp_ticket_service),
) -> OTPVerifyResponse:
    try:
        ticket = await otp_svc.verify_otp_and_issue_ticket(payload.email, payload.otp)
        return OTPVerifyResponse(signup_ticket=ticket)
    except OTPInvalidError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(e))

@router.post("/signup", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def signup(
    payload: SignupRequest,
    otp_svc: OTPTicketService = Depends(get_otp_ticket_service),
    uc: CreateUser = Depends(get_create_user_uc),
) -> UserResponse:
    try:
        await otp_svc.consume_ticket(payload.email, payload.signup_ticket)
        user = await run_in_threadpool(
            uc.execute,
            CreateUserInput(
                email=payload.email,
                password=payload.password,
                full_name=payload.full_name,
            )
        )
        return UserResponse.model_validate(user)
    except TicketInvalidError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(e))
    except DuplicateEmailError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))

# UPDATED LOGIN
@router.post("/login", response_model=Token)
async def login(
    request: Request,
    payload: LoginRequest,
    uc: AuthenticateUser = Depends(get_authenticate_user_uc),
    token_svc: TokenService = Depends(get_token_service),
    limiter: RateLimiter = Depends(get_rate_limiter),
) -> Token:
    client_ip = request.client.host if request.client else "unknown"
    await limiter.allow_request(
        key=f"login_req:{client_ip}",
        limit=settings.RATE_LIMIT_LOGIN_REQ_PER_MIN,
        window_seconds=60
    )

    try:
        user = await run_in_threadpool(
            uc.execute,
            LoginInput(email=payload.email, password=payload.password)
        )
        
        access_token = token_svc.create_access_token(subject=user.id)
        refresh_token = token_svc.create_refresh_token(user_id=user.id)
        
        return Token(
            access_token=access_token, 
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        )
        
    except InvalidCredentialsError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

# NEW: REFRESH ENDPOINT
@router.post("/refresh", response_model=Token)
async def refresh_token(
    payload: RefreshRequest,
    token_svc: TokenService = Depends(get_token_service),
) -> Token:
    try:
        # Atomic rotation
        new_access, new_refresh, _ = token_svc.rotate_refresh_token(payload.refresh_token)
        
        return Token(
            access_token=new_access,
            refresh_token=new_refresh,
            token_type="bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        )
    except ValueError:
        # 401 indicates invalid token (or reused)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )

# NEW: LOGOUT ENDPOINT
@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    payload: LogoutRequest,
    token_svc: TokenService = Depends(get_token_service),
) -> None:
    token_svc.revoke_refresh_token(payload.refresh_token)

# NEW: REQUEST PASSWORD RESET ENDPOINT
@router.post("/request-password-reset", status_code=status.HTTP_204_NO_CONTENT)
async def request_password_reset(
    payload: PasswordResetRequest,
    uc: RequestPasswordReset = Depends(get_request_password_reset_uc),
) -> None:
    await uc.execute(RequestPasswordResetInput(email=payload.email))


# NEW: CONFIRM PASSWORD RESET ENDPOINT
@router.post("/confirm-password-reset", status_code=status.HTTP_204_NO_CONTENT)
async def confirm_password_reset(
    payload: PasswordResetConfirm,
    uc: ConfirmPasswordReset = Depends(get_confirm_password_reset_uc),
) -> None:
    try:
        await uc.execute(ConfirmPasswordResetInput(
            token=payload.token,
            new_password=payload.new_password,
        ))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(e))