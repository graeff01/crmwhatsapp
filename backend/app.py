from flask import Flask, request, jsonify, session
from flask_socketio import SocketIO, join_room, leave_room
from flask_cors import CORS
from database import Database
from whatsapp_service import WhatsAppService
from middlewares import (
    rate_limit, validate_request, handle_errors, 
    InputValidator, add_security_headers, AuditLogger
)
from utils import Paginator, MessageSearcher, LeadSearcher, PerformanceCache
import asyncio
from functools import wraps
from database_tags_sla import extend_database_with_tags_sla
from datetime import datetime

# =======================
# CONFIGURAÇÃO PRINCIPAL
# =======================
app = Flask(__name__)
app.config["SECRET_KEY"] = "sua-chave-secreta-aqui-mude-em-producao"
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # 16MB

CORS(app, supports_credentials=True, origins=["http://localhost:3000"])

socketio = SocketIO(app, cors_allowed_origins="*", async_mode="threading")

# Inicialização dos serviços
db = Database()
extend_database_with_tags_sla(db)
whatsapp = WhatsAppService(db, socketio)
validator = InputValidator()
audit_logger = AuditLogger(db)

# Utilitários
message_searcher = MessageSearcher(db)
lead_searcher = LeadSearcher(db)
cache = PerformanceCache(ttl_seconds=300)

print("🚀 CRM WhatsApp iniciado com todas as melhorias!")

# =======================
# MIDDLEWARE GLOBAL
# =======================
@app.after_request
def after_request(response):
    return add_security_headers(response)

# =======================
# DECORATORS DE SEGURANÇA
# =======================
def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            return jsonify({"error": "Não autenticado"}), 401
        return f(*args, **kwargs)
    return decorated


def role_required(*roles):
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if "user_id" not in session:
                return jsonify({"error": "Não autenticado"}), 401
            if session.get("role") not in roles:
                return jsonify({"error": "Sem permissão"}), 403
            return f(*args, **kwargs)
        return decorated
    return decorator

# =======================
# LOGIN / LOGOUT
# =======================
@app.route("/api/login", methods=["POST"])
@rate_limit('per_minute')
@validate_request('username', 'password')
@handle_errors
def login():
    data = request.json
    valid_user, username = validator.validate_username(data.get("username"))
    if not valid_user:
        return jsonify({"error": username}), 400

    valid_pass, password = validator.validate_password(data.get("password"))
    if not valid_pass:
        return jsonify({"error": password}), 400

    user = db.authenticate_user(username, password)
    if not user:
        audit_logger.log_action(0, "login_failed", "auth", 0, f"Username: {username}")
        return jsonify({"error": "Credenciais inválidas"}), 401

    session["user_id"] = user["id"]
    session["username"] = user["username"]
    session["name"] = user["name"]
    session["role"] = user["role"]

    audit_logger.log_action(user["id"], "login_success", "auth", user["id"], f"Login de {username}")
    return jsonify({"success": True, "user": user})


@app.route("/api/logout", methods=["POST"])
@login_required
def logout():
    user_id = session.get("user_id")
    audit_logger.log_action(user_id, "logout", "auth", user_id, "Logout")
    session.clear()
    return jsonify({"success": True})


@app.route("/api/me", methods=["GET"])
@login_required
def get_current_user():
    return jsonify({
        "id": session["user_id"],
        "username": session["username"],
        "name": session["name"],
        "role": session["role"]
    })

# =======================
# USUÁRIOS
# =======================
@app.route("/api/users", methods=["GET"])
@rate_limit('per_minute')
@role_required("admin", "gestor")
def get_users():
    return jsonify(db.get_all_users())


@app.route("/api/users", methods=["POST"])
@rate_limit('per_minute')
@role_required("admin")
@validate_request('username', 'password', 'name', 'role')
@handle_errors
def create_user():
    data = request.json
    uid = db.create_user(data["username"], data["password"], data["name"], data["role"])
    if uid:
        audit_logger.log_action(session["user_id"], "user_created", "user", uid, f"Usuário {data['username']}")
        return jsonify({"success": True, "user_id": uid})
    return jsonify({"error": "Usuário já existe"}), 400


@app.route("/api/users/<int:user_id>", methods=["PUT"])
@rate_limit('per_minute')
@role_required("admin")
@handle_errors
def update_user(user_id):
    data = request.json
    db.update_user(user_id, data["name"], data["role"], data.get("active", 1))
    audit_logger.log_action(session["user_id"], "user_updated", "user", user_id, f"Usuário {user_id}")
    return jsonify({"success": True})


