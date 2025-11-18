import axios from "axios";

const API_URL = "http://localhost:5000/api";

// Configura axios para manter sessão autenticada
axios.defaults.withCredentials = true;

const api = {
  // =============================
  // 🔐 AUTENTICAÇÃO
  // =============================
  login: async (username, password) => {
    const response = await axios.post(`${API_URL}/login`, { username, password });
    return response.data;
  },

  logout: async () => {
    const response = await axios.post(`${API_URL}/logout`);
    return response.data;
  },

  getCurrentUser: async () => {
    const response = await axios.get(`${API_URL}/me`);
    return response.data;
  },

  // =============================
  // 👤 USUÁRIOS
  // =============================
  getUsers: async () => {
    const response = await axios.get(`${API_URL}/users`);
    return response.data;
  },

  createUser: async (userData) => {
    const response = await axios.post(`${API_URL}/users`, userData);
    return response.data;
  },

  updateUser: async (userId, userData) => {
    const response = await axios.put(`${API_URL}/users/${userId}`, userData);
    return response.data;
  },

  deleteUser: async (userId) => {
    const response = await axios.delete(`${API_URL}/users/${userId}`);
    return response.data;
  },

  changePassword: async (userId, newPassword) => {
    const response = await axios.put(`${API_URL}/users/${userId}/password`, {
      new_password: newPassword,
    });
    return response.data;
  },

  // =============================
  // 💬 LEADS
  // =============================
  getLeads: async () => {
    const response = await axios.get(`${API_URL}/leads`);
    return response.data;
  },

  getLeadsQueue: async () => {
    const response = await axios.get(`${API_URL}/leads/queue`);
    return response.data;
  },

  assignLead: async (leadId) => {
    const response = await axios.post(`${API_URL}/leads/${leadId}/assign`);
    return response.data;
  },

  updateLeadStatus: async (leadId, status) => {
    const response = await axios.put(`${API_URL}/leads/${leadId}/status`, { status });
    return response.data;
  },

  transferLead: async (leadId, vendedorId) => {
    const response = await axios.post(`${API_URL}/leads/${leadId}/transfer`, {
      vendedor_id: vendedorId,
    });
    return response.data;
  },

  // =============================
  // 🧾 MENSAGENS
  // =============================
  getMessages: async (leadId) => {
    const response = await axios.get(`${API_URL}/leads/${leadId}/messages`);
    return response.data;
  },

  sendMessage: async (leadId, content) => {
    const response = await axios.post(`${API_URL}/leads/${leadId}/messages`, { content });
    return response.data;
  },

// =============================
  // 🗒️ NOTAS INTERNAS
  // =============================
  getNotes: async (leadId) => {
    const response = await axios.get(`${API_URL}/leads/${leadId}/notes`);
    return response.data;
  },

  addNote: async (leadId, note) => {
  const response = await axios.post(`${API_URL}/leads/${leadId}/notes`, { note });
  return response.data;
},

  // =============================
  // 📜 TIMELINE DO LEAD
  // =============================
  getLeadLogs: async (leadId) => {
    const response = await axios.get(`${API_URL}/lead/${leadId}/logs`);
    return response.data;
  },

  // =============================
  // 📊 MÉTRICAS
  // =============================
  getMetrics: async (period = "month", vendedorId = null) => {
    const params = { period };
    if (vendedorId) params.vendedor_id = vendedorId;
    const response = await axios.get(`${API_URL}/metrics`, { params });
    return response.data;
  },

  // =============================
  // 📞 WHATSAPP
  // =============================
  getWhatsAppStatus: async () => {
    const response = await axios.get(`${API_URL}/whatsapp/status`);
    return response.data;
  },

  // =============================
  // 🧩 LOGS DE AUDITORIA
  // =============================
  getAuditLog: async (params = {}) => {
    const response = await axios.get(`${API_URL}/audit-log`, { params });
    return response.data;
  },
  

  // =============================
  // 🧪 SIMULADOR (modo DEV)
  // =============================
  simulateMessage: async (phone, content, name) => {
    const response = await axios.post(`${API_URL}/simulate/message`, {
      phone,
      content,
      name,
    });
    return response.data;
  },
  // =============================
  // 🏷️ TAGS
  // =============================
  getAllTags: async () => {
    const response = await axios.get(`${API_URL}/tags`);
    return response.data;
  },

  getLeadTags: async (leadId) => {
    const response = await axios.get(`${API_URL}/leads/${leadId}/tags`);
    return response.data;
  },

  addTagToLead: async (leadId, tagId) => {
    const response = await axios.post(`${API_URL}/leads/${leadId}/tags`, { 
      tag_id: tagId 
    });
    return response.data;
  },

  removeTagFromLead: async (leadId, tagId) => {
    const response = await axios.delete(`${API_URL}/leads/${leadId}/tags/${tagId}`);
    return response.data;
  },

  createTag: async (tagData) => {
    const response = await axios.post(`${API_URL}/tags`, tagData);
    return response.data;
  },

  // =============================
  // ⏱️ SLA
  // =============================
  getLeadSLA: async (leadId) => {
    const response = await axios.get(`${API_URL}/leads/${leadId}/sla`);
    return response.data;
  },

  getSLAMetrics: async () => {
    const response = await axios.get(`${API_URL}/sla/metrics`);
    return response.data;
  },

  getSLAAlerts: async (threshold = 5) => {
    const response = await axios.get(`${API_URL}/sla/alerts`, {
      params: { threshold }
    });
    return response.data;
  },

  // =============================
  // 📱 NOTIFICAÇÕES WHATSAPP GESTOR
  // =============================
  getGestorWhatsAppConfig: async () => {
    const response = await axios.get(`${API_URL}/gestores/whatsapp-config`);
    return response.data;
  },

  setGestorWhatsAppConfig: async (config) => {
    const response = await axios.post(`${API_URL}/gestores/whatsapp-config`, config);
    return response.data;
  },

  testGestorWhatsApp: async () => {
    const response = await axios.post(`${API_URL}/gestores/whatsapp-config/test`);
    return response.data;
  },

  disableGestorWhatsApp: async () => {
    const response = await axios.delete(`${API_URL}/gestores/whatsapp-config`);
    return response.data;
  },

  getGestorStats: async () => {
    const response = await axios.get(`${API_URL}/gestores/stats`);
    return response.data;
  },

  // =============================
  // 🤖 IA DASHBOARD
  // =============================
  getAIStats: async () => {
    const response = await axios.get(`${API_URL}/ai/stats`);
    return response.data;
  },

  getAIActiveConversations: async () => {
    const response = await axios.get(`${API_URL}/ai/conversations/active`);
    return response.data;
  },

  getAIConversation: async (phone) => {
    const response = await axios.get(`${API_URL}/ai/conversations/${phone}`);
    return response.data;
  },

  escalateAIConversation: async (phone) => {
    const response = await axios.post(`${API_URL}/ai/conversations/${phone}/escalate`);
    return response.data;
  },

  endAIConversation: async (phone, reason = 'Manual') => {
    const response = await axios.post(`${API_URL}/ai/conversations/${phone}/end`, { reason });
    return response.data;
  },

  getAIPerformance: async () => {
    const response = await axios.get(`${API_URL}/ai/performance`);
    return response.data;
  },
};



export default api;
