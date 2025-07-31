"""
Constants for PyHMMER search functionality.
"""

# Substitution matrix choices - keep in sync with HmmerJob.MXChoices
MX_CHOICES = ["BLOSUM62", "BLOSUM45", "BLOSUM90", "PAM30", "PAM70", "PAM250"]

# Default substitution matrix
DEFAULT_MX = "BLOSUM62"

# Create Literal type for Pydantic schemas
MX_CHOICES_LITERAL = tuple(MX_CHOICES)

# Generate Django choices tuples for models
MX_CHOICES_TUPLES = [(choice, choice) for choice in MX_CHOICES]
