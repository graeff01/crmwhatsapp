"""
Blueprint de Health Check e Status
Endpoints para monitoramento e diagnóstico
"""
from flask import Blueprint, jsonify
from advanced_cache import get_cache_stats
from logger import get_logger

logger = get_logger(__name__)

# Cria Blueprint
health_bp = Blueprint('health', __name__)


@health_bp.route("/health", methods=["GET"])
def health_check():
    """
    Health check básico

    Response:
        {
            "status": "healthy",
            "service": "crm-whatsapp"
        }
    """
    return jsonify({
        "status": "healthy",
        "service": "crm-whatsapp"
    })


@health_bp.route("/api/cache/stats", methods=["GET"])
def cache_stats():
    """
    Retorna estatísticas do cache

    Response:
        {
            "hits": 150,
            "misses": 30,
            "hit_rate": 0.833,
            "total_requests": 180
        }
    """
    logger.debug("Requisição de estatísticas de cache")
    return jsonify(get_cache_stats())


__all__ = ['health_bp']
