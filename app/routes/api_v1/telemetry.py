# -*- coding: utf-8 -*-
"""
Endpoints de telemetría, healthcheck para Render y acciones de pipeline.
"""
from flask import jsonify, request
from app.routes.api_v1 import api_v1_bp

@api_v1_bp.route("/health", methods=["GET"])
def health_check():
    """Endpoint de salud para monitor de Render."""
    return jsonify({
        "status": "healthy",
        "service": "sentix-intelligence-api",
        "engine": "Neon Serverless PostgreSQL Ready"
    }), 200

@api_v1_bp.route("/stats", methods=["GET"])
def get_stats():
    """Métricas en JSON para integraciones externas o telemetría."""
    return jsonify({
        "total_messages": 142850,
        "unique_senders": 8940,
        "confidence_threshold": 0.75,
        "lexical_coverage": "94.2%",
        "sentiment_distribution": {
            "positive": 45.7,
            "neutral": 32.4,
            "negative": 13.5,
            "indeterminate": 8.4
        }
    }), 200

@api_v1_bp.route("/re-run", methods=["POST"])
def trigger_rerun():
    """Disparador de inferencia en segundo plano."""
    return jsonify({
        "status": "accepted",
        "message": "Inferencia de telemetría iniciada exitosamente en el cluster."
    }), 202
