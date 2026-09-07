from __future__ import annotations

from django.core.management.base import BaseCommand

from dataportal.ingest.es_repo import StrainIndexRepository
from dataportal.ingest.strain.contig_importer import StrainContigImporter
from dataportal.ingest.strain.mapping import read_mapping_tsv
from dataportal.ingest.strain_experiment.runner import ingest_strain_experiments
from dataportal.utils.constants import INDEX_STRAIN_EXPERIMENTS


class Command(BaseCommand):
    help = (
        "Import isolate identity/contigs into strain_index. "
        "Optional MIC/metabolism flags still work; prefer import_strain_experiments."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--es-index",
            required=True,
            help="Concrete ES strain index (e.g., strain_index-2025.09.03)",
        )
        parser.add_argument(
            "--strain-experiment-index",
            "--drug-index",
            dest="strain_experiment_index",
            default=INDEX_STRAIN_EXPERIMENTS,
            help="Used only if --include-mic / --include-metabolism are set",
        )

        parser.add_argument(
            "--skip-strains", action="store_true", help="Skip FTP strain/contig import"
        )
        parser.add_argument("--ftp-server", default="ftp.ebi.ac.uk")
        parser.add_argument(
            "--ftp-directory",
            default="/pub/databases/mett/all_hd_isolates/deduplicated_assemblies/",
        )
        parser.add_argument(
            "--map-tsv",
            default="../data-generators/data/gff-assembly-prefixes.tsv",
            help="TSV with columns: assembly, prefix",
        )
        parser.add_argument(
            "--set-type-strains",
            nargs="*",
            help="If provided, set only these isolates to type_strain=True; others False. If omitted, preserve existing flags.",
        )

        parser.add_argument("--include-mic", action="store_true")
        parser.add_argument("--mic-bu-file", type=str)
        parser.add_argument("--mic-pv-file", type=str)
        parser.add_argument("--include-metabolism", action="store_true")
        parser.add_argument("--metab-bu-file", type=str)
        parser.add_argument("--metab-pv-file", type=str)
        parser.add_argument("--gff-server", type=str, help="FTP server for GFFs (optional)")
        parser.add_argument(
            "--gff-base", type=str, help="Base directory for GFFs on the GFF server (optional)"
        )

    def handle(self, *args, **opts):
        es_index = opts["es_index"]
        repo = StrainIndexRepository(concrete_index=es_index)

        if not opts["skip_strains"]:
            self.stdout.write(self.style.SUCCESS("Importing strains/contigs from FTP..."))
            mapping = read_mapping_tsv(opts["map_tsv"])
            StrainContigImporter(
                repo=repo,
                ftp_server=opts["ftp_server"],
                ftp_directory=opts["ftp_directory"],
                assembly_to_isolate=mapping,
                type_strains=opts.get("set_type_strains", None),
                gff_server=opts.get("gff_server"),
                gff_base=opts.get("gff_base"),
            ).run()
            self.stdout.write(self.style.SUCCESS("Strains/contigs import complete."))
        else:
            self.stdout.write(self.style.WARNING("Skipped strains/contigs (--skip-strains)."))

        if opts["include_mic"] or opts["include_metabolism"]:
            self.stdout.write(
                self.style.WARNING(
                    "MIC/metabolism flags were passed to import_strains. "
                    "Prefer: python manage.py import_strain_experiments"
                )
            )
            ingest_strain_experiments(
                strain_index=es_index,
                experiment_index=opts["strain_experiment_index"],
                include_mic=opts["include_mic"],
                mic_bu_file=opts.get("mic_bu_file"),
                mic_pv_file=opts.get("mic_pv_file"),
                include_metabolism=opts["include_metabolism"],
                metab_bu_file=opts.get("metab_bu_file"),
                metab_pv_file=opts.get("metab_pv_file"),
            )

        self.stdout.write(self.style.SUCCESS("All tasks finished."))
