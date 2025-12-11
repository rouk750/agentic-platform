import Markdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism';
import { Message } from '../../store/runStore';
import clsx from 'clsx';
import { Bot, User, ChevronDown, Wrench } from 'lucide-react';
import * as Collapsible from '@radix-ui/react-collapsible';
import { useState } from 'react';

interface ChatMessageProps {
    message: Message;
}

export function ChatMessage({ message }: ChatMessageProps) {
    const isAi = message.role === 'ai';
    const isTool = message.role === 'tool';
    const [isOpen, setIsOpen] = useState(false);

    if (isTool) {
        return (
            <div className="flex justify-start mb-4 px-4 w-full">
                <Collapsible.Root open={isOpen} onOpenChange={setIsOpen} className="w-full max-w-[85%]">
                    <Collapsible.Trigger className="flex items-center gap-2 p-3 bg-zinc-100 dark:bg-zinc-800 rounded-lg w-full hover:bg-zinc-200 dark:hover:bg-zinc-700 transition-colors border border-zinc-200 dark:border-zinc-700">
                        <div className="p-1 bg-orange-100 text-orange-600 rounded">
                            <Wrench size={14} />
                        </div>
                        <span className="text-sm font-medium text-zinc-700 dark:text-zinc-300 flex-1 text-left">
                            Executed: <span className="font-mono text-xs">{message.toolDetails?.name}</span>
                        </span>
                        <ChevronDown size={14} className={clsx("transition-transform text-zinc-400", isOpen && "rotate-180")} />
                    </Collapsible.Trigger>

                    <Collapsible.Content className="mt-2 text-xs font-mono bg-zinc-900 text-zinc-300 p-3 rounded-lg overflow-x-auto">
                        <div className="mb-2 text-zinc-500">Input:</div>
                        <pre>{message.toolDetails?.input}</pre>
                        {/* Output would go here if we updated the message with output */}
                    </Collapsible.Content>
                </Collapsible.Root>
            </div>
        );
    }

    return (
        <div className={clsx("flex gap-3 mb-4", isAi ? "justify-start" : "justify-end")}>
            {isAi && (
                <div className="w-8 h-8 rounded-full bg-blue-100 dark:bg-blue-900 flex items-center justify-center shrink-0">
                    <Bot size={18} className="text-blue-600 dark:text-blue-300" />
                </div>
            )}

            <div className={clsx(
                "max-w-[85%] px-4 py-3 rounded-2xl shadow-sm text-sm overflow-hidden",
                isAi
                    ? "bg-white dark:bg-zinc-800 border border-zinc-200 dark:border-zinc-700 text-zinc-800 dark:text-zinc-200 rounded-tl-none"
                    : "bg-blue-600 text-white rounded-tr-none"
            )}>
                <Markdown
                    remarkPlugins={[remarkGfm]}
                    components={{
                        code({ node, inline, className, children, ...props }: any) {
                            const match = /language-(\w+)/.exec(className || '');
                            return !inline && match ? (
                                <SyntaxHighlighter
                                    {...props}
                                    style={vscDarkPlus}
                                    language={match[1]}
                                    PreTag="div"
                                    className="rounded-md !bg-zinc-900 !m-0"
                                >
                                    {String(children).replace(/\n$/, '')}
                                </SyntaxHighlighter>
                            ) : (
                                <code {...props} className={clsx(className, "bg-black/10 dark:bg-white/10 px-1 rounded")}>
                                    {children}
                                </code>
                            );
                        }
                    }}
                >
                    {message.content}
                </Markdown>
            </div>

            {!isAi && (
                <div className="w-8 h-8 rounded-full bg-zinc-200 dark:bg-zinc-700 flex items-center justify-center shrink-0">
                    <User size={18} className="text-zinc-600 dark:text-zinc-300" />
                </div>
            )}
        </div>
    );
}
