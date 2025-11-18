"""
Rotas Flask para sistema de qualificação por IA
Integra WhatsApp -> IA -> CRM
"""
from flask import Blueprint, request, jsonify
from typing import Dict
import asyncio
import os

from ai_qualification.engine import QualificationEngine
from ai_qualification.providers.openai_provider import OpenAIProvider
from ai_qualification.models import QualificationCriteria
from services.lead_service import LeadService
from services.whatsapp_service import WhatsAppService

# Blueprint
ai_bp = Blueprint('ai', __name__, url_prefix='/api/ai')

# Variáveis globais para lazy initialization
ai_provider = None
qualification_engine = None
lead_service = None
whatsapp_service = None


def get_ai_provider():
    """Inicializa AI Provider (lazy)"""
    global ai_provider
    if ai_provider is None:
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise ValueError(
                "OPENAI_API_KEY não configurada. "
                "Configure no arquivo .env para usar o sistema de IA."
            )

        ai_provider = OpenAIProvider(
            api_key=api_key,
            model=os.getenv('OPENAI_MODEL', 'gpt-3.5-turbo')
        )
    return ai_provider


def get_qualification_engine():
    """Inicializa Qualification Engine (lazy)"""
    global qualification_engine
    if qualification_engine is None:
        qualification_engine = QualificationEngine(
            ai_provider=get_ai_provider(),
            business_type=os.getenv('BUSINESS_TYPE', 'services'),
            qualification_criteria=QualificationCriteria(
                required_fields=['name', 'phone', 'interest'],
                min_score=50,
                max_attempts=5
            )
        )
    return qualification_engine


def get_lead_service():
    """Inicializa Lead Service (lazy)"""
    global lead_service
    if lead_service is None:
        lead_service = LeadService()
    return lead_service


def get_whatsapp_service():
    """Inicializa WhatsApp Service (lazy)"""
    global whatsapp_service
    if whatsapp_service is None:
        whatsapp_service = WhatsAppService()
    return whatsapp_service


