/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_APP_TITLE: string;
  readonly VITE_SIMPLE_USERNAME?: string;
  readonly VITE_SIMPLE_AUTH_HEADER?: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
  readonly hot: {
    accept(): void;
    dispose(cb: (data: any) => void): void;
    data: any;
  };
}
