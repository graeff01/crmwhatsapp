"""
Blueprint de IA Dashboard
Rotas para monitoramento e gestão do sistema de qualificação por IA
"""
from flask import Blueprint, request, jsonify, session
from auth_decorators import login_required, role_required
from middlewares import rate_limit, handle_errors
from logger import get_logger, get_audit_logger
from datetime import datetime, timedelta

ai_dashboard_bp = Blueprint('ai_dashboard', __name__, url_prefix='/api/ai')
logger = get_logger('ai_dashboard')
audit_logger = get_audit_logger()

# Será injetado pelo app.py
_db = None
_ai_engine = None

def init_ai_dashboard_routes(db, ai_engine=None):
    """Inicializa dependências do blueprint"""
    global _db, _ai_engine
    _db = db
    _ai_engine = ai_engine
    logger.info("Blueprint de IA Dashboard inicializado")


@ai_dashboard_bp.route("/stats", methods=["GET"])
@login_required
@role_required("admin", "gestor")
@handle_errors
def get_ai_stats():
    """Retorna estatísticas do sistema de IA"""
    logger.info("Buscando estatísticas de IA")

    conn = _db.get_connection()
    c = conn.cursor()

    try:
        # Total de conversas (leads com estado de IA)
        c.execute("SELECT COUNT(*) as total FROM lead_ia_state")
        total_conversations = c.fetchone()['total']

        # Leads qualificados pela IA
        c.execute("""
            SELECT COUNT(*) as total FROM lead_ia_state
            WHERE qualificado_em IS NOT NULL
        """)
        qualified_leads = c.fetchone()['total']

        # Escalados para humano
        c.execute("""
            SELECT COUNT(*) as total FROM lead_ia_state
            WHERE escalado_humano = 1
        """)
        escalated_to_human = c.fetchone()['total']

        # Conversas ativas (não qualificadas e não escaladas)
        c.execute("""
            SELECT COUNT(*) as total FROM lead_ia_state
            WHERE qualificado_em IS NULL AND escalado_humano = 0
        """)
        active_conversations = c.fetchone()['total']

        # Taxa de conversão
        conversion_rate = (qualified_leads / total_conversations * 100) if total_conversations > 0 else 0

        # Média de mensagens por conversa
        c.execute("SELECT AVG(mensagens_ia_count) as avg FROM lead_ia_state")
        avg_messages = c.fetchone()['avg'] or 0

        stats = {
            "total_conversations": total_conversations,
            "qualified_leads": qualified_leads,
            "escalated_to_human": escalated_to_human,
            "active_conversations": active_conversations,
            "conversion_rate": round(conversion_rate, 2),
            "avg_messages_per_conversation": round(avg_messages, 1)
        }

        logger.info("Estatísticas de IA recuperadas", extra=stats)

        return jsonify({
            "success": True,
            "stats": stats
        })

    finally:
        conn.close()


@ai_dashboard_bp.route("/conversations/active", methods=["GET"])
@login_required
@role_required("admin", "gestor")
@handle_errors
def get_active_conversations():
    """Retorna conversas ativas em andamento"""
    logger.info("Buscando conversas ativas da IA")

    conn = _db.get_connection()
    c = conn.cursor()

    try:
        # Buscar conversas ativas (não qualificadas e não escaladas)
        c.execute("""
            SELECT
                l.id,
                l.phone,
                l.name,
                l.status,
                s.proxima_pergunta_id,
                s.mensagens_ia_count,
                s.escalado_humano,
                s.updated_at,
                (SELECT COUNT(*) FROM messages WHERE lead_id = l.id) as total_messages
            FROM leads l
            INNER JOIN lead_ia_state s ON l.id = s.lead_id
            WHERE s.qualificado_em IS NULL
            AND s.escalado_humano = 0
            ORDER BY s.updated_at DESC
            LIMIT 50
        """)

        conversations = []
        for row in c.fetchall():
            # Buscar respostas coletadas
            c.execute("""
                SELECT pergunta_id, resposta
                FROM lead_qualificacao
                WHERE lead_id = ?
            """, (row['id'],))

            respostas = {r['pergunta_id']: r['resposta'] for r in c.fetchall()}

            # Calcular score simples baseado em respostas
            score = len(respostas) * 20  # 20 pontos por resposta (max 100 com 5 respostas)
            score = min(score, 100)

            conversations.append({
                "phone": row['phone'],
                "collected_data": {
                    "name": row['name'] or respostas.get('nome', ''),
                    **respostas
                },
                "status": "in_progress",
                "score": score,
                "messages_count": row['total_messages'],
                "attempts": row['mensagens_ia_count'],
                "last_interaction": row['updated_at']
            })

        logger.info(f"Encontradas {len(conversations)} conversas ativas")

        return jsonify({
            "success": True,
            "conversations": conversations
        })

    finally:
        conn.close()


