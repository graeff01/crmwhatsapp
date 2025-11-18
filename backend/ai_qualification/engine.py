"""
Regras de negócio para qualificação de leads
Centraliza lógica de decisão e scoring
"""
from typing import Dict, List, Optional
from models import LeadConversation, QualificationStatus


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
        user_messages = [m for m in conversation.messages if m.role.value == "user"]
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
            if message.role.value == "user":
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
            if message.role.value == "user":
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
            if message.role.value == "user":
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
        all_text = " ".join([m.content.lower() for m in conversation.messages if m.role.value == "user"])
        
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
        user_messages = [m.content for m in conversation.messages if m.role.value == "user"]
        if user_messages:
            summary_parts.append(f"\nMensagens do cliente: {len(user_messages)}")
            summary_parts.append(f"Primeira mensagem: \"{user_messages[0][:100]}...\"")
        
        return "\n".join(summary_parts)


class QualificationEngine:
    """
    Engine principal de qualificação de leads por IA
    Gerencia conversas, processa mensagens e toma decisões
    """

    def __init__(self, ai_provider, business_type: str = "default", qualification_criteria=None):
        """
        Inicializa a engine de qualificação

        Args:
            ai_provider: Provider de IA (OpenAI, etc)
            business_type: Tipo de negócio para regras específicas
            qualification_criteria: Critérios de qualificação
        """
        self.ai_provider = ai_provider
        self.business_type = business_type
        self.criteria = qualification_criteria
        self.active_conversations: Dict[str, LeadConversation] = {}
        self.stats = {
            'total_conversations': 0,
            'qualified': 0,
            'disqualified': 0,
            'escalated': 0,
            'in_progress': 0
        }

    async def process_message(self, phone: str, message: str, metadata: Dict = None) -> Dict:
        """
        Processa uma mensagem recebida do lead

        Args:
            phone: Telefone do lead
            message: Mensagem recebida
            metadata: Metadados adicionais

        Returns:
            Dict com resposta e status da qualificação
        """
        from models import MessageRole

        # Busca ou cria conversa
        conversation = self.get_or_create_conversation(phone, metadata)

        # Adiciona mensagem do usuário
        conversation.add_message(MessageRole.USER, message)

        # Verifica se deve escalar para humano
        if QualificationRules.should_escalate_to_human(conversation):
            return await self._handle_escalation(conversation)

        # Verifica se deve desqualificar
        if QualificationRules.should_disqualify(conversation):
            return self._handle_disqualification(conversation)

        # Verifica se já está qualificado
        if QualificationRules.should_qualify(conversation, self.business_type):
            return await self._handle_qualification(conversation)

        # Continua coletando informações
        return await self._continue_qualification(conversation, message)

    def get_or_create_conversation(self, phone: str, metadata: Dict = None) -> LeadConversation:
        """Busca conversa existente ou cria nova"""
        if phone not in self.active_conversations:
            conversation = LeadConversation(phone=phone, metadata=metadata or {})
            self.active_conversations[phone] = conversation
            self.stats['total_conversations'] += 1
            self.stats['in_progress'] += 1
        return self.active_conversations[phone]

    def get_conversation(self, phone: str) -> Optional[LeadConversation]:
        """Retorna conversa específica"""
        return self.active_conversations.get(phone)

    def end_conversation(self, phone: str, reason: str = "Manual"):
        """Encerra uma conversa"""
        if phone in self.active_conversations:
            conversation = self.active_conversations[phone]
            conversation.end_conversation(QualificationStatus.COMPLETED)
            conversation.add_note(f"Encerrada: {reason}")
            del self.active_conversations[phone]
            self.stats['in_progress'] = max(0, self.stats['in_progress'] - 1)

    async def _handle_escalation(self, conversation: LeadConversation) -> Dict:
        """Escalação para atendimento humano"""
        from models import MessageRole

        conversation.status = QualificationStatus.ESCALATED
        self.stats['escalated'] += 1
        self.stats['in_progress'] = max(0, self.stats['in_progress'] - 1)

        response = "Entendo! Vou transferir você para um de nossos especialistas que poderá te atender melhor. Aguarde um momento."
        conversation.add_message(MessageRole.ASSISTANT, response)

        return {
            'status': 'escalated',
            'response': response,
            'should_send_to_crm': True,
            'crm_data': self._prepare_crm_data(conversation)
        }

    def _handle_disqualification(self, conversation: LeadConversation) -> Dict:
        """Desqualificação do lead"""
        from models import MessageRole

        conversation.status = QualificationStatus.DISQUALIFIED
        self.stats['disqualified'] += 1
        self.stats['in_progress'] = max(0, self.stats['in_progress'] - 1)

        response = "Obrigado pelo contato! Se precisar de algo, estamos à disposição."
        conversation.add_message(MessageRole.ASSISTANT, response)

        return {
            'status': 'disqualified',
            'response': response,
            'should_send_to_crm': False
        }

    async def _handle_qualification(self, conversation: LeadConversation) -> Dict:
        """Lead qualificado com sucesso"""
        from models import MessageRole

        conversation.status = QualificationStatus.QUALIFIED
        conversation.qualification_score = QualificationRules.calculate_lead_score(conversation)
        self.stats['qualified'] += 1
        self.stats['in_progress'] = max(0, self.stats['in_progress'] - 1)

        response = "Perfeito! Coletamos todas as informações necessárias. Em breve nossa equipe entrará em contato com você!"
        conversation.add_message(MessageRole.ASSISTANT, response)

        return {
            'status': 'qualified',
            'response': response,
            'should_send_to_crm': True,
            'crm_data': self._prepare_crm_data(conversation)
        }

    async def _continue_qualification(self, conversation: LeadConversation, user_message: str) -> Dict:
        """Continua processo de qualificação"""
        from models import MessageRole

        # Monta contexto para IA
        context = self._build_ai_context(conversation)

        # Chama IA para gerar próxima pergunta
        try:
            ai_response = await self.ai_provider.generate_response(
                context=context,
                user_message=user_message,
                conversation_history=conversation.get_conversation_history()
            )

            response = ai_response.get('message', 'Desculpe, tive um problema. Pode repetir?')

            # Extrai dados da resposta (se a IA detectou)
            if 'extracted_data' in ai_response:
                conversation.update_collected_data(ai_response['extracted_data'])

        except Exception as e:
            response = "Desculpe, tive um problema técnico. Pode repetir sua mensagem?"
            conversation.add_note(f"Erro IA: {str(e)}")

        conversation.add_message(MessageRole.ASSISTANT, response)

        # Atualiza score
        conversation.qualification_score = QualificationRules.calculate_lead_score(conversation)

        return {
            'status': 'collecting',
            'response': response,
            'should_send_to_crm': False,
            'score': conversation.qualification_score
        }

    def _build_ai_context(self, conversation: LeadConversation) -> str:
        """Constrói contexto para enviar à IA"""
        missing_fields = [
            field for field in self.criteria.required_fields
            if field not in conversation.collected_data
        ]

        context = f"""
Você é um assistente de qualificação de leads para uma empresa de {self.business_type}.

Campos já coletados: {list(conversation.collected_data.keys())}
Campos faltando: {missing_fields}
Tentativas: {conversation.attempts}/{self.criteria.max_attempts}

Sua tarefa é fazer perguntas naturais e amigáveis para coletar os campos faltando.
Seja breve, objetivo e profissional.
"""
        return context

    def _prepare_crm_data(self, conversation: LeadConversation) -> Dict:
        """Prepara dados para enviar ao CRM"""
        return {
            'phone': conversation.phone,
            'name': conversation.collected_data.get('name', ''),
            'status': conversation.status.value,
            'score': conversation.qualification_score,
            'priority': QualificationRules.determine_priority(conversation),
            'tags': QualificationRules.suggest_tags(conversation),
            'notes': QualificationRules.generate_summary(conversation),
            'collected_data': conversation.collected_data,
            'metadata': conversation.metadata
        }

    def get_stats(self) -> Dict:
        """Retorna estatísticas da engine"""
        return {
            **self.stats,
            'active_conversations': len(self.active_conversations)
        }