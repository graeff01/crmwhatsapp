"""
Serviço de Leads com suporte a qualificação por IA
Extensão do LeadService original
"""
from datetime import datetime
from typing import Dict, List, Optional
import json


class LeadService:
    """Serviço para gerenciamento de leads"""
    
    def __init__(self, db_connection=None):
        """
        Inicializa serviço
        
        Args:
            db_connection: Conexão com banco de dados
        """
        self.db = db_connection
    
    async def create_from_ai_qualification(self, crm_data: Dict) -> Dict:
        """
        Cria lead a partir de qualificação por IA
        
        Args:
            crm_data: Dados formatados do lead qualificado
            
        Returns:
            Lead criado com ID
        """
        try:
            # Prepara dados para inserção
            lead_data = {
                'phone': crm_data['phone'],
                'name': crm_data['name'],
                'status': crm_data.get('status', 'new'),
                'source': crm_data.get('source', 'ai_qualification'),
                'priority': crm_data.get('priority', 'medium'),
                'tags': json.dumps(crm_data.get('tags', [])),
                'custom_fields': json.dumps(crm_data.get('custom_fields', {})),
                'notes': crm_data.get('notes', ''),
                'qualification_score': crm_data.get('qualification_score', 0),
                'qualified_at': crm_data.get('qualified_at', datetime.now().isoformat()),
                'created_at': datetime.now().isoformat(),
                'assigned_to': self._get_next_available_agent()  # Round-robin ou regras de atribuição
            }
            
            # Insere no banco (exemplo simplificado)
            if self.db:
                lead_id = await self._insert_lead(lead_data)
            else:
                # Fallback para sistema sem BD (desenvolvimento)
                lead_id = f"LEAD_{datetime.now().timestamp()}"
            
            lead_data['id'] = lead_id
            
            # Notifica atendente atribuído
            await self._notify_assigned_agent(lead_data)
            
            # Log de auditoria
            await self._log_lead_creation(lead_data)
            
            return lead_data
            
        except Exception as e:
            raise Exception(f"Erro ao criar lead: {str(e)}")
    
    async def _insert_lead(self, lead_data: Dict) -> str:
        """Insere lead no banco de dados"""
        # Implementação real de insert no BD
        # Este é um exemplo simplificado
        query = """
            INSERT INTO leads (
                phone, name, status, source, priority, 
                tags, custom_fields, notes, qualification_score,
                qualified_at, created_at, assigned_to
            ) VALUES (
                %(phone)s, %(name)s, %(status)s, %(source)s, %(priority)s,
                %(tags)s, %(custom_fields)s, %(notes)s, %(qualification_score)s,
                %(qualified_at)s, %(created_at)s, %(assigned_to)s
            ) RETURNING id
        """
        
        result = await self.db.execute(query, lead_data)
        return result['id']
    
    def _get_next_available_agent(self) -> Optional[str]:
        """
        Determina próximo agente disponível
        
        Estratégias possíveis:
        - Round-robin
        - Menor carga de trabalho
        - Especialização por tipo de lead
        - Disponibilidade em tempo real
        """
        # Implementação simplificada - retorna None para fila geral
        # Em produção, implementar lógica sofisticada de atribuição
        return None
    
    async def _notify_assigned_agent(self, lead_data: Dict):
        """Notifica agente sobre novo lead"""
        if lead_data.get('assigned_to'):
            # Implementar notificação (push, email, SMS, etc)
            notification = {
                'type': 'new_lead',
                'agent_id': lead_data['assigned_to'],
                'lead_id': lead_data['id'],
                'priority': lead_data['priority'],
                'message': f"Novo lead qualificado por IA: {lead_data['name']}"
            }
            
            # Enviar notificação (implementar conforme sistema)
            # await notification_service.send(notification)
            pass
    
    async def _log_lead_creation(self, lead_data: Dict):
        """Registra criação de lead para auditoria"""
        log_entry = {
            'event': 'lead_created',
            'source': 'ai_qualification',
            'lead_id': lead_data['id'],
            'timestamp': datetime.now().isoformat(),
            'data': lead_data
        }
        
        # Salvar em sistema de logs (implementar conforme infraestrutura)
        # await audit_service.log(log_entry)
        pass
    
    async def get_ai_qualified_leads(
        self,
        limit: int = 50,
        offset: int = 0,
        priority: Optional[str] = None
    ) -> List[Dict]:
        """
        Obtém leads qualificados por IA
        
        Args:
            limit: Quantidade de leads
            offset: Paginação
            priority: Filtro por prioridade
            
        Returns:
            Lista de leads
        """
        query = """
            SELECT * FROM leads
            WHERE source = 'ai_qualification'
        """
        
        params = {}
        
        if priority:
            query += " AND priority = %(priority)s"
            params['priority'] = priority
        
        query += " ORDER BY qualified_at DESC LIMIT %(limit)s OFFSET %(offset)s"
        params.update({'limit': limit, 'offset': offset})
        
        if self.db:
            results = await self.db.fetch_all(query, params)
            return [dict(row) for row in results]
        
        return []
    
    async def get_lead_stats(self) -> Dict:
        """Retorna estatísticas de leads qualificados por IA"""
        if not self.db:
            return {}
        
        query = """
            SELECT 
                COUNT(*) as total,
                COUNT(CASE WHEN priority = 'urgent' THEN 1 END) as urgent,
                COUNT(CASE WHEN priority = 'high' THEN 1 END) as high,
                COUNT(CASE WHEN priority = 'medium' THEN 1 END) as medium,
                COUNT(CASE WHEN priority = 'low' THEN 1 END) as low,
                AVG(qualification_score) as avg_score,
                COUNT(CASE WHEN status = 'converted' THEN 1 END) as converted,
                COUNT(CASE WHEN status = 'lost' THEN 1 END) as lost
            FROM leads
            WHERE source = 'ai_qualification'
        """
        
        result = await self.db.fetch_one(query)
        
        return {
            'total_qualified': result['total'],
            'by_priority': {
                'urgent': result['urgent'],
                'high': result['high'],
                'medium': result['medium'],
                'low': result['low']
            },
            'avg_qualification_score': round(result['avg_score'], 2),
            'conversion_rate': (
                result['converted'] / result['total'] * 100 
                if result['total'] > 0 else 0
            ),
            'lost_rate': (
                result['lost'] / result['total'] * 100
                if result['total'] > 0 else 0
            )
        }
    
    async def update_lead_status(
        self,
        lead_id: str,
        new_status: str,
        notes: Optional[str] = None
    ) -> bool:
        """Atualiza status de um lead"""
        if not self.db:
            return False
        
        query = """
            UPDATE leads
            SET status = %(status)s,
                updated_at = %(updated_at)s
        """
        
        params = {
            'status': new_status,
            'updated_at': datetime.now().isoformat()
        }
        
        if notes:
            query += ", notes = CONCAT(notes, %(notes)s)"
            params['notes'] = f"\n\n[{datetime.now().isoformat()}] {notes}"
        
        query += " WHERE id = %(lead_id)s"
        params['lead_id'] = lead_id
        
        await self.db.execute(query, params)
        return True
    
    async def assign_lead(
        self,
        lead_id: str,
        agent_id: str
    ) -> bool:
        """Atribui lead a um agente"""
        if not self.db:
            return False
        
        query = """
            UPDATE leads
            SET assigned_to = %(agent_id)s,
                assigned_at = %(assigned_at)s
            WHERE id = %(lead_id)s
        """
        
        await self.db.execute(query, {
            'agent_id': agent_id,
            'assigned_at': datetime.now().isoformat(),
            'lead_id': lead_id
        })
        
        return True