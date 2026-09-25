"""The development site serves the working tree; production serves the image.

One host runs both, so most of what matters here is separation: the dev stack must not
publish ports production holds, must not be reachable as production's project, and
production's configuration must contain none of the development machinery.
"""

import json
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MIB = 1024 * 1024
IMAGE = "ghcr.io/ivangetsitdone/website:" + "a" * 40


def rendered(compose_file, **env):
    result = subprocess.run(
        ["docker", "compose", "-f", compose_file, "config", "--format", "json"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        env={"PATH": "/usr/bin:/bin", **env},
    )
    if result.returncode != 0:
        raise AssertionError(result.stderr)
    return json.loads(result.stdout)


class DevStackTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.config = rendered("compose.dev.yaml", APP_IMAGE=IMAGE)
        cls.dev = cls.config["services"]["dev-app"]

    def test_it_runs_the_image_production_runs(self):
        """Only the source is local; the dependencies are the ones that were tested."""
        self.assertEqual(self.dev["image"], IMAGE)
        self.assertNotIn("build", self.dev)

    def test_it_reloads_from_the_working_tree(self):
        self.assertIn("--reload", self.dev["command"])

    def test_only_source_is_mounted(self):
        """app/static and app/media are generated and git-ignored: mounting the tree over
        them would serve a site with no stylesheet, no script and no photographs."""
        mounted = {v["source"].rsplit("/app/", 1)[-1] for v in self.dev["volumes"]}
        self.assertEqual(mounted, {"main.py", "templates", "data", "print"})
        for generated in ("static", "media"):
            with self.subTest(directory=generated):
                self.assertNotIn(generated, mounted)

    def test_the_source_mounts_are_read_only(self):
        for volume in self.dev["volumes"]:
            with self.subTest(source=volume["source"]):
                self.assertTrue(volume.get("read_only"), "the dev site must not edit the tree")

    def test_it_publishes_no_ports(self):
        """Production holds 80 and 443 on this host; dev is proxied on an internal alias."""
        self.assertNotIn("ports", self.dev)
        self.assertEqual(self.dev["networks"]["website"]["aliases"], ["dev-app"])
        self.assertIs(self.config["networks"]["website"]["external"], True)
        self.assertEqual(self.config["networks"]["website"]["name"], "website_default")

    def test_it_cannot_starve_production(self):
        self.assertLessEqual(int(self.dev["mem_limit"]), 256 * MIB)
        self.assertLessEqual(self.dev["cpus"], 0.5)
        self.assertEqual(self.dev["pids_limit"], 128)

    def test_the_hardening_survives(self):
        self.assertIs(self.dev["read_only"], True)
        self.assertEqual(self.dev["cap_drop"], ["ALL"])
        self.assertEqual(self.dev["security_opt"], ["no-new-privileges:true"])


class ProductionIsNotDevTests(unittest.TestCase):
    """The two configurations run on one machine. Nothing may leak between them."""

    COMPOSE = (ROOT / "compose.yaml").read_text()
    DEPLOY = (ROOT / ".github/workflows/deploy.yml").read_text()

    def test_production_compose_has_no_dev_machinery(self):
        for leak in ("--reload", "./app:", "/srv/app"):
            with self.subTest(leak=leak):
                self.assertNotIn(leak, self.COMPOSE)

    def test_the_deploy_strips_compose_file_from_production(self):
        """A COMPOSE_FILE line in production's .env would layer the overlay onto the live
        stack. It is removed every run rather than trusted to be absent."""
        remote = self.DEPLOY[self.DEPLOY.index("<<'REMOTE'"):self.DEPLOY.index("          REMOTE")]
        self.assertIn("sed -i '/^COMPOSE_FILE=/d' .env", remote)
        self.assertLess(
            remote.index("COMPOSE_FILE"),
            remote.index("docker compose up -d --no-build"),
            "strip it before compose runs, not after",
        )

    def test_the_deploy_validates_the_dev_address(self):
        remote = self.DEPLOY[self.DEPLOY.index("<<'REMOTE'"):self.DEPLOY.index("          REMOTE")]
        self.assertIn("invalid DEV_ADDRESS", remote)
        self.assertIn(":8083|dev.ivangetsitdone.com", remote)

    def test_the_dev_site_is_unindexed(self):
        """It is the same content as production; production must be the indexed copy."""
        caddy = (ROOT / "Caddyfile").read_text()
        dev_block = caddy[caddy.index("{$DEV_ADDRESS"):]
        dev_block = dev_block[:dev_block.index("\n}")]
        self.assertIn('X-Robots-Tag "noindex, nofollow, noarchive"', dev_block)
        self.assertIn("reverse_proxy dev-app:8000", dev_block)

    def test_the_dev_address_defaults_to_an_unpublished_port(self):
        """A clone or a runner has no DNS for the dev hostname and must not ask for a cert."""
        self.assertIn("DEV_ADDRESS: ${DEV_ADDRESS:-:8083}", self.COMPOSE)


if __name__ == "__main__":
    unittest.main()
