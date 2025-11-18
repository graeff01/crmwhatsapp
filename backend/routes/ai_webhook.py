"""
Rotas Flask para sistema de qualificação por IA
Integra WhatsApp -> IA -> CRM

NOTA: Rotas temporariamente desabilitadas - em desenvolvimento
Para usar as rotas de IA, configure via factory pattern no app.py
"""
from flask import Blueprint, request, jsonify
from typing import Dict
import os

# Blueprint
ai_bp = Blueprint('ai', __name__, url_prefix='/api/ai')


@ai_bp.route('/status', methods=['GET'])
def get_status():
    """Status do módulo de IA"""
    return jsonify({
        'success': True,
        'status': 'development',
        'message': 'Módulo de qualificação por IA em desenvolvimento',
        'features': {
            'ai_qualification': 'planned',
            'auto_response': 'planned',
            'lead_scoring': 'planned'
        }
    })


@ai_bp.route('/webhook/whatsapp', methods=['POST'])
def whatsapp_webhook():
    """
    Webhook para receber mensagens do WhatsApp
    TEMPORARIAMENTE DESABILITADO
    """
    return jsonify({
        'success': False,
        'error': 'Serviço de qualificação por IA em desenvolvimento',
        'message': 'Use o sistema de IA Assistant principal por enquanto'
    }), 503


@ai_bp.route('/stats', methods=['GET'])
def get_stats():
    """Estatísticas do sistema de qualificação"""
    return jsonify({
        'success': True,
        'stats': {
            'total_conversations': 0,
            'qualified': 0,
            'disqualified': 0,
            'escalated': 0,
            'in_progress': 0
        },
        'message': 'Serviço em desenvolvimento'
    })


@ai_bp.route('/conversations/active', methods=['GET'])
def get_active_conversations():
    """Lista conversas ativas"""
    return jsonify({
        'success': True,
        'conversations': [],
        'total': 0,
        'message': 'Serviço em desenvolvimento'
    })


def register_ai_routes(app):
    """
    Registra rotas de IA no app Flask

    NOTA: As rotas estão em modo de desenvolvimento
    Para habilitar completamente, configure via factory pattern
    """
    app.register_blueprint(ai_bp)
    print("ℹ️  Rotas de IA registradas (modo desenvolvimento)")
