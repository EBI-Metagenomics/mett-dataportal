import csv
from django.core.management.base import BaseCommand
from dataportal.models import Gene, GeneEssentiality, EssentialityTag


class Command(BaseCommand):
    help = "Import essentiality data from a CSV file and map to existing Gene records"

    def add_arguments(self, parser):
        parser.add_argument(
            "--csv",
            type=str,
            help="Path to the CSV file containing essentiality data",
            default="../data-generators/data/essentiality_table_all_libraries_240818_14102024.csv",
        )

    def handle(self, *args, **kwargs):
        csv_file = kwargs["csv"]
        valid_strains = ["BU_ATCC8492", "PV_ATCC8482"]

        # Define valid essentiality categories with their corresponding labels
        valid_essentiality_categories = {
            "unclear": "Unclear",
            "essential": "Essential",
            "not essential": "Not Essential",
            "essential_liquid": "Essential Liquid",
            "essential_solid": "Essential Solid",
        }

        # Preload or create essentiality tags with names and labels
        essentiality_tags = {
            tag.name.lower(): tag for tag in EssentialityTag.objects.all()
        }

        for name, label in valid_essentiality_categories.items():
            if name not in essentiality_tags:
                essentiality_tags[name] = EssentialityTag.objects.create(
                    name=name, label=label
                )
            elif essentiality_tags[name].label != label:
                # Update the label if it has changed
                essentiality_tags[name].label = label
                essentiality_tags[name].save()

        gene_essentiality_batch = []
        batch_size = 500

        imported_count = 0
        skipped_count = 0

        try:
            with open(csv_file, "r") as file:
                reader = csv.DictReader(file, delimiter=",")

                for row in reader:
                    locus_tag = row["locus_tag"].strip()
                    strain_id = "_".join(locus_tag.split("_")[:2])
                    essentiality_value = (
                        row["unified_final_call_240817"].strip().lower()
                    )

                    if (
                        strain_id in valid_strains
                        and essentiality_value in essentiality_tags
                    ):
                        try:
                            gene = Gene.objects.get(locus_tag=locus_tag)
                            gene_essentiality_batch.append(
                                GeneEssentiality(
                                    gene=gene,
                                    media=row["media"].strip(),
                                    essentiality=essentiality_tags[essentiality_value],
                                )
                            )
                            imported_count += 1

                            # Insert in batches
                            if len(gene_essentiality_batch) >= batch_size:
                                GeneEssentiality.objects.bulk_create(
                                    gene_essentiality_batch, ignore_conflicts=True
                                )
                                gene_essentiality_batch.clear()

                        except Gene.DoesNotExist:
                            skipped_count += 1
                            self.stderr.write(
                                f"Gene with locus_tag '{locus_tag}' not found."
                            )
                    else:
                        skipped_count += 1

                # Insert any remaining records
                if gene_essentiality_batch:
                    GeneEssentiality.objects.bulk_create(
                        gene_essentiality_batch, ignore_conflicts=True
                    )

            self.stdout.write(
                self.style.SUCCESS(f"Successfully imported {imported_count} records.")
            )
            self.stdout.write(self.style.WARNING(f"Skipped {skipped_count} records."))

        except FileNotFoundError:
            self.stderr.write(self.style.ERROR(f"File '{csv_file}' not found."))
