"""
Configurações centralizadas do CRM WhatsApp
"""
import os
from dotenv import load_dotenv

# Carrega variáveis de ambiente
load_dotenv()

class Config:
    """Configurações base"""
    
    # Flask
    SECRET_KEY = os.getenv('SECRET_KEY', 'sua-chave-secreta-mude-em-producao')
    DEBUG = os.getenv('DEBUG', 'False') == 'True'
    HOST = os.getenv('FLASK_HOST', '0.0.0.0')
    PORT = int(os.getenv('FLASK_PORT', '5000'))
    
    # Database
    DATABASE_NAME = os.getenv('DATABASE_NAME', 'crm_whatsapp.db')
    
    # WhatsApp Service
    WHATSAPP_SERVICE_URL = os.getenv('WHATSAPP_SERVICE_URL', 'http://localhost:3001')
    WHATSAPP_TIMEOUT = int(os.getenv('WHATSAPP_TIMEOUT', '10'))
    WHATSAPP_MAX_RETRIES = int(os.getenv('WHATSAPP_MAX_RETRIES', '3'))
    
    # CORS
    CORS_ORIGINS = os.getenv('CORS_ORIGINS', 'http://localhost:3000').split(',')
    
    # Rate Limiting
    RATE_LIMIT_ENABLED = os.getenv('RATE_LIMIT_ENABLED', 'True') == 'True'
    RATE_LIMIT_PER_MINUTE = int(os.getenv('RATE_LIMIT_PER_MINUTE', '60'))
    RATE_LIMIT_PER_HOUR = int(os.getenv('RATE_LIMIT_PER_HOUR', '1000'))
    
    # Upload
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
    
    # Socket.io
    SOCKETIO_ASYNC_MODE = os.getenv('SOCKETIO_ASYNC_MODE', 'threading')
    
    # Logs
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE = os.getenv('LOG_FILE', 'crm_whatsapp.log')


class DevelopmentConfig(Config):
    """Configurações para desenvolvimento"""
    DEBUG = True
    LOG_LEVEL = 'DEBUG'


class ProductionConfig(Config):
    """Configurações para produção"""
    DEBUG = False
    LOG_LEVEL = 'WARNING'
    # Em produção, use um banco de dados adequado (PostgreSQL, MySQL)
    # DATABASE_URI = os.getenv('DATABASE_URI', 'postgresql://user:pass@localhost/crm')


# Seleciona configuração baseada no ambiente
ENV = os.getenv('ENVIRONMENT', 'development')

if ENV == 'production':
    config = ProductionConfig()
elif ENV == 'development':
    config = DevelopmentConfig()
else:
    config = Config()