import React, { useState, useEffect } from 'react';
import axios from 'axios';
import '../styles/components/Sladashboard.css';



/**
 * Dashboard com métricas de SLA
 */
const SLADashboard = () => {
  const [metrics, setMetrics] = useState(null);
  const [alerts, setAlerts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [threshold, setThreshold] = useState(5);

  useEffect(() => {
    loadData();
    
    // Atualizar a cada 30 segundos
    const interval = setInterval(loadData, 30000);
    return () => clearInterval(interval);
  }, [threshold]);

  const loadData = async () => {
    try {
      const [metricsRes, alertsRes] = await Promise.all([
        axios.get('http://localhost:5000/api/sla/metrics', { withCredentials: true }),
        axios.get(`http://localhost:5000/api/sla/alerts?threshold=${threshold}`, { withCredentials: true })
      ]);

      setMetrics(metricsRes.data);
      setAlerts(alertsRes.data.leads || []);
    } catch (error) {
      console.error('Erro ao carregar métricas SLA:', error);
    } finally {
      setLoading(false);
    }
  };

  const getSLAStatus = (rate) => {
    if (rate >= 90) return { color: '#4CAF50', label: 'Excelente' };
    if (rate >= 75) return { color: '#FF9800', label: 'Bom' };
    if (rate >= 60) return { color: '#FF5722', label: 'Atenção' };
    return { color: '#F44336', label: 'Crítico' };
  };

  if (loading) {
    return <div className="sla-loading">⏱️ Carregando métricas...</div>;
  }

  if (!metrics) {
    return <div className="sla-error">Erro ao carregar métricas</div>;
  }

  const slaStatus = getSLAStatus(metrics.sla_compliance_rate || 0);

  return (
    <div className="sla-dashboard">
      <div className="sla-header">
        <h2>⏱️ Métricas de SLA</h2>
        <div className="sla-threshold">
          <label>Limite de alerta:</label>
          <select value={threshold} onChange={(e) => setThreshold(Number(e.target.value))}>
            <option value={3}>3 minutos</option>
            <option value={5}>5 minutos</option>
            <option value={10}>10 minutos</option>
            <option value={15}>15 minutos</option>
            <option value={30}>30 minutos</option>
          </select>
        </div>
      </div>

      {/* Cards de Métricas */}
      <div className="metrics-grid">
        {/* Taxa de Cumprimento */}
        <div className="metric-card metric-highlight">
          <div className="metric-icon">🎯</div>
          <div className="metric-content">
            <div className="metric-label">Taxa de Cumprimento</div>
            <div className="metric-value" style={{ color: slaStatus.color }}>
              {metrics.sla_compliance_rate?.toFixed(1) || 0}%
            </div>
            <div className="metric-status" style={{ color: slaStatus.color }}>
              {slaStatus.label}
            </div>
          </div>
        </div>

        {/* Primeira Resposta */}
        <div className="metric-card">
          <div className="metric-icon">⚡</div>
          <div className="metric-content">
            <div className="metric-label">Tempo Médio Primeira Resposta</div>
            <div className="metric-value">
              {metrics.avg_first_response_formatted || 'N/A'}
            </div>
            <div className="metric-detail">
              {metrics.avg_first_response ? 
                `${Math.round(metrics.avg_first_response)} segundos` : 
                'Sem dados'
              }
            </div>
          </div>
        </div>

        {/* Tempo Médio Geral */}
        <div className="metric-card">
          <div className="metric-icon">📊</div>
          <div className="metric-content">
            <div className="metric-label">Tempo Médio Geral</div>
            <div className="metric-value">
              {metrics.avg_overall_response_formatted || 'N/A'}
            </div>
            <div className="metric-detail">
              {metrics.avg_overall_response ? 
                `${Math.round(metrics.avg_overall_response)} segundos` : 
                'Sem dados'
              }
            </div>
          </div>
        </div>

        {/* Total de Leads */}
        <div className="metric-card">
          <div className="metric-icon">📈</div>
          <div className="metric-content">
            <div className="metric-label">Total de Leads</div>
            <div className="metric-value">{metrics.total_leads || 0}</div>
            <div className="metric-detail">
              ✅ {metrics.sla_met_count || 0} cumpridos • 
              ❌ {metrics.sla_missed_count || 0} atrasados
            </div>
          </div>
        </div>

        {/* Resposta Mais Rápida */}
        <div className="metric-card metric-success">
          <div className="metric-icon">🚀</div>
          <div className="metric-content">
            <div className="metric-label">Resposta Mais Rápida</div>
            <div className="metric-value">
              {metrics.fastest_response_formatted || 'N/A'}
            </div>
          </div>
        </div>

        {/* Resposta Mais Lenta */}
        <div className="metric-card metric-warning">
          <div className="metric-icon">🐌</div>
          <div className="metric-content">
            <div className="metric-label">Resposta Mais Lenta</div>
            <div className="metric-value">
              {metrics.slowest_response_formatted || 'N/A'}
            </div>
          </div>
        </div>
      </div>

      {/* Alertas de SLA */}
      {alerts.length > 0 && (
        <div className="sla-alerts">
          <div className="alerts-header">
            <h3>🚨 Leads Aguardando Resposta</h3>
            <span className="alert-count">{alerts.length} lead(s)</span>
          </div>
          <div className="alerts-list">
            {alerts.map(lead => (
              <div key={lead.id} className="alert-item">
                <div className="alert-info">
                  <span className="alert-name">{lead.name}</span>
                  <span className="alert-phone">{lead.phone}</span>
                </div>
                <div className="alert-time">
                  <span className="time-elapsed">{lead.elapsed_time_formatted}</span>
                  <span className="time-label">aguardando</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {alerts.length === 0 && (
        <div className="no-alerts">
          ✅ Todos os leads estão dentro do SLA!
        </div>
      )}
    </div>
  );
};

export default SLADashboard;