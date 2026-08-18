from prometheus_client import Counter, Histogram

REQUEST_COUNT = Counter(
    "http_requests_total", "Total HTTP Requests", 
    ["method", "endpoint", "http_status"]
)

REQUEST_DURATION = Histogram(
    "http_request_duration_seconds", "Request duration", 
    ["method", "endpoint"]
)

