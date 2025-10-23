"""
Role definitions and constants for API authentication.

This module defines available roles and their descriptions for role-based
access control of API endpoints.
"""

# ==============================================================================
# Role Definitions
# ==============================================================================

class APIRoles:
    """
    Predefined API roles for access control.
    
    Each role grants access to specific experimental data endpoints.
    """
    
    # Full access
    ADMIN = "admin"  # Full access to all endpoints
    
    # Core data access
    READ_ONLY = "read_only"  # Basic genome/gene browsing (no experimental data)
    
    # Experimental data roles
    PROTEOMICS = "proteomics"  # Access to proteomics data
    ESSENTIALITY = "essentiality"  # Access to essentiality data
    FITNESS = "fitness"  # Access to fitness data
    MUTANT_GROWTH = "mutant_growth"  # Access to mutant growth data
    REACTIONS = "reactions"  # Access to metabolic reactions data
    DRUGS = "drugs"  # Access to drug data
    
    # Interaction data roles
    PPI = "ppi"  # Protein-protein interaction data
    TTP = "ttp"  # Transcription factor-target protein data
    FITNESS_CORRELATION = "fitness_correlation"  # Fitness correlation data
    ORTHOLOGS = "orthologs"  # Ortholog data
    OPERONS = "operons"  # Operon data
    
    # Advanced features
    NATURAL_QUERY = "natural_query"  # Natural language query access
    PYHMMER_SEARCH = "pyhmmer_search"  # PyHMMER search access
    
    @classmethod
    def all_roles(cls):
        """Get list of all available roles."""
        return [
            cls.ADMIN,
            cls.READ_ONLY,
            cls.PROTEOMICS,
            cls.ESSENTIALITY,
            cls.FITNESS,
            cls.MUTANT_GROWTH,
            cls.REACTIONS,
            cls.DRUGS,
            cls.PPI,
            cls.TTP,
            cls.FITNESS_CORRELATION,
            cls.ORTHOLOGS,
            cls.OPERONS,
            cls.NATURAL_QUERY,
            cls.PYHMMER_SEARCH,
        ]
    
    @classmethod
    def experimental_data_roles(cls):
        """Get roles related to experimental data."""
        return [
            cls.PROTEOMICS,
            cls.ESSENTIALITY,
            cls.FITNESS,
            cls.MUTANT_GROWTH,
            cls.REACTIONS,
            cls.DRUGS,
        ]
    
    @classmethod
    def interaction_data_roles(cls):
        """Get roles related to interaction data."""
        return [
            cls.PPI,
            cls.TTP,
            cls.FITNESS_CORRELATION,
            cls.ORTHOLOGS,
            cls.OPERONS,
        ]
    
    @classmethod
    def get_role_description(cls, role):
        """Get human-readable description of a role."""
        descriptions = {
            cls.ADMIN: "Full access to all API endpoints",
            cls.READ_ONLY: "Basic genome/gene browsing (no experimental data)",
            cls.PROTEOMICS: "Access to proteomics experimental data",
            cls.ESSENTIALITY: "Access to gene essentiality data",
            cls.FITNESS: "Access to fitness data",
            cls.MUTANT_GROWTH: "Access to mutant growth data",
            cls.REACTIONS: "Access to metabolic reactions data",
            cls.DRUGS: "Access to drug interaction data",
            cls.PPI: "Access to protein-protein interaction data",
            cls.TTP: "Access to transcription factor-target protein data",
            cls.FITNESS_CORRELATION: "Access to fitness correlation data",
            cls.ORTHOLOGS: "Access to ortholog data",
            cls.OPERONS: "Access to operon data",
            cls.NATURAL_QUERY: "Access to natural language query API",
            cls.PYHMMER_SEARCH: "Access to PyHMMER protein search",
        }
        return descriptions.get(role, f"Custom role: {role}")


# ==============================================================================
# Role Groups (Presets)
# ==============================================================================

class RolePresets:
    """
    Predefined role combinations for common use cases.
    """
    
    @staticmethod
    def full_access():
        """All roles - complete API access."""
        return [APIRoles.ADMIN]
    
    @staticmethod
    def experimental_data_basic():
        """Basic access - core data + common experimental data."""
        return [
            APIRoles.READ_ONLY,
            APIRoles.PROTEOMICS,
            APIRoles.ESSENTIALITY,
            APIRoles.FITNESS,
        ]
    
    @staticmethod
    def experimental_interaction_data():
        """Full access to all experimental data."""
        return [
            APIRoles.READ_ONLY,
            APIRoles.PROTEOMICS,
            APIRoles.ESSENTIALITY,
            APIRoles.FITNESS,
            APIRoles.MUTANT_GROWTH,
            APIRoles.REACTIONS,
            APIRoles.DRUGS,
            APIRoles.PPI,
            APIRoles.TTP,
            APIRoles.FITNESS_CORRELATION,
            APIRoles.ORTHOLOGS,
            APIRoles.OPERONS,
        ]
    
    @staticmethod
    def experimental_only():
        """Experimental data only - no interaction data."""
        return APIRoles.experimental_data_roles()
    
    @staticmethod
    def interactions_only():
        """Interaction data only - no experimental data."""
        return APIRoles.interaction_data_roles()
    
    @staticmethod
    def researcher():
        """For researchers - all data + advanced features."""
        return [
            APIRoles.ADMIN,
            APIRoles.NATURAL_QUERY,
            APIRoles.PYHMMER_SEARCH,
        ]


# ==============================================================================
# Helper Functions
# ==============================================================================

def get_role_choices():
    """
    Get role choices for Django forms.
    
    Returns:
        List of (role_value, role_label) tuples
    """
    return [
        (role, f"{role} - {APIRoles.get_role_description(role)}")
        for role in APIRoles.all_roles()
    ]


def validate_roles(roles):
    """
    Validate that all roles are valid.
    
    Args:
        roles: List of role names
        
    Returns:
        Tuple of (is_valid, invalid_roles)
    """
    if not roles:
        return True, []
    
    valid_roles = set(APIRoles.all_roles())
    invalid = [r for r in roles if r not in valid_roles]
    
    return len(invalid) == 0, invalid

