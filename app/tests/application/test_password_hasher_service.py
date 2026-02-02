from app.application.services.password_hasher_service import PBKDF2PasswordHasher


def test_verify_returns_false_on_malformed_hash():
    hasher = PBKDF2PasswordHasher(iterations=10_000)

    # malformed formats
    assert hasher.verify("pw", "not-a-hash") is False
    assert hasher.verify("pw", "pbkdf2$nope$salt$dk") is False
    assert hasher.verify("pw", "pbkdf2$-1$c2FsdA==$ZGs=") is False

    # non-string encoded value
    assert hasher.verify("pw", None) is False  # type: ignore[arg-type]

    # empty decoded expected (dklen == 0 case)
    assert hasher.verify("pw", "pbkdf2$1$c2FsdA==$") is False
    
def test_verify_happy_path():
    hasher = PBKDF2PasswordHasher(iterations=10_000)
    encoded = hasher.hash("correct-horse-battery-staple")
    assert hasher.verify("correct-horse-battery-staple", encoded) is True
    assert hasher.verify("wrong-password", encoded) is False

