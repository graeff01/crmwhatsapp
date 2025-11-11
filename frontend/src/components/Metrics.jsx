import { useEffect, useState, useMemo } from 'react';
import { 
  LineChart, Line, BarChart, Bar, PieChart, Pie, Cell,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer 
} from 'recharts';
import { 
  TrendingUp, TrendingDown, Users, Target, Clock, Award,
  RefreshCw, Calendar
} from 'lucide-react';
import "../styles/components/metrics.css";
import api from '../api';

export default function Metrics({ currentUser }) {
  const [period, setPeriod] = useState('month');
  const [vendedorId, setVendedorId] = useState('');
  const [vendedores, setVendedores] = useState([]);
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  const periods = [
    { key: 'day', label: 'Hoje' },
    { key: 'week', label: '7 dias' },
    { key: 'month', label: '30 dias' },
  ];

  useEffect(() => {
    const fetchUsers = async () => {
      if (currentUser?.role === 'admin' || currentUser?.role === 'gestor') {
        const users = await api.getUsers();
        setVendedores(users.filter(u => u.role === 'vendedor' && u.active));
      }
    };
    fetchUsers();
  }, [currentUser]);

  const fetchMetrics = async () => {
    setLoading(true);
    try {
      const response = await api.getMetrics(period, vendedorId || null);
      setData(response);
    } catch (err) {
      console.error('Erro ao carregar métricas', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
  if (data && !data.insights) {
    data.insights = [
      { type: 'positive', message: 'Taxa de conversão subiu 12% nesta semana 🚀' },
      { type: 'negative', message: 'Tempo médio de resposta aumentou 15% ⏱️' },
      { type: 'neutral', message: 'João foi o vendedor com mais ganhos no período 🏆' },
    ];
  }
}, [data]);


  useEffect(() => {
    fetchMetrics();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [period, vendedorId]);

  const funilArray = useMemo(() => {
    if (!data?.funil) return [];
    return [
      { status: 'Novo', value: data.funil.novo || 0, color: '#667eea' },
      { status: 'Em Atendimento', value: data.funil.em_atendimento || 0, color: '#ffc107' },
      { status: 'Qualificado', value: data.funil.qualificado || 0, color: '#00d4aa' },
      { status: 'Ganho', value: data.funil.ganho || 0, color: '#4caf50' },
      { status: 'Perdido', value: data.funil.perdido || 0, color: '#f44336' },
    ];
  }, [data]);

  const pieData = useMemo(() => {
    if (!data?.funil) return [];
    return [
      { name: 'Novo', value: data.funil.novo || 0, color: '#667eea' },
      { name: 'Atendimento', value: data.funil.em_atendimento || 0, color: '#ffc107' },
      { name: 'Qualificado', value: data.funil.qualificado || 0, color: '#00d4aa' },
      { name: 'Ganho', value: data.funil.ganho || 0, color: '#4caf50' },
      { name: 'Perdido', value: data.funil.perdido || 0, color: '#f44336' },
    ].filter(i => i.value > 0);
  }, [data]);

  const conversaoEtapas = useMemo(() => {
    if (!data?.funil) return [];
    return [
      {
        etapa: 'Novo → Atendimento',
        taxa: ((data.funil.em_atendimento / (data.funil.novo + data.funil.em_atendimento)) * 100 || 0).toFixed(1)
      },
      {
        etapa: 'Atendimento → Qualificado',
        taxa: ((data.funil.qualificado / (data.funil.em_atendimento + data.funil.qualificado)) * 100 || 0).toFixed(1)
      },
      {
        etapa: 'Qualificado → Ganho',
        taxa: ((data.funil.ganho / (data.funil.qualificado + data.funil.ganho)) * 100 || 0).toFixed(1)
      },
    ];
  }, [data]);

  if (loading) {
    return (
      <section className="metrics-page">
        <div className="loading-dashboard">
          <RefreshCw className="spin" size={48} />
          <p>Carregando métricas...</p>
        </div>
      </section>
    );
  }

  return (
    <section className="metrics-page">
      <div className="metrics-container">
        {/* Cabeçalho */}
        <header className="metrics-header">
          <h2>📊 Painel de Desempenho</h2>
          <p className="metrics-sub">Acompanhe os principais indicadores de vendas e performance em tempo real</p>
        </header>

        {/* Filtros */}
        <div className="metrics-filters-premium">
          <div className="filter-group">
            <Calendar size={18} />
            <select value={period} onChange={e => setPeriod(e.target.value)}>
              {periods.map(p => (
                <option key={p.key} value={p.key}>{p.label}</option>
              ))}
            </select>
          </div>

          {(currentUser?.role === 'admin' || currentUser?.role === 'gestor') && (
            <div className="filter-group">
              <Users size={18} />
              <select value={vendedorId} onChange={e => setVendedorId(e.target.value)}>
                <option value="">Todos os vendedores</option>
                {vendedores.map(v => (
                  <option key={v.id} value={v.id}>{v.name}</option>
                ))}
              </select>
            </div>
          )}

          <button className="btn-refresh" onClick={fetchMetrics}>
            <RefreshCw size={16} />
            Atualizar
          </button>
        </div>

        {/* KPIs */}
        <div className="kpi-grid-premium">
          <div className="kpi-card-premium">
            <div className="kpi-icon" style={{ background: 'rgba(102,126,234,0.15)' }}>
              <Users size={24} color="#667eea" />
            </div>
            <div className="kpi-content">
              <div className="kpi-label">Total de Leads</div>
              <div className="kpi-value-premium">{data?.total_leads || 0}</div>
              <div className="kpi-trend positive"><TrendingUp size={14} /><span>+12% vs período anterior</span></div>
            </div>
          </div>

          <div className="kpi-card-premium">
            <div className="kpi-icon" style={{ background: 'rgba(76,175,80,0.15)' }}>
              <Target size={24} color="#4caf50" />
            </div>
            <div className="kpi-content">
              <div className="kpi-label">Leads Ganhos</div>
              <div className="kpi-value-premium">{data?.leads_ganhos || 0}</div>
              <div className="kpi-trend positive"><TrendingUp size={14} /><span>+8% vs período anterior</span></div>
            </div>
          </div>

          <div className="kpi-card-premium">
            <div className="kpi-icon" style={{ background: 'rgba(0,212,170,0.15)' }}>
              <Award size={24} color="#00d4aa" />
            </div>
            <div className="kpi-content">
              <div className="kpi-label">Taxa de Conversão</div>
              <div className="kpi-value-premium">{data?.taxa_conversao || 0}%</div>
              <div className="kpi-trend positive"><TrendingUp size={14} /><span>+3.2% vs período anterior</span></div>
            </div>
          </div>

          <div className="kpi-card-premium">
            <div className="kpi-icon" style={{ background: 'rgba(255,193,7,0.15)' }}>
              <Clock size={24} color="#ffc107" />
            </div>
            <div className="kpi-content">
              <div className="kpi-label">Tempo Médio Resposta</div>
              <div className="kpi-value-premium">{data?.tempo_resposta || 0} min</div>
              <div className="kpi-trend negative"><TrendingDown size={14} /><span>-15% vs período anterior</span></div>
            </div>
          </div>
        </div>

        {/* ===== INSIGHT CARDS ===== */}
{data?.insights && data.insights.length > 0 && (
  <div className="insights-container">
    {data.insights.map((insight, index) => (
      <div key={index} className={`insight-card ${insight.type}`}>
        <div className="insight-icon">
          {insight.type === 'positive' && <TrendingUp size={18} color="#00d95f" />}
          {insight.type === 'negative' && <TrendingDown size={18} color="#ef4444" />}
          {insight.type === 'neutral' && <Award size={18} color="#00a884" />}
        </div>
        <p>{insight.message}</p>
      </div>
    ))}
  </div>
)}


        {/* GRÁFICOS – linha 1 */}
        <div className="charts-grid">
          <div className="chart-card">
            <div className="chart-header">
              <h3>🎯 Funil de Conversão</h3>
              <p>Distribuição de leads por etapa</p>
            </div>
            <div className="chart-content">
              <ResponsiveContainer width="100%" height={220}>
                <BarChart data={funilArray}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#2a3942" />
                  <XAxis dataKey="status" stroke="#8696a0" />
                  <YAxis stroke="#8696a0" />
                  <Tooltip contentStyle={{ background: '#202c33', border: '1px solid #2a3942', borderRadius: '8px' }} />
                  <Bar dataKey="value" radius={[8,8,0,0]}>
                    {funilArray.map((e,i)=><Cell key={i} fill={e.color}/>)}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>

          <div className="chart-card">
            <div className="chart-header">
              <h3>📊 Distribuição de Status</h3>
              <p>Proporção de leads por status</p>
            </div>
            <div className="chart-content">
              <ResponsiveContainer width="100%" height={220}>
                <PieChart>
                  <Pie data={pieData} cx="50%" cy="50%" outerRadius={100} dataKey="value" labelLine={false}
                       label={({name,percent})=>`${name}: ${(percent*100).toFixed(0)}%`}>
                    {pieData.map((e,i)=><Cell key={i} fill={e.color}/>)}
                  </Pie>
                  <Tooltip contentStyle={{ background: '#202c33', border: '1px solid #2a3942', borderRadius: '8px' }} />
                </PieChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>

        {/* GRÁFICOS – linha 2 */}
        <div className="charts-grid">
          <div className="chart-card">
            <div className="chart-header">
              <h3>📈 Taxa de Conversão por Etapa</h3>
              <p>Eficiência de conversão entre fases do funil</p>
            </div>
            <div className="chart-content">
              <ResponsiveContainer width="100%" height={220}>
                <BarChart data={conversaoEtapas} layout="vertical">
                  <CartesianGrid strokeDasharray="3 3" stroke="#2a3942" />
                  <XAxis type="number" stroke="#8696a0" />
                  <YAxis dataKey="etapa" type="category" stroke="#8696a0" width={160} />
                  <Tooltip contentStyle={{ background: '#202c33', border: '1px solid #2a3942', borderRadius: '8px' }} />
                  <Bar dataKey="taxa" fill="#00d4aa" radius={[0,8,8,0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>

          <div className="chart-card">
            <div className="chart-header">
              <h3>🏆 Ranking de Vendedores</h3>
              <p>Top performers do período</p>
            </div>
            <div className="ranking-premium">
              {(data?.ranking || []).map((r,i)=>(
                <div key={i} className="ranking-item">
                  <div className="ranking-position">
                    {i===0?'🥇':i===1?'🥈':i===2?'🥉':`#${i+1}`}
                  </div>
                  <div className="ranking-info">
                    <div className="ranking-name">{r.name}</div>
                    <div className="ranking-stats">
                      <span>{r.ganhos} ganhos</span><span>•</span><span>{r.taxa}% taxa</span>
                    </div>
                  </div>
                  <div className="ranking-progress">
                    <div className="ranking-progress-bar" style={{ width:`${r.taxa}%` }}/>
                  </div>
                </div>
              ))}
              {(!data?.ranking || data.ranking.length===0) && (
                <div className="empty-state">
                  <Users size={48} color="#555" />
                  <p>Nenhum dado disponível no período selecionado</p>
                </div>
              )}
            </div>
          </div>
        </div>

      </div>
    </section>
  );
}
