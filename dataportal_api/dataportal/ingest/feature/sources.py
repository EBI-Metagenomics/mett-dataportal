import ftplib
import os
import time
import tempfile

_SKIP_FTP_DIR_NAMES = {".", "..", "multiqc", "pipeline_info"}


def isolate_names_from_ftp_entries(entries) -> list[str]:
    names = []
    for entry in entries or []:
        name = os.path.basename(str(entry).rstrip("/"))
        if name and name not in _SKIP_FTP_DIR_NAMES and not name.startswith("."):
            names.append(name)
    return names


def ftp_connect(host, retries=6, delay=5):
    """Login to anonymous FTP. Back off on 4xx (including EBI 421 capacity)."""
    last = None
    for attempt in range(retries):
        try:
            ftp = ftplib.FTP(host, timeout=60)
            ftp.login()
            return ftp
        except ftplib.error_temp as exc:
            last = exc
            if attempt >= retries - 1:
                raise
            wait = min(delay * (2**attempt), 60)
            print(f"[ftp] {exc}; retrying in {wait}s ({attempt + 1}/{retries})")
            time.sleep(wait)
        except ftplib.all_errors as exc:
            last = exc
            if attempt >= retries - 1:
                raise
            time.sleep(delay)
    raise last


def list_isolates_from_ftp_session(ftp, ftp_root: str) -> list[str]:
    root = (ftp_root or "").rstrip("/") or "/"
    entries = []
    try:
        ftp.cwd(root)
        entries = ftp.nlst()
    except ftplib.all_errors as cwd_exc:
        try:
            entries = ftp.nlst(root)
        except ftplib.all_errors as nlst_exc:
            raise RuntimeError(
                f"Could not list isolate folders under {root}: cwd={cwd_exc}; nlst={nlst_exc}"
            ) from nlst_exc
    return isolate_names_from_ftp_entries(entries)


def load_protein_seqs(ftp, faa_path):
    seqs, cur, buf = {}, None, []
    with tempfile.NamedTemporaryFile(mode="w+b", delete=False) as tmp:
        ftp.retrbinary(f"RETR {faa_path}", tmp.write)
        tmp.flush()
        tmp.seek(0)
        for raw in tmp:
            line = raw.decode("utf-8").strip()
            if line.startswith(">"):
                if cur:
                    seqs[cur] = "".join(buf)
                    buf = []
                cur = line.split()[0][1:]
            elif line:
                buf.append(line)
        if cur:
            seqs[cur] = "".join(buf)
    os.unlink(tmp.name)
    return seqs
