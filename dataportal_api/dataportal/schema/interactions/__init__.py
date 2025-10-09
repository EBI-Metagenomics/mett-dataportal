"""Gene/protein interaction schemas."""

from dataportal.schema.interactions.ppi_schemas import (
    PPISearchQuerySchema,
    PPISearchResponseSchema,
    PPINeighborsQuerySchema,
    PPINetworkQuerySchema,
    PPINetworkPropertiesQuerySchema,
    PPIScoreTypesResponseSchema,
)
from dataportal.schema.interactions.ttp_schemas import (
    TTPInteractionQuerySchema,
    TTPFacetedSearchQuerySchema,
    TTPGeneInteractionsQuerySchema,
    TTPCompoundInteractionsQuerySchema,
    TTPHitAnalysisQuerySchema,
    TTPPoolAnalysisQuerySchema,
    TTPDownloadQuerySchema,
)
from dataportal.schema.interactions.fitness_correlation_schemas import (
    GeneCorrelationQuerySchema,
    GenePairCorrelationQuerySchema,
    TopCorrelationsQuerySchema,
    CorrelationSearchQuerySchema,
)

__all__ = [
    # PPI schemas
    "PPISearchQuerySchema",
    "PPISearchResponseSchema",
    "PPINeighborsQuerySchema",
    "PPINetworkQuerySchema",
    "PPINetworkPropertiesQuerySchema",
    "PPIScoreTypesResponseSchema",
    # TTP schemas
    "TTPInteractionQuerySchema",
    "TTPFacetedSearchQuerySchema",
    "TTPGeneInteractionsQuerySchema",
    "TTPCompoundInteractionsQuerySchema",
    "TTPHitAnalysisQuerySchema",
    "TTPPoolAnalysisQuerySchema",
    "TTPDownloadQuerySchema",
    # Fitness correlation schemas
    "GeneCorrelationQuerySchema",
    "GenePairCorrelationQuerySchema",
    "TopCorrelationsQuerySchema",
    "CorrelationSearchQuerySchema",
]
