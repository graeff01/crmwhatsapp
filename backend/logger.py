"""
Sistema de Logging Estruturado para CRM WhatsApp
Configuração centralizada de logs com suporte a rotação e formato JSON
"""
import logging
import logging.handlers
import os
import sys
from datetime import datetime
from pythonjsonlogger import jsonlogger
from config import config


class CustomJsonFormatter(jsonlogger.JsonFormatter):
    """Formatter JSON customizado com campos adicionais"""

    def add_fields(self, log_record, record, message_dict):
        super(CustomJsonFormatter, self).add_fields(log_record, record, message_dict)

        # Adiciona timestamp ISO 8601
        if not log_record.get('timestamp'):
            log_record['timestamp'] = datetime.utcnow().isoformat() + 'Z'

        # Adiciona nível de log
        if log_record.get('level'):
            log_record['level'] = log_record['level'].upper()
        else:
            log_record['level'] = record.levelname

        # Adiciona ambiente
        log_record['environment'] = os.getenv('ENVIRONMENT', 'development')

        # Adiciona nome da aplicação
        log_record['app'] = 'crm-whatsapp'


def setup_logger(name='crm_whatsapp', level=None):
    """
    Configura e retorna um logger estruturado

    Args:
        name: Nome do logger
        level: Nível de log (DEBUG, INFO, WARNING, ERROR, CRITICAL)

    Returns:
        logging.Logger: Logger configurado
    """
    logger = logging.getLogger(name)

    # Evita duplicação de handlers
    if logger.handlers:
        return logger

    # Define nível de log (usa configuração ou padrão)
    log_level = level or getattr(logging, config.LOG_LEVEL.upper(), logging.INFO)
    logger.setLevel(log_level)

    # ===== Console Handler (sempre ativo) =====
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)

    # Formato para console (legível para humanos)
    if config.DEBUG:
        console_format = logging.Formatter(
            fmt='%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
    else:
        # Em produção, usa JSON para facilitar parsing
        console_format = CustomJsonFormatter(
            '%(timestamp)s %(level)s %(name)s %(message)s'
        )

    console_handler.setFormatter(console_format)
    logger.addHandler(console_handler)

    # ===== File Handler (produção) =====
    if not config.DEBUG:
        # Cria diretório de logs se não existir
        log_dir = os.path.join(os.path.dirname(__file__), 'logs')
        os.makedirs(log_dir, exist_ok=True)

        log_file = os.path.join(log_dir, config.LOG_FILE)

        # Rotating file handler (10MB por arquivo, mantém 5 backups)
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setLevel(log_level)

        # Formato JSON para arquivo
        file_format = CustomJsonFormatter(
            '%(timestamp)s %(level)s %(name)s %(message)s %(pathname)s %(lineno)d'
        )
        file_handler.setFormatter(file_format)
        logger.addHandler(file_handler)

    # Não propaga para o logger raiz
    logger.propagate = False

    return logger


# ===== Loggers especializados =====

def get_logger(name=None):
    """
    Retorna logger configurado para uso geral

    Usage:
        from logger import get_logger
        logger = get_logger(__name__)
        logger.info("Mensagem")
    """
    if name:
        return logging.getLogger(f'crm_whatsapp.{name}')
    return logging.getLogger('crm_whatsapp')


def get_audit_logger():
    """
    Retorna logger especializado para auditoria

    Usage:
        from logger import get_audit_logger
        audit_logger = get_audit_logger()
        audit_logger.info("User action", extra={'user_id': 123, 'action': 'create_lead'})
    """
    audit_logger = logging.getLogger('crm_whatsapp.audit')

    if not audit_logger.handlers:
        # Cria arquivo separado para logs de auditoria
        log_dir = os.path.join(os.path.dirname(__file__), 'logs')
        os.makedirs(log_dir, exist_ok=True)

        audit_file = os.path.join(log_dir, 'audit.log')

        # Handler específico para auditoria
        audit_handler = logging.handlers.RotatingFileHandler(
            audit_file,
            maxBytes=10 * 1024 * 1024,
            backupCount=10,  # Mantém mais backups para auditoria
            encoding='utf-8'
        )
        audit_handler.setLevel(logging.INFO)

        # Formato JSON para auditoria
        audit_format = CustomJsonFormatter(
            '%(timestamp)s %(level)s %(message)s'
        )
        audit_handler.setFormatter(audit_format)
        audit_logger.addHandler(audit_handler)

    audit_logger.propagate = False
    return audit_logger


def get_security_logger():
    """
    Retorna logger especializado para eventos de segurança

    Usage:
        from logger import get_security_logger
        security_logger = get_security_logger()
        security_logger.warning("Failed login attempt", extra={'ip': '1.2.3.4'})
    """
    security_logger = logging.getLogger('crm_whatsapp.security')

    if not security_logger.handlers:
        # Cria arquivo separado para logs de segurança
        log_dir = os.path.join(os.path.dirname(__file__), 'logs')
        os.makedirs(log_dir, exist_ok=True)

        security_file = os.path.join(log_dir, 'security.log')

        security_handler = logging.handlers.RotatingFileHandler(
            security_file,
            maxBytes=10 * 1024 * 1024,
            backupCount=10,
            encoding='utf-8'
        )
        security_handler.setLevel(logging.WARNING)

        security_format = CustomJsonFormatter(
            '%(timestamp)s %(level)s %(message)s'
        )
        security_handler.setFormatter(security_format)
        security_logger.addHandler(security_handler)

    security_logger.propagate = False
    return security_logger


# Inicializa logger principal na importação
main_logger = setup_logger()


# Exporta para facilitar importação
__all__ = [
    'setup_logger',
    'get_logger',
    'get_audit_logger',
    'get_security_logger',
    'main_logger'
]
