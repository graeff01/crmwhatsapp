"""
Blueprint de Tags e SLA
TODO: Migrar rotas de tags/SLA do app.py para cá
"""
from flask import Blueprint

tags_sla_bp = Blueprint('tags_sla', __name__, url_prefix='/api')

# TODO: Migrar rotas:
# - GET/POST /api/tags
# - GET/POST /api/leads/:id/tags
# - DELETE /api/leads/:id/tags/:tag_id
# - GET /api/leads/:id/sla
# - GET /api/sla/metrics
# - GET /api/sla/alerts

__all__ = ['tags_sla_bp']
