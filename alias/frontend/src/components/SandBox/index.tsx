import React, { useEffect, memo } from "react";
import { Result } from "@agentscope-ai/design";
import styles from "./index.module.scss";
import { useI18n } from "@/context/LanguageContext";

interface SandBoxProps {
  sandboxUrl: string;
}

const SandBox: React.FC<SandBoxProps> = ({ sandboxUrl }) => {
  const { t } = useI18n();
  return (
    <div className={styles.sandbox}>
      {/* <div className={styles.title}>{sandboxUrl}</div> */}
      {sandboxUrl && (
        <iframe
          src={sandboxUrl}
          className={styles.sandboxIframe}
          title="Alias Sandbox"
          allowFullScreen
          frameBorder="0"
        />
      )}
      {!sandboxUrl && (
        <Result
          type="error"
          title={t("sandbox.errorTitle")}
          description={t("sandbox.errorDesc")}
        />
      )}
    </div>
  );
};

export default memo(SandBox);
