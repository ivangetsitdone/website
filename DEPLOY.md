# Rebuilding this site on a fresh host

Everything the site needs is in this repository: source, templates, styles, the photo
originals, the catalogue that describes them, the Dockerfile that turns them into served
assets, and the tests that check the result. Nothing has to be copied off the old host.

Verified on 2026-09-19 by cloning this repository into an empty directory, building it
with no cache, and running the suites against the result — see **Proof** at the bottom.

## 0. The short way: cloud-init

Paste [`cloud-init.yaml`](cloud-init.yaml) into the **User data** field when creating the
droplet. At first boot it runs [`scripts/bootstrap.sh`](scripts/bootstrap.sh), which installs
Docker if the image lacks it, clones this repository to `/srv/website`, writes `.env`, and
starts the site — the droplet boots with the site already running, and nothing is typed on
the host at all. First boot takes a few minutes while the images build;
`/var/log/site-bootstrap.log` has the transcript.

On a host that does not have a checkout yet, the same script does the same job:

```sh
curl -fsSL https://raw.githubusercontent.com/ivangetsitdone/website/main/scripts/bootstrap.sh | bash
```

It does **not** install Claude Code: serving the site does not need it. Pass
`INSTALL_CLAUDE=yes` if you want it on the box.

**It refuses to run against a checkout that already exists.** Once `/srv/website` is there,
the deploy workflow owns it — it resets that checkout to the commit it is shipping and rolls
back if the commit turns out unhealthy. Pulling into it from the host would leave the site
serving a commit no run ever tested, outside that rollback path, until the next push
silently discarded it. So: to ship a change, push to `main`. To rebuild a host whose
checkout survived — disaster recovery, not deployment — re-run with
`ALLOW_EXISTING_CHECKOUT=yes`.

It comes up on plain HTTP so it does not depend on DNS having moved yet. Once the A record
points at the droplet, set the hostname and restart:

```sh
cd /srv/website
echo 'SITE_ADDRESS=ivangetsitdone.com' > .env
docker compose up -d
```

The rest of this guide is the manual equivalent, for when something needs doing by hand.

## 1. What the new host needs

- **Docker Engine and the Compose plugin.** Nothing else: Node, Python and Pillow all run
  inside the build, not on the host.
- **Ports 80 and 443 free and reachable from the internet.** Caddy needs both to obtain a
  certificate (it uses the `tls-alpn-01` challenge on 443, and redirects 80 to 443).
- **DNS already pointing at the new host** before the first start. Caddy asks Let's Encrypt
  for a certificate on boot; if the name does not resolve to this machine yet, that fails
  and retries, and the site is unreachable over HTTPS until it succeeds.
- About 2 GB of RAM. The image builds comfortably on the 2 GB droplet this was developed on.
- **Swap, on a host with under 2 GB.** `scripts/bootstrap.sh` adds a 2 GB swapfile when the
  host has less than that and none already. Without it the kernel can only reclaim page
  cache, so under pressure it thrashes on executables rather than killing anything: no OOM
  line in the log, just everything stalling for seconds. Measured here, with two agents and
  the site sharing 2 GB, `/proc/pressure/memory` went from `some avg60=53.98 full
  avg60=18.59` to `8.09` and `2.78` once swap existed — while swap itself stayed at 0 B
  used. The gain is that reclaim has somewhere to go, not that pages move.

  ```sh
  free -m                     # a Swap line with a non-zero total
  cat /proc/pressure/memory   # `full avg60` in single digits
  ```

Host tools are only needed to run the *tests*: Python 3 for the two HTTP suites, and Node 22
plus a Chromium download for the browser suite.

## 1a. Preparing a bare droplet

**Running as root is fine, and is the shorter path.** Everything below the Docker install is
optional hardening, and it is worth being honest about what it does and does not buy: the
`docker` group is root-equivalent, so a deploy account is not a security boundary, and the
application runs unprivileged inside the container either way. The real gain is switching
off root SSH login, which needs keys — so on a droplet provisioned with a root password and
no keys at all, this becomes a key-management errand that has nothing to do with getting the
site up. Deploy first; come back to it if you want it.

Order matters: the `docker` group is created by the Docker package, so a user cannot be
added to it before Docker is installed.

