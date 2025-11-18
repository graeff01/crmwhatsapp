# -*- coding: utf-8 -*-
"""
Provider para OpenAI (GPT-3.5, GPT-4)
Implementa integracao com API da OpenAI para qualificacao de leads
"""
import json
import re
from typing import Dict, List, Optional
from ai_qualification.providers.base_provider import BaseAIProvider

try:
    from openai import AsyncOpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False


class OpenAIProvider(BaseAIProvider):
    """
    Provider para modelos OpenAI (GPT-3.5-turbo, GPT-4, etc)
    """

    def __init__(
        self,
        api_key: str,
        model: str = "gpt-3.5-turbo",
        temperature: float = 0.7,
        max_tokens: int = 500,
        **kwargs
    ):
        """
        Inicializa provider OpenAI

        Args:
            api_key: API key da OpenAI
            model: Modelo a usar (gpt-3.5-turbo, gpt-4, etc)
            temperature: Criatividade da resposta (0-1)
            max_tokens: Maximo de tokens na resposta
        """
        super().__init__(api_key, model, **kwargs)
        self.temperature = temperature
        self.max_tokens = max_tokens

        if not OPENAI_AVAILABLE:
            raise ImportError(
                "Biblioteca 'openai' nao instalada. "
                "Instale com: pip install openai"
            )

        if not self.validate_api_key():
            raise ValueError("API key da OpenAI nao foi fornecida")

        # Inicializa cliente assincrono
        self.client = AsyncOpenAI(api_key=self.api_key)

    async def generate_response(
        self,
        system_prompt: str,
        messages: List[Dict[str, str]],
        extract_data: bool = True,
        **kwargs
    ) -> Dict:
        """
        Gera resposta usando GPT

        Args:
            system_prompt: Contexto/instrucoes para o modelo
            messages: Historico de mensagens
            extract_data: Se deve tentar extrair dados estruturados
            **kwargs: Parametros adicionais (temperature, max_tokens)

        Returns:
            Dict com message, extracted_data e metadata
        """
        try:
            # Prepara mensagens para API
            api_messages = [{"role": "system", "content": system_prompt}]
            api_messages.extend(messages)

            # Adiciona instrucao para extracao de dados se necessario
            if extract_data:
                extraction_prompt = """

IMPORTANTE: Ao final da sua resposta, extraia informacoes estruturadas no formato JSON:
```json
{
  "name": "nome do cliente (se mencionado)",
  "phone": "telefone (se mencionado)",
  "email": "email (se mencionado)",
  "company": "empresa (se mencionado)",
  "interest": "interesse/necessidade principal",
  "urgency": "alta/media/baixa",
  "budget": "orcamento mencionado (se houver)",
  "notes": "observacoes importantes"
}
```
Use null para campos nao mencionados.
"""
                api_messages[-1]["content"] += extraction_prompt

            # Chama API OpenAI
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=api_messages,
                temperature=kwargs.get("temperature", self.temperature),
                max_tokens=kwargs.get("max_tokens", self.max_tokens),
            )

            # Extrai resposta
            assistant_message = response.choices[0].message.content

            # Tenta extrair JSON estruturado
            extracted_data = {}
            clean_message = assistant_message

            if extract_data:
                extracted_data = self._extract_json_from_text(assistant_message)
                # Remove o JSON da mensagem se encontrado
                clean_message = re.sub(r'```json.*?```', '', assistant_message, flags=re.DOTALL).strip()

            return {
                "message": clean_message,
                "extracted_data": extracted_data,
                "metadata": {
                    "model": response.model,
                    "tokens_used": response.usage.total_tokens,
                    "finish_reason": response.choices[0].finish_reason
                }
            }

        except Exception as e:
            # Em caso de erro, retorna resposta padrao
            return {
                "message": "Desculpe, tive um problema tecnico. Pode repetir sua mensagem?",
                "extracted_data": {},
                "metadata": {"error": str(e)}
            }

    async def extract_structured_data(
        self,
        text: str,
        schema: Dict
    ) -> Dict:
        """
        Extrai dados estruturados de texto livre

        Args:
            text: Texto para analise
            schema: Schema com campos esperados

        Returns:
            Dict com dados extraidos
        """
        prompt = f"""Analise o texto abaixo e extraia informacoes estruturadas.

Texto:
{text}

Extraia os seguintes campos (use null se nao encontrar):
{json.dumps(schema, indent=2, ensure_ascii=False)}

Responda APENAS com um JSON valido contendo os dados extraidos."""

        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,  # Baixa temperatura para extracao precisa
                max_tokens=500,
            )

            extracted_text = response.choices[0].message.content
            return self._extract_json_from_text(extracted_text)

        except Exception as e:
            return {"error": str(e)}

    def _extract_json_from_text(self, text: str) -> Dict:
        """
        Extrai objeto JSON de texto que pode conter outras coisas

        Args:
            text: Texto contendo JSON

        Returns:
            Dict parseado ou {} se nao encontrar
        """
        try:
            # Tenta encontrar JSON entre ```json e ```
            json_match = re.search(r'```json\s*(.*?)\s*```', text, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
                return json.loads(json_str)

            # Tenta encontrar qualquer JSON no texto
            json_match = re.search(r'\{.*\}', text, re.DOTALL)
            if json_match:
                return json.loads(json_match.group(0))

            return {}

        except json.JSONDecodeError:
            return {}

    async def test_connection(self) -> bool:
        """
        Testa conexao com API OpenAI

        Returns:
            True se conectado com sucesso
        """
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": "Hello"}],
                max_tokens=5
            )
            return True
        except Exception:
            return False
