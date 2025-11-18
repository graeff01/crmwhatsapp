"""
Provider para OpenAI (GPT-3.5, GPT-4)
Implementa integração com API da OpenAI para qualificação de leads
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
            max_tokens: Máximo de tokens na resposta
        """
        super().__init__(api_key, model, **kwargs)
        self.temperature = temperature
        self.max_tokens = max_tokens

        if not OPENAI_AVAILABLE:
            raise ImportError(
                "Biblioteca 'openai' não instalada. "
                "Instale com: pip install openai"
            )

        if not self.validate_api_key():
            raise ValueError("API key da OpenAI não foi fornecida")

        # Inicializa cliente assíncrono
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
            system_prompt: Contexto/instruções para o modelo
            messages: Histórico de mensagens
            extract_data: Se deve tentar extrair dados estruturados
            **kwargs: Parâmetros adicionais (temperature, max_tokens)

        Returns:
            Dict com message, extracted_data e metadata
        """
        try:
            # Prepara mensagens para API
            api_messages = [{"role": "system", "content": system_prompt}]
            api_messages.extend(messages)

            # Adiciona instrução para extração de dados se necessário
            if extract_data:
                extraction_prompt = """

IMPORTANTE: Ao final da sua resposta, extraia informações estruturadas no formato JSON:
```json
{
  "name": "nome do cliente (se mencionado)",
  "phone": "telefone (se mencionado)",
  "email": "email (se mencionado)",
  "company": "empresa (se mencionado)",
  "interest": "interesse/necessidade principal",
  "urgency": "alta/média/baixa",
  "budget": "orçamento mencionado (se houver)",
  "notes": "observações importantes"
}
```
Use null para campos não mencionados.
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
            # Em caso de erro, retorna resposta padrão
            return {
                "message": "Desculpe, tive um problema técnico. Pode repetir sua mensagem?",
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
            text: Texto para análise
            schema: Schema com campos esperados

        Returns:
            Dict com dados extraídos
        """
        prompt = f"""Analise o texto abaixo e extraia informações estruturadas.

Texto:
{text}

Extraia os seguintes campos (use null se não encontrar):
{json.dumps(schema, indent=2, ensure_ascii=False)}

Responda APENAS com um JSON válido contendo os dados extraídos."""

        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,  # Baixa temperatura para extração precisa
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
            Dict parseado ou {} se não encontrar
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
        Testa conexão com API OpenAI

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
