import pytest
from unittest.mock import MagicMock, patch


@pytest.fixture(autouse=True, scope="session")
def patch_elasticsearch_dsl():
    # Patch all ES DSL connection creation to avoid real ES calls
    with patch("elasticsearch_dsl.connections.connections.get_connection") as mock_conn:
        mock_conn.return_value = MagicMock()
        yield


@pytest.fixture(autouse=True, scope="session")
def patch_celery():
    # Mock Celery to prevent import errors during testing
    with patch.dict(
        "sys.modules",
        {
            "celery": MagicMock(),
            "celery.app": MagicMock(),
            "celery.app.base": MagicMock(),
            "celery.app.control": MagicMock(),
            "celery.app.task": MagicMock(),
            "celery.utils": MagicMock(),
            "celery.utils.log": MagicMock(),
            "celery.utils.time": MagicMock(),
            "celery.utils.timeutils": MagicMock(),
            "celery.utils.imports": MagicMock(),
            "celery.utils.functional": MagicMock(),
            "celery.utils.text": MagicMock(),
            "celery.utils.term": MagicMock(),
            "celery.utils.threads": MagicMock(),
            "celery.utils.timer2": MagicMock(),
            "celery.utils.uuid": MagicMock(),
            "celery.utils.worker": MagicMock(),
            "celery.utils.worker_direct": MagicMock(),
            "celery.utils.worker_control": MagicMock(),
            "celery.utils.worker_direct_control": MagicMock(),
            "celery.utils.worker_direct_control_control": MagicMock(),
            "celery.utils.worker_direct_control_control_control": MagicMock(),
            "celery.utils.worker_direct_control_control_control_control": MagicMock(),
            "celery.utils.worker_direct_control_control_control_control_control": MagicMock(),
            "celery.utils.worker_direct_control_control_control_control_control_control": MagicMock(),
            "celery.utils.worker_direct_control_control_control_control_control_control_control": MagicMock(),
            "celery.utils.worker_direct_control_control_control_control_control_control_control_control": MagicMock(),
            "celery.utils.worker_direct_control_control_control_control_control_control_control_control_control": MagicMock(),
            "celery.utils.worker_direct_control_control_control_control_control_agent_control_control_control_control_agent_control_control": MagicMock(),
        },
    ):
        yield


@pytest.fixture(autouse=True, scope="session")
def patch_django_settings():
    # Mock Django settings to prevent database connection attempts
    with patch("django.conf.settings") as mock_settings:
        mock_settings.DATABASES = {
            "default": {
                "ENGINE": "django.db.backends.sqlite3",
                "NAME": ":memory:",
            }
        }
        mock_settings.INSTALLED_APPS = []
        mock_settings.MIDDLEWARE = []
        mock_settings.SECRET_KEY = "test-secret-key"
        mock_settings.DEBUG = True
        yield


@pytest.fixture(autouse=True, scope="session")
def patch_database_connections():
    # Mock all database connection attempts
    with patch("django.db.connections") as mock_connections:
        mock_connections.databases = {"default": {}}
        mock_connections.all.return_value = [MagicMock()]
        yield


@pytest.fixture(autouse=True, scope="session")
def patch_django_db():
    # Mock Django database operations
    with patch("django.db.backends.base.base.BaseDatabaseWrapper") as mock_db:
        mock_db.ensure_connection = MagicMock()
        mock_db.close = MagicMock()
        yield


@pytest.fixture(autouse=True, scope="session")
def patch_elasticsearch():
    # Mock Elasticsearch client
    with patch("elasticsearch.Elasticsearch") as mock_es:
        mock_es.return_value = MagicMock()
        yield


@pytest.fixture(autouse=True, scope="session")
def patch_openai():
    # Mock OpenAI client
    with patch("openai.OpenAI") as mock_openai:
        mock_openai.return_value = MagicMock()
        yield
