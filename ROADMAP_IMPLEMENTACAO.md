# 📊 ROADMAP DE IMPLEMENTAÇÃO - PRIORIDADES

## SPRINT 0: Correções Críticas (Semanal 1-2)

### 1. Logging Estruturado (2 dias)

**Status:** 🔴 P0 CRÍTICO

**Tarefas:**
- [ ] Criar módulo `logger.py` com logging configurado
- [ ] Implementar FileHandler com rotação diária
- [ ] Adicionar logging JSON estruturado
- [ ] Substituir todos `print()` por `logger.info/warning/error`
- [ ] Criar endpoint `/api/logs` (apenas admin) para visualizar logs

**Referência:** `/backend/middlewares.py` linha 281

**Exemplo:**
```python
# ANTES
print(f"📝 AUDIT: [{timestamp}] ...")

# DEPOIS
logger.info(
    "user_action",
    extra={
        "user_id": user_id,
        "action": action,
        "entity_type": entity_type,
        "timestamp": datetime.now().isoformat()
    }
)
```

**Arquivos a modificar:**
- [ ] `middlewares.py` - RemoverAuditLogger.log_action()
- [ ] `app.py` - Substituir 100+ print statements
- [ ] Criar `logger.py` novo

---

### 2. Proteção contra Brute Force (1 dia)

**Status:** 🔴 P0 CRÍTICO

**Tarefas:**
- [ ] Adicionar tabela `login_attempts` no banco
- [ ] Implementar contagem de tentativas falhadas
- [ ] Bloquear após 5 tentativas
- [ ] Desbloquear após 15 minutos ou admin manualmente
- [ ] Enviar alerta ao admin

**Código esqueleto:**
```python
# Em database.py
def log_failed_login(self, username):
    # Insere tentativa falhada
    
def get_failed_login_count(self, username):
    # Retorna tentativas dos últimos 15 min
    
def is_account_locked(self, username):
    # Retorna True se locked

# Em app.py login endpoint
if is_account_locked(username):
    return {"error": "Conta bloqueada. Tente novamente em 15 min"}, 429
```

**Arquivos a modificar:**
- [ ] `database.py` - Adicionar métodos acima
- [ ] `app.py` linhas 195-216 (login endpoint)

---

### 3. Validação de Permissão por Recurso (3 dias)

**Status:** 🔴 P0 CRÍTICO

**Tarefas:**
- [ ] Criar decorator `@resource_required(resource_type)`
- [ ] Validar que vendedor só acessa seus leads
- [ ] Validar que vendedor não consegue acessar usuários
- [ ] Adicionar testes de acesso negado

**Problema atual:**
```python
# ❌ INSEGURO - Vendedor A consegue ver lead de Vendedor B
@app.route("/api/leads/<int:lead_id>", methods=["GET"])
def get_lead(lead_id):
    lead = db.get_lead(lead_id)  # SEM VALIDAÇÃO!
    return jsonify(lead)
```

**Solução:**
```python
# ✅ SEGURO - Valida propriedade do lead
def check_lead_access(lead_id, user_id, user_role):
    lead = db.get_lead(lead_id)
    
    # Admin/Gestor veem tudo
    if user_role in ["admin", "gestor"]:
        return True
    
    # Vendedor vê apenas seus leads
    if lead["assigned_to"] == user_id:
        return True
    
    return False

@app.route("/api/leads/<int:lead_id>", methods=["GET"])
@login_required
def get_lead(lead_id):
    if not check_lead_access(lead_id, session["user_id"], session["role"]):
        return {"error": "Acesso negado"}, 403
    lead = db.get_lead(lead_id)
    return jsonify(lead)
```

**Endpoints que precisam correção:**
- [ ] GET `/api/leads/<id>` - Validar propriedade
- [ ] GET `/api/leads/<id>/messages` - Validar propriedade
- [ ] POST `/api/leads/<id>/messages` - Validar propriedade
- [ ] PUT `/api/leads/<id>/status` - Validar propriedade (vendedor não pode mudar)
- [ ] GET `/api/leads/<id>/notes` - Validar propriedade
- [ ] POST `/api/leads/<id>/notes` - Validar propriedade

