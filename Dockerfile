FROM node:22-alpine AS assets
WORKDIR /build/frontend
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

FROM python:3.13-slim AS photos
WORKDIR /build
RUN pip install --no-cache-dir Pillow==11.3.0
COPY scripts/build_photos.py ./scripts/build_photos.py
COPY content/photos/ ./content/photos/
COPY content/portraits/ ./content/portraits/
COPY app/data/portfolio.json ./app/data/portfolio.json
RUN python scripts/build_photos.py

FROM python:3.13-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /srv
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt && useradd --uid 10001 --create-home app
COPY app/ ./app/
COPY --from=assets /build/app/static ./app/static
COPY --from=photos /build/app/media ./app/media
USER app
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--no-proxy-headers"]
