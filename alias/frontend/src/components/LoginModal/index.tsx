import { Button, Modal } from "@agentscope-ai/design";
import { memo, useState } from "react";
import { useNavigate } from "react-router-dom";
import styles from "./index.module.scss";
import { getSimpleUsername } from "@/utils/simpleAuth";
import { useI18n } from "@/context/LanguageContext";

const LoginModal = () => {
  const [isModalOpen, setIsModalOpen] = useState<boolean>(true);
  const navigate = useNavigate();
  const { t } = useI18n();
  const showModal = () => {
    setIsModalOpen(true);
  };

  const handleOk = () => {
    setIsModalOpen(false);
  };

  const handleCancel = () => {
    setIsModalOpen(false);
  };
  if (
    localStorage.getItem("access_token") === null &&
    localStorage.getItem("refresh_token") === null &&
    !getSimpleUsername()
  )
    return (
      <Modal
        // title="Basic Modal"
        open={isModalOpen}
        onOk={handleOk}
        onCancel={handleCancel}
        footer={null}
        centered={true}
        width={384}
        closable={false}
      >
        <div className={styles.modalWrap}>
          <h1>{t("loginModal.title")}</h1>
          <p className={styles.tips}>
            {t("loginModal.tips")}
          </p>
          <Button
            type="primary"
            className={styles.logBtn}
            onClick={() => {
              navigate("/login?mode=login");
            }}
          >
            {t("login.signIn")}
          </Button>
          <Button
            className={styles.registerBtn}
            onClick={() => {
              navigate("/login?mode=register");
            }}
          >
            {t("login.signUp")}
          </Button>
        </div>
      </Modal>
    );
  return null;
};
export default memo(LoginModal);
