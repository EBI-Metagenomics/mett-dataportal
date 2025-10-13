from django.core.management.base import BaseCommand
from pathlib import Path
from dataportal.ingest.operon.flows.operons import Operons
from dataportal.ingest.gff.parser import GFFParser
from dataportal.ingest.utils import list_csv_files


class Command(BaseCommand):
    help = "Import operons into a versioned operon_index."

    def add_arguments(self, p):
        p.add_argument("--index", default="operon_index")
        p.add_argument("--operons-dir", required=True, help="Folder containing operon tables (CSV/TSV).")
        p.add_argument("--preload-gff", action="store_true", help="Preload GFF files inferred from operon TSVs.")
        p.add_argument(
            "--ftp-server",
            type=str,
            default="ftp.ebi.ac.uk",
            help="FTP server for GFF files (default: ftp.ebi.ac.uk)",
        )
        p.add_argument(
            "--ftp-directory",
            type=str,
            default="/pub/databases/mett/annotations/v1_2024-04-15/",
            help="FTP directory for GFF files",
        )

    def handle(self, *args, **o):
        index = o["index"]
        files = list_csv_files(o["operons_dir"])
        print(f"[import_operons] files: {len(files)}")
        gff_parser = None
        if o.get("preload_gff"):
            # Infer species->isolate mapping from operon files by sampling locus tags
            from dataportal.ingest.ortholog.flows.orthologs import _extract_species_from_locus
            species_isolate_map = {}
            # sample first file to infer mapping
            for fpath in files[:3]:
                try:
                    import pandas as pd
                    df = pd.read_csv(fpath, sep="\t", nrows=200)
                    for col in ("gene1", "gene2", "gene_a_locus_tag", "gene_b_locus_tag"):
                        if col in df.columns:
                            for v in df[col].dropna().astype(str).head(100).tolist():
                                acr, species_name, isolate = _extract_species_from_locus(v)
                                if species_name and isolate and species_name not in species_isolate_map:
                                    species_isolate_map[species_name] = isolate
                except Exception:
                    pass
            if species_isolate_map:
                gff_parser = GFFParser(
                    ftp_server=o.get("ftp_server"),
                    ftp_directory=o.get("ftp_directory"),
                )
                gff_parser.set_species_mapping(species_isolate_map)
                gff_parser.preload_gff_files(list(species_isolate_map.keys()))

        flow = Operons(index_name=index, gff_parser=gff_parser)
        for f in files:
            print(f"  - {f}")
            flow.run(f)
        flow.flush()
