"""Fixed values for the PyHMMER app.

Paths and operational limits that differ between deployments are read from the
environment in ``dataportal.settings``. This module holds their defaults and
the values that stay the same in every environment.
"""

# Deployment defaults. Override with the environment variables of the same name
# except where noted.
DEFAULT_FAA_BASE_PATH = "/data/pyhmmer/output/"
DEFAULT_ISOLATES_BASE_PATH = "/data/pyhmmer/output/isolates-db/"
DEFAULT_RESULT_MAX_BYTES = 50 * 1024 * 1024
DEFAULT_TASK_RETENTION_DAYS = 30
MIN_TASK_RETENTION_DAYS = 1
MAX_TASK_RETENTION_DAYS = 365

# PYHMMER_DB, PYHMMER_FAA_BASE_PATH, PYHMMER_ISOLATES_BASE_PATH,
# PYHMMER_RESULT_MAX_BYTES, PYHMMER_TASK_RETENTION_DAYS, PYHMMER_SPECIES_CSV

PROTEIN_DB_FILENAME = "mett_proteins.faa"
DATABASE_ID = "mett_proteins"
DATABASE_LABEL = "METT proteins"
ISOLATE_DB_PREFIX = "isolate_"
ISOLATE_DB_SUFFIX = "_deduplicated.faa"
DEFAULT_ISOLATE_SPECIES = "BU"
SPECIES_PREFIX = (("BU_", "BU"), ("PV_", "PV"))
HD_SPECIES = ("BU", "PV")
COLLECTION_HD = "hd"
COLLECTION_EXTENDED = "20hm"
SHORTCUT_ALL_ID = "all"
SHORTCUT_ALL_LABEL = "All species"
SHORTCUT_HD_ID = "hd"
SHORTCUT_HD_LABEL = "B. uniformis + P. vulgatus"

# Old dropdown ids. A saved search with one of these still runs on the single file.
ALIASES: dict[str, tuple[list[str], bool, str]] = {
    "bu_all": (["BU"], False, ""),
    "bu_type_strains": (["BU"], True, ""),
    "pv_all": (["PV"], False, ""),
    "pv_type_strains": (["PV"], True, ""),
    "bu_pv_all": (["BU", "PV"], False, ""),
    "bu_pv_type_strains": (["BU", "PV"], True, ""),
    DATABASE_ID: ([], False, ""),
}

LEGACY_FAA_FILES = {
    "bu_type_strains": "bu_typestrains_deduplicated.faa",
    "bu_all": "bu_all_strains_deduplicated.faa",
    "pv_type_strains": "pv_typestrains_deduplicated.faa",
    "pv_all": "pv_all_strains_deduplicated.faa",
    "bu_pv_type_strains": "bu_pv_typestrains_deduplicated.faa",
    "bu_pv_all": "bu_pv_all_strains_deduplicated.faa",
}

STATUS_PENDING = "PENDING"
STATUS_STARTED = "STARTED"
STATUS_SUCCESS = "SUCCESS"
STATUS_FAILURE = "FAILURE"

FORMAT_TAB = "tab"
FORMAT_FASTA = "fasta"
FORMAT_ALIGNED_FASTA = "aligned_fasta"
DOWNLOAD_FORMATS = (FORMAT_TAB, FORMAT_FASTA, FORMAT_ALIGNED_FASTA)

# HMMER reporting defaults. These are also the database column defaults.
DEFAULT_THRESHOLD = "evalue"
THRESHOLD_BITSCORE = "bitscore"
DEFAULT_THRESHOLD_VALUE = 1.0
DEFAULT_E = 1.0
DEFAULT_DOM_E = 1.0
DEFAULT_T = 7.0
DEFAULT_DOM_T = 5.0
DEFAULT_INC_E = 0.01
DEFAULT_INC_DOM_E = 0.03
DEFAULT_INC_T = 25.0
DEFAULT_INC_DOM_T = 22.0
DEFAULT_POPEN = 0.02
DEFAULT_PEXTEND = 0.4

PIPELINE_FIELDS = ("E", "domE", "incE", "incdomE", "T", "domT", "incT", "incdomT")

JOB_LOAD_ATTEMPTS = 5
JOB_LOAD_RETRY_SECONDS = 0.5

VALID_AMINO_ACIDS = set("ACDEFGHIKLMNPQRSTVWY*")

MX_CHOICES = ["BLOSUM62", "BLOSUM45", "BLOSUM90", "PAM30", "PAM70", "PAM250"]
DEFAULT_MX = "BLOSUM62"
MX_CHOICES_LITERAL = tuple(MX_CHOICES)
MX_CHOICES_TUPLES = [(choice, choice) for choice in MX_CHOICES]
