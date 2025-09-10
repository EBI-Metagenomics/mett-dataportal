from django.core.management.base import BaseCommand
from pathlib import Path
from dataportal.ingest.ortholog.flows.orthologs import Orthologs
from dataportal.ingest.utils import list_csv_files


class Command(BaseCommand):
    help = "Import ortholog pairs into a versioned ortholog_index."

    def add_arguments(self, p):
        p.add_argument("--index", default="ortholog_index")
        p.add_argument("--orthologs-dir", required=True, help="Folder with ortholog pair files (CSV/TSV).")

    def handle(self, *args, **o):
        index = o["index"]
        files = list_csv_files(o["orthologs_dir"])
        print(f"[import_orthologs] files: {len(files)}")
        flow = Orthologs(index_name=index)
        for f in files:
            print(f"  - {f}")
            flow.run(f)
        flow.flush()
