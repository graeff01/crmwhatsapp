"""
Regras de negócio para qualificação de leads
Centraliza lógica de decisão e scoring
"""
from typing import Dict, List, Optional
from datetime import datetime
from ai_qualification.models import LeadConversation, QualificationStatus, QualificationCriteria, Message


class QualificationRules:
    """Regras para qualificar ou desqualificar leads"""
    
    # Palavras-chave que indicam desqualificação
    DISQUALIFICATION_KEYWORDS = [
        "spam", "teste", "bot", "desisto", 
        "não quero mais", "me tire da lista"
    ]
    
    # Palavras que indicam urgência
    URGENCY_KEYWORDS = {
        "urgente": 3,
        "hoje": 3,
        "agora": 3,
        "rápido": 2,
        "logo": 2,
        "em breve": 1
    }
    
    # Palavras positivas (aumentam score)
    POSITIVE_SIGNALS = [
        "interessado", "quero", "preciso", "gostaria",
        "quando", "como", "quanto custa", "valor",
        "comprar", "contratar", "orçamento"
    ]
    
    # Campos críticos por tipo de negócio
    CRITICAL_FIELDS = {
        "default": ["name", "phone"],
        "ecommerce": ["name", "phone", "product_interest"],
        "services": ["name", "phone", "service_type", "location"],
        "b2b": ["name", "phone", "company", "role"],
        "real_estate": ["name", "phone", "property_type", "budget"]
    }
    
    @staticmethod
    def calculate_lead_score(conversation: LeadConversation) -> int:
        """
        Calcula score do lead (0-100)
        
        Fatores considerados:
        - Completude dos dados (40 pontos)
        - Engajamento na conversa (30 pontos)
        - Sinais positivos (20 pontos)
        - Urgência (10 pontos)
        """
        score = 0
        
        # 1. Completude dos dados (40 pontos)
        required_fields = 5  # Ajustável
        collected_fields = len([v for v in conversation.collected_data.values() if v])
        completeness = min(collected_fields / required_fields, 1.0)
        score += int(completeness * 40)
        
        # 2. Engajamento (30 pontos)
        # Baseado no número de mensagens do usuário
        user_messages = [m for m in conversation.messages if m.role == "user"]
        engagement = min(len(user_messages) / 5, 1.0)  # 5 mensagens = 100%
        score += int(engagement * 30)
        
        # 3. Sinais positivos (20 pontos)
        positive_count = 0
        for message in user_messages:
            content_lower = message.content.lower()
            positive_count += sum(
                1 for signal in QualificationRules.POSITIVE_SIGNALS
                if signal in content_lower
            )
        
        positive_score = min(positive_count / 3, 1.0)  # 3 sinais = 100%
        score += int(positive_score * 20)
        
        # 4. Urgência (10 pontos)
        urgency_score = QualificationRules._calculate_urgency_score(conversation)
        score += urgency_score
        
        return min(score, 100)
    
    @staticmethod
    def _calculate_urgency_score(conversation: LeadConversation) -> int:
        """Calcula score de urgência (0-10)"""
        urgency_points = 0
        
        for message in conversation.messages:
            if message.role == "user":
                content_lower = message.content.lower()
                for keyword, points in QualificationRules.URGENCY_KEYWORDS.items():
                    if keyword in content_lower:
                        urgency_points = max(urgency_points, points)
        
        # Normaliza para 0-10
        return min(int(urgency_points * 3.33), 10)
    
    @staticmethod
    def should_qualify(conversation: LeadConversation, business_type: str = "default") -> bool:
        """
        Determina se o lead deve ser qualificado
        
        Args:
            conversation: Conversa do lead
            business_type: Tipo de negócio para regras específicas
            
        Returns:
            True se deve qualificar, False caso contrário
        """
        # Verifica campos críticos
        critical_fields = QualificationRules.CRITICAL_FIELDS.get(
            business_type, 
            QualificationRules.CRITICAL_FIELDS["default"]
        )
        
        has_critical_fields = all(
            field in conversation.collected_data and conversation.collected_data[field]
            for field in critical_fields
        )
        
        if not has_critical_fields:
            return False
        
        # Verifica score mínimo
        score = QualificationRules.calculate_lead_score(conversation)
        if score < 50:  # Score mínimo para qualificação
            return False
        
        # Verifica sinais de desqualificação
        if QualificationRules.should_disqualify(conversation):
            return False
        
        return True
    
    @staticmethod
    def should_disqualify(conversation: LeadConversation) -> bool:
        """Verifica se o lead deve ser desqualificado"""
        # Verifica palavras-chave de desqualificação
        for message in conversation.messages:
            if message.role == "user":
                content_lower = message.content.lower()
                if any(keyword in content_lower for keyword in QualificationRules.DISQUALIFICATION_KEYWORDS):
                    return True
        
        # Verifica tentativas excessivas sem progresso
        if conversation.attempts >= 5:
            if len(conversation.collected_data) < 2:
                return True
        
        return False
    
    @staticmethod
    def should_escalate_to_human(conversation: LeadConversation) -> bool:
        """Verifica se deve escalar para atendimento humano"""
        # Cliente pede explicitamente
        keywords_human = ["falar com pessoa", "atendente", "humano", "pessoa real"]
        for message in conversation.messages:
            if message.role == "user":
                content_lower = message.content.lower()
                if any(keyword in content_lower for keyword in keywords_human):
                    return True
        
        # Muitas tentativas sem sucesso
        if conversation.attempts >= 4 and len(conversation.collected_data) < 3:
            return True
        
        # Lead de alto valor (score alto mas faltam detalhes)
        score = QualificationRules.calculate_lead_score(conversation)
        if score >= 70 and not QualificationRules.should_qualify(conversation):
            return True
        
        return False
    
    @staticmethod
    def determine_priority(conversation: LeadConversation) -> str:
        """
        Determina prioridade do lead
        
        Returns:
            "urgent", "high", "medium", ou "low"
        """
        score = QualificationRules.calculate_lead_score(conversation)
        urgency = QualificationRules._calculate_urgency_score(conversation)
        
        # Urgente: score alto + urgência alta
        if score >= 80 and urgency >= 7:
            return "urgent"
        
        # Alta: score alto OU urgência alta
        if score >= 70 or urgency >= 7:
            return "high"
        
        # Média: score médio
        if score >= 50:
            return "medium"
        
        return "low"
    
    @staticmethod
    def suggest_tags(conversation: LeadConversation) -> List[str]:
        """Sugere tags baseado na conversa"""
        tags = []
        
        # Tag por fonte
        tags.append("ai_qualified")
        
        # Tag por urgência
        urgency = QualificationRules._calculate_urgency_score(conversation)
        if urgency >= 7:
            tags.append("urgent")
        
        # Tags por palavras-chave
        all_text = " ".join([m.content.lower() for m in conversation.messages if m.role == "user"])
        
        keyword_tags = {
            "orçamento": "budget_request",
            "valor": "pricing_inquiry",
            "comprar": "ready_to_buy",
            "dúvida": "has_questions",
            "comparar": "comparing_options",
            "urgente": "urgent",
            "problema": "has_issue"
        }
        
        for keyword, tag in keyword_tags.items():
            if keyword in all_text:
                tags.append(tag)
        
        return list(set(tags))  # Remove duplicatas
    
    @staticmethod
    def generate_summary(conversation: LeadConversation) -> str:
        """Gera resumo executivo da conversa para o CRM"""
        summary_parts = []
        
        # Score e prioridade
        score = QualificationRules.calculate_lead_score(conversation)
        priority = QualificationRules.determine_priority(conversation)
        summary_parts.append(f"Score: {score}/100 | Prioridade: {priority.upper()}")
        
        # Dados coletados
        if conversation.collected_data:
            summary_parts.append("\nInformações coletadas:")
            for key, value in conversation.collected_data.items():
                if value:
                    summary_parts.append(f"• {key}: {value}")
        
        # Observações importantes
        if conversation.notes:
            summary_parts.append("\nObservações:")
            for note in conversation.notes[-3:]:  # Últimas 3 notas
                summary_parts.append(f"• {note}")
        
        # Contexto da conversa
        user_messages = [m.content for m in conversation.messages if m.role == "user"]
        if user_messages:
            summary_parts.append(f"\nMensagens do cliente: {len(user_messages)}")
            summary_parts.append(f"Primeira mensagem: \"{user_messages[0][:100]}...\"")

        return "\n".join(summary_parts)


