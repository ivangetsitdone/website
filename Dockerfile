# Digest-pinned so the runner and the droplet build the same image. The tag stays for
# readability; the digest is what resolves. Dependabot's docker ecosystem bumps these.
FROM node:26-alpine@sha256:dbaa92e5758cbbcf85d65d5403fdb530fe3442cbe8c6dbfb7ef23365450d5070 AS assets
WORKDIR /build/frontend
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

FROM python:3.13-slim@sha256:8d9d0b8bcf6506481eae4907c18f5e3e7902e629f5f6d684f9e7c32e85e3ddf0 AS photos
WORKDIR /build
RUN pip install --no-cache-dir Pillow==11.3.0
COPY scripts/build_photos.py ./scripts/build_photos.py
COPY content/photos/ ./content/photos/
COPY content/portraits/ ./content/portraits/
COPY content/brand/ ./content/brand/
COPY app/data/portfolio.json ./app/data/portfolio.json
RUN python scripts/build_photos.py

FROM python:3.13-slim@sha256:8d9d0b8bcf6506481eae4907c18f5e3e7902e629f5f6d684f9e7c32e85e3ddf0
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
