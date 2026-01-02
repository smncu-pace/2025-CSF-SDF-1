#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import logging
from datetime import datetime
from flask import Flask, jsonify
from flask_cors import CORS

from config import Config
from models import db
from routes.memory_routes import memory_bp
from routes.user_routes import user_bp


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    db.init_app(app)

    # CORS
    CORS(app, resources={r"/api/*": {"origins": "*"}})

    # 注册蓝图
    app.register_blueprint(memory_bp, url_prefix="/api")
    app.register_blueprint(user_bp, url_prefix="/api")

    @app.route("/")
    def index():
        return jsonify({
            "app": "Memory Library Backend",
            "version": "1.0.0",
            "time": datetime.now().isoformat(),
        })

    @app.route("/health")
    def health():
        return jsonify({"status": "ok", "time": datetime.now().isoformat()})

    @app.errorhandler(404)
    def not_found(e):
        return jsonify({"error": "not found"}), 404

    @app.errorhandler(500)
    def internal(e):
        return jsonify({"error": "internal error"}), 500

    if not app.debug:
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s %(levelname)s: %(message)s [%(pathname)s:%(lineno)d]"
        )

    return app


def _get_local_ip():
    import socket
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            return s.getsockname()[0]
    except Exception:
        return "127.0.0.1"


if __name__ == "__main__":
    app = create_app()
    port = app.config.get("PORT",1145)
    ip = _get_local_ip()

    print("=" * 60)
    print("Memory Library Backend")
    print(f"Local    : http://127.0.0.1:{port}")
    print(f"LAN      : http://{ip}:{port}")
    print("=" * 60)

    app.run(host="0.0.0.0", port=port, debug=app.config["DEBUG"], threaded=True)
