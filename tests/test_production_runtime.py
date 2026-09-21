"""Production runtime policy: the live services are bounded, bounded at least as well
as the preview candidate they share a host with, and reachable as a Compose project only
from the checkout entitled to them.

Numbers come from the rendered Compose config rather than the file text, so a change
that happens to keep the same words but a different effective value still fails.
"""

import json
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MIB = 1024 * 1024


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


class ProductionRuntimeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.config = rendered("compose.yaml")
        cls.app = cls.config["services"]["app"]
        cls.caddy = cls.config["services"]["caddy"]

    def test_app_memory_is_bounded(self):
        """Unbounded, the kernel picks the OOM victim, and it need not be the app."""
        self.assertEqual(int(self.app["mem_limit"]), 512 * MIB)

    def test_app_processes_and_scratch_space_are_bounded(self):
        self.assertEqual(self.app["pids_limit"], 128)
        self.assertEqual(self.app["tmpfs"], ["/tmp:size=64m,mode=1777"])

    def test_app_keeps_the_whole_cpu(self):
        """Deliberate asymmetry: preview is capped so it cannot starve production."""
        self.assertIsNone(self.app.get("cpus"))

    def test_caddy_is_bounded_too(self):
        """Losing the proxy takes the site off the internet, not just one service."""
        self.assertEqual(int(self.caddy["mem_limit"]), 128 * MIB)
        self.assertEqual(self.caddy["pids_limit"], 64)

    def test_logs_rotate_on_both_services(self):
        for name, service in (("app", self.app), ("caddy", self.caddy)):
            with self.subTest(service=name):
                self.assertEqual(
                    service["logging"]["options"],
                    {"max-file": "3", "max-size": "10m"},
                    "json-file never rotates on its own",
                )

    def test_existing_hardening_is_still_in_place(self):
        self.assertIs(self.app["read_only"], True)
        self.assertEqual(self.app["cap_drop"], ["ALL"])
        self.assertEqual(self.app["security_opt"], ["no-new-privileges:true"])
        self.assertEqual(self.app["restart"], "unless-stopped")
        self.assertEqual(self.caddy["restart"], "unless-stopped")

    def test_production_is_not_tighter_than_preview(self):
        """They share a host. The candidate must never out-resource the live site."""
        preview = rendered(
            "compose.preview.yaml",
            PREVIEW_IMAGE="website-preview-candidate:" + "a" * 40,
        )["services"]["preview-app"]
        self.assertGreaterEqual(
            int(self.app["mem_limit"]),
            int(preview["mem_limit"]),
            "preview may not be given more memory than production",
        )
        self.assertGreaterEqual(self.app["pids_limit"], preview["pids_limit"])


class ComposeProjectIsolationTests(unittest.TestCase):
    """`docker compose` in a development clone must not reach the live containers.

    Compose names a project after its directory unless told otherwise, so a clone in any
    directory called `website` inherited production's project. The default in the file is
    deliberately not production's name; production opts back in through its untracked .env.
    """

    DEPLOY = (ROOT / ".github/workflows/deploy.yml").read_text()
    PRODUCTION_PROJECT = "website"

    def rendered_from(self, project_dir):
        result = subprocess.run(
            [
                "docker", "compose",
                "-f", str(ROOT / "compose.yaml"),
                "--project-directory", str(project_dir),
                "config", "--format", "json",
            ],
            text=True,
            capture_output=True,
            env={"PATH": "/usr/bin:/bin"},
        )
        if result.returncode != 0:
            raise AssertionError(result.stderr)
        return json.loads(result.stdout)["name"]

    def test_a_clone_does_not_inherit_the_production_project(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertNotEqual(self.rendered_from(tmp), self.PRODUCTION_PROJECT)

    def test_the_default_does_not_depend_on_the_directory_name(self):
        """A clone into a directory called `website` was the whole bug."""
        with tempfile.TemporaryDirectory() as tmp:
            looks_like_production = Path(tmp) / self.PRODUCTION_PROJECT
            looks_like_production.mkdir()
            self.assertNotEqual(
                self.rendered_from(looks_like_production), self.PRODUCTION_PROJECT
            )

    def test_production_opts_back_in_through_its_env_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / ".env").write_text(
                f"COMPOSE_PROJECT_NAME={self.PRODUCTION_PROJECT}\n"
            )
            self.assertEqual(self.rendered_from(tmp), self.PRODUCTION_PROJECT)

    def test_the_preview_network_still_names_the_production_project(self):
        """compose.preview.yaml joins `<project>_default`; rename one, break the other."""
        preview = (ROOT / "compose.preview.yaml").read_text()
        self.assertIn(f"name: {self.PRODUCTION_PROJECT}_default", preview)

    def test_bootstrap_gives_a_fresh_host_the_production_project(self):
        bootstrap = (ROOT / "scripts/bootstrap.sh").read_text()
        self.assertIn("COMPOSE_PROJECT_NAME=", bootstrap)
        self.assertIn(f"COMPOSE_PROJECT=${{COMPOSE_PROJECT:-{self.PRODUCTION_PROJECT}}}", bootstrap)

    def test_the_deploy_pins_the_project_before_it_runs_compose(self):
        remote = self.DEPLOY[self.DEPLOY.index("<<'REMOTE'"):self.DEPLOY.index("          REMOTE")]
        pin = remote.index(f"COMPOSE_PROJECT_NAME={self.PRODUCTION_PROJECT}")
        # Whatever the deploy runs, the project must already be pinned. Matching the first
        # executed compose statement rather than a literal command keeps this honest when
        # the deploy changes shape — as it did when the droplet stopped building.
        executed = min(
            remote.index(statement)
            for statement in (
                "docker compose up -d --no-build || roll_back",
                "wait_healthy ||",
                "docker compose exec -T caddy",
            )
        )
        self.assertLess(pin, executed, "the project must be pinned before any compose call")


if __name__ == "__main__":
    unittest.main()
