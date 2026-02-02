from app.application.services.password_hasher_service import PBKDF2PasswordHasher


def test_verify_returns_false_on_malformed_hash():
    hasher = PBKDF2PasswordHasher(iterations=10_000)

    assert hasher.verify("pw", "not-a-hash") is False
    assert hasher.verify("pw", "pbkdf2$nope$salt$dk") is False
    assert hasher.verify("pw", "pbkdf2$-1$c2FsdA==$ZGs=") is False