```sh
# Docker Engine and the Compose plugin, from Docker's own repository.
# Not `apt install docker.io` (older engine) and not the snap (sandboxed paths make
# bind mounts and compose awkward). `compose.yaml` needs Compose v2 - `docker compose`.
apt-get update
apt-get install -y ca-certificates curl
install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
chmod a+r /etc/apt/keyrings/docker.asc
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] \
https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo "$VERSION_CODENAME") stable" \
  > /etc/apt/sources.list.d/docker.list
apt-get update
apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
```

Then a deploy account, rather than running day to day as root:

```sh
id deploy || useradd -m -s /bin/bash deploy
usermod -aG sudo,docker deploy
install -d -m 700 -o deploy -g deploy /home/deploy/.ssh
passwd deploy          # sudo needs one; SSH stays key-only via PasswordAuthentication no
```

Now give the account a key. If the droplet was provisioned **with an SSH key**, root already
has one to inherit; if it was provisioned with a **root password**, `/root/.ssh/authorized_keys`
is empty or missing and there is nothing to copy — paste the public key from your own machine
instead (`cat ~/.ssh/id_ed25519.pub`, or `ssh-keygen -t ed25519` if you have none).

```sh
# Inherit root's key, only if root actually has one:
[ -s /root/.ssh/authorized_keys ] && cp /root/.ssh/authorized_keys /home/deploy/.ssh/

# Otherwise, or in addition, paste your own public key:
printf '%s\n' 'ssh-ed25519 AAAAC3... you@laptop' >> /home/deploy/.ssh/authorized_keys

chown deploy:deploy /home/deploy/.ssh/authorized_keys
chmod 600 /home/deploy/.ssh/authorized_keys
wc -c /home/deploy/.ssh/authorized_keys     # must not be 0
```

A zero-byte `authorized_keys` is the quiet failure here: ownership and modes all look right,
and SSH still answers `Permission denied (publickey)` because there is no key to match.

**The password is for `sudo`, not for logging in.** `useradd` (and `adduser
--disabled-password`) leave the account's password locked, and `sudo` then prompts for
something no one can supply. Logging in needs no password at all: `deploy` inherits root's
key from the copied `authorized_keys`, so `ssh deploy@<host>` just works. If a password on
the account is unwanted, the alternative is
`echo 'deploy ALL=(ALL) NOPASSWD:ALL' > /etc/sudoers.d/deploy && chmod 440 /etc/sudoers.d/deploy`
— though a set password means a stolen key still meets one more gate before root.

Group membership applies to new logins only, so verify from a **second** session rather
than by switching user in the first one — `su - deploy` proves nothing about SSH:

```sh
ssh deploy@<host>      # from your own machine, in a new terminal
docker ps              # no sudo: reconnecting is what picks up the docker group
sudo -v                # the password just set
```

Only once both of those work, harden SSH from the still-open root session. If the login
fails, `ssh -v` usually names it; on the host check that `/home/deploy/.ssh` is `700` and
`authorized_keys` is `600`, both owned by `deploy`.

```sh
sed -i 's/^#*PermitRootLogin.*/PermitRootLogin no/; s/^#*PasswordAuthentication.*/PasswordAuthentication no/' /etc/ssh/sshd_config
systemctl reload ssh
```

**What the deploy account is and is not for.** It is not a sandbox: anyone in the `docker`
group can mount the host filesystem into a container and become root, so treat that group
as root-equivalent. What it buys is that root SSH login can be switched off, keys are
per-person and revocable, `sudo` leaves a trail, and routine shell work stops running as
uid 0. The application itself is unprivileged either way — the container runs as uid 10001
on a read-only filesystem with `cap_drop: [ALL]` and `no-new-privileges`, whoever started
it. If a real privilege boundary is ever wanted, that is rootless Docker, which needs extra
work to bind 80 and 443 and is overkill for a single-site host.

## 2. Bring it up

```sh
# The repository is public, so HTTPS needs no key on the new host.
git clone https://github.com/ivangetsitdone/website.git
cd website
docker compose up -d --build
```

That clone gets its own Compose project, `website-local`, named by ‘name:’ in
`compose.yaml`. It is therefore safe to run on a host that is already serving the site: it
cannot stop, rebuild or delete the live containers, which run under the project `website`.
Only the deploy checkout claims that name, through `COMPOSE_PROJECT_NAME` in its `.env`.

