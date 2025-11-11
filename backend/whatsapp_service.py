import requests
from datetime import datetime
import time
from functools import wraps

class WhatsAppService:
    def __init__(self, database, socketio):
        self.db = database
        self.socketio = socketio
        self.venom_url = "http://localhost:3001"
        self.is_ready = False
        self.max_retries = 3
        self.retry_delay = 2  # segundos
        self.last_health_check = None
        self.health_check_interval = 30  # segundos
        self.connection_errors = 0
        self.max_connection_errors = 5

    # =============================
    # UTILITÁRIOS
    # =============================
    def validate_phone(self, phone):
        """Valida e normaliza número de telefone"""
        if not phone:
            return None
        
        # Remove caracteres não numéricos
        phone_clean = ''.join(filter(str.isdigit, str(phone)))
        
        # Valida comprimento mínimo
        if len(phone_clean) < 10:
            print(f"⚠️ Telefone inválido (muito curto): {phone}")
            return None
        
        # Valida comprimento máximo
        if len(phone_clean) > 15:
            print(f"⚠️ Telefone inválido (muito longo): {phone}")
            return None
        
        return phone_clean

    # =============================
    # STATUS DE CONEXÃO E HEALTH CHECK
    # =============================
    def check_connection(self):
        """Verifica se VenomBot está conectado - COM RETRY"""
        max_attempts = 2
        delay = 1
        
        for attempt in range(max_attempts):
            try:
                response = requests.get(f"{self.venom_url}/status", timeout=5)
                if response.status_code == 200:
                    data = response.json()
                    self.is_ready = data.get("connected", False)
                    self.last_health_check = datetime.now()
                    self.connection_errors = 0  # Reset contador de erros
                    
                    if self.is_ready:
                        print(f"✅ WhatsApp conectado: {data.get('phone', 'N/A')}")
                    else:
                        print(f"⚠️ WhatsApp não conectado")
                    
                    return data
                return {"connected": False}
                
            except requests.exceptions.RequestException as e:
                if attempt < max_attempts - 1:
                    print(f"⚠️ Tentativa {attempt + 1}/{max_attempts} falhou. Tentando novamente em {delay}s...")
                    time.sleep(delay)
                else:
                    print(f"❌ Erro ao verificar conexão com VenomBot: {e}")
                    self.is_ready = False
                    self.last_health_check = datetime.now()
                    self.connection_errors += 1
                    
                    if self.connection_errors >= self.max_connection_errors:
                        print(f"🚨 ALERTA: {self.connection_errors} erros consecutivos de conexão!")
                    
                    return {"connected": False}
    
    def should_check_health(self):
        """Verifica se deve fazer health check"""
        if self.last_health_check is None:
            return True
        elapsed = (datetime.now() - self.last_health_check).total_seconds()
        return elapsed >= self.health_check_interval
    
    def ensure_connected(self):
        """Garante que está conectado antes de operações críticas"""
        if self.should_check_health():
            self.check_connection()
        
        if not self.is_ready:
            print("⚠️ WhatsApp não está conectado. Tentando reconectar...")
            self.check_connection()
        
        return self.is_ready

    # =============================
    # RECEBER MENSAGEM DO LEAD
    # =============================
    async def on_message(self, message):
        """
        Callback chamado pelo VenomBot (via webhook)
        Quando um lead envia mensagem para o número da empresa
        """
        try:
            phone = message.get("from", "").replace("@c.us", "").replace("+", "").strip()
            content = message.get("body", "").strip()
            sender_name = message.get("notifyName", message.get("pushName", "Lead"))

            # Ignora mensagens enviadas pela própria empresa
            if message.get("fromMe"):
                return

            # Valida telefone
            phone = self.validate_phone(phone)
            if not phone:
                print(f"❌ Telefone inválido rejeitado")
                return

            # Valida conteúdo
            if not content or len(content) > 4096:
                print(f"⚠️ Mensagem inválida (vazia ou muito grande)")
                return

            print(f"📨 Mensagem recebida de {sender_name} ({phone}): {content[:50]}...")

            # Cria ou busca o lead no banco
            lead = self.db.create_or_get_lead(phone, sender_name)

            

            # Salva a mensagem recebida
            self.db.add_message(
                lead_id=lead["id"],
                sender_type="lead",
                sender_name=sender_name,
                content=content
            )

            # Adiciona log na timeline do lead
            self.db.add_lead_log(
                lead_id=lead["id"],
                action="mensagem_recebida",
                user_name=sender_name,
                details=content[:100]
            )

            # Emite atualização em tempo real pro front-end
            self.socketio.emit("new_message", {
                "lead_id": lead["id"],
                "phone": phone,
                "name": sender_name,
                "content": content,
                "timestamp": datetime.now().isoformat(),
                "sender_type": "lead"
            })

            print("✅ Mensagem recebida e registrada com sucesso")

        except Exception as e:
            print(f"❌ Erro ao processar mensagem recebida: {e}")
            import traceback
            traceback.print_exc()

    # =============================
    # ENVIAR MENSAGEM PARA O LEAD
    # =============================
    def send_message(self, phone, content, vendedor_id=None):
        """Envia mensagem para o lead via VenomBot com retry"""
        
        # Validações
        phone = self.validate_phone(phone)
        if not phone:
            print(f"❌ Telefone inválido: {phone}")
            return False
        
        if not content or not content.strip():
            print(f"❌ Mensagem vazia não pode ser enviada")
            return False
        
        if len(content) > 4096:
            print(f"❌ Mensagem muito grande (max 4096 caracteres)")
            return False
        
        # Verifica conexão
        if not self.ensure_connected():
            print(f"❌ WhatsApp não conectado. Não é possível enviar mensagem.")
            return False
        
        # Tenta enviar com retry
        for attempt in range(self.max_retries):
            try:
                print(f"📤 Enviando mensagem para {phone} (tentativa {attempt + 1}/{self.max_retries})")
                
                response = requests.post(
                    f"{self.venom_url}/send",
                    json={"phone": phone, "message": content},
                    timeout=10
                )

                if response.status_code != 200:
                    print(f"❌ Erro HTTP {response.status_code}: {response.text}")
                    if attempt < self.max_retries - 1:
                        time.sleep(self.retry_delay)
                        continue
                    return False

                lead = self.db.get_lead_by_phone(phone)
                if not lead:
                    print(f"⚠️ Nenhum lead encontrado com o número {phone}. Mensagem não será enviada.")
                    return False


                # Busca nome do vendedor
                vendedor_name = "Vendedor"
                if vendedor_id:
                    users = self.db.get_all_users()
                    user = next((u for u in users if u["id"] == vendedor_id), None)
                    if user:
                        vendedor_name = user["name"]

                # Salva mensagem enviada
                self.db.add_message(
                    lead_id=lead["id"],
                    sender_type="vendedor",
                    sender_name=vendedor_name,
                    content=content
                )

                # Adiciona log de envio
                self.db.add_lead_log(
                    lead_id=lead["id"],
                    action="mensagem_enviada",
                    user_name=vendedor_name,
                    details=content[:100]
                )

                # Notifica o front em tempo real
                self.socketio.emit("message_sent", {
                    "lead_id": lead["id"],
                    "phone": phone,
                    "content": content,
                    "timestamp": datetime.now().isoformat(),
                    "sender_type": "vendedor",
                    "sender_id": vendedor_id
                })

                print("✅ Mensagem enviada e salva com sucesso")

                

                return True

            except requests.exceptions.Timeout:
                print(f"⏱️ Timeout na tentativa {attempt + 1}/{self.max_retries}")
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay)
                else:
                    print("❌ Timeout: VenomBot não responde.")
                    return False
                    
            except requests.exceptions.ConnectionError:
                print(f"🔌 Erro de conexão na tentativa {attempt + 1}/{self.max_retries}")
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay)
                else:
                    print("❌ VenomBot offline ou inacessível")
                    return False
                    
            except Exception as e:
                print(f"❌ Erro inesperado ao enviar mensagem: {e}")
                import traceback
                traceback.print_exc()
                return False
        
        return False

    # =============================
    # STATUS E DESCONECTAR
    # =============================
    def get_status(self):
        """Retorna status atual do VenomBot com informações detalhadas"""
        status = self.check_connection()
        
        return {
            "connected": status.get("connected", False),
            "phone": status.get("phone", "Não conectado"),
            "venom_url": self.venom_url,
            "is_ready": self.is_ready,
            "last_health_check": self.last_health_check.isoformat() if self.last_health_check else None,
            "connection_errors": self.connection_errors,
            "health_status": "healthy" if self.connection_errors == 0 else "degraded" if self.connection_errors < 3 else "critical"
        }

    def disconnect(self):
        """Força desconexão manual do VenomBot"""
        try:
            response = requests.post(f"{self.venom_url}/disconnect", timeout=5)
            if response.status_code == 200:
                print("🔌 Desconectado do WhatsApp com sucesso")
                self.is_ready = False
                return {"success": True}
            return {"success": False, "error": response.text}
        except Exception as e:
            print(f"❌ Erro ao desconectar: {e}")
            return {"success": False, "error": str(e)}