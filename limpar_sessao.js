#!/usr/bin/env node
/**
 * Script para LIMPAR completamente a sessão do VenomBot
 * Use quando quiser reconectar com outro número
 */

const fs = require('fs');
const path = require('path');

console.log('🧹 Limpando sessão do VenomBot...\n');

// Pastas que o VenomBot cria para guardar sessão
const sessionFolders = [
    './tokens',
    './.wwebjs_auth',
    './.wwebjs_cache',
    './session',
    './tokens/veloce-crm',
    './tokens/crm-whatsapp',
];

let cleaned = 0;

sessionFolders.forEach(folder => {
    const folderPath = path.join(__dirname, folder);
    
    if (fs.existsSync(folderPath)) {
        try {
            fs.rmSync(folderPath, { recursive: true, force: true });
            console.log(`✅ Removido: ${folder}`);
            cleaned++;
        } catch (error) {
            console.log(`⚠️  Erro ao remover ${folder}: ${error.message}`);
        }
    } else {
        console.log(`⏭️  Não existe: ${folder}`);
    }
});

console.log(`\n✨ Limpeza concluída! ${cleaned} pasta(s) removida(s)`);
console.log('\n📱 Próximo passo:');
console.log('   1. Execute: npm run dev');
console.log('   2. Escaneie o QR Code com o NOVO WhatsApp');
console.log('   3. Aguarde a conexão');
console.log('   4. Envie uma mensagem de teste\n');