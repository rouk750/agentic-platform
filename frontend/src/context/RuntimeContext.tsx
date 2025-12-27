import { createContext, useContext, useRef, useCallback, type ReactNode, useEffect } from 'react';
import { useRunStore } from '../store/runStore';
import { toast } from 'sonner';

interface RuntimeContextType {
  connect: (graphJson: any, input: string) => void;
  stop: () => void;
  resume: () => void;
}

const RuntimeContext = createContext<RuntimeContextType | null>(null);

export function useRuntime() {
  const context = useContext(RuntimeContext);
  if (!context) {
    throw new Error('useRuntime must be used within a RuntimeProvider');
  }
  return context;
}

interface RuntimeProviderProps {
  children: ReactNode;
}

export function RuntimeProvider({ children }: RuntimeProviderProps) {
  const socketRef = useRef<WebSocket | null>(null);
  const {
    setStatus,
    setRunId,
    appendToken,
    addActiveNode,
    removeActiveNode,
    setCurrentTool,
    addLog,
    addMessage,
    clearSession,
    updateIteratorProgress,
    incrementNodeExecution,
    addToolExecution,
    addSnapshot,
    setPaused,
    addTokenUsage,
    setGraphDefinition,
    completeNodeMessage,
    storeNodeInput,
  } = useRunStore();

  const connect = useCallback(
    (graphJson: any, input: string) => {
      // 1. Reset state
      clearSession();
      setStatus('connecting');
      addMessage({ role: 'user', content: input });

      if (graphJson && Array.isArray(graphJson.nodes)) {
        const labels: Record<string, string> = {};
        graphJson.nodes.forEach((node: any) => {
          if (node.id) {
            labels[node.id] = node.data?.label || node.id;
          }
        });
        useRunStore.getState().setNodeLabels(labels);
        setGraphDefinition(graphJson);
      }

      const graphId = 'playground-' + Date.now();
      setRunId(graphId);

      const startSocket = async () => {
        try {
          let port = 8000;
          if ((window as any).electronAPI) {
            port = await (window as any).electronAPI.getApiPort();
          } else {
            console.warn('Electron API not found, defaulting to 8000');
          }

          const url = `ws://localhost:${port}/api/ws/run/${graphId}`;

          const socket = new WebSocket(url);
          socketRef.current = socket;

          socket.onopen = () => {
            setStatus('running');
            addLog({ event: 'Connection Established', level: 'info', details: { url } });

            const payload = {
              graph: graphJson,
              input: input,
              thread_id: 'session-' + Date.now(),
            };
            socket.send(JSON.stringify(payload));
          };

          socket.onmessage = (event) => {
            try {
              const data = JSON.parse(event.data);

              switch (data.type) {
                case 'token':
                  appendToken(data.content, data.node_id);
                  break;
                case 'token_usage':
                  addTokenUsage(data.node_id, data.usage);
                  break;
                case 'node_active': {
                  addActiveNode(data.node_id);
                  incrementNodeExecution(data.node_id);

                  // [FIX] Store input for observability
                  if (data.input) {
                    storeNodeInput(data.node_id, data.input);
                  }

                  const currentCount =
                    useRunStore.getState().nodeExecutionCounts[data.node_id] || 1;
                  const label = useRunStore.getState().nodeLabels[data.node_id] || data.node_id;

                  addMessage({
                    role: 'trace',
                    content: '',
                    name: label,
                    nodeId: data.node_id,
                    traceDetails: {
                      nodeId: data.node_id,
                      input: JSON.stringify(data.input, null, 2),
                      count: currentCount,
                    },
                  });

                  addLog({
                    event: 'Node Active',
                    level: 'info',
                    details: { nodeId: data.node_id },
                  });
                  break;
                }
                case 'node_finished': {
                  if (data.data && data.data._iterator_metadata) {
                    const { node_id, current, total } = data.data._iterator_metadata;
                    updateIteratorProgress(node_id, current, total);
                  }

                  if (data.snapshot) {
                    // [FIX] Pass optional output if available
                    const output = data.data?.output;
                    addSnapshot(data.node_id, data.snapshot, output);
                  }

                  // Mark the LAST message from this node as complete,
                  // so subsequent runs (e.g. within a loop) start a new message block.
                  completeNodeMessage(data.node_id);

                  const hasToolCalls = data.data && data.data.has_tool_calls;

                  if (!hasToolCalls) {
                    setTimeout(() => {
                      removeActiveNode(data.node_id);
                    }, 1500);
                  } else {
                    addLog({
                      event: 'Agent Waiting for Tool',
                      level: 'info',
                      details: { nodeId: data.node_id },
                    });
                  }
                  break;
                }
                case 'done':
                  setStatus('done');
                  addLog({ event: 'Execution Finished', level: 'info', details: {} });
                  socket.close();
                  break;
                case 'error':
                  setStatus('error');
                  addLog({
                    event: 'Runtime Error',
                    level: 'error',
                    details: { message: data.message },
                  });
                  console.error('Agent Runtime Error:', data.message);

                  addMessage({
                    role: 'system',
                    content: data.message || 'An unknown error occurred.',
                  });

                  toast.error(data.message || 'An error occurred during execution');
                  break;
                case 'tool_start':
                  setCurrentTool(data.name);
                  addMessage({
                    role: 'tool',
                    content: '',
                    toolDetails: {
                      name: data.name,
                      input: JSON.stringify(data.input, null, 2),
                    },
                  });
                  break;
                case 'tool_end':
                  setTimeout(() => {
                    setCurrentTool(null);
                  }, 500);
                  addLog({
                    event: 'Tool Finished',
                    level: 'info',
                    details: { output: data.output },
                  });

                  if (data.node_id) {
                    addToolExecution(data.node_id, data.name);
                  }
                  break;
                case 'interrupt': {
                  setPaused(data.node_id);

                  const pausedCount = useRunStore.getState().nodeExecutionCounts[data.node_id] || 0;
                  const pausedLabel =
                    useRunStore.getState().nodeLabels[data.node_id] || data.node_id;

                  addMessage({
                    role: 'trace',
                    content: 'Waiting for approval...',
                    name: pausedLabel,
                    nodeId: data.node_id,
                    traceDetails: {
                      nodeId: data.node_id,
                      input: 'Paused execution.',
                      count: pausedCount,
                    },
                  });

                  addLog({
                    event: 'Execution Paused',
                    level: 'warn',
                    details: { nodeId: data.node_id },
                  });
                  toast.info(`Workflow paused at ${pausedLabel} for approval.`);
                  break;
                }
              }
            } catch (err) {
              console.error('Error parsing WS message', err);
            }
          };

          socket.onerror = (error) => {
            console.error('WebSocket Error', error);
            setStatus('error');
            toast.error('Connection error');
          };

          socket.onclose = () => {
            if (useRunStore.getState().status === 'running') {
              setStatus('done');
            }
          };
        } catch (e) {
          console.error('Failed to create WebSocket', e);
          setStatus('error');
          toast.error('Failed to connect to agent runtime');
        }
      };

      startSocket();
    },
    [
      setStatus,
      appendToken,
      addActiveNode,
      removeActiveNode,
      addLog,
      addMessage,
      clearSession,
      setCurrentTool,
      updateIteratorProgress,
      addToolExecution,
      addSnapshot,
      setRunId,
      setPaused,
      addTokenUsage,
      setGraphDefinition,
      // Added missing dependencies to fix linter warning and manual memoization preservation error
      completeNodeMessage,
      incrementNodeExecution,
      storeNodeInput,
    ]
  );

  const stop = useCallback(() => {
    if (socketRef.current) {
      socketRef.current.close();
      socketRef.current = null;
      setStatus('done');
      addLog({ event: 'Stopped by User', level: 'warn', details: {} });
    }
  }, [setStatus, addLog]);

  const resume = useCallback(() => {
    if (socketRef.current && socketRef.current.readyState === WebSocket.OPEN) {
      socketRef.current.send(JSON.stringify({ command: 'resume' }));
      setPaused(null);
      setStatus('running');
      toast.success('Resuming execution...');
    } else {
      toast.error('Cannot resume: Connection lost');
    }
  }, [setPaused, setStatus]);

  // Cleanup only on Application Unmount (or provider unmount)
  useEffect(() => {
    return () => {
      if (socketRef.current) {
        console.log('RuntimeProvider unmounting, closing socket.');
        socketRef.current.close();
      }
    };
  }, []);

  return (
    <RuntimeContext.Provider value={{ connect, stop, resume }}>{children}</RuntimeContext.Provider>
  );
}
