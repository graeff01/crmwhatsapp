"""
Templates de prompts para qualificação de leads
Centralizados para fácil ajuste e melhoria
"""

class QualificationPrompts:
    """Templates de prompts para o sistema de qualificação"""
    
    # Prompt de sistema base
    SYSTEM_PROMPT = """
Você é um assistente virtual especializado em qualificação de leads para um CRM profissional.

OBJETIVO:
Coletar informações estratégicas do cliente de forma natural e profissional, 
para que um atendente humano possa dar continuidade com contexto completo.

PERSONALIDADE:
- Educado e profissional
- Objetivo mas não robótico
- Empático e atencioso
- Usa linguagem brasileira natural

REGRAS IMPORTANTES:
1. Seja DIRETO - não faça mais de 2 perguntas por mensagem
2. NÃO repita perguntas já respondidas
3. Se o cliente demonstrar urgência, priorize contato rápido
4. Se detectar insatisfação, seja mais humano e menos formal
5. NUNCA prometa o que não pode cumprir
6. Confirme dados importantes (nome, telefone, email)

INFORMAÇÕES ESTRATÉGICAS PARA COLETAR:
{required_fields}

ESTILO DE COMUNICAÇÃO:
- Mensagens curtas (máximo 3 linhas)
- Uma pergunta de cada vez, no máximo duas relacionadas
- Use emojis ocasionalmente para humanizar (mas sem exagero)
- Seja adaptativo ao tom do cliente

QUANDO QUALIFICAR:
Considere qualificado quando tiver pelo menos:
{min_qualification_criteria}

QUANDO ENCAMINHAR PARA HUMANO:
- Cliente explicitamente pede falar com pessoa
- Situação complexa que requer expertise
- Cliente demonstra irritação com bot
- Após {max_attempts} tentativas sem sucesso
"""

    # Prompt para primeira interação
    FIRST_CONTACT = """
Mensagem do cliente: "{user_message}"

Esta é a primeira interação. Responda de forma acolhedora:
1. Agradeça o contato
2. Faça UMA pergunta estratégica relevante baseada na mensagem dele
3. Seja breve (máximo 2 linhas)

Se a mensagem já contém informações valiosas, reconheça isso antes de perguntar mais.
"""

    # Prompt para continuação da conversa
    CONTINUE_CONVERSATION = """
Histórico da conversa:
{conversation_history}

Dados já coletados:
{collected_data}

Dados ainda necessários:
{missing_fields}

Última mensagem do cliente: "{user_message}"

INSTRUÇÕES:
1. Analise se a última mensagem responde alguma pergunta anterior
2. Extraia e registre novas informações
3. Se tiver informações suficientes, agradeça e informe que um especialista entrará em contato
4. Caso contrário, faça a PRÓXIMA pergunta mais relevante
5. Seja natural - não pareça um interrogatório

Responda ao cliente:
"""

    # Prompt para extração de dados
    EXTRACT_DATA = """
Da seguinte conversa, extraia as informações estruturadas:

Conversa:
{conversation_text}

Extraia no formato JSON:
{schema}

Regras:
- Se uma informação não estiver clara, use null
- Normalize telefones para formato brasileiro
- Capitalize nomes próprios
- Para emails, valide formato básico
"""

    # Prompt para classificação de urgência
    CLASSIFY_URGENCY = """
Analise esta mensagem e classifique a urgência:

"{message}"

Níveis:
- baixa: Cliente fazendo pesquisa inicial, sem pressa
- media: Cliente interessado, tempo normal de resposta
- alta: Cliente com necessidade específica, quer resposta rápida
- urgente: Palavras como "urgente", "hoje", "agora", problema crítico

Responda APENAS com: baixa, media, alta ou urgente
"""

    # Mensagem de transição para humano
    HANDOFF_MESSAGE = """
Perfeito, {name}! 👍

Coletei as informações principais. Um especialista da nossa equipe vai entrar 
em contato com você em breve para dar continuidade.

Obrigado pela atenção! 

{additional_info}
"""

    # Mensagem quando lead não qualifica
    DISQUALIFICATION_MESSAGE = """
Agradeço muito pelo seu contato, {name}! 

No momento, {disqualification_reason}. 

{alternative_action}

Fique à vontade para entrar em contato novamente! 😊
"""

    @staticmethod
    def format_required_fields(fields: list) -> str:
        """Formata lista de campos obrigatórios"""
        return "\n".join([f"- {field}" for field in fields])
    
    @staticmethod
    def format_conversation_history(messages: list) -> str:
        """Formata histórico para o prompt"""
        formatted = []
        for msg in messages[-10:]:  # Últimas 10 mensagens
            role = "Cliente" if msg["role"] == "user" else "Você"
            formatted.append(f"{role}: {msg['content']}")
        return "\n".join(formatted)
    
    @staticmethod
    def format_collected_data(data: dict) -> str:
        """Formata dados coletados"""
        if not data:
            return "Nenhum dado coletado ainda"
        
        formatted = []
        for key, value in data.items():
            if value:
                formatted.append(f"- {key}: {value}")
        return "\n".join(formatted) if formatted else "Nenhum dado coletado ainda"
    
    @staticmethod
    def format_missing_fields(required: list, collected: dict) -> str:
        """Lista campos que ainda faltam"""
        missing = [field for field in required if field not in collected or not collected[field]]
        return ", ".join(missing) if missing else "Todos os dados coletados"


# Configurações específicas por tipo de negócio
class BusinessSpecificPrompts:
    """Prompts específicos por tipo de negócio"""
    
    ECOMMERCE = {
        "required_fields": [
            "Nome completo",
            "Produto de interesse",
            "Orçamento aproximado",
            "Prazo de compra"
        ],
        "qualification_message": "Ótimo! Vou conectar você com nosso consultor de vendas."
    }
    
    SERVICES = {
        "required_fields": [
            "Nome completo",
            "Tipo de serviço",
            "Localização",
            "Urgência"
        ],
        "qualification_message": "Perfeito! Um especialista vai entrar em contato."
    }
    
    B2B = {
        "required_fields": [
            "Nome completo",
            "Empresa",
            "Cargo",
            "Tamanho da empresa",
            "Necessidade específica"
        ],
        "qualification_message": "Excelente! Nosso time comercial vai preparar uma proposta."
    }
    
    REAL_ESTATE = {
        "required_fields": [
            "Nome completo",
            "Tipo de imóvel",
            "Localização preferida",
            "Faixa de preço",
            "Prazo"
        ],
        "qualification_message": "Ótimo! Vou direcionar para um corretor especializado."
    }