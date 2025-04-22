# need to see if it can be store in some database with dynamic flow to update

class COGCategoryService:
    _categories = {
        "J": "Translation, ribosomal structure and biogenesis",
        "A": "RNA processing and modification",
        "K": "Transcription",
        "L": "Replication, recombination and repair",
        "B": "Chromatin structure and dynamics",
        "D": "Cell cycle control, cell division, chromosome partitioning",
        "Y": "Nuclear structure",
        "V": "Defense mechanisms",
        "T": "Signal transduction mechanisms",
        "M": "Cell wall/membrane/envelope biogenesis",
        "N": "Cell motility",
        "Z": "Cytoskeleton",
        "W": "Extracellular structures",
        "U": "Intracellular trafficking, secretion, and vesicular transport",
        "O": "Posttranslational modification, protein turnover, chaperones",
        "C": "Energy production and conversion",
        "G": "Carbohydrate transport and metabolism",
        "E": "Amino acid transport and metabolism",
        "F": "Nucleotide transport and metabolism",
        "H": "Coenzyme transport and metabolism",
        "I": "Lipid transport and metabolism",
        "P": "Inorganic ion transport and metabolism",
        "Q": "Secondary metabolites biosynthesis, transport and catabolism",
        "R": "General function prediction only",
        "S": "Function unknown",
        "-": "Not in COGs"
    }

    @classmethod
    def get_all(cls) -> dict:
        """Return all COG categories as a dictionary."""
        return cls._categories

    @classmethod
    def get_definition(cls, code: str) -> str:
        """Return the definition of a given COG category code."""
        return cls._categories.get(code.upper(), "Unknown COG category")

    @classmethod
    def as_list(cls) -> list[dict]:
        """Return the categories as a list of dicts with 'code' and 'label'."""
        return [{"code": code, "label": label} for code, label in cls._categories.items()]
