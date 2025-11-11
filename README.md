<<<<<<< HEAD
# 🚀 CRM WhatsApp Multi-Atendente - MVP

Sistema de CRM com interface compartilhada de WhatsApp onde múltiplos vendedores podem atender leads através de um único número.

## 📋 Funcionalidades Implementadas

### ✅ Já Funciona no MVP:
- 🔐 Sistema de login/autenticação
- 👥 Múltiplos perfis (Admin, Gestor, Vendedor)
- 📊 Fila de leads não atribuídos
- 🎯 Vendedor pode "pegar" lead da fila
- 💬 Interface de chat estilo WhatsApp Web
- ⚡ Mensagens em tempo real (Socket.io)
- 📝 Histórico completo de conversas
- 🏷️ Status de leads (Novo, Em Atendimento, Qualificado, etc)
- 📱 Interface responsiva

### 🔄 Para Adicionar Depois:
- WhatsApp Business API oficial (agora usa simulação)
- Dashboard de métricas para gestores
- Relatórios e analytics
- Notas internas entre equipe
- Transferência de leads entre vendedores
- Automações de mensagens

## 🛠️ Tecnologias Utilizadas

**Backend:**
- Python 3.x
- Flask (API REST)
- Flask-SocketIO (Real-time)
- SQLite (Banco de dados)

**Frontend:**
- React 18
- Socket.io Client
- Axios
- Lucide React (ícones)
- Vite

## 📦 Instalação

### 1. Backend

```bash
cd backend

# Instalar dependências
pip install -r requirements.txt

# Rodar servidor
python app.py
```

O backend vai rodar em: `http://localhost:5000`

### 2. Frontend

```bash
cd frontend

# Instalar dependências
npm install

# Rodar em desenvolvimento
npm run dev
```

O frontend vai rodar em: `http://localhost:3000`

## 🔑 Credenciais Padrão

**Usuário Admin:**
- Username: `admin`
- Senha: `admin123`

## 📖 Como Usar

### 1. Fazer Login
- Acesse http://localhost:3000
- Use as credenciais padrão
- Você será direcionado para o dashboard

### 2. Simular Mensagens de Leads (Teste)

Como ainda não temos VenomBot conectado, use esta API para simular mensagens:

```bash
curl -X POST http://localhost:5000/api/simulate/message \
  -H "Content-Type: application/json" \
  -d '{
    "phone": "5551999999999",
    "content": "Olá, tenho interesse no produto!",
    "name": "João Silva"
  }'
```

Ou crie um arquivo `test_message.html` com este código:

```html
<!DOCTYPE html>
<html>
<head>
    <title>Simulador de Mensagens</title>
</head>
<body>
    <h1>Simulador de Mensagens WhatsApp</h1>
    <form id="messageForm">
        <input type="text" id="phone" placeholder="Telefone (ex: 5551999999999)" required>
        <input type="text" id="name" placeholder="Nome do Lead" required>
        <textarea id="content" placeholder="Mensagem" required></textarea>
        <button type="submit">Enviar Mensagem Simulada</button>
    </form>

    <script>
        document.getElementById('messageForm').addEventListener('submit', async (e) => {
            e.preventDefault();
            const response = await fetch('http://localhost:5000/api/simulate/message', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    phone: document.getElementById('phone').value,
                    content: document.getElementById('content').value,
                    name: document.getElementById('name').value
                })
            });
            alert('Mensagem simulada enviada!');
        });
    </script>
</body>
</html>
```

### 3. Fluxo de Atendimento

1. **Lead envia mensagem** (simulada ou real quando integrar VenomBot)
2. **Mensagem cai na aba "Fila"** (leads não atribuídos)
3. **Vendedor clica em "Pegar Lead"** 
4. **Lead vai para aba "Meus Leads"** com status "Em Atendimento"
5. **Vendedor conversa** através da interface
6. **Lead sempre vê o mesmo número** respondendo
7. **Gestor tem acesso** a todas as conversas

## 🏗️ Estrutura do Projeto

```
crm-whatsapp/
├── backend/
│   ├── app.py                 # API Flask principal
│   ├── database.py            # Gerenciamento SQLite
│   ├── whatsapp_service.py    # Serviço WhatsApp (preparado para VenomBot)
│   ├── requirements.txt       # Dependências Python
│   └── crm_whatsapp.db       # Banco SQLite (criado automaticamente)
│
└── frontend/
    ├── src/
    │   ├── components/
    │   │   ├── Login.jsx      # Tela de login
    │   │   └── Dashboard.jsx  # Dashboard principal
    │   ├── api.js            # Comunicação com backend
    │   ├── App.jsx           # App principal
    │   ├── main.jsx          # Entry point
    │   └── styles.css        # Estilos globais
    ├── index.html
    ├── package.json
    └── vite.config.js
```

## 🔧 Próximos Passos (Integração VenomBot)

Quando estiver pronto para integrar o VenomBot real:

1. Instalar VenomBot:
```bash
npm install venom-bot
```

2. No arquivo `whatsapp_service.py`, descomentar e implementar:
```python
# TODO: Implementar VenomBot real aqui
from venom import create, Whatsapp
self.client = await create('crm-session')
```

3. Conectar callbacks:
- `on_qr_code` → Gerar QR Code para autenticação
- `on_message` → Receber mensagens
- `sendText` → Enviar mensagens

## 🎨 Customização

### Adicionar Novo Usuário

Via Python:
```python
from database import Database
db = Database()
db.create_user('vendedor1', 'senha123', 'João Vendedor', 'vendedor')
```

### Mudar Status de Lead

Os status disponíveis são:
- `novo` - Lead acabou de chegar
- `em_atendimento` - Vendedor está atendendo
- `qualificado` - Lead tem potencial
- `perdido` - Lead não converteu
- `ganho` - Lead virou cliente

## 🐛 Troubleshooting

**Erro de CORS:**
- Certifique-se que o backend está rodando na porta 5000
- Verifique o proxy no `vite.config.js`

**Mensagens não aparecem em tempo real:**
- Verifique se Socket.io está conectado (console do navegador)
- Confirme que ambos servidores estão rodando

**Não consegue fazer login:**
- Verifique se o banco de dados foi criado em `backend/crm_whatsapp.db`
- Use as credenciais padrão: admin / admin123

## 📞 Suporte

Dúvidas ou problemas? Me chama que eu te ajudo a configurar!

---

**Desenvolvido para**: Veloce - Agência Digital  
**Objetivo**: MVP funcional para testar fluxo multi-atendente antes de integrar WhatsApp Business API oficial
=======
# crmwhatsapp
>>>>>>> 5b044837e24ce04c320a3d1530e5f6168594321c
