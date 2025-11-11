/**
 * ===================================
 * CRM WhatsApp - Serviço WhatsApp
 * ===================================
 * 
 * Usando Baileys - Mais estável que Venom
 */

const {
  default: makeWASocket,
  DisconnectReason,
  useMultiFileAuthState,
  fetchLatestBaileysVersion
} = require('@whiskeysockets/baileys');
const express = require('express');
const axios = require('axios');
const dotenv = require('dotenv');
const P = require('pino');
const qrcode = require('qrcode-terminal');

dotenv.config();

// ===================================
// CONFIGURAÇÕES
// ===================================
const CONFIG = {
  SESSION_DIR: './auth_info_baileys',
  WEBHOOK_URL: process.env.WEBHOOK_URL || 'http://localhost:5000/api/webhook/message',
  PORT: process.env.PORT || 3001,
  LOG_LEVEL: process.env.LOG_LEVEL || 'info',
};

// ===================================
// LOGGER
// ===================================
const logger = {
  info: (...args) => console.log('ℹ️ ', ...args),
  success: (...args) => console.log('✅', ...args),
  error: (...args) => console.error('❌', ...args),
  warn: (...args) => console.warn('⚠️ ', ...args),
  debug: (...args) => CONFIG.LOG_LEVEL === 'debug' && console.log('🔍', ...args),
};

// ===================================
// APLICAÇÃO EXPRESS
// ===================================
const app = express();
app.use(express.json());

let sock = null;
let isReady = false;

// ===================================
// INICIALIZAÇÃO DO BAILEYS
// ===================================
async function connectToWhatsApp() {
  console.log('');
  console.log('='.repeat(60));
  console.log('  CRM WhatsApp - Serviço WhatsApp (Baileys)');
  console.log('='.repeat(60));
  console.log('');
  
  logger.info('Iniciando Baileys...');
  logger.info(`Webhook: ${CONFIG.WEBHOOK_URL}`);
  
  try {
    // Carrega autenticação
    const { state, saveCreds } = await useMultiFileAuthState(CONFIG.SESSION_DIR);
    
    // Versão do Baileys
    const { version } = await fetchLatestBaileysVersion();
    logger.info(`Versão do Baileys: ${version.join('.')}`);
    
    // Cria socket
    sock = makeWASocket({
      version,
      logger: P({ level: 'silent' }),
      printQRInTerminal: false,
      auth: state,
      getMessage: async () => undefined,
    });
    
    // ===================================
    // EVENTOS
    // ===================================
    
    // Salvar credenciais
    sock.ev.on('creds.update', saveCreds);
    
    // QR Code
    sock.ev.on('connection.update', async (update) => {
      const { connection, lastDisconnect, qr } = update;
      
      if (qr) {
        console.log('');
        logger.info('Escaneie o QR Code abaixo:');
        console.log('');
        qrcode.generate(qr, { small: true });
        console.log('');
      }
      
      if (connection === 'close') {
        const shouldReconnect =
          lastDisconnect?.error?.output?.statusCode !== DisconnectReason.loggedOut;
        
        logger.warn('Conexão fechada');
        
        if (shouldReconnect) {
          logger.info('Reconectando...');
          connectToWhatsApp();
        } else {
          logger.error('Desconectado. Faça login novamente.');
          isReady = false;
        }
      } else if (connection === 'open') {
        logger.success('WhatsApp conectado com sucesso!');
        isReady = true;
        
        // Informações da conexão
        try {
          const me = sock.user;
          logger.info(`Conectado como: ${me.id.split(':')[0]}`);
        } catch (err) {
          logger.debug('Não foi possível obter info do usuário');
        }
        
        console.log('');
        console.log('='.repeat(60));
        console.log('🎯 Aguardando mensagens...');
        console.log('='.repeat(60));
        console.log('');
      }
    });
    
    // Mensagens recebidas
    sock.ev.on('messages.upsert', async ({ messages, type }) => {
      console.log('');
      console.log('🔔 EVENTO messages.upsert DISPARADO!');
      console.log('   Type:', type);
      console.log('   Quantidade de mensagens:', messages.length);
      console.log('');
      
      if (type !== 'notify') {
        logger.debug(`Tipo ${type} ignorado (não é notify)`);
        return;
      }
      
      for (const message of messages) {
        handleIncomingMessage(message);
      }
    });
    
  } catch (error) {
    logger.error('Erro ao inicializar Baileys:', error.message);
    process.exit(1);
  }
}