**If DNS still points at the old host**, start on plain HTTP first, or Caddy will sit there
failing to get a certificate for a name that resolves elsewhere:

```sh
SITE_ADDRESS=:80 WWW_ADDRESS=:8080 PREVIEW_ADDRESS=:8081 docker compose up -d --build
curl -I http://<new-host-ip>/
```

Move the A record, then `docker compose down && docker compose up -d` to pick up the real
hostname and issue the certificate.

The build does three things in sequence, and fails loudly rather than quietly shipping
something wrong. All three base images are pinned by digest, so the runner and the droplet
build against the same bytes and a base image change arrives as a reviewable diff — see
[ADR-0015](docs/adr/0015-base-images-pinned-by-digest.md):

1. **Assets stage** (`node:22-alpine`) — `npm ci` against the committed lockfile, then Vite
   bundles `frontend/` into `app/static/site.js` and `site.css`.
2. **Photos stage** (`python:3.13-slim` + Pillow) — `scripts/build_photos.py` reads the
   originals in `content/`, **verifies the SHA-256 of every source against
   `app/data/portfolio.json`**, and writes metadata-free WebP derivatives into `app/media`.
   A changed or missing original stops the build. That is deliberate: it is the tripwire
   that keeps the catalogue honest.
3. **Runtime stage** — FastAPI and the generated assets, running as an unprivileged user in
   a read-only container with all capabilities dropped.

First boot takes a few minutes, most of it Pillow regenerating 81 images. Watch it with
`docker compose logs -f`.

## 2a. Automatic deploys

Once the host is up, every push to `main` redeploys it. `.github/workflows/deploy.yml` has
three jobs, in order:

| Job | Where | What |
| --- | --- | --- |
| `check` | runner | Builds the images, starts the stack on plain HTTP, runs all three suites against it. Runs on pull requests too; touches nothing live. |
| `deploy` | droplet | Resets `/srv/website` to the commit, pulls the image `check` published, waits for the app's healthcheck, reloads Caddy, asserts `HEAD` **and** the running image. Rolls back on any failure. Skipped for pull requests. |
| `verify` | runner | Re-runs the two HTTP suites against production, proving this host and its certificate serve what was tested. |

A pull request therefore runs `check` alone: a change that breaks the site is caught before
anything reaches the droplet. Reasoning is in
[ADR-0010](docs/adr/0010-continuous-deployment.md).

**What a deploy does to the live site.** The image was built and tested on the runner, so
the droplet only pulls it — and the pull happens before anything is touched, with the current
containers still serving, so a registry failure or a bad tag leaves the site exactly where it
was. The containers are replaced only once that image is on the host. The swap is still a restart, but nobody sees it: the app image is compiled at
build time so it starts in about three seconds, and Caddy holds connections and retries
across the gap rather than returning 502. Measured at 25 samples a second while the app
container is replaced: **zero errors, one request held for 3.72 seconds**. Measured again
against the live site through a real deploy: **3,482 samples, zero non-200, slowest request
0.16s**.

Replacing Caddy itself costs about **3.6 seconds of refused connections**, since nothing is
left to absorb it. That happens only when `compose.yaml` changes — a `Caddyfile` change is a
graceful reload with no interruption at all.

**If the new image will not serve**, the deploy puts the previous commit back, restarts the
image that was running minutes earlier — tagged aside before the swap, so nothing is built or
fetched — waits for it to become healthy, then fails the job. Rehearsed against a real
clone with a commit that builds cleanly and refuses to start: the site ends at HTTP 200 on
the previous commit, and the run is red. A rollback is an incident — read the log, fix
forward, push again. `git revert` and push is a normal deploy through the same gate.

**The droplet is a deploy target, not a workspace.** The deploy runs `git reset --hard`, so
anything edited on the host is discarded. `.env` is untracked and survives, which is how the
`SITE_ADDRESS` pin and the `COMPOSE_PROJECT_NAME=website` that makes this checkout the
live one stay put. Before the first automatic deploy, check there is nothing on
the host worth keeping:

```sh
ssh root@ivangetsitdone.com 'git -C /srv/website status --short'
```

**The checkout must be `/srv/website`** — where `scripts/bootstrap.sh` and `cloud-init.yaml`
put it. If an earlier deploy left it somewhere else, move it rather than pointing the
workflow at it:

