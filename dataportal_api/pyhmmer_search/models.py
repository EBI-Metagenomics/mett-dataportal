import datetime
import uuid
from django.db import models
from django_celery_results.models import TaskResult


class HmmerJob(models.Model):
    class AlgoChoices(models.TextChoices):
        PHMMER = "phmmer"

    class ThresholdChoices(models.TextChoices):
        EVALUE = "evalue", "E-value"
        BITSCORE = "bitscore", "Bit score"

    class DbChoices(models.TextChoices):
        BU_TYPE_STRAINS = "bu_type_strains", "BU Type Strains"
        BU_ALL = "bu_all", "BU All Strains"
        PV_TYPE_STRAINS = "pv_type_strains", "PV Type Strains"
        PV_ALL = "pv_all", "PV All Strains"
        BU_PV_TYPE_STRAINS = "bu_pv_type_strains", "BU+PV Type Strains"
        BU_PV_ALL = "bu_pv_all", "BU+PV All Strains"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    algo = models.CharField(max_length=16, choices=AlgoChoices.choices, default=AlgoChoices.PHMMER)
    database = models.CharField(max_length=32, choices=DbChoices.choices)
    input = models.TextField()

    threshold = models.CharField(
        max_length=16,
        choices=ThresholdChoices.choices,
        default=ThresholdChoices.EVALUE,
    )

    threshold_value = models.FloatField(default=1.0)

    task = models.OneToOneField(TaskResult, related_name="+", null=True, blank=True, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.algo} search on {self.database} ({self.id})"

    class Meta:
        app_label = "pyhmmer_search"



class Database(models.Model):
    class TypeChoices(models.TextChoices):
        SEQ = "seq"

    id = models.CharField(max_length=32, primary_key=True, unique=True)
    type = models.CharField(max_length=16, choices=TypeChoices.choices, default=TypeChoices.SEQ)
    name = models.CharField(max_length=32)
    version = models.CharField(max_length=32)
    release_date = models.DateField(default=datetime.date.today)
    order = models.IntegerField(default=-1)

    class Meta:
        app_label = "pyhmmer_search"
