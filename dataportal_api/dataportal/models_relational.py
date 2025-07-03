from django.db import models

class GeneFitnessCorrelation(models.Model):
    """
    Stores pairwise Pearson correlation coefficients of gene fitness profiles
    across all tested conditions for a given species.

    deduplicate and store efficiently
        Since correlation is symmetric:
        Store only gene1 < gene2 lexicographically to halve storage:
            E.g., store (PV_ATCC8482_00001, PV_ATCC8482_00002, -0.5) but not (PV_ATCC8482_00002, PV_ATCC8482_00001, -0.5).
            Diagonal (gene1 == gene2) can be included if needed for analysis, or omitted to save space since 1 is implicit.
    """

    species_acronym = models.CharField(max_length=20, db_index=True)
    gene1_locus_tag = models.CharField(max_length=100, db_index=True)
    gene2_locus_tag = models.CharField(max_length=100, db_index=True)
    correlation_value = models.FloatField(db_index=True)

    class Meta:
        db_table = "gene_fitness_correlation"
        indexes = [
            models.Index(fields=["gene1_locus_tag", "gene2_locus_tag"], name="idx_gene_fitness_corr_lookup"),
            models.Index(fields=["correlation_value"], name="idx_gene_fitness_corr_value"),
        ]
        constraints = [
            models.CheckConstraint(
                check=~models.Q(gene1_locus_tag=models.F('gene2_locus_tag')),
                name="check_gene1_not_gene2",
            )
        ]
        verbose_name = "Gene Fitness Correlation"
        verbose_name_plural = "Gene Fitness Correlations"

    def __str__(self):
        return (
            f"{self.species_acronym}: {self.gene1_locus_tag} ↔ {self.gene2_locus_tag} "
            f"(corr={self.correlation_value:.3f})"
        )



class ProteinCompoundInteraction(models.Model):
    """
    Stores protein-compound thermal stability interaction measurements.

    condition-based, numeric, structured.

    Can grow large (2000 proteins * 2 species * 56 compounds ≈ 224,000 rows).

    May require:
        Filtering by compound.
        Filtering by protein.
        Filtering by hit_calling, p-value, or score thresholds.
    """

    species_acronym = models.CharField(max_length=20, db_index=True)
    locus_tag = models.CharField(max_length=100, db_index=True)
    compound = models.CharField(max_length=255, db_index=True)
    thermal_stability_score = models.FloatField()
    p_value = models.FloatField()
    adj_p_value = models.FloatField()
    hit_calling = models.BooleanField()

    class Meta:
        db_table = "protein_compound_interaction"
        indexes = [
            models.Index(fields=["locus_tag", "compound"], name="idx_prot_compound_lookup"),
            models.Index(fields=["compound"], name="idx_compound"),
            models.Index(fields=["hit_calling"], name="idx_hit_calling"),
        ]
        verbose_name = "Protein Compound Interaction"
        verbose_name_plural = "Protein Compound Interactions"

    def __str__(self):
        return (
            f"{self.species_acronym}: {self.locus_tag} x {self.compound} "
            f"(score={self.thermal_stability_score}, hit={self.hit_calling})"
        )


class SingleMutantGrowthRate(models.Model):
    """
    Stores single mutant growth rate measurements under specific media conditions.

    possible use cases:
        Filtering by gene (locus_tag).
        Filtering by medium (media).
        Filtering or sorting by doubling_rate for phenotype strength.
        Statistical analysis across replicates.
    """

    species_acronym = models.CharField(max_length=20, db_index=True)
    locus_tag = models.CharField(max_length=100, db_index=True)
    media = models.CharField(max_length=100, db_index=True)
    mutant_replicate = models.PositiveSmallIntegerField()
    tas_hit = models.FloatField(help_text="Transposon abundance score (0-1)")
    doubling_rate_h = models.FloatField(help_text="Doubling rate in hours")

    class Meta:
        db_table = "single_mutant_growth_rate"
        indexes = [
            models.Index(fields=["locus_tag", "media"], name="idx_mutant_growth_lookup"),
            models.Index(fields=["media"], name="idx_growth_media"),
        ]
        verbose_name = "Single Mutant Growth Rate"
        verbose_name_plural = "Single Mutant Growth Rates"

    def __str__(self):
        return (
            f"{self.species_acronym}: {self.locus_tag} in {self.media} "
            f"(rep={self.mutant_replicate}, rate={self.doubling_rate_h:.2f}h)"
        )

class DrugBacteriaInteraction(models.Model):
    """
    Stores drug-bacteria interaction data including MIC and drug metabolism for each strain-drug pair.

    Strain-centric exploration:
        Show how a strain responds to various drugs (MIC, metabolism).

    Drug-centric exploration:
        List strains sensitive or resistant to a drug (MIC < X).
        Identify strains that metabolize a drug heavily (drug_metabolism_percent > 0.8).

    Overlay with essentiality/gene data:
        Determine if specific gene knockouts affect drug sensitivity (future integrated analyses).
    """

    strain = models.CharField(max_length=100, db_index=True)
    drug = models.CharField(max_length=255, db_index=True)

    mic_um = models.FloatField(help_text="Minimum Inhibitory Concentration (uM)")
    drug_metabolism_percent = models.FloatField(help_text="Percentage of drug metabolized (0-1)")
    drug_metabolism_pval = models.FloatField()
    drug_metabolism_fdr = models.FloatField()

    class Meta:
        db_table = "drug_bacteria_interaction"
        indexes = [
            models.Index(fields=["strain", "drug"], name="idx_strain_drug_lookup"),
            models.Index(fields=["drug"], name="idx_drug"),
        ]
        verbose_name = "Drug Bacteria Interaction"
        verbose_name_plural = "Drug Bacteria Interactions"

    def __str__(self):
        return (
            f"{self.strain} x {self.drug} (MIC={self.mic_um}uM, "
            f"metab={self.drug_metabolism_percent}, p={self.drug_metabolism_pval})"
        )


