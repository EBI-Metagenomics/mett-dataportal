from django.core.management.base import BaseCommand
from pathlib import Path
from dataportal.ingest.operon.flows.operons import Operons
from dataportal.ingest.utils import list_csv_files


class Command(BaseCommand):
    help = "Import operons into a versioned operon_index."

    def add_arguments(self, p):
        p.add_argument("--index", default="operon_index")
        p.add_argument("--operons-dir", required=True, help="Folder containing operon tables (CSV/TSV).")

    def handle(self, *args, **o):
        index = o["index"]
        files = list_csv_files(o["operons_dir"])
        print(f"[import_operons] files: {len(files)}")
        flow = Operons(index_name=index)
        for f in files:
            print(f"  - {f}")
            flow.run(f)
        flow.flush()
