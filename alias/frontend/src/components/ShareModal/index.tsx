import { conversationApi } from "@/services/api/conversation";
import { Conversation } from "@/types/api";
import { Button, Input, message, Modal, Switch } from "@agentscope-ai/design";
import copy from "copy-to-clipboard";
import React, { useState } from "react";
import { useI18n } from "@/context/LanguageContext";

import styles from "./index.module.scss";

interface ShareModalProps {
  isOpen: boolean;
  onClose: () => void;
  shareUrl: string;
  shared: boolean;
  conversationId: string;
  setCurrentConversation: (con: Conversation) => void;
}

export const ShareModal: React.FC<ShareModalProps> = ({
  isOpen,
  onClose,
  shareUrl,
  shared,
  conversationId,
  setCurrentConversation,
}) => {
  const { t } = useI18n();
  const [copied, setCopied] = useState(false);
  const [isShared, setIsShared] = useState(shared);

  const handleCopy = () => {
    // navigator.clipboard.writeText(shareUrl);
    copy(shareUrl);
    setCopied(true);

    message.success(t("share.copySuccess"));
    setTimeout(() => setCopied(false), 2000);
    onClose();
  };
  const onChangeShare = (share: boolean) => {
    if (!!conversationId) {
      conversationApi
        .shareConversations(conversationId, share)
        .then((res: any) => {
          if (res?.payload) {
            setCurrentConversation(res.payload);
            setIsShared(share);
          }
        })
        .catch((error) => {
          message.error(t("share.networkError"));
        });
    } else setIsShared(share);
  };

  return (
    <Modal
      title={t("share.title")}
      open={isOpen}
      onCancel={onClose}
      footer={null}
      width={400}
    >
      <div className={styles.container}>
        <div>{t("share.confirm")}</div>
        <Switch
          className={styles.share}
          checked={isShared}
          onChange={onChangeShare}
          label={isShared ? t("share.on") : t("share.off")}
        />
        <span></span>
        <div className={styles.urlContainer}>
          <Input
            disabled={!isShared}
            value={shareUrl}
            readOnly
            className={styles.urlInput}
          />
          <Button type="primary" disabled={!isShared} onClick={handleCopy}>
            {copied ? t("share.linkCopied") : t("share.copyLink")}
          </Button>
        </div>
        <p className={styles.description}>
          {t("share.description")}
        </p>
      </div>
    </Modal>
  );
};
