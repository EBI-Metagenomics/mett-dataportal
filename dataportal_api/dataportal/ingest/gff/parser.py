"""
Shared GFF parsing utilities.

This module exposes the GFFParser used across PPI, Ortholog, and Operon flows.
Currently it re-exports the implementation from the PPI package to avoid code
duplication while providing a stable shared import path.
"""

from ..ppi.gff_parser import GFFParser, GeneInfo  # re-export for shared use

__all__ = ["GFFParser", "GeneInfo"]


