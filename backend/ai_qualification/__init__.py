"""
Sistema de qualificacao de leads por IA
Exporta principais classes e funcoes
"""
from .models import (
    QualificationStatus,
    MessageRole,
    Message,
    LeadConversation,
    QualificationCriteria,
    QualificationResult
)

from .rules.qualification_rules import QualificationRules
from .prompts.qualification_prompts import QualificationPrompts, BusinessSpecificPrompts

__all__ = [
    "QualificationStatus",
    "MessageRole",
    "Message",
    "LeadConversation",
    "QualificationCriteria",
    "QualificationResult",
    "QualificationRules",
    "QualificationPrompts",
    "BusinessSpecificPrompts"
]
