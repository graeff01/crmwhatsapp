"""
Blueprint de Configurações de Gestores
Gerencia notificações WhatsApp e configurações de alertas para gestores
"""
from flask import Blueprint, request, jsonify, session
from auth_decorators import login_required, requires_role
from middlewares import rate_limit, validate_request, handle_errors
from logger import get_logger, audit_logger

gestor_bp = Blueprint('gestor', __name__, url_prefix='/api/gestores')
logger = get_logger('gestor')

# Será injetado pelo app.py
_db = None
_whatsapp = None
_notifier = None

def init_gestor_routes(db, whatsapp, notifier):
    """Inicializa dependências do blueprint"""
    global _db, _whatsapp, _notifier
    _db = db
    _whatsapp = whatsapp
    _notifier = notifier
    logger.info("Blueprint de Gestores inicializado")


@gestor_bp.route("/whatsapp-config", methods=["GET"])
@login_required
@rate_limit('per_minute')
@requires_role("admin", "gestor")
@handle_errors
def get_whatsapp_config():
    """Retorna configuração de WhatsApp do gestor"""
    user_id = session["user_id"]

    logger.info(f"Buscando config WhatsApp", extra={"user_id": user_id})

    config = _notifier.get_config(user_id)

    return jsonify({
        "success": True,
        "config": config if config else None
    })


@gestor_bp.route("/whatsapp-config", methods=["POST"])
@login_required
@rate_limit('per_minute')
@requires_role("admin", "gestor")
@validate_request('phone')
@handle_errors
def set_whatsapp_config():
    """Configura WhatsApp para receber alertas"""
    data = request.json
    user_id = session["user_id"]
    phone = data["phone"]

    # Validar formato do telefone
    if not phone.startswith("55"):
        logger.warning("Telefone sem código do país", extra={"user_id": user_id, "phone": phone})
        return jsonify({
            "success": False,
            "error": "Telefone deve iniciar com 55 (código do Brasil)"
        }), 400

    if len(phone) < 12 or len(phone) > 13:
        logger.warning("Telefone com formato inválido", extra={"user_id": user_id, "phone": phone})
        return jsonify({
            "success": False,
            "error": "Formato inválido. Use: 5511999999999"
        }), 400

    logger.info("Configurando WhatsApp para gestor", extra={
        "user_id": user_id,
        "phone": phone,
        "receive_critical": data.get("receive_critical", True),
        "receive_danger": data.get("receive_danger", True),
        "receive_warning": data.get("receive_warning", False)
    })

    config_id = _notifier.add_gestor_config(
        user_id=user_id,
        phone=phone,
        receive_critical=data.get("receive_critical", True),
        receive_danger=data.get("receive_danger", True),
        receive_warning=data.get("receive_warning", False)
    )

    audit_logger.info("Configuração de notificações WhatsApp salva", extra={
        "user_id": user_id,
        "config_id": config_id,
        "phone": phone
    })

    return jsonify({
        "success": True,
        "message": "Configuração salva com sucesso!",
        "config_id": config_id
    })


@gestor_bp.route("/whatsapp-config/test", methods=["POST"])
@login_required
@rate_limit('per_minute')
@requires_role("admin", "gestor")
@handle_errors
def test_whatsapp():
    """Envia mensagem de teste para o gestor"""
    user_id = session["user_id"]

    logger.info("Enviando mensagem de teste", extra={"user_id": user_id})

    success = _notifier.test_notification(user_id)

    if success:
        audit_logger.info("Teste de notificação enviado com sucesso", extra={"user_id": user_id})
        return jsonify({
            "success": True,
            "message": "Mensagem de teste enviada! Verifique seu WhatsApp."
        })
    else:
        logger.error("Falha ao enviar teste de notificação", extra={"user_id": user_id})
        return jsonify({
            "success": False,
            "error": "Falha ao enviar mensagem. Verifique se o número está correto e o WhatsApp conectado."
        }), 500


@gestor_bp.route("/whatsapp-config", methods=["DELETE"])
@login_required
@rate_limit('per_minute')
@requires_role("admin", "gestor")
@handle_errors
def disable_whatsapp():
    """Desativa notificações WhatsApp"""
    user_id = session["user_id"]

    logger.info("Desativando notificações WhatsApp", extra={"user_id": user_id})

    _notifier.disable_config(user_id)

    audit_logger.info("Notificações WhatsApp desativadas", extra={"user_id": user_id})

    return jsonify({
        "success": True,
        "message": "Notificações WhatsApp desativadas"
    })


@gestor_bp.route("/stats", methods=["GET"])
@login_required
@requires_role("admin", "gestor")
@handle_errors
def get_gestor_stats():
    """Retorna estatísticas gerais para gestores"""
    user_id = session["user_id"]

    logger.info("Buscando estatísticas de gestor", extra={"user_id": user_id})

    conn = _db.get_connection()
    c = conn.cursor()

    # Total de vendedores
    c.execute("SELECT COUNT(*) as total FROM users WHERE role = 'vendedor' AND active = 1")
    total_vendedores = c.fetchone()['total']

    # Total de leads
    c.execute("SELECT COUNT(*) as total FROM leads")
    total_leads = c.fetchone()['total']

    # Leads ativos (não finalizados)
    c.execute("SELECT COUNT(*) as total FROM leads WHERE status NOT IN ('finalizado', 'perdido')")
    leads_ativos = c.fetchone()['total']

    # Taxa de conversão geral
    c.execute("SELECT COUNT(*) as total FROM leads WHERE status = 'finalizado'")
    leads_finalizados = c.fetchone()['total']

    taxa_conversao = (leads_finalizados / total_leads * 100) if total_leads > 0 else 0

    conn.close()

    return jsonify({
        "success": True,
        "stats": {
            "total_vendedores": total_vendedores,
            "total_leads": total_leads,
            "leads_ativos": leads_ativos,
            "leads_finalizados": leads_finalizados,
            "taxa_conversao": round(taxa_conversao, 2)
        }
    })


__all__ = ['gestor_bp', 'init_gestor_routes']
