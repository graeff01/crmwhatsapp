"""
Notification Service
Sistema profissional de notificações em tempo real

Tipos de notificações:
- novo_lead: Novo lead chegou
- nova_mensagem: Lead enviou mensagem
- sla_alerta: SLA próximo do limite
- status_mudou: Status do lead alterado
- lead_atribuido: Lead atribuído ao vendedor
"""

from datetime import datetime
from typing import Dict, Any, List
from flask_socketio import SocketIO


class NotificationService:
    """
    Serviço de notificações em tempo real
    """
    
    # Prioridades de notificação
    PRIORITY_LOW = 'low'
    PRIORITY_MEDIUM = 'medium'
    PRIORITY_HIGH = 'high'
    PRIORITY_URGENT = 'urgent'
    
    # Tipos de notificação
    TYPE_NEW_LEAD = 'novo_lead'
    TYPE_NEW_MESSAGE = 'nova_mensagem'
    TYPE_SLA_ALERT = 'sla_alerta'
    TYPE_STATUS_CHANGED = 'status_mudou'
    TYPE_LEAD_ASSIGNED = 'lead_atribuido'
    TYPE_LEAD_TRANSFERRED = 'lead_transferido'
    
    def __init__(self, socketio: SocketIO):
        """
        Inicializa o serviço de notificações
        
        Args:
            socketio: Instância do SocketIO
        """
        self.socketio = socketio
        print("🔔 Serviço de notificações inicializado")
    
    def notify_new_lead(self, lead: Dict[str, Any], room: str = 'gestores'):
        """
        Notifica sobre novo lead
        
        Args:
            lead: Dados do lead
            room: Sala para enviar (gestores, vendedores, etc)
        """
        notification = {
            'id': f"lead_{lead['id']}_{datetime.now().timestamp()}",
            'type': self.TYPE_NEW_LEAD,
            'priority': self.PRIORITY_HIGH,
            'title': '🆕 Novo Lead',
            'message': f"Novo lead chegou: {lead.get('name', lead.get('nome', 'Sem nome'))}",
            'data': {
                'lead_id': lead['id'],
                'lead_name': lead.get('name', lead.get('nome')),
                'lead_phone': lead.get('phone', lead.get('telefone')),
                'status': lead.get('status')
            },
            'timestamp': datetime.now().isoformat(),
            'read': False,
            'sound': 'new_lead'
        }
        
        self.socketio.emit('notification', notification, room=room)
        print(f"🔔 Notificação enviada: Novo lead {lead['id']}")
    
    def notify_new_message(self, lead: Dict[str, Any], message: str, room: str = 'gestores'):
        """
        Notifica sobre nova mensagem
        
        Args:
            lead: Dados do lead
            message: Conteúdo da mensagem
            room: Sala para enviar
        """
        notification = {
            'id': f"msg_{lead['id']}_{datetime.now().timestamp()}",
            'type': self.TYPE_NEW_MESSAGE,
            'priority': self.PRIORITY_MEDIUM,
            'title': '💬 Nova Mensagem',
            'message': f"{lead.get('name', lead.get('nome', 'Lead'))}: {message[:50]}{'...' if len(message) > 50 else ''}",
            'data': {
                'lead_id': lead['id'],
                'lead_name': lead.get('name', lead.get('nome')),
                'message_preview': message[:100]
            },
            'timestamp': datetime.now().isoformat(),
            'read': False,
            'sound': 'new_message'
        }
        
        self.socketio.emit('notification', notification, room=room)
        print(f"🔔 Notificação enviada: Nova mensagem do lead {lead['id']}")
    
    def notify_sla_alert(self, lead: Dict[str, Any], minutes_waiting: int, room: str = 'gestores'):
        """
        Notifica sobre alerta de SLA
        
        Args:
            lead: Dados do lead
            minutes_waiting: Minutos esperando resposta
            room: Sala para enviar
        """
        notification = {
            'id': f"sla_{lead['id']}_{datetime.now().timestamp()}",
            'type': self.TYPE_SLA_ALERT,
            'priority': self.PRIORITY_URGENT if minutes_waiting > 60 else self.PRIORITY_HIGH,
            'title': '⚠️ Alerta de SLA',
            'message': f"Lead {lead.get('name', lead.get('nome'))} sem resposta há {minutes_waiting} minutos",
            'data': {
                'lead_id': lead['id'],
                'lead_name': lead.get('name', lead.get('nome')),
                'minutes_waiting': minutes_waiting
            },
            'timestamp': datetime.now().isoformat(),
            'read': False,
            'sound': 'sla_alert'
        }
        
        self.socketio.emit('notification', notification, room=room)
        print(f"🔔 Notificação enviada: Alerta SLA lead {lead['id']}")
    
    def notify_status_changed(self, lead: Dict[str, Any], old_status: str, new_status: str, room: str = 'gestores'):
        """
        Notifica sobre mudança de status
        
        Args:
            lead: Dados do lead
            old_status: Status anterior
            new_status: Novo status
            room: Sala para enviar
        """
        # Mapear status para português
        status_map = {
            'novo': 'Novo',
            'contatado': 'Contatado',
            'qualificado': 'Qualificado',
            'negociacao': 'Em Negociação',
            'ganho': 'Ganho',
            'perdido': 'Perdido'
        }
        
        notification = {
            'id': f"status_{lead['id']}_{datetime.now().timestamp()}",
            'type': self.TYPE_STATUS_CHANGED,
            'priority': self.PRIORITY_LOW if new_status != 'ganho' else self.PRIORITY_HIGH,
            'title': '✅ Status Alterado',
            'message': f"{lead.get('name', lead.get('nome'))} mudou de {status_map.get(old_status, old_status)} para {status_map.get(new_status, new_status)}",
            'data': {
                'lead_id': lead['id'],
                'lead_name': lead.get('name', lead.get('nome')),
                'old_status': old_status,
                'new_status': new_status
            },
            'timestamp': datetime.now().isoformat(),
            'read': False,
            'sound': 'status_changed' if new_status != 'ganho' else 'lead_won'
        }
        
        self.socketio.emit('notification', notification, room=room)
        print(f"🔔 Notificação enviada: Status mudou lead {lead['id']}")
    
    def notify_lead_assigned(self, lead: Dict[str, Any], vendedor_name: str, vendedor_id: int, room: str = 'gestores'):
        """
        Notifica sobre lead atribuído
        
        Args:
            lead: Dados do lead
            vendedor_name: Nome do vendedor
            vendedor_id: ID do vendedor
            room: Sala para enviar
        """
        notification = {
            'id': f"assign_{lead['id']}_{datetime.now().timestamp()}",
            'type': self.TYPE_LEAD_ASSIGNED,
            'priority': self.PRIORITY_MEDIUM,
            'title': '📞 Lead Atribuído',
            'message': f"Lead {lead.get('name', lead.get('nome'))} atribuído para {vendedor_name}",
            'data': {
                'lead_id': lead['id'],
                'lead_name': lead.get('name', lead.get('nome')),
                'vendedor_name': vendedor_name,
                'vendedor_id': vendedor_id
            },
            'timestamp': datetime.now().isoformat(),
            'read': False,
            'sound': 'lead_assigned'
        }
        
        # Envia para gestores
        self.socketio.emit('notification', notification, room='gestores')
        
        # Envia para o vendedor específico
        self.socketio.emit('notification', notification, room=f'user_{vendedor_id}')
        
        print(f"🔔 Notificação enviada: Lead {lead['id']} atribuído")
    
    def notify_lead_transferred(self, lead: Dict[str, Any], from_vendedor: str, to_vendedor: str, to_vendedor_id: int, room: str = 'gestores'):
        """
        Notifica sobre lead transferido
        
        Args:
            lead: Dados do lead
            from_vendedor: Nome do vendedor de origem
            to_vendedor: Nome do vendedor destino
            to_vendedor_id: ID do vendedor destino
            room: Sala para enviar
        """
        notification = {
            'id': f"transfer_{lead['id']}_{datetime.now().timestamp()}",
            'type': self.TYPE_LEAD_TRANSFERRED,
            'priority': self.PRIORITY_MEDIUM,
            'title': '🔄 Lead Transferido',
            'message': f"Lead {lead.get('name', lead.get('nome'))} transferido de {from_vendedor} para {to_vendedor}",
            'data': {
                'lead_id': lead['id'],
                'lead_name': lead.get('name', lead.get('nome')),
                'from_vendedor': from_vendedor,
                'to_vendedor': to_vendedor
            },
            'timestamp': datetime.now().isoformat(),
            'read': False,
            'sound': 'lead_transferred'
        }
        
        # Envia para gestores
        self.socketio.emit('notification', notification, room='gestores')
        
        # Envia para o novo vendedor
        self.socketio.emit('notification', notification, room=f'user_{to_vendedor_id}')
        
        print(f"🔔 Notificação enviada: Lead {lead['id']} transferido")
    
    def notify_custom(self, title: str, message: str, notification_type: str = 'info', 
                     priority: str = PRIORITY_MEDIUM, data: Dict = None, room: str = 'gestores'):
        """
        Envia notificação customizada
        
        Args:
            title: Título da notificação
            message: Mensagem
            notification_type: Tipo personalizado
            priority: Prioridade
            data: Dados adicionais
            room: Sala para enviar
        """
        notification = {
            'id': f"custom_{datetime.now().timestamp()}",
            'type': notification_type,
            'priority': priority,
            'title': title,
            'message': message,
            'data': data or {},
            'timestamp': datetime.now().isoformat(),
            'read': False,
            'sound': 'default'
        }
        
        self.socketio.emit('notification', notification, room=room)
        print(f"🔔 Notificação customizada enviada: {title}")
    
    def get_notification_stats(self) -> Dict[str, int]:
        """
        Retorna estatísticas de notificações
        
        Returns:
            Dict com contadores de notificações
        """
        # TODO: Implementar contadores reais se necessário
        return {
            'total': 0,
            'unread': 0,
            'by_type': {
                self.TYPE_NEW_LEAD: 0,
                self.TYPE_NEW_MESSAGE: 0,
                self.TYPE_SLA_ALERT: 0,
                self.TYPE_STATUS_CHANGED: 0,
                self.TYPE_LEAD_ASSIGNED: 0
            }
        }