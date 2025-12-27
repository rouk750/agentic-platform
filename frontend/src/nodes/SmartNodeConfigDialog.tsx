import * as Dialog from '@radix-ui/react-dialog';
import { X, Loader2, Plus, Trash2, Brain, Zap, Sparkles } from 'lucide-react';
import { useForm, useFieldArray } from 'react-hook-form';
import { useEffect, useState } from 'react';
import { toast } from 'sonner';
import { getModels } from '../api/settings';
import type { LLMProfile } from '../types/settings';
import { optimizeNode, getAvailableGuardrails, type GuardrailDefinition } from '../api/smartNode';

import type { SmartNodeData, Example, IOSpec } from '../types/smartNode';
import type { GuardrailConfig } from '../api/smartNode';

interface SmartNodeOutput extends IOSpec {
  guardrail?: GuardrailConfig | null;
  guardrails?: GuardrailConfig[];
}

interface SmartNodeFormValues {
  label: string;
  goal: string;
  mode: 'ChainOfThought' | 'Predict';
  inputs: IOSpec[];
  outputs: SmartNodeOutput[];
  llm_profile: string;
}

interface SmartNodeConfigDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  data: SmartNodeData & { id?: string }; // Expect id might be merged in data for this dialog
  onUpdate: (data: SmartNodeData) => void;
}

export function SmartNodeConfigDialog({
  open,
  onOpenChange,
  data,
  onUpdate,
}: SmartNodeConfigDialogProps) {
  const { register, control, handleSubmit, reset, watch, setValue } = useForm({
    defaultValues: {
      label: data.label || 'Smart Node',
      goal: data.goal || '',
      mode: data.mode || 'ChainOfThought',
      inputs: data.inputs || [{ name: 'input', desc: 'Main input' }],
      outputs: data.outputs || [{ name: 'output', desc: 'Main output' }],
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      llm_profile: data.llm_profile ? (data.llm_profile as any).id?.toString() : '',
    },
    shouldUnregister: false, // Keep values validation state when unmounting components (switching tabs)
  });

  const {
    fields: inputFields,
    append: appendInput,
    remove: removeInput,
  } = useFieldArray({
    control,
    name: 'inputs',
  });

  const {
    fields: outputFields,
    append: appendOutput,
    remove: removeOutput,
  } = useFieldArray({
    control,
    name: 'outputs',
  });

  const [models, setModels] = useState<LLMProfile[]>([]);
  const [availableGuardrails, setAvailableGuardrails] = useState<GuardrailDefinition[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (open) {
      setLoading(true);
      Promise.all([
        getModels().then(setModels),
        getAvailableGuardrails().then(setAvailableGuardrails),
      ]).finally(() => setLoading(false));

      reset({
        label: data.label || 'Smart Node',
        goal: data.goal || '',
        mode: data.mode || 'ChainOfThought',
        inputs: data.inputs || [{ name: 'input', desc: 'Main input' }],
        outputs: data.outputs || [{ name: 'output', desc: 'Main output' }],
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        llm_profile: data.llm_profile ? (data.llm_profile as any).id?.toString() : '',
      });
    }
  }, [open, data, reset]);

  const onSubmit = (formData: SmartNodeFormValues, shouldClose: boolean = true) => {
    const selectedModel = models.find((m) => m.id?.toString() === formData.llm_profile);

    onUpdate({
      ...formData,
      llm_profile: selectedModel, // Store full profile object or reference
      examples: examples, // Ensure examples are saved with config
    });

    if (shouldClose) {
      onOpenChange(false);
    } else {
      toast.success('Configuration saved');
    }
  };

  const selectedMode = watch('mode');

  const [activeTab, setActiveTab] = useState<'config' | 'training'>('config');
  const [examples, setExamples] = useState<Example[]>(data.examples || []);
  const [maxRounds, setMaxRounds] = useState<number>(data.maxRounds || 10);
  const [isOptimizing, setIsOptimizing] = useState(false);
  const [optimizationResult, setOptimizationResult] = useState<any>(null);

  // Sync state when data changes
  useEffect(() => {
    if (open) {
      setExamples(data.examples || []);
      setMaxRounds(data.maxRounds || 10);
      setOptimizationResult(data.optimizationResult || null);
    }
  }, [open, data]);

  const handleAddExample = () => {
    const inputKeys = inputFields.map((f) => f.name).filter((n) => n);
    const outputKeys = outputFields.map((f) => f.name).filter((n) => n);

    if (inputKeys.length === 0 || outputKeys.length === 0) {
      alert('Please define Inputs and Outputs first in the Config tab.');
      return;
    }

    const newExample = {
      inputs: Object.fromEntries(inputKeys.map((k) => [k, ''])),
      outputs: Object.fromEntries(outputKeys.map((k) => [k, ''])),
    };
    setExamples([...examples, newExample]);
  };

  const handleUpdateExample = (
    index: number,
    type: 'inputs' | 'outputs',
    key: string,
    value: string
  ) => {
    const newExamples = [...examples];
    newExamples[index][type][key] = value;
    setExamples(newExamples);
  };

  const handleRemoveExample = (index: number) => {
    setExamples(examples.filter((_, i) => i !== index));
  };

  const handleOptimize = async () => {
    if (examples.length === 0) {
      alert('Add at least one example to optimize.');
      return;
    }

    const llmProfileId = watch('llm_profile');
    if (!llmProfileId) {
      alert('Please select an LLM Profile in Config tab.');
      return;
    }

    setIsOptimizing(true);
    try {
      // Save state *before* optimization to ensure examples aren't lost if it fails
      const formData = watch();
      const selectedModel = models.find((m) => m.id?.toString() === formData.llm_profile);

      // Initial save (without result yet)
      onUpdate({
        ...formData,
        llm_profile: selectedModel,
        examples: examples,
        maxRounds: maxRounds,
      });

      // Prepare request payload
      const payload = {
        node_id: (data.id || 'unknown_node') as string, // Assuming data has id from react flow node
        goal: watch('goal'),
        mode: watch('mode'),
        inputs: inputFields.map((f) => ({ name: f.name, desc: f.desc })),
        outputs: outputFields.map((f) => ({ name: f.name, desc: f.desc })),
        examples: examples,
        llm_profile_id: parseInt(llmProfileId),
        metric: 'exact_match',
        max_rounds: maxRounds,
      };

      const result = await optimizeNode(payload);
      setOptimizationResult(result);

      // Save again with result
      onUpdate({
        ...formData,
        llm_profile: selectedModel,
        examples: examples,
        maxRounds: maxRounds,
        optimizationResult: result,
      });
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : 'Unknown error';
      alert(`Optimization failed: ${msg}`);
    } finally {
      setIsOptimizing(false);
    }
  };

  // CSV Import Logic
  const [showPasteDialog, setShowPasteDialog] = useState(false);
  const [pasteContent, setPasteContent] = useState('');

  const parseCSV = (content: string) => {
    const lines = content.split(/\r?\n/).filter((line) => line.trim());
    if (lines.length < 2) {
      toast.error('CSV must have at least a header and one row.');
      return;
    }

    // Detect delimiter (comma or semicolon)
    const headerLine = lines[0];
    const delimiter = headerLine.includes(';') ? ';' : ',';

    // Simple CSV splitter handling quotes
    const splitCSV = (line: string) => {
      // const matches = line.match(/(".*?"|[^",\s]+)(?=\s*,|\s*$)/g) || [];
      // Fallback simplistic split if regex fails or too complex,
      // but for now let's use a simpler approach for standard CSV:
      // "val1","val2" or val1,val2

      // Better regex for standard CSV:
      const re =
        delimiter === ';' ? /(?:^|;)(?:"([^"]*)"|([^;]*))/g : /(?:^|,)(?:"([^"]*)"|([^,]*))/g;

      const res = [];
      let match;
      while ((match = re.exec(line))) {
        res.push(match[1] ? match[1] : match[2]); // match[1] is quoted, match[2] is unquoted
      }
      return res.length ? res : line.split(delimiter);
    };

    const headers = splitCSV(headerLine).map((h) => h?.trim().toLowerCase().replace(/^"|"$/g, ''));

    // Map headers to input/output keys
    const inputKeys = inputFields.map((f) => f.name);
    const outputKeys = outputFields.map((f) => f.name);

    const mapHeaderToKey = (header: string) => {
      // Exact match
      if (inputKeys.includes(header)) return { type: 'inputs', key: header };
      if (outputKeys.includes(header)) return { type: 'outputs', key: header };

      // Case insensitive match
      const inMatch = inputKeys.find((k) => k.toLowerCase() === header);
      if (inMatch) return { type: 'inputs' as const, key: inMatch };

      const outMatch = outputKeys.find((k) => k.toLowerCase() === header);
      if (outMatch) return { type: 'outputs' as const, key: outMatch };

      return null;
    };

    const columnMapping = headers.map((h) => mapHeaderToKey(h || ''));

    const newExamples = [];

    for (let i = 1; i < lines.length; i++) {
      const row = splitCSV(lines[i]);
      if (row.length === 0) continue;

      const example: Example = { inputs: {}, outputs: {} };
      let hasData = false;

      row.forEach((cell, idx) => {
        const map = columnMapping[idx];
        if (map && cell) {
          const cleanCell = cell.replace(/^"|"$/g, '').replace(/""/g, '"');
          // Use type assertion for dynamic access to Example keys
          const typeKey = map.type as keyof Example;
          (example[typeKey] as Record<string, string>)[map.key] = cleanCell;
          hasData = true;
        }
      });

      if (hasData) {
        // Ensure all keys exist even if empty
        inputKeys.forEach((k) => {
          if (!example.inputs[k]) example.inputs[k] = '';
        });
        outputKeys.forEach((k) => {
          if (!example.outputs[k]) example.outputs[k] = '';
        });
        newExamples.push(example);
      } else {
        // skipped++;
      }
    }

    if (newExamples.length > 0) {
      setExamples([...examples, ...newExamples]);
      toast.success(`Imported ${newExamples.length} examples.`);
      setShowPasteDialog(false);
      setPasteContent('');
    } else {
      toast.warning('No valid examples found. Check your headers.');
    }
  };

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = (evt) => {
      const content = evt.target?.result as string;
      if (content) parseCSV(content);
    };
    reader.readAsText(file);
    // Reset input
    e.target.value = '';
  };

  return (
    <Dialog.Root open={open} onOpenChange={onOpenChange}>
      <Dialog.Portal>
        <Dialog.Overlay className="fixed inset-0 bg-black/50 z-50 backdrop-blur-sm" />
        <Dialog.Content className="fixed top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-full max-w-4xl bg-white rounded-xl shadow-2xl z-50 p-0 border border-slate-200 overflow-hidden flex flex-col max-h-[90vh]">
          {/* Header */}
          <div className="flex justify-between items-center p-6 border-b border-slate-100 bg-slate-50/50">
            <div className="flex items-center gap-4">
              <Dialog.Title className="text-xl font-bold text-slate-800 flex items-center gap-2">
                <span className="text-amber-600 bg-amber-50 px-2 py-1 rounded text-xs uppercase tracking-wide flex items-center gap-1">
                  <Sparkles size={12} /> Beta
                </span>
                Smart Node Configuration
              </Dialog.Title>

              {/* Tab Switcher */}
              <div className="flex bg-slate-100 p-1 rounded-lg">
                <button
                  onClick={() => setActiveTab('config')}
                  className={`px-3 py-1.5 text-sm font-medium rounded-md transition-all ${activeTab === 'config' ? 'bg-white text-slate-900 shadow-sm' : 'text-slate-500 hover:text-slate-700'}`}
                >
                  Configuration
                </button>
                <button
                  onClick={() => setActiveTab('training')}
                  className={`px-3 py-1.5 text-sm font-medium rounded-md transition-all ${activeTab === 'training' ? 'bg-white text-amber-600 shadow-sm' : 'text-slate-500 hover:text-slate-700'}`}
                >
                  Training & Data
                </button>
              </div>
            </div>

            <Dialog.Close className="text-slate-400 hover:text-slate-600">
              <X size={20} />
            </Dialog.Close>
          </div>

          <div className="flex-1 overflow-y-auto p-6 bg-slate-50/30">
            {activeTab === 'config' ? (
              <form
                id="config-form"
                onSubmit={handleSubmit((data) => onSubmit(data, true))}
                className="flex flex-col gap-6 overflow-y-auto pr-2 min-h-0"
              >
                {/* General Settings */}
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <label className="text-sm font-semibold text-slate-700">Node Label</label>
                    <input
                      {...register('label')}
                      placeholder="e.g. Summarizer"
                      className="w-full p-2.5 rounded-lg border border-slate-300 bg-white text-sm focus:ring-2 focus:ring-amber-500 focus:border-amber-500 outline-none transition-all"
                    />
                  </div>
                  <div className="space-y-2">
                    <label className="text-sm font-semibold text-slate-700">LLM Profile</label>
                    {loading ? (
                      <div className="flex items-center gap-2 text-sm text-slate-500">
                        <Loader2 size={16} className="animate-spin" /> Loading...
                      </div>
                    ) : (
                      <select
                        {...register('llm_profile')}
                        className="w-full p-2.5 rounded-lg border border-slate-300 bg-white text-sm focus:ring-2 focus:ring-amber-500 focus:border-amber-500 outline-none transition-all"
                      >
                        <option value="">Select a model...</option>
                        {models.map((m) => (
                          <option key={m.id} value={m.id?.toString()}>
                            {m.name} ({m.provider})
                          </option>
                        ))}
                      </select>
                    )}
                  </div>
                </div>

                {/* Mode Selection */}
                <div className="space-y-3">
                  <label className="text-sm font-semibold text-slate-700">
                    Reasoning Mode (DSPy Module)
                  </label>
                  <div className="grid grid-cols-2 gap-4">
                    <div
                      className={`cursor-pointer border-2 rounded-xl p-4 flex flex-col gap-2 transition-all ${selectedMode === 'ChainOfThought' ? 'border-amber-500 bg-amber-50/50 ring-1 ring-amber-500/20' : 'border-slate-200 hover:border-slate-300'}`}
                      // eslint-disable-next-line @typescript-eslint/no-explicit-any
                      onClick={() => setValue('mode', 'ChainOfThought' as any)}
                    >
                      <div className="flex items-center gap-2 font-semibold text-amber-700">
                        <Brain size={18} />
                        ChainOfThought
                      </div>
                      <p className="text-xs text-slate-500">
                        Best for reasoning, explanation, and complex tasks. Generates rationale
                        before answer.
                      </p>
                    </div>

                    <div
                      className={`cursor-pointer border-2 rounded-xl p-4 flex flex-col gap-2 transition-all ${selectedMode === 'Predict' ? 'border-blue-500 bg-blue-50/50 ring-1 ring-blue-500/20' : 'border-slate-200 hover:border-slate-300'}`}
                      // eslint-disable-next-line @typescript-eslint/no-explicit-any
                      onClick={() => setValue('mode', 'Predict' as any)}
                    >
                      <div className="flex items-center gap-2 font-semibold text-blue-700">
                        <Zap size={18} />
                        Predict
                      </div>
                      <p className="text-xs text-slate-500">
                        Best for simple extraction, classification, or strict output formats.
                        Cheaper & faster.
                      </p>
                    </div>
                  </div>
                </div>

                {/* Goal */}
                <div className="space-y-2">
                  <label className="text-sm font-semibold text-slate-700">
                    Goal / Instructions
                  </label>
                  <textarea
                    {...register('goal')}
                    placeholder="Describe what this node should do. Be specific."
                    className="w-full p-3 rounded-lg border border-slate-300 bg-white text-sm focus:ring-2 focus:ring-amber-500 focus:border-amber-500 outline-none transition-all h-24 resize-none font-mono"
                  />
                  <p className="text-[10px] text-slate-400">
                    This will be compiled into the DSPy signature instructions.
                  </p>
                </div>

                {/* Inputs & Outputs (The Signature) */}
                <div className="grid grid-cols-2 gap-8 border-t border-slate-100 pt-6">
                  {/* Inputs */}
                  <div className="space-y-3">
                    <div className="flex items-center justify-between">
                      <label className="text-sm font-semibold text-blue-600">Inputs</label>
                      <button
                        type="button"
                        className="text-xs flex items-center gap-1 text-slate-600 hover:text-blue-600 border border-slate-200 hover:border-blue-200 px-2 py-1 rounded transition-colors"
                        onClick={() => appendInput({ name: '', desc: '' })}
                      >
                        <Plus size={14} /> Add User Input
                      </button>
                    </div>
                    <div className="space-y-2">
                      {inputFields.map((field, index) => (
                        <div key={field.id} className="flex gap-2 items-start">
                          <div className="grid gap-1 flex-1">
                            <input
                              {...register(`inputs.${index}.name`)}
                              placeholder="Field name (e.g. question)"
                              className="w-full text-xs p-1.5 rounded border border-slate-300 font-mono focus:border-blue-500 outline-none"
                            />
                            <input
                              {...register(`inputs.${index}.desc`)}
                              placeholder="Description"
                              className="w-full text-xs p-1.5 rounded border border-slate-300 focus:border-blue-500 outline-none"
                            />
                          </div>
                          <button
                            type="button"
                            className="p-1.5 text-slate-400 hover:text-red-500 hover:bg-red-50 rounded transition-colors"
                            onClick={() => removeInput(index)}
                          >
                            <Trash2 size={14} />
                          </button>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Outputs */}
                  <div className="space-y-3">
                    <div className="flex items-center justify-between">
                      <label className="text-sm font-semibold text-green-600">Outputs</label>
                      <button
                        type="button"
                        className="text-xs flex items-center gap-1 text-slate-600 hover:text-green-600 border border-slate-200 hover:border-green-200 px-2 py-1 rounded transition-colors"
                        onClick={() => appendOutput({ name: '', desc: '' })}
                      >
                        <Plus size={14} /> Add AI Field
                      </button>
                    </div>
                    <div className="space-y-2">
                      {outputFields.map((field, index) => {
                        // Cast paths to any to avoid strict type checking on array indices
                        // eslint-disable-next-line @typescript-eslint/no-explicit-any
                        const currentLegacyGuardrail = watch(`outputs.${index}.guardrail` as any);
                        // eslint-disable-next-line @typescript-eslint/no-explicit-any
                        const currentGuardrails = watch(`outputs.${index}.guardrails` as any) || [];

                        // Combine legacy and new list for display
                        const activeGuardrails =
                          currentGuardrails.length > 0
                            ? currentGuardrails
                            : currentLegacyGuardrail
                              ? [currentLegacyGuardrail]
                              : [];

                        // Helper to update specific guardrail in list
                        const updateGuardrail = (gIndex: number, newG: GuardrailConfig) => {
                          const newErrors = [...activeGuardrails];
                          newErrors[gIndex] = newG;
                          // eslint-disable-next-line @typescript-eslint/no-explicit-any
                          setValue(`outputs.${index}.guardrails` as any, newErrors);
                          // Clear legacy to avoid confusion if we are now using list
                          // eslint-disable-next-line @typescript-eslint/no-explicit-any
                          setValue(`outputs.${index}.guardrail` as any, null);
                        };

                        const addGuardrail = () => {
                          const newList: GuardrailConfig[] = [
                            ...activeGuardrails,
                            { id: 'json', params: {} },
                          ];
                          // eslint-disable-next-line @typescript-eslint/no-explicit-any
                          setValue(`outputs.${index}.guardrails` as any, newList);
                          // eslint-disable-next-line @typescript-eslint/no-explicit-any
                          setValue(`outputs.${index}.guardrail` as any, null);
                        };

                        const removeGuardrail = (gIndex: number) => {
                          const newG = activeGuardrails.filter(
                            (_: unknown, i: number) => i !== gIndex
                          );
                          // eslint-disable-next-line @typescript-eslint/no-explicit-any
                          setValue(`outputs.${index}.guardrails` as any, newG);
                          // eslint-disable-next-line @typescript-eslint/no-explicit-any
                          setValue(`outputs.${index}.guardrail` as any, null);
                        };

                        return (
                          <div
                            key={field.id}
                            className="flex gap-2 items-start bg-slate-50 p-3 rounded-lg border border-slate-100 mb-2"
                          >
                            <div className="grid gap-3 flex-1">
                              {/* Basic Fields */}
                              <div className="flex gap-2">
                                <input
                                  {...register(`outputs.${index}.name`)}
                                  placeholder="Field name (e.g. answer)"
                                  className="w-1/3 text-xs p-2 rounded border border-slate-300 font-mono focus:border-green-500 outline-none"
                                />
                                <input
                                  {...register(`outputs.${index}.desc`)}
                                  placeholder="Description"
                                  className="flex-1 text-xs p-2 rounded border border-slate-300 focus:border-green-500 outline-none"
                                />
                              </div>

                              {/* Guardrails List */}
                              <div className="space-y-2">
                                {activeGuardrails.map((g: GuardrailConfig, gIndex: number) => (
                                  <div
                                    key={gIndex}
                                    className="flex items-start gap-2 bg-white p-2 rounded border border-slate-200 shadow-sm"
                                  >
                                    <div className="flex-1">
                                      <select
                                        className="w-full text-xs p-1.5 rounded border border-slate-200 text-slate-700 outline-none focus:border-amber-500 mb-1"
                                        value={g.id}
                                        onChange={(e) =>
                                          updateGuardrail(gIndex, {
                                            ...g,
                                            id: e.target.value,
                                            params: {},
                                          })
                                        }
                                      >
                                        {availableGuardrails.map((def) => (
                                          <option key={def.id} value={def.id}>
                                            {def.label}
                                          </option>
                                        ))}
                                      </select>

                                      {/* Description */}
                                      <div className="text-[10px] text-slate-500 mb-2 px-1">
                                        {
                                          availableGuardrails.find((def) => def.id === g.id)
                                            ?.description
                                        }
                                      </div>

                                      {/* Dynamic Params */}
                                      {availableGuardrails
                                        .find((def) => def.id === g.id)
                                        ?.params.map((param) => (
                                          <div key={param.name} className="mt-1">
                                            <label className="text-[10px] font-semibold text-slate-500 uppercase mb-0.5 block">
                                              {param.label}
                                            </label>
                                            <input
                                              type={param.type === 'number' ? 'number' : 'text'}
                                              value={g.params?.[param.name] || ''}
                                              onChange={(e) => {
                                                const val =
                                                  param.type === 'number'
                                                    ? parseFloat(e.target.value)
                                                    : e.target.value;
                                                updateGuardrail(gIndex, {
                                                  ...g,
                                                  params: { ...g.params, [param.name]: val },
                                                });
                                              }}
                                              className="w-full text-xs p-1.5 rounded border border-slate-100 bg-slate-50 outline-none focus:border-amber-500"
                                              placeholder={param.label}
                                            />
                                          </div>
                                        ))}
                                    </div>
                                    <button
                                      type="button"
                                      onClick={() => removeGuardrail(gIndex)}
                                      className="text-slate-400 hover:text-red-500 p-1"
                                    >
                                      <Trash2 size={12} />
                                    </button>
                                  </div>
                                ))}

                                <button
                                  type="button"
                                  onClick={addGuardrail}
                                  className="text-[10px] font-medium text-amber-600 hover:text-amber-700 flex items-center gap-1 py-1 px-2 hover:bg-amber-50 rounded transition-colors w-fit"
                                >
                                  <Plus size={12} /> Add Guardrail
                                </button>
                              </div>
                            </div>
                            <button
                              type="button"
                              className="p-1.5 text-slate-400 hover:text-red-500 hover:bg-red-50 rounded transition-colors"
                              onClick={() => removeOutput(index)}
                            >
                              <Trash2 size={14} />
                            </button>
                          </div>
                        );
                      })}
                    </div>
                  </div>
                </div>
              </form>
            ) : (
              <div className="space-y-6">
                <div className="flex items-center justify-between">
                  <p className="text-sm text-slate-600">
                    Providing examples helps DSPy learn the best way to prompt the LLM for your
                    specific task.
                    <br />
                    Add at least 5-10 varied examples for best results.
                  </p>
                  <div className="flex items-center gap-2">
                    <button
                      onClick={handleAddExample}
                      className="px-3 py-1.5 text-xs font-medium bg-white border border-slate-200 text-slate-700 hover:bg-slate-50 rounded-lg flex items-center gap-1.5 transition-colors"
                    >
                      <Plus size={14} /> Add Example
                    </button>
                    <button
                      onClick={() => setShowPasteDialog(true)}
                      className="px-3 py-1.5 text-xs font-medium bg-white border border-slate-200 text-slate-700 hover:bg-slate-50 rounded-lg flex items-center gap-1.5 transition-colors"
                    >
                      📋 Import CSV
                    </button>
                    <label className="px-3 py-1.5 text-xs font-medium bg-white border border-slate-200 text-slate-700 hover:bg-slate-50 rounded-lg flex items-center gap-1.5 transition-colors cursor-pointer">
                      📂 Upload
                      <input
                        type="file"
                        accept=".csv,.txt"
                        className="hidden"
                        onChange={handleFileUpload}
                      />
                    </label>
                    <div className="flex items-center gap-2 border-r border-slate-200 pr-3 mr-1">
                      <label className="text-xs font-semibold text-slate-500 whitespace-nowrap">
                        Rounds:
                      </label>
                      <input
                        type="number"
                        min="1"
                        max="50"
                        value={maxRounds}
                        onChange={(e) =>
                          setMaxRounds(Math.max(1, Math.min(50, parseInt(e.target.value) || 1)))
                        }
                        className="w-12 text-xs p-1 rounded border border-slate-200 text-center focus:border-amber-500 outline-none"
                        title="Optimization Attempts (Max Rounds)"
                      />
                    </div>
                    <button
                      onClick={handleOptimize}
                      disabled={isOptimizing}
                      className="px-3 py-1.5 text-xs font-medium bg-amber-600 text-white hover:bg-amber-700 rounded-lg flex items-center gap-1.5 transition-colors disabled:opacity-50"
                    >
                      {isOptimizing ? (
                        <Loader2 size={14} className="animate-spin" />
                      ) : (
                        <Sparkles size={14} />
                      )}
                      {isOptimizing ? 'Optimizing...' : 'Compile & Optimize'}
                    </button>
                  </div>
                </div>

                {optimizationResult && (
                  <div className="bg-green-50 border border-green-200 rounded-lg p-3 text-sm text-green-800 flex items-center justify-between">
                    <span className="flex items-center gap-2">
                      <Sparkles size={14} /> Node Optimized Successfully!
                    </span>
                    <span className="font-bold">Score: {optimizationResult.score}</span>
                  </div>
                )}

                <div className="bg-white border border-slate-200 rounded-xl overflow-hidden shadow-sm">
                  <table className="w-full text-sm">
                    <thead className="bg-slate-50 border-b border-slate-200 text-slate-600 font-semibold">
                      <tr>
                        <th className="p-3 text-left w-10">#</th>
                        <th className="p-3 text-left border-r border-slate-200 w-1/2">
                          <span className="text-blue-600">INPUTS</span>
                        </th>
                        <th className="p-3 text-left w-1/2">
                          <span className="text-green-600">OUTPUTS (Expected)</span>
                        </th>
                        <th className="p-3 w-10"></th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100">
                      {examples.map((ex, index) => (
                        <tr key={index} className="group hover:bg-slate-50/50">
                          <td className="p-3 text-slate-400 font-mono text-xs">{index + 1}</td>
                          <td className="p-3 border-r border-slate-200 align-top">
                            <div className="space-y-2">
                              {Object.entries(ex.inputs).map(([key, val]) => (
                                <div key={key}>
                                  <label className="text-[10px] text-blue-400 uppercase font-mono block mb-0.5">
                                    {key}
                                  </label>
                                  <textarea
                                    value={val as string}
                                    onChange={(e) =>
                                      handleUpdateExample(index, 'inputs', key, e.target.value)
                                    }
                                    className="w-full text-xs p-1.5 rounded border border-slate-200 focus:border-blue-500 outline-none resize-y min-h-[40px]"
                                  />
                                </div>
                              ))}
                            </div>
                          </td>
                          <td className="p-3 align-top">
                            <div className="space-y-2">
                              {Object.entries(ex.outputs).map(([key, val]) => (
                                <div key={key}>
                                  <label className="text-[10px] text-green-400 uppercase font-mono block mb-0.5">
                                    {key}
                                  </label>
                                  <textarea
                                    value={val as string}
                                    onChange={(e) =>
                                      handleUpdateExample(index, 'outputs', key, e.target.value)
                                    }
                                    className="w-full text-xs p-1.5 rounded border border-slate-200 focus:border-green-500 outline-none resize-y min-h-[40px]"
                                  />
                                </div>
                              ))}
                            </div>
                          </td>
                          <td className="p-3 text-center align-top pt-8">
                            <button
                              onClick={() => handleRemoveExample(index)}
                              className="text-slate-300 hover:text-red-500 transition-colors"
                            >
                              <Trash2 size={14} />
                            </button>
                          </td>
                        </tr>
                      ))}
                      {examples.length === 0 && (
                        <tr>
                          <td colSpan={4} className="p-8 text-center text-slate-400 italic">
                            No examples yet. Click &quot;Add Example&quot; to start teaching your
                            node.
                          </td>
                        </tr>
                      )}
                    </tbody>
                  </table>
                </div>
              </div>
            )}
          </div>

          <div className="flex justify-end gap-3 p-6 border-t border-slate-100 bg-slate-50/50 shrink-0">
            {activeTab === 'config' ? (
              <>
                <button
                  type="button"
                  onClick={() => onOpenChange(false)}
                  className="px-4 py-2 text-sm font-medium text-slate-600 hover:bg-slate-100 rounded-lg transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="button"
                  onClick={handleSubmit((data) => {
                    onSubmit(data, false);
                  })}
                  className="px-4 py-2 text-sm font-medium text-amber-700 bg-amber-100 hover:bg-amber-200 rounded-lg transition-colors"
                >
                  Save
                </button>
                <button
                  type="submit"
                  form="config-form"
                  className="px-4 py-2 text-sm font-medium text-white bg-amber-600 hover:bg-amber-700 rounded-lg shadow-sm transition-colors"
                >
                  Save & Close
                </button>
              </>
            ) : (
              <>
                <button
                  type="button"
                  onClick={() => onOpenChange(false)}
                  className="px-4 py-2 text-sm font-medium text-slate-600 hover:bg-slate-100 rounded-lg transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="button"
                  onClick={() => {
                    const formData = watch();
                    const selectedModel = models.find(
                      (m) => m.id?.toString() === formData.llm_profile
                    );
                    onUpdate({
                      ...formData,
                      llm_profile: selectedModel,
                      examples,
                      maxRounds,
                      optimizationResult,
                    });
                    toast.success('Training data saved');
                  }}
                  className="px-4 py-2 text-sm font-medium text-amber-700 bg-amber-100 hover:bg-amber-200 rounded-lg transition-colors"
                >
                  Save
                </button>
                <button
                  type="button"
                  onClick={() => {
                    // Save examples manually since outside form
                    const formData = watch();
                    const selectedModel = models.find(
                      (m) => m.id?.toString() === formData.llm_profile
                    );
                    onUpdate({
                      ...formData,
                      llm_profile: selectedModel,
                      examples,
                      maxRounds,
                      optimizationResult,
                    });
                    onOpenChange(false);
                  }}
                  className="px-4 py-2 text-sm font-medium text-white bg-amber-600 hover:bg-amber-700 rounded-lg shadow-sm transition-colors"
                >
                  Save & Close
                </button>
              </>
            )}
          </div>
        </Dialog.Content>
      </Dialog.Portal>

      {/* Paste CSV Dialog */}
      <Dialog.Root open={showPasteDialog} onOpenChange={setShowPasteDialog}>
        <Dialog.Portal>
          <Dialog.Overlay className="fixed inset-0 bg-black/40 backdrop-blur-sm z-[60]" />
          <Dialog.Content className="fixed top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-full max-w-lg bg-white rounded-xl shadow-xl border border-slate-200 p-6 z-[61] outline-none">
            <Dialog.Title className="text-lg font-semibold text-slate-800 mb-2">
              Import CSV
            </Dialog.Title>
            <Dialog.Description className="text-sm text-slate-500 mb-4">
              Paste your CSV content below. The first row must contain headers matching your
              Input/Output names.
            </Dialog.Description>

            <textarea
              className="w-full h-64 p-3 text-xs font-mono border border-slate-200 rounded-lg focus:ring-2 focus:ring-amber-500 focus:border-amber-500 outline-none resize-none bg-slate-50"
              placeholder={'input_name,output_name\n"Sample Input","Sample Output"...'}
              value={pasteContent}
              onChange={(e) => setPasteContent(e.target.value)}
            />

            <div className="flex justify-end gap-3 mt-4">
              <button
                onClick={() => setShowPasteDialog(false)}
                className="px-4 py-2 text-sm font-medium text-slate-600 hover:bg-slate-100 rounded-lg transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={() => parseCSV(pasteContent)}
                disabled={!pasteContent.trim()}
                className="px-4 py-2 text-sm font-medium text-white bg-amber-600 hover:bg-amber-700 rounded-lg shadow-sm transition-colors disabled:opacity-50"
              >
                Import
              </button>
            </div>
          </Dialog.Content>
        </Dialog.Portal>
      </Dialog.Root>
    </Dialog.Root>
  );
}