```sh
ssh root@ivangetsitdone.com 'cd /srv/website 2>/dev/null || (docker compose -f ~/website/compose.yaml down && mv ~/website /srv/website)'
```

`DEPLOY_USER` (default `root`) and `DEPLOY_HOST` (default `ivangetsitdone.com`, so a rotated
droplet IP needs no change) are repository variables, if either ever needs overriding.

### One-time setup

Two repository secrets, from your own machine:

```sh
# A key only Actions uses. No passphrase — nothing can type one for it.
ssh-keygen -t ed25519 -f ~/.ssh/id_ed25519_zipllc_ci -N '' -C 'github-actions@ivangetsitdone'

# Let the droplet accept it.
ssh-copy-id -i ~/.ssh/id_ed25519_zipllc_ci.pub root@ivangetsitdone.com

# Hand GitHub the private half, and pin the droplet's host key so the runner cannot be
# redirected to some other machine.
gh secret set DEPLOY_KEY -R ivangetsitdone/website < ~/.ssh/id_ed25519_zipllc_ci
ssh-keyscan -t ed25519 ivangetsitdone.com |
  gh secret set DEPLOY_KNOWN_HOSTS -R ivangetsitdone/website
```

Without `gh`, the same two values go in by hand at **Settings → Secrets and variables →
Actions → New repository secret**. `DEPLOY_KEY` is the whole private key file including its
`-----BEGIN`/`-----END` lines; `DEPLOY_KNOWN_HOSTS` is the one-line output of `ssh-keyscan`.

Then push anything, or run the workflow by hand from the **Actions** tab. The run fails on
its first step, before touching the droplet, if either secret is missing.

### When it goes wrong

- **`Permission denied (publickey)`** — the public half is not in the droplet's
  `authorized_keys`, or `DEPLOY_KEY` was pasted without its trailing newline.
- **`Host key verification failed`** — the droplet was rebuilt and its host key changed.
  Re-run the `ssh-keyscan` line above. This is the check working, not misfiring.
- **`/srv/website: No such file or directory`** — the droplet's checkout is elsewhere. Move
  it, as above; the path is fixed on purpose.
- **A run on `main` shows `cancelled`** — normal when pushes land faster than deploys. A
  newly queued run cancels any run in its group that is still *pending*; `cancel-in-progress:
  false` only protects the one actually running, so no deploy is ever interrupted part-way.
  Nothing is lost either: the deploy resets to the commit that triggered it, so the later
  run ships the skipped commit's content too, and the `HEAD` assertion proves it.
- **`rolling back to <sha>`** — the new build never became healthy. The job prints
  `docker compose logs` first; that is where the reason is. The site is back on the previous
  commit by the time the job goes red.
- **`could not pull <image>; the site is untouched on <sha>`** — the registry, a bad tag, or
  a half-published image. Nothing was changed; the previous commit is still serving. Re-run
  the job once the image is there.
- **`the rollback is unhealthy too - the site is down`** — the rare bad one. The image that
  was serving minutes ago no longer starts, which points at the host rather than the code:
  check `df -h /` in the same log, then `docker compose logs` on the droplet.
- **A red `verify` or `browser` job** — the deploy happened and the live site broke. Fix
  forward, or `git revert` and push, which deploys the revert.
- Rebuilding the droplet resets all of this: re-add the public key and refresh the host key.

## 2b. Preview deploys

The mutable `preview` branch identifies a candidate for owner review at
<https://preview.ivangetsitdone.com>, but it does **not** define or trigger its own deployment.
The trusted Preview workflow is dispatched from `main` with the exact current preview SHA.
Candidate tests run without deployment secrets.

On the host, the separate preview key belongs to the dedicated `preview-deploy` system user and
is restricted to a forced `/usr/local/sbin/website-preview-deploy` command. It cannot open an
interactive shell or choose another command. The deployer is installed only after a trusted
`main` production deploy is healthy. The candidate image is built and tested on an isolated
GitHub runner, capped at 600 MB and streamed with a SHA-256 checksum. The host verifies the
checksum and exact `origin/preview` SHA, loads the image, and applies the trusted
`/srv/website/compose.preview.yaml`. Candidate Dockerfiles never execute on the production
host, and the runtime has CPU, memory and PID limits in addition to its read-only filesystem.

