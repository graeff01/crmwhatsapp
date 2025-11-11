/**
 * 🚀 Integração entre VenomBot e CRM Flask (localhost:5000)
 * Atualizado para remover leads fakes e enviar mensagens reais do WhatsApp
 */

import venom from 'venom-bot';
import express from 'express';
import bodyParser from 'body-parser';
import fetch from 'node-fetch';

const app = express();
app.use(bodyParser.json());

const FLASK_URL = 'http://localhost:5000/api/webhook/message'; // Endpoint do Flask
const PORT = 3001;

// ============================
// 1️⃣ INICIALIZAÇÃO DO VENOM
// ============================
console.log('⚙️ Iniciando VenomBot...');

venom
  .create({
    session: 'veloce-crm',
    multidevice: true,
    headless: false, // navegador visível para debug
    logQR: true,
  })
  .then((client) => start(client))
  .catch((error) => {
    console.error('❌ Erro ao iniciar Venom:', error);
  });

// ============================
// 2️⃣ FUNÇÃO PRINCIPAL
// ============================
function start(client) {
  console.log(`✅ VenomBot inicializado com sucesso!`);
  console.log(`🎯 Aguardando mensagens do WhatsApp...`);

  // ============================
  // 🔁 HEALTH CHECK
  // ============================
  app.get('/status', async (req, res) => {
    try {
      const state = await client.getConnectionState();
      res.json({
        connected: state === 'CONNECTED',
        phone: client.session,
        state,
      });
    } catch (error) {
      res.status(500).json({ connected: false, error: error.message });
    }
  });

  // ============================
  // ✉️ RECEBER MENSAGEM DO WHATSAPP
  // ============================
  client.onMessage(async (message) => {
    try {
      // Ignora mensagens enviadas pelo próprio número
      if (message.fromMe) return;

      // Limpar número do WhatsApp
      const rawPhone = message.from || '';
      const phone = rawPhone.replace('@c.us', '').replace('+', '').trim();
      const content = (message.body || '').trim();
      const name = message.notifyName || message.sender?.pushname || 'Lead';

      if (!phone || !content) return;

      console.log('======================================================================');
      console.log('💬 MENSAGEM RECEBIDA');
      console.log('======================================================================');
      console.log(`📱 De: ${name} (${phone})`);
      console.log(`💬 Conteúdo: ${content}`);
      console.log('======================================================================');

      // Envia pro Flask
      const payload = { phone, content, name };

      const response = await fetch(FLASK_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });

      if (response.ok) {
        console.log(`✅ Mensagem enviada ao Flask (${FLASK_URL}) com sucesso`);
      } else {
        const errorText = await response.text();
        console.error(`❌ Erro ao enviar pro Flask: ${response.status} - ${errorText}`);
      }
    } catch (error) {
      console.error('❌ Erro no processamento da mensagem:', error);
    }
  });

  // ============================
  // 🚀 TESTE DE ENVIO MANUAL
  // ============================
  app.post('/send', async (req, res) => {
    const { phone, message } = req.body;
    if (!phone || !message) {
      return res.status(400).json({ error: 'Faltam parâmetros (phone, message)' });
    }

    try {
      const to = `${phone}@c.us`;
      await client.sendText(to, message);
      console.log(`📤 Mensagem enviada para ${phone}: ${message}`);
      res.json({ success: true });
    } catch (error) {
      console.error('❌ Erro ao enviar mensagem:', error);
      res.status(500).json({ success: false, error: error.message });
    }
  });

  // ============================
  // 🔌 DESCONECTAR MANUALMENTE
  // ============================
  app.post('/disconnect', async (req, res) => {
    try {
      await client.logout();
      console.log('🔌 VenomBot desconectado manualmente.');
      res.json({ success: true });
    } catch (error) {
      console.error('❌ Erro ao desconectar:', error);
      res.status(500).json({ success: false, error: error.message });
    }
  });

  // ============================
  // 🧠 TESTE DE COMUNICAÇÃO COM FLASK
  // ============================
  app.get('/test-flask', async (req, res) => {
    try {
      const response = await fetch('http://localhost:5000/health');
      const data = await response.json();
      res.json({
        flask_online: true,
        flask_response: data,
      });
    } catch (error) {
      res.json({
        flask_online: false,
        error: error.message,
      });
    }
  });

  // ============================
  // 🌐 INICIALIZAR SERVIDOR EXPRESS
  // ============================
  app.listen(PORT, () => {
    console.log(`🚀 Servidor Venom rodando em http://localhost:${PORT}`);
  });
}
