import { Server, Activity, AlertTriangle, CheckCircle } from 'lucide-react';

export default function SystemState({ services, alerts }) {
    return (
        <div className="bg-white/5 p-6 rounded-xl border border-white/10 shadow-xl">
            <h2 className="text-xl font-bold mb-4 flex items-center gap-2">
                <Activity className="text-blue-400" /> System State
            </h2>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {/* Services */}
                <div>
                    <h3 className="text-sm font-semibold text-slate-400 mb-3 uppercase tracking-wider">Services</h3>
                    <div className="space-y-2">
                        {services.length === 0 ? (
                            <p className="text-slate-500 italic">No services found</p>
                        ) : (
                            services.map(svc => (
                                <div key={svc.id} className="flex items-center justify-between bg-black/20 p-3 rounded-lg border border-white/5">
                                    <div className="flex items-center gap-3">
                                        <Server size={18} className={svc.status === 'running' ? 'text-emerald-400' : 'text-red-400'} />
                                        <span className="font-mono text-sm">{svc.id}</span>
                                    </div>
                                    <span className={`text-xs px-2 py-1 rounded-full ${svc.status === 'running' ? 'bg-emerald-900/30 text-emerald-300' : 'bg-red-900/30 text-red-300'
                                        }`}>
                                        {svc.status}
                                    </span>
                                </div>
                            ))
                        )}
                    </div>
                </div>

                {/* Alerts */}
                <div>
                    <h3 className="text-sm font-semibold text-slate-400 mb-3 uppercase tracking-wider">Active Alerts</h3>
                    <div className="space-y-2 max-h-[200px] overflow-y-auto pr-1">
                        {alerts.length === 0 ? (
                            <div className="flex items-center gap-2 text-emerald-400/50 italic p-2">
                                <CheckCircle size={16} /> All systems nominal
                            </div>
                        ) : (
                            alerts.map(alert => (
                                <div key={alert.id} className="bg-red-900/10 border border-red-900/30 p-3 rounded-lg">
                                    <div className="flex justify-between items-start mb-1">
                                        <span className="text-xs font-bold text-red-400 uppercase">{alert.severity}</span>
                                        <span className="text-[10px] text-slate-500 font-mono">{alert.type}</span>
                                    </div>
                                    <p className="text-sm text-slate-300 leading-tight">{alert.msg}</p>
                                </div>
                            ))
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
}
