import os

from prometheus_client import Counter, Histogram, start_http_server

automation_runs = Counter(
    'network_automation_runs_total',
    'Total automation runs',
    ['status']
)

automation_duration = Histogram(
    'network_automation_duration_seconds',
    'Automation execution time',
    buckets=(1, 5, 10, 30, 60, 300)
)

metrics_port = int(os.environ.get("METRICS_PORT", "8000"))
start_http_server(metrics_port)
automation_runs.labels(status='success').inc()
automation_duration.observe(15.5)
