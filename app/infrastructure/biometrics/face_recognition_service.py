from __future__ import annotations

import json
from io import BytesIO


class FaceRecognitionService:
    TOLERANCE = 0.55  # lower = stricter (library default is 0.6)

    @staticmethod
    def encode(image_bytes: bytes) -> list[float]:
        """Return 128-d face encoding from raw image bytes.

        Raises:
            ValueError: If no face is detected in the image.
        """
        import face_recognition  # lazy — avoids startup crash if models missing
        import numpy as np
        from PIL import Image

        img = Image.open(BytesIO(image_bytes)).convert("RGB")
        rgb = np.array(img)
        encodings = face_recognition.face_encodings(rgb)
        if not encodings:
            raise ValueError("No face detected in image")
        return encodings[0].tolist()

    @staticmethod
    def match(stored_encoding: str, live_encoding: list[float]) -> bool:
        """Compare a stored JSON encoding against a live encoding.

        Args:
            stored_encoding: JSON-serialized list[float] from the database.
            live_encoding:   128-d encoding from the current photo.

        Returns:
            True if the face matches within the configured tolerance.
        """
        import face_recognition
        import numpy as np

        known = np.array(json.loads(stored_encoding))
        result = face_recognition.compare_faces(
            [known],
            np.array(live_encoding),
            tolerance=FaceRecognitionService.TOLERANCE,
        )
        return bool(result[0])
