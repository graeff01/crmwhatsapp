"""
Blueprint de WhatsApp e Webhooks  
TODO: Migrar rotas de WhatsApp do app.py para cá
"""
from flask import Blueprint

whatsapp_bp = Blueprint('whatsapp', __name__, url_prefix='/api')

# TODO: Migrar rotas:
# - POST /api/webhook/message
# - POST /api/simulate/message
# - GET /api/whatsapp/status

__all__ = ['whatsapp_bp']
