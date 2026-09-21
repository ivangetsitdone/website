#!/usr/bin/env bash
# Bring this site up on a fresh host. Installs Docker if it is missing, clones the
# repository, and starts the stack.
#
# This provisions a host; it does not update one. Once a checkout exists, the deploy
# workflow owns it, and re-running here refuses rather than pulling. See ALLOW_EXISTING_
# CHECKOUT below and DEPLOY.md, "Automatic deploys".
#
#   curl -fsSL https://raw.githubusercontent.com/ivangetsitdone/website/main/scripts/bootstrap.sh | bash
#
# cloud-init.yaml runs this same script at first boot, so a droplet created with it
# needs nothing typed by hand.
#
# Environment:
#   SITE_ADDRESS   hostname Caddy serves, or ":80" for plain HTTP on the IP.
#                  Default ":80", which works before DNS points here. Once the A
#                  record is right: `rm /srv/website/.env && docker compose up -d`,
#                  since ivangetsitdone.com is the built-in default.
#   INSTALL_CLAUDE "yes" also installs Claude Code. Default "no" — running the site
#                  does not need it.
#   ALLOW_EXISTING_CHECKOUT
#                  "yes" lets this script update a checkout that already exists, which
#                  it otherwise refuses to touch. For rebuilding a host whose checkout
#                  survived, not for shipping changes: pushes to main deploy themselves.
#                  Default "no".
set -euo pipefail

REPO=${REPO:-https://github.com/ivangetsitdone/website.git}
DIR=${DIR:-/srv/website}
if [ -z "${SITE_ADDRESS+x}" ] && [ -f "$DIR/.env" ]; then
  SITE_ADDRESS=$(grep '^SITE_ADDRESS=' "$DIR/.env" | cut -d= -f2- || true)
fi
SITE_ADDRESS=${SITE_ADDRESS:-:80}
# Caddy obtains a certificate for every *named* site it is given. When SITE_ADDRESS is a
# bare address, DNS has not moved here yet and neither name can answer a challenge, so the
# www redirect gets an address too rather than its real hostname.
case "$SITE_ADDRESS" in
  :*)
    WWW_ADDRESS=${WWW_ADDRESS:-:8080}
    PREVIEW_ADDRESS=${PREVIEW_ADDRESS:-:8081}
    ;;
  *)
    WWW_ADDRESS=${WWW_ADDRESS:-www.$SITE_ADDRESS}
    PREVIEW_ADDRESS=${PREVIEW_ADDRESS:-preview.$SITE_ADDRESS}
    ;;
esac
INSTALL_CLAUDE=${INSTALL_CLAUDE:-no}
ALLOW_EXISTING_CHECKOUT=${ALLOW_EXISTING_CHECKOUT:-no}
# The Compose project the live site runs under. compose.preview.yaml joins
# "${COMPOSE_PROJECT}_default", so the two must agree.
COMPOSE_PROJECT=${COMPOSE_PROJECT:-website}

log() { echo "[bootstrap] $*"; }

# $DIR is a deploy target, not a workspace. .github/workflows/deploy.yml resets it to the
# commit it is shipping and rolls back if that commit is unhealthy. Pulling into it from
# here would leave the host serving a commit no deploy run ever tested, outside that
# rollback path and invisible from the repository — the next push would silently discard
# it. Refuse before touching anything: provisioning a fresh host is this script's job.
if [ -d "$DIR/.git" ] && [ "$ALLOW_EXISTING_CHECKOUT" != yes ]; then
  log "$DIR already holds a checkout; the deploy workflow owns it from here."
  log "To ship a change, push to main. To rebuild this host anyway, re-run with"
  log "ALLOW_EXISTING_CHECKOUT=yes."
  exit 1
fi

if ! command -v docker >/dev/null; then
  log "installing Docker"
  apt-get update
  apt-get install -y ca-certificates curl git
  install -m 0755 -d /etc/apt/keyrings
  curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
  chmod a+r /etc/apt/keyrings/docker.asc
  . /etc/os-release
  echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu ${VERSION_CODENAME} stable" \
    > /etc/apt/sources.list.d/docker.list
  apt-get update
  apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
fi

# Some images ship Docker without Compose v2, which compose.yaml requires.
docker compose version >/dev/null 2>&1 || apt-get install -y docker-compose-plugin
command -v git >/dev/null || apt-get install -y git

mkdir -p "$(dirname "$DIR")"
if [ -d "$DIR/.git" ]; then
  # Only reachable with ALLOW_EXISTING_CHECKOUT=yes, checked above.
  log "updating $DIR (ALLOW_EXISTING_CHECKOUT=yes)"
  git -C "$DIR" pull --ff-only
else
  log "cloning into $DIR"
  git clone "$REPO" "$DIR"
fi

# compose.yaml reads the addresses; .env keeps them across restarts and reboots.
if ! grep -q '^SITE_ADDRESS=' "$DIR/.env" 2>/dev/null; then
  printf 'SITE_ADDRESS=%s\nWWW_ADDRESS=%s\nPREVIEW_ADDRESS=%s\n' \
    "$SITE_ADDRESS" "$WWW_ADDRESS" "$PREVIEW_ADDRESS" > "$DIR/.env"
elif ! grep -q '^PREVIEW_ADDRESS=' "$DIR/.env"; then
  printf 'PREVIEW_ADDRESS=%s\n' "$PREVIEW_ADDRESS" >> "$DIR/.env"
fi

# compose.yaml defaults to a project name that is not production's, so a stray clone
# cannot act on the live stack. This is the host that is entitled to the real one.
grep -q '^COMPOSE_PROJECT_NAME=' "$DIR/.env" ||
  printf 'COMPOSE_PROJECT_NAME=%s\n' "$COMPOSE_PROJECT" >> "$DIR/.env"

log "building and starting"
cd "$DIR"
docker compose up -d --build

if [ "$INSTALL_CLAUDE" = yes ] && ! command -v claude >/dev/null; then
  # Node 18+ is required. NodeSource rather than the distro package, whose version
  # depends on the Ubuntu release; the native installer script has failed on a bare
  # droplet, and npm was the fix, so this is the path known to work.
  log "installing Claude Code"
  curl -fsSL https://deb.nodesource.com/setup_22.x | bash -
  apt-get install -y nodejs
  npm install -g @anthropic-ai/claude-code
fi

log "finished at $(date -Is)"
docker compose ps
