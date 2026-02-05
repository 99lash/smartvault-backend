from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status, Request
from starlette.concurrency import run_in_threadpool

from app.api.deps.users import get_create_user_uc
from app.api.deps.auth import get_email_service, get_otp_ticket_service
from app.application.use_cases.create_user import CreateUser, CreateUserInput, DuplicateEmailError
from app.infrastructure.notifications.email_service import EmailService
from app.infrastructure.services.otp_ticket_service import OTPTicketService, OTPInvalidError, TicketInvalidError
from app.infrastructure.security.rate_limiter import RateLimiter
from app.core.settings import settings
from app.schemas.auth import OTPRequest, OTPVerifyRequest, OTPVerifyResponse, SignupRequest
from app.schemas.users import UserResponse

router = APIRouter(prefix="/auth", tags=["auth"])

# Dependency for RateLimiter (stateless)
def get_rate_limiter() -> RateLimiter:
    return RateLimiter()

@router.post("/request-otp", status_code=status.HTTP_204_NO_CONTENT)
async def request_otp(  
    request: Request,
    payload: OTPRequest,
    otp_svc: OTPTicketService = Depends(get_otp_ticket_service),
    email_svc: EmailService = Depends(get_email_service),
    limiter: RateLimiter = Depends(get_rate_limiter),
) -> None:
    # Rate Limit: IP Address
    # Fallback to 'unknown' if client is None (unlikely in HTTP)
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
        # 1) consume ticket first (one-time)
        await otp_svc.consume_ticket(payload.email, payload.signup_ticket)

        # 2) create user
        # FIX: Offload sync work to threadpool (Previous Task)
        user = await run_in_threadpool(
            uc.execute,
            CreateUserInput(
                email=payload.email,
                password=payload.password,
                full_name=payload.full_name,
            )
        )

        # 3) map to response
        return UserResponse.model_validate(user)

    except TicketInvalidError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(e))
    except DuplicateEmailError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))