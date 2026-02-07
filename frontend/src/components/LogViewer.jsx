import { Scroll, Terminal } from 'lucide-react';
import { useEffect, useRef } from 'react';

export default function LogViewer({ logs }) {
    const scrollRef = useRef(null);

    // Auto-scroll to bottom
    useEffect(() => {
        if (scrollRef.current) {
            scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
        }
    }, [logs]);

    return (
        <div className="bg-white/5 p-6 rounded-xl border border-white/10 shadow-xl h-full flex flex-col min-h-[400px]">
            <h2 className="text-xl font-bold mb-4 flex items-center gap-2">
                <Terminal className="text-orange-400" /> Execution Logs
            </h2>

            <div
                ref={scrollRef}
                className="flex-1 bg-black/40 p-4 rounded-lg border border-white/5 font-mono text-xs overflow-y-auto max-h-[500px]"
            >
                {logs.length === 0 ? (
                    <p className="text-slate-600 italic">Waiting for log activity...</p>
                ) : (
                    logs.map((log, idx) => (
                        <div key={idx} className="mb-2 border-b border-white/5 pb-1 last:border-0 break-words">
                            <span className="text-slate-500 mr-2">
                                [{new Date(log.timestamp || Date.now()).toLocaleTimeString()}]
                            </span>
                            {log.action ? (
                                <>
                                    <span className={`font-bold mr-2 ${log.action.includes('error') ? 'text-red-400' :
                                            log.action.includes('infra') ? 'text-blue-400' :
                                                log.action.includes('alert') ? 'text-orange-400' :
                                                    'text-emerald-400'
                                        }`}>
                                        {log.action}
                                    </span>
                                    <span className="text-slate-300">
                                        {/* Filter out sensitive/long fields from display if needed */}
                                        {JSON.stringify({ ...log, action: undefined, timestamp: undefined })}
                                    </span>
                                </>
                            ) : (
                                <span className="text-slate-300">{JSON.stringify(log)}</span>
                            )}
                        </div>
                    ))
                )}
            </div>
        </div>
    );
}
