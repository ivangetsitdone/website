"""An asset version must follow the file, because the header promises a year.

A versioned URL is served `public, max-age=31536000, immutable` (ADR-0006). A version that
outlives the bytes it describes is therefore not just stale: it is an immutable promise
about the wrong file, which a browser will not revalidate even when the reader reloads. On
a development site with a watcher rebuilding the stylesheet, that is an edit you make,
cannot see, and cannot clear.
"""

import ast
import sys
import time
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app.assets import version, versioned_url  # noqa: E402  (after the path insert)


class AssetVersionTests(unittest.TestCase):
    def setUp(self):
        self.tmp = TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.css = self.root / "static" / "site.css"
        self.css.parent.mkdir()
        self.css.write_text("body { color: red }")

    def test_a_version_is_appended(self):
        url = versioned_url(self.root, "/static/site.css")
        self.assertRegex(url, r"^/static/site\.css\?v=[0-9a-f]{10}$")

    def test_it_is_stable_while_the_file_is(self):
        first = versioned_url(self.root, "/static/site.css")
        self.assertEqual(first, versioned_url(self.root, "/static/site.css"))

    def test_it_changes_when_the_file_changes(self):
        """The watcher case: same name, new bytes, and it must not keep the old version."""
        before = versioned_url(self.root, "/static/site.css")
        time.sleep(0.01)
        self.css.write_text("body { color: blue }")
        after = versioned_url(self.root, "/static/site.css")
        self.assertNotEqual(before, after, "a rebuilt asset kept its old version")

    def test_it_changes_on_a_rewrite_of_the_same_length(self):
        """Size alone would miss this; mtime is what moves when a watcher rewrites."""
        before = versioned_url(self.root, "/static/site.css")
        time.sleep(0.01)
        self.css.write_text("body { color: cyan }")
        self.assertNotEqual(before, versioned_url(self.root, "/static/site.css"))

    def test_a_missing_file_gets_no_version(self):
        """No version means the middleware sends no-cache, rather than promising a year."""
        self.assertEqual(versioned_url(self.root, "/static/gone.css"), "/static/gone.css")
        self.assertEqual(version(self.root / "static/gone.css"), "")

    def test_a_directory_gets_no_version(self):
        self.assertEqual(version(self.root / "static"), version(self.root / "static"))
        self.assertNotEqual(versioned_url(self.root, "/static"), "/static?v=")


class NoMemoisationTests(unittest.TestCase):
    """Guard the reason, not just the behaviour: this is an inviting thing to optimise."""

    def test_the_application_keeps_no_version_cache(self):
        main = (ROOT / "app/main.py").read_text()
        self.assertNotIn("_asset_versions", main)
        for cache in ("lru_cache", "@cache"):
            with self.subTest(decorator=cache):
                self.assertNotIn(cache, main)

    def test_the_helper_keeps_no_version_cache(self):
        assets = (ROOT / "app/assets.py").read_text()
        for cache in ("lru_cache", "@cache", "_versions"):
            with self.subTest(decorator=cache):
                self.assertNotIn(cache, assets)

    def test_the_helper_needs_no_web_framework(self):
        """So this suite can run in the gate before the stack is built. Imports only —
        the module's docstring names FastAPI while explaining why it does not import it."""
        tree = ast.parse((ROOT / "app/assets.py").read_text())
        imported = {
            (node.module or "").split(".")[0]
            for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)
        } | {
            alias.name.split(".")[0]
            for node in ast.walk(tree) if isinstance(node, ast.Import)
            for alias in node.names
        }
        self.assertEqual(imported, {"hashlib", "pathlib"})


if __name__ == "__main__":
    unittest.main()
