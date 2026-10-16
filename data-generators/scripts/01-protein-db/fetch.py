"""Download a missing HD protein FASTA from the public EBI copy.

``/pub/databases/mett`` on the cluster is the same tree as
``https://ftp.ebi.ac.uk/pub/databases/mett``. The 20hm annotations live under
``/pub/databases/metagenomics/temp`` and are not on that site.
"""

from __future__ import annotations

import shutil
import urllib.request
from pathlib import Path

CLUSTER_ROOT = "/pub/databases/mett"
PUBLIC_URL = "https://ftp.ebi.ac.uk/pub/databases/mett"


def public_url(faa: str) -> str | None:
    """Return the HTTPS URL for a cluster path, or None when it is not public."""
    path = faa.rstrip("/")
    if path == CLUSTER_ROOT:
        return PUBLIC_URL
    prefix = CLUSTER_ROOT + "/"
    if path.startswith(prefix):
        return PUBLIC_URL + path[len(CLUSTER_ROOT) :]
    return None


def local_faa(faa: Path, *, fetch: bool, cache: Path, opener=None) -> Path:
    """Return a readable FASTA, downloading the public copy when asked."""
    if faa.is_file():
        return faa
    if not fetch:
        raise FileNotFoundError(faa)

    url = public_url(str(faa))
    if url is None:
        raise FileNotFoundError(
            f"{faa} is not on this machine and is not in the public EBI tree "
            f"({PUBLIC_URL}). The 20hm annotations need a local or cluster path."
        )

    relative = str(faa)[len(CLUSTER_ROOT) :].lstrip("/")
    dest = cache / relative
    if dest.is_file() and dest.stat().st_size > 0:
        print(f"Using cached {dest}")
        return dest

    dest.parent.mkdir(parents=True, exist_ok=True)
    partial = dest.with_suffix(dest.suffix + ".partial")
    print(f"Downloading {url}")
    open_url = opener or urllib.request.urlopen
    try:
        with open_url(url, timeout=120) as response, partial.open("wb") as handle:
            shutil.copyfileobj(response, handle)
    except Exception:
        partial.unlink(missing_ok=True)
        raise
    partial.replace(dest)
    return dest
