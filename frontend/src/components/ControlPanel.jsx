import { useState } from 'react';
import axios from 'axios';
import { Play, RotateCw, AlertTriangle, ShieldCheck } from 'lucide-react';

export default function ControlPanel({ onRun, isRunning, lastStatus }) {
    const [goal, setGoal] = useState('');

    const handleRun = () => {
        onRun(goal);
    };

    return (
        <div className="bg-white/5 p-6 rounded-xl border border-white/10 shadow-xl">
            <h2 className="text-xl font-bold mb-4 flex items-center gap-2">
                <Play className="text-emerald-400" /> Control Center
            </h2>

            <div className="flex gap-4 mb-4">
                <input
                    type="text"
                    value={goal}
                    onChange={(e) => setGoal(e.target.value)}
                    placeholder="Override Goal (Optional)..."
                    className="flex-1 bg-black/20 border border-white/10 rounded-lg px-4 py-2 focus:outline-none focus:border-emerald-500 transition-colors"
                />
                <button
                    onClick={handleRun}
                    disabled={isRunning}
                    className={`px-6 py-2 rounded-lg font-bold transition-all flex items-center gap-2
            ${isRunning
                            ? 'bg-slate-600 cursor-not-allowed opacity-50'
                            : 'bg-emerald-600 hover:bg-emerald-500 shadow-lg shadow-emerald-900/20'}`}
                >
                    {isRunning ? <RotateCw className="animate-spin" /> : <Play size={18} />}
                    {isRunning ? 'Running Cycle...' : 'Run Agent'}
                </button>
            </div>

            {lastStatus && (
                <div className={`p-3 rounded-lg text-sm border ${lastStatus === 'success' ? 'bg-emerald-900/20 border-emerald-800 text-emerald-200' : 'bg-red-900/20 border-red-800 text-red-200'
                    }`}>
                    Last Cycle: <span className="font-mono font-bold capitalize">{lastStatus}</span>
                </div>
            )}
        </div>
    );
}
