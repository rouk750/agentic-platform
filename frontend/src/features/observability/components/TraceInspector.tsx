import { useState } from 'react';
import { Code2, ArrowRightLeft, Database, ChevronRight, ChevronDown, Cpu, ArrowRight, ArrowLeft } from 'lucide-react';

interface InspectorProps {
  stepId: string | null;
  data: any | null; // StepSnapshot
}

function Section({ title, icon: Icon, children, defaultOpen = true }: { title: string; icon: any; children: React.ReactNode; defaultOpen?: boolean }) {
  const [isOpen, setIsOpen] = useState(defaultOpen);
  return (
    <section className="bg-white rounded-lg border border-slate-200 overflow-hidden">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="w-full flex items-center justify-between p-3 bg-slate-50 border-b border-slate-100 hover:bg-slate-100 transition-colors"
      >
        <div className="flex items-center gap-2">
          <Icon size={14} className="text-slate-500" />
          <h4 className="text-xs font-semibold text-slate-700 uppercase tracking-wide">{title}</h4>
        </div>
        {isOpen ? <ChevronDown size={14} className="text-slate-400" /> : <ChevronRight size={14} className="text-slate-400" />}
      </button>

      {isOpen && (
        <div className="p-3">
          {children}
        </div>
      )}
    </section>
  );
}

function DataDisplay({ data }: { data: any }) {
  if (data === undefined || data === null) {
    return <span className="text-slate-400 italic text-xs">None</span>;
  }

  if (typeof data === 'object') {
    return (
      <div className="bg-slate-50 rounded border border-slate-200 p-2 font-mono text-xs text-slate-700 overflow-x-auto">
        <pre>{JSON.stringify(data, null, 2)}</pre>
      </div>
    );
  }

  return (
    <div className="font-mono text-sm text-slate-700 whitespace-pre-wrap">
      {String(data)}
    </div>
  );
}

export default function TraceInspector({ stepId, data }: InspectorProps) {
  if (!stepId || !data) {
    return (
      <div className="h-full flex items-center justify-center text-slate-400 bg-slate-50">
        <div className="text-center">
          <Database size={32} className="mx-auto mb-2 opacity-50" />
          <p>Select a step to inspect details</p>
        </div>
      </div>
    );
  }

  // Extract relevant data points
  // Priority: Direct prop -> State prop -> undefined
  const inputData = data.input ?? data.state?.input;
  const outputData = data.output ?? data.state?.output;
  const tokens = data.tokens ?? data._meta?.tokens;

  return (
    <div className="h-full flex flex-col bg-slate-50">
      <div className="p-3 border-b border-slate-200 bg-white flex items-center justify-between shrink-0 shadow-sm z-10">
        <h3 className="text-sm font-semibold text-slate-700 flex items-center gap-2">
          <span className="w-2 h-2 rounded-full bg-blue-500"></span>
          Trace Details
          <span className="text-slate-400 font-normal ml-2 text-xs font-mono">{stepId}</span>
        </h3>
        <div className="flex gap-1">
          <button className="p-1.5 hover:bg-slate-100 rounded text-slate-500 transition-colors" title="State Diff">
            <ArrowRightLeft size={16} />
          </button>
          <button
            className="p-1.5 hover:bg-slate-100 rounded text-slate-500 transition-colors"
            title="Raw JSON"
          >
            <Code2 size={16} />
          </button>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto p-4 space-y-4">

        {/* Token Usage Section */}
        {tokens && (
          <div className="grid grid-cols-3 gap-3 mb-4">
            <div className="bg-white p-3 rounded-lg border border-slate-200 shadow-sm flex flex-col items-center justify-center">
              <span className="text-[10px] uppercase text-slate-400 font-semibold mb-1 flex items-center gap-1">
                <ArrowRight size={10} /> Input
              </span>
              <span className="text-lg font-bold text-slate-700">{tokens.input ?? tokens.input_tokens ?? 0}</span>
            </div>
            <div className="bg-white p-3 rounded-lg border border-slate-200 shadow-sm flex flex-col items-center justify-center">
              <span className="text-[10px] uppercase text-slate-400 font-semibold mb-1 flex items-center gap-1">
                <ArrowLeft size={10} /> Output
              </span>
              <span className="text-lg font-bold text-slate-700">{tokens.output ?? tokens.output_tokens ?? 0}</span>
            </div>
            <div className="bg-white p-3 rounded-lg border border-slate-200 shadow-sm flex flex-col items-center justify-center relative overflow-hidden">
              <div className="absolute inset-0 bg-blue-50/50 z-0"></div>
              <span className="text-[10px] uppercase text-blue-500 font-semibold mb-1 flex items-center gap-1 relative z-10">
                <Cpu size={10} /> Total
              </span>
              <span className="text-lg font-bold text-blue-700 relative z-10">{tokens.total ?? tokens.total_tokens ?? 0}</span>
            </div>
          </div>
        )}

        {/* Input Section */}
        <Section title="Input Variables" icon={ArrowRight}>
          <DataDisplay data={inputData} />
        </Section>

        {/* Output Section */}
        <Section title="Output / Result" icon={ArrowLeft}>
          <DataDisplay data={outputData} />
        </Section>

        {/* Full State Snapshot */}
        <Section title="Full State Snapshot" icon={Database} defaultOpen={false}>
          <div className="bg-slate-50 rounded border border-slate-200 p-2 font-mono text-xs text-slate-600 overflow-x-auto">
            <pre>{JSON.stringify(data.state || {}, null, 2)}</pre>
          </div>
        </Section>

        {/* Debug Raw Frame */}
        <div className="opacity-50 hover:opacity-100 transition-opacity">
          <Section title="Debug: Raw Frame" icon={Code2} defaultOpen={false}>
            <div className="bg-slate-50 rounded border border-slate-200 p-2 font-mono text-[10px] text-slate-400 overflow-x-auto">
              <pre>{JSON.stringify(data || {}, null, 2)}</pre>
            </div>
          </Section>
        </div>
      </div>
    </div>
  );
}
