"""Production has exactly one way in: a push to main.

deploy.yml deploys on push to main and runs its gate on pull requests; it has no
workflow_dispatch trigger, so nobody can deploy an arbitrary ref by hand. The preview
suite used to assert this (retired in ADR-0019); it outlives preview because it is about
production.
"""

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WORKFLOW = (ROOT / ".github/workflows/deploy.yml").read_text()


class OneWayIn(unittest.TestCase):
    def test_no_manual_dispatch(self):
        self.assertNotIn("workflow_dispatch", WORKFLOW)

    def test_deploys_only_from_main(self):
        head = WORKFLOW.split("jobs:", 1)[0]
        self.assertRegex(head, r"push:\n\s+branches:\s*\[main\]")
        self.assertIn("pull_request:", head)

    def test_the_gate_job_is_called_check(self):
        """The branch ruleset requires a status check named `check` (ADR-0018)."""
        block = re.search(r"^  check:\n(.*?)(?=^  [A-Za-z_-]+:\n|\Z)", WORKFLOW, re.S | re.M)
        self.assertIsNotNone(block)
        self.assertNotRegex(block.group(1), r"^    name:")

    def test_nothing_preview_is_left(self):
        for name in ("compose.preview.yaml", "scripts/deploy_preview.sh",
                     ".github/workflows/preview.yml", "deploy/preview_deploy.pub"):
            self.assertFalse((ROOT / name).exists(), f"{name} should be gone (ADR-0019)")


if __name__ == "__main__":
    unittest.main()