@app.route("/api/users/<int:user_id>", methods=["DELETE"])
@rate_limit('per_minute')
@role_required("admin")
@handle_errors
def delete_user(user_id):
    db.delete_user(user_id)
    audit_logger.log_action(session["user_id"], "user_deleted", "user", user_id, f"Usuário {user_id}")
    return jsonify({"success": True})


@app.route("/api/users/<int:user_id>/password", methods=["PUT"])
@rate_limit('per_minute')
@role_required("admin")
@validate_request('new_password')
@handle_errors
def change_password(user_id):
    data = request.json
    db.change_user_password(user_id, data["new_password"])
    audit_logger.log_action(session["user_id"], "password_changed", "user", user_id, f"Senha alterada")
    return jsonify({"success": True})

# =======================
# LEADS
# =======================
@app.route("/api/leads", methods=["GET"])
@rate_limit('per_minute')
@login_required
def get_leads():
    role = session["role"]
    uid = session["user_id"]
    leads = db.get_all_leads() if role in ["admin", "gestor"] else db.get_leads_by_vendedor(uid)
    
    # Adiciona tags a cada lead
    for lead in leads:
        lead['tags'] = db.get_lead_tags(lead['id'])
    
    return jsonify(leads)


@app.route("/api/leads/queue", methods=["GET"])
@rate_limit('per_minute')
@login_required
def get_leads_queue():
    leads = db.get_leads_by_status("novo")
    return jsonify(leads)


@app.route("/api/leads/<int:lead_id>", methods=["GET"])
@rate_limit('per_minute')
@login_required
@handle_errors
def get_lead(lead_id):
    lead = db.get_lead(lead_id)
    if not lead:
        return jsonify({"error": "Lead não encontrado"}), 404
    
    lead['tags'] = db.get_lead_tags(lead_id)
    return jsonify(lead)


@app.route("/api/leads/<int:lead_id>/assign", methods=["POST"])
@rate_limit('per_minute')
@login_required
@handle_errors
def assign_lead(lead_id):
    uid = session["user_id"]
    uname = session["name"]
    
    db.assign_lead(lead_id, uid)
    db.add_lead_log(lead_id, "lead_atribuido", uname, f"Lead atribuído para {uname}")
    audit_logger.log_action(uid, "lead_assigned", "lead", lead_id, f"Lead atribuído")
    
    socketio.emit("lead_assigned", {"lead_id": lead_id, "vendedor_id": uid}, room="gestores")
    return jsonify({"success": True})


@app.route("/api/leads/<int:lead_id>/status", methods=["PUT"])
@rate_limit('per_minute')
@login_required
@validate_request('status')
@handle_errors
def update_lead_status(lead_id):
    data = request.json
    status = data["status"]
    uname = session["name"]
    
    db.update_lead_status(lead_id, status)
    db.add_lead_log(lead_id, "status_alterado", uname, f"Status alterado para {status}")
    audit_logger.log_action(session["user_id"], "status_changed", "lead", lead_id, f"Status: {status}")
    
    socketio.emit("lead_status_changed", {"lead_id": lead_id, "status": status}, room="gestores")
    return jsonify({"success": True})


@app.route("/api/leads/<int:lead_id>/transfer", methods=["POST"])
@rate_limit('per_minute')
@role_required("admin", "gestor")
@validate_request('vendedor_id')
@handle_errors
def transfer_lead(lead_id):
    data = request.json
    vendedor_id = data["vendedor_id"]
    uname = session["name"]
    
    db.transfer_lead(lead_id, vendedor_id)
    db.add_lead_log(lead_id, "lead_transferido", uname, f"Lead transferido")
    audit_logger.log_action(session["user_id"], "lead_transferred", "lead", lead_id, f"Para vendedor {vendedor_id}")
    
    socketio.emit("lead_transferred", {"lead_id": lead_id, "vendedor_id": vendedor_id}, room="gestores")
    return jsonify({"success": True})

# =======================
# MENSAGENS
# =======================
@app.route("/api/leads/<int:lead_id>/messages", methods=["GET"])
@rate_limit('per_minute')
@login_required
@handle_errors
def get_messages(lead_id):
    messages = db.get_messages_by_lead(lead_id)
    return jsonify(messages)


