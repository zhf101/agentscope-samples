export const SIMPLE_AUTH_HEADER =
  import.meta.env.VITE_SIMPLE_AUTH_HEADER || "X-User-Name";

const DEFAULT_SIMPLE_USERNAME =
  import.meta.env.VITE_SIMPLE_USERNAME || "gdpSysUser";

type SimpleUser = {
  username?: string;
  userName?: string;
};

export const getSimpleUsername = (): string => {
  const globalUser = (window as any).__ALIAS_USER__ as SimpleUser | undefined;
  return (
    globalUser?.username ||
    globalUser?.userName ||
    localStorage.getItem("simple_username") ||
    DEFAULT_SIMPLE_USERNAME ||
    ""
  );
};

export const attachSimpleAuthHeader = (
  headers: Record<string, any>,
): Record<string, any> => {
  const simpleUsername = getSimpleUsername();
  if (simpleUsername) {
    headers[SIMPLE_AUTH_HEADER] = simpleUsername;
  }
  return headers;
};
