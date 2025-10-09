from elasticsearch import exceptions as es_exceptions
from elasticsearch_dsl import connections


class AppHealthService:

    def get_es_client(self):
        return connections.get_connection()

    def healthz(self):
        try:
            if not self.get_es_client().ping():
                return 503, {
                    "status": "unhealthy",
                    "reason": "Elasticsearch not reachable",
                }
        except es_exceptions.ElasticsearchException as e:
            return 503, {"status": "unhealthy", "reason": str(e)}

        return {"status": "ok"}