The preview app publishes no host port. It joins the existing `website_default` Docker network
as `preview-app`; the production Caddy container proxies the preview hostname to that alias.
Responses carry `X-Robots-Tag: noindex, nofollow, noarchive`. This discourages indexing but is
not access control, so deploy only photos already authorized for public disclosure. Production
continues to serve `main` from `/srv/website` and the `app` service.

### One-time preview setup

1. Create an **A** record for `preview.ivangetsitdone.com` pointing to the same droplet IP as
   the bare domain. Keep it **DNS-only**, not Cloudflare-proxied, so Caddy can complete its
   TLS-ALPN certificate challenge.
2. Create a GitHub environment named `preview`, restrict its deployment branches to selected
   branch `main`, and optionally add required reviewers. Store the private half of the dedicated
   preview key as `PREVIEW_DEPLOY_KEY` in that environment. Its matching public half is tracked
   at `deploy/preview_deploy.pub`.
3. Merge the preview infrastructure through the normal production workflow. After production
   is healthy, that deploy installs the root-owned forced command, provisions the dedicated
   `preview-deploy` system user, and writes the reviewed public key to the AuthorizedKeysFile
   paths reported by the live SSH configuration. Any earlier preview key under root is removed.
4. Enable the public Caddy hostname only after DNS resolves:

```sh
gh variable set PREVIEW_ADDRESS -R ivangetsitdone/website \
  --body preview.ivangetsitdone.com
```

The next `main` deployment writes that value to the host's `.env`. Until the variable is set,
preview stays on unpublished internal address `:8081`, so a missing DNS record cannot trigger
certificate attempts. The existing repository `DEPLOY_KNOWN_HOSTS` secret is reused only for
host-key verification; the production private key is never exposed to the preview workflow.

To rotate the preview key, generate a new pair, replace `deploy/preview_deploy.pub` through a
reviewed production PR, and update the environment secret before deploying another preview.

### Deploy a reviewed candidate

```sh
git push --force-with-lease origin HEAD:preview
candidate=$(git rev-parse HEAD)
gh workflow run Preview --repo ivangetsitdone/website --ref main -f candidate_sha="$candidate"
gh run list --workflow Preview --limit 1
```

The workflow confirms the requested SHA is the current `preview` ref, runs all three suites and
builds the capped candidate image on a runner, then asks the forced-command host deployer to
verify and load that tested image under trusted runtime policy. It finally reruns the HTTP and
browser suites against the HTTPS preview. A green preview is evidence for review, not permission
to publish; approved work still goes through a pull request to `main` and the production
workflow.

## 2c. The development site

`dev.ivangetsitdone.com` serves the checkout at `/srv/website-dev`, live: save a template and
it is on that URL on the next request. Reasoning and its limits are in
[ADR-0017](docs/adr/0017-development-site-on-one-host.md).

It is one container — `compose.dev.yaml`, project `website-dev`, no Caddy and no published
ports. Production's Caddy proxies it on the `dev-app` alias, the same arrangement preview
uses, and adds `X-Robots-Tag: noindex`.

**What is live, and what is not.** `app/main.py`, `app/templates`, `app/data` and `app/print`
are mounted from the tree. `app/static`, `app/media` and everything built from `frontend/` are
**not**: they are generated and git-ignored, and come from `APP_IMAGE`. So copy, markup and
routing changes are instant; stylesheet, script and photograph changes appear after a deploy.

### One-time setup on the host

The tree is root-owned and shared with the assistant, which may write `app/` and `frontend/`
only — the ACL is the boundary, and the skill that says so is worth nothing without it.

```sh
git clone https://github.com/ivangetsitdone/website.git /srv/website-dev
cd /srv/website-dev
printf 'COMPOSE_PROJECT_NAME=website-dev\nCOMPOSE_FILE=compose.dev.yaml\nAPP_IMAGE=%s\n' \
  "$(ssh root@ivangetsitdone.com 'grep ^APP_IMAGE= /srv/website/.env | cut -d= -f2-')" > .env

setfacl -m u:hermes:rx /srv/website-dev
setfacl -R -m u:hermes:rwx -m d:u:hermes:rwx /srv/website-dev/app /srv/website-dev/frontend

docker compose up -d
```

