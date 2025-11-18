"""
Sistema de Notificações WhatsApp para Gestores
Envia alertas automáticos via WhatsApp quando detecta problemas críticos
"""

from datetime import datetime
from typing import List, Dict, Any
from logger import get_logger, get_audit_logger

logger = get_logger('gestor_notifier')
audit_logger = get_audit_logger()


class GestorWhatsAppNotifier:
    """
    Sistema de notificações automáticas via WhatsApp para gestores
    """
    
    # Emojis para cada tipo de alerta
    ALERT_EMOJIS = {
        'sla_primeira_resposta': '⏰',
        'lead_assumido_sem_resposta': '⚠️',
        'lead_abandonado': '🔴',
        'performance_baixa': '📉',
        'system_alert': '🚨'
    }
    
    # Severidades que disparam notificação WhatsApp
    NOTIFY_SEVERITIES = ['danger', 'critical']
    
    def __init__(self, db, whatsapp_service):
        """
        Args:
            db: Database instance
            whatsapp_service: WhatsAppService instance
        """
        self.db = db
        self.whatsapp = whatsapp_service
        self._create_gestores_config_table()
    
    def _create_gestores_config_table(self):
        """Cria tabela de configuração de gestores"""
        conn = self.db.get_connection()
        c = conn.cursor()
        
        c.execute('''
            CREATE TABLE IF NOT EXISTS gestor_whatsapp_config (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                phone TEXT NOT NULL,
                active BOOLEAN DEFAULT 1,
                receive_critical BOOLEAN DEFAULT 1,
                receive_danger BOOLEAN DEFAULT 1,
                receive_warning BOOLEAN DEFAULT 0,
                quiet_hours_start TEXT DEFAULT '22:00',
                quiet_hours_end TEXT DEFAULT '08:00',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')
        
        c.execute('''
            CREATE INDEX IF NOT EXISTS idx_gestor_config_active 
            ON gestor_whatsapp_config(active)
        ''')
        
        conn.commit()
        conn.close()

        logger.info("Tabela de configuração de gestores criada")
    
    def add_gestor_config(self, user_id: int, phone: str, 
                         receive_critical: bool = True,
                         receive_danger: bool = True,
                         receive_warning: bool = False) -> int:
        """
        Adiciona configuração de notificações para gestor
        """
        conn = self.db.get_connection()
        c = conn.cursor()
        
        # Verificar se já existe
        c.execute('''
            SELECT id FROM gestor_whatsapp_config 
            WHERE user_id = ?
        ''', (user_id,))
        
        existing = c.fetchone()
        
        if existing:
            # Atualizar
            c.execute('''
                UPDATE gestor_whatsapp_config
                SET phone = ?, 
                    receive_critical = ?,
                    receive_danger = ?,
                    receive_warning = ?,
                    active = 1
                WHERE user_id = ?
            ''', (phone, receive_critical, receive_danger, receive_warning, user_id))
            
            config_id = existing['id']
        else:
            # Criar novo
            c.execute('''
                INSERT INTO gestor_whatsapp_config
                (user_id, phone, receive_critical, receive_danger, receive_warning)
                VALUES (?, ?, ?, ?, ?)
            ''', (user_id, phone, receive_critical, receive_danger, receive_warning))
            
            config_id = c.lastrowid
        
        conn.commit()
        conn.close()
        
        return config_id
    
    def get_gestores_to_notify(self, severity: str) -> List[Dict[str, Any]]:
        """Retorna gestores que devem ser notificados baseado na severidade"""
        conn = self.db.get_connection()
        c = conn.cursor()
        
        severity_field = f"receive_{severity}"
        
        query = f'''
            SELECT 
                g.id,
                g.user_id,
                g.phone,
                u.name as gestor_name,
                g.quiet_hours_start,
                g.quiet_hours_end
            FROM gestor_whatsapp_config g
            INNER JOIN users u ON g.user_id = u.id
            WHERE g.active = 1
            AND g.{severity_field} = 1
            AND u.active = 1
            AND u.role IN ('admin', 'gestor')
        '''
        
        c.execute(query)
        gestores = [dict(row) for row in c.fetchall()]
        conn.close()
        
        return [g for g in gestores if not self._is_quiet_hours(g)]
    
    def _is_quiet_hours(self, gestor: Dict) -> bool:
        """Verifica se está em horário silencioso"""
        now = datetime.now().time()
        start = datetime.strptime(gestor['quiet_hours_start'], '%H:%M').time()
        end = datetime.strptime(gestor['quiet_hours_end'], '%H:%M').time()
        
        if start < end:
            return start <= now <= end
        else:
            return now >= start or now <= end
    
    def notify_alert(self, alert: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Envia notificação WhatsApp para gestores sobre um alerta"""
        severity = alert.get('severity')
        
        if severity not in self.NOTIFY_SEVERITIES:
            return []
        
        gestores = self.get_gestores_to_notify(severity)

        if not gestores:
            logger.warning(f"Nenhum gestor configurado para receber alertas", extra={"severity": severity})
            return []
        
        message = self._build_alert_message(alert)
        
        results = []
        for gestor in gestores:
            try:
                success = self.whatsapp.send_message(
                    phone=gestor['phone'],
                    content=message,
                    vendedor_id=gestor['user_id'],
                    bypass_lead_check=True
                )
                
                results.append({
                    'gestor_id': gestor['user_id'],
                    'gestor_name': gestor['gestor_name'],
                    'phone': gestor['phone'],
                    'success': success
                })

                if success:
                    logger.info("Alerta enviado com sucesso", extra={
                        "gestor_name": gestor['gestor_name'],
                        "phone": gestor['phone'],
                        "alert_type": alert.get('alert_type')
                    })
                else:
                    logger.error("Falha ao enviar alerta", extra={
                        "gestor_name": gestor['gestor_name'],
                        "phone": gestor['phone']
                    })
            
            except Exception as e:
                logger.exception("Erro ao notificar gestor", extra={
                    "gestor_name": gestor['gestor_name'],
                    "phone": gestor['phone'],
                    "error": str(e)
                })
                results.append({
                    'gestor_id': gestor['user_id'],
                    'gestor_name': gestor['gestor_name'],
                    'phone': gestor['phone'],
                    'success': False,
                    'error': str(e)
                })
        
        return results
    
    def _build_alert_message(self, alert: Dict[str, Any]) -> str:
        """Constrói mensagem personalizada baseada no tipo de alerta"""
        severity_emoji = {'critical': '🚨', 'danger': '⚠️', 'warning': '⚡'}
        
        alert_type = alert.get('alert_type', 'system_alert')
        emoji = self.ALERT_EMOJIS.get(alert_type, '📢')
        severity = alert.get('severity', 'warning')
        title = alert.get('title', 'Alerta do Sistema')
        message_text = alert.get('message', '')
        data = alert.get('data', {})
        
        lines = [
            f"{severity_emoji[severity]} *ALERTA - CRM WHATSAPP*",
            "",
            f"{emoji} *{title}*",
            "",
            message_text
        ]
        
        if alert_type == 'lead_assumido_sem_resposta':
            lines.extend([
                "",
                f"👤 *Vendedor:* {data.get('vendedor_name', 'N/A')}",
                f"📱 *Lead:* {data.get('lead_name', 'N/A')}",
                f"⏱️ *Tempo sem resposta:* {data.get('minutes_since_assigned', 0)} minutos",
                "",
                f"💡 *Sugestão:* {data.get('action_suggestion', 'Verificar situação')}"
            ])
        
        elif alert_type == 'sla_primeira_resposta':
            lines.extend([
                "",
                f"📱 *Lead:* {data.get('lead_name', 'N/A')}",
                f"📞 *Telefone:* {data.get('lead_phone', 'N/A')}",
                f"👤 *Vendedor:* {data.get('vendedor_name', 'N/A')}",
                f"⏱️ *Aguardando:* {data.get('minutes_waiting', 0)} minutos"
            ])
        
        elif alert_type == 'lead_abandonado':
            lines.extend([
                "",
                f"📱 *Lead:* {data.get('lead_name', 'N/A')}",
                f"👤 *Vendedor:* {data.get('vendedor_name', 'N/A')}",
                f"⏱️ *Sem interação:* {data.get('hours_abandoned', 0)} horas"
            ])
        
        elif alert_type == 'performance_baixa':
            lines.extend([
                "",
                f"👤 *Vendedor:* {data.get('vendedor_name', 'N/A')}",
                f"📊 *Taxa de resposta:* {data.get('taxa_resposta', 0):.1f}%",
                f"📈 *Mínimo esperado:* 80%",
                f"📋 *Total de leads:* {data.get('total_leads', 0)}",
                f"✅ *Respondidos:* {data.get('leads_respondidos', 0)}"
            ])
        
        lines.extend([
            "",
            "─────────────────",
            f"🕐 {datetime.now().strftime('%d/%m/%Y %H:%M')}",
            "💻 Sistema CRM WhatsApp"
        ])
        
        return "\n".join(lines)
    
    def test_notification(self, gestor_id: int) -> bool:
        """Envia mensagem de teste para um gestor"""
        conn = self.db.get_connection()
        c = conn.cursor()
        
        c.execute('''
            SELECT g.phone, u.name
            FROM gestor_whatsapp_config g
            INNER JOIN users u ON g.user_id = u.id
            WHERE g.user_id = ? AND g.active = 1
        ''', (gestor_id,))
        
        result = c.fetchone()
        conn.close()

        if not result:
            logger.warning("Gestor sem WhatsApp configurado", extra={"gestor_id": gestor_id})
            return False
        
        # Converter para dict
        gestor_config = dict(result)
        
        message = f"""✅ *TESTE - CRM WhatsApp*

Olá {gestor_config['name']}!

Este é um teste de notificação automática.

Você está configurado para receber alertas críticos e urgentes do sistema.

🕐 {datetime.now().strftime('%d/%m/%Y %H:%M')}
💻 Sistema CRM WhatsApp"""
        
        success = self.whatsapp.send_message(
            phone=gestor_config['phone'],
            content=message,
            vendedor_id=gestor_id,
            bypass_lead_check=True
        )

        if success:
            audit_logger.info("Mensagem de teste enviada", extra={
                "gestor_id": gestor_id,
                "gestor_name": gestor_config['name'],
                "phone": gestor_config['phone']
            })
        else:
            logger.error("Falha ao enviar mensagem de teste", extra={
                "gestor_id": gestor_id,
                "gestor_name": gestor_config['name']
            })

        return success
    
    def get_config(self, user_id: int) -> Dict[str, Any]:
        """Retorna configuração de um gestor"""
        conn = self.db.get_connection()
        c = conn.cursor()
        c.execute('SELECT * FROM gestor_whatsapp_config WHERE user_id = ?', (user_id,))
        config = c.fetchone()
        conn.close()
        return dict(config) if config else None
    
    def disable_config(self, user_id: int):
        """Desativa notificações para um gestor"""
        conn = self.db.get_connection()
        c = conn.cursor()
        c.execute('UPDATE gestor_whatsapp_config SET active = 0 WHERE user_id = ?', (user_id,))
        conn.commit()
        conn.close()