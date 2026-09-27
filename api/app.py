"""Flask application factory for the business intelligence API."""

from __future__ import annotations

import logging
import os
from typing import Any
from pathlib import Path

from flask import Flask, jsonify, request, send_from_directory

from api.routes.analytics import analytics_bp
from api.routes.ai import ai_bp
from api.routes.health import health_bp
from api.routes.prediction import prediction_bp


def create_app(test_config: dict[str, Any] | None = None) -> Flask:
    frontend_dir = Path(__file__).resolve().parents[1] / "frontend"
    app = Flask(__name__, static_folder=str(frontend_dir), static_url_path="/static")
    app.config.from_mapping(
        JSON_SORT_KEYS=False,
        DEBUG=os.getenv("APP_DEBUG", "false").lower() in {"1", "true", "yes"},
    )
    if test_config:
        app.config.update(test_config)

    logging.basicConfig(level=logging.INFO)
    logger = app.logger
    app.register_blueprint(health_bp)
    app.register_blueprint(analytics_bp)
    app.register_blueprint(prediction_bp)
    app.register_blueprint(ai_bp)

    @app.get("/")
    def index():
        return send_from_directory(frontend_dir, "index.html")

    @app.before_request
    def log_request() -> None:
        logger.info("API request: %s %s", request.method, request.path)

    @app.errorhandler(ValueError)
    def handle_validation_error(error: ValueError):
        return jsonify({"error": {"code": "validation_error", "message": str(error)}}), 400

    @app.errorhandler(404)
    def handle_not_found(_error: object):
        return jsonify({"error": {"code": "not_found", "message": "Endpoint not found."}}), 404

    @app.errorhandler(Exception)
    def handle_unexpected_error(error: Exception):
        logger.exception("Unhandled API error: %s", error)
        return jsonify({"error": {"code": "internal_error", "message": "An internal server error occurred."}}), 500

    return app


app = create_app()


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=app.config.get("DEBUG", False))