@ai_bp.route('/webhook/whatsapp', methods=['POST'])
async def whatsapp_webhook():
    """
    Webhook para receber mensagens do WhatsApp
    Processa via IA e responde automaticamente
    """
    try:
        data = request.json
        
        # Valida payload
        if not data or 'phone' not in data or 'message' not in data:
            return jsonify({
                'success': False,
                'error': 'Payload inválido'
            }), 400
        
        phone = data['phone']
        message = data['message']
        contact_name = data.get('name', '')

        # Processa mensagem via IA
        engine = get_qualification_engine()
        result = await engine.process_message(
            phone=phone,
            message=message,
            metadata={'contact_name': contact_name}
        )

        # Envia resposta via WhatsApp
        whatsapp = get_whatsapp_service()
        await whatsapp.send_message(
            phone=phone,
            message=result['response']
        )

        # Se qualificado ou escalado, envia para CRM
        if result.get('should_send_to_crm'):
            lead_svc = get_lead_service()
            crm_lead = await lead_svc.create_from_ai_qualification(
                result['crm_data']
            )
            result['crm_lead_id'] = crm_lead['id']
        
        return jsonify({
            'success': True,
            'status': result['status'],
            'response_sent': True,
            'crm_lead_created': result.get('should_send_to_crm', False),
            'data': result
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@ai_bp.route('/stats', methods=['GET'])
def get_stats():
    """Retorna estatísticas do sistema de qualificação"""
    try:
        engine = get_qualification_engine()
        stats = engine.get_stats()
        return jsonify({
            'success': True,
            'stats': stats
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@ai_bp.route('/conversations/active', methods=['GET'])
def get_active_conversations():
    """Lista conversas ativas"""
    try:
        engine = get_qualification_engine()
        conversations = []
        for phone, conv in engine.active_conversations.items():
            conversations.append({
                'phone': phone,
                'status': conv.status.value,
                'score': conv.score,
                'attempts': conv.attempts,
                'collected_data': conv.collected_data,
                'messages_count': len(conv.messages),
                'started_at': conv.started_at
            })
        
        return jsonify({
            'success': True,
            'conversations': conversations,
            'total': len(conversations)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@ai_bp.route('/conversations/<phone>', methods=['GET'])
def get_conversation(phone: str):
    """Obtém detalhes de uma conversa específica"""
    try:
        engine = get_qualification_engine()
        conversation = engine.get_conversation(phone)
        
        if not conversation:
            return jsonify({
                'success': False,
                'error': 'Conversa não encontrada'
            }), 404
        
        return jsonify({
            'success': True,
            'conversation': {
                'phone': conversation.phone,
                'status': conversation.status.value,
                'score': conversation.score,
                'attempts': conversation.attempts,
                'collected_data': conversation.collected_data,
                'messages': [
                    {'role': m.role, 'content': m.content, 'timestamp': m.timestamp}
                    for m in conversation.messages
                ],
                'notes': conversation.notes,
                'started_at': conversation.started_at
            }
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@ai_bp.route('/conversations/<phone>/end', methods=['POST'])
def end_conversation(phone: str):
    """Encerra uma conversa manualmente"""
    try:
        engine = get_qualification_engine()
        data = request.json or {}
        reason = data.get('reason', 'Manual')

        engine.end_conversation(phone, reason)
        
        return jsonify({
            'success': True,
            'message': 'Conversa encerrada'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@ai_bp.route('/conversations/<phone>/escalate', methods=['POST'])
async def escalate_conversation(phone: str):
    """Escala conversa para atendimento humano manualmente"""
    try:
        engine = get_qualification_engine()
        conversation = engine.get_conversation(phone)

        if not conversation:
            return jsonify({
                'success': False,
                'error': 'Conversa não encontrada'
            }), 404

        # Força escalação
        result = await engine._handle_escalation(conversation)

        # Envia mensagem de escalação
        whatsapp = get_whatsapp_service()
        await whatsapp.send_message(
            phone=phone,
            message=result['response']
        )

        # Cria lead no CRM
        if result.get('should_send_to_crm'):
            lead_svc = get_lead_service()
            crm_lead = await lead_svc.create_from_ai_qualification(
                result['crm_data']
            )
            result['crm_lead_id'] = crm_lead['id']
        
        return jsonify({
            'success': True,
            'message': 'Conversa escalada',
            'data': result
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@ai_bp.route('/test', methods=['POST'])
async def test_qualification():
    """
    Endpoint para testar o sistema sem WhatsApp
    Útil para desenvolvimento e testes
    """
    try:
        engine = get_qualification_engine()
        data = request.json

        if not data or 'phone' not in data or 'message' not in data:
            return jsonify({
                'success': False,
                'error': 'Envie phone e message'
            }), 400

        result = await engine.process_message(
            phone=data['phone'],
            message=data['message'],
            metadata=data.get('metadata', {})
        )
        
        return jsonify({
            'success': True,
            'result': result
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@ai_bp.route('/config', methods=['GET', 'PUT'])
def manage_config():
    """Gerencia configurações do sistema de IA"""
    engine = get_qualification_engine()

    if request.method == 'GET':
        return jsonify({
            'success': True,
            'config': {
                'business_type': engine.business_type,
                'model': engine.ai_provider.model,
                'min_score': engine.criteria.min_score,
                'max_attempts': engine.criteria.max_attempts,
                'required_fields': engine.criteria.required_fields
            }
        })

    else:  # PUT
        try:
            data = request.json

            # Atualiza configurações (em produção, persistir em DB)
            if 'min_score' in data:
                engine.criteria.min_score = data['min_score']

            if 'max_attempts' in data:
                engine.criteria.max_attempts = data['max_attempts']

            if 'business_type' in data:
                engine.business_type = data['business_type']
            
            return jsonify({
                'success': True,
                'message': 'Configurações atualizadas'
            })
        except Exception as e:
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500


def register_ai_routes(app):
    """Registra rotas de IA no app Flask"""
    app.register_blueprint(ai_bp)