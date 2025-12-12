import { useRef, useCallback, useEffect } from 'react';
import { useRunStore } from '../store/runStore';
import { toast } from 'sonner';

// I need to use the relative path so Vite handles it, OR find the port.
// In this template, normally there is a proxy.
// Let's try changing to relative URL for WS.


export function useAgentRuntime() {
  const socketRef = useRef<WebSocket | null>(null);
  const { 
    setStatus, 
    appendToken, 
    setActiveNode, 
    setCurrentTool,
    addLog, 
    addMessage,
    clearSession,
    updateIteratorProgress,
    incrementNodeExecution
  } = useRunStore();

  const connect = useCallback((graphJson: any, input: string) => {
    // 1. Reset state
    clearSession();
    setStatus('connecting');
    addMessage({ role: 'user', content: input });
    
    // Extract Node Labels from Graph
    if (graphJson && Array.isArray(graphJson.nodes)) {
        const labels: Record<string, string> = {};
        graphJson.nodes.forEach((node: any) => {
            if (node.id) {
                labels[node.id] = node.data?.label || node.id;
            }
        });
        useRunStore.getState().setNodeLabels(labels);
    }
    
    // 2. Open WebSocket
    // Generate a temporary graph ID or use a fixed one for playground
    const graphId = 'playground-' + Date.now();

    const startSocket = async () => {
        try {
            let port = 8000;
            if (window.electronAPI) {
                port = await window.electronAPI.getApiPort();
            } else {
                console.warn("Electron API not found, defaulting to 8000");
            }
            
            const url = `ws://localhost:${port}/api/ws/run/${graphId}`;
            
            const socket = new WebSocket(url);
            socketRef.current = socket;
            
            socket.onopen = () => {
                setStatus('running');
                addLog({ event: 'Connection Established', level: 'info', details: { url } });
                
                // 3. Send Initialization Data
                const payload = {
                    graph: graphJson,
                    input: input,
                    thread_id: 'session-' + Date.now()
                };
                socket.send(JSON.stringify(payload));
            };
            
            socket.onmessage = (event) => {
                try {
                    const data = JSON.parse(event.data);
                    
                    switch (data.type) {
                        case 'token':
                            appendToken(data.content);
                            break;
                        case 'node_active':
                            setActiveNode(data.node_id);
                            incrementNodeExecution(data.node_id);
                            
                            // Add Trace Message for visibility
                            const currentCount = useRunStore.getState().nodeExecutionCounts[data.node_id] || 1;
                            const label = useRunStore.getState().nodeLabels[data.node_id] || data.node_id;
                            
                            addMessage({
                                role: 'trace',
                                content: '',
                                name: label,
                                nodeId: data.node_id,
                                traceDetails: {
                                    nodeId: data.node_id,
                                    input: JSON.stringify(data.input, null, 2),
                                    count: currentCount
                                }
                            });

                            addLog({ event: 'Node Active', level: 'info', details: { nodeId: data.node_id } });
                            break;
                        case 'node_finished':
                            // Handle iterator progress
                            if (data.data && data.data._iterator_metadata) {
                                const { node_id, current, total } = data.data._iterator_metadata;
                                updateIteratorProgress(node_id, current, total);
                            }
                            
                            // Clear active node to prevent it sticking
                            setActiveNode(null);
                            break;
                        case 'done':
                            setStatus('done');
                            addLog({ event: 'Execution Finished', level: 'info', details: {} });
                            socket.close();
                            break;
                        case 'error':
                            setStatus('error');
                            addLog({ event: 'Runtime Error', level: 'error', details: { message: data.message } });
                            toast.error(data.message || 'An error occurred');
                            break;
                        case 'tool_start':
                            setCurrentTool(data.name);
                            addMessage({
                                role: 'tool',
                                content: '', 
                                toolDetails: {
                                    name: data.name,
                                    input: JSON.stringify(data.input, null, 2),
                                }
                            });
                            break;
                        case 'tool_end':
                            setCurrentTool(null);
                            addLog({ event: 'Tool Finished', level: 'info', details: { output: data.output } });
                            break;
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
        
  }, [setStatus, appendToken, setActiveNode, addLog, addMessage, clearSession, setCurrentTool, updateIteratorProgress]);

  const stop = useCallback(() => {
    if (socketRef.current) {
        socketRef.current.close();
        socketRef.current = null;
        setStatus('done'); // stopped by user
        addLog({ event: 'Stopped by User', level: 'warn', details: {} });
    }
  }, [setStatus, addLog]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
        if (socketRef.current) {
            socketRef.current.close();
        }
    };
  }, []);

  return { connect, stop };
}
