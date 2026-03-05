FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Build deps for dlib (required by face_recognition)
RUN apt-get update && apt-get install -y --no-install-recommends \
    cmake \
    build-essential \
    libopenblas-dev \
    liblapack-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt requirements.txt
COPY requirements-dev.txt requirements-dev.txt

# setuptools must be installed first — face_recognition_models imports pkg_resources from it
RUN pip install --no-cache-dir setuptools && \
    pip install --no-cache-dir -r requirements.txt -r requirements-dev.txt

# Patch face_recognition_models: pkg_resources removed in setuptools >=73
RUN python - <<'EOF'
import pathlib
f = pathlib.Path('/usr/local/lib/python3.12/site-packages/face_recognition_models/__init__.py')
src = f.read_text()
src = src.replace(
    'from pkg_resources import resource_filename',
    'import importlib.resources\nresource_filename = lambda pkg, path: str(importlib.resources.files(pkg) / path)'
)
f.write_text(src)
EOF

COPY . .

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host=0.0.0.0", "--port=8000"]
