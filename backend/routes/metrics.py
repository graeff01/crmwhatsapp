"""
Blueprint de Métricas e Dashboards
TODO: Migrar rotas de métricas do app.py para cá
"""
from flask import Blueprint

metrics_bp = Blueprint('metrics', __name__, url_prefix='/api')

# TODO: Migrar rotas:
# - GET /api/metrics
# - GET /api/audit-log

__all__ = ['metrics_bp']
