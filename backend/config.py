"""
Configurações centralizadas do CRM WhatsApp
"""
import os
import secrets
from dotenv import load_dotenv

# Carrega variáveis de ambiente
load_dotenv()


class Config:
    """Configurações base"""

    # Flask - Gera chave segura automaticamente se não estiver definida
    SECRET_KEY = os.getenv('SECRET_KEY') or secrets.token_hex(32)
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

    def __init__(self):
        # Em desenvolvimento, avisa se SECRET_KEY não foi definida
        if not os.getenv('SECRET_KEY'):
            print("⚠️  WARNING: SECRET_KEY não definida. Usando chave gerada automaticamente.")
            print("   Para desenvolvimento consistente, defina SECRET_KEY no arquivo .env")
            print(f"   Sugestão: SECRET_KEY={secrets.token_hex(32)}")


class ProductionConfig(Config):
    """Configurações para produção"""
    DEBUG = False
    LOG_LEVEL = 'WARNING'

    def __init__(self):
        # PRODUÇÃO: SECRET_KEY é OBRIGATÓRIA e deve ser segura
        secret_key = os.getenv('SECRET_KEY')

        if not secret_key:
            raise ValueError(
                "\n"
                "❌ ERRO CRÍTICO: SECRET_KEY não configurada!\n"
                "   Em ambiente de PRODUÇÃO, a SECRET_KEY é OBRIGATÓRIA.\n"
                "\n"
                "   Passos para corrigir:\n"
                "   1. Gere uma chave segura:\n"
                f"      SECRET_KEY={secrets.token_hex(32)}\n"
                "\n"
                "   2. Adicione ao arquivo .env ou configure como variável de ambiente:\n"
                "      export SECRET_KEY=<chave_gerada_acima>\n"
            )

        if len(secret_key) < 32:
            raise ValueError(
                f"\n"
                f"❌ ERRO CRÍTICO: SECRET_KEY muito curta ({len(secret_key)} caracteres)!\n"
                f"   Em ambiente de PRODUÇÃO, a SECRET_KEY deve ter no mínimo 32 caracteres.\n"
                f"\n"
                f"   Gere uma chave segura:\n"
                f"   SECRET_KEY={secrets.token_hex(32)}\n"
            )

        # Sobrescreve a SECRET_KEY validada
        self.SECRET_KEY = secret_key

    # IMPORTANTE: Para escalar como SaaS B2B, migre de SQLite para PostgreSQL/MySQL
    # SQLite não suporta concorrência adequada para produção multi-tenant
    # Descomente e configure quando migrar:
    # DATABASE_URI = os.getenv('DATABASE_URI', 'postgresql://user:pass@localhost/crm')


class TestingConfig(Config):
    """Configurações para testes"""
    TESTING = True
    DEBUG = True
    DATABASE_NAME = ':memory:'  # SQLite em memória para testes


# Seleciona configuração baseada no ambiente
ENV = os.getenv('ENVIRONMENT', 'development').lower()

if ENV == 'production':
    config = ProductionConfig()
elif ENV == 'testing':
    config = TestingConfig()
elif ENV == 'development':
    config = DevelopmentConfig()
else:
    config = Config()


# Exporta a configuração selecionada
__all__ = ['config', 'Config', 'DevelopmentConfig', 'ProductionConfig', 'TestingConfig']
