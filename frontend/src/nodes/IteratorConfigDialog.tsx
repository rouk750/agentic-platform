import * as Dialog from '@radix-ui/react-dialog';
import { X, RefreshCw } from 'lucide-react';
import { useState, useEffect } from 'react';

interface IteratorConfigDialogProps {
    open: boolean;
    onOpenChange: (open: boolean) => void;
    data: any;
    onUpdate: (data: any) => void;
}

export function IteratorConfigDialog({ open, onOpenChange, data, onUpdate }: IteratorConfigDialogProps) {
    const [label, setLabel] = useState(data.label || "Iterator");
    const [inputVar, setInputVar] = useState(data.input_list_variable || "items");
    const [outputVar, setOutputVar] = useState(data.output_item_variable || "current_item");

    useEffect(() => {
        if (open) {
            setLabel(data.label || "Iterator");
            setInputVar(data.input_list_variable || "items");
            setOutputVar(data.output_item_variable || "current_item");
        }
    }, [open, data]);

    const handleSave = () => {
        onUpdate({
            ...data,
            label,
            input_list_variable: inputVar,
            output_item_variable: outputVar
        });
        onOpenChange(false);
    };

    return (
        <Dialog.Root open={open} onOpenChange={onOpenChange}>
            <Dialog.Portal>
                <Dialog.Overlay className="fixed inset-0 bg-black/50 z-50 backdrop-blur-sm transition-all duration-200" />
                <Dialog.Content className="fixed left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 w-full max-w-md bg-white rounded-xl shadow-2xl border border-slate-200 z-50 overflow-hidden outline-none">

                    {/* Header */}
                    <div className="flex items-center justify-between p-4 border-b border-slate-100 bg-slate-50/50">
                        <Dialog.Title className="text-lg font-semibold text-slate-800 flex items-center gap-2">
                            <RefreshCw size={20} className="text-orange-600" />
                            Configure Iterator
                        </Dialog.Title>
                        <Dialog.Close className="p-1 hover:bg-slate-200 rounded-full transition-colors text-slate-500">
                            <X size={20} />
                        </Dialog.Close>
                    </div>

                    {/* Body */}
                    <div className="p-6 space-y-6">
                        {/* Label */}
                        <div className="space-y-2">
                            <label className="text-sm font-semibold text-slate-700">Node Label</label>
                            <input
                                value={label}
                                onChange={(e) => setLabel(e.target.value)}
                                className="w-full p-2 text-sm border border-slate-200 rounded-lg focus:ring-2 focus:ring-orange-500 focus:border-orange-500 outline-none transition-all"
                                placeholder="Node Name"
                            />
                        </div>

                        {/* Input List Variable */}
                        <div className="space-y-2">
                            <label className="text-sm font-semibold text-slate-700">Input List Variable</label>
                            <input
                                value={inputVar}
                                onChange={(e) => setInputVar(e.target.value)}
                                className="w-full p-2 text-sm border border-slate-200 rounded-lg focus:ring-2 focus:ring-orange-500 focus:border-orange-500 outline-none transition-all"
                                placeholder="e.g. items"
                            />
                            <p className="text-xs text-slate-500">
                                The name of the variable in the state (context) that contains the list to iterate over.
                            </p>
                        </div>

                        {/* Output Item Variable */}
                        <div className="space-y-2">
                            <label className="text-sm font-semibold text-slate-700">Output Item Variable</label>
                            <input
                                value={outputVar}
                                onChange={(e) => setOutputVar(e.target.value)}
                                className="w-full p-2 text-sm border border-slate-200 rounded-lg focus:ring-2 focus:ring-orange-500 focus:border-orange-500 outline-none transition-all"
                                placeholder="e.g. current_item"
                            />
                            <p className="text-xs text-slate-500">
                                The name of the variable where the current item will be stored for each iteration.
                            </p>
                        </div>
                    </div>

                    {/* Footer */}
                    <div className="flex justify-end gap-3 p-4 border-t border-slate-100 bg-slate-50/50">
                        <button
                            onClick={() => onOpenChange(false)}
                            className="px-4 py-2 text-sm font-medium text-slate-600 hover:bg-slate-200 rounded-lg transition-colors"
                        >
                            Cancel
                        </button>
                        <button
                            onClick={handleSave}
                            className="px-4 py-2 text-sm font-medium text-white bg-orange-600 hover:bg-orange-700 rounded-lg shadow-sm transition-colors"
                        >
                            Save Changes
                        </button>
                    </div>

                </Dialog.Content>
            </Dialog.Portal>
        </Dialog.Root>
    );
}
