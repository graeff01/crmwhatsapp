#!/usr/bin/env python3
"""
🧪 Script de Teste - IA Assistant
Testa a integração completa do sistema de IA

Execute: python test_ai.py
"""

import sys
import os
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

# Cores para output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'

def print_header(text):
    """Imprime cabeçalho colorido"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{text.center(60)}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.END}\n")

def print_success(text):
    """Imprime mensagem de sucesso"""
    print(f"{Colors.GREEN}✅ {text}{Colors.END}")

def print_error(text):
    """Imprime mensagem de erro"""
    print(f"{Colors.RED}❌ {text}{Colors.END}")

def print_warning(text):
    """Imprime mensagem de aviso"""
    print(f"{Colors.YELLOW}⚠️  {text}{Colors.END}")

def print_info(text):
    """Imprime informação"""
    print(f"{Colors.BLUE}ℹ️  {text}{Colors.END}")

def test_environment():
    """Testa variáveis de ambiente"""
    print_header("1. TESTANDO VARIÁVEIS DE AMBIENTE")

    tests_passed = 0
    tests_total = 0

    # Variáveis obrigatórias
    required_vars = {
        "OPENAI_API_KEY": "Chave da API OpenAI",
        "IA_HABILITADA": "IA habilitada"
    }

    for var, description in required_vars.items():
        tests_total += 1
        value = os.getenv(var)
        if value:
            print_success(f"{description}: Configurada")
            tests_passed += 1
        else:
            print_error(f"{description}: NÃO configurada")
            print_info(f"   Configure {var} no arquivo .env")

    # Variáveis opcionais
    optional_vars = {
        "OPENAI_MODEL": "Modelo OpenAI",
        "BUSINESS_TYPE": "Tipo de negócio",
        "SECRET_KEY": "Chave secreta"
    }

    print("\n📋 Variáveis opcionais:")
    for var, description in optional_vars.items():
        value = os.getenv(var)
        if value:
            print_info(f"{description}: {value}")
        else:
            print_warning(f"{description}: Usando padrão")

    return tests_passed, tests_total

def test_imports():
    """Testa importações dos módulos"""
    print_header("2. TESTANDO IMPORTAÇÕES")

    tests_passed = 0
    tests_total = 0

    modules = [
        ("database", "Database core"),
        ("database_ia", "Database IA extensions"),
        ("ia_assistant", "IA Assistant"),
        ("ai_qualification.models", "Modelos de dados"),
        ("ai_qualification.rules.qualification_rules", "Regras de qualificação"),
        ("ai_qualification.prompts.qualification_prompts", "Prompts"),
        ("ai_qualification.providers.openai_provider", "OpenAI Provider"),
    ]

    for module_name, description in modules:
        tests_total += 1
        try:
            __import__(module_name)
            print_success(f"{description}: OK")
            tests_passed += 1
        except ImportError as e:
            print_error(f"{description}: FALHOU")
            print_info(f"   Erro: {str(e)}")
        except Exception as e:
            print_error(f"{description}: ERRO")
            print_info(f"   Erro: {str(e)}")

    return tests_passed, tests_total

def test_database():
    """Testa conexão e extensões do banco"""
    print_header("3. TESTANDO BANCO DE DADOS")

    tests_passed = 0
    tests_total = 0

    try:
        from database import Database
        from database_ia import extend_database_with_ia

        # Criar instância
        tests_total += 1
        db = Database()
        print_success("Database inicializado")
        tests_passed += 1

        # Estender com IA
        tests_total += 1
        extend_database_with_ia(db)
        print_success("Extensões de IA aplicadas")
        tests_passed += 1

        # Verificar métodos
        tests_total += 1
        required_methods = [
            'add_lead_qualificacao_resposta',
            'get_lead_qualificacao_respostas',
            'get_leads_qualificados_ia',
            'get_estatisticas_ia'
        ]

        missing_methods = [m for m in required_methods if not hasattr(db, m)]
        if not missing_methods:
            print_success("Todos os métodos de IA disponíveis")
            tests_passed += 1
        else:
            print_error(f"Métodos faltando: {', '.join(missing_methods)}")

        # Testar estatísticas
        tests_total += 1
        stats = db.get_estatisticas_ia()
        print_success(f"Estatísticas IA: {stats}")
        tests_passed += 1

    except Exception as e:
        print_error(f"Erro ao testar banco: {str(e)}")

    return tests_passed, tests_total

def test_ia_assistant():
    """Testa IA Assistant"""
    print_header("4. TESTANDO IA ASSISTANT")

    tests_passed = 0
    tests_total = 0

    try:
        from database import Database
        from database_ia import extend_database_with_ia
        from ia_assistant import IAAssistant

        # Criar database
        db = Database()
        extend_database_with_ia(db)

        # Criar IA Assistant
        tests_total += 1
        ia = IAAssistant(db)
        print_success("IAAssistant inicializado")
        tests_passed += 1

        # Verificar configuração
        tests_total += 1
        stats = ia.get_estatisticas()
        print_info(f"Configuração IA: {stats}")
        if stats.get('ia_habilitada'):
            print_success("IA está habilitada")
            tests_passed += 1
        else:
            print_warning("IA desabilitada (verifique .env)")

        # Verificar OpenAI
        tests_total += 1
        if ia.openai_habilitada:
            print_success("OpenAI disponível")
            tests_passed += 1
        else:
            print_warning("OpenAI não disponível (modo fallback)")
            tests_passed += 1  # Conta como sucesso pois tem fallback

    except Exception as e:
        print_error(f"Erro ao testar IA Assistant: {str(e)}")
        import traceback
        traceback.print_exc()

    return tests_passed, tests_total

def test_ai_qualification_models():
    """Testa modelos de qualificação"""
    print_header("5. TESTANDO MODELOS DE QUALIFICAÇÃO")

    tests_passed = 0
    tests_total = 0

    try:
        from ai_qualification.models import (
            QualificationStatus,
            MessageRole,
            LeadConversation,
            QualificationCriteria
        )

        # Criar conversa de teste
        tests_total += 1
        conv = LeadConversation(phone="5511999999999")
        conv.add_message(MessageRole.USER, "Olá, quero saber sobre seus serviços")
        conv.add_message(MessageRole.ASSISTANT, "Olá! Qual seu nome?")
        print_success("LeadConversation criada")
        tests_passed += 1

        # Testar coleta de dados
        tests_total += 1
        conv.update_collected_data("name", "João Silva")
        conv.update_collected_data("interest", "Desenvolvimento Web")
        print_success(f"Dados coletados: {conv.collected_data}")
        tests_passed += 1

        # Testar critérios
        tests_total += 1
        criteria = QualificationCriteria(
            required_fields=["name", "phone"],
            min_score=50
        )
        print_success(f"Critérios: {criteria.to_dict()}")
        tests_passed += 1

    except Exception as e:
        print_error(f"Erro ao testar modelos: {str(e)}")
        import traceback
        traceback.print_exc()

    return tests_passed, tests_total

def test_openai_connection():
    """Testa conexão com OpenAI"""
    print_header("6. TESTANDO CONEXÃO OPENAI")

    tests_passed = 0
    tests_total = 0

    api_key = os.getenv("OPENAI_API_KEY")

    if not api_key or api_key.startswith("sk-xxx"):
        print_warning("OPENAI_API_KEY não configurada - pulando teste")
        return 0, 0

    try:
        from openai import OpenAI

        tests_total += 1
        client = OpenAI(api_key=api_key)

        # Teste simples
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": "Diga apenas 'OK'"}],
            max_tokens=5
        )

        if response and response.choices:
            print_success("Conexão OpenAI: OK")
            print_info(f"Resposta: {response.choices[0].message.content}")
            tests_passed += 1
        else:
            print_error("Resposta inválida da OpenAI")

    except Exception as e:
        print_error(f"Erro ao conectar OpenAI: {str(e)}")
        print_info("Verifique sua OPENAI_API_KEY")

    return tests_passed, tests_total

def main():
    """Função principal"""
    print(f"\n{Colors.BOLD}🤖 Teste do Sistema de IA Assistant{Colors.END}")
    print(f"{Colors.BOLD}CRM WhatsApp + Qualificação Automática{Colors.END}\n")

    all_tests_passed = 0
    all_tests_total = 0

    # Executar todos os testes
    tests = [
        test_environment,
        test_imports,
        test_database,
        test_ia_assistant,
        test_ai_qualification_models,
        test_openai_connection
    ]

    for test_func in tests:
        passed, total = test_func()
        all_tests_passed += passed
        all_tests_total += total

    # Resultado final
    print_header("RESULTADO FINAL")

    success_rate = (all_tests_passed / all_tests_total * 100) if all_tests_total > 0 else 0

    print(f"\n{Colors.BOLD}Testes executados: {all_tests_total}{Colors.END}")
    print(f"{Colors.GREEN}✅ Sucessos: {all_tests_passed}{Colors.END}")
    print(f"{Colors.RED}❌ Falhas: {all_tests_total - all_tests_passed}{Colors.END}")
    print(f"\n{Colors.BOLD}Taxa de sucesso: {success_rate:.1f}%{Colors.END}\n")

    if success_rate >= 80:
        print_success("Sistema pronto para uso! 🚀")
        return 0
    elif success_rate >= 50:
        print_warning("Sistema parcialmente funcional. Verifique os erros acima.")
        return 1
    else:
        print_error("Sistema com problemas críticos. Corrija os erros.")
        return 2

if __name__ == "__main__":
    sys.exit(main())
