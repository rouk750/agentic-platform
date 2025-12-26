/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_USE_JSON_API: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}

interface Window {
  electronAPI: {
    getApiPort: () => Promise<number>;
    onPythonLog: (callback: (event: any, value: string) => void) => any;
    offPythonLog: (callback: any) => void;
  };
}
