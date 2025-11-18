"""
Base Provider para sistemas de IA
Define interface padrão para diferentes providers (OpenAI, Anthropic, etc)
"""
from abc import ABC, abstractmethod
from typing import Dict, List, Optional


class BaseAIProvider(ABC):
    """
    Classe base abstrata para providers de IA
    Todos os providers devem implementar esta interface
    """

    def __init__(self, api_key: str, model: str, **kwargs):
        """
        Inicializa o provider

        Args:
            api_key: Chave de API do serviço
            model: Nome do modelo a ser usado
            **kwargs: Configurações adicionais específicas do provider
        """
        self.api_key = api_key
        self.model = model
        self.config = kwargs

    @abstractmethod
    async def generate_response(
        self,
        system_prompt: str,
        messages: List[Dict[str, str]],
        **kwargs
    ) -> Dict:
        """
        Gera resposta usando o modelo de IA

        Args:
            system_prompt: Prompt de sistema/contexto
            messages: Lista de mensagens da conversa [{"role": "user", "content": "..."}]
            **kwargs: Parâmetros adicionais (temperature, max_tokens, etc)

        Returns:
            Dict com:
                - message: Resposta gerada
                - extracted_data: Dados estruturados extraídos (opcional)
                - metadata: Metadados da geração (tokens usados, etc)
        """
        pass

    @abstractmethod
    async def extract_structured_data(
        self,
        text: str,
        schema: Dict
    ) -> Dict:
        """
        Extrai dados estruturados de texto usando IA

        Args:
            text: Texto para extrair dados
            schema: Schema dos dados a serem extraídos

        Returns:
            Dict com dados extraídos
        """
        pass

    def validate_api_key(self) -> bool:
        """Valida se a API key está configurada"""
        return bool(self.api_key and len(self.api_key) > 0)