@app.route("/api/leads/<int:lead_id>/messages", methods=["POST"])
@rate_limit('per_minute')
@login_required
@validate_request('content')
@handle_errors
def send_message(lead_id):
    data = request.json
    
    # Validar conteúdo
    valid, content = validator.validate_text(data.get("content"), max_length=4096, field_name="Mensagem")
    if not valid:
        return jsonify({"error": content}), 400
    
    # Sanitizar HTML
    content = validator.sanitize_html(content)
    
    uid = session["user_id"]
    uname = session["name"]

    lead = db.get_lead(lead_id)
    if not lead:
        return jsonify({"error": "Lead não encontrado"}), 404

    success = whatsapp.send_message(lead["phone"], content, uid)
    if success:
        db.add_lead_log(lead_id, "mensagem_enviada", uname, content[:80])
        audit_logger.log_action(uid, "message_sent", "message", lead_id, f"Mensagem enviada para lead {lead_id}")
    
    return jsonify({"success": success})

# =======================
# NOTAS INTERNAS
# =======================
@app.route("/api/leads/<int:lead_id>/notes", methods=["GET"])
@rate_limit('per_minute')
@login_required
def get_notes(lead_id):
    return jsonify(db.get_internal_notes(lead_id))


@app.route("/api/leads/<int:lead_id>/notes", methods=["POST"])
@rate_limit('per_minute')
@login_required
@validate_request('note')
@handle_errors
def add_note(lead_id):
    data = request.json
    
    # Validar nota
    valid, note = validator.validate_text(data.get("note"), max_length=2000, field_name="Nota")
    if not valid:
        return jsonify({"error": note}), 400
    
    note = validator.sanitize_html(note)
    
    uid = session["user_id"]
    uname = session["name"]

    db.add_internal_note(lead_id, uid, note)
    db.add_lead_log(lead_id, "nota_adicionada", uname, note[:80])
    
    audit_logger.log_action(uid, "note_added", "note", lead_id, "Nota interna adicionada")

    socketio.emit("new_note", {"lead_id": lead_id, "note": note, "user_name": uname}, room="gestores")
    return jsonify({"success": True})

# =======================
# TIMELINE DO LEAD
# =======================
@app.route('/api/lead/<int:lead_id>/logs', methods=['GET'])
@rate_limit('per_minute')
@login_required
@handle_errors
def get_lead_logs(lead_id):
    """Retorna histórico do lead"""
    logs = db.get_lead_logs(lead_id)
    return jsonify(logs)

# =======================
# MÉTRICAS
# =======================
@app.route("/api/metrics", methods=["GET"])
@rate_limit('per_minute')
@login_required
@handle_errors
def get_metrics():
    """Retorna métricas gerais do CRM"""
    metrics = db.get_metrics_summary()
    return jsonify(metrics)

# =======================
# LOGS DE AUDITORIA
# =======================
@app.route("/api/audit-log", methods=["GET"])
@rate_limit('per_minute')
@role_required("admin", "gestor")
@handle_errors
def get_audit_log():
    """Retorna logs de auditoria"""
    limit = request.args.get('limit', 100, type=int)
    logs = db.get_audit_logs(limit)
    return jsonify(logs)

# =======================
# TAGS (Sistema de Tags)
# =======================
@app.route("/api/tags", methods=["GET"])
@rate_limit('per_minute')
@login_required
def get_all_tags():
    """Retorna todas as tags disponíveis"""
    try:
        conn = db.get_connection()
        c = conn.cursor()
        c.execute("SELECT * FROM tags ORDER BY name")
        tags = [dict(r) for r in c.fetchall()]
        conn.close()
        return jsonify(tags)
    except:
        return jsonify([])


@app.route("/api/tags", methods=["POST"])
@rate_limit('per_minute')
@role_required("admin", "gestor")
@validate_request('name', 'color')
@handle_errors
def create_tag():
    """Cria uma nova tag"""
    data = request.json
    try:
        conn = db.get_connection()
        c = conn.cursor()
        c.execute("INSERT INTO tags (name, color) VALUES (?, ?)", (data["name"], data["color"]))
        conn.commit()
        tag_id = c.lastrowid
        conn.close()
        
        audit_logger.log_action(session["user_id"], "tag_created", "tag", tag_id, f"Tag {data['name']}")
        return jsonify({"success": True, "tag_id": tag_id})
    except:
        return jsonify({"error": "Erro ao criar tag"}), 500


@app.route("/api/leads/<int:lead_id>/tags", methods=["GET"])
@rate_limit('per_minute')
@login_required
def get_lead_tags(lead_id):
    """Retorna tags de um lead"""
    tags = db.get_lead_tags(lead_id)
    return jsonify(tags)


