"""
Utilidades para paginação, busca e performance
"""
import sqlite3
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta


class Paginator:
    """
    Classe para paginar resultados
    """
    def __init__(self, items: List[Any], page: int = 1, per_page: int = 20):
        self.items = items
        self.page = max(1, page)
        self.per_page = min(100, max(1, per_page))  # Limite de 100 itens por página
        self.total = len(items)
        self.pages = (self.total + self.per_page - 1) // self.per_page or 1
    
    def get_page_items(self) -> List[Any]:
        """Retorna itens da página atual"""
        start = (self.page - 1) * self.per_page
        end = start + self.per_page
        return self.items[start:end]
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário com metadados"""
        return {
            "items": self.get_page_items(),
            "pagination": {
                "page": self.page,
                "per_page": self.per_page,
                "total_items": self.total,
                "total_pages": self.pages,
                "has_next": self.page < self.pages,
                "has_prev": self.page > 1
            }
        }


class MessageSearcher:
    """
    Busca otimizada de mensagens com filtros
    """
    def __init__(self, database):
        self.db = database
    
    def search_messages(
        self,
        lead_id: Optional[int] = None,
        search_term: Optional[str] = None,
        sender_type: Optional[str] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        limit: int = 50,
        offset: int = 0
    ) -> Dict[str, Any]:
        """
        Busca mensagens com filtros avançados
        
        Args:
            lead_id: Filtrar por lead específico
            search_term: Termo de busca no conteúdo
            sender_type: Tipo de remetente (lead/vendedor/sistema)
            date_from: Data inicial
            date_to: Data final
            limit: Quantidade máxima de resultados
            offset: Offset para paginação
        
        Returns:
            Dict com mensagens e total de resultados
        """
        conn = sqlite3.connect(self.db.db_name)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Construir query
        query = "SELECT * FROM messages WHERE 1=1"
        params = []
        
        # Filtros
        if lead_id:
            query += " AND lead_id = ?"
            params.append(lead_id)
        
        if search_term:
            query += " AND content LIKE ?"
            params.append(f"%{search_term}%")
        
        if sender_type:
            query += " AND sender_type = ?"
            params.append(sender_type)
        
        if date_from:
            query += " AND timestamp >= ?"
            params.append(date_from.isoformat())
        
        if date_to:
            query += " AND timestamp <= ?"
            params.append(date_to.isoformat())
        
        # Count total
        count_query = query.replace("SELECT *", "SELECT COUNT(*)")
        cursor.execute(count_query, params)
        total = cursor.fetchone()[0]
        
        # Buscar com paginação
        query += " ORDER BY timestamp DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])
        
        cursor.execute(query, params)
        messages = [dict(row) for row in cursor.fetchall()]
        
        conn.close()
        
        return {
            "messages": messages,
            "total": total,
            "limit": limit,
            "offset": offset
        }
    
    def search_in_lead(self, lead_id: int, search_term: str) -> List[Dict[str, Any]]:
        """
        Busca mensagens em um lead específico
        Retorna com contexto (mensagens antes e depois)
        """
        conn = sqlite3.connect(self.db.db_name)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Buscar mensagens que correspondem ao termo
        cursor.execute("""
            SELECT id, content, timestamp, sender_type, sender_name
            FROM messages
            WHERE lead_id = ? AND content LIKE ?
            ORDER BY timestamp DESC
            LIMIT 10
        """, (lead_id, f"%{search_term}%"))
        
        results = []
        for row in cursor.fetchall():
            message_id = row['id']
            
            # Buscar contexto (2 mensagens antes e 2 depois)
            cursor.execute("""
                SELECT * FROM messages
                WHERE lead_id = ?
                AND id BETWEEN ? AND ?
                ORDER BY id ASC
            """, (lead_id, message_id - 2, message_id + 2))
            
            context = [dict(r) for r in cursor.fetchall()]
            
            results.append({
                "match": dict(row),
                "context": context
            })
        
        conn.close()
        return results


class LeadSearcher:
    """
    Busca otimizada de leads
    """
    def __init__(self, database):
        self.db = database
    
    def search_leads(
        self,
        search_term: Optional[str] = None,
        status: Optional[str] = None,
        assigned_to: Optional[int] = None,
        city: Optional[str] = None,
        origin: Optional[str] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        sort_by: str = "updated_at",
        sort_order: str = "DESC",
        limit: int = 50,
        offset: int = 0
    ) -> Dict[str, Any]:
        """
        Busca leads com filtros avançados
        
        Args:
            search_term: Busca em nome, telefone e email
            status: Filtrar por status
            assigned_to: Filtrar por vendedor
            city: Filtrar por cidade
            origin: Filtrar por origem
            date_from: Data inicial
            date_to: Data final
            sort_by: Campo para ordenação
            sort_order: ASC ou DESC
            limit: Quantidade máxima de resultados
            offset: Offset para paginação
        
        Returns:
            Dict com leads e total de resultados
        """
        conn = sqlite3.connect(self.db.db_name)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Construir query
        query = """
            SELECT l.*, u.name as vendedor_name,
                   COUNT(DISTINCT m.id) as messages_count
            FROM leads l
            LEFT JOIN users u ON l.assigned_to = u.id
            LEFT JOIN messages m ON l.id = m.lead_id
            WHERE 1=1
        """
        params = []
        
        # Filtros
        if search_term:
            query += " AND (l.name LIKE ? OR l.phone LIKE ? OR l.email LIKE ?)"
            search_pattern = f"%{search_term}%"
            params.extend([search_pattern, search_pattern, search_pattern])
        
        if status:
            query += " AND l.status = ?"
            params.append(status)
        
        if assigned_to is not None:
            if assigned_to == -1:  # Não atribuídos
                query += " AND l.assigned_to IS NULL"
            else:
                query += " AND l.assigned_to = ?"
                params.append(assigned_to)
        
        if city:
            query += " AND l.city LIKE ?"
            params.append(f"%{city}%")
        
        if origin:
            query += " AND l.origin LIKE ?"
            params.append(f"%{origin}%")
        
        if date_from:
            query += " AND l.created_at >= ?"
            params.append(date_from.isoformat())
        
        if date_to:
            query += " AND l.created_at <= ?"
            params.append(date_to.isoformat())
        
        query += " GROUP BY l.id"
        
        # Count total
        count_query = f"SELECT COUNT(*) FROM ({query})"
        cursor.execute(count_query, params)
        total = cursor.fetchone()[0]
        
        # Ordenação
        valid_sort_fields = ['id', 'name', 'phone', 'status', 'created_at', 'updated_at', 'last_message_at']
        if sort_by not in valid_sort_fields:
            sort_by = 'updated_at'
        
        sort_order = 'DESC' if sort_order.upper() == 'DESC' else 'ASC'
        query += f" ORDER BY l.{sort_by} {sort_order}"
        
        # Paginação
        query += " LIMIT ? OFFSET ?"
        params.extend([limit, offset])
        
        cursor.execute(query, params)
        leads = [dict(row) for row in cursor.fetchall()]
        
        conn.close()
        
        return {
            "leads": leads,
            "total": total,
            "limit": limit,
            "offset": offset
        }


class PerformanceCache:
    """
    Cache simples em memória para queries frequentes
    Em produção: usar Redis
    """
    def __init__(self, ttl_seconds: int = 300):
        self.cache = {}
        self.ttl = ttl_seconds
    
    def get(self, key: str) -> Optional[Any]:
        """Busca item no cache"""
        if key in self.cache:
            item, timestamp = self.cache[key]
            if (datetime.now() - timestamp).total_seconds() < self.ttl:
                return item
            else:
                del self.cache[key]
        return None
    
    def set(self, key: str, value: Any):
        """Adiciona item ao cache"""
        self.cache[key] = (value, datetime.now())
    
    def delete(self, key: str):
        """Remove item do cache"""
        if key in self.cache:
            del self.cache[key]
    
    def clear(self):
        """Limpa todo o cache"""
        self.cache.clear()
    
    def clear_expired(self):
        """Remove itens expirados"""
        now = datetime.now()
        expired_keys = [
            key for key, (_, timestamp) in self.cache.items()
            if (now - timestamp).total_seconds() >= self.ttl
        ]
        for key in expired_keys:
            del self.cache[key]


class QueryOptimizer:
    """
    Otimizador de queries com estatísticas
    """
    def __init__(self):
        self.stats = {
            'total_queries': 0,
            'slow_queries': [],
            'cache_hits': 0,
            'cache_misses': 0
        }
    
    def log_query(self, query: str, duration: float, used_cache: bool = False):
        """Registra estatísticas de uma query"""
        self.stats['total_queries'] += 1
        
        if used_cache:
            self.stats['cache_hits'] += 1
        else:
            self.stats['cache_misses'] += 1
        
        # Registra queries lentas (> 1 segundo)
        if duration > 1.0:
            self.stats['slow_queries'].append({
                'query': query,
                'duration': duration,
                'timestamp': datetime.now().isoformat()
            })
            
            # Mantém apenas últimas 100 queries lentas
            if len(self.stats['slow_queries']) > 100:
                self.stats['slow_queries'] = self.stats['slow_queries'][-100:]
    
    def get_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas"""
        return {
            **self.stats,
            'cache_hit_rate': (
                self.stats['cache_hits'] / self.stats['total_queries'] * 100
                if self.stats['total_queries'] > 0 else 0
            )
        }