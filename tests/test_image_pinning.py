"""Every image pulled from a registry is pinned by digest, and the image that deploys
is the one the gate tested.

A tag is a moving target: the runner tests one image and the droplet can build against
another, and a base image change reaches production without appearing in any diff.
"""

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DIGEST = re.compile(r"@sha256:[a-f0-9]{64}\b")


class ImagePinningTests(unittest.TestCase):
    def test_every_dockerfile_base_is_pinned(self):
        froms = [
            line for line in (ROOT / "Dockerfile").read_text().splitlines()
            if line.startswith("FROM ")
        ]
        self.assertTrue(froms, "no FROM lines found")
        for line in froms:
            with self.subTest(line=line):
                self.assertRegex(line, DIGEST)

    def test_compose_images_are_pinned(self):
        """compose.preview.yaml's image is built locally and interpolated, not pulled."""
        for name in ("compose.yaml", "compose.preview.yaml"):
            for line in (ROOT / name).read_text().splitlines():
                stripped = line.strip()
                if not stripped.startswith("image:"):
                    continue
                value = stripped.split("image:", 1)[1].strip()
                with self.subTest(file=name, image=value):
                    if value.startswith("${"):
                        continue
                    self.assertRegex(value, DIGEST)

    def test_the_two_python_stages_agree(self):
        """Different digests across stages would build the photos on one and run on another."""
        pins = re.findall(r"^FROM (python:[^\s]+)", (ROOT / "Dockerfile").read_text(), re.M)
        self.assertEqual(len(set(pins)), 1, f"python stages disagree: {pins}")

    def test_dependabot_watches_the_dockerfile(self):
        config = (ROOT / ".github/dependabot.yml").read_text()
        self.assertIn("package-ecosystem: docker", config)

    def test_the_audit_watches_what_dependabot_cannot(self):
        """Compose files are outside the docker ecosystem, so a pin there needs its own watch."""
        audit = (ROOT / ".github/workflows/audit.yml").read_text()
        self.assertIn("images:", audit)
        self.assertIn("compose.yaml", audit)
        self.assertIn("imagetools inspect", audit)


class ImageProvenanceTests(unittest.TestCase):
    """What ships should be the artefact that passed, not a rebuild that ought to match it."""

    COMPOSE = (ROOT / "compose.yaml").read_text()
    DEPLOY = (ROOT / ".github/workflows/deploy.yml").read_text()

    def test_the_app_service_can_be_built_or_supplied(self):
        """`build` for local development, `image` so production can run --no-build."""
        app = self.COMPOSE[self.COMPOSE.index("  app:"):self.COMPOSE.index("  caddy:")]
        self.assertIn("build: .", app)
        self.assertRegex(app, r"image: \$\{APP_IMAGE:-[^}]+\}")

    def test_the_default_image_is_local(self):
        """A checkout with no APP_IMAGE must never pull a deploy image."""
        default = re.search(r"image: \$\{APP_IMAGE:-([^}]+)\}", self.COMPOSE).group(1)
        self.assertNotIn("/", default, f"{default} looks like a registry reference")
        self.assertNotIn(".", default.split(":")[0])

    def test_the_gate_tags_what_it_builds(self):
        self.assertIn("APP_IMAGE=%s", self.DEPLOY)
        self.assertIn('"$IMAGE:$GITHUB_SHA"', self.DEPLOY)

    def test_the_image_is_published_only_after_the_suites_pass(self):
        publish = self.DEPLOY.index("Publish the tested image")
        for suite in ("Browser suite, desktop and mobile", "portfolio_http.py", "smoke.py"):
            with self.subTest(suite=suite):
                self.assertLess(self.DEPLOY.index(suite), publish)

    def test_pull_requests_do_not_publish(self):
        publish = self.DEPLOY[self.DEPLOY.index("Publish the tested image"):]
        self.assertIn("if: github.event_name != 'pull_request'", publish[:400])

    REMOTE = DEPLOY[DEPLOY.index("<<'REMOTE'"):DEPLOY.index("          REMOTE")]

    def test_the_droplet_does_not_build(self):
        """The whole point: ship the artefact that was tested, not a rebuild of it."""
        builds = [
            line.strip() for line in self.REMOTE.splitlines()
            if line.strip().startswith("docker") and "--build" in line and "--no-build" not in line
        ]
        self.assertEqual(builds, [], f"the droplet still builds: {builds}")

    def test_the_image_is_pulled_before_anything_changes(self):
        """A registry failure must leave the site serving the previous commit."""
        self.assertLess(
            self.REMOTE.index("docker pull"),
            self.REMOTE.index("docker compose up"),
        )

    def test_the_rollback_does_not_build(self):
        rollback = self.REMOTE[self.REMOTE.index("roll_back() {"):]
        rollback = rollback[:rollback.index("\n          }")]
        self.assertIn("--no-build", rollback)
        self.assertIn("set_app_image", rollback)

    def test_the_host_validates_the_image_it_is_told_to_run(self):
        self.assertIn("ghcr\\.io/[a-z0-9._/-]+:[0-9a-f]{40}", self.REMOTE)

    def test_the_deploy_asserts_what_it_is_serving(self):
        """HEAD alone no longer proves it: the image is a separate fact now."""
        self.assertIn('running=$(docker inspect -f \'{{.Config.Image}}\'', self.REMOTE)
        self.assertIn('[ "$running" = "$image" ]', self.REMOTE)


    def test_the_image_name_is_not_hardcoded(self):
        """A fork or a whitelabel instance publishes under its own repository."""
        self.assertIn("IMAGE: ghcr.io/${{ github.repository }}", self.DEPLOY)


if __name__ == "__main__":
    unittest.main()
