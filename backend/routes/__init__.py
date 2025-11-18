"""
Routes Package
Blueprints organizados para o CRM WhatsApp
"""

from flask import Blueprint


def register_blueprints(app):
    """
    Registra todos os blueprints na aplicação Flask

    Args:
        app: Instância do Flask
    """
    from .auth import auth_bp
    from .leads import leads_bp
    from .tags_sla import tags_sla_bp
    from .metrics import metrics_bp
    from .whatsapp import whatsapp_bp
    from .alerts import alerts_bp
    from .gestor import gestor_bp
    from .health import health_bp

    # Registra blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(leads_bp)
    app.register_blueprint(tags_sla_bp)
    app.register_blueprint(metrics_bp)
    app.register_blueprint(whatsapp_bp)
    app.register_blueprint(alerts_bp)
    app.register_blueprint(gestor_bp)
    app.register_blueprint(health_bp)


__all__ = ['register_blueprints']
