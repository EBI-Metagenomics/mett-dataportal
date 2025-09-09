from django.core.management.base import BaseCommand
from pathlib import Path
from dataportal.ingest.ortholog.flows.orthologs import Orthologs

def _list_tabular(pathlike: str | None, exts=(".csv",".tsv",".tab",".txt"), recursive=True) -> list[str]:
    if not pathlike: return []
    p = Path(pathlike).expanduser().resolve()
    if not p.exists(): print(f"[import_orthologs] not found: {p}"); return []
    if p.is_file() and p.suffix.lower() in exts: return [str(p)]
    if p.is_dir():
        globber = p.rglob if recursive else p.glob
        return [str(f) for f in sorted(globber("*")) if f.suffix.lower() in exts]
    return []

class Command(BaseCommand):
    help = "Import ortholog pairs into a versioned ortholog_index."

    def add_arguments(self, p):
        p.add_argument("--index", default="ortholog_index")
        p.add_argument("--orthologs-dir", required=True, help="Folder with ortholog pair files (CSV/TSV).")

    def handle(self, *args, **o):
        index = o["index"]
        files = _list_tabular(o["orthologs_dir"])
        print(f"[import_orthologs] files: {len(files)}")
        flow = Orthologs(index_name=index)
        for f in files:
            print(f"  - {f}")
            flow.run(f)
        flow.flush()
