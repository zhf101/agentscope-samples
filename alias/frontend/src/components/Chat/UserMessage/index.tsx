import { useTheme } from "@/context/ThemeContext";
import { useI18n } from "@/context/LanguageContext";
import { UserMessage as UserMessageType } from "@/types/message";
import { Modal } from "@agentscope-ai/design";
import { SparkProcessJudgmentLine } from "@agentscope-ai/icons";
import { Flex } from "antd";
import React, { useState } from "react";
import { Prism as SyntaxHighlighter } from "react-syntax-highlighter";
import { oneDark, prism } from "react-syntax-highlighter/dist/esm/styles/prism";
import { FileItems } from "../FileItems";
import styles from "./index.module.scss";

interface UserMessageProps {
  message: UserMessageType;
}

export const UserMessage: React.FC<UserMessageProps> = ({ message }) => {
  const { files, roadmap } = message;
  const { theme } = useTheme();
  const { t } = useI18n();
  const [diffOpen, setDiffOpen] = useState(false);
  const fontSize = { fontSize: 20 };
  const viewRoadmapDiff = () => {
    setDiffOpen(true);
  };
  const onCancel = () => {
    setDiffOpen(false);
  };
  const customStyle = {
    borderTopRightRadius: 0,
    borderTopLeftRadius: 0,
    overflow: "auto",
    padding: 0,
    backgroundColor: "var(--sps-color-bg-base)",
  };
  const CodeView = ({ value }: { value: string }) => {
    return (
      <SyntaxHighlighter
        language="JSON"
        showLineNumbers={true}
        wrapLines={true}
        style={theme === "dark" ? oneDark : prism}
        customStyle={
          theme === "dark"
            ? customStyle
            : { ...customStyle, background: "transparent" }
        }
      >
        {value}
      </SyntaxHighlighter>
    );
  };
  return (
    <Flex gap="small" vertical className={styles.userMessageFlex}>
      <Flex justify="flex-end" className={styles.userMessageText}>
        <div className={styles.userContentFlex}>{message.content}</div>
      </Flex>
      {files && files?.length > 0 && (
        <Flex wrap gap="small" justify="flex-end">
          <FileItems files={files} />
        </Flex>
      )}
      {roadmap && (
        <Flex justify="flex-end">
          <div className={styles.roadmapCard} onClick={viewRoadmapDiff}>
              <SparkProcessJudgmentLine
                className={styles.roadmapLeft}
                style={fontSize}
              />
              <div className={styles.roadmapRight}>
              <div className={styles.title}>{t("chat.roadmap")}</div>
              <div className={styles.description}>
                {t("chat.tasksCount", {
                  count: roadmap.current?.subtasks?.length || 0,
                })}
              </div>
              </div>
            </div>
          </Flex>
      )}
      {diffOpen && roadmap && (
        <Modal
          width={960}
          open={diffOpen}
          showDivider={false}
          title={t("chat.roadmapDiff")}
          footer={null}
          onCancel={onCancel}
          styles={{
            body: { padding: 0 },
          }}
        >
          <Flex className={styles.diffRoadmap}>
            <div className={`${styles.left} ${styles.diffRoadmapJson}`}>
              <div>{t("chat.previousJson")}</div>
              {roadmap.previous && (
                <CodeView value={JSON.stringify(roadmap.previous, null, 2)} />
              )}
            </div>
            <div className={styles.diffRoadmapJson}>
              <div>{t("chat.currentJson")}</div>
              {roadmap.current && (
                <CodeView value={JSON.stringify(roadmap.current, null, 2)} />
              )}
            </div>
          </Flex>
        </Modal>
      )}
    </Flex>
  );
};
