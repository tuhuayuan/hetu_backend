from urllib.parse import urlencode
from django.conf import settings
import requests


class PrometheusQueryError(Exception):
    pass


def query_prometheus(query_str):
    query_params = urlencode({"query": query_str})
    url = f"{settings.PROMETHEUS_URL}/api/v1/query?{query_params}"

    try:
        response = requests.get(url, timeout=(3, 5))
        response.raise_for_status()  # Raises HTTPError for bad responses (4xx or 5xx)
        query_data = response.json()

        if query_data["status"] != "success":
            raise PrometheusQueryError(f'tsdb error {query_data["error"]}')

        return query_data
    except requests.RequestException as e:
        raise PrometheusQueryError(f"tsdb error: {str(e)}")
