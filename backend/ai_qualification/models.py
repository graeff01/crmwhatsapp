"""
Modelos específicos do módulo de qualificação por IA
"""
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any


@dataclass
class QualificationCriteria:
    """
    Critérios para qualificação de leads
    Define regras e limites do processo
    """
    required_fields: List[str] = field(default_factory=lambda: ['name', 'phone'])
    min_score: int = 50
    max_attempts: int = 5
    timeout_minutes: int = 30
    auto_escalate_keywords: List[str] = field(default_factory=lambda: [
        'humano', 'atendente', 'pessoa', 'vendedor', 'falar com alguem'
    ])

    def validate_collected_data(self, collected_data: Dict[str, Any]) -> bool:
        """
        Valida se todos os campos obrigatórios foram coletados

        Args:
            collected_data: Dados coletados do lead

        Returns:
            True se todos os campos obrigatórios estão presentes e preenchidos
        """
        return all(
            field in collected_data and collected_data[field]
            for field in self.required_fields
        )

    def should_escalate_by_keywords(self, message: str) -> bool:
        """
        Verifica se a mensagem contém palavras-chave para escalação

        Args:
            message: Mensagem do usuário

        Returns:
            True se deve escalar para atendimento humano
        """
        message_lower = message.lower()
        return any(keyword in message_lower for keyword in self.auto_escalate_keywords)

    def to_dict(self) -> Dict:
        """Converte para dicionário"""
        return {
            'required_fields': self.required_fields,
            'min_score': self.min_score,
            'max_attempts': self.max_attempts,
            'timeout_minutes': self.timeout_minutes,
            'auto_escalate_keywords': self.auto_escalate_keywords
        }


@dataclass
class QualificationPrompt:
    """
    Prompts do sistema para diferentes contextos
    """
    system_prompt: str
    greeting_template: str
    qualification_template: str
    escalation_template: str
    completion_template: str

    @classmethod
    def default_for_business(cls, business_type: str = "services") -> "QualificationPrompt":
        """
        Retorna prompts padrão para um tipo de negócio

        Args:
            business_type: Tipo de negócio (services, ecommerce, b2b, real_estate)

        Returns:
            QualificationPrompt configurado
        """
        prompts = {
            "services": cls(
                system_prompt="""Você é um assistente de qualificação de leads para uma empresa de serviços.
Seu objetivo é coletar informações do lead de forma natural e amigável:
- Nome
- Telefone
- Tipo de serviço de interesse
- Localização (se aplicável)
- Urgência/prazo

Seja cordial, objetivo e profissional.""",
                greeting_template="Olá! Bem-vindo(a) à {company_name}. Como posso ajudá-lo(a) hoje?",
                qualification_template="Ótimo! Para te atender melhor, preciso de algumas informações...",
                escalation_template="Entendo. Vou transferir você para um de nossos especialistas que poderá te ajudar melhor!",
                completion_template="Obrigado pelas informações! Em breve entraremos em contato."
            ),
            "ecommerce": cls(
                system_prompt="""Você é um assistente de vendas para um e-commerce.
Colete informações sobre:
- Nome
- Telefone/Email
- Produto de interesse
- Quantidade
- Forma de pagamento preferida

Seja solícito e mostre entusiasmo pelos produtos.""",
                greeting_template="Olá! Bem-vindo(a) à nossa loja! O que você procura hoje?",
                qualification_template="Perfeito! Vou te ajudar a finalizar seu pedido...",
                escalation_template="Vou conectar você com nossa equipe de vendas para finalizar!",
                completion_template="Pedido registrado! Logo nossa equipe entrará em contato."
            ),
            "b2b": cls(
                system_prompt="""Você é um assistente de prospecção B2B.
Colete:
- Nome do contato
- Empresa
- Cargo
- Telefone/Email
- Desafio ou necessidade
- Tamanho da empresa

Seja profissional e focado em valor de negócio.""",
                greeting_template="Olá! Obrigado pelo interesse em nossa solução. Qual seu nome?",
                qualification_template="Ótimo! Para preparar uma proposta adequada...",
                escalation_template="Vou agendar uma reunião com nosso consultor especializado!",
                completion_template="Informações registradas! Retornaremos em até 24h."
            ),
            "real_estate": cls(
                system_prompt="""Você é um assistente para imobiliária.
Colete:
- Nome
- Telefone
- Tipo de imóvel (compra/aluguel)
- Localização desejada
- Faixa de preço/orçamento
- Número de quartos

Seja consultivo e entusiasta.""",
                greeting_template="Olá! Procurando o imóvel ideal? Vamos encontrá-lo juntos!",
                qualification_template="Perfeito! Vou buscar as melhores opções para você...",
                escalation_template="Vou te conectar com um corretor especializado na região!",
                completion_template="Ótimo! Logo teremos novidades sobre imóveis disponíveis."
            )
        }

        return prompts.get(business_type, prompts["services"])
