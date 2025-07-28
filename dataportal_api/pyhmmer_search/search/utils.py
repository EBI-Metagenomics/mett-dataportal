"""
Utility functions for PyHMMER search calculations.
"""
import logging
from typing import Tuple, Optional

logger = logging.getLogger(__name__)


class AlignmentCalculator:
    """Class for calculating identity and similarity from alignment data."""
    
    @classmethod
    def calculate_identity(cls, model: str, mline: str, aseq: str) -> Optional[Tuple[float, int]]:
        """Calculate identity percentage and count from alignment data."""
        try:
            if len(mline) != len(aseq):
                return None

            # Count asterisks (*) which represent identical matches
            number_of_identical = mline.count('*')
            
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
    def calculate_similarity(cls, model: str, mline: str, aseq: str) -> Optional[Tuple[float, int]]:
        """Calculate similarity percentage and count from alignment data."""
        try:
            if len(mline) != len(aseq):
                return None

            match = "".join(mline.split())
            number_of_identical_and_similar = len(match)
            
            seq1 = "".join(filter(str.isalpha, model))
            seq2 = "".join(filter(str.isalpha, aseq))

            len1 = len(seq1)
            len2 = len(seq2)
            min_len = min(len1, len2)

            if min_len and number_of_identical_and_similar:
                result = number_of_identical_and_similar / min_len, number_of_identical_and_similar
            else:
                result = 0, 0
            
            return result
                
        except Exception as e:
            logger.warning(f"Failed to calculate similarity: {e}")
            return None



    @classmethod
    def create_match_line(cls, hmm_sequence: str, target_sequence: str) -> str:
        """Create a match line showing identical positions between two sequences."""
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
        """Calculate identity and similarity from raw sequences by creating the match line first."""
        try:
            mline = cls.create_match_line(hmm_sequence, target_sequence)
            
            identity_result = cls.calculate_identity(hmm_sequence, mline, target_sequence)
            if identity_result is None:
                identity_result = (0.0, 0)
            
            similarity_result = cls.calculate_similarity(hmm_sequence, mline, target_sequence)
            if similarity_result is None:
                similarity_result = (0.0, 0)
            
            return identity_result, similarity_result
            
        except Exception as e:
            logger.warning(f"Failed to calculate identity and similarity from sequences: {e}")
            return (0.0, 0), (0.0, 0)

    @classmethod
    def calculate_identity_and_similarity_from_match_line(
        cls, hmm_sequence: str, mline: str, target_sequence: str
    ) -> Tuple[Tuple[float, int], Tuple[float, int]]:
        """Calculate identity and similarity from PyHMMER's match line."""
        try:
            identity_result = cls.calculate_identity(hmm_sequence, mline, target_sequence)
            if identity_result is None:
                identity_result = (0.0, 0)
            
            similarity_result = cls.calculate_similarity(hmm_sequence, mline, target_sequence)
            if similarity_result is None:
                similarity_result = (0.0, 0)
            
            return identity_result, similarity_result
            
        except Exception as e:
            logger.warning(f"Failed to calculate identity and similarity from match line: {e}")
            return (0.0, 0), (0.0, 0)


# Backward compatibility functions
def calculate_identity_and_similarity(
    hmm_sequence: str, 
    target_sequence: str, 
    mline: str
) -> Tuple[Tuple[float, int], Tuple[float, int]]:
    """Legacy function for backward compatibility."""
    identity_result = AlignmentCalculator.calculate_identity(hmm_sequence, mline, target_sequence)
    similarity_result = AlignmentCalculator.calculate_similarity(hmm_sequence, mline, target_sequence)
    
    if identity_result is None:
        identity_result = (0.0, 0)
    if similarity_result is None:
        similarity_result = (0.0, 0)
    
    return identity_result, similarity_result


def create_match_line(hmm_sequence: str, target_sequence: str) -> str:
    """Legacy function for backward compatibility."""
    return AlignmentCalculator.create_match_line(hmm_sequence, target_sequence)


def calculate_identity_and_similarity_from_sequences(
    hmm_sequence: str, 
    target_sequence: str
) -> Tuple[Tuple[float, int], Tuple[float, int]]:
    """Legacy function for backward compatibility."""
    return AlignmentCalculator.calculate_identity_and_similarity_from_sequences(hmm_sequence, target_sequence)


def calculate_identity_and_similarity_from_match_line(
    hmm_sequence: str, 
    mline: str, 
    target_sequence: str
) -> Tuple[Tuple[float, int], Tuple[float, int]]:
    """Legacy function for backward compatibility."""
    return AlignmentCalculator.calculate_identity_and_similarity_from_match_line(hmm_sequence, mline, target_sequence) 