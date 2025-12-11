export interface IElectronAPI {
  getApiPort: () => Promise<number>,
  onPythonLog: (callback: (event: any, value: string) => void) => any,
  offPythonLog: (callback: any) => void
}

declare global {
  interface Window {
    electronAPI: IElectronAPI
  }
}
