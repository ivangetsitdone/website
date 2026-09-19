# 8. Docker Compose and Caddy on a single droplet

Status: accepted

## Context

One low-traffic site, one owner, no ops team. It needs HTTPS, it needs to survive a reboot,
and it needs to be reconstructible after the host is destroyed — which has already happened
more than once.

## Decision

Two containers via Compose: the app, and Caddy as the reverse proxy. Caddy obtains and
renews Let's Encrypt certificates automatically using the `tls-alpn-01` challenge. The
repository is the only artefact: `scripts/bootstrap.sh` installs Docker if missing, clones,
and starts the stack, and `cloud-init.yaml` runs that same script at first boot so a
droplet created with it needs nothing typed by hand.

## Consequences

- **The DNS record must be DNS-only, not proxied.** A Cloudflare proxied record terminates
  TLS itself and the `tls-alpn-01` challenge can never complete.
- **DNS must resolve to the host before it starts with a hostname set.** The bootstrap
  therefore starts on plain HTTP (`SITE_ADDRESS=:80`), so a record that has not moved yet
  cannot wedge the first boot on a failing certificate request.
- Certificates live in the `caddy_data` volume and are re-issued on a new host. Never run
  `docker compose down -v`; it deletes them and burns a rate-limited re-issue.
- Running as root on the droplet is acceptable. A deploy account is optional hardening, and
  the `docker` group is root-equivalent anyway, so it is not a security boundary. The
  application is unprivileged regardless: uid 10001, read-only filesystem, capabilities
  dropped.
- Three places name the domain and must agree — `SITE_ADDRESS`, the canonical URL in
  `app/main.py`, and the test defaults. [DEPLOY.md](../../DEPLOY.md) has the table.
