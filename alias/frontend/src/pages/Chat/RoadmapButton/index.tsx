import React, { memo, useRef, useLayoutEffect } from "react";
import { Button } from "@agentscope-ai/design";
import { Flex } from "antd";
import { SparkEditLine } from "@agentscope-ai/icons";
import { useWorkspace } from "@/context/WorkspaceContext";
import { isAtBottom } from "@/utils/sharedRefs";
import { useI18n } from "@/context/LanguageContext";

interface RoadmapButtonProps {
  handleSendMessage: (message: string) => void;
  setShow: (show: boolean) => void;
  startTimer: () => void;
  setShowRoadmapEditBtn: (edit: boolean) => void;
}
const RoadmapButton: React.FC<RoadmapButtonProps> = ({
  handleSendMessage,
  setShow,
  startTimer,
  setShowRoadmapEditBtn,
}) => {
  const { t } = useI18n();
  const { setActiveKey } = useWorkspace();
  const shouldScrollRef = useRef(isAtBottom.current);
  useLayoutEffect(() => {
    if (!shouldScrollRef.current) return;
    startTimer();
  }, [startTimer]);
  const acceptedRoadmap = () => {
    const acceptedMessage = t("roadmap.acceptedMessage");
    handleSendMessage(acceptedMessage);
    setShow(false);
  };
  return (
    <Flex gap={16} align="center" style={{ paddingBottom: 80 }}>
      <Button
        onClick={() => {
          setActiveKey("roadmap");
          setShow(false);
          setShowRoadmapEditBtn(true);
        }}
      >
        <SparkEditLine /> {t("roadmap.editRoadmap")}
      </Button>
      <Button onClick={acceptedRoadmap}>
        <SparkEditLine /> {t("roadmap.acceptRoadmap")}
      </Button>
    </Flex>
  );
};

export default memo(RoadmapButton);