**Arquivos a modificar:**
- [ ] `app.py` - Adicionar validações em ~15 endpoints
- [ ] Criar `decorators.py` novo com helpers

---

### 4. Fila de Mensagens com Retry (4 dias)

**Status:** 🔴 P0 CRÍTICO

**Tarefas:**
- [ ] Instalar Celery + Redis
- [ ] Criar task `send_whatsapp_message` com retry automático
- [ ] Implementar DLQ (Dead Letter Queue)
- [ ] Substituir código síncrono por async

**Diagrama:**
```
send_message() 
  → Enqueue task (salva status "pending")
    → Worker recebe task
      → Tenta enviar (retry up to 3x)
        → ✅ Sucesso: status "sent"
        → ❌ Falha: status "failed" → DLQ
```

**Setup:**
```bash
# Instalar
pip install celery redis

# Criar tasks.py
from celery import Celery

celery = Celery('crm', broker='redis://localhost:6379')

@celery.task(autoretry_for=(Exception,), retry_kwargs={'max_retries': 3})
def send_whatsapp_message(lead_id, phone, content):
    # Tenta enviar
    success = whatsapp.send_message(phone, content)
    if not success:
        raise Exception("Failed to send")
```

**Modificações:**
- [ ] Criar `tasks.py` com tasks Celery
- [ ] `docker-compose.yml` - Adicionar Redis
- [ ] `app.py` - Trocar `whatsapp.send_message()` por `task.delay()`
- [ ] Criar tabela `message_queue` para tracking
- [ ] Dashboard para visualizar falhas

---

### 5. Encriptação de Dados Sensíveis (3 dias)

**Status:** 🔴 P0 CRÍTICO

**Tarefas:**
- [ ] Implementar encriptação de campos sensíveis
- [ ] Encriptar: `phone`, `email`, `content` (mensagens)
- [ ] Criar migration script
- [ ] Atualizar queries para descriptografar

**Bibliotecas:**
```bash
pip install cryptography
```

**Exemplo:**
```python
from cryptography.fernet import Fernet

class Database:
    def __init__(self):
        key = os.getenv('ENCRYPTION_KEY')
        self.cipher = Fernet(key)
    
    def encrypt_field(self, value):
        return self.cipher.encrypt(value.encode()).decode()
    
    def decrypt_field(self, encrypted_value):
        return self.cipher.decrypt(encrypted_value.encode()).decode()

# Uso:
def add_message(self, lead_id, content):
    encrypted_content = self.encrypt_field(content)
    c.execute("INSERT INTO messages VALUES (...)", 
              (lead_id, encrypted_content, ...))
```

**Arquivos a modificar:**
- [ ] `database.py` - Adicionar encrypt/decrypt
- [ ] `database.py` - Atualizar inserção/leitura
- [ ] Criar migration script

---

### 6. Transações de Banco (1 dia)

**Status:** 🔴 P0 CRÍTICO

**Tarefas:**
- [ ] Adicionar try/except/rollback em operações críticas
- [ ] Implementar context manager para transações

**Exemplo:**
```python
# ❌ ANTES - Sem transação
def assign_lead(self, lead_id, user_id):
    c.execute("UPDATE leads SET assigned_to = ?", (user_id,))
    c.execute("INSERT INTO lead_logs VALUES (...)")
    conn.commit()  # Se falhar no meio, inconsistente!

# ✅ DEPOIS - Com transação
def assign_lead(self, lead_id, user_id):
    conn = self.get_connection()
    try:
        c = conn.cursor()
        c.execute("UPDATE leads SET assigned_to = ?", (user_id,))
        c.execute("INSERT INTO lead_logs VALUES (...)")
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise
    finally:
        conn.close()
```

