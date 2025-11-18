"""
Blueprint de Autenticação e Gerenciamento de Usuários
Responsável por login, logout, CRUD de usuários
"""
from flask import Blueprint, request, jsonify, session
from middlewares import rate_limit, validate_request, handle_errors, InputValidator
from auth_decorators import login_required, role_required
from advanced_cache import cached, invalidate_cache
from logger import get_logger, get_audit_logger, get_security_logger

# Inicializa loggers
logger = get_logger(__name__)
audit_logger = get_audit_logger()
security_logger = get_security_logger()

# Cria Blueprint
auth_bp = Blueprint('auth', __name__, url_prefix='/api')

# Instância do validador
validator = InputValidator()


# ===== AUTENTICAÇÃO =====

@auth_bp.route("/login", methods=["POST"])
@rate_limit('per_minute')
@validate_request('username', 'password')
@handle_errors
def login():
    """
    Endpoint de login

    Request:
        {
            "username": "admin",
            "password": "senha123"
        }

    Response:
        {
            "success": true,
            "user": {
                "id": 1,
                "username": "admin",
                "name": "Administrador",
                "role": "admin"
            }
        }
    """
    from database import Database
    db = Database()

    data = request.json

    # Valida username
    valid_user, username = validator.validate_username(data.get("username"))
    if not valid_user:
        security_logger.warning(f"Login com username inválido: {data.get('username')}")
        return jsonify({"error": username}), 400

    # Valida password
    valid_pass, password = validator.validate_password(data.get("password"))
    if not valid_pass:
        return jsonify({"error": password}), 400

    # Autentica
    user = db.authenticate_user(username, password)
    if not user:
        security_logger.warning(
            "Tentativa de login falhou",
            extra={'username': username, 'ip': request.remote_addr}
        )
        audit_logger.info(
            "Login falhou",
            extra={'action': 'login_failed', 'username': username}
        )
        return jsonify({"error": "Credenciais inválidas"}), 401

    # Cria sessão
    session["user_id"] = user["id"]
    session["username"] = user["username"]
    session["name"] = user["name"]
    session["role"] = user["role"]

    logger.info(f"Login bem-sucedido: {username}", extra={'user_id': user['id']})
    audit_logger.info(
        "Login realizado",
        extra={
            'action': 'login_success',
            'user_id': user['id'],
            'username': username
        }
    )

    return jsonify({"success": True, "user": user})


@auth_bp.route("/logout", methods=["POST"])
@login_required
def logout():
    """
    Endpoint de logout

    Response:
        {"success": true}
    """
    user_id = session.get("user_id")
    username = session.get("username")

    audit_logger.info(
        "Logout realizado",
        extra={'action': 'logout', 'user_id': user_id, 'username': username}
    )

    session.clear()
    logger.info(f"Logout: {username}")

    return jsonify({"success": True})


@auth_bp.route("/me", methods=["GET"])
@login_required
def get_current_user():
    """
    Retorna informações do usuário autenticado

    Response:
        {
            "id": 1,
            "username": "admin",
            "name": "Administrador",
            "role": "admin"
        }
    """
    return jsonify({
        "id": session["user_id"],
        "username": session["username"],
        "name": session["name"],
        "role": session["role"]
    })


# ===== GERENCIAMENTO DE USUÁRIOS =====

@auth_bp.route("/users", methods=["GET"])
@rate_limit('per_minute')
@role_required("admin", "gestor")
@cached(ttl=60, key_prefix="users")
def get_users():
    """
    Lista todos os usuários (apenas admin e gestor)

    Response:
        [
            {
                "id": 1,
                "username": "admin",
                "name": "Administrador",
                "role": "admin",
                "active": 1
            },
            ...
        ]
    """
    from database import Database
    db = Database()

    users = db.get_all_users()
    logger.info(f"Listagem de usuários por {session.get('username')}")

    return jsonify(users)