`DEV_ADDRESS` reaches production's Caddy through its `.env`, which the deploy maintains; the
route exists from the next deploy onwards.

**Hermes reads its skills from this checkout.** The four skills in `.hermes/skills/` load by
reference, through Hermes' `skills.external_dirs` setting, so a `git pull` updates them and
the assistant cannot edit them: the directory is root-owned, with no ACL. Two details matter.
The gateway is the **system** unit `hermes-gateway.service`, whose `HERMES_HOME` is
`/var/lib/hermes`; and the `hermes` command run as that user defaults to a second, unused
profile at `/var/lib/hermes/.hermes`, so a setting written through the CLI without
`HERMES_HOME` lands in the wrong file. Edit the live config directly (it is `hermes`-owned,
mode 0600; keep it that way) and restart the gateway:

```yaml
# /var/lib/hermes/config.yaml
skills:
  external_dirs:
    - /srv/website-dev/.hermes/skills
```

```sh
systemctl restart hermes-gateway
sudo -u hermes -H env HERMES_HOME=/var/lib/hermes hermes skills list | grep -Ew 'site|todo|recent|ship'
```

Hermes indexes an external directory by path, so each of the four appears under a category
of its own name. The trusted-project mechanism (`hermes skills trust`) is not used: it keys
off the session's working directory, which for the gateway is `/var/lib/hermes`, not the
checkout.

### Keeping it current

```sh
cd /srv/website-dev && git pull --ff-only     # source
docker compose pull && docker compose up -d   # dependencies, after a requirements change
```

A dependency change is the one case needing the second line: `APP_IMAGE` supplies the
installed packages, and the tree only supplies the source.

## 3. Serving a different domain

Three places name the domain, and they have to agree:

| What | Where | Default |
| --- | --- | --- |
| Certificate + virtual host | `SITE_ADDRESS` env var, read by `compose.yaml` → `Caddyfile` | `ivangetsitdone.com` |
| The www redirect's own host | `WWW_ADDRESS`, same route | `www.ivangetsitdone.com` |
| `<link rel="canonical">` and the `canonical` context value | `app/main.py`, in the `page()` route | `https://ivangetsitdone.com/...` |
| Default target of all three test suites | `tests/smoke.py`, `tests/portfolio_http.py`, `tests/browser/playwright.config.js` | same |

For a new domain, set `SITE_ADDRESS` (an `.env` file beside `compose.yaml` works, and is
git-ignored) and edit the canonical string in `app/main.py`. Canonical URLs pointing at a
domain you no longer serve will quietly tell search engines the wrong thing, so do not skip
the second one.

For a **local HTTP-only preview** with no certificate at all:

```sh
SITE_ADDRESS=:80 WWW_ADDRESS=:8080 PREVIEW_ADDRESS=:8081 docker compose up -d
```

## 4. Verify, in order

```sh
curl -fsS https://<your-domain>/healthz            # {"status":"ok"}
python3 tests/smoke.py https://<your-domain>       # pages, headers, licensing guardrails
python3 tests/portfolio_http.py https://<your-domain>   # 38 sources, 81 generated assets, isolation
cd tests/browser && npm ci && PLAYWRIGHT_BROWSERS_PATH=../../recovery/browsers npx playwright install chromium
BASE_URL=https://<your-domain> npm test            # 30 tests, desktop + mobile, axe WCAG A/AA
```

The HTTP suites need no dependencies at all — they are standard-library only. The browser
suite downloads Chromium into git-ignored `recovery/browsers`.

`tests/smoke.py` is also the licensing guardrail: it fails if a regulated-trade word appears
in the blocks that offer work, if the CCB disclosure goes missing from any page, or if a
rate appears in the cost panel. Run it after any copy change, not just after a deploy.

## 5. What does not come from this repository

- **The TLS certificate.** It lives in the `caddy_data` volume and is re-issued
  automatically on the new host. Nothing to copy; just do not run `docker compose down -v`,
  which would delete it and burn a rate-limited re-issue.
- **`app/static` and `app/media`.** Generated during the build, git-ignored on purpose.
- **`recovery/`.** Local diagnostics, screenshots and Playwright browsers. Disposable.
- **The deployed image.** Since [ADR-0016](docs/adr/0016-deploy-the-tested-image.md) the
  droplet runs `ghcr.io/ivangetsitdone/website:<sha>`, published by the `check` job. The host
  builds nothing; it holds the tag it is serving and the one a rollback would need.

