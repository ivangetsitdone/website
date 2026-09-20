"""Validate the isolated preview deployment contract."""

import json
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


class PreviewConfigTests(unittest.TestCase):
    def test_preview_compose_contract(self):
        compose = ROOT / "compose.preview.yaml"
        self.assertTrue(compose.is_file(), "compose.preview.yaml is missing")
        result = subprocess.run(
            ["docker", "compose", "-f", str(compose), "config", "--format", "json"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            env={"PREVIEW_IMAGE": "website-preview-candidate:" + "a" * 40},
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        config = json.loads(result.stdout)
        service = config["services"]["preview-app"]
        self.assertEqual(service["image"], "website-preview-candidate:" + "a" * 40)
        self.assertNotIn("build", service)
        self.assertEqual(service["mem_limit"], "402653184")
        self.assertEqual(service["pids_limit"], 128)
        self.assertEqual(service["cpus"], 0.75)
        self.assertEqual(service["tmpfs"], ["/tmp:size=64m,mode=1777"])
        self.assertEqual(service["logging"]["options"], {"max-file": "3", "max-size": "10m"})
        self.assertIs(service["read_only"], True)
        self.assertEqual(service["restart"], "unless-stopped")
        self.assertEqual(service["cap_drop"], ["ALL"])
        self.assertEqual(service["security_opt"], ["no-new-privileges:true"])
        self.assertEqual(service["networks"]["website"]["aliases"], ["preview-app"])
        self.assertIs(config["networks"]["website"]["external"], True)
        self.assertEqual(config["networks"]["website"]["name"], "website_default")
        self.assertNotIn("ports", service)

    def test_caddy_routes_preview_without_indexing(self):
        caddy = (ROOT / "Caddyfile").read_text()
        self.assertIn("{$PREVIEW_ADDRESS:preview.ivangetsitdone.com}", caddy)
        self.assertIn("reverse_proxy preview-app:8000", caddy)
        self.assertIn('X-Robots-Tag "noindex, nofollow, noarchive"', caddy)

    def test_bootstrap_keeps_predns_start_http_only(self):
        bootstrap = (ROOT / "scripts/bootstrap.sh").read_text()
        self.assertIn("PREVIEW_ADDRESS=${PREVIEW_ADDRESS:-:8081}", bootstrap)
        self.assertIn("PREVIEW_ADDRESS=%s", bootstrap)

    def test_preview_workflow_uses_trusted_main_definition(self):
        workflow = (ROOT / ".github/workflows/preview.yml").read_text()
        self.assertNotIn("push:\n    branches: [preview]", workflow)
        self.assertIn("workflow_dispatch:", workflow)
        self.assertIn("${{ github.ref }}\" != 'refs/heads/main'", workflow)
        self.assertIn("PREVIEW_DEPLOY_KEY", workflow)
        self.assertNotIn("DEPLOY_KEY: ${{ secrets.DEPLOY_KEY }}", workflow)
        self.assertIn("docker save", workflow)
        self.assertIn("preview-image.tar.gz", workflow)
        self.assertIn('ssh -o BatchMode=yes "$TARGET" "$CANDIDATE_SHA $archive_sha"', workflow)
        self.assertNotIn("compose.preview.yaml up", workflow)

    def test_host_owned_deployer_pins_preview_ref_and_trusted_compose(self):
        deployer = (ROOT / "scripts/deploy_preview.sh").read_text()
        self.assertIn('expected=$(git rev-parse "origin/preview^{commit}")', deployer)
        self.assertIn('[ "$expected" = "$sha" ]', deployer)
        self.assertIn("/srv/website/compose.preview.yaml", deployer)
        self.assertIn("docker load", deployer)
        self.assertIn("PREVIEW_IMAGE=", deployer)
        self.assertIn("ulimit -f 524288", deployer)
        self.assertIn('docker image rm "$failed_image"', deployer)
        self.assertIn('prune_preview_images "$image"', deployer)
        self.assertNotIn("PREVIEW_BUILD_CONTEXT", deployer)
        production = (ROOT / ".github/workflows/deploy.yml").read_text()
        self.assertNotIn("workflow_dispatch:", production)
        install_at = production.index("/usr/local/sbin/website-preview-deploy")
        healthy_at = production.index("wait_healthy ||")
        self.assertGreater(install_at, healthy_at)


if __name__ == "__main__":
    unittest.main()
