import os
import random
import gevent
from locust import HttpUser, LoadTestShape, events, task, between
from prometheus_client import Counter, Gauge, Histogram, start_http_server

LOCUST_USER_COUNT = Gauge("locust_user_count", "Concurrent simulated users")
LOCUST_REQUEST_DURATION = Histogram(
    "locust_request_duration_seconds", "Client-observed request duration",
    ["method", "name"]
)
LOCUST_REQUEST_FAILURES = Counter(
    "locust_request_failures_total", "Client-observed request failures",
    ["method", "name"]
)
METRICS_PORT = 9646

STRATEGY = os.environ.get("LOAD_TEST_STRATEGY", "nocache")

# One real seeded user id per line (see plan/mini-concurrency-comparison-plan-2026-09-21.md,
# Step "getting seeded user ids" — exported via:
#   docker compose exec postgres psql -U twitter_clone -d twitter_clone -t -A -c "SELECT id FROM users;" > backend/scripts/seeded_user_ids.txt
_ids_path = os.path.join(os.path.dirname(__file__), "scripts", "seeded_user_ids.txt")
with open(_ids_path) as f:
    SEEDED_USER_IDS = [line.strip() for line in f if line.strip()]


class TwitterUser(HttpUser):
    wait_time = between(1, 3)

    def on_start(self):
        # each simulated Locust user sticks to one real user id for its whole
        # run, modeling "one person repeatedly checking their own feed" —
        # rather than a fresh random user on every request. Across many
        # concurrent simulated users this still spreads reads/cache keys
        # over the population instead of hammering a single feed.
        self.user_id = random.choice(SEEDED_USER_IDS)

    @task(10)
    def read_feed(self):
        self.client.get(
            f"/feed?userId={self.user_id}&strategy={STRATEGY}",
            name=f"/feed?strategy={STRATEGY}",
        )

    @task(2)
    def create_post(self):
        author_id = random.choice(SEEDED_USER_IDS)
        self.client.post(
            "/posts",
            json={"author_id": author_id, "content": "strategy comparison load test post"},
            name="/posts",
        )


class MiniRamp(LoadTestShape):
    # Ramps to ~300 concurrent users (near the knee from the original
    # baseline ramp), then holds steady for 2 minutes so p95/p99 have time
    # to settle into a stable reading rather than being caught mid-climb.
    stages = [
        {"duration": 20, "users": 20, "spawn_rate": 5},
        {"duration": 40, "users": 100, "spawn_rate": 10},
        {"duration": 60, "users": 200, "spawn_rate": 10},
        {"duration": 80, "users": 300, "spawn_rate": 10},
        {"duration": 200, "users": 300, "spawn_rate": 10},  # steady state: 120s hold at 300
    ]

    def tick(self):
        run_time = self.get_run_time()
        for stage in self.stages:
            if run_time < stage["duration"]:
                return (stage["users"], stage["spawn_rate"])
        return None


@events.init.add_listener
def on_locust_init(environment, **kwargs):
    # Locust doesn't export concurrent user count to Prometheus itself, so we
    # poll environment.runner.user_count and republish it as a gauge on our
    # own /metrics endpoint (separate port from the Flask app under test).
    start_http_server(METRICS_PORT)

    def report_user_count():
        while True:
            if environment.runner is not None:
                LOCUST_USER_COUNT.set(environment.runner.user_count)
            gevent.sleep(1)

    gevent.spawn(report_user_count)


@events.request.add_listener
def on_request(request_type, name, response_time, response_length, exception, **kwargs):
    # response_time is ms; Flask-side histogram uses seconds, so match units here
    # to keep both comparable on the same Grafana axis.
    LOCUST_REQUEST_DURATION.labels(method=request_type, name=name).observe(response_time / 1000)
    if exception:
        LOCUST_REQUEST_FAILURES.labels(method=request_type, name=name).inc()
