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
COPY content/brand/ ./content/brand/
COPY app/data/portfolio.json ./app/data/portfolio.json
RUN python scripts/build_photos.py

FROM python:3.13-slim
ENV PYTHONUNBUFFERED=1
WORKDIR /srv
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt && useradd --uid 10001 --create-home app
COPY app/ ./app/
COPY --from=assets /build/app/static ./app/static
COPY --from=photos /build/app/media ./app/media
# Compile every module once, here. The runtime filesystem is read-only, so anything left
# uncompiled is recompiled from source on each container start — which is most of the time
# a visitor spends looking at a 502 during a deploy.
RUN python -m compileall -q /usr/local/lib/python3.13/site-packages /srv/app
# Only now: at runtime there is nowhere to write bytecode anyway, and trying is wasted work.
ENV PYTHONDONTWRITEBYTECODE=1
USER app
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--no-proxy-headers"]