// ===================================
// PROCESSAR MENSAGEM RECEBIDA
// ===================================
async function handleIncomingMessage(message) {
  try {
    console.log('');
    console.log('='.repeat(60));
    console.log('📨 PROCESSANDO MENSAGEM');
    console.log('='.repeat(60));
    
    // Extrai informações
    const remoteJid = message.key.remoteJid;
    const fromMe = message.key.fromMe;
    const messageContent = message.message;
    
    console.log('   remoteJid:', remoteJid);
    console.log('   fromMe:', fromMe);
    console.log('   messageContent:', JSON.stringify(messageContent, null, 2));
    console.log('');
    
    // Filtros
    if (fromMe) {
      logger.info('⏭️  Mensagem própria - ignorada');
      console.log('='.repeat(60));
      console.log('');
      return;
    }
    
    if (remoteJid.endsWith('@g.us')) {
      logger.info('⏭️  Mensagem de grupo - ignorada');
      console.log('='.repeat(60));
      console.log('');
      return;
    }
    
    // Extrai texto
    const text =
      messageContent?.conversation ||
      messageContent?.extendedTextMessage?.text ||
      '';
    
    console.log('   Texto extraído:', text);
    console.log('');
    
    if (!text || text.trim() === '') {
      logger.info('⏭️  Mensagem sem texto - ignorada');
      console.log('='.repeat(60));
      console.log('');
      return;
    }
    
    // Nome do remetente
    const pushName = message.pushName || 'Lead';
    
    console.log('   pushName:', pushName);
    console.log('');
    
    // Prepara payload
    // Extrai apenas o número (remove @s.whatsapp.net)
    const phoneClean = remoteJid.replace('@s.whatsapp.net', '');
    
    const payload = {
      from: phoneClean,  // ✅ SEM @c.us - Flask vai adicionar depois
      body: text,
      notifyName: pushName,
      timestamp: message.messageTimestamp || Date.now(),
      fromMe: fromMe,
    };
    
    logger.info(`📨 Nova mensagem de ${pushName} (${remoteJid})`);
    logger.info(`💬 Conteúdo: ${text.substring(0, 50)}`);
    logger.info(`📞 Telefone para Flask: ${phoneClean}`);
    console.log('');
    console.log('📤 Enviando para webhook...');
    
    // Envia para webhook
    await sendToWebhook(payload);
    
    console.log('='.repeat(60));
    console.log('');
    
  } catch (error) {
    logger.error('Erro ao processar mensagem:', error.message);
    console.error(error.stack);
    console.log('');
  }
}

// ===================================
// ENVIAR PARA WEBHOOK
// ===================================
async function sendToWebhook(payload) {
  try {
    const response = await axios.post(CONFIG.WEBHOOK_URL, payload, {
      headers: { 'Content-Type': 'application/json' },
      timeout: 10000,
    });
    
    logger.success(`Webhook chamado com sucesso (Status: ${response.status})`);
    logger.debug('Resposta:', response.data);
    
  } catch (error) {
    if (error.code === 'ECONNREFUSED') {
      logger.error('Webhook não respondeu - CRM Backend offline?');
    } else if (error.response) {
      logger.error(`Webhook retornou erro ${error.response.status}`);
      logger.debug('Detalhes:', error.response.data);
    } else {
      logger.error('Erro ao chamar webhook:', error.message);
    }
  }
}