class QualificationEngine:
    """
    Motor de qualificação de leads usando IA
    Orquestra conversas, aplica regras e gerencia estado
    """

    def __init__(self, ai_provider, business_type: str = "default",
                 qualification_criteria: Optional[QualificationCriteria] = None):
        """
        Inicializa o motor de qualificação

        Args:
            ai_provider: Provider de IA (OpenAI, Anthropic, etc)
            business_type: Tipo de negócio para regras específicas
            qualification_criteria: Critérios de qualificação personalizados
        """
        self.ai_provider = ai_provider
        self.business_type = business_type
        self.criteria = qualification_criteria or QualificationCriteria()
        self.active_conversations: Dict[str, LeadConversation] = {}
        self.completed_conversations: List[LeadConversation] = []

    async def process_message(self, phone: str, message: str, metadata: Dict = None) -> Dict:
        """
        Processa mensagem de um lead

        Args:
            phone: Telefone do lead
            message: Mensagem recebida
            metadata: Metadados adicionais

        Returns:
            Dict com status, resposta e dados para CRM
        """
        metadata = metadata or {}

        # Obtém ou cria conversa
        conversation = self.get_or_create_conversation(phone, metadata)

        # Adiciona mensagem do usuário
        conversation.add_message("user", message)
        conversation.increment_attempts()

        # Verifica se deve desqualificar
        if QualificationRules.should_disqualify(conversation):
            conversation.status = QualificationStatus.DISQUALIFIED
            response = "Obrigado pelo contato. No momento não conseguimos prosseguir com seu atendimento."
            self.end_conversation(phone, "Desqualificado")
            return {
                "status": "disqualified",
                "response": response,
                "should_send_to_crm": False
            }

        # Verifica se deve escalar para humano
        if QualificationRules.should_escalate_to_human(conversation):
            return await self._handle_escalation(conversation)

        # Processa com IA
        ai_response = await self._get_ai_response(conversation, message)

        # Adiciona resposta da IA
        conversation.add_message("assistant", ai_response["response"])

        # Extrai dados estruturados da resposta da IA
        if ai_response.get("collected_data"):
            for key, value in ai_response["collected_data"].items():
                conversation.collect_data(key, value)

        # Atualiza score
        conversation.score = QualificationRules.calculate_lead_score(conversation)

        # Verifica se está qualificado
        if QualificationRules.should_qualify(conversation, self.business_type):
            conversation.status = QualificationStatus.QUALIFIED
            return {
                "status": "qualified",
                "response": ai_response["response"],
                "should_send_to_crm": True,
                "crm_data": self._prepare_crm_data(conversation)
            }

        # Conversa ainda em progresso
        return {
            "status": "in_progress",
            "response": ai_response["response"],
            "should_send_to_crm": False,
            "score": conversation.score
        }

    async def _get_ai_response(self, conversation: LeadConversation, message: str) -> Dict:
        """
        Obtém resposta da IA

        Args:
            conversation: Conversa atual
            message: Mensagem do usuário

        Returns:
            Dict com resposta e dados coletados
        """
        # Prepara contexto para IA
        system_prompt = self._build_system_prompt(conversation)
        conversation_history = [
            {"role": m.role, "content": m.content}
            for m in conversation.messages[-10:]  # Últimas 10 mensagens
        ]

        # Chama provider de IA
        ai_response = await self.ai_provider.generate_response(
            system_prompt=system_prompt,
            messages=conversation_history
        )

        return {
            "response": ai_response.get("message", "Desculpe, não entendi. Pode reformular?"),
            "collected_data": ai_response.get("extracted_data", {})
        }

    def _build_system_prompt(self, conversation: LeadConversation) -> str:
        """Constrói prompt de sistema para IA"""
        missing_fields = [
            field for field in self.criteria.required_fields
            if field not in conversation.collected_data
        ]

        prompt = f"""Você é um assistente de qualificação de leads para um negócio tipo: {self.business_type}.

Seu objetivo é coletar as seguintes informações de forma natural e amigável:
{', '.join(self.criteria.required_fields)}

Informações já coletadas: {list(conversation.collected_data.keys())}
Ainda faltam: {missing_fields}

Score atual do lead: {conversation.score}/100
Tentativas: {conversation.attempts}/{self.criteria.max_attempts}

Diretrizes:
1. Seja amigável e profissional
2. Faça UMA pergunta por vez
3. Se o cliente demonstrar urgência, colete informações essenciais rapidamente
4. Se o cliente pedir para falar com humano, indique que iremos transferir
5. Extraia dados estruturados sempre que possível

Responda de forma natural e objetiva."""

        return prompt

    async def _handle_escalation(self, conversation: LeadConversation) -> Dict:
        """Escalação para atendimento humano"""
        conversation.status = QualificationStatus.NEEDS_HUMAN
        conversation.add_note("Escalado para atendimento humano")

        response = """Entendo! Vou transferir você para um de nossos especialistas que poderá ajudá-lo melhor.
Em breve um membro da nossa equipe entrará em contato. Obrigado pela paciência!"""

        conversation.add_message("assistant", response)

        return {
            "status": "escalated",
            "response": response,
            "should_send_to_crm": True,
            "crm_data": self._prepare_crm_data(conversation, escalated=True)
        }

    def _prepare_crm_data(self, conversation: LeadConversation, escalated: bool = False) -> Dict:
        """Prepara dados para envio ao CRM"""
        priority = QualificationRules.determine_priority(conversation)
        tags = QualificationRules.suggest_tags(conversation)
        summary = QualificationRules.generate_summary(conversation)

        if escalated:
            tags.append("escalated_from_ai")

        return {
            "phone": conversation.phone,
            "name": conversation.collected_data.get("name", ""),
            "collected_data": conversation.collected_data,
            "score": conversation.score,
            "priority": priority,
            "tags": tags,
            "summary": summary,
            "conversation_history": [
                {"role": m.role, "content": m.content, "timestamp": m.timestamp}
                for m in conversation.messages
            ],
            "notes": conversation.notes,
            "qualification_status": conversation.status.value
        }

    def get_or_create_conversation(self, phone: str, metadata: Dict = None) -> LeadConversation:
        """Obtém conversa existente ou cria nova"""
        if phone not in self.active_conversations:
            conversation = LeadConversation(phone=phone)

            # Adiciona informações de metadata
            if metadata:
                if "contact_name" in metadata:
                    conversation.collect_data("name", metadata["contact_name"])

            self.active_conversations[phone] = conversation

        return self.active_conversations[phone]

    def get_conversation(self, phone: str) -> Optional[LeadConversation]:
        """Retorna conversa ativa ou None"""
        return self.active_conversations.get(phone)

    def end_conversation(self, phone: str, reason: str = "Completed"):
        """Encerra uma conversa"""
        if phone in self.active_conversations:
            conversation = self.active_conversations[phone]
            conversation.status = QualificationStatus.COMPLETED
            conversation.add_note(f"Encerrado: {reason}")

            # Move para conversas completas
            self.completed_conversations.append(conversation)
            del self.active_conversations[phone]

    def get_stats(self) -> Dict:
        """Retorna estatísticas do sistema"""
        total_conversations = len(self.active_conversations) + len(self.completed_conversations)

        qualified = sum(
            1 for conv in self.completed_conversations
            if conv.status == QualificationStatus.QUALIFIED
        )

        disqualified = sum(
            1 for conv in self.completed_conversations
            if conv.status == QualificationStatus.DISQUALIFIED
        )

        escalated = sum(
            1 for conv in self.completed_conversations
            if conv.status == QualificationStatus.NEEDS_HUMAN
        )

        avg_score = 0
        if self.completed_conversations:
            avg_score = sum(c.score for c in self.completed_conversations) / len(self.completed_conversations)

        return {
            "total_conversations": total_conversations,
            "active_conversations": len(self.active_conversations),
            "completed_conversations": len(self.completed_conversations),
            "qualified_leads": qualified,
            "disqualified_leads": disqualified,
            "escalated_to_human": escalated,
            "average_score": round(avg_score, 1),
            "conversion_rate": (qualified / total_conversations * 100) if total_conversations > 0 else 0
        }