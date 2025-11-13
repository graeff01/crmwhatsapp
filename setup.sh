#!/bin/bash

# ================================
# Script de Inicialização
# Sistema de Qualificação IA
# ================================

echo "🤖 Iniciando setup do Sistema de Qualificação IA..."

# Cores para output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Função para verificar sucesso
check_success() {
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ $1${NC}"
    else
        echo -e "${RED}✗ Erro: $1${NC}"
        exit 1
    fi
}

# 1. Verificar Python
echo -e "\n${YELLOW}1. Verificando Python...${NC}"
python3 --version
check_success "Python encontrado"

# 2. Criar diretórios necessários
echo -e "\n${YELLOW}2. Criando estrutura de diretórios...${NC}"
mkdir -p backend/ai_qualification/{providers,prompts,rules,qualifiers}
mkdir -p backend/{routes,services}
mkdir -p frontend/components
mkdir -p logs
mkdir -p backups
check_success "Diretórios criados"

# 3. Copiar .env example
echo -e "\n${YELLOW}3. Configurando variáveis de ambiente...${NC}"
if [ ! -f .env ]; then
    cp .env.example .env
    check_success "Arquivo .env criado"
    echo -e "${YELLOW}⚠️  IMPORTANTE: Edite o arquivo .env e configure sua OPENAI_API_KEY${NC}"
else
    echo -e "${GREEN}✓ Arquivo .env já existe${NC}"
fi

# 4. Instalar dependências Python
echo -e "\n${YELLOW}4. Instalando dependências Python...${NC}"
pip install -r requirements.txt --break-system-packages
check_success "Dependências instaladas"

# 5. Criar __init__.py files
echo -e "\n${YELLOW}5. Criando arquivos __init__.py...${NC}"
touch backend/ai_qualification/__init__.py
touch backend/ai_qualification/providers/__init__.py
touch backend/ai_qualification/prompts/__init__.py
touch backend/ai_qualification/rules/__init__.py
touch backend/ai_qualification/qualifiers/__init__.py
check_success "Arquivos __init__.py criados"

# 6. Verificar OpenAI API Key
echo -e "\n${YELLOW}6. Verificando configuração...${NC}"
if grep -q "sk-" .env; then
    echo -e "${GREEN}✓ API Key parece configurada${NC}"
else
    echo -e "${RED}⚠️  ATENÇÃO: Configure a OPENAI_API_KEY no arquivo .env${NC}"
fi

# 7. Testar importações
echo -e "\n${YELLOW}7. Testando importações...${NC}"
python3 -c "
import sys
sys.path.insert(0, 'backend')
try:
    from ai_qualification.engine import QualificationEngine
    from ai_qualification.providers.openai_provider import OpenAIProvider
    from ai_qualification.models import LeadConversation
    print('✓ Importações OK')
except Exception as e:
    print(f'✗ Erro nas importações: {e}')
    sys.exit(1)
"
check_success "Módulos Python verificados"

# 8. Criar script de teste
echo -e "\n${YELLOW}8. Criando script de teste...${NC}"
cat > test_ai_system.py << 'EOF'
#!/usr/bin/env python3
"""
Script de teste do sistema de qualificação IA
"""
import asyncio
import os
from dotenv import load_dotenv

load_dotenv()

# Importa componentes
import sys
sys.path.insert(0, 'backend')

from ai_qualification.engine import QualificationEngine
from ai_qualification.providers.openai_provider import OpenAIProvider
from ai_qualification.models import QualificationCriteria

async def test_system():
    print("🧪 Testando Sistema de Qualificação IA...\n")
    
    # Verifica API key
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key or not api_key.startswith('sk-'):
        print("❌ ERRO: Configure OPENAI_API_KEY no arquivo .env")
        return
    
    print("✓ API Key configurada")
    
    # Inicializa sistema
    try:
        provider = OpenAIProvider(api_key=api_key, model='gpt-3.5-turbo')
        print("✓ Provider OpenAI inicializado")
        
        engine = QualificationEngine(
            ai_provider=provider,
            business_type='services'
        )
        print("✓ Engine de qualificação inicializado")
        
        # Simula conversa
        print("\n📱 Simulando conversa...\n")
        
        result = await engine.process_message(
            phone="+5551999999999",
            message="Olá, quero saber mais sobre seus serviços",
            metadata={"name": "João Teste"}
        )
        
        print(f"Status: {result['status']}")
        print(f"Score: {result.get('qualification_score', 0)}")
        print(f"\nResposta da IA:\n{result['response']}\n")
        
        # Segunda mensagem
        result2 = await engine.process_message(
            phone="+5551999999999",
            message="Meu nome é João Silva e preciso de um orçamento urgente",
        )
        
        print(f"Status: {result2['status']}")
        print(f"Score: {result2.get('qualification_score', 0)}")
        print(f"\nResposta da IA:\n{result2['response']}\n")
        
        print("✅ Sistema funcionando corretamente!")
        
        # Estatísticas
        stats = engine.get_stats()
        print(f"\n📊 Estatísticas:")
        print(f"   Total de conversas: {stats['total_conversations']}")
        print(f"   Conversas ativas: {stats['active_conversations']}")
        
    except Exception as e:
        print(f"❌ Erro no teste: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_system())
EOF

chmod +x test_ai_system.py
check_success "Script de teste criado"

# 9. Resumo final
echo -e "\n${GREEN}════════════════════════════════════════${NC}"
echo -e "${GREEN}✅ Setup concluído com sucesso!${NC}"
echo -e "${GREEN}════════════════════════════════════════${NC}"

echo -e "\n📋 Próximos passos:"
echo -e "   1. Configure sua API key da OpenAI no arquivo ${YELLOW}.env${NC}"
echo -e "   2. Execute: ${YELLOW}python3 test_ai_system.py${NC} para testar"
echo -e "   3. Integre as rotas no seu app.py:"
echo -e "      ${YELLOW}from routes.ai_webhook import register_ai_routes${NC}"
echo -e "      ${YELLOW}register_ai_routes(app)${NC}"
echo -e "   4. Acesse o dashboard: ${YELLOW}http://localhost:3000/ai-qualification${NC}"

echo -e "\n📚 Documentação:"
echo -e "   - Guia rápido: ${YELLOW}QUICK_START.md${NC}"
echo -e "   - Documentação completa: ${YELLOW}AI_QUALIFICATION_README.md${NC}"
echo -e "   - Exemplo de .env: ${YELLOW}.env.example${NC}"

echo -e "\n🔗 Links úteis:"
echo -e "   - OpenAI API Keys: ${YELLOW}https://platform.openai.com/api-keys${NC}"
echo -e "   - Documentação OpenAI: ${YELLOW}https://platform.openai.com/docs${NC}"

echo -e "\n${GREEN}Bom trabalho! 🚀${NC}\n"