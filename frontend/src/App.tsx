import React, { useState, useEffect } from 'react';
import { Activity, TrendingUp, DollarSign, ShieldAlert, BarChart3, LayoutDashboard, Settings, History, Menu, X } from 'lucide-react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { apiFetch, getAuthToken, setAuthToken, removeAuthToken } from './api';
import Login from './Login';

const SettingsTab = () => {
  const [formData, setFormData] = useState({
    binance_api_key: '',
    binance_api_secret: '',
    gemini_api_key: '',
    telegram_bot_token: '',
    max_risk_per_trade: 0.01,
    trailing_stop_activation: 1.015,
    trailing_stop_distance: 0.015,
    ai_confidence_threshold: 0.5,
    active_assets: 'BTC/USDT,ETH/USDT,SOL/USDT,US100,SPX500,XAU/USD',
    strategy_sensitivity: 0.01
  });
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');

  useEffect(() => {
    apiFetch('http://localhost:8000/api/settings')
      .then(res => res.json())
      .then(data => {
        setFormData({
          binance_api_key: data.binance_api_key || '',
          binance_api_secret: data.binance_api_secret || '',
          gemini_api_key: data.gemini_api_key || '',
          telegram_bot_token: data.telegram_bot_token || '',
          max_risk_per_trade: data.max_risk_per_trade || 0.01,
          trailing_stop_activation: data.trailing_stop_activation || 1.015,
          trailing_stop_distance: data.trailing_stop_distance || 0.015,
          ai_confidence_threshold: data.ai_confidence_threshold || 0.5,
          active_assets: data.active_assets || 'BTC/USDT,ETH/USDT,SOL/USDT,US100,SPX500,XAU/USD',
          strategy_sensitivity: data.strategy_sensitivity || 0.01
        });
      })
      .catch(err => console.error("Erro ao carregar configs:", err));
  }, []);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: (name === 'active_assets' || name.includes('key') || name.includes('secret') || name.includes('token')) ? value : parseFloat(value)
    }));
  };

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setMessage('');
    try {
      const res = await apiFetch('http://localhost:8000/api/settings', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData)
      });
      if (res.ok) {
        setMessage('Configurações salvas com sucesso! O sistema usará os novos valores.');
      } else {
        setMessage('Erro ao salvar configurações.');
      }
    } catch (err) {
      setMessage('Erro de conexão ao salvar.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-3xl mx-auto pb-10">
      <header className="mb-8">
        <h2 className="text-3xl font-semibold mb-1 flex items-center gap-2"><Settings /> Configurações do Sistema</h2>
        <p className="text-slate-400">Configure chaves de API das corretoras, inteligência artificial e limites de risco.</p>
      </header>

      {message && (
        <div className={`p-4 mb-6 rounded-lg font-medium ${message.includes('sucesso') ? 'bg-green-500/10 text-green-500 border border-green-500/20' : 'bg-red-500/10 text-red-500 border border-red-500/20'}`}>
          {message}
        </div>
      )}

      <form onSubmit={handleSave} className="space-y-6">
        <div className="bg-[#1e293b] p-6 rounded-2xl border border-slate-800">
          <h3 className="text-xl font-semibold mb-4 text-slate-200">Parâmetros de Risco</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label className="block text-sm font-medium text-slate-400 mb-2">Risco Máximo por Trade (%)</label>
              <input 
                type="number" 
                step="0.001"
                name="max_risk_per_trade"
                value={formData.max_risk_per_trade}
                onChange={handleChange}
                className="w-full bg-slate-900 border border-slate-700 rounded-lg px-4 py-2 text-slate-200 focus:outline-none focus:border-blue-500"
              />
              <p className="text-xs text-slate-500 mt-1">Exemplo: 0.01 para 1% da banca.</p>
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-400 mb-2">Ativação Trailing Stop</label>
              <input 
                type="number" 
                step="0.001"
                name="trailing_stop_activation"
                value={formData.trailing_stop_activation}
                onChange={handleChange}
                className="w-full bg-slate-900 border border-slate-700 rounded-lg px-4 py-2 text-slate-200 focus:outline-none focus:border-blue-500"
              />
              <p className="text-xs text-slate-500 mt-1">Gatilho (ex: 1.015 = 1.5% de lucro).</p>
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-400 mb-2">Distância Trailing Stop</label>
              <input 
                type="number" 
                step="0.001"
                name="trailing_stop_distance"
                value={formData.trailing_stop_distance}
                onChange={handleChange}
                className="w-full bg-slate-900 border border-slate-700 rounded-lg px-4 py-2 text-slate-200 focus:outline-none focus:border-blue-500"
              />
              <p className="text-xs text-slate-500 mt-1">Distância do topo (ex: 0.015 = 1.5%).</p>
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-400 mb-2">Confiança da IA</label>
              <input 
                type="number" 
                step="0.01"
                name="ai_confidence_threshold"
                value={formData.ai_confidence_threshold}
                onChange={handleChange}
                className="w-full bg-slate-900 border border-slate-700 rounded-lg px-4 py-2 text-slate-200 focus:outline-none focus:border-blue-500"
              />
              <p className="text-xs text-slate-500 mt-1">Confiança mínima (ex: 0.5 = 50%).</p>
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-400 mb-2">Sensibilidade da Estratégia</label>
              <input 
                type="number" 
                step="0.001"
                name="strategy_sensitivity"
                value={formData.strategy_sensitivity}
                onChange={handleChange}
                className="w-full bg-slate-900 border border-slate-700 rounded-lg px-4 py-2 text-slate-200 focus:outline-none focus:border-blue-500"
              />
              <p className="text-xs text-slate-500 mt-1">Gatilho (ex: 0.01 = 1%). Menor = mais agressivo.</p>
            </div>
          </div>
        </div>

        <div className="bg-[#1e293b] p-6 rounded-2xl border border-slate-800">
          <h3 className="text-xl font-semibold mb-4 text-slate-200">Ativos Monitorados</h3>
          <div>
            <label className="block text-sm font-medium text-slate-400 mb-2">Lista de Ativos (Separados por vírgula)</label>
            <textarea 
              name="active_assets"
              value={formData.active_assets}
              onChange={handleChange as any}
              rows={3}
              className="w-full bg-slate-900 border border-slate-700 rounded-lg px-4 py-2 text-slate-200 focus:outline-none focus:border-blue-500"
            />
            <p className="text-xs text-slate-500 mt-1">Ex: BTC/USDT, ETH/USDT, US100</p>
          </div>
        </div>

        <div className="bg-[#1e293b] p-6 rounded-2xl border border-slate-800">
          <h3 className="text-xl font-semibold mb-4 text-slate-200">Corretora (Binance)</h3>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-slate-400 mb-2">API Key</label>
              <input 
                type="password" 
                name="binance_api_key"
                value={formData.binance_api_key}
                onChange={handleChange}
                placeholder="Cole sua API Key aqui..."
                className="w-full bg-slate-900 border border-slate-700 rounded-lg px-4 py-2 text-slate-200 focus:outline-none focus:border-blue-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-400 mb-2">API Secret</label>
              <input 
                type="password" 
                name="binance_api_secret"
                value={formData.binance_api_secret}
                onChange={handleChange}
                placeholder="Cole seu API Secret aqui..."
                className="w-full bg-slate-900 border border-slate-700 rounded-lg px-4 py-2 text-slate-200 focus:outline-none focus:border-blue-500"
              />
            </div>
          </div>
        </div>

        <div className="bg-[#1e293b] p-6 rounded-2xl border border-slate-800">
          <h3 className="text-xl font-semibold mb-4 text-slate-200">Inteligência Artificial (Gemini)</h3>
          <div>
            <label className="block text-sm font-medium text-slate-400 mb-2">Gemini API Key</label>
            <input 
              type="password" 
              name="gemini_api_key"
              value={formData.gemini_api_key}
              onChange={handleChange}
              placeholder="Chave do Google AI Studio..."
              className="w-full bg-slate-900 border border-slate-700 rounded-lg px-4 py-2 text-slate-200 focus:outline-none focus:border-blue-500"
            />
          </div>
        </div>

        <div className="bg-[#1e293b] p-6 rounded-2xl border border-slate-800">
          <h3 className="text-xl font-semibold mb-4 text-slate-200">Notificações (Telegram)</h3>
          <div>
            <label className="block text-sm font-medium text-slate-400 mb-2">Bot Token</label>
            <input 
              type="password" 
              name="telegram_bot_token"
              value={formData.telegram_bot_token}
              onChange={handleChange}
              placeholder="Token do BotFather..."
              className="w-full bg-slate-900 border border-slate-700 rounded-lg px-4 py-2 text-slate-200 focus:outline-none focus:border-blue-500"
            />
          </div>
        </div>

        <div className="flex justify-end">
          <button 
            type="submit" 
            disabled={loading}
            className="px-6 py-3 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white rounded-lg transition-colors font-bold shadow-lg shadow-blue-500/20"
          >
            {loading ? 'Salvando...' : 'Salvar Configurações'}
          </button>
        </div>
      </form>
    </div>
  );
};

const BacktestTab = () => {
  const [formData, setFormData] = useState({ asset: 'BTC/USD', days: 30, initial_balance: 10000 });
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [error, setError] = useState('');

  const runBacktest = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    setResult(null);
    try {
      const res = await apiFetch('http://localhost:8000/api/backtest', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData)
      });
      const data = await res.json();
      if (res.ok) {
        setResult(data);
      } else {
        setError(data.detail || 'Erro ao rodar backtest');
      }
    } catch (err) {
      setError('Erro de conexão ao rodar backtest.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto pb-10">
      <header className="mb-8">
        <h2 className="text-3xl font-semibold mb-1 flex items-center gap-2"><History /> Motor de Backtesting</h2>
        <p className="text-slate-400">Simule estratégias do robô no passado sem arriscar capital real.</p>
      </header>

      {error && (
        <div className="p-4 mb-6 rounded-lg font-medium bg-red-500/10 text-red-500 border border-red-500/20">
          {error}
        </div>
      )}

      <form onSubmit={runBacktest} className="bg-[#1e293b] p-6 rounded-2xl border border-slate-800 mb-8 space-y-6">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div>
            <label className="block text-sm font-medium text-slate-400 mb-2">Ativo (Ex: BTC/USD)</label>
            <input 
              type="text" 
              value={formData.asset}
              onChange={(e) => setFormData({...formData, asset: e.target.value})}
              className="w-full bg-slate-900 border border-slate-700 rounded-lg px-4 py-2 text-slate-200 focus:outline-none focus:border-blue-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-400 mb-2">Período (Dias Passados)</label>
            <input 
              type="number" 
              value={formData.days}
              onChange={(e) => setFormData({...formData, days: parseInt(e.target.value)})}
              className="w-full bg-slate-900 border border-slate-700 rounded-lg px-4 py-2 text-slate-200 focus:outline-none focus:border-blue-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-400 mb-2">Saldo Inicial ($)</label>
            <input 
              type="number" 
              value={formData.initial_balance}
              onChange={(e) => setFormData({...formData, initial_balance: parseFloat(e.target.value)})}
              className="w-full bg-slate-900 border border-slate-700 rounded-lg px-4 py-2 text-slate-200 focus:outline-none focus:border-blue-500"
            />
          </div>
        </div>
        <div className="flex justify-end">
          <button 
            type="submit" 
            disabled={loading}
            className="px-6 py-3 bg-purple-600 hover:bg-purple-700 disabled:opacity-50 text-white rounded-lg transition-colors font-bold shadow-lg shadow-purple-500/20"
          >
            {loading ? 'Simulando...' : 'Rodar Backtest'}
          </button>
        </div>
      </form>

      {result && (
        <div className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
             <div className="bg-[#1e293b] p-6 rounded-2xl border border-slate-800">
               <div className="text-sm text-slate-400 mb-2">Saldo Final</div>
               <div className={`text-2xl font-bold ${result.final_balance > result.initial_balance ? 'text-green-500' : 'text-red-500'}`}>
                 $ {result.final_balance.toLocaleString()}
               </div>
             </div>
             <div className="bg-[#1e293b] p-6 rounded-2xl border border-slate-800">
               <div className="text-sm text-slate-400 mb-2">Total de Operações</div>
               <div className="text-2xl font-bold">{result.total_trades}</div>
             </div>
             <div className="bg-[#1e293b] p-6 rounded-2xl border border-slate-800">
               <div className="text-sm text-slate-400 mb-2">Taxa de Acerto (Win Rate)</div>
               <div className="text-2xl font-bold">{result.win_rate}%</div>
             </div>
          </div>
          
          <div className="bg-[#1e293b] p-6 rounded-2xl border border-slate-800 h-80">
             <h3 className="text-lg font-semibold mb-4">Curva de Capital (Equity Curve)</h3>
             <ResponsiveContainer width="100%" height="80%">
                <LineChart data={result.equity_curve}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                  <XAxis dataKey="date" stroke="#94a3b8" fontSize={12} tickFormatter={(tick) => tick.split(' ')[0]} />
                  <YAxis stroke="#94a3b8" domain={['auto', 'auto']} />
                  <Tooltip contentStyle={{backgroundColor: '#1e293b', borderColor: '#334155'}} />
                  <Line type="monotone" dataKey="equity" stroke="#a855f7" strokeWidth={2} dot={false} />
                </LineChart>
             </ResponsiveContainer>
          </div>
        </div>
      )}
    </div>
  );
};

