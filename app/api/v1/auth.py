from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps.users import get_create_user_uc
from app.api.deps.auth import get_email_service, get_otp_ticket_service
from app.application.use_cases.create_user import CreateUser, CreateUserInput, DuplicateEmailError
from app.infrastructure.notifications.email_service import EmailService
from app.infrastructure.services.otp_ticket_service import OTPTicketService, OTPInvalidError, TicketInvalidError
from app.schemas.auth import OTPRequest, OTPVerifyRequest, OTPVerifyResponse, SignupRequest
from app.schemas.users import UserResponse

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/request-otp", status_code=status.HTTP_204_NO_CONTENT)
async def request_otp(  
    payload: OTPRequest,
    otp_svc: OTPTicketService = Depends(get_otp_ticket_service),
    email_svc: EmailService = Depends(get_email_service),
) -> None:
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
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))

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
        user = uc.execute(
            CreateUserInput(
                email=payload.email,
                password=payload.password,
                full_name=payload.full_name,
            )
        )

        # 3) map to response
        # If CreateUser returns a domain User, this should work with Pydantic v2:
        return UserResponse.model_validate(user)

    except TicketInvalidError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    except DuplicateEmailError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
