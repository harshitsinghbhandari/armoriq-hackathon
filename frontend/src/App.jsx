import { useState, useEffect } from 'react';
import axios from 'axios';
import { LayoutDashboard } from 'lucide-react';

import ControlPanel from './components/ControlPanel';
import SystemState from './components/SystemState';
import AgentPlan from './components/AgentPlan';
import LogViewer from './components/LogViewer';

function App() {
  const [isRunning, setIsRunning] = useState(false);
  const [lastStatus, setLastStatus] = useState(null);

  const [services, setServices] = useState([]);
  const [alerts, setAlerts] = useState([]);
  const [plan, setPlan] = useState(null);
  const [logs, setLogs] = useState([]);

  // Polling Effect
  useEffect(() => {
    const poll = async () => {
      try {
        const [infraRes, alertsRes] = await Promise.all([
          axios.get('/api/mcp/infra/list'),
          axios.get('/api/mcp/alerts/')
        ]);

        // Simulating logs fetch if endpoint missing or just mocking for demo
        // const logsRes = await axios.get('/api/logs'); 

        if (infraRes.data.services) setServices(infraRes.data.services);
        if (alertsRes.data.alerts) setAlerts(alertsRes.data.alerts);
        // if (logsRes.data.logs) setLogs(logsRes.data.logs);

      } catch (error) {
        console.error("Polling error:", error);
      }
    };

    const interval = setInterval(poll, 3000);
    poll(); // Initial call

    return () => clearInterval(interval);
  }, []);

  const runAgent = async (goal) => {
    setIsRunning(true);
    setLastStatus(null);
    try {
      const res = await axios.post('/api/run',
        { input: goal || "Fix the system" },
        { headers: { 'x-api-key': 'default-insecure-key' } }
      );
      setPlan(res.data.plan); // Note: server.py returns `plan` directly or as a dict? 
      // User's server.py: `return plan`. `generate_plan` likely returns a dict or object. 
      // If `generate_plan` returns a dict, then `res.data` IS that dict.
      // If `generate_plan` returns the full plan structure, we probably want `res.data`.
      // Let's assume res.data IS the plan.
      setPlan(res.data);
      setLastStatus('success');
    } catch (error) {
      console.error("Agent run error:", error);
      setLastStatus('error');
    } finally {
      setIsRunning(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-200 font-sans p-8">
      <header className="max-w-7xl mx-auto mb-8 flex items-center gap-3 border-b border-white/10 pb-4">
        <div className="p-3 bg-emerald-500/10 rounded-xl border border-emerald-500/20">
          <LayoutDashboard className="text-emerald-400" size={32} />
        </div>
        <div>
          <h1 className="text-3xl font-bold bg-gradient-to-r from-emerald-400 to-blue-400 bg-clip-text text-transparent">
            ArmorIQ Agent Dashboard
          </h1>
          <p className="text-slate-500">Autonomous Infrastructure Management & Governance</p>
        </div>
      </header>

      <main className="max-w-7xl mx-auto grid grid-cols-1 lg:grid-cols-3 gap-8">

        {/* Left Column: Controls & State */}
        <div className="lg:col-span-2 space-y-8">
          <ControlPanel
            onRun={runAgent}
            isRunning={isRunning}
            lastStatus={lastStatus}
          />
          <SystemState services={services} alerts={alerts} />
          <AgentPlan plan={plan} />
        </div>

        {/* Right Column: Logs */}
        <div className="lg:col-span-1">
          <LogViewer logs={logs} />
        </div>

      </main>
    </div>
  );
}

export default App;
