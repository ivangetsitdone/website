"""Every image pulled from a registry is pinned by digest.

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


if __name__ == "__main__":
    unittest.main()