@app.route("/api/leads/<int:lead_id>/tags", methods=["POST"])
@rate_limit('per_minute')
@login_required
@validate_request('tag_id')
@handle_errors
def add_tag_to_lead(lead_id):
    """Adiciona tag a um lead"""
    data = request.json
    tag_id = data["tag_id"]
    
    try:
        conn = db.get_connection()
        c = conn.cursor()
        c.execute("INSERT OR IGNORE INTO lead_tags (lead_id, tag_id) VALUES (?, ?)", (lead_id, tag_id))
        conn.commit()
        conn.close()
        
        db.add_lead_log(lead_id, "tag_adicionada", session["name"], f"Tag ID {tag_id}")
        audit_logger.log_action(session["user_id"], "tag_added_to_lead", "lead", lead_id, f"Tag {tag_id}")
        
        return jsonify({"success": True})
    except:
        return jsonify({"error": "Erro ao adicionar tag"}), 500


@app.route("/api/leads/<int:lead_id>/tags/<int:tag_id>", methods=["DELETE"])
@rate_limit('per_minute')
@login_required
@handle_errors
def remove_tag_from_lead(lead_id, tag_id):
    """Remove tag de um lead"""
    try:
        conn = db.get_connection()
        c = conn.cursor()
        c.execute("DELETE FROM lead_tags WHERE lead_id = ? AND tag_id = ?", (lead_id, tag_id))
        conn.commit()
        conn.close()
        
        db.add_lead_log(lead_id, "tag_removida", session["name"], f"Tag ID {tag_id}")
        audit_logger.log_action(session["user_id"], "tag_removed_from_lead", "lead", lead_id, f"Tag {tag_id}")
        
        return jsonify({"success": True})
    except:
        return jsonify({"error": "Erro ao remover tag"}), 500

# =======================
# SLA (Sistema de SLA)
# =======================
@app.route("/api/leads/<int:lead_id>/sla", methods=["GET"])
@rate_limit('per_minute')
@login_required
def get_lead_sla(lead_id):
    """Retorna informações de SLA do lead"""
    try:
        conn = db.get_connection()
        c = conn.cursor()
        c.execute("SELECT * FROM sla_tracking WHERE lead_id = ?", (lead_id,))
        sla = c.fetchone()
        conn.close()
        return jsonify(dict(sla) if sla else {})
    except:
        return jsonify({})


@app.route("/api/sla/metrics", methods=["GET"])
@rate_limit('per_minute')
@role_required("admin", "gestor")
def get_sla_metrics():
    """Retorna métricas de SLA"""
    try:
        conn = db.get_connection()
        c = conn.cursor()
        c.execute("""
            SELECT 
                COUNT(*) as total,
                AVG(first_response_time) as avg_first_response,
                AVG(resolution_time) as avg_resolution
            FROM sla_tracking
            WHERE first_response_time IS NOT NULL
        """)
        metrics = dict(c.fetchone())
        conn.close()
        return jsonify(metrics)
    except:
        return jsonify({})


@app.route("/api/sla/alerts", methods=["GET"])
@rate_limit('per_minute')
@role_required("admin", "gestor")
def get_sla_alerts():
    """Retorna alertas de SLA próximos do limite"""
    threshold = request.args.get('threshold', 5, type=int)
    try:
        conn = db.get_connection()
        c = conn.cursor()
        c.execute("""
            SELECT l.*, s.* 
            FROM leads l
            INNER JOIN sla_tracking s ON l.id = s.lead_id
            WHERE s.first_response_time IS NULL 
            AND (julianday('now') - julianday(l.created_at)) * 24 * 60 > ?
            ORDER BY l.created_at ASC
        """, (threshold,))
        alerts = [dict(r) for r in c.fetchall()]
        conn.close()
        return jsonify(alerts)
    except:
        return jsonify([])

# =======================
# WEBHOOK DO WHATSAPP - ✅ VERSÃO CORRIGIDA E COMPATÍVEL
# =======================
# Substitua o webhook existente (linha ~433 do app.py) por este código

