from elasticsearch import exceptions as es_exceptions
from elasticsearch_dsl import connections


class AppHealthService:
    # get the default ES connection
    es_client = connections.get_connection()

    def healthz(self):
        try:
            if not self.es_client.ping():
                return 503, {"status": "unhealthy", "reason": "Elasticsearch not reachable"}
        except es_exceptions.ElasticsearchException as e:
            return 503, {"status": "unhealthy", "reason": str(e)}

        return {"status": "ok"}
