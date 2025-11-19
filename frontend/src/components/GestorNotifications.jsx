/**
 * Componente de Configuração de Notificações WhatsApp para Gestores
 * Permite configurar telefone e preferências de alertas
 */

import { useState, useEffect } from 'react';
import { Bell, Phone, Check, X, AlertCircle, Send } from 'lucide-react';
import { toast } from './Toast';
import api from '../api';
import '../styles/components/GestorNotifications.css';

export default function GestorNotifications({ currentUser }) {
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [testing, setTesting] = useState(false);
  const [config, setConfig] = useState(null);
  const [formData, setFormData] = useState({
    phone: '',
    receive_critical: true,
    receive_danger: true,
    receive_warning: false
  });

  // Carregar configuração atual
  useEffect(() => {
    loadConfig();
  }, []);

  const loadConfig = async () => {
    try {
      const data = await api.getGestorWhatsAppConfig();
      if (data.config) {
        setConfig(data.config);
        setFormData({
          phone: data.config.phone || '',
          receive_critical: data.config.receive_critical !== 0,
          receive_danger: data.config.receive_danger !== 0,
          receive_warning: data.config.receive_warning !== 0
        });
      }
      setLoading(false);
    } catch (error) {
      console.error('Erro ao carregar config:', error);
      toast.error('Erro ao carregar configurações');
      setLoading(false);
    }
  };

  const handleSave = async () => {
    // Validar telefone
    if (!formData.phone || formData.phone.length < 12) {
      toast.error('Telefone inválido. Use o formato: 5511999999999');
      return;
    }

    if (!formData.phone.startsWith('55')) {
      toast.error('Telefone deve iniciar com 55 (código do Brasil)');
      return;
    }

    setSaving(true);
    try {
      const response = await api.setGestorWhatsAppConfig(formData);
      toast.success(response.message || 'Configurações salvas com sucesso!');
      await loadConfig();
    } catch (error) {
      toast.error(error.message || 'Erro ao salvar configurações');
    } finally {
      setSaving(false);
    }
  };

  const handleTest = async () => {
    if (!config) {
      toast.error('Salve a configuração antes de testar');
      return;
    }

    setTesting(true);
    try {
      const response = await api.testGestorWhatsApp();
      toast.success(response.message || 'Mensagem de teste enviada!');
    } catch (error) {
      toast.error(error.message || 'Erro ao enviar teste');
    } finally {
      setTesting(false);
    }
  };

  const handleDisable = async () => {
    if (!confirm('Deseja realmente desativar as notificações WhatsApp?')) return;

    try {
      await api.disableGestorWhatsApp();
      toast.success('Notificações desativadas');
      setConfig(null);
      setFormData({
        phone: '',
        receive_critical: true,
        receive_danger: true,
        receive_warning: false
      });
    } catch (error) {
      toast.error('Erro ao desativar notificações');
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto p-6">
      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center gap-3 mb-2">
          <Bell className="w-8 h-8 text-blue-600" />
          <h1 className="text-3xl font-bold text-gray-900">Notificações WhatsApp</h1>
        </div>
        <p className="text-gray-600">
          Configure seu telefone para receber alertas críticos do sistema
        </p>
      </div>

      {/* Status Card */}
      {config && config.active && (
        <div className="mb-6 p-4 bg-green-50 border border-green-200 rounded-lg flex items-start gap-3">
          <Check className="w-5 h-5 text-green-600 mt-0.5" />
          <div>
            <div className="font-semibold text-green-900">Notificações Ativas</div>
            <div className="text-sm text-green-700">
              Você receberá alertas no número: {config.phone}
            </div>
          </div>
        </div>
      )}

      {/* Formulário */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <div className="space-y-6">
          {/* Telefone */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              <Phone className="w-4 h-4 inline mr-2" />
              Número do WhatsApp
            </label>
            <input
              type="tel"
              value={formData.phone}
              onChange={(e) => setFormData({ ...formData, phone: e.target.value.replace(/\D/g, '') })}
              placeholder="5511999999999"
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              maxLength="13"
            />
            <p className="text-xs text-gray-500 mt-1">
              Formato: 55 + DDD + Número (ex: 5511999999999)
            </p>
          </div>

          {/* Tipos de Alertas */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-3">
              Tipos de Alertas para Receber
            </label>

            <div className="space-y-3">
              {/* Críticos */}
              <label className="flex items-center gap-3 p-3 border border-gray-200 rounded-lg hover:bg-gray-50 cursor-pointer">
                <input
                  type="checkbox"
                  checked={formData.receive_critical}
                  onChange={(e) => setFormData({ ...formData, receive_critical: e.target.checked })}
                  className="w-4 h-4 text-blue-600 rounded focus:ring-2 focus:ring-blue-500"
                />
                <div className="flex-1">
                  <div className="flex items-center gap-2">
                    <span className="font-medium text-gray-900">Críticos</span>
                    <span className="px-2 py-0.5 text-xs font-medium bg-red-100 text-red-800 rounded">
                      URGENTE
                    </span>
                  </div>
                  <p className="text-sm text-gray-600">
                    Problemas graves que requerem ação imediata
                  </p>
                </div>
              </label>

              {/* Danger */}
              <label className="flex items-center gap-3 p-3 border border-gray-200 rounded-lg hover:bg-gray-50 cursor-pointer">
                <input
                  type="checkbox"
                  checked={formData.receive_danger}
                  onChange={(e) => setFormData({ ...formData, receive_danger: e.target.checked })}
                  className="w-4 h-4 text-blue-600 rounded focus:ring-2 focus:ring-blue-500"
                />
                <div className="flex-1">
                  <div className="flex items-center gap-2">
                    <span className="font-medium text-gray-900">Perigo</span>
                    <span className="px-2 py-0.5 text-xs font-medium bg-orange-100 text-orange-800 rounded">
                      IMPORTANTE
                    </span>
                  </div>
                  <p className="text-sm text-gray-600">
                    SLA estourado, leads abandonados, performance baixa
                  </p>
                </div>
              </label>

              {/* Warning */}
              <label className="flex items-center gap-3 p-3 border border-gray-200 rounded-lg hover:bg-gray-50 cursor-pointer">
                <input
                  type="checkbox"
                  checked={formData.receive_warning}
                  onChange={(e) => setFormData({ ...formData, receive_warning: e.target.checked })}
                  className="w-4 h-4 text-blue-600 rounded focus:ring-2 focus:ring-blue-500"
                />
                <div className="flex-1">
                  <div className="flex items-center gap-2">
                    <span className="font-medium text-gray-900">Avisos</span>
                    <span className="px-2 py-0.5 text-xs font-medium bg-yellow-100 text-yellow-800 rounded">
                      INFORMATIVO
                    </span>
                  </div>
                  <p className="text-sm text-gray-600">
                    Notificações informativas e menos urgentes
                  </p>
                </div>
              </label>
            </div>
          </div>

          {/* Horário Silencioso Info */}
          <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg">
            <div className="flex items-start gap-3">
              <AlertCircle className="w-5 h-5 text-blue-600 mt-0.5" />
              <div>
                <div className="font-medium text-blue-900">Horário Silencioso</div>
                <p className="text-sm text-blue-700 mt-1">
                  Alertas não serão enviados entre 22:00 e 08:00 para respeitar seu descanso.
                </p>
              </div>
            </div>
          </div>

          {/* Ações */}
          <div className="flex gap-3 pt-4 border-t border-gray-200">
            <button
              onClick={handleSave}
              disabled={saving}
              className="flex-1 px-6 py-3 bg-blue-600 text-white font-medium rounded-lg hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors flex items-center justify-center gap-2"
            >
              {saving ? (
                <>
                  <div className="animate-spin rounded-full h-4 w-4 border-2 border-white border-t-transparent"></div>
                  Salvando...
                </>
              ) : (
                <>
                  <Check className="w-5 h-5" />
                  Salvar Configurações
                </>
              )}
            </button>

            {config && (
              <button
                onClick={handleTest}
                disabled={testing}
                className="px-6 py-3 bg-green-600 text-white font-medium rounded-lg hover:bg-green-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors flex items-center gap-2"
              >
                {testing ? (
                  <>
                    <div className="animate-spin rounded-full h-4 w-4 border-2 border-white border-t-transparent"></div>
                    Enviando...
                  </>
                ) : (
                  <>
                    <Send className="w-5 h-5" />
                    Enviar Teste
                  </>
                )}
              </button>
            )}

            {config && (
              <button
                onClick={handleDisable}
                className="px-6 py-3 bg-red-600 text-white font-medium rounded-lg hover:bg-red-700 transition-colors flex items-center gap-2"
              >
                <X className="w-5 h-5" />
                Desativar
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Exemplos de Alertas */}
      <div className="mt-8">
        <h2 className="text-xl font-semibold text-gray-900 mb-4">Exemplos de Alertas</h2>
        <div className="space-y-3">
          <div className="p-4 bg-gray-50 border border-gray-200 rounded-lg">
            <div className="font-mono text-sm text-gray-800 whitespace-pre-line">
              🚨 *ALERTA - CRM WHATSAPP*{'\n'}
              {'\n'}
              ⚠️ *Lead assumido sem resposta*{'\n'}
              {'\n'}
              👤 *Vendedor:* João Silva{'\n'}
              📱 *Lead:* Maria Santos{'\n'}
              ⏱️ *Tempo sem resposta:* 45 minutos{'\n'}
              {'\n'}
              💡 *Sugestão:* Verificar situação
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