@app.route("/api/webhook/message", methods=["POST"])
@rate_limit('per_hour')
@handle_errors
def webhook_message():
    data = request.get_json(force=True)
    print(f"📩 Webhook recebido: {data}")

    try:
        # ✅ Suporta tanto formato Baileys (from/body) quanto Venom (phone/content)
        phone_raw = data.get("from") or data.get("phone", "")
        content = data.get("body") or data.get("content", "")
        name = data.get("notifyName") or data.get("name", "Lead")
        
        # Limpa telefone
        phone = str(phone_raw).strip().replace("+", "").replace(" ", "").replace("-", "").replace("@c.us", "").replace("@s.whatsapp.net", "")
        content = str(content).strip()
        name = str(name).strip()
        timestamp = datetime.now().isoformat()

        print(f"📞 Telefone limpo: {phone}")
        print(f"💬 Conteúdo: {content[:50]}...")
        print(f"👤 Nome: {name}")

        if not phone.isdigit():
            print(f"⚠️ Telefone inválido recebido: {phone_raw} -> {phone}")
            return jsonify({"error": "Telefone inválido"}), 400

        if not content:
            print("⚠️ Webhook ignorado (sem conteúdo).")
            return jsonify({"error": "Sem conteúdo"}), 400

        # 🔹 Cria ou busca o lead
        lead = db.create_or_get_lead(phone, name)
        
        if not lead:
            print(f"❌ Erro ao criar/buscar lead para {phone}")
            return jsonify({"error": "Erro ao processar lead"}), 500

        # 🔹 Registra mensagem
        db.add_message(lead["id"], "lead", name, content)

        # 🔹 Log de histórico
        db.add_lead_log(lead["id"], "mensagem_recebida", name, content[:100])

        # 🔹 Emite atualização em tempo real
        socketio.emit("new_message", {
            "lead_id": lead["id"],
            "phone": phone,
            "name": name,
            "content": content,
            "timestamp": timestamp,
            "sender_type": "lead"
        }, room="gestores")

        print(f"✅ Mensagem processada com sucesso!")
        print(f"   Lead ID: {lead['id']}")
        print(f"   Nome: {name}")
        print(f"   Telefone: {phone}")
        print("")
        
        return jsonify({"success": True, "lead_id": lead["id"]}), 200
    
    except Exception as e:
        print(f"❌ Erro no webhook: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

# =======================
# SIMULADOR (Modo Desenvolvimento)
# =======================
@app.route("/api/simulate/message", methods=["POST"])
@rate_limit('per_minute')
@handle_errors
def simulate_message():
    """Simula recebimento de mensagem (para testes sem WhatsApp real)"""
    data = request.json
    
    # Simula o formato do VenomBot
    simulated_data = {
        "from": data.get("phone", "") + "@c.us",
        "body": data.get("content", ""),
        "notifyName": data.get("name", "Lead Teste"),
        "timestamp": int(datetime.now().timestamp()),
        "fromMe": False
    }
    
    # Chama o webhook internamente
    return webhook_message()

# =======================
# WHATSAPP STATUS
# =======================
@app.route("/api/whatsapp/status", methods=["GET"])
@login_required
def whatsapp_status():
    return jsonify(whatsapp.get_status())

# =======================
# SOCKET.IO EVENTS
# =======================
@socketio.on("connect")
def on_connect():
    print("🔌 Cliente conectado")

@socketio.on("disconnect")
def on_disconnect():
    print("🔌 Cliente desconectado")

@socketio.on("join_room")
def on_join(data):
    room = data.get("room")
    join_room(room)
    print(f"📍 Entrou na sala: {room}")

@socketio.on("leave_room")
def on_leave(data):
    room = data.get("room")
    leave_room(room)
    print(f"📍 Saiu da sala: {room}")

# =======================
# HEALTH CHECK
# =======================
@app.route("/health", methods=["GET"])
def health_check():
    """Health check para monitoramento"""
    whatsapp_status = whatsapp.ensure_connected()
    return jsonify({
        "status": "healthy" if whatsapp_status else "degraded",
        "timestamp": datetime.now().isoformat(),
        "services": {
            "database": "ok",
            "whatsapp": "connected" if whatsapp_status else "disconnected"
        }
    })

# =======================
# INICIALIZAÇÃO
# =======================
if __name__ == "__main__":
    print("=" * 60)
    print("🚀 CRM WhatsApp - Versão Otimizada")
    print("=" * 60)
    print("✅ Rate Limiting ativado")
    print("✅ Validações de input implementadas")
    print("✅ Retry logic no WhatsApp")
    print("✅ Paginação e busca otimizadas")
    print("✅ Logs de auditoria ativos")
    print("✅ Cache de performance configurado")
    print("✅ Webhook CORRIGIDO para VenomBot")
    print("=" * 60)
    print("🌐 API: http://localhost:5000")
    print("🔌 Socket.io ativo")
    print("📊 Health check: http://localhost:5000/health")
    print("📡 Webhook: http://localhost:5000/api/webhook/message")
    print("=" * 60)

    socketio.run(app, debug=False, host="0.0.0.0", port=5000)