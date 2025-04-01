from elasticsearch import Elasticsearch
from elasticsearch_dsl import connections


def init_es_connection(host, user, password, timeout, max_retries):
    if not user or not password:
        print("⚠️ Skipping Elasticsearch init: missing credentials.")
        return

    connections.create_connection(
        hosts=[host],
        basic_auth=(user, password),
        timeout=timeout,
        max_retries=max_retries,
        retry_on_timeout=True,
        # Keep-alive tuning
        sniff_on_connection_fail=True,
        sniff_on_start=False,
        sniffer_timeout=60.0,
        http_compress=True,
    )
