import { useState, useEffect } from 'react';
import { useForm } from 'react-hook-form';
import * as Dialog from '@radix-ui/react-dialog';
import { X, Check, Loader2, AlertCircle } from 'lucide-react';
import { createModel, testConnection, scanOllamaModels, scanLMStudioModels } from '../../api/settings';

interface AddModelDialogProps {
    open: boolean;
    onOpenChange: (open: boolean) => void;
    onModelAdded: () => void;
}

type FormData = {
    name: string;
    provider: string;
    model_id: string;
    api_key?: string;
    base_url?: string;
};

const PROVIDERS = [
    { value: 'openai', label: 'OpenAI' },
    { value: 'anthropic', label: 'Anthropic' },
    { value: 'ollama', label: 'Ollama (Local)' },
    { value: 'lmstudio', label: 'LM Studio (Local)' },
    { value: 'mistral', label: 'Mistral AI' },
    { value: 'bedrock', label: 'Amazon Bedrock' },
];

export function AddModelDialog({ open, onOpenChange, onModelAdded }: AddModelDialogProps) {
    const { register, handleSubmit, watch, setValue, reset, formState: { errors } } = useForm<FormData>({
        defaultValues: {
            provider: 'openai',
            base_url: 'http://localhost:11434'
        }
    });

    const [testing, setTesting] = useState(false);
    const [testStatus, setTestStatus] = useState<'idle' | 'success' | 'error'>('idle');
    const [scannedModels, setScannedModels] = useState<string[]>([]);
    const [scanning, setScanning] = useState(false);

    const selectedProvider = watch('provider');

    // Update base_url default based on provider
    useEffect(() => {
        if (selectedProvider === 'ollama') {
            setValue('base_url', 'http://localhost:11434');
        } else if (selectedProvider === 'lmstudio') {
            setValue('base_url', 'http://localhost:1234/v1');
        }
    }, [selectedProvider, setValue]);

    useEffect(() => {
        if (selectedProvider === 'ollama' || selectedProvider === 'lmstudio') {
            scanModels();
        } else {
            setScannedModels([]);
        }
    }, [selectedProvider]);

    const scanModels = async () => {
        setScanning(true);
        let models: string[] = [];
        if (selectedProvider === 'ollama') {
            models = await scanOllamaModels();
        } else if (selectedProvider === 'lmstudio') {
            models = await scanLMStudioModels();
        }
        setScannedModels(models);
        setScanning(false);
    };

    const onTestConnection = async () => {
        const data = watch();
        if (!data.model_id) return;

        setTesting(true);
        setTestStatus('idle');
        const success = await testConnection(data.provider, data.model_id, data.api_key, data.base_url);
        setTesting(false);
        setTestStatus(success ? 'success' : 'error');
    };

    const onSubmit = async (data: FormData) => {
        try {
            await createModel(data);
            onModelAdded();
            onOpenChange(false);
            reset();
            setTestStatus('idle');
        } catch (error) {
            console.error(error);
            // Handle error (could show toast)
        }
    };

    return (
        <Dialog.Root open={open} onOpenChange={onOpenChange}>
            <Dialog.Portal>
                <Dialog.Overlay className="fixed inset-0 bg-black/50 z-50 backdro-blur-sm" />
                <Dialog.Content className="fixed left-[50%] top-[50%] max-h-[85vh] w-[90vw] max-w-[500px] translate-x-[-50%] translate-y-[-50%] rounded-lg bg-slate-100 p-6 shadow-lg focus:outline-none z-50 border border-slate-200">
                    <div className="flex items-center justify-between mb-4">
                        <Dialog.Title className="text-lg font-semibold text-slate-900">
                            Add New Model
                        </Dialog.Title>
                        <Dialog.Close asChild>
                            <button className="text-slate-500 hover:text-slate-700" aria-label="Close">
                                <X size={20} />
                            </button>
                        </Dialog.Close>
                    </div>

                    <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
                        <div>
                            <label className="block text-sm font-medium mb-1 text-slate-700">Name</label>
                            <input
                                {...register('name', { required: true })}
                                className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white text-slate-900"
                                placeholder="My Awesome Model"
                            />
                            {errors.name && <span className="text-xs text-red-500">Name is required</span>}
                        </div>

                        <div>
                            <label className="block text-sm font-medium mb-1 text-slate-700">Provider</label>
                            <select
                                {...register('provider')}
                                className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white text-slate-900"
                            >
                                {PROVIDERS.map(p => (
                                    <option key={p.value} value={p.value}>{p.label}</option>
                                ))}
                            </select>
                        </div>

                        {['ollama', 'lmstudio'].includes(selectedProvider) ? (
                            <>
                                <div>
                                    <label className="block text-sm font-medium mb-1 text-slate-700">Model ID</label>
                                    {scanning ? (
                                        <div className="flex items-center gap-2 text-sm text-slate-500">
                                            <Loader2 className="animate-spin" size={14} /> Scanning Local Models...
                                        </div>
                                    ) : (
                                        <div className="flex gap-2">
                                            <select
                                                {...register('model_id', { required: true })}
                                                className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white text-slate-900"
                                            >
                                                <option value="">Select a model...</option>
                                                {scannedModels.map(m => <option key={m} value={m}>{m}</option>)}
                                            </select>
                                            <button type="button" onClick={scanModels} className="text-xs bg-white px-2 rounded border border-slate-300 text-slate-700 hover:bg-slate-50">Rescan</button>
                                        </div>
                                    )}
                                </div>
                                <div>
                                    <label className="block text-sm font-medium mb-1 text-slate-700">Base URL</label>
                                    <input
                                        {...register('base_url')}
                                        className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white text-slate-900"
                                        placeholder={selectedProvider === 'lmstudio' ? "http://localhost:1234/v1" : "http://localhost:11434"}
                                    />
                                </div>
                            </>
                        ) : (
                            <>
                                <div>
                                    <label className="block text-sm font-medium mb-1 text-slate-700">Model ID</label>
                                    <input
                                        {...register('model_id', { required: true })}
                                        className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white text-slate-900"
                                        placeholder={selectedProvider === 'openai' ? 'gpt-4-turbo' : 'claude-3-opus'}
                                    />
                                </div>
                                <div>
                                    <label className="block text-sm font-medium mb-1 text-slate-700">API Key</label>
                                    <input
                                        type="password"
                                        {...register('api_key', { required: true })}
                                        className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white text-slate-900"
                                        placeholder="sk-..."
                                    />
                                </div>
                            </>
                        )}

                        <div className="flex items-center justify-between pt-4">
                            <button
                                type="button"
                                onClick={onTestConnection}
                                disabled={testing}
                                className={`flex items-center gap-2 px-3 py-2 rounded-md text-sm font-medium transition-colors
                  ${testStatus === 'success' ? 'text-green-700 bg-green-50 border border-green-200' : ''}
                  ${testStatus === 'error' ? 'text-red-700 bg-red-50 border border-red-200' : ''}
                  ${testStatus === 'idle' ? 'text-slate-700 bg-white hover:bg-slate-50 border border-slate-300' : ''}
                `}
                            >
                                {testing ? <Loader2 className="animate-spin" size={16} /> :
                                    testStatus === 'success' ? <Check size={16} /> :
                                        testStatus === 'error' ? <AlertCircle size={16} /> : null
                                }
                                {testing ? 'Testing...' : testStatus === 'success' ? 'Connection Verified' : testStatus === 'error' ? 'Connection Failed' : 'Test Connection'}
                            </button>

                            <button
                                type="submit"
                                className="bg-blue-600 text-white px-4 py-2 rounded-md text-sm font-medium hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                            >
                                Save Model
                            </button>
                        </div>
                    </form>
                </Dialog.Content>
            </Dialog.Portal>
        </Dialog.Root>
    );
}
