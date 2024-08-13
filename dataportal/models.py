from django.db import models

from django.db import models

class Species(models.Model):
    id = models.AutoField(primary_key=True)  # Primary key, auto-incrementing ID
    scientific_name = models.CharField(max_length=255)
    common_name = models.CharField(max_length=255, blank=True, null=True)
    taxonomy_id = models.IntegerField(unique=True)  # Unique taxonomy ID

    class Meta:
        db_table = 'species'

    def __str__(self):
        return self.scientific_name


class Strain(models.Model):
    id = models.AutoField(primary_key=True)  # Primary key, auto-incrementing ID
    species = models.ForeignKey(Species, on_delete=models.CASCADE, related_name='strains')
    isolate_name = models.CharField(max_length=255)
    strain_name = models.CharField(max_length=255, blank=True, null=True)
    assembly_name = models.CharField(max_length=255, blank=True, null=True)
    assembly_accession = models.CharField(max_length=255, blank=True, null=True)
    fasta_file = models.CharField(max_length=255)
    gff_file = models.CharField(max_length=255)

    class Meta:
        db_table = 'strain'

    def __str__(self):
        return f"{self.isolate_name} ({self.strain_name})"


class Gene(models.Model):
    id = models.AutoField(primary_key=True)  # Primary key, auto-incrementing ID
    strain = models.ForeignKey(Strain, on_delete=models.CASCADE, related_name='genes')
    gene_id = models.CharField(max_length=255)
    gene_name = models.CharField(max_length=255, blank=True, null=True)
    gene_symbol = models.CharField(max_length=255, blank=True, null=True)
    locus_tag = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        db_table = 'gene'

    def __str__(self):
        return self.gene_name or self.gene_id