**Operações críticas:**
- [ ] `assign_lead()`
- [ ] `transfer_lead()`
- [ ] `update_lead_status()`
- [ ] `add_message()` + atualizar lead
- [ ] `create_user()`

---

## SPRINT 1: Segurança & Estabilidade (Semana 3-4)

### 7. Validação de Senha Forte (1 dia)

**Status:** 🟡 P1 ALTO

**Requisitos:**
- Mínimo 12 caracteres
- Pelo menos 1 maiúscula
- Pelo menos 1 número
- Pelo menos 1 símbolo

**Código:**
```python
import re

def validate_password_strength(password):
    if len(password) < 12:
        return False, "Mínimo 12 caracteres"
    if not re.search(r"[A-Z]", password):
        return False, "Requer maiúscula"
    if not re.search(r"[a-z]", password):
        return False, "Requer minúscula"
    if not re.search(r"[0-9]", password):
        return False, "Requer número"
    if not re.search(r"[!@#$%^&*()_+\-=\[\]{};':\"\\|,.<>\/?]", password):
        return False, "Requer símbolo"
    return True, "OK"
```

**Arquivos:**
- [ ] `middlewares.py` - Atualizar `validate_password()`
- [ ] Forçar mudança de senha ao primeiro login

---

### 8. Rate Limiting Distribuído com Redis (2 dias)

**Status:** 🟡 P1 ALTO

**Setup:**
```python
# Em config.py
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(
    app,
    key_func=get_remote_address,
    storage_uri="redis://localhost:6379",
    default_limits=["200 per day", "50 per hour"]
)

# Em app.py
@app.route("/api/login", methods=["POST"])
@limiter.limit("5 per minute")  # Mais restritivo para login
def login():
    ...

@app.route("/api/leads", methods=["GET"])
@limiter.limit("100 per minute")  # Menos restritivo
def get_leads():
    ...
```

**Arquivos:**
- [ ] `requirements.txt` - Adicionar flask-limiter
- [ ] `config.py` - Configurar limiter
- [ ] `app.py` - Substituir rate_limit() por @limiter.limit()
- [ ] `docker-compose.yml` - Redis já precisa estar lá

---

### 9. Circuit Breaker (2 dias)

**Status:** 🟡 P1 ALTO

**Biblioteca:**
```bash
pip install pybreaker
```

**Exemplo:**
```python
from pybreaker import CircuitBreaker

whatsapp_breaker = CircuitBreaker(
    fail_max=5,
    reset_timeout=60,
    listeners=[MyListener()]
)

def send_message_with_breaker(phone, content):
    try:
        return whatsapp_breaker.call(
            whatsapp.send_message, 
            phone, 
            content
        )
    except:
        # Circuit aberto, falha rápido
        logger.error("WhatsApp circuit breaker open")
        return False
```

**Arquivos:**
- [ ] `whatsapp_service.py` - Adicionar circuit breaker
- [ ] `requirements.txt` - pybreaker

---

### 10. Backup Automático com Cron (1 dia)

**Status:** 🟡 P1 ALTO

**Setup:**
```bash
# Tornar script executável
chmod +x /home/user/crmwhatsapp/backup_database.sh

# Adicionar ao crontab (executar todos os dias às 2am)
crontab -e

# Adicionar linha:
0 2 * * * /home/user/crmwhatsapp/backup_database.sh

# Verificar:
crontab -l
```

**Testar:**
```bash
# Rodar manualmente
bash /home/user/crmwhatsapp/backup_database.sh

# Verificar se criou arquivo
ls -la backups/
```

**Melhorias:**
- [ ] Enviar backup para S3/Dropbox
- [ ] Rodar teste de restauração diariamente
- [ ] Manter últimos 30 dias de backups

---

## SPRINT 2: Observabilidade & Funcionalidades (Semana 5-6)

### 11. Alertas Automáticos via Slack (2 dias)

**Status:** 🟡 P1 ALTO

