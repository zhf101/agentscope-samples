import Chat from "@/pages/Chat";
import Login from "@/pages/Login";
import SharePage from "@/pages/SharePage";
import { ErrorBoundary } from "react-error-boundary";
import type { FallbackProps } from "react-error-boundary";
import { createBrowserRouter } from "react-router-dom";

const ErrorFallback = ({ error, resetErrorBoundary }: FallbackProps) => {
  const errorMessage =
    error instanceof Error ? error.message : "Unknown runtime error";
  return (
    <div style={{ padding: "20px", textAlign: "center" }}>
      <h2>Something went wrong!</h2>
      <p style={{ color: "red" }}>{errorMessage}</p>
      <button
        onClick={resetErrorBoundary}
        style={{
          padding: "10px 20px",
          backgroundColor: "#1890ff",
          color: "white",
          border: "none",
          borderRadius: "4px",
          cursor: "pointer",
        }}
      >
        Reload the page
      </button>
    </div>
  );
};

export const router = createBrowserRouter([
  {
    path: "/",
    element: (
      <ErrorBoundary FallbackComponent={ErrorFallback}>
        <Chat />
      </ErrorBoundary>
    ),
  },
  {
    path: "/share/:userId/:sessionId",
    element: (
      <ErrorBoundary FallbackComponent={ErrorFallback}>
        <SharePage />
      </ErrorBoundary>
    ),
  },
  {
    path: "/login",
    element: (
      <ErrorBoundary FallbackComponent={ErrorFallback}>
        <Login />
      </ErrorBoundary>
    ),
  },
]);
