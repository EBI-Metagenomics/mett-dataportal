"""Download a missing HD protein FASTA from the public EBI copy.

``/pub/databases/mett`` on the cluster is the same tree as
``https://ftp.ebi.ac.uk/pub/databases/mett``. The 20hm annotations live under
``/pub/databases/metagenomics/temp`` and are not on that site.
"""

from __future__ import annotations

import os
import shutil
import urllib.request
from pathlib import Path

CLUSTER_ROOT = "/pub/databases/mett"
PUBLIC_URL = "https://ftp.ebi.ac.uk/pub/databases/mett"
_DEFAULT_ANNOTATION_ROOT = (
    Path(__file__).resolve().parents[2]
    / "data"
    / "generated"
    / "mettannotator"
    / "gff3_files"
)


def public_url(faa: str) -> str | None:
    """Return the HTTPS URL for a cluster path, or None when it is not public."""
    path = faa.rstrip("/")
    if path == CLUSTER_ROOT:
        return PUBLIC_URL
    prefix = CLUSTER_ROOT + "/"
    if path.startswith(prefix):
        return PUBLIC_URL + path[len(CLUSTER_ROOT) :]
    return None


def annotation_root() -> Path:
    """Local mettannotator tree. ``METTANNOTATOR_OUT`` overrides the default."""
    override = os.environ.get("METTANNOTATOR_OUT")
    if not override:
        return _DEFAULT_ANNOTATION_ROOT
    return Path(override).expanduser() / "gff3_files"


def local_annotation_copy(faa: Path, root: Path | None = None) -> Path | None:
    """Same isolate under the local annotation tree, when that file exists."""
    if not faa.name.endswith(".faa"):
        return None
    isolate = faa.name[: -len(".faa")]
    if not isolate:
        return None
    candidate = (
        (root or annotation_root())
        / isolate
        / "functional_annotation"
        / "prokka"
        / faa.name
    )
    if candidate.is_file() and candidate != faa:
        return candidate
    return None


def local_faa(
    faa: Path,
    *,
    fetch: bool,
    cache: Path,
    opener=None,
    annotation: Path | None = None,
) -> Path:
    """Return a readable FASTA.

    A missing path is replaced by the local mettannotator copy when that
    isolate has one. A missing ``/pub/databases/mett`` path is otherwise
    downloaded from the public EBI site when ``fetch`` is set.
    """
    if faa.is_file():
        return faa
    local = local_annotation_copy(faa, root=annotation)
    if local is not None:
        print(f"Using local annotation {local}")
        return local
    url = public_url(str(faa))
    if not fetch or url is None:
        if url:
            raise FileNotFoundError(
                f"{faa} is not on this machine. The public copy is {url}."
            )
        raise FileNotFoundError(
            f"{faa} is not on this machine and is not in the public EBI tree "
            f"({PUBLIC_URL}). Looked for a local copy under {annotation_root()}."
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
