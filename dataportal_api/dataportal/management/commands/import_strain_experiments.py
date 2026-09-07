from django.core.management.base import BaseCommand

from dataportal.ingest.strain_experiment.runner import ingest_strain_experiments
from dataportal.utils.constants import INDEX_STRAIN_EXPERIMENTS


class Command(BaseCommand):
    help = "Import strain-level assays (MIC, metabolism) into strain_experiment_index."

    def add_arguments(self, parser):
        parser.add_argument(
            "--es-index",
            required=True,
            help="Concrete ES strain index used to resolve isolate names",
        )
        parser.add_argument(
            "--strain-experiment-index",
            "--drug-index",
            dest="strain_experiment_index",
            default=INDEX_STRAIN_EXPERIMENTS,
            help="Concrete ES strain-experiment index",
        )
        parser.add_argument("--include-mic", action="store_true")
        parser.add_argument("--mic-bu-file", type=str)
        parser.add_argument("--mic-pv-file", type=str)
        parser.add_argument("--include-metabolism", action="store_true")
        parser.add_argument("--metab-bu-file", type=str)
        parser.add_argument("--metab-pv-file", type=str)

    def handle(self, *args, **opts):
        ingest_strain_experiments(
            strain_index=opts["es_index"],
            experiment_index=opts["strain_experiment_index"],
            include_mic=opts["include_mic"],
            mic_bu_file=opts.get("mic_bu_file"),
            mic_pv_file=opts.get("mic_pv_file"),
            include_metabolism=opts["include_metabolism"],
            metab_bu_file=opts.get("metab_bu_file"),
            metab_pv_file=opts.get("metab_pv_file"),
        )
        self.stdout.write(self.style.SUCCESS("Strain experiment ingest finished."))
