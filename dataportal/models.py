from django.db import models

class SpeciesData(models.Model):
    species = models.CharField(max_length=255)
    isolate_name = models.CharField(max_length=255)
    assembly_name = models.CharField(max_length=255)
    fasta_file = models.URLField()
    gff_file = models.URLField()

    class Meta:
        db_table = 'speciesdata'

    def __str__(self):
        return f"{self.species} - {self.isolate_name}"
