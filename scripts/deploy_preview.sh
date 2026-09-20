#!/usr/bin/env bash
# Host-owned forced command for loading and serving a runner-built preview image.
set -euo pipefail

PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
repo_url=https://github.com/ivangetsitdone/website.git
checkout=/srv/website-preview
compose_file=/srv/website/compose.preview.yaml
project=website-preview
command=${SSH_ORIGINAL_COMMAND:-${*:-}}
read -r sha archive_hash extra <<<"$command"

if [[ ! "$sha" =~ ^[0-9a-f]{40}$ ]] || [[ ! "$archive_hash" =~ ^[0-9a-f]{64}$ ]] || [ -n "${extra:-}" ]; then
  echo "expected: <40-character commit SHA> <64-character archive SHA-256>" >&2
  exit 2
fi

[ -r "$compose_file" ] || { echo "trusted preview Compose file is missing" >&2; exit 1; }
docker network inspect website_default >/dev/null

mkdir -p "$checkout"
exec 9>"${HOME}/.website-preview-deploy.lock"
flock 9

if [ ! -d "$checkout/.git" ]; then
  git clone --no-checkout "$repo_url" "$checkout"
fi
cd "$checkout"
git remote set-url origin "$repo_url"
git fetch --prune origin preview
expected=$(git rev-parse "origin/preview^{commit}")
[ "$expected" = "$sha" ] || {
  echo "requested commit $sha is not the current origin/preview commit $expected" >&2
  exit 1
}

archive=$(mktemp "${HOME}/.preview-image.XXXXXX.tar.gz")
trap 'rm -f "$archive"' EXIT
# Cap the compressed transfer at 512 MiB. The runner also rejects large unpacked images.
ulimit -f 524288
cat >"$archive"
printf '%s  %s\n' "$archive_hash" "$archive" | sha256sum -c -
gzip -t "$archive"
available=$(df --output=avail -B1 "${HOME}" | tail -1 | tr -d ' ')
[ "$available" -ge 1000000000 ] || {
  echo "less than 1 GB free before loading preview image" >&2
  exit 1
}
gzip -dc "$archive" | docker load >/dev/null

image="website-preview-candidate:$sha"
docker image inspect "$image" >/dev/null
image_size=$(docker image inspect -f '{{.Size}}' "$image")
[ "$image_size" -le 600000000 ] || {
  echo "preview image is too large: $image_size bytes" >&2
  exit 1
}

previous=$(git rev-parse HEAD 2>/dev/null || true)
previous_image=""
if [ -n "$previous" ]; then
  previous_image="website-preview-candidate:$previous"
fi

dc() {
  PREVIEW_IMAGE="$image" docker compose -p "$project" -f "$compose_file" "$@"
}

# Preserve the currently running image under its commit tag before replacement.
current_container=$(dc ps -q preview-app 2>/dev/null || true)
if [ -n "$previous_image" ] && [ -n "$current_container" ]; then
  current_image=$(docker inspect -f '{{.Image}}' "$current_container")
  docker tag "$current_image" "$previous_image"
fi

wait_healthy() {
  local container state=starting
  for _ in $(seq 60); do
    container=$(dc ps -q preview-app)
    state=$(docker inspect -f '{{.State.Health.Status}}' "$container" 2>/dev/null || echo starting)
    if [ "$state" = healthy ]; then return 0; fi
    sleep 3
  done
  echo "preview app is $state after three minutes" >&2
  return 1
}

prune_preview_images() {
  local keep_a=${1:-} keep_b=${2:-} old_image
  while read -r old_image; do
    [ -n "$old_image" ] || continue
    if [ "$old_image" != "$keep_a" ] && [ "$old_image" != "$keep_b" ]; then
      docker image rm "$old_image" >/dev/null 2>&1 || true
    fi
  done < <(docker image ls website-preview-candidate --format '{{.Repository}}:{{.Tag}}')
}

roll_back() {
  local failed_image=$image
  echo "$1" >&2
  if [ -n "$previous" ] && docker image inspect "$previous_image" >/dev/null 2>&1; then
    echo "rolling preview back to $previous" >&2
    git reset --hard "$previous"
    git clean -fdx
    image="$previous_image"
    dc up -d --no-build
    wait_healthy || echo "preview rollback is unhealthy" >&2
    docker image rm "$failed_image" >/dev/null 2>&1 || true
    prune_preview_images "$image"
  else
    dc down || true
    docker image rm "$failed_image" >/dev/null 2>&1 || true
    prune_preview_images
  fi
  exit 1
}

git reset --hard "$sha"
git clean -fdx
dc up -d --no-build || roll_back "preview start failed for $sha"
wait_healthy || { dc logs --tail 80 preview-app; roll_back "$sha never became healthy"; }
[ "$(git rev-parse HEAD)" = "$sha" ] || roll_back "preview checkout does not match $sha"

# Keep the current and immediately previous preview images for rollback; discard older tags.
prune_preview_images "$image" "$previous_image"

echo "preview is serving $sha from runner-built image $image"
dc ps
