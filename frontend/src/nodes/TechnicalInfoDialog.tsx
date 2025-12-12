import * as Dialog from '@radix-ui/react-dialog';
import { X, Code } from 'lucide-react';
import React from 'react';

interface TechnicalInfoDialogProps {
    open: boolean;
    onOpenChange: (open: boolean) => void;
    data: any;
}

export function TechnicalInfoDialog({ open, onOpenChange, data }: TechnicalInfoDialogProps) {
    return (
        <Dialog.Root open={open} onOpenChange={onOpenChange}>
            <Dialog.Portal>
                <Dialog.Overlay className="fixed inset-0 bg-black/50 z-50 backdrop-blur-sm" />
                <Dialog.Content className="fixed top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-full max-w-2xl bg-white rounded-xl shadow-2xl z-50 p-0 border border-slate-200 overflow-hidden flex flex-col max-h-[80vh]">

                    {/* Header */}
                    <div className="flex justify-between items-center p-4 border-b border-slate-100 bg-slate-50/50">
                        <div className="flex items-center gap-2">
                            <div className="p-2 bg-slate-200 text-slate-600 rounded-lg">
                                <Code size={18} />
                            </div>
                            <div>
                                <Dialog.Title className="text-lg font-bold text-slate-800">
                                    Technical Details
                                </Dialog.Title>
                                <div className="text-xs text-slate-500 font-mono">
                                    Node ID: {data.id}
                                </div>
                            </div>
                        </div>

                        <Dialog.Close className="text-slate-400 hover:text-slate-600 p-1 rounded-md hover:bg-slate-100 transition-colors">
                            <X size={20} />
                        </Dialog.Close>
                    </div>

                    {/* Content */}
                    <div className="flex-1 overflow-auto p-0 bg-slate-900">
                        <pre className="p-4 text-xs font-mono text-emerald-400 leading-relaxed">
                            {JSON.stringify(data, null, 2)}
                        </pre>
                    </div>

                    {/* Footer */}
                    <div className="p-3 border-t border-slate-100 bg-slate-50 flex justify-end">
                        <button
                            onClick={() => onOpenChange(false)}
                            className="px-4 py-2 text-sm font-medium text-slate-600 hover:bg-slate-100 rounded-lg transition-colors"
                        >
                            Close
                        </button>
                    </div>
                </Dialog.Content>
            </Dialog.Portal>
        </Dialog.Root>
    );
}
