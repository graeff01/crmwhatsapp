"""
Blueprint de Gerenciamento de Leads
TODO: Migrar rotas de leads do app.py para cá
"""
from flask import Blueprint

leads_bp = Blueprint('leads', __name__, url_prefix='/api/leads')

# TODO: Migrar rotas:
# - GET /api/leads
# - GET /api/leads/queue
# - GET /api/leads/:id
# - POST /api/leads/:id/assign
# - PUT /api/leads/:id/status
# - POST /api/leads/:id/transfer
# - GET /api/leads/:id/messages
# - POST /api/leads/:id/messages
# - GET /api/leads/:id/notes
# - POST /api/leads/:id/notes
# - GET /api/lead/:id/logs

__all__ = ['leads_bp']
