/// <reference types="vite/client" />

interface Window {
  electronAPI: {
    getApiPort: () => Promise<number>
    onPythonLog: (callback: (event: any, value: string) => void) => any
    offPythonLog: (callback: any) => void
  }
}
