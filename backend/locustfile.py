import os
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

ALICE = "d220cbf2-d52f-4230-8c63-9be15ff2fb5e"
BOB = "2f8976a6-bda2-4a40-b14b-0c0cab8d709f"
CAROL = "d2380873-13dd-4b1e-b598-5c50773a4979"
STRATEGY = os.environ.get("LOAD_TEST_STRATEGY", "nocache")
## mimics a twitter user hammering the api 
## numbers are relative weights; 
## user read feed 10x as often as follow 

class TwitterUser(HttpUser):
    wait_time = between(1, 3)

    @task(10)
    def read_feed(self):
        self.client.get(f"/feed?userId={ALICE}&strategy={STRATEGY}", name="/feed")

    @task(2)
    def create_post(self):
        self.client.post("/posts", json={"author_id": BOB, "content": "load test post"}, name="/posts")

    @task(1)
    def follow(self):
        self.client.post("/follow", json={"follower_id": CAROL, "following_id": ALICE}, name="/follow")


class StepLoad(LoadTestShape):
    # "duration" is cumulative elapsed time, not per-stage length — each stage's
    # actual window is (this duration - previous duration). spawn_rate is bumped
    # on the bigger jumps so the ramp finishes with steady-state time left over.
    stages = [
        {"duration": 30, "users": 10, "spawn_rate": 5},
        {"duration": 60, "users": 50, "spawn_rate": 5},
        {"duration": 90, "users": 100, "spawn_rate": 10},
        {"duration": 120, "users": 200, "spawn_rate": 10},
        {"duration": 150, "users": 300, "spawn_rate": 10},
        {"duration": 180, "users": 400, "spawn_rate": 10},
        {"duration": 210, "users": 500, "spawn_rate": 10},
        {"duration": 250, "users": 600, "spawn_rate": 10},
        {"duration": 290, "users": 700, "spawn_rate": 10},
        {"duration": 330, "users": 800, "spawn_rate": 10},
        {"duration": 380, "users": 1000, "spawn_rate": 20},
        {"duration": 440, "users": 1500, "spawn_rate": 25},
        {"duration": 520, "users": 2000, "spawn_rate": 25},
        {"duration": 600, "users": 3000, "spawn_rate": 25},
        {"duration": 700, "users": 5000, "spawn_rate": 30},
        {"duration": 800, "users": 7000, "spawn_rate": 35},
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
