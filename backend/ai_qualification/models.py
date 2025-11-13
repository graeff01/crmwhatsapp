"""
Modelos de dados para o sistema de qualificacao de leads por IA
Define estruturas de dados e enums usados pelo sistema
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional
from enum import Enum


class QualificationStatus(Enum):
    """Status da qualifica��o do lead"""
    IN_PROGRESS = "in_progress"
    QUALIFIED = "qualified"
    DISQUALIFIED = "disqualified"
    ESCALATED = "escalated"
    TIMEOUT = "timeout"


class MessageRole(Enum):
    """Papel/origem da mensagem"""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


@dataclass
class Message:
    """Representa uma mensagem na conversa"""
    role: MessageRole
    content: str
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        """Converte para dicion�rio"""
        return {
            "role": self.role.value,
            "content": self.content,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata
        }


@dataclass
class LeadConversation:
    """Representa uma conversa de qualifica��o com um lead"""
    phone: str
    messages: List[Message] = field(default_factory=list)
    collected_data: Dict[str, any] = field(default_factory=dict)
    status: QualificationStatus = QualificationStatus.IN_PROGRESS
    qualification_score: int = 0
    attempts: int = 0
    notes: List[str] = field(default_factory=list)
    started_at: datetime = field(default_factory=datetime.now)
    ended_at: Optional[datetime] = None
    metadata: Dict = field(default_factory=dict)

    def add_message(self, role: MessageRole, content: str, metadata: Dict = None):
        """Adiciona uma mensagem � conversa"""
        message = Message(
            role=role,
            content=content,
            metadata=metadata or {}
        )
        self.messages.append(message)
        return message

    def add_note(self, note: str):
        """Adiciona uma nota/observa��o"""
        self.notes.append(f"[{datetime.now().isoformat()}] {note}")

    def update_collected_data(self, field: str, value: any):
        """Atualiza dados coletados"""
        self.collected_data[field] = value
        self.add_note(f"Campo '{field}' coletado: {value}")

    def get_conversation_history(self) -> List[dict]:
        """Retorna hist�rico formatado"""
        return [msg.to_dict() for msg in self.messages]

    def end_conversation(self, status: QualificationStatus):
        """Encerra a conversa"""
        self.status = status
        self.ended_at = datetime.now()

    def to_dict(self) -> dict:
        """Converte para dicion�rio"""
        return {
            "phone": self.phone,
            "messages": self.get_conversation_history(),
            "collected_data": self.collected_data,
            "status": self.status.value,
            "qualification_score": self.qualification_score,
            "attempts": self.attempts,
            "notes": self.notes,
            "started_at": self.started_at.isoformat(),
            "ended_at": self.ended_at.isoformat() if self.ended_at else None,
            "metadata": self.metadata
        }


@dataclass
class QualificationCriteria:
    """Crit�rios para qualifica��o de leads"""
    required_fields: List[str] = field(default_factory=list)
    min_score: int = 50
    max_attempts: int = 5
    timeout_minutes: int = 30
    business_type: str = "default"

    def to_dict(self) -> dict:
        """Converte para dicion�rio"""
        return {
            "required_fields": self.required_fields,
            "min_score": self.min_score,
            "max_attempts": self.max_attempts,
            "timeout_minutes": self.timeout_minutes,
            "business_type": self.business_type
        }


@dataclass
class QualificationResult:
    """Resultado do processamento de qualifica��o"""
    success: bool
    status: QualificationStatus
    response: str
    collected_data: Dict = field(default_factory=dict)
    score: int = 0
    should_send_to_crm: bool = False
    crm_data: Dict = field(default_factory=dict)
    metadata: Dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        """Converte para dicion�rio"""
        return {
            "success": self.success,
            "status": self.status.value,
            "response": self.response,
            "collected_data": self.collected_data,
            "score": self.score,
            "should_send_to_crm": self.should_send_to_crm,
            "crm_data": self.crm_data,
            "metadata": self.metadata
        }
