import logging
from typing import Tuple, Optional
from Bio.Align import substitution_matrices

logger = logging.getLogger(__name__)


class AlignmentCalculator:
    """Class for calculating identity and similarity from alignment data."""

    @classmethod
    def calculate_identity(
        cls, model: str, mline: str, aseq: str
    ) -> Optional[Tuple[float, int]]:
        try:
            if len(mline) != len(aseq):
                return None

            number_of_identical = mline.count("*")

            seq1 = "".join(filter(str.isalpha, model))
            seq2 = "".join(filter(str.isalpha, aseq))

            len1 = len(seq1)
            len2 = len(seq2)
            min_len = min(len1, len2)

            if min_len and number_of_identical:
                result = number_of_identical / min_len, number_of_identical
            else:
                result = 0, 0

            return result

        except Exception as e:
            logger.warning(f"Failed to calculate identity: {e}")
            return None

    @classmethod
    def calculate_similarity(
        cls, model: str, mline: str, aseq: str
    ) -> Optional[Tuple[float, int]]:
        try:
            if len(mline) != len(aseq):
                return None

            # Load BLOSUM62 substitution matrix for amino acid similarity
            try:
                matrix = substitution_matrices.load("BLOSUM62")
            except Exception as e:
                logger.warning(f"Failed to load BLOSUM62 matrix: {e}")
                # Fallback to simple identity calculation
                return cls.calculate_identity(model, mline, aseq)

            number_of_identical_and_similar = 0
            total_aligned = 0

            for i, (a, b) in enumerate(zip(model, aseq)):
                if a == "-" or b == "-":
                    continue

                total_aligned += 1

                if a.upper() == b.upper():
                    # Identical
                    number_of_identical_and_similar += 1
                else:
                    # Check if similar using BLOSUM62 matrix
                    a_upper = a.upper()
                    b_upper = b.upper()

                    try:
                        # Get substitution score from BLOSUM62
                        score = matrix[a_upper, b_upper]
                        # Consider amino acids similar if BLOSUM62 score >= 0
                        # (positive scores indicate favorable substitutions)
                        if score >= 0:
                            number_of_identical_and_similar += 1
                    except (KeyError, IndexError):
                        # If amino acid not in matrix, treat as different
                        pass

            if total_aligned > 0:
                result = (
                    number_of_identical_and_similar / total_aligned,
                    number_of_identical_and_similar,
                )
            else:
                result = 0, 0

            return result

        except Exception as e:
            logger.warning(f"Failed to calculate similarity: {e}")
            return None

    @classmethod
    def create_match_line(cls, hmm_sequence: str, target_sequence: str) -> str:
        try:
            mline = ""

            for a, b in zip(hmm_sequence, target_sequence):
                if a == "-" or b == "-":
                    mline += " "
                elif a.upper() == b.upper():  # Case-insensitive comparison
                    mline += "*"
                else:
                    mline += " "

            return mline
        except Exception as e:
            logger.warning(f"Failed to create match line: {e}")
            return ""

    @classmethod
    def calculate_identity_and_similarity_from_sequences(
        cls, hmm_sequence: str, target_sequence: str
    ) -> Tuple[Tuple[float, int], Tuple[float, int]]:
        try:
            mline = cls.create_match_line(hmm_sequence, target_sequence)

            identity_result = cls.calculate_identity(
                hmm_sequence, mline, target_sequence
            )
            if identity_result is None:
                identity_result = (0.0, 0)

            similarity_result = cls.calculate_similarity(
                hmm_sequence, mline, target_sequence
            )
            if similarity_result is None:
                similarity_result = (0.0, 0)

            return identity_result, similarity_result

        except Exception as e:
            logger.warning(
                f"Failed to calculate identity and similarity from sequences: {e}"
            )
            return (0.0, 0), (0.0, 0)

    @classmethod
    def calculate_identity_and_similarity_from_match_line(
        cls, hmm_sequence: str, mline: str, target_sequence: str
    ) -> Tuple[Tuple[float, int], Tuple[float, int]]:
        try:
            identity_result = cls.calculate_identity(
                hmm_sequence, mline, target_sequence
            )
            if identity_result is None:
                identity_result = (0.0, 0)

            similarity_result = cls.calculate_similarity(
                hmm_sequence, mline, target_sequence
            )
            if similarity_result is None:
                similarity_result = (0.0, 0)

            return identity_result, similarity_result

        except Exception as e:
            logger.warning(
                f"Failed to calculate identity and similarity from match line: {e}"
            )
            return (0.0, 0), (0.0, 0)
