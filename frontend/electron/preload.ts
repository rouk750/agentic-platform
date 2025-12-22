import { ipcRenderer, contextBridge } from 'electron';

contextBridge.exposeInMainWorld('electronAPI', {
  getApiPort: () => ipcRenderer.invoke('get-api-port'),
  onPythonLog: (callback: (event: any, value: string) => void) => {
    const subscription = (_event: any, value: string) => callback(_event, value);
    ipcRenderer.on('python-log', subscription);
    return subscription;
  },
  offPythonLog: (callback: any) => ipcRenderer.removeListener('python-log', callback),
});
