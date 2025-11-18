"""
Blueprint de Configurações de Gestores
TODO: Migrar rotas de gestores do app.py para cá
"""
from flask import Blueprint

gestor_bp = Blueprint('gestor', __name__, url_prefix='/api/gestores')

# TODO: Migrar rotas:
# - GET/POST/DELETE /api/gestores/whatsapp-config
# - POST /api/gestores/whatsapp-config/test

__all__ = ['gestor_bp']
