"""
Provider OpenAI para sistema de qualificação
Implementa integração com API da OpenAI
"""
from typing import List, Dict, Optional
import json
import os
from openai import OpenAI, AsyncOpenAI
from .base_provider import BaseAIProvider


class OpenAIProvider(BaseAIProvider):
    """Provider para OpenAI (GPT-4, GPT-3.5, etc)"""

    def __init__(
        self,
        api_key: str = None,
        model: str = "gpt-4o-mini",
        organization: str = None,
        **kwargs
    ):
        """
        Inicializa provider OpenAI

        Args:
            api_key: Chave da API OpenAI
            model: Modelo a usar (gpt-4, gpt-3.5-turbo, etc)
            organization: ID da organização (opcional)
            **kwargs: Configurações adicionais
        """
        super().__init__(model=model, **kwargs)

        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY não configurada")

        self.organization = organization or os.getenv("OPENAI_ORG_ID")

        # Cliente síncrono e assíncrono
        self.client = OpenAI(
            api_key=self.api_key,
            organization=self.organization
        )

        self.async_client = AsyncOpenAI(
            api_key=self.api_key,
            organization=self.organization
        )

        # Estatísticas
        self.stats = {
            "total_requests": 0,
            "total_tokens": 0,
            "errors": 0
        }

    async def generate_response(
        self,
        messages: List[Dict[str, str]],
        max_tokens: int = 150,
        temperature: float = 0.7,
        **kwargs
    ) -> str:
        """
        Gera resposta usando OpenAI

        Args:
            messages: Histórico de mensagens
            max_tokens: Máximo de tokens
            temperature: Criatividade (0-1)
            **kwargs: Parâmetros extras (top_p, frequency_penalty, etc)

        Returns:
            String com resposta gerada
        """
        try:
            self.stats["total_requests"] += 1

            response = await self.async_client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
                **kwargs
            )

            # Atualiza estatísticas
            if hasattr(response, 'usage'):
                self.stats["total_tokens"] += response.usage.total_tokens

            result = response.choices[0].message.content.strip()

            if not self.validate_response(result):
                raise ValueError("Resposta inválida gerada")

            return result

        except Exception as e:
            self.stats["errors"] += 1
            raise Exception(f"Erro ao gerar resposta OpenAI: {str(e)}")

    async def extract_structured_data(
        self,
        text: str,
        schema: Dict
    ) -> Dict:
        """
        Extrai dados estruturados usando OpenAI

        Args:
            text: Texto para extrair dados
            schema: Schema JSON esperado

        Returns:
            Dicionário com dados extraídos
        """
        try:
            prompt = f"""
Extraia as seguintes informações do texto abaixo e retorne em formato JSON.

Schema esperado:
{json.dumps(schema, indent=2, ensure_ascii=False)}

Texto:
{text}

Retorne APENAS o JSON, sem explicações.
"""

            messages = [
                {"role": "system", "content": "Você é um extrator de dados especializado. Retorne apenas JSON válido."},
                {"role": "user", "content": prompt}
            ]

            response = await self.generate_response(
                messages=messages,
                temperature=0.1,  # Baixa temperatura para extração
                max_tokens=500
            )

            # Tenta parsear JSON
            try:
                # Remove markdown code blocks se existirem
                response = response.strip()
                if response.startswith("```"):
                    response = response.split("```")[1]
                    if response.startswith("json"):
                        response = response[4:]
                response = response.strip()

                data = json.loads(response)
                return data

            except json.JSONDecodeError:
                # Fallback: retorna dados vazios
                return {key: None for key in schema.keys()}

        except Exception as e:
            raise Exception(f"Erro ao extrair dados: {str(e)}")

    def get_model_info(self) -> Dict:
        """Retorna informações sobre o modelo OpenAI"""
        return {
            "provider": "OpenAI",
            "model": self.model,
            "organization": self.organization,
            "api_key_configured": bool(self.api_key),
            "capabilities": {
                "chat": True,
                "extraction": True,
                "streaming": True,
                "function_calling": "gpt-4" in self.model or "gpt-3.5" in self.model
            }
        }

    async def health_check(self) -> bool:
        """Verifica saúde da API OpenAI"""
        try:
            # Faz uma requisição simples
            response = await self.async_client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": "test"}],
                max_tokens=5
            )
            return bool(response and response.choices)

        except Exception as e:
            print(f"Health check falhou: {e}")
            return False

    def get_stats(self) -> Dict:
        """Retorna estatísticas de uso"""
        base_stats = super().get_stats()
        base_stats.update(self.stats)
        return base_stats

    # Método síncrono para compatibilidade
    def generate_response_sync(
        self,
        messages: List[Dict[str, str]],
        max_tokens: int = 150,
        temperature: float = 0.7,
        **kwargs
    ) -> str:
        """Versão síncrona de generate_response"""
        try:
            self.stats["total_requests"] += 1

            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
                **kwargs
            )

            if hasattr(response, 'usage'):
                self.stats["total_tokens"] += response.usage.total_tokens

            result = response.choices[0].message.content.strip()

            if not self.validate_response(result):
                raise ValueError("Resposta inválida gerada")

            return result

        except Exception as e:
            self.stats["errors"] += 1
            raise Exception(f"Erro ao gerar resposta OpenAI: {str(e)}")
