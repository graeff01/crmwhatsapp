"""
Rotas Flask para sistema de qualificação por IA
Integra WhatsApp -> IA -> CRM
"""
from flask import Blueprint, request, jsonify
from typing import Dict
import asyncio
import os

from ..ai_qualification.engine import QualificationEngine
from ..ai_qualification.providers.openai_provider import OpenAIProvider
from ..ai_qualification.models import QualificationCriteria
from ..services.lead_service import LeadService
from ..services.whatsapp_service import WhatsAppService

# Blueprint
ai_bp = Blueprint('ai', __name__, url_prefix='/api/ai')

# Inicializa engine (em produção, usar factory pattern)
ai_provider = OpenAIProvider(
    api_key=os.getenv('OPENAI_API_KEY'),
    model=os.getenv('OPENAI_MODEL', 'gpt-3.5-turbo')
)

qualification_engine = QualificationEngine(
    ai_provider=ai_provider,
    business_type=os.getenv('BUSINESS_TYPE', 'services'),
    qualification_criteria=QualificationCriteria(
        required_fields=['name', 'phone', 'interest'],
        min_score=50,
        max_attempts=5
    )
)

# Serviços
lead_service = LeadService()
whatsapp_service = WhatsAppService()


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
        result = await qualification_engine.process_message(
            phone=phone,
            message=message,
            metadata={'contact_name': contact_name}
        )
        
        # Envia resposta via WhatsApp
        await whatsapp_service.send_message(
            phone=phone,
            message=result['response']
        )
        
        # Se qualificado ou escalado, envia para CRM
        if result.get('should_send_to_crm'):
            crm_lead = await lead_service.create_from_ai_qualification(
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
        stats = qualification_engine.get_stats()
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
        conversations = []
        for phone, conv in qualification_engine.active_conversations.items():
            conversations.append({
                'phone': phone,
                'status': conv.status.value,
                'score': conv.qualification_score,
                'attempts': conv.attempts,
                'collected_data': conv.collected_data,
                'messages_count': len(conv.messages),
                'started_at': conv.started_at.isoformat()
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
        conversation = qualification_engine.get_conversation(phone)
        
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
                'score': conversation.qualification_score,
                'attempts': conversation.attempts,
                'collected_data': conversation.collected_data,
                'messages': conversation.get_conversation_history(),
                'notes': conversation.notes,
                'started_at': conversation.started_at.isoformat()
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
        data = request.json or {}
        reason = data.get('reason', 'Manual')
        
        qualification_engine.end_conversation(phone, reason)
        
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
        conversation = qualification_engine.get_conversation(phone)
        
        if not conversation:
            return jsonify({
                'success': False,
                'error': 'Conversa não encontrada'
            }), 404
        
        # Força escalação
        result = await qualification_engine._handle_escalation(conversation)
        
        # Envia mensagem de escalação
        await whatsapp_service.send_message(
            phone=phone,
            message=result['response']
        )
        
        # Cria lead no CRM
        if result.get('should_send_to_crm'):
            crm_lead = await lead_service.create_from_ai_qualification(
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
        data = request.json
        
        if not data or 'phone' not in data or 'message' not in data:
            return jsonify({
                'success': False,
                'error': 'Envie phone e message'
            }), 400
        
        result = await qualification_engine.process_message(
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
    if request.method == 'GET':
        return jsonify({
            'success': True,
            'config': {
                'business_type': qualification_engine.business_type,
                'model': qualification_engine.ai_provider.model,
                'min_score': qualification_engine.criteria.min_score,
                'max_attempts': qualification_engine.criteria.max_attempts,
                'required_fields': qualification_engine.criteria.required_fields
            }
        })
    
    else:  # PUT
        try:
            data = request.json
            
            # Atualiza configurações (em produção, persistir em DB)
            if 'min_score' in data:
                qualification_engine.criteria.min_score = data['min_score']
            
            if 'max_attempts' in data:
                qualification_engine.criteria.max_attempts = data['max_attempts']
            
            if 'business_type' in data:
                qualification_engine.business_type = data['business_type']
            
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