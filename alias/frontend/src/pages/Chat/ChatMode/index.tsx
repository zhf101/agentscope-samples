import React, { memo } from "react";
import { Button } from "@agentscope-ai/design";
import { Flex } from "antd";
import classNames from "classnames";
import {
  SparkBrowseLine,
  SparkSingleStarLine,
} from "@agentscope-ai/icons";
import { ChatModeList, ChatModeType } from "@/utils/constant";
import { useI18n } from "@/context/LanguageContext";
import styles from "./index.module.scss";

interface ChatModeProps {
  chatModeValue: ChatModeType;
  setChatModeValue: (type: ChatModeType) => void;
}

const ChatMode: React.FC<ChatModeProps> = ({
  chatModeValue,
  setChatModeValue,
}) => {
  const { t } = useI18n();
  const getIcon = (value: string) => {
    switch (value) {
      case ChatModeType.GENERAL:
        return <SparkSingleStarLine />;
      case ChatModeType.BROWSER:
        return <SparkBrowseLine />;
      default:
        return null; // or returning a default icon.
    }
  };
  return (
    <Flex
      gap="small"
      align="center"
      justify="center"
      className={styles.chatMode}
    >
      {ChatModeList.map((item) => {
        return (
          <Button
            className={classNames({
              [styles.chatTag]: item.value === chatModeValue,
            })}
            key={item.value}
            onClick={() => {
              setChatModeValue(item.value);
            }}
          >
            {getIcon(item.value)}
            {t(item.labelKey)}
          </Button>
        );
      })}
    </Flex>
  );
};

export default memo(ChatMode);
