import asyncio

import pytest

from app.infrastructure.services.otp_ticket_service import OTPTicketService, OTPInvalidError
from app.infrastructure.cache.redis_client import redis_get, redis_del


@pytest.mark.asyncio
async def test_verify_otp_consumes_once_atomically():
    svc = OTPTicketService()
    email = "concurrent@example.com"
    otp = (await svc.issue_otp(email)).otp

    async def attempt():
        try:
            return await svc.verify_otp_and_issue_ticket(email, otp)
        except OTPInvalidError:
            return "invalid"

    first, second = await asyncio.gather(attempt(), attempt())
    successes = [t for t in (first, second) if t != "invalid"]
    failures = [t for t in (first, second) if t == "invalid"]

    assert len(successes) == 1
    assert len(failures) == 1

    # OTP should be removed after the successful verification
    stored = await redis_get(svc._otp_key(email))
    assert stored is None

    # cleanup any ticket that was issued
    for ticket in successes:
        await redis_del(svc._ticket_key(ticket))


@pytest.mark.asyncio
async def test_wrong_otp_does_not_consume():
    svc = OTPTicketService()
    email = "wrong@example.com"
    otp = (await svc.issue_otp(email)).otp

    with pytest.raises(OTPInvalidError):
        await svc.verify_otp_and_issue_ticket(email, "000000")

    # OTP should still be present after a wrong attempt
    still_there = await redis_get(svc._otp_key(email))
    assert still_there is not None

    # cleanup
    await redis_del(svc._otp_key(email))