**Setup:**
```python
# Em utils.py
from slack_sdk import WebClient

slack_client = WebClient(token=os.getenv('SLACK_BOT_TOKEN'))

def send_slack_alert(channel, message, severity="warning"):
    color = {"critical": "danger", "warning": "warning", "info": "good"}
    slack_client.chat_postMessage(
        channel=channel,
        blocks=[{
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"⚠️ *{severity.upper()}*\n{message}"
            }
        }]
    )

# Usar em alert_system.py
if alert.severity == "critical":
    send_slack_alert("#alerts", f"SLA crítico: {alert.message}", "critical")
```

**Arquivos:**
- [ ] `requirements.txt` - slack-sdk
- [ ] `.env` - SLACK_BOT_TOKEN
- [ ] `utils.py` - Funções Slack
- [ ] `alert_system.py` - Integrar Slack

---

### 12. Templates de Mensagens (2 dias)

**Status:** 🟡 P1 ALTO

**Schema:**
```python
# Em database.py, adicionar tabela:
CREATE TABLE message_templates (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    content TEXT NOT NULL,
    variables TEXT,  # JSON ["name", "phone"]
    created_by INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
```

**CRUD:**
```python
# Em app.py
@app.route("/api/templates", methods=["GET"])
@role_required("admin", "gestor")
def get_templates():
    return jsonify(db.get_message_templates())

@app.route("/api/templates", methods=["POST"])
@role_required("admin", "gestor")
def create_template():
    data = request.json
    template_id = db.create_message_template(
        name=data["name"],
        content=data["content"],
        variables=data.get("variables", [])
    )
    return {"success": True, "template_id": template_id}

# Usar template
@app.route("/api/leads/<id>/send-template", methods=["POST"])
def send_template(lead_id):
    data = request.json
    template = db.get_template(data["template_id"])
    
    # Substituir variáveis
    content = template["content"]
    for var in template["variables"]:
        content = content.replace(f"{{{var}}}", lead[var])
    
    # Enviar
    send_whatsapp_message.delay(lead_id, lead["phone"], content)
```

**Arquivos:**
- [ ] `database.py` - CRUD de templates
- [ ] `app.py` - Endpoints /templates e /send-template

---

### 13. Automações de Follow-up (4 dias)

**Status:** 🟡 P1 ALTO

**Exemplo: Auto follow-up após 24h sem resposta**

```python
# Em tasks.py (Celery)
@celery.task
def check_and_send_followups():
    # Buscar leads sem resposta há 24h
    leads = db.get_leads_without_response(hours=24)
    
    for lead in leads:
        template = db.get_template("followup_24h")
        send_whatsapp_message.delay(
            lead["id"],
            lead["phone"],
            template["content"]
        )
        db.log_automation(lead["id"], "auto_followup_24h")

# Em app.py, agendar task
from celery.schedules import crontab

app.conf.beat_schedule = {
    'check-followups': {
        'task': 'tasks.check_and_send_followups',
        'schedule': crontab(hour=9, minute=0),  # 9am todo dia
    },
}
```

**Arquivos:**
- [ ] `tasks.py` - Adicionar automações
- [ ] `docker-compose.yml` - Celery Beat
- [ ] `app.py` - Configurar schedule

---

## RESUMO

```
SPRINT 0 (Semana 1-2): P0s
├─ Logging estruturado (2d)
├─ Brute force protection (1d)
├─ Validação de permissão (3d)
├─ Fila de mensagens (4d)
├─ Encriptação (3d)
└─ Transações (1d)

SPRINT 1 (Semana 3-4): P1 Segurança
├─ Senha forte (1d)
├─ Rate limiting Redis (2d)
├─ Circuit breaker (2d)
└─ Backup automático (1d)

SPRINT 2 (Semana 5-6): P1 Observabilidade
├─ Slack alerts (2d)
├─ Templates (2d)
└─ Automações (4d)
```

**Total: 4-6 semanas até estar pronto para produção**

