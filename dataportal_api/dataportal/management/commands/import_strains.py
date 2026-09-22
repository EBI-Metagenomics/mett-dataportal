from __future__ import annotations

from django.core.management.base import BaseCommand

from dataportal.ingest.es_repo import StrainIndexRepository
from dataportal.ingest.ftp_paths import (
    add_fasta_extensions_argument,
    add_gff_dir_template_argument,
    parse_fasta_extensions,
)
from dataportal.ingest.strain.contig_importer import StrainContigImporter
from dataportal.ingest.strain.mapping import read_mapping_tsv
from dataportal.ingest.strain.provenance import (
    build_annotation_payload,
    parse_isolate_allowlist,
)
from dataportal.ingest.strain_experiment.runner import ingest_strain_experiments
from dataportal.models import StrainDocument
from dataportal.utils.constants import INDEX_STRAIN_EXPERIMENTS


class Command(BaseCommand):
    help = (
        "Import isolate identity/contigs into strain_index. "
        "Optional MIC/metabolism flags still work; prefer import_strain_experiments. "
        "Optional --pipeline/--pipeline-version stamp processing provenance on written strains. "
        "FASTA and GFF public HTTPS URLs are stored per strain from --ftp-server/--ftp-directory "
        "and --gff-server/--gff-base. GFF folders use --gff-dir-template "
        "({base}/{isolate}/functional_annotation/merged_gff by default). "
        "Assemblies may be .fa/.fna/.fasta (--fasta-extensions). "
        "Re-run with --isolates for mixed FTP roots."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--es-index",
            required=True,
            help="Concrete ES strain index (e.g., mett-v1-g001-strains)",
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
            help="FTP directory of FASTA assemblies. Stored as https://{ftp-server}{directory}/{fasta} on each strain.",
        )
        add_fasta_extensions_argument(parser)
        parser.add_argument(
            "--map-tsv",
            default="../data-generators/data/reference/gff-assembly-prefixes.tsv",
            help="TSV with columns: assembly, prefix",
        )
        parser.add_argument(
            "--set-type-strains",
            nargs="*",
            help="If provided, set only these isolates to type_strain=True; others False. If omitted, preserve existing flags.",
        )
        parser.add_argument(
            "--isolates",
            type=str,
            default=None,
            help="Comma-separated isolate names to import/stamp (mixed-pipeline batches).",
        )
        parser.add_argument(
            "--isolates-file",
            type=str,
            default=None,
            help="File of isolate names (one per line or comma-separated). Combined with --isolates.",
        )
        parser.add_argument(
            "--pipeline",
            type=str,
            default=None,
            help="Annotation pipeline name stamped on imported strains (e.g. mettannotator).",
        )
        parser.add_argument(
            "--pipeline-version",
            type=str,
            default=None,
            help="Annotation pipeline version (e.g. 2.0).",
        )
        parser.add_argument(
            "--processing-reference",
            type=str,
            default=None,
            help="Short processing recipe id (e.g. processing-v2.0).",
        )
        parser.add_argument(
            "--processing-document-url",
            type=str,
            default=None,
            help="URL of the processing README / recipe document.",
        )

        parser.add_argument("--include-mic", action="store_true")
        parser.add_argument("--mic-bu-file", type=str)
        parser.add_argument("--mic-pv-file", type=str)
        parser.add_argument("--include-metabolism", action="store_true")
        parser.add_argument("--metab-bu-file", type=str)
        parser.add_argument("--metab-pv-file", type=str)
        parser.add_argument(
            "--gff-server", type=str, help="FTP server for GFFs (optional)"
        )
        parser.add_argument(
            "--gff-base",
            type=str,
            help=(
                "Annotation root for GFFs on the GFF server (optional). "
                "Combined with --gff-dir-template to locate each isolate's GFF."
            ),
        )
        add_gff_dir_template_argument(parser)

    def handle(self, *args, **opts):
        es_index = opts["es_index"]
        repo = StrainIndexRepository(concrete_index=es_index)
        allowlist = parse_isolate_allowlist(
            opts.get("isolates"), opts.get("isolates_file")
        )
        annotation = build_annotation_payload(
            pipeline=opts.get("pipeline"),
            pipeline_version=opts.get("pipeline_version"),
            processing_reference=opts.get("processing_reference"),
            processing_document_url=opts.get("processing_document_url"),
        )

        if not opts["skip_strains"]:
            self._ensure_annotation_mapping(es_index)
            self.stdout.write(
                self.style.SUCCESS("Importing strains/contigs from FTP...")
            )
            mapping = read_mapping_tsv(opts["map_tsv"])
            StrainContigImporter(
                repo=repo,
                ftp_server=opts["ftp_server"],
                ftp_directory=opts["ftp_directory"],
                assembly_to_isolate=mapping,
                type_strains=opts.get("set_type_strains", None),
                gff_server=opts.get("gff_server"),
                gff_base=opts.get("gff_base"),
                gff_dir_template=opts.get("gff_dir_template"),
                fasta_extensions=parse_fasta_extensions(opts.get("fasta_extensions")),
                isolates=sorted(allowlist) if allowlist else None,
                annotation=annotation,
            ).run()
            self.stdout.write(self.style.SUCCESS("Strains/contigs import complete."))
        else:
            self.stdout.write(
                self.style.WARNING("Skipped strains/contigs (--skip-strains).")
            )

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

    def _ensure_annotation_mapping(self, es_index: str) -> None:
        try:
            from dataportal.elasticsearch.indexing import ProjectIndexManager

            mgr = ProjectIndexManager([StrainDocument]).manager_for_family("strains")
            mgr.put_mapping(es_index)
        except Exception as exc:
            self.stdout.write(
                self.style.WARNING(
                    f"Could not PUT strain annotation mapping on {es_index}: {exc}"
                )
            )
