import datetime
import uuid
from django.db import models
from django_celery_results.models import TaskResult


class HmmerJob(models.Model):
    class MXChoices(models.TextChoices):
        BLOSUM62 = "BLOSUM62"
        BLOSUM45 = "BLOSUM45"
        BLOSUM90 = "BLOSUM90"
        PAM30 = "PAM30"
        PAM70 = "PAM70"
        PAM250 = "PAM250"

    class AlgoChoices(models.TextChoices):
        PHMMER = "phmmer"

    class ThresholdChoices(models.TextChoices):
        EVALUE = "evalue", "E-value"
        BITSCORE = "bitscore", "Bit score"

    class DbChoices(models.TextChoices):
        BU_TYPE_STRAINS = "bu_type_strains", "Bacteroides uniformis Type Strains"
        BU_ALL = "bu_all", "Bacteroides uniformis All Strains"
        PV_TYPE_STRAINS = "pv_type_strains", "Phocaeicola vulgatus Type Strains"
        PV_ALL = "pv_all", "Phocaeicola vulgatus All Strains"
        BU_PV_TYPE_STRAINS = (
            "bu_pv_type_strains",
            "Bacteroides uniformis + Phocaeicola vulgatus Type Strains",
        )
        BU_PV_ALL = (
            "bu_pv_all",
            "Bacteroides uniformis + Phocaeicola vulgatus All Strains",
        )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    algo = models.CharField(
        max_length=16, choices=AlgoChoices.choices, default=AlgoChoices.PHMMER
    )
    database = models.CharField(max_length=32, choices=DbChoices.choices)
    input = models.TextField()

    threshold = models.CharField(
        max_length=16,
        choices=ThresholdChoices.choices,
        default=ThresholdChoices.EVALUE,
    )

    E = models.FloatField(default=1.0, null=True, blank=True)
    domE = models.FloatField(default=1.0, null=True, blank=True)
    T = models.FloatField(default=7.0, null=True, blank=True)
    domT = models.FloatField(default=5.0, null=True, blank=True)
    incE = models.FloatField(default=0.01, null=True, blank=True)
    incdomE = models.FloatField(default=0.03, null=True, blank=True)
    incT = models.FloatField(default=25.0, null=True, blank=True)
    incdomT = models.FloatField(default=22.0, null=True, blank=True)

    popen = models.FloatField(default=0.02, null=True, blank=True)
    pextend = models.FloatField(default=0.4, null=True, blank=True)

    threshold_value = models.FloatField(default=1.0)

    bias_filter = models.CharField(
        max_length=8,
        choices=[("on", "On"), ("off", "Off")],
        default="on",
        help_text="Bias composition filter setting",
    )

    task = models.OneToOneField(
        TaskResult, related_name="+", null=True, blank=True, on_delete=models.CASCADE
    )

    mx = models.CharField(
        max_length=16,
        null=True,
        blank=True,
        choices=MXChoices.choices,
        default=MXChoices.BLOSUM62,
    )

    def __str__(self):
        return f"{self.algo} search on {self.database} ({self.id})"

    class Meta:
        app_label = "pyhmmer_search"


class Database(models.Model):
    class TypeChoices(models.TextChoices):
        SEQ = "seq"

    id = models.CharField(max_length=32, primary_key=True, unique=True)
    type = models.CharField(
        max_length=16, choices=TypeChoices.choices, default=TypeChoices.SEQ
    )
    name = models.CharField(max_length=128)
    version = models.CharField(max_length=32)
    release_date = models.DateField(default=datetime.date.today)
    order = models.IntegerField(default=-1)

    class Meta:
        app_label = "pyhmmer_search"
