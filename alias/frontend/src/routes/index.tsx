import Chat from "@/pages/Chat";
import Login from "@/pages/Login";
import SharePage from "@/pages/SharePage";
import { ErrorBoundary } from "react-error-boundary";
import { useI18n } from "@/context/LanguageContext";
import { createBrowserRouter } from "react-router-dom";

const ErrorFallback = ({
  error,
  resetErrorBoundary,
}: {
  error: Error;
  resetErrorBoundary: () => void;
}) => {
  const { t } = useI18n();
  return (
    <div style={{ padding: "20px", textAlign: "center" }}>
      <h2>{t("app.errorFallback.title")}</h2>
      <p style={{ color: "red" }}>{error.message}</p>
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
        {t("app.errorFallback.reload")}
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