// ===================================
// API ENDPOINTS
// ===================================

// Health check
app.get('/health', (req, res) => {
  res.json({
    status: 'ok',
    service: 'whatsapp-service-baileys',
    ready: isReady,
    uptime: process.uptime(),
    timestamp: new Date().toISOString(),
  });
});

// Status da conexão
app.get('/status', (req, res) => {
  res.json({
    connected: isReady,
    phone: isReady && sock?.user ? sock.user.id.split(':')[0] : 'N/A',
    timestamp: new Date().toISOString(),
  });
});

// Enviar mensagem
app.post('/send', async (req, res) => {
  try {
    if (!sock || !isReady) {
      return res.status(503).json({
        success: false,
        error: 'WhatsApp não está conectado',
      });
    }
    
    const { phone, message } = req.body;
    
    if (!phone || !message) {
      return res.status(400).json({
        success: false,
        error: 'Telefone e mensagem são obrigatórios',
      });
    }
    
    logger.info(`📤 Enviando mensagem para ${phone}`);
    
    // Formata número para o padrão Baileys
    let jid = phone;
    
    // Remove caracteres não numéricos
    const phoneClean = phone.replace(/\D/g, '');
    
    // Converte para formato Baileys
    if (!jid.includes('@')) {
      jid = `${phoneClean}@s.whatsapp.net`;
    } else if (jid.includes('@c.us')) {
      // Converte de @c.us para @s.whatsapp.net
      jid = jid.replace('@c.us', '@s.whatsapp.net');
    }
    
    logger.info(`📞 JID formatado: ${jid}`);
    
    await sock.sendMessage(jid, { text: message });
    
    logger.success('Mensagem enviada com sucesso!');
    
    res.json({ success: true });
    
  } catch (error) {
    logger.error('Erro ao enviar mensagem:', error.message);
    res.status(500).json({
      success: false,
      error: error.message,
    });
  }
});

// Testar conexão com backend
app.get('/test-backend', async (req, res) => {
  try {
    const backendUrl = CONFIG.WEBHOOK_URL.replace('/api/webhook/message', '/health');
    const response = await axios.get(backendUrl, { timeout: 5000 });
    
    logger.success('Backend está respondendo!');
    
    res.json({
      backend_online: true,
      backend_response: response.data,
    });
  } catch (error) {
    logger.error('Backend não está respondendo:', error.message);
    
    res.json({
      backend_online: false,
      error: error.message,
    });
  }
});

// ===================================
// INICIALIZAÇÃO
// ===================================
async function start() {
  // Conecta WhatsApp
  await connectToWhatsApp();
  
  // Inicia servidor
  app.listen(CONFIG.PORT, () => {
    logger.success(`Servidor rodando em http://localhost:${CONFIG.PORT}`);
    console.log('');
    console.log('📋 Endpoints disponíveis:');
    console.log(`   GET  /health        - Health check`);
    console.log(`   GET  /status        - Status da conexão`);
    console.log(`   POST /send          - Enviar mensagem`);
    console.log(`   GET  /test-backend  - Testar backend`);
    console.log('');
  });
}

// Tratamento de erros
process.on('unhandledRejection', (error) => {
  logger.error('Unhandled Rejection:', error);
});

process.on('uncaughtException', (error) => {
  logger.error('Uncaught Exception:', error);
  process.exit(1);
});

// Graceful shutdown
process.on('SIGINT', async () => {
  logger.warn('Encerrando serviço...');
  
  if (sock) {
    try {
      await sock.logout();
      logger.info('WhatsApp desconectado');
    } catch (error) {
      logger.error('Erro ao desconectar:', error.message);
    }
  }
  
  process.exit(0);
});

// Inicia aplicação
start().catch((error) => {
  logger.error('Erro fatal:', error);
  process.exit(1);
});