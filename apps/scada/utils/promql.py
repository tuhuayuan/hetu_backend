from urllib.parse import urlencode
from django.conf import settings
import requests


class PrometheusQueryError(Exception):
    pass


def promql_query(query_str):
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


def promql_query_range(
    query: str,
    start_time: int,
    end_time: int,
    step: int,
):
    """
    Query Prometheus /api/v1/query_range endpoint.

    Args:
    - query (str): Prometheus query expression.
    - start_time (int): Start time in seconds since the Unix epoch.
    - end_time (int): End time in seconds since the Unix epoch.
    - step (int): Query step in seconds.

    Returns:
    - list: Result array or raise an error.
    """
    try:
        # Prepare the request parameters
        params = {
            "query": query,
            "start": start_time,
            "end": end_time,
            "step": step,
        }

        # Make the request to Prometheus API
        response = requests.get(
            f"{settings.PROMETHEUS_URL}/api/v1/query_range", params=params
        )
        response.raise_for_status()  # Raise an HTTPError for bad responses

        # Parse and return the result array from the JSON response
        result = response.json().get("data", {}).get("result", [])
        return result

    except requests.exceptions.RequestException as e:
        raise PrometheusQueryError(f"tsdb error: {str(e)}")
