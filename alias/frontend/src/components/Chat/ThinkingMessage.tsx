import React from "react";
import styles from "./Message.module.scss";
import AssistantAvatar from "@/assets/icons/avatar/assistantHeader.png";
import { Flex } from "antd";
import { useI18n } from "@/context/LanguageContext";

export const ThinkingMessage: React.FC = () => {
  const { t } = useI18n();
  return (
    <Flex gap="middle" align="center">
      <div className={styles.avatar}>
        <img src={AssistantAvatar} alt={t("chat.aliasAgent")} />
      </div>
      <div className={styles.thinkingText}>
        {t("chat.thinking")}
      </div>
      <div className={styles.thinkingDots}>
        <span></span>
        <span></span>
        <span></span>
      </div>
    </Flex>
  );
};
