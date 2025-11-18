# -*- coding: utf-8 -*-
"""
Provider de IA usando OpenAI
"""
from typing import Dict, List, Optional
import os


class OpenAIProvider:
    """
    Provider para integracao com OpenAI API
    """

    def __init__(self, api_key: str = None, model: str = "gpt-3.5-turbo"):
        """
        Inicializa provider OpenAI

        Args:
            api_key: API key da OpenAI
            model: Modelo a ser usado
        """
        self.api_key = api_key or os.getenv('OPENAI_API_KEY')
        self.model = model

        if not self.api_key:
            print("WARNING: OpenAI API key nao configurada")

        # Inicializa cliente OpenAI apenas se tiver API key
        self.client = None
        if self.api_key:
            try:
                from openai import AsyncOpenAI
                self.client = AsyncOpenAI(api_key=self.api_key)
                print(f"OpenAI Provider inicializado com modelo: {self.model}")
            except ImportError:
                print("WARNING: Biblioteca openai nao instalada. Execute: pip install openai")
            except Exception as e:
                print(f"WARNING: Erro ao inicializar OpenAI: {e}")

    async def generate_response(
        self,
        context: str,
        user_message: str,
        conversation_history: List[Dict] = None
    ) -> Dict:
        """
        Gera resposta usando OpenAI

        Args:
            context: Contexto do sistema
            user_message: Mensagem do usuario
            conversation_history: Historico da conversa

        Returns:
            Dict com resposta e dados extraidos
        """
        if not self.client:
            return {
                'message': 'Sistema de IA temporariamente indisponivel. Um atendente entrara em contato em breve.',
                'extracted_data': {}
            }

        try:
            # Monta mensagens para API
            messages = [
                {"role": "system", "content": context}
            ]

            # Adiciona historico (ultimas 10 mensagens)
            if conversation_history:
                for msg in conversation_history[-10:]:
                    messages.append({
                        "role": msg['role'],
                        "content": msg['content']
                    })

            # Adiciona mensagem atual do usuario
            messages.append({
                "role": "user",
                "content": user_message
            })

            # Chama API
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.7,
                max_tokens=200
            )

            assistant_message = response.choices[0].message.content

            # Tenta extrair dados estruturados da mensagem
            extracted_data = self._extract_data_from_conversation(user_message)

            return {
                'message': assistant_message,
                'extracted_data': extracted_data
            }

        except Exception as e:
            print(f"Erro ao chamar OpenAI: {e}")
            return {
                'message': 'Desculpe, tive um problema tecnico. Pode repetir?',
                'extracted_data': {}
            }

    def _extract_data_from_conversation(self, user_message: str) -> Dict:
        """
        Extrai dados estruturados da mensagem do usuario
        (Implementacao basica - pode ser melhorada com NLP)

        Args:
            user_message: Mensagem do usuario

        Returns:
            Dict com dados extraidos
        """
        extracted = {}

        message_lower = user_message.lower()

        # Detecta nome (padroes simples)
        if any(word in message_lower for word in ['meu nome e', 'me chamo', 'sou o', 'sou a']):
            # Extracao basica de nome
            words = user_message.split()
            for i, word in enumerate(words):
                if word.lower() in ['e', 'chamo', 'sou']:
                    if i + 1 < len(words):
                        potential_name = words[i + 1]
                        if potential_name[0].isupper():
                            extracted['name'] = potential_name

        # Detecta telefone (regex simples)
        import re
        phone_pattern = r'\(?\d{2}\)?\s?\d{4,5}[-\s]?\d{4}'
        phone_match = re.search(phone_pattern, user_message)
        if phone_match:
            extracted['phone'] = phone_match.group()

        # Detecta interesse/produto
        product_keywords = ['quero', 'interessado', 'gostaria', 'preciso']
        if any(keyword in message_lower for keyword in product_keywords):
            # Extrai o que vem depois da palavra-chave
            for keyword in product_keywords:
                if keyword in message_lower:
                    parts = user_message.split(keyword, 1)
                    if len(parts) > 1:
                        interest = parts[1].strip()[:100]  # Limita tamanho
                        if interest:
                            extracted['interest'] = interest
                            break

        return extracted

    def test_connection(self) -> bool:
        """
        Testa conexao com OpenAI

        Returns:
            True se conectou com sucesso
        """
        if not self.client:
            return False

        try:
            # Faz uma chamada simples de teste
            import asyncio
            async def test():
                response = await self.client.chat.completions.create(
                    model=self.model,
                    messages=[{"role": "user", "content": "test"}],
                    max_tokens=5
                )
                return response is not None

            return asyncio.run(test())

        except Exception as e:
            print(f"Erro ao testar OpenAI: {e}")
            return False
