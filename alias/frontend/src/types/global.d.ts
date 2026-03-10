export {};

declare global {
  interface Window {
    __ALIAS_USER__?: {
      username?: string;
      userName?: string;
    };
  }
}
