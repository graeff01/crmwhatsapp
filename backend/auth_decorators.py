"""
Decorators de Autenticação e Autorização
Centraliza lógica de controle de acesso
"""
from flask import session, jsonify
from functools import wraps
from logger import get_security_logger

security_logger = get_security_logger()


def login_required(f):
    """
    Decorator que requer autenticação

    Usage:
        @login_required
        def minha_rota():
            user_id = session['user_id']
            ...
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            security_logger.warning(
                "Acesso não autenticado bloqueado",
                extra={'endpoint': f.__name__}
            )
            return jsonify({"error": "Não autenticado"}), 401
        return f(*args, **kwargs)
    return decorated


def role_required(*roles):
    """
    Decorator que requer roles específicas

    Usage:
        @role_required("admin", "gestor")
        def minha_rota():
            ...
    """
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if "user_id" not in session:
                security_logger.warning(
                    "Acesso não autenticado bloqueado",
                    extra={'endpoint': f.__name__, 'required_roles': roles}
                )
                return jsonify({"error": "Não autenticado"}), 401

            user_role = session.get("role")
            if user_role not in roles:
                security_logger.warning(
                    "Acesso sem permissão bloqueado",
                    extra={
                        'user_id': session.get('user_id'),
                        'user_role': user_role,
                        'required_roles': roles,
                        'endpoint': f.__name__
                    }
                )
                return jsonify({"error": "Sem permissão"}), 403

            return f(*args, **kwargs)
        return decorated
    return decorator


def self_or_admin_required(f):
    """
    Decorator que permite acesso ao próprio usuário ou admin

    Usage:
        @self_or_admin_required
        def update_user(user_id):
            # Pode acessar se for o próprio usuário OU admin
            ...
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            return jsonify({"error": "Não autenticado"}), 401

        user_id = kwargs.get('user_id') or args[0] if args else None
        session_user_id = session.get("user_id")
        user_role = session.get("role")

        # Permite se for o próprio usuário ou admin
        if session_user_id != user_id and user_role != "admin":
            security_logger.warning(
                "Tentativa de acesso a recurso de outro usuário",
                extra={
                    'user_id': session_user_id,
                    'target_user_id': user_id,
                    'endpoint': f.__name__
                }
            )
            return jsonify({"error": "Sem permissão"}), 403

        return f(*args, **kwargs)
    return decorated


__all__ = ['login_required', 'role_required', 'self_or_admin_required']