@auth_bp.route("/users", methods=["POST"])
@rate_limit('per_minute')
@role_required("admin")
@validate_request('username', 'password', 'name', 'role')
@handle_errors
def create_user():
    """
    Cria novo usuário (apenas admin)

    Request:
        {
            "username": "joao",
            "password": "senha123",
            "name": "João Silva",
            "role": "vendedor"
        }

    Response:
        {"success": true, "user_id": 5}
    """
    from database import Database
    db = Database()

    data = request.json

    # Valida role
    valid_role, role_msg = validator.validate_role(data["role"])
    if not valid_role:
        return jsonify({"error": role_msg}), 400

    # Cria usuário
    uid = db.create_user(
        data["username"],
        data["password"],
        data["name"],
        data["role"]
    )

    if uid:
        invalidate_cache("users")  # Invalida cache de usuários
        logger.info(f"Usuário criado: {data['username']}", extra={'user_id': uid})
        audit_logger.info(
            "Usuário criado",
            extra={
                'action': 'user_created',
                'user_id': uid,
                'username': data['username'],
                'created_by': session['user_id']
            }
        )
        return jsonify({"success": True, "user_id": uid})

    logger.warning(f"Tentativa de criar usuário duplicado: {data['username']}")
    return jsonify({"error": "Usuário já existe"}), 400


@auth_bp.route("/users/<int:user_id>", methods=["PUT"])
@rate_limit('per_minute')
@role_required("admin")
@handle_errors
def update_user(user_id):
    """
    Atualiza usuário (apenas admin)

    Request:
        {
            "name": "João Silva Jr",
            "role": "gestor",
            "active": 1
        }

    Response:
        {"success": true}
    """
    from database import Database
    db = Database()

    data = request.json

    # Valida role se fornecida
    if "role" in data:
        valid_role, role_msg = validator.validate_role(data["role"])
        if not valid_role:
            return jsonify({"error": role_msg}), 400

    db.update_user(user_id, data["name"], data["role"], data.get("active", 1))

    invalidate_cache("users")
    logger.info(f"Usuário {user_id} atualizado por {session['username']}")
    audit_logger.info(
        "Usuário atualizado",
        extra={
            'action': 'user_updated',
            'user_id': user_id,
            'updated_by': session['user_id']
        }
    )

    return jsonify({"success": True})


@auth_bp.route("/users/<int:user_id>", methods=["DELETE"])
@rate_limit('per_minute')
@role_required("admin")
@handle_errors
def delete_user(user_id):
    """
    Remove usuário (apenas admin)

    Response:
        {"success": true}
    """
    from database import Database
    db = Database()

    # Não permite deletar a si mesmo
    if user_id == session['user_id']:
        return jsonify({"error": "Não é possível deletar seu próprio usuário"}), 400

    db.delete_user(user_id)

    invalidate_cache("users")
    logger.info(f"Usuário {user_id} deletado por {session['username']}")
    audit_logger.info(
        "Usuário deletado",
        extra={
            'action': 'user_deleted',
            'user_id': user_id,
            'deleted_by': session['user_id']
        }
    )

    return jsonify({"success": True})


@auth_bp.route("/users/<int:user_id>/password", methods=["PUT"])
@rate_limit('per_minute')
@role_required("admin")
@validate_request('new_password')
@handle_errors
def change_password(user_id):
    """
    Altera senha de usuário (apenas admin)

    Request:
        {"new_password": "novaSenha123"}

    Response:
        {"success": true}
    """
    from database import Database
    db = Database()

    data = request.json

    # Valida nova senha
    valid_pass, pass_msg = validator.validate_password(data["new_password"])
    if not valid_pass:
        return jsonify({"error": pass_msg}), 400

    db.change_user_password(user_id, data["new_password"])

    logger.info(f"Senha do usuário {user_id} alterada por {session['username']}")
    audit_logger.info(
        "Senha alterada",
        extra={
            'action': 'password_changed',
            'user_id': user_id,
            'changed_by': session['user_id']
        }
    )

    return jsonify({"success": True})


# Exporta blueprint
__all__ = ['auth_bp']
