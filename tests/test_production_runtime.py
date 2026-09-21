"""Production runtime policy: the live services are bounded, and bounded at least as
well as the preview candidate they share a host with.

Numbers come from the rendered Compose config rather than the file text, so a change
that happens to keep the same words but a different effective value still fails.
"""

import json
import subprocess
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


if __name__ == "__main__":
    unittest.main()
