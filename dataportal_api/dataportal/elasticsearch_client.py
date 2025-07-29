from elasticsearch_dsl import connections


def init_es_connection(host, user, password, timeout, max_retries):
    if not user or not password:
        print("⚠️ Skipping Elasticsearch init: missing credentials.")
        return

    connections.create_connection(
        hosts=[host],
        basic_auth=(user, password),
        max_retries=max_retries,
        retry_on_timeout=True,
        sniff_on_start=False,
        sniff_on_connection_fail=False,
        http_compress=True,
        request_timeout=timeout,
        connections_per_node=10,
        retry_on_status=[429, 500, 502, 503, 504],
    )
