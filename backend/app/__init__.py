from flask import Flask
from flask_cors import CORS

from app.routes.posts import posts_bp
from app.routes.follow import follow_bp
from app.routes.feed import feed_bp

from app.db import pool 

def create_app():
    app = Flask(__name__)
    CORS(app)  # React dev server runs on a different origin/port

    if pool.closed: 
        pool.open()

    app.register_blueprint(posts_bp)
    app.register_blueprint(follow_bp)
    app.register_blueprint(feed_bp)
    return app

#     from app.routes import bp
#     app.register_blueprint(bp)

#     return app