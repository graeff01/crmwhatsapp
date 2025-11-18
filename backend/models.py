"""
Modelos de dados para o sistema de qualificação de leads por IA
"""
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any


class QualificationStatus(Enum):
    """Status da qualificação de um lead"""
    COLLECTING = "collecting"  # Coletando informações
    QUALIFIED = "qualified"  # Lead qualificado
    DISQUALIFIED = "disqualified"  # Lead desqualificado
    ESCALATED = "escalated"  # Escalado para humano
    COMPLETED = "completed"  # Conversa completada
    TIMEOUT = "timeout"  # Timeout sem resposta


class MessageRole(Enum):
    """Papel de quem enviou a mensagem"""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


@dataclass
class Message:
    """Representa uma mensagem na conversa"""
    role: MessageRole
    content: str
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict:
        """Converte para dicionário"""
        return {
            'role': self.role.value,
            'content': self.content,
            'timestamp': self.timestamp.isoformat(),
            'metadata': self.metadata
        }


@dataclass
class LeadConversation:
    """
    Representa uma conversa completa com um lead
    Armazena histórico, dados coletados e status
    """
    phone: str
    status: QualificationStatus = QualificationStatus.COLLECTING
    messages: List[Message] = field(default_factory=list)
    collected_data: Dict[str, Any] = field(default_factory=dict)
    qualification_score: int = 0
    attempts: int = 0
    notes: List[str] = field(default_factory=list)
    started_at: datetime = field(default_factory=datetime.now)
    ended_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def add_message(self, role: MessageRole, content: str, metadata: Optional[Dict] = None):
        """Adiciona uma mensagem à conversa"""
        message = Message(
            role=role,
            content=content,
            metadata=metadata or {}
        )
        self.messages.append(message)

        # Incrementa tentativas se for mensagem do assistente
        if role == MessageRole.ASSISTANT:
            self.attempts += 1

    def get_conversation_history(self) -> List[Dict]:
        """Retorna histórico da conversa formatado"""
        return [msg.to_dict() for msg in self.messages]

    def get_user_messages(self) -> List[Message]:
        """Retorna apenas mensagens do usuário"""
        return [msg for msg in self.messages if msg.role == MessageRole.USER]

    def get_assistant_messages(self) -> List[Message]:
        """Retorna apenas mensagens do assistente"""
        return [msg for msg in self.messages if msg.role == MessageRole.ASSISTANT]

    def update_collected_data(self, data: Dict[str, Any]):
        """Atualiza dados coletados"""
        self.collected_data.update(data)

    def add_note(self, note: str):
        """Adiciona nota à conversa"""
        self.notes.append(note)

    def end_conversation(self, status: QualificationStatus):
        """Encerra a conversa"""
        self.status = status
        self.ended_at = datetime.now()

    def to_dict(self) -> Dict:
        """Converte para dicionário"""
        return {
            'phone': self.phone,
            'status': self.status.value,
            'messages': self.get_conversation_history(),
            'collected_data': self.collected_data,
            'qualification_score': self.qualification_score,
            'attempts': self.attempts,
            'notes': self.notes,
            'started_at': self.started_at.isoformat(),
            'ended_at': self.ended_at.isoformat() if self.ended_at else None,
            'metadata': self.metadata
        }
