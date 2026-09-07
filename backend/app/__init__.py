import time

from flask import Flask, g, request
from flask_cors import CORS

from app.db import pool
from app.metrics import REQUEST_COUNT, REQUEST_DURATION
from app.routes.feed import feed_bp
from app.routes.follow import follow_bp
from app.routes.metrics import metrics_bp
from app.routes.posts import posts_bp


def create_app():
    app = Flask(__name__)
    CORS(app)  # React dev server runs on a different origin/port

    if pool.closed:
        pool.open()

    @app.before_request
    def start_timer():
        g.start_time = time.time()

    @app.after_request
    def record_metrics(response):
        if request.url_rule is not None:
            endpoint = request.url_rule.rule
            duration = time.time() - g.start_time

            REQUEST_DURATION.labels(
                method=request.method, endpoint=endpoint
            ).observe(duration)

            REQUEST_COUNT.labels(
                method=request.method,
                endpoint=endpoint,
                http_status=response.status_code,
            ).inc()

        return response

    app.register_blueprint(posts_bp)
    app.register_blueprint(follow_bp)
    app.register_blueprint(feed_bp)
    app.register_blueprint(metrics_bp)
    return app

#     from app.routes import bp
#     app.register_blueprint(bp)

#     return app
