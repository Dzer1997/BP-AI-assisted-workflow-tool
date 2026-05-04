from prometheus_client import Counter, Histogram

API_REQUESTS_TOTAL = Counter(
    "api_requests_total",
    "Total API requests",
    ["method", "path", "status_code"]
)

api_request_duration_seconds = Histogram(
    "api_request_duration_seconds",
    "Duration of API requests",
    ["method", "path"]
)

pipeline_runs_total = Counter(
    "pipeline_runs_total",
    "Pipeline run status",
    ["status"]
)

pipeline_step_duration_seconds = Histogram(
    "pipeline_step_duration_seconds",
    "Duration of each pipeline step",
    ["step"]
)

db_operations_total = Counter(
    "db_operations_total",
    "DB operations",
    ["operation", "status"]
)

db_operation_duration_seconds = Histogram(
    "db_operation_duration_seconds",
    "Duration of DB operation",
    ["operation"]
)

errors_total = Counter(
    "errors_total",
    "Error counter",
    ["layer"]
)