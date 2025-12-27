import Markdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism';
import type { Message } from '../../types/execution';
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
            <ChevronDown
              size={14}
              className={clsx('transition-transform text-zinc-400', isOpen && 'rotate-180')}
            />
          </Collapsible.Trigger>

          <Collapsible.Content className="mt-2 text-xs font-mono bg-zinc-900 text-zinc-300 p-3 rounded-lg overflow-x-auto">
            <div className="mb-2 text-zinc-500">Input:</div>
            <pre>{message.toolDetails?.input}</pre>
          </Collapsible.Content>
        </Collapsible.Root>
      </div>
    );
  }

  if (message.role === 'trace') {
    return (
      <div className="flex justify-start mb-4 px-4 w-full">
        <Collapsible.Root open={isOpen} onOpenChange={setIsOpen} className="w-full max-w-[85%]">
          <Collapsible.Trigger className="flex items-center gap-2 p-3 bg-indigo-50 dark:bg-indigo-900/20 rounded-lg w-full hover:bg-indigo-100 dark:hover:bg-indigo-900/30 transition-colors border border-indigo-100 dark:border-indigo-800">
            <div className="p-1 bg-indigo-100 text-indigo-600 rounded">
              <Bot size={14} />
            </div>
            <div className="flex-1 text-left flex items-center gap-2">
              <span className="text-sm font-medium text-indigo-900 dark:text-indigo-200">
                Trace: <span className="font-mono text-xs">{message.name}</span>
              </span>
              <span className="text-[10px] px-1.5 py-0.5 bg-indigo-200 text-indigo-800 rounded-full font-bold">
                #{message.traceDetails?.count}
              </span>
            </div>
            <ChevronDown
              size={14}
              className={clsx('transition-transform text-indigo-400', isOpen && 'rotate-180')}
            />
          </Collapsible.Trigger>

          <Collapsible.Content className="mt-2 text-xs font-mono bg-zinc-900 text-zinc-300 p-3 rounded-lg overflow-x-auto border border-zinc-800">
            <div className="mb-2 text-zinc-500 font-semibold">Node Input:</div>
            <pre className="text-indigo-200">{message.traceDetails?.input}</pre>
          </Collapsible.Content>
        </Collapsible.Root>
      </div>
    );
  }

  if (message.role === 'system') {
    return (
      <div className="flex justify-center mb-4 px-4 w-full">
        <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 text-red-700 dark:text-red-300 px-4 py-3 rounded-lg text-sm flex flex-col gap-1 w-full max-w-[85%]">
          <div className="font-bold flex items-center gap-2">
            <span>⚠️ System Alert</span>
          </div>
          <Markdown
            remarkPlugins={[remarkGfm]}
            components={{
              code({ inline: _inline, className, children, ...props }: any) {
                return (
                  <code
                    {...props}
                    className={clsx(
                      className,
                      'bg-red-100 dark:bg-red-900/40 px-1 rounded font-mono text-xs'
                    )}
                  >
                    {children}
                  </code>
                );
              },
            }}
          >
            {message.content}
          </Markdown>
        </div>
      </div>
    );
  }

  return (
    <div className={clsx('flex gap-3 mb-4', isAi ? 'justify-start' : 'justify-end')}>
      {isAi && (
        <div className="w-8 h-8 rounded-full bg-blue-100 dark:bg-blue-900 flex items-center justify-center shrink-0">
          <Bot size={18} className="text-blue-600 dark:text-blue-300" />
        </div>
      )}

      <div className="flex flex-col gap-1 max-w-[85%]">
        {isAi && message.name && (
          <span className="text-xs text-zinc-500 dark:text-zinc-400 ml-1 font-medium">
            {message.name}
          </span>
        )}
        <div
          className={clsx(
            'px-4 py-3 rounded-2xl shadow-sm text-sm overflow-hidden',
            isAi
              ? 'bg-white dark:bg-zinc-800 border border-zinc-200 dark:border-zinc-700 text-zinc-800 dark:text-zinc-200 rounded-tl-none'
              : 'bg-blue-600 text-white rounded-tr-none'
          )}
        >
          <Markdown
            remarkPlugins={[remarkGfm]}
            components={{
              code({ inline, className, children, ...props }: any) {
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
                  <code
                    {...props}
                    className={clsx(className, 'bg-black/10 dark:bg-white/10 px-1 rounded')}
                  >
                    {children}
                  </code>
                );
              },
            }}
          >
            {message.content}
          </Markdown>
        </div>
      </div>

      {!isAi && (
        <div className="w-8 h-8 rounded-full bg-zinc-200 dark:bg-zinc-700 flex items-center justify-center shrink-0">
          <User size={18} className="text-zinc-600 dark:text-zinc-300" />
        </div>
      )}
    </div>
  );
}
