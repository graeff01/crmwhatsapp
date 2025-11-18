"""
Blueprint de Sistema de Alertas
TODO: Migrar rotas de alertas do app.py para cá
"""
from flask import Blueprint

alerts_bp = Blueprint('alerts', __name__, url_prefix='/api/alerts')

# TODO: Migrar rotas:
# - GET /api/alerts
# - POST /api/alerts/:id/resolve
# - GET /api/alerts/dashboard
# - POST /api/alerts/check-now

__all__ = ['alerts_bp']
