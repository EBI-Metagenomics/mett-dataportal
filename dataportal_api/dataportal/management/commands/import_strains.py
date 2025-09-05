from __future__ import annotations
from django.core.management.base import BaseCommand

from dataportal.ingest.es_repo import StrainIndexRepository
from dataportal.ingest.strain.parsers import read_mapping_tsv
from dataportal.ingest.strain.importers import StrainContigImporter
from dataportal.ingest.strain.drug_importers import DrugMICUpserter, DrugMetabolismUpserter
from dataportal.ingest.strain.resolver import StrainResolver


class Command(BaseCommand):
    help = "Single entrypoint: optionally import strains/contigs (FTP) and upsert Drug MIC/Metabolism into a concrete ES index."

    def add_arguments(self, parser):
        parser.add_argument("--es-index", required=True, help="Concrete ES index (e.g., strain_index-2025.09.03)")

        # Step A: strains/contigs (optional)
        parser.add_argument("--skip-strains", action="store_true", help="Skip FTP strain/contig import")
        parser.add_argument("--ftp-server", default="ftp.ebi.ac.uk")
        parser.add_argument("--ftp-directory", default="/pub/databases/mett/all_hd_isolates/deduplicated_assemblies/")
        parser.add_argument("--map-tsv", default="../data-generators/data/gff-assembly-prefixes.tsv",
                            help="TSV with columns: assembly, prefix")
        parser.add_argument("--set-type-strains", nargs="*", help="If provided, set only these isolates to type_strain=True; others False. If omitted, preserve existing flags.")

        # Step B: MIC upsert (optional)
        parser.add_argument("--include-mic", action="store_true")
        parser.add_argument("--mic-bu-file", type=str)
        parser.add_argument("--mic-pv-file", type=str)

        # Step C: Metabolism upsert (optional)
        parser.add_argument("--include-metabolism", action="store_true")
        parser.add_argument("--metab-bu-file", type=str)
        parser.add_argument("--metab-pv-file", type=str)
        parser.add_argument("--gff-server", type=str, help="FTP server for GFFs (optional)")
        parser.add_argument("--gff-base", type=str, help="Base directory for GFFs on the GFF server (optional)")

    def handle(self, *args, **opts):
        es_index = opts["es_index"]
        repo = StrainIndexRepository(concrete_index=es_index)


        # A) Strains/Contigs (FTP) — only if not skipped
        if not opts["skip_strains"]:
            self.stdout.write(self.style.SUCCESS("Importing strains/contigs from FTP..."))
            mapping = read_mapping_tsv(opts["map_tsv"])
            # If --set-type-strains is omitted => None => DO NOT modify existing type_strain flags
            type_list = opts.get("set_type_strains", None)
            StrainContigImporter(
                repo=repo,
                ftp_server=opts["ftp_server"],
                ftp_directory=opts["ftp_directory"],
                assembly_to_isolate=mapping,
                type_strains=type_list,
                gff_server=opts.get("gff_server"),
                gff_base=opts.get("gff_base"),
            ).run()
            self.stdout.write(self.style.SUCCESS("Strains/contigs import complete."))
        else:
            self.stdout.write(self.style.WARNING("Skipped strains/contigs (--skip-strains)."))


        # 0) Load resolver once per run
        resolver = StrainResolver(index=es_index)
        resolver.load()

        # B) MIC upsert
        if opts["include_mic"]:
            self.stdout.write(self.style.SUCCESS("Upserting Drug MIC..."))
            DrugMICUpserter(
                repo=repo,
                resolver=resolver,
                bu_csv=opts.get("mic_bu_file"),
                pv_csv=opts.get("mic_pv_file"),
            ).run()
            self.stdout.write(self.style.SUCCESS("Drug MIC upsert complete."))
        else:
            self.stdout.write(self.style.WARNING("MIC upsert skipped (no --include-mic)."))

        # C) Metabolism upsert
        if opts["include_metabolism"]:
            self.stdout.write(self.style.SUCCESS("Upserting Drug Metabolism..."))
            DrugMetabolismUpserter(
                repo=repo,
                resolver=resolver,
                bu_csv=opts.get("metab_bu_file"),
                pv_csv=opts.get("metab_pv_file"),
            ).run()
            self.stdout.write(self.style.SUCCESS("Drug Metabolism upsert complete."))
        else:
            self.stdout.write(self.style.WARNING("Metabolism upsert skipped (no --include-metabolism)."))

        self.stdout.write(self.style.SUCCESS("All tasks finished."))
