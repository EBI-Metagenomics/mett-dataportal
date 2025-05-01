import pytest
from elasticsearch_dsl import connections
from unittest.mock import MagicMock, patch

@pytest.fixture(autouse=True, scope="session")
def patch_elasticsearch_dsl():
    # Patch all ES DSL connection creation to avoid real ES calls
    with patch("elasticsearch_dsl.connections.connections.get_connection") as mock_conn:
        mock_conn.return_value = MagicMock()
        yield