@ai_dashboard_bp.route("/conversations/<phone>", methods=["GET"])
@login_required
@role_required("admin", "gestor")
@handle_errors
def get_conversation_details(phone):
    """Retorna detalhes completos de uma conversa"""
    logger.info(f"Buscando detalhes da conversa", extra={"phone": phone})

    conn = _db.get_connection()
    c = conn.cursor()

    try:
        # Buscar lead
        c.execute("SELECT * FROM leads WHERE phone = ?", (phone,))
        lead = c.fetchone()

        if not lead:
            return jsonify({
                "success": False,
                "error": "Conversa não encontrada"
            }), 404

        lead_dict = dict(lead)

        # Buscar estado da IA
        c.execute("SELECT * FROM lead_ia_state WHERE lead_id = ?", (lead_dict['id'],))
        ia_state = c.fetchone()

        # Buscar mensagens
        c.execute("""
            SELECT content, sender_type, timestamp
            FROM messages
            WHERE lead_id = ?
            ORDER BY timestamp ASC
        """, (lead_dict['id'],))

        messages = []
        for msg in c.fetchall():
            messages.append({
                "role": "user" if msg['sender_type'] == 'lead' else "assistant",
                "content": msg['content'],
                "timestamp": msg['timestamp']
            })

        # Buscar respostas de qualificação
        c.execute("""
            SELECT pergunta_id, resposta
            FROM lead_qualificacao
            WHERE lead_id = ?
        """, (lead_dict['id'],))

        respostas = {r['pergunta_id']: r['resposta'] for r in c.fetchall()}

        conversation = {
            "phone": lead_dict['phone'],
            "name": lead_dict['name'],
            "status": "in_progress" if ia_state and not ia_state['qualificado_em'] else "qualified",
            "score": len(respostas) * 20,
            "messages": messages,
            "collected_data": respostas,
            "notes": []
        }

        return jsonify({
            "success": True,
            "conversation": conversation
        })

    finally:
        conn.close()


@ai_dashboard_bp.route("/conversations/<phone>/escalate", methods=["POST"])
@login_required
@role_required("admin", "gestor")
@handle_errors
def escalate_conversation(phone):
    """Escala conversa para atendimento humano"""
    user_id = session["user_id"]

    logger.info("Escalando conversa para humano", extra={"phone": phone, "user_id": user_id})

    conn = _db.get_connection()
    c = conn.cursor()

    try:
        # Buscar lead
        c.execute("SELECT id FROM leads WHERE phone = ?", (phone,))
        lead = c.fetchone()

        if not lead:
            return jsonify({
                "success": False,
                "error": "Lead não encontrado"
            }), 404

        lead_id = lead['id']

        # Marcar como escalado
        c.execute("""
            UPDATE lead_ia_state
            SET escalado_humano = 1,
                updated_at = CURRENT_TIMESTAMP
            WHERE lead_id = ?
        """, (lead_id,))

        # Atualizar status do lead
        c.execute("""
            UPDATE leads
            SET status = 'em_atendimento'
            WHERE id = ?
        """, (lead_id,))

        conn.commit()

        audit_logger.info("Conversa escalada para atendimento humano", extra={
            "phone": phone,
            "lead_id": lead_id,
            "escalated_by": user_id
        })

        return jsonify({
            "success": True,
            "message": "Conversa escalada para atendimento humano"
        })

    finally:
        conn.close()


@ai_dashboard_bp.route("/conversations/<phone>/end", methods=["POST"])
@login_required
@role_required("admin", "gestor")
@handle_errors
def end_conversation(phone):
    """Encerra uma conversa"""
    data = request.json or {}
    reason = data.get('reason', 'Manual')
    user_id = session["user_id"]

    logger.info("Encerrando conversa", extra={"phone": phone, "reason": reason, "user_id": user_id})

    conn = _db.get_connection()
    c = conn.cursor()

    try:
        # Buscar lead
        c.execute("SELECT id FROM leads WHERE phone = ?", (phone,))
        lead = c.fetchone()

        if not lead:
            return jsonify({
                "success": False,
                "error": "Lead não encontrado"
            }), 404

        lead_id = lead['id']

        # Marcar como qualificado (encerrado)
        c.execute("""
            UPDATE lead_ia_state
            SET qualificado_em = CURRENT_TIMESTAMP,
                updated_at = CURRENT_TIMESTAMP
            WHERE lead_id = ?
        """, (lead_id,))

        # Atualizar status do lead
        c.execute("""
            UPDATE leads
            SET status = 'perdido'
            WHERE id = ?
        """, (lead_id,))

        conn.commit()

        audit_logger.info("Conversa encerrada", extra={
            "phone": phone,
            "lead_id": lead_id,
            "reason": reason,
            "ended_by": user_id
        })

        return jsonify({
            "success": True,
            "message": "Conversa encerrada"
        })

    finally:
        conn.close()


@ai_dashboard_bp.route("/performance", methods=["GET"])
@login_required
@role_required("admin", "gestor")
@handle_errors
def get_ai_performance():
    """Retorna métricas de performance da IA nos últimos 7 dias"""
    logger.info("Buscando métricas de performance da IA")

    conn = _db.get_connection()
    c = conn.cursor()

    try:
        # Performance por dia nos últimos 7 dias
        c.execute("""
            SELECT
                DATE(qualificado_em) as dia,
                COUNT(*) as total_qualificados,
                AVG(mensagens_ia_count) as avg_mensagens
            FROM lead_ia_state
            WHERE qualificado_em >= DATE('now', '-7 days')
            GROUP BY DATE(qualificado_em)
            ORDER BY dia DESC
        """)

        daily_performance = [dict(row) for row in c.fetchall()]

        return jsonify({
            "success": True,
            "performance": {
                "daily": daily_performance
            }
        })

    finally:
        conn.close()


__all__ = ['ai_dashboard_bp', 'init_ai_dashboard_routes']
