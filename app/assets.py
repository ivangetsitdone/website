"""Content versions for generated asset URLs.

Separate from main.py so it can be tested without FastAPI installed: the check job runs
this suite directly, before the stack is built.

**Versions are computed on every call and never memoized.** That reads like an obvious
thing to optimise, so here is why not to. The version feeds `?v=`, and the middleware
serves any URL carrying one as `public, max-age=31536000, immutable` (ADR-0006). A version
cached for the life of the process is therefore not merely stale — it is a year-long
`immutable` promise about the wrong bytes, which a browser will not revalidate even on a
manual reload. On a development site whose stylesheet is being rebuilt by a watcher, that
is a change you make, cannot see, and cannot clear.

The cost is one `stat` and one short hash per asset reference: measured at 4.06 us, or
about 309 us for the 76 references on the gallery page. Memoising the digest keyed on the
stat saves 38 us of that, because the dict lookup costs about what the hash does, and buys
back the failure above the first time someone mounts a writable asset directory. Not worth
it.
"""

import hashlib
from pathlib import Path


def version(file: Path) -> str:
    """A short content version for `file`, or '' if it is not there.

    Derived from size and mtime rather than contents: the gallery page references 76
    files, and reading them all to hash them would cost far more than it is worth.
    Generated assets keep stable filenames across builds, so mtime is what moves.
    """
    try:
        stat = file.stat()
    except OSError:
        return ''
    return hashlib.sha256(f'{stat.st_mtime_ns}:{stat.st_size}'.encode()).hexdigest()[:10]


def versioned_url(root: Path, url: str) -> str:
    """Return `url` with a version query, for safe long caching.

    Filenames are stable across builds, so without this a browser can keep serving an old
    stylesheet against fresh HTML. A missing file gets no version, which also means it is
    served `no-cache` rather than promised as immutable.
    """
    stamp = version(root / url.lstrip('/'))
    return f'{url}?v={stamp}' if stamp else url
