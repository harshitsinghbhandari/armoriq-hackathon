import { Brain, CornerDownRight } from 'lucide-react';

export default function AgentPlan({ plan }) {
    if (!plan) {
        return (
            <div className="bg-white/5 p-6 rounded-xl border border-white/10 shadow-xl min-h-[200px] flex items-center justify-center text-slate-500">
                <div className="text-center">
                    <Brain size={48} className="mx-auto mb-2 opacity-20" />
                    <p>Waiting for agent plan...</p>
                </div>
            </div>
        );
    }

    // Handle plan JSON or string
    const displayPlan = typeof plan === 'string' ? { raw: plan } : plan;

    return (
        <div className="bg-white/5 p-6 rounded-xl border border-white/10 shadow-xl">
            <h2 className="text-xl font-bold mb-4 flex items-center gap-2">
                <Brain className="text-purple-400" /> Agent Logic
            </h2>

            <div className="bg-black/30 p-4 rounded-lg border border-white/5 font-mono text-sm overflow-x-auto">
                {displayPlan.goal && (
                    <div className="mb-4 pb-4 border-b border-white/10">
                        <span className="text-purple-400 font-bold block mb-1">GOAL:</span>
                        <span className="text-slate-200">{displayPlan.goal}</span>
                    </div>
                )}

                <div className="space-y-3">
                    {displayPlan.steps ? (
                        displayPlan.steps.map((step, idx) => (
                            <div key={idx} className="bg-white/5 p-3 rounded border border-white/5">
                                <div className="flex items-center gap-2 text-blue-300 font-bold mb-1">
                                    <CornerDownRight size={14} />
                                    {step.action}
                                </div>
                                {step.params && (
                                    <pre className="text-[10px] text-slate-400 pl-6">
                                        {JSON.stringify(step.params, null, 2)}
                                    </pre>
                                )}
                            </div>
                        ))
                    ) : (
                        <p className="text-slate-500 italic">No steps required.</p>
                    )}
                </div>
            </div>
        </div>
    );
}
