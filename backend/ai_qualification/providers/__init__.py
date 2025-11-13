"""
Providers de IA para qualificação
Suporta múltiplos LLMs
"""
from .base_provider import BaseAIProvider
from .openai_provider import OpenAIProvider

__all__ = [
    "BaseAIProvider",
    "OpenAIProvider"
]
