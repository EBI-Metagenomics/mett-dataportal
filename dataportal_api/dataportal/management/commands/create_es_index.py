from django.core.management.base import BaseCommand, CommandError

from dataportal.elasticsearch.indexing import ProjectIndexManager
from dataportal.elasticsearch.names import (
    INDEX_FAMILIES,
    IndexNameError,
    coerce_family,
    normalize_release,
)
from dataportal.elasticsearch.release_ops import adopt_legacy_indexes, create_release_indexes
from dataportal.models import (
    SpeciesDocument,
    StrainDocument,
    FeatureDocument,
    StrainExperimentDocument,
    FeatureExperimentDocument,
    ProteinProteinDocument,
    OperonDocument,
    OrthologDocument,
    GeneFitnessCorrelationDocument,
)


AVAILABLE_MODELS = {
    "SpeciesDocument": SpeciesDocument,
    "StrainDocument": StrainDocument,
    "FeatureDocument": FeatureDocument,
    "StrainExperimentDocument": StrainExperimentDocument,
    "FeatureExperimentDocument": FeatureExperimentDocument,
    "ProteinProteinDocument": ProteinProteinDocument,
    "OperonDocument": OperonDocument,
    "OrthologDocument": OrthologDocument,
    "GeneFitnessCorrelationDocument": GeneFitnessCorrelationDocument,
}


class Command(BaseCommand):
    help = (
        "Create Elasticsearch indexes. "
        "Prefer --release v1 to create a full METT set (mett-v1-g001-*). "
        "Use --adopt-legacy to alias existing *_index names as mett-v1-* without re-ingest. "
        "Does not switch mett-current-* aliases."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--model",
            type=str,
            default=None,
            help=f"Legacy: create one document family by class name. "
            f"Available: {', '.join(AVAILABLE_MODELS.keys())}",
        )
        parser.add_argument(
            "--family",
            action="append",
            dest="families",
            help="Limit to one or more family tokens (species, strains, features, …). Repeatable.",
        )
        parser.add_argument(
            "--release",
            type=str,
            default=None,
            help="METT version token (v1, v2, …). Creates/adopts the whole set.",
        )
        parser.add_argument(
            "--generation",
            type=int,
            default=1,
            help="Physical generation number for mett-vN-gNNN-* (default 1).",
        )
        parser.add_argument(
            "--adopt-legacy",
            action="store_true",
            help="Point mett-vN-{family} aliases at existing *_index names. No re-ingest.",
        )
        parser.add_argument(
            "--es-version",
            dest="es_version",
            type=str,
            default=None,
            help="Deprecated: suffix on legacy base names (feature_index-2025.09.03).",
        )
        parser.add_argument(
            "--if-exists",
            dest="if_exists",
            type=str,
            choices=["skip", "recreate", "fail"],
            default="skip",
            help="Behavior if a physical index already exists (ignored by --adopt-legacy).",
        )

    def handle(self, *args, **kwargs):
        release = kwargs.get("release")
        generation = kwargs.get("generation") or 1
        adopt_legacy = kwargs.get("adopt_legacy")
        es_version = kwargs.get("es_version")
        if_exists = kwargs.get("if_exists", "skip")
        model_name = kwargs.get("model")
        families = kwargs.get("families")

        if adopt_legacy and not release:
            raise CommandError("--adopt-legacy requires --release (e.g. --release v1)")
        if adopt_legacy and es_version:
            raise CommandError("Do not combine --adopt-legacy with --es-version")
        if release and es_version:
            raise CommandError("Use --release/--generation, not --es-version")
        if release:
            try:
                normalize_release(release)
            except IndexNameError as exc:
                raise CommandError(str(exc)) from exc

        if model_name:
            if model_name not in AVAILABLE_MODELS:
                raise CommandError(
                    f"Unknown model: {model_name}. "
                    f"Available models: {', '.join(AVAILABLE_MODELS.keys())}"
                )
            models_to_create = [AVAILABLE_MODELS[model_name]]
        else:
            models_to_create = list(AVAILABLE_MODELS.values())

        pim = ProjectIndexManager(models_to_create)

        if model_name and not families:
            families = [coerce_family(AVAILABLE_MODELS[model_name].Index.name)]

        if families:
            try:
                families = [coerce_family(f) for f in families]
            except IndexNameError as exc:
                raise CommandError(str(exc)) from exc
            unknown = [f for f in families if f not in INDEX_FAMILIES]
            if unknown:
                raise CommandError(f"Unknown families: {unknown}")

        if adopt_legacy:
            self.stdout.write(
                self.style.SUCCESS(
                    f"Adopting legacy *_index names as aliases for {release} "
                    "(mett-current-* is not switched)."
                )
            )
            adopted = adopt_legacy_indexes(
                release=release,
                generation=generation,
                families=families,
                actor="create_es_index",
            )
            for fam, physical in adopted.items():
                self.stdout.write(
                    self.style.SUCCESS(f"  ✓ mett-{normalize_release(release)}-{fam} -> {physical}")
                )
            skipped = set(families or INDEX_FAMILIES) - set(adopted)
            for fam in sorted(skipped):
                self.stdout.write(self.style.WARNING(f"  – skipped {fam} (legacy index missing)"))
            self.stdout.write(
                self.style.SUCCESS(
                    "\nRelease aliases are ready. Portal default still uses legacy names "
                    "until a later promote_release step points mett-current-*."
                )
            )
            return

        if release:
            self.stdout.write(
                self.style.SUCCESS(
                    f"Creating physical set {release} generation {generation} "
                    "(release aliases only; mett-current-* is not switched)."
                )
            )
            created = create_release_indexes(
                release=release,
                generation=generation,
                project=pim,
                if_exists=if_exists,
                families=families,
                actor="create_es_index",
            )
            rel = normalize_release(release)
            for fam, concrete in created.items():
                self.stdout.write(self.style.SUCCESS(f"  ✓ {concrete}  alias mett-{rel}-{fam}"))
            self.stdout.write(self.style.SUCCESS(f"\n{len(created)} index(es) created."))
            return

        # Legacy path: unversioned *_index, optional --es-version suffix
        if model_name:
            self.stdout.write(self.style.SUCCESS(f"Creating index for {model_name}..."))
        else:
            self.stdout.write(
                self.style.SUCCESS("Creating Elasticsearch indexes at legacy base names...")
            )

        created = pim.create_all(version=es_version, if_exists=if_exists)
        for base, concrete in created.items():
            self.stdout.write(self.style.SUCCESS(f"  ✓ {base} -> {concrete}"))

        if model_name:
            self.stdout.write(self.style.SUCCESS(f"\nIndex creation for {model_name} completed."))
        else:
            self.stdout.write(
                self.style.SUCCESS(f"\nAll {len(created)} index(es) created successfully.")
            )
