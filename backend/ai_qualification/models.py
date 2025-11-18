"""
Modelos de dados para o sistema de qualificação de IA
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Optional
from enum import Enum


class QualificationStatus(Enum):
    """Status da qualificação de um lead"""
    IN_PROGRESS = "in_progress"
    QUALIFIED = "qualified"
    DISQUALIFIED = "disqualified"
    NEEDS_HUMAN = "needs_human"
    COMPLETED = "completed"


@dataclass
class QualificationCriteria:
    """Critérios para qualificação de leads"""
    required_fields: List[str] = field(default_factory=lambda: ["name", "phone", "interest"])
    min_score: int = 50
    max_attempts: int = 5


@dataclass
class Message:
    """Representa uma mensagem na conversa"""
    role: str  # 'user' ou 'assistant'
    content: str
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())


@dataclass
class LeadConversation:
    """
    Representa uma conversa de qualificação com um lead
    """
    phone: str
    status: QualificationStatus = QualificationStatus.IN_PROGRESS
    messages: List[Message] = field(default_factory=list)
    collected_data: Dict[str, any] = field(default_factory=dict)
    score: int = 0
    attempts: int = 0
    notes: List[str] = field(default_factory=list)
    started_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def add_message(self, role: str, content: str):
        """Adiciona uma mensagem à conversa"""
        self.messages.append(Message(role=role, content=content))
        self.updated_at = datetime.utcnow().isoformat()

    def update_score(self, points: int):
        """Atualiza o score do lead"""
        self.score = max(0, min(100, self.score + points))
        self.updated_at = datetime.utcnow().isoformat()

    def add_note(self, note: str):
        """Adiciona uma nota à conversa"""
        self.notes.append(note)
        self.updated_at = datetime.utcnow().isoformat()

    def collect_data(self, key: str, value: any):
        """Armazena dados coletados do lead"""
        self.collected_data[key] = value
        self.updated_at = datetime.utcnow().isoformat()

    def increment_attempts(self):
        """Incrementa contador de tentativas"""
        self.attempts += 1
        self.updated_at = datetime.utcnow().isoformat()

    def is_qualified(self) -> bool:
        """Verifica se o lead está qualificado"""
        return self.status == QualificationStatus.QUALIFIED

    def is_in_progress(self) -> bool:
        """Verifica se a conversa está em progresso"""
        return self.status == QualificationStatus.IN_PROGRESS

    def to_dict(self) -> Dict:
        """Converte para dicionário"""
        return {
            'phone': self.phone,
            'status': self.status.value,
            'messages': [{'role': m.role, 'content': m.content, 'timestamp': m.timestamp} for m in self.messages],
            'collected_data': self.collected_data,
            'score': self.score,
            'attempts': self.attempts,
            'notes': self.notes,
            'started_at': self.started_at,
            'updated_at': self.updated_at
        }
