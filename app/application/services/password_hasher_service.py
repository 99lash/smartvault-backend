from __future__ import annotations

import base64
import hashlib
import hmac
import os


class PBKDF2PasswordHasher:
    """
    Encodes hash as: pbkdf2$<iterations>$<salt_b64>$<dk_b64>
    """
    def __init__(self, iterations: int = 210_000):
        self._iterations = iterations

    def hash(self, raw_password: str) -> str:
        salt = os.urandom(16)
        dk = hashlib.pbkdf2_hmac(
            "sha256",
            raw_password.encode("utf-8"),
            salt,
            self._iterations,
            dklen=32,
        )
        return "pbkdf2${}${}${}".format(
            self._iterations,
            base64.urlsafe_b64encode(salt).decode("ascii"),
            base64.urlsafe_b64encode(dk).decode("ascii"),
        )

    def verify(self, raw_password: str, encoded: str) -> bool:
        scheme, iters_s, salt_b64, dk_b64 = encoded.split("$")
        if scheme != "pbkdf2":
            return False
        iters = int(iters_s)
        salt = base64.urlsafe_b64decode(salt_b64.encode("ascii"))
        expected = base64.urlsafe_b64decode(dk_b64.encode("ascii"))
        actual = hashlib.pbkdf2_hmac("sha256", raw_password.encode("utf-8"), salt, iters, dklen=len(expected))
        return hmac.compare_digest(actual, expected)