### What the host carries beyond this repository

Verified on the live droplet, 2026-09-21; the three Hermes rows on 2026-09-25. This list used to say "there is nothing", which
stopped being true when preview deployment landed:

| On the host | What it is |
| --- | --- |
| `preview-deploy` (uid 1000) | System user in the **`docker` group**, which is root-equivalent. Created and maintained by every production deploy. |
| `/usr/local/sbin/website-preview-deploy` | Root-owned forced command the preview key is restricted to. Installed from `scripts/deploy_preview.sh`. |
| `/srv/website-preview` | The preview checkout, owned by `preview-deploy`. |
| `/root/.ssh/authorized_keys` | 2 entries. One is the CI deploy key; confirm what the other is before handing the host over. |
| `/home/preview-deploy/.ssh/authorized_keys` | 1 restricted entry, rewritten on every deploy. |
| `website_caddy_data`, `website_caddy_config` | Docker volumes. The first holds the TLS certificate — see above. |
| `/srv/website/.env` | Untracked, and load-bearing: `SITE_ADDRESS`, `PREVIEW_ADDRESS`, `COMPOSE_PROJECT_NAME`, `APP_IMAGE`. |
| `PermitRootLogin yes` | Root SSH is enabled. §1a describes turning it off; it has not been done. |
| `hermes` (uid 997) | Unprivileged system user the owner's assistant runs as: no sudo, not in `docker`. ACLs on `/srv/website-dev/{app,frontend,.git}` are its only write access to the tree. |
| `/var/lib/hermes` | Its home, and `HERMES_HOME` of the system unit `hermes-gateway.service` (the user unit of the same name under its `.config` is disabled and stale). `config.yaml` there is private and carries `skills.external_dirs` (§2c). |
| `/srv/website-dev` | The development checkout, root-owned and served live (§2c). |

### Handing the site to someone else

None of the following is in the repository, and none transfers by cloning it.

**Rotate, in this order** — add the new credential before removing the old one, so there is
never a window with no working key:

1. New owner generates a deploy keypair; add the public half to the droplet's
   `authorized_keys` **alongside** the existing one.
2. Update `DEPLOY_KEY` and `DEPLOY_KNOWN_HOSTS`, push a trivial change, confirm a green deploy.
3. Only now remove the outgoing key from `authorized_keys`.
4. Rotate `PREVIEW_DEPLOY_KEY` the same way: new pair, `deploy/preview_deploy.pub` replaced
   through a reviewed PR, environment secret updated, then a preview deploy to confirm.
5. Revoke any personal access token used for repository automation.
6. Re-run `ssh-keyscan` if the droplet is ever rebuilt.

**Transfer or confirm ownership of:** the droplet and its billing account; the
`ivangetsitdone.com` registration and DNS; the GitHub account owning this repository and the
`ghcr.io` package published from it.

**Note what the credentials actually grant.** `DEPLOY_KEY` is root SSH on the droplet.
`PREVIEW_DEPLOY_KEY` is restricted to a forced command, but `preview-deploy` is in the
`docker` group, and that group is root-equivalent — §1a is explicit about this. Both are
full access to the host in practice.

## 6. Proof this works

On 2026-09-19, from commit `5cd8d03`:

1. `git clone` of this repository into an empty directory — 26 MB including history.
2. `docker compose build` with a fresh project name: all three stages completed, including
   the SHA-256 verification of all 35 photo sources, the portrait and both brand originals.
3. The stack came up (Caddy on a scratch HTTP port, since the live site held 80/443) and:
   - all six pages returned 200, as did `/static/site.css`, `/static/site.js`,
     `/media/logo.webp`, `/media/card.webp`, `/media/p42-full.webp`,
     `/media/ivan-pineda.webp` and `/print/honey-do-list.svg`;
   - `tests/smoke.py` passed against it;
   - `tests/portfolio_http.py` passed: 35 catalogue sources, 70 project WebPs plus the
     portrait and four brand files, 8.70 MiB;
   - the 30-test browser suite passed against it.

One note from that run: hitting the app container directly, bypassing Caddy, fails the
`X-Content-Type-Options: nosniff` assertion — that header is set by the proxy, so always
test through Caddy rather than against port 8000.
