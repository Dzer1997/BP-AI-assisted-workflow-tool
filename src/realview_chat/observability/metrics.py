from prometheus_client import Counter, Histogram

HTTP_REQUESTS_TOTAL = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["endpoint", "method", "status"]
)

REQUEST_DURATION = Histogram(
    "http_request_duration_seconds",
    "Request duration in seconds",
    ["endpoint"]
)