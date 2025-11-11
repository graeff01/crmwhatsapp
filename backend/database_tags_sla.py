"""
EXTENSÃO DO DATABASE.PY - TAGS + SLA TRACKING

Adicione este código ao final do seu database.py existente
ou importe estas funções no seu arquivo atual
"""
import sqlite3
from datetime import datetime, timedelta
import json


class DatabaseTagsSLA:
    """
    Extensão para adicionar Tags e SLA Tracking ao banco existente
    """
    
    def __init__(self, db_name="crm_whatsapp.db"):
        self.db_name = db_name
        self.init_tags_sla_tables()
    
    # =============================
    # INICIALIZAÇÃO DAS TABELAS
    # =============================
    def init_tags_sla_tables(self):
        """Cria tabelas de Tags e SLA"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        # Tabela de Tags disponíveis
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tags (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                color TEXT NOT NULL,
                icon TEXT,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Tabela de relacionamento Lead-Tag (many-to-many)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS lead_tags (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                lead_id INTEGER NOT NULL,
                tag_id INTEGER NOT NULL,
                added_by INTEGER,
                added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (lead_id) REFERENCES leads(id),
                FOREIGN KEY (tag_id) REFERENCES tags(id),
                FOREIGN KEY (added_by) REFERENCES users(id),
                UNIQUE(lead_id, tag_id)
            )
        """)
        
        # Tabela de SLA (métricas de tempo)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS lead_sla (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                lead_id INTEGER NOT NULL UNIQUE,
                first_contact_at TIMESTAMP,
                first_response_at TIMESTAMP,
                first_response_time_seconds INTEGER,
                last_interaction_at TIMESTAMP,
                total_response_time_seconds INTEGER DEFAULT 0,
                response_count INTEGER DEFAULT 0,
                avg_response_time_seconds INTEGER,
                status TEXT DEFAULT 'pending',
                sla_met BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (lead_id) REFERENCES leads(id)
            )
        """)
        
        conn.commit()
        
        # Inserir tags padrão se não existirem
        self._insert_default_tags(cursor)
        
        conn.commit()
        conn.close()
        
        print("✅ Tabelas de Tags e SLA criadas com sucesso!")
    
    def _insert_default_tags(self, cursor):
        """Insere tags padrão do sistema"""
        default_tags = [
            ("🔥 Quente", "#FF4444", "🔥", "Lead com alta chance de conversão"),
            ("⭐ VIP", "#FFD700", "⭐", "Cliente importante ou alto ticket"),
            ("⚡ Urgente", "#FF6600", "⚡", "Requer atenção imediata"),
            ("💰 Alto Ticket", "#00AA00", "💰", "Oportunidade de alto valor"),
            ("📅 Agendar Retorno", "#4169E1", "📅", "Marcar para contato futuro"),
            ("🤔 Indeciso", "#FFA500", "🤔", "Cliente em dúvida"),
            ("❌ Não Qualificado", "#999999", "❌", "Não se encaixa no perfil"),
            ("🎯 Novo Lead", "#00CED1", "🎯", "Lead recém chegado"),
            ("📞 Sem Resposta", "#8B008B", "📞", "Tentativas sem sucesso"),
            ("✅ Pronto para Fechar", "#32CD32", "✅", "Negociação avançada"),
        ]
        
        for name, color, icon, description in default_tags:
            try:
                cursor.execute("""
                    INSERT OR IGNORE INTO tags (name, color, icon, description)
                    VALUES (?, ?, ?, ?)
                """, (name, color, icon, description))
            except:
                pass
    
    # =============================
    # GESTÃO DE TAGS
    # =============================
    def get_all_tags(self):
        """Retorna todas as tags disponíveis"""
        conn = sqlite3.connect(self.db_name)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT t.*, COUNT(lt.lead_id) as usage_count
            FROM tags t
            LEFT JOIN lead_tags lt ON t.id = lt.tag_id
            GROUP BY t.id
            ORDER BY t.name
        """)
        
        tags = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return tags
    
    def create_tag(self, name, color, icon="", description=""):
        """Cria uma nova tag"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                INSERT INTO tags (name, color, icon, description)
                VALUES (?, ?, ?, ?)
            """, (name, color, icon, description))
            conn.commit()
            tag_id = cursor.lastrowid
            conn.close()
            return tag_id
        except sqlite3.IntegrityError:
            conn.close()
            return None  # Tag já existe
    
    def get_lead_tags(self, lead_id):
        """Retorna todas as tags de um lead"""
        conn = sqlite3.connect(self.db_name)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT t.*, lt.added_at, u.name as added_by_name
            FROM tags t
            JOIN lead_tags lt ON t.id = lt.tag_id
            LEFT JOIN users u ON lt.added_by = u.id
            WHERE lt.lead_id = ?
            ORDER BY lt.added_at DESC
        """, (lead_id,))
        
        tags = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return tags
    
    def add_tag_to_lead(self, lead_id, tag_id, user_id=None):
        """Adiciona uma tag a um lead"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                INSERT INTO lead_tags (lead_id, tag_id, added_by)
                VALUES (?, ?, ?)
            """, (lead_id, tag_id, user_id))
            conn.commit()
            conn.close()
            return True
        except sqlite3.IntegrityError:
            conn.close()
            return False  # Tag já está no lead
    
    def remove_tag_from_lead(self, lead_id, tag_id):
        """Remove uma tag de um lead"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute("""
            DELETE FROM lead_tags
            WHERE lead_id = ? AND tag_id = ?
        """, (lead_id, tag_id))
        
        conn.commit()
        conn.close()
        return True
    
    def get_leads_by_tag(self, tag_id):
        """Retorna todos os leads com uma tag específica"""
        conn = sqlite3.connect(self.db_name)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT l.*
            FROM leads l
            JOIN lead_tags lt ON l.id = lt.lead_id
            WHERE lt.tag_id = ?
            ORDER BY lt.added_at DESC
        """, (tag_id,))
        
        leads = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return leads
    
    # =============================
    # SLA TRACKING
    # =============================
    def init_lead_sla(self, lead_id):
        """Inicializa SLA para um novo lead"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        now = datetime.now().isoformat()
        
        cursor.execute("""
            INSERT OR IGNORE INTO lead_sla 
            (lead_id, first_contact_at, status, created_at, updated_at)
            VALUES (?, ?, 'pending', ?, ?)
        """, (lead_id, now, now, now))
        
        conn.commit()
        conn.close()
    
    def record_first_response(self, lead_id):
        """Registra a primeira resposta ao lead"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        now = datetime.now()
        
        # Buscar dados do SLA
        cursor.execute("""
            SELECT first_contact_at, first_response_at
            FROM lead_sla
            WHERE lead_id = ?
        """, (lead_id,))
        
        row = cursor.fetchone()
        
        if row and not row[1]:  # Se ainda não tem primeira resposta
            first_contact = datetime.fromisoformat(row[0])
            response_time = int((now - first_contact).total_seconds())
            
            # Define se SLA foi cumprido (exemplo: 5 minutos)
            sla_met = response_time <= 300
            
            cursor.execute("""
                UPDATE lead_sla
                SET first_response_at = ?,
                    first_response_time_seconds = ?,
                    status = 'responded',
                    sla_met = ?,
                    updated_at = ?
                WHERE lead_id = ?
            """, (now.isoformat(), response_time, sla_met, now.isoformat(), lead_id))
            
            conn.commit()
        
        conn.close()
    
    def update_lead_interaction(self, lead_id, response_time_seconds=None):
        """Atualiza métricas de interação do lead"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        now = datetime.now().isoformat()
        
        if response_time_seconds:
            cursor.execute("""
                UPDATE lead_sla
                SET total_response_time_seconds = total_response_time_seconds + ?,
                    response_count = response_count + 1,
                    avg_response_time_seconds = (total_response_time_seconds + ?) / (response_count + 1),
                    last_interaction_at = ?,
                    updated_at = ?
                WHERE lead_id = ?
            """, (response_time_seconds, response_time_seconds, now, now, lead_id))
        else:
            cursor.execute("""
                UPDATE lead_sla
                SET last_interaction_at = ?,
                    updated_at = ?
                WHERE lead_id = ?
            """, (now, now, lead_id))
        
        conn.commit()
        conn.close()
    
    def get_lead_sla(self, lead_id):
        """Retorna métricas de SLA de um lead"""
        conn = sqlite3.connect(self.db_name)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM lead_sla
            WHERE lead_id = ?
        """, (lead_id,))
        
        sla = cursor.fetchone()
        conn.close()
        
        return dict(sla) if sla else None
    
    def get_sla_metrics(self):
        """Retorna métricas gerais de SLA"""
        conn = sqlite3.connect(self.db_name)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                COUNT(*) as total_leads,
                AVG(first_response_time_seconds) as avg_first_response,
                AVG(avg_response_time_seconds) as avg_overall_response,
                SUM(CASE WHEN sla_met = 1 THEN 1 ELSE 0 END) as sla_met_count,
                SUM(CASE WHEN sla_met = 0 THEN 1 ELSE 0 END) as sla_missed_count,
                MIN(first_response_time_seconds) as fastest_response,
                MAX(first_response_time_seconds) as slowest_response
            FROM lead_sla
            WHERE first_response_at IS NOT NULL
        """)
        
        metrics = dict(cursor.fetchone())
        conn.close()
        
        # Calcular percentual de SLA cumprido
        if metrics['total_leads'] > 0:
            metrics['sla_compliance_rate'] = round(
                (metrics['sla_met_count'] / metrics['total_leads']) * 100, 2
            )
        else:
            metrics['sla_compliance_rate'] = 0
        
        return metrics
    
    def get_leads_with_sla_alert(self, threshold_minutes=5):
        """Retorna leads que estouraram o SLA"""
        conn = sqlite3.connect(self.db_name)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        threshold_seconds = threshold_minutes * 60
        
        cursor.execute("""
            SELECT l.*, s.first_contact_at, s.first_response_time_seconds
            FROM leads l
            JOIN lead_sla s ON l.id = s.lead_id
            WHERE s.status = 'pending'
            AND (
                julianday('now') - julianday(s.first_contact_at)
            ) * 24 * 60 * 60 > ?
            ORDER BY s.first_contact_at ASC
        """, (threshold_seconds,))
        
        leads = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return leads
    
    # =============================
    # UTILITÁRIOS
    # =============================
    def format_response_time(self, seconds):
        """Formata tempo de resposta para leitura humana"""
        if not seconds:
            return "N/A"
        
        if seconds < 60:
            return f"{int(seconds)}s"
        elif seconds < 3600:
            return f"{int(seconds / 60)}min"
        else:
            hours = int(seconds / 3600)
            minutes = int((seconds % 3600) / 60)
            return f"{hours}h {minutes}min"


# =============================
# FUNÇÃO PARA INTEGRAR NO DATABASE.PY
# =============================
def extend_database_with_tags_sla(database_instance):
    """
    Estende uma instância existente do Database com Tags e SLA
    
    Usage:
        db = Database()
        extend_database_with_tags_sla(db)
        # Agora db tem todos os métodos de tags e SLA
    """
    tags_sla = DatabaseTagsSLA(database_instance.db_name)
    
    # Adiciona métodos ao objeto database
    database_instance.get_all_tags = tags_sla.get_all_tags
    database_instance.create_tag = tags_sla.create_tag
    database_instance.get_lead_tags = tags_sla.get_lead_tags
    database_instance.add_tag_to_lead = tags_sla.add_tag_to_lead
    database_instance.remove_tag_from_lead = tags_sla.remove_tag_from_lead
    database_instance.get_leads_by_tag = tags_sla.get_leads_by_tag
    
    database_instance.init_lead_sla = tags_sla.init_lead_sla
    database_instance.record_first_response = tags_sla.record_first_response
    database_instance.update_lead_interaction = tags_sla.update_lead_interaction
    database_instance.get_lead_sla = tags_sla.get_lead_sla
    database_instance.get_sla_metrics = tags_sla.get_sla_metrics
    database_instance.get_leads_with_sla_alert = tags_sla.get_leads_with_sla_alert
    database_instance.format_response_time = tags_sla.format_response_time
    
    print("✅ Database estendido com Tags e SLA!")