"""
Provider base abstrato para LLMs
Define interface comum para diferentes provedores de IA
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Optional


class BaseAIProvider(ABC):
    """
    Classe abstrata para providers de IA
    Permite trocar facilmente entre OpenAI, Anthropic, local models, etc.
    """

    def __init__(self, model: str = None, **kwargs):
        """
        Inicializa o provider

        Args:
            model: Nome do modelo a ser usado
            **kwargs: Configurações adicionais específicas do provider
        """
        self.model = model
        self.config = kwargs

    @abstractmethod
    async def generate_response(
        self,
        messages: List[Dict[str, str]],
        max_tokens: int = 150,
        temperature: float = 0.7,
        **kwargs
    ) -> str:
        """
        Gera resposta baseada em histórico de mensagens

        Args:
            messages: Lista de mensagens no formato [{"role": "user|assistant|system", "content": "..."}]
            max_tokens: Máximo de tokens na resposta
            temperature: Criatividade (0-1)
            **kwargs: Parâmetros adicionais

        Returns:
            String com a resposta gerada
        """
        pass

    @abstractmethod
    async def extract_structured_data(
        self,
        text: str,
        schema: Dict
    ) -> Dict:
        """
        Extrai dados estruturados de texto

        Args:
            text: Texto para extrair dados
            schema: Schema JSON dos dados a extrair

        Returns:
            Dicionário com dados extraídos
        """
        pass

    @abstractmethod
    def get_model_info(self) -> Dict:
        """
        Retorna informações sobre o modelo

        Returns:
            Dicionário com informações (nome, provider, limites, etc)
        """
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        """
        Verifica se o provider está funcionando

        Returns:
            True se estiver OK, False caso contrário
        """
        pass

    def format_messages(self, messages: List[Dict]) -> List[Dict]:
        """
        Formata mensagens para o formato do provider
        Pode ser sobrescrito por providers específicos

        Args:
            messages: Mensagens no formato padrão

        Returns:
            Mensagens no formato do provider
        """
        return messages

    def validate_response(self, response: str) -> bool:
        """
        Valida resposta gerada

        Args:
            response: Resposta a validar

        Returns:
            True se válida, False caso contrário
        """
        if not response or not response.strip():
            return False

        # Validações básicas
        if len(response) > 10000:  # Muito longo
            return False

        return True

    def get_stats(self) -> Dict:
        """
        Retorna estatísticas de uso (opcional)

        Returns:
            Dicionário com estatísticas
        """
        return {
            "provider": self.__class__.__name__,
            "model": self.model,
            "config": self.config
        }