function App() {
  const [stats, setStats] = useState<any>(null);
  const [markets, setMarkets] = useState<any[]>([]);
  const [history, setHistory] = useState<any[]>([]);
  const [risk, setRisk] = useState<any>(null);
  const [activeTab, setActiveTab] = useState('dashboard');
  const [loading, setLoading] = useState(true);
  const [isAuthenticated, setIsAuthenticated] = useState<boolean>(!!getAuthToken());
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  useEffect(() => {
    const handleAuthError = () => {
      setIsAuthenticated(false);
    };
    window.addEventListener('auth_error', handleAuthError);
    return () => window.removeEventListener('auth_error', handleAuthError);
  }, []);

  useEffect(() => {
    if (!isAuthenticated) return;
    // Busca os dados do backend
    const fetchData = async () => {
      try {
        const statsRes = await apiFetch('http://localhost:8000/api/dashboard');
        const marketsRes = await apiFetch('http://localhost:8000/api/markets');
        const historyRes = await apiFetch('http://localhost:8000/api/trades/history');
        const riskRes = await apiFetch('http://localhost:8000/api/risk');
        
        if (statsRes.ok) setStats(await statsRes.json());
        if (marketsRes.ok) setMarkets(await marketsRes.json());
        if (historyRes.ok) setHistory(await historyRes.json());
        if (riskRes.ok) setRisk(await riskRes.json());
      } catch (error) {
        console.error("Erro ao buscar dados:", error);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
    const interval = setInterval(fetchData, 3000); // Polling rapido para simulacao
    return () => clearInterval(interval);
  }, [isAuthenticated]);

  const handleLogout = () => {
    removeAuthToken();
    setIsAuthenticated(false);
  };

  if (!isAuthenticated) {
    return (
      <Login 
        onLogin={(token) => {
          setAuthToken(token);
          setIsAuthenticated(true);
        }} 
      />
    );
  }

  const deleteTrade = async (id: number) => {
    if (window.confirm("Deseja realmente excluir esta operação do histórico?")) {
      try {
        const res = await apiFetch(`http://localhost:8000/api/trades/${id}`, { method: 'DELETE' });
        if (res.ok) {
          setHistory(prev => prev.filter(t => t.id !== id));
        } else {
          alert('Erro ao excluir operação.');
        }
      } catch (e) {
        console.error("Erro ao excluir", e);
        alert('Erro ao excluir operação.');
      }
    }
  };

  return (
    <div className="min-h-screen bg-[#0f172a] text-slate-50 flex flex-col md:flex-row">
      {/* Mobile Top Bar */}
      <div className="md:hidden bg-[#1e293b] border-b border-slate-800 p-4 flex items-center justify-between sticky top-0 z-50">
        <div className="flex items-center gap-3">
          <Activity className="text-blue-500" size={24} />
          <h1 className="text-lg font-bold tracking-wider">AI TRADER</h1>
        </div>
        <button onClick={() => setMobileMenuOpen(!mobileMenuOpen)} className="text-slate-400 hover:text-white">
          {mobileMenuOpen ? <X size={24} /> : <Menu size={24} />}
        </button>
      </div>

      {/* Mobile Menu Dropdown */}
      {mobileMenuOpen && (
        <div className="md:hidden fixed inset-0 top-[65px] bg-[#0f172a] z-40 p-4 flex flex-col gap-2 overflow-y-auto pb-24">
          <NavItem icon={<LayoutDashboard />} label="Dashboard" active={activeTab === 'dashboard'} onClick={() => {setActiveTab('dashboard'); setMobileMenuOpen(false);}} />
          <NavItem icon={<History />} label="Histórico" active={activeTab === 'history'} onClick={() => {setActiveTab('history'); setMobileMenuOpen(false);}} />
          <NavItem icon={<Activity />} label="Backtesting" active={activeTab === 'backtesting'} onClick={() => {setActiveTab('backtesting'); setMobileMenuOpen(false);}} />
          <NavItem icon={<TrendingUp />} label="Mercados" active={activeTab === 'markets'} onClick={() => {setActiveTab('markets'); setMobileMenuOpen(false);}} />
          <NavItem icon={<BarChart3 />} label="Métricas" active={activeTab === 'metrics'} onClick={() => {setActiveTab('metrics'); setMobileMenuOpen(false);}} />
          <NavItem icon={<ShieldAlert />} label="Risco" active={activeTab === 'risco'} onClick={() => {setActiveTab('risco'); setMobileMenuOpen(false);}} />
          <NavItem icon={<Settings />} label="Configurações" active={activeTab === 'configuracoes'} onClick={() => {setActiveTab('configuracoes'); setMobileMenuOpen(false);}} />
          
          <button 
              onClick={handleLogout}
              className="mt-4 text-sm text-slate-400 hover:text-white px-3 py-3 border border-slate-700 hover:border-slate-500 hover:bg-slate-800 rounded-lg transition-colors flex justify-center w-full"
            >
              Sair do Sistema
          </button>
        </div>
      )}

      {/* Sidebar */}
      <aside className="w-64 bg-[#1e293b] border-r border-slate-800 p-6 flex-col hidden md:flex shrink-0">
        <div className="flex items-center gap-3 mb-10">
          <Activity className="text-blue-500" size={28} />
          <h1 className="text-xl font-bold tracking-wider">AI TRADER</h1>
        </div>
        
        <nav className="flex-1 space-y-2">
          <NavItem icon={<LayoutDashboard />} label="Dashboard" active={activeTab === 'dashboard'} onClick={() => setActiveTab('dashboard')} />
          <NavItem icon={<History />} label="Histórico" active={activeTab === 'history'} onClick={() => setActiveTab('history')} />
          <NavItem icon={<Activity />} label="Backtesting" active={activeTab === 'backtesting'} onClick={() => setActiveTab('backtesting')} />
          <NavItem icon={<TrendingUp />} label="Mercados" active={activeTab === 'markets'} onClick={() => setActiveTab('markets')} />
          <NavItem icon={<BarChart3 />} label="Métricas" active={activeTab === 'metrics'} onClick={() => setActiveTab('metrics')} />
          <NavItem icon={<ShieldAlert />} label="Risco" active={activeTab === 'risco'} onClick={() => setActiveTab('risco')} />
          <NavItem icon={<Settings />} label="Configurações" active={activeTab === 'configuracoes'} onClick={() => setActiveTab('configuracoes')} />
        </nav>
        
        <div className="mt-auto pt-6 border-t border-slate-800">
          <div className="flex flex-col gap-4">
            <div className="flex items-center gap-3 text-sm text-slate-400">
              <div className={`w-2 h-2 rounded-full ${loading ? 'bg-yellow-500' : 'bg-green-500'} animate-pulse`}></div>
              {loading ? 'Conectando...' : 'Sistema Operacional'}
            </div>
            
            <button 
              onClick={handleLogout}
              className="text-sm text-slate-400 hover:text-white px-3 py-2 border border-slate-700 hover:border-slate-500 hover:bg-slate-800 rounded-lg transition-colors flex justify-center w-full"
            >
              Sair do Sistema
            </button>
          </div>
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 p-4 md:p-8 overflow-y-auto">
        {activeTab === 'dashboard' && (
          <>
            {risk?.protection_level && risk.protection_level !== 'NORMAL' && (
              <div className={`mb-6 border p-4 rounded-xl flex items-center gap-4 animate-pulse ${
                risk.protection_level === 'LEVEL_1_PROTECTION' ? 'bg-yellow-500/10 border-yellow-500/20' : 'bg-red-500/10 border-red-500/20'
              }`}>
                <ShieldAlert className={`${risk.protection_level === 'LEVEL_1_PROTECTION' ? 'text-yellow-500' : 'text-red-500'} shrink-0`} size={24} />
                <div>
                  <h3 className={`font-bold ${risk.protection_level === 'LEVEL_1_PROTECTION' ? 'text-yellow-500' : 'text-red-500'}`}>Trava de Proteção Ativa!</h3>
                  <p className={`text-sm ${risk.protection_level === 'LEVEL_1_PROTECTION' ? 'text-yellow-400' : 'text-red-400'}`}>
                    O sistema atingiu limites de risco e ativou o modo: <strong>{risk.protection_level}</strong>. 
                    {risk.protection_level === 'LEVEL_1_PROTECTION' && " O tamanho dos próximos lotes será reduzido."}
                    {risk.protection_level === 'LEVEL_2_PROTECTION' && " Novas entradas estão temporariamente bloqueadas."}
                    {risk.protection_level === 'LEVEL_3_PROTECTION' && " O robô foi totalmente pausado por segurança máxima."}
                  </p>
                </div>
              </div>
            )}
            <header className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 mb-8">
              <div>
                <h2 className="text-3xl font-semibold mb-1">Visão Geral</h2>
                <p className="text-slate-400">Resumo da performance da sua carteira e risco global.</p>
              </div>
              <div className="flex flex-wrap gap-4 w-full md:w-auto">
                <button 
                  onClick={async () => {
                    if (window.confirm("🚨 TEM CERTEZA? Isso vai fechar TODAS as posições a mercado agora e pausar o robô!")) {
                      try {
                        const res = await apiFetch('http://localhost:8000/api/bot/panic', { method: 'POST' });
                        if (res.ok) {
                          alert("Botão de Pânico acionado! Posições fechadas.");
                          // O pooling já vai atualizar a tela em até 3 segundos, mas forçamos uma att visual
                          setStats((prev: any) => ({ ...prev, bot_running: false }));
                        }
                      } catch (e) {
                        console.error('Erro no botão de pânico', e);
                      }
                    }
                  }}
                  className="px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg transition-all shadow-lg shadow-red-600/30 font-bold flex items-center gap-2 animate-pulse hover:animate-none flex-1 md:flex-none justify-center">
                  <ShieldAlert size={18} /> ZERAR TUDO
                </button>
                <button className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors shadow-lg shadow-blue-500/20 font-medium flex-1 md:flex-none justify-center">
                  Relatório
                </button>
              </div>
            </header>

            {/* Top Cards */}
            <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-6 mb-8">
              <StatCard title="Saldo da Conta" value={`$ ${stats?.balance?.toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2}) || '---'}`} icon={<DollarSign className="text-blue-500" />} />
              <StatCard title="Lucro Mensal" value={`$ ${stats?.monthly_profit?.toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2}) || '---'}`} icon={<TrendingUp className="text-green-500" />} positive={stats?.monthly_profit >= 0} />
              <StatCard title="Drawdown Atual" value={`${stats?.current_drawdown || '0'}%`} icon={<ShieldAlert className="text-red-500" />} />
              <StatCard title="Operações Abertas" value={stats?.open_trades || 0} icon={<Activity className="text-purple-500" />} />
            </div>

            {/* Equity Curve Chart */}
            {stats?.equity_curve && (
              <div className="bg-[#1e293b] p-6 rounded-2xl border border-slate-800 mb-8">
                <h3 className="text-xl font-semibold mb-6">Curva de Capital (Equity)</h3>
                <div className="h-64 w-full">
                  <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={stats.equity_curve}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#334155" vertical={false} />
                      <XAxis dataKey="date" stroke="#94a3b8" />
                      <YAxis stroke="#94a3b8" domain={['auto', 'auto']} />
                      <Tooltip 
                        contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', color: '#f8fafc' }}
                        itemStyle={{ color: '#3b82f6' }}
                      />
                      <Line type="monotone" dataKey="equity" stroke="#3b82f6" strokeWidth={3} dot={{ fill: '#3b82f6', strokeWidth: 2 }} activeDot={{ r: 8 }} />
                    </LineChart>
                  </ResponsiveContainer>
                </div>
              </div>
            )}
          </>
        )}

        {activeTab === 'markets' && (
          <>
            <header className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 mb-8">
              <div>
                <h2 className="text-3xl font-semibold mb-1">Mercados e Posições</h2>
                <p className="text-slate-400">Monitoramento em tempo real dos ativos que o robô está posicionado.</p>
              </div>
            </header>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              {markets.map((market, idx) => (
                 <MarketCard 
                   key={idx}
                   id={market.id}
                   asset={market.asset} 
                   strategy={market.strategy} 
                   status={market.status} 
                   price={market.price} 
                   metric={market.metric}
                   takeProfit={market.take_profit}
                   stopLoss={market.stop_loss}
                   entryPrice={market.entry_price}
                 />
              ))}
              {markets.length === 0 && !loading && (
                <div className="col-span-full bg-[#1e293b] p-10 rounded-2xl border border-slate-800 text-center text-slate-400">
                  <Activity className="w-12 h-12 mx-auto mb-4 text-slate-600" />
                  <p className="text-lg">Nenhuma operação aberta no momento.</p>
                  <p className="text-sm">O sistema de inteligência artificial está buscando oportunidades...</p>
                </div>
              )}
            </div>
          </>
        )}

        {activeTab === 'history' && (
          <>
            <header className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 mb-8">
              <div>
                <h2 className="text-3xl font-semibold mb-1">Histórico de Operações</h2>
                <p className="text-slate-400">Registro completo de todos os trades fechados.</p>
              </div>
            </header>
            
            <div className="bg-[#1e293b] rounded-2xl border border-slate-800 overflow-hidden shadow-xl">
              <div className="overflow-x-auto">
                <table className="w-full text-left border-collapse">
                  <thead>
                    <tr className="bg-slate-800/50 text-slate-300 text-sm">
                      <th className="px-6 py-4 font-medium">Ativo</th>
                      <th className="px-6 py-4 font-medium">Estratégia</th>
                      <th className="px-6 py-4 font-medium">Direção</th>
                      <th className="px-6 py-4 font-medium">Preço Entrada</th>
                      <th className="px-6 py-4 font-medium">Preço Saída</th>
                      <th className="px-6 py-4 font-medium">PnL</th>
                      <th className="px-6 py-4 font-medium">Justificativa IA</th>
                      <th className="px-6 py-4 font-medium text-center">Ações</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/50">
                    {history.map((trade: any) => (
                      <tr key={trade.id} className="hover:bg-slate-800/20 transition-colors">
                        <td className="px-6 py-4 font-medium">{trade.asset}</td>
                        <td className="px-6 py-4 text-slate-400 text-sm">{trade.strategy}</td>
                        <td className="px-6 py-4">
                          <span className={`px-2 py-1 rounded text-xs font-bold ${trade.direction === 'LONG' ? 'bg-green-500/10 text-green-500' : 'bg-red-500/10 text-red-500'}`}>
                            {trade.direction}
                          </span>
                        </td>
                        <td className="px-6 py-4 text-slate-300">${trade.entry_price}</td>
                        <td className="px-6 py-4 text-slate-300">${trade.exit_price?.toFixed(2) || '---'}</td>
                        <td className={`px-6 py-4 font-bold ${trade.pnl >= 0 ? 'text-green-500' : 'text-red-500'}`}>
                          ${trade.pnl?.toFixed(2)}
                        </td>
                        <td className="px-6 py-4 text-slate-400 text-xs max-w-xs truncate" title={trade.reason}>{trade.reason}</td>
                        <td className="px-6 py-4 text-center">
                          <button 
                            onClick={() => deleteTrade(trade.id)}
                            className="text-xs px-3 py-1 bg-red-500/10 text-red-500 hover:bg-red-500/20 rounded transition-colors"
                          >
                            Excluir
                          </button>
                        </td>
                      </tr>
                    ))}
                    {history.length === 0 && (
                      <tr>
                        <td colSpan={8} className="px-6 py-8 text-center text-slate-500">Nenhum trade fechado ainda.</td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          </>
        )}

        {activeTab === 'metrics' && (
          <>
            <header className="flex justify-between items-center mb-8">
              <div>
                <h2 className="text-3xl font-semibold mb-1">Métricas de Performance</h2>
                <p className="text-slate-400">Análise detalhada de risco e eficiência do robô.</p>
              </div>
            </header>
            
            {history.length > 0 ? (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                <StatCard 
                  title="Taxa de Acerto (Win Rate)" 
                  value={`${((history.filter((t: any) => t.pnl > 0).length / history.length) * 100).toFixed(1)}%`} 
                  icon={<Activity className="text-green-500" />} 
                />
                <StatCard 
                  title="Total de Operações" 
                  value={history.length} 
                  icon={<BarChart3 className="text-blue-500" />} 
                />
                <StatCard 
                  title="Lucro Médio por Trade" 
                  value={`$ ${(history.filter((t: any) => t.pnl > 0).reduce((acc: number, t: any) => acc + t.pnl, 0) / (history.filter((t: any) => t.pnl > 0).length || 1)).toFixed(2)}`} 
                  icon={<TrendingUp className="text-green-500" />} 
                />
                <StatCard 
                  title="Prejuízo Médio por Trade" 
                  value={`$ ${(history.filter((t: any) => t.pnl < 0).reduce((acc: number, t: any) => acc + t.pnl, 0) / (history.filter((t: any) => t.pnl < 0).length || 1)).toFixed(2)}`} 
                  icon={<ShieldAlert className="text-red-500" />} 
                />
                <StatCard 
                  title="Melhor Trade" 
                  value={`$ ${Math.max(...history.map((t: any) => t.pnl || 0)).toFixed(2)}`} 
                  icon={<DollarSign className="text-green-500" />} 
                />
                <StatCard 
                  title="Pior Trade" 
                  value={`$ ${Math.min(...history.map((t: any) => t.pnl || 0)).toFixed(2)}`} 
                  icon={<ShieldAlert className="text-red-500" />} 
                />
              </div>
            ) : (
              <div className="bg-[#1e293b] p-10 rounded-2xl border border-slate-800 text-center text-slate-400">
                <BarChart3 className="w-12 h-12 mx-auto mb-4 text-slate-600" />
                <p className="text-lg">Dados Insuficientes</p>
                <p className="text-sm">As métricas estarão disponíveis assim que o primeiro trade for concluído.</p>
              </div>
            )}
          </>
        )}

        {activeTab === 'risco' && (
          <>
            <header className="flex justify-between items-center mb-8">
              <div>
                <h2 className="text-3xl font-semibold mb-1">Gerenciamento de Risco</h2>
                <p className="text-slate-400">Controle de exposição, proteção de capital e correlação de ativos.</p>
              </div>
            </header>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
              <StatCard 
                title="Risco por Operação" 
                value={`${((risk?.max_risk_per_trade || 0) * 100).toFixed(1)}%`} 
                icon={<DollarSign className="text-blue-500" />} 
              />
              <StatCard 
                title="Drawdown Atual" 
                value={`${(risk?.max_drawdown || 0).toFixed(1)}%`} 
                icon={<TrendingUp className="text-purple-500" />} 
              />
              <StatCard 
                title="Nível de Proteção" 
                value={risk?.protection_level?.replace(/_/g, ' ') || 'NORMAL'} 
                icon={<ShieldAlert className={risk?.protection_level !== 'NORMAL' ? "text-yellow-500" : "text-green-500"} />} 
              />
            </div>

            <div className="bg-[#1e293b] p-6 rounded-2xl border border-slate-800 mb-8">
              <h3 className="text-xl font-semibold mb-6">Matriz de Correlação Global</h3>
              <div className="overflow-x-auto">
                <table className="w-full text-left border-collapse">
                  <thead>
                    <tr className="bg-slate-800/50 text-slate-300 text-sm">
                      <th className="px-4 py-3 font-medium">Ativo</th>
                      {risk?.correlation_matrix && Object.keys(risk.correlation_matrix).map(asset => (
                        <th key={asset} className="px-4 py-3 font-medium">{asset}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/50">
                    {risk?.correlation_matrix && Object.keys(risk.correlation_matrix).map(baseAsset => (
                      <tr key={baseAsset} className="hover:bg-slate-800/20 transition-colors">
                        <td className="px-4 py-4 font-bold">{baseAsset}</td>
                        {Object.keys(risk.correlation_matrix).map(targetAsset => {
                          const val = risk.correlation_matrix[baseAsset][targetAsset] || (baseAsset === targetAsset ? 1.0 : 0.0);
                          let color = 'text-slate-400';
                          if (val >= 0.7 && val < 1.0) color = 'text-red-500 font-medium';
                          else if (val >= 0.4 && val < 1.0) color = 'text-yellow-500 font-medium';
                          else if (val === 1.0) color = 'text-slate-600';
                          
                          return (
                            <td key={targetAsset} className={`px-4 py-4 ${color}`}>
                              {val.toFixed(2)}
                            </td>
                          );
                        })}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </>
        )}

        {activeTab === 'configuracoes' && (
          <>
            <header className="flex justify-between items-center mb-8">
              <div>
                <h2 className="text-3xl font-semibold mb-1">Configurações do Sistema</h2>
                <p className="text-slate-400">Gerencie o robô de operações, chaves de API e preferências gerais.</p>
              </div>
            </header>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
              {/* Controle do Robô */}
              <div className="bg-[#1e293b] p-8 rounded-2xl border border-slate-800">
                <h3 className="text-xl font-semibold mb-4 flex items-center gap-2">
                  <Activity className="text-blue-500" /> Estado do AI Trader
                </h3>
                <p className="text-slate-400 mb-6 text-sm">
                  Liga ou desliga o motor de trading automático. Quando desligado, as posições abertas continuarão sendo monitoradas apenas para Stop Loss / Take Profit via corretora, se já enviados.
                </p>
                <div className="flex items-center justify-between p-4 bg-slate-800/50 rounded-xl">
                  <div>
                    <div className="font-bold text-lg">Motor de Trading Automático</div>
                    <div className={`text-sm font-medium ${stats?.bot_running ? 'text-green-500' : 'text-red-500'}`}>
                      {stats?.bot_running ? 'Em Execução' : 'Pausado'}
                    </div>
                  </div>
                  <button 
                    onClick={async () => {
                      try {
                        const res = await apiFetch('http://localhost:8000/api/bot/toggle', { method: 'POST' });
                        if (res.ok) {
                          const data = await res.json();
                          setStats((prev: any) => ({ ...prev, bot_running: data.bot_running }));
                        }
                      } catch (e) {
                        console.error('Erro ao alternar bot', e);
                      }
                    }}
                    className={`px-6 py-3 rounded-lg font-bold transition-all shadow-lg ${
                      stats?.bot_running 
                        ? 'bg-red-500/20 text-red-500 hover:bg-red-500/30 shadow-red-500/10' 
                        : 'bg-green-500/20 text-green-500 hover:bg-green-500/30 shadow-green-500/10'
                    }`}
                  >
                    {stats?.bot_running ? 'Pausar Robô' : 'Ligar Robô'}
                  </button>
                </div>
              </div>

              {/* Informações do Sistema */}
              <div className="bg-[#1e293b] p-8 rounded-2xl border border-slate-800">
                <h3 className="text-xl font-semibold mb-4 flex items-center gap-2">
                  <Settings className="text-slate-400" /> Preferências e API
                </h3>
                <p className="text-slate-400 mb-6 text-sm">
                  Configurações adicionais de infraestrutura e conexão com brokers. (Em desenvolvimento)
                </p>
                <div className="space-y-4">
                  <div className="flex items-center justify-between border-b border-slate-800 pb-4">
                    <span className="text-slate-300">Modo de Operação</span>
                    <span className="px-3 py-1 bg-yellow-500/10 text-yellow-500 text-xs font-bold rounded-full">Testnet (Papertrading)</span>
                  </div>
                  <div className="flex items-center justify-between border-b border-slate-800 pb-4">
                    <span className="text-slate-300">Frequência de Atualização</span>
                    <span className="text-slate-400">3 segundos</span>
                  </div>
                  <div className="flex items-center justify-between pb-2">
                    <span className="text-slate-300">Conexões Ativas</span>
                    <span className="text-green-500 font-medium">Binance, Bybit</span>
                  </div>
                </div>
              </div>
            </div>
          </>
        )}

        {activeTab === 'configuracoes' && <SettingsTab />}
        {activeTab === 'backtesting' && <BacktestTab />}
      </main>
    </div>
  );
}

// Components
const NavItem = ({ icon, label, active = false, onClick }: { icon: React.ReactNode, label: string, active?: boolean, onClick?: () => void }) => (
  <a href="#" onClick={(e) => { e.preventDefault(); if(onClick) onClick(); }} className={`flex items-center gap-3 px-4 py-3 rounded-lg transition-all ${active ? 'bg-blue-600/10 text-blue-500 font-medium' : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800'}`}>
    {icon}
    {label}
  </a>
);

const StatCard = ({ title, value, icon, trend, positive }: any) => (
  <div className="bg-[#1e293b] p-6 rounded-2xl border border-slate-800 hover:border-slate-700 transition-colors">
    <div className="flex justify-between items-start mb-4">
      <h3 className="text-slate-400 font-medium">{title}</h3>
      <div className="p-2 bg-slate-800/50 rounded-lg">{icon}</div>
    </div>
    <div className="flex items-end gap-3">
      <span className="text-2xl font-bold">{value}</span>
      {trend && (
        <span className={`text-sm font-medium mb-1 ${positive ? 'text-green-500' : 'text-red-500'}`}>
          {trend}
        </span>
      )}
    </div>
  </div>
);

const MarketCard = ({ id, asset, strategy, status, price, metric, takeProfit, stopLoss, entryPrice }: any) => {
  const isLong = status === 'Comprado';
  const isShort = status === 'Vendido';
  const [closing, setClosing] = useState(false);

  const handleClose = async () => {
    if (window.confirm(`Tem certeza que deseja fechar a posição em ${asset}?`)) {
      setClosing(true);
      try {
        const res = await apiFetch(`http://localhost:8000/api/trades/close/${id}`, { method: 'POST' });
        if (res.ok) {
          alert(`Posição ${asset} fechada com sucesso!`);
        } else {
          alert('Erro ao fechar posição.');
        }
      } catch (e) {
        console.error('Erro ao fechar posição', e);
        alert('Erro ao fechar posição.');
      } finally {
        setClosing(false);
      }
    }
  };
  
  return (
    <div className="bg-[#1e293b] p-6 rounded-2xl border border-slate-800 hover:border-slate-700 transition-colors group">
      <div className="flex justify-between items-start mb-4">
        <div>
          <h4 className="text-lg font-bold group-hover:text-blue-400 transition-colors">{asset}</h4>
          <span className="text-sm text-slate-400">{strategy}</span>
        </div>
        <div className="flex flex-col items-end gap-2">
          <div className={`px-3 py-1 rounded-full text-xs font-bold ${isLong ? 'bg-green-500/10 text-green-500 border border-green-500/20' : isShort ? 'bg-red-500/10 text-red-500 border border-red-500/20' : 'bg-slate-700 text-slate-300'}`}>
            {status}
          </div>
          <button 
            onClick={handleClose} 
            disabled={closing}
            className="text-xs px-2 py-1 bg-red-600/20 text-red-500 hover:bg-red-600/40 rounded transition-colors"
          >
            {closing ? 'Fechando...' : 'Fechar'}
          </button>
        </div>
      </div>
      
      <div className="grid grid-cols-2 gap-4 mt-6">
        <div>
          <div className="text-sm text-slate-400 mb-1">Preço Atual</div>
          <div className="font-semibold text-lg">{price}</div>
        </div>
        <div>
          <div className="text-sm text-slate-400 mb-1">Status</div>
          <div className="font-medium text-slate-200 text-sm">{metric}</div>
        </div>
        <div>
          <div className="text-xs text-slate-400 mb-1">Preço de Entrada</div>
          <div className="font-medium text-blue-400 text-sm">{entryPrice ? `$ ${entryPrice.toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 4})}` : '---'}</div>
        </div>
        {takeProfit && (
          <div>
            <div className="text-xs text-slate-400 mb-1">Take Profit</div>
            <div className="font-medium text-green-500 text-sm">$ {takeProfit.toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 4})}</div>
          </div>
        )}
        {stopLoss && (
          <div>
            <div className="text-xs text-slate-400 mb-1">Stop Loss</div>
            <div className="font-medium text-red-500 text-sm">$ {stopLoss.toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 4})}</div>
          </div>
        )}
      </div>
    </div>
  );
};

export default App;
