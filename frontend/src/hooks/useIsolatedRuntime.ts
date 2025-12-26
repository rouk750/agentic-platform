import { useRef, useCallback, useState, useEffect } from 'react';
import { toast } from 'sonner';

interface IsolatedRunState {
  status: 'idle' | 'running' | 'done' | 'error';
  output: any;
  logs: string[];
}

export function useIsolatedRuntime() {
  const socketRef = useRef<WebSocket | null>(null);
  const [state, setState] = useState<IsolatedRunState>({
    status: 'idle',
    output: null,
    logs: [],
  });

  const runNode = useCallback((nodeId: string, graphJson: any, input: any) => {
    // 1. Reset State
    setState({ status: 'running', output: null, logs: [] });

    // 2. Open Dedicated WebSocket
    const graphId = 'debug-' + Date.now();
    const startSocket = async () => {
      try {
        let port = 8000;
        if ((window as any).electronAPI) {
          port = await (window as any).electronAPI.getApiPort();
        }

        const url = `ws://localhost:${port}/api/ws/run/${graphId}`;
        const socket = new WebSocket(url);
        socketRef.current = socket;

        socket.onopen = () => {
          setState((s) => ({ ...s, logs: [...s.logs, 'Connection established.'] }));

          // 3. Send Payload (Modified to support single node run if backend supports it,
          // or just run the graph with specific input that triggers that node?
          // Actually, running a single node in isolation usually requires a modified graph where that node is the start.
          // For now, let's assume we run the WHOLE graph but with the input mocked for this node.
          // TODO: Backend needs 'entry_point' feature to truly isolate, or we rely on the graph structure.
          // For this MVC, we'll just run the graph with the Playground Input.

          const payload = {
            graph: graphJson, // In future, trim this to just the node + dependencies?
            input: input,
            thread_id: 'debug-session-' + Date.now(),
          };
          socket.send(JSON.stringify(payload));
        };

        socket.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data);
            if (data.type === 'token') {
              // Accumulate tokens if streaming text
              setState((s) => ({
                ...s,
                output: (s.output || '') + data.content,
              }));
            } else if (data.type === 'node_finished' && data.node_id === nodeId) {
              // Capture specific node output
              setState((s) => ({
                ...s,
                output: data.data?.output || s.output, // Prefer structured output if available
              }));
            } else if (data.type === 'error') {
              setState((s) => ({
                ...s,
                status: 'error',
                logs: [...s.logs, `Error: ${data.message}`],
              }));
            } else if (data.type === 'done') {
              setState((s) => ({ ...s, status: 'done', logs: [...s.logs, 'Execution finished.'] }));
              socket.close();
            }
          } catch (e) {
            console.error(e);
          }
        };

        socket.onerror = (e) => {
          setState((s) => ({ ...s, status: 'error', logs: [...s.logs, 'WebSocket Error'] }));
        };
      } catch (e) {
        setState((s) => ({ ...s, status: 'error', logs: [...s.logs, 'Failed to connect'] }));
      }
    };

    startSocket();
  }, []);

  const stop = useCallback(() => {
    if (socketRef.current) {
      socketRef.current.close();
      socketRef.current = null;
      setState((s) => ({ ...s, status: 'idle', logs: [...s.logs, 'Execution stopped by user.'] }));
    }
  }, []);

  // Cleanup
  useEffect(() => {
    return () => {
      if (socketRef.current) socketRef.current.close();
    };
  }, []);

  return { runNode, stop, ...state };
}
