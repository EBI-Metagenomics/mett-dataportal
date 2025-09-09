from django.core.management.base import BaseCommand
from pathlib import Path
from dataportal.ingest.operon.flows.operons import Operons

def _list_tabular(pathlike: str | None, exts=(".csv",".tsv",".tab",".txt"), recursive=True) -> list[str]:
    if not pathlike: return []
    p = Path(pathlike).expanduser().resolve()
    if not p.exists(): print(f"[import_operons] not found: {p}"); return []
    if p.is_file() and p.suffix.lower() in exts: return [str(p)]
    if p.is_dir():
        globber = p.rglob if recursive else p.glob
        return [str(f) for f in sorted(globber("*")) if f.suffix.lower() in exts]
    return []

class Command(BaseCommand):
    help = "Import operons into a versioned operon_index."

    def add_arguments(self, p):
        p.add_argument("--index", default="operon_index")
        p.add_argument("--operons-dir", required=True, help="Folder containing operon tables (CSV/TSV).")

    def handle(self, *args, **o):
        index = o["index"]
        files = _list_tabular(o["operons_dir"])
        print(f"[import_operons] files: {len(files)}")
        flow = Operons(index_name=index)
        for f in files:
            print(f"  - {f}")
            flow.run(f)
        flow.flush()
