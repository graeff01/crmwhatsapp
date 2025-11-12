"""
Serviço de Monitoramento de Alertas
Executa verificações periódicas e notifica gestores
"""

import threading
import time
from datetime import datetime
from alert_system import AlertSystem
from gestor_whatsapp_notifier import GestorWhatsAppNotifier


class AlertMonitoringService:
    """
    Serviço que roda em background verificando alertas
    """
    
    def __init__(self, db, socketio, notification_service, whatsapp_service, check_interval=300):
        """
        Args:
            db: Database instance
            socketio: SocketIO instance
            notification_service: NotificationService instance
            whatsapp_service: WhatsAppService instance
            check_interval: Intervalo entre verificações em segundos (padrão: 5 min)
        """
        self.db = db
        self.socketio = socketio
        self.notification_service = notification_service
        self.alert_system = AlertSystem(db)
        self.whatsapp_notifier = GestorWhatsAppNotifier(db, whatsapp_service)
        self.check_interval = check_interval
        self.running = False
        self.thread = None
        
        print("🚨 Serviço de Alertas inicializado")
        print("📱 Notificações WhatsApp para gestores ativadas")
    
    def start(self):
        """Inicia o serviço de monitoramento"""
        if self.running:
            return
        
        self.running = True
        self.thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.thread.start()
        print(f"🚨 Monitoramento de alertas iniciado (intervalo: {self.check_interval}s)")
    
    def stop(self):
        """Para o serviço de monitoramento"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)
        print("🚨 Monitoramento de alertas parado")
    
    def _monitor_loop(self):
        """Loop principal de monitoramento"""
        while self.running:
            try:
                self._check_and_notify()
            except Exception as e:
                print(f"❌ Erro no monitoramento de alertas: {e}")
            
            # Aguarda intervalo
            time.sleep(self.check_interval)
    
    def _check_and_notify(self):
        """Verifica alertas e notifica"""
        # Executar verificação de todos os alertas
        new_alerts = self.alert_system.check_all_alerts()
        
        if not new_alerts:
            return
        
        # Filtrar alertas None (duplicados)
        new_alerts = [a for a in new_alerts if a is not None]
        
        if not new_alerts:
            return
        
        print(f"🚨 {len(new_alerts)} novos alertas detectados")
        
        # Notificar gestores sobre alertas críticos e danger
        critical_alerts = [a for a in new_alerts if a['severity'] in ['critical', 'danger']]
        
        for alert in critical_alerts:
            self._send_alert_notification(alert)
        
        # Emitir alertas via Socket.IO para dashboard
        self.socketio.emit('system_alerts', {
            'alerts': new_alerts,
            'stats': self.alert_system.get_alert_stats()
        }, room='gestores')
    
    def _send_alert_notification(self, alert: dict):
        """Envia notificação de alerta"""
        # Determinar emoji por severidade
        emoji_map = {
            'critical': '🚨',
            'danger': '⚠️',
            'warning': '⚡'
        }
        
        emoji = emoji_map.get(alert['severity'], '📢')
        
        # Enviar notificação personalizada via Socket.IO
        self.notification_service.notify_custom(
            title=f"{emoji} {alert['title']}",
            message=alert['message'],
            notification_type='system_alert',
            priority='urgent' if alert['severity'] == 'critical' else 'high',
            data={
                'alert_id': alert['id'],
                'alert_type': alert['alert_type'],
                'severity': alert['severity'],
                **alert['data']
            },
            room='gestores'
        )
        
        # 📱 ENVIAR WHATSAPP PARA GESTORES
        if alert['severity'] in ['critical', 'danger']:
            try:
                results = self.whatsapp_notifier.notify_alert(alert)
                
                if results:
                    success_count = sum(1 for r in results if r.get('success'))
                    print(f"📱 WhatsApp enviado para {success_count}/{len(results)} gestores")
            except Exception as e:
                print(f"❌ Erro ao enviar WhatsApp: {e}")
    
    def get_dashboard_data(self) -> dict:
        """
        Retorna dados para o dashboard de alertas
        """
        stats = self.alert_system.get_alert_stats()
        active_alerts = self.alert_system.get_active_alerts()
        
        # Agrupar por vendedor
        alerts_by_vendedor = {}
        for alert in active_alerts:
            vid = alert.get('vendedor_id')
            if vid:
                if vid not in alerts_by_vendedor:
                    alerts_by_vendedor[vid] = []
                alerts_by_vendedor[vid].append(alert)
        
        return {
            'stats': stats,
            'active_alerts': active_alerts[:20],  # Top 20
            'alerts_by_vendedor': alerts_by_vendedor,
            'last_check': datetime.now().isoformat()
        }


def check_alerts_once(db, socketio, notification_service, whatsapp_service):
    """
    Executa verificação única de alertas (útil para testes)
    """
    alert_system = AlertSystem(db)
    whatsapp_notifier = GestorWhatsAppNotifier(db, whatsapp_service)
    
    new_alerts = alert_system.check_all_alerts()
    
    # Filtrar None
    new_alerts = [a for a in new_alerts if a is not None]
    
    if new_alerts:
        print(f"🚨 {len(new_alerts)} alertas encontrados")
        
        # Notificar via Socket.IO
        socketio.emit('system_alerts', {
            'alerts': new_alerts,
            'stats': alert_system.get_alert_stats()
        }, room='gestores')
        
        # 📱 Enviar WhatsApp para alertas críticos/urgentes
        critical_alerts = [a for a in new_alerts if a['severity'] in ['critical', 'danger']]
        
        for alert in critical_alerts:
            try:
                whatsapp_notifier.notify_alert(alert)
            except Exception as e:
                print(f"❌ Erro ao enviar WhatsApp: {e}")
        
        return new_alerts
    
    print("✅ Nenhum alerta detectado")
    return []