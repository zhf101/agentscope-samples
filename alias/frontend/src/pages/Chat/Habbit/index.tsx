import { HabbitApi } from "@/services/api/habbit";
import {
  AlertDialog,
  Button,
  Dropdown,
  IconButton,
  Input,
  message,
  Modal,
  Tooltip,
} from "@agentscope-ai/design";
import {
  SparkCopyLine,
  SparkDeleteLine,
  SparkDownArrowLine,
  SparkEditLine,
  SparkMoreLine,
  SparkPlusLine,
  SparkSearchLine,
  SparkUserCheckedLine,
} from "@agentscope-ai/icons";
import { Flex, List } from "antd";
import copy from "copy-to-clipboard";
import React, { memo, useEffect, useMemo, useState } from "react";
import styles from "./index.module.scss";
import { useI18n } from "@/context/LanguageContext";

interface MetadataProps {
  session_id: string;
  is_confirmed: number;
}
interface HabbitDataProps {
  content: string;
  pid: string;
  uid: string;
  metadata: MetadataProps;
}

interface HabbitModalProps {
  open: boolean;
  setOpen: (open: boolean) => void;
  uid: string;
}
const { TextArea } = Input;

const Header: React.FC<{
  searchKeyword: string;
  setSearchKeyword: (value: string) => void;
  copyHandle: () => void;
  downHandle: () => void;
  addHabbit: () => void;
}> = ({
  searchKeyword,
  setSearchKeyword,
  copyHandle,
  downHandle,
  addHabbit,
}) => {
  const { t } = useI18n();
  const fontSize = { fontSize: "20px" };

  return (
    <Flex gap="large" justify="space-between" style={{ padding: "20px 0" }}>
      <Flex style={{ width: "200px" }}>
        <Input
          placeholder={t("habbit.searchKnowledge")}
          prefix={<SparkSearchLine style={fontSize} />}
          value={searchKeyword}
          onChange={(e) => setSearchKeyword(e.target.value)}
        />
      </Flex>
      <Flex gap="small">
        <Button type="text" onClick={copyHandle}>
          <SparkCopyLine style={fontSize} />
        </Button>
        <Dropdown
          menu={{
            items: [
              {
                key: "1",
                label: t("common.download"),
                icon: <SparkDownArrowLine style={{ fontSize: 20 }} />,
                onClick: downHandle,
              },
              {
                key: "2",
                label: t("common.delete"),
                danger: true,
                icon: <SparkDeleteLine style={{ fontSize: 20 }} />,
                onClick: () => {
                  AlertDialog.warning({
                    title: t("habbit.deleteAllConfirmTitle"),
                    children: t("common.deleteConfirmDesc"),
                    centered: true,
                    okText: t("common.confirmDelete"),
                    onOk: () => {},
                  });
                },
              },
            ],
          }}
        >
          <Button type="text">
            <SparkMoreLine style={fontSize} />
          </Button>
        </Dropdown>
        <Button type="primary" onClick={addHabbit}>
          <SparkPlusLine style={fontSize} /> {t("habbit.addHabit")}
        </Button>
      </Flex>
    </Flex>
  );
};

const HabbitModal: React.FC<HabbitModalProps> = (props) => {
  const { t } = useI18n();
  const { open, setOpen, uid } = props;
  const [editOpen, setEditOpen] = useState(false);
  const [habbitContent, setHabbitContent] = useState("");
  const [contentBefore, setContentBefore] = useState("");
  const [pid, setPid] = useState("");
  const [loading, setLoading] = useState(false);
  const [dataList, setDataList] = useState<HabbitDataProps[]>([]);
  const [searchKeyword, setSearchKeyword] = useState("");

  const getProfilingData = () => {
    HabbitApi.getUserProfiling(uid)
      .then((res: { data: HabbitDataProps[] }) => {
        const data = res?.data;
        if (data && Array.isArray(data)) setDataList(data);
      })
      .catch((e) => {
        message.error(t("common.networkError"));
      });
  };

  useEffect(() => {
    if (open) getProfilingData();
  }, [open]);

  // Use useMemo to implement filtering logic
  const filteredDataList = useMemo(() => {
    if (!searchKeyword) return dataList;

    return dataList.filter((item) =>
      item.content.toLowerCase().includes(searchKeyword.toLowerCase()),
    );
  }, [dataList, searchKeyword]);

  const addHabbit = () => {
    setEditOpen(true);
    setHabbitContent("");
    setPid("");
  };

  const editHabbit = (contents: string) => {
    setEditOpen(true);
    setHabbitContent(contents);
    setContentBefore(contents);
  };

  const copyHandle = () => {
    if (dataList.length > 0) {
      const contents = JSON.stringify(dataList, null, 2);
      if (contents) {
        copy(contents);
        message.success(t("common.copiedSuccess"));
      }
    }
  };

  const downHandle = () => {
    if (dataList.length > 0) {
      try {
        const contents = JSON.stringify(dataList, null, 2);
        const blob = new Blob([contents], { type: "application/json" });
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = "habbits.json";
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
      } catch (error) {
        message.error(t("habbit.downloadFailed"));
      }
    }
  };

  const onClose = () => {
    setOpen(false);
    setSearchKeyword("");
  };
  const getTitle = () => {
    if (pid) return t("habbit.editHabit");
    return t("habbit.addHabit");
  };

  const onCloseEdit = () => {
    setEditOpen(false);
  };
  const deleteProfiling = async (uid: string, pid: string) => {
    try {
      const result = await HabbitApi.deleteProfiling(uid, pid);
      if (result) {
        getProfilingData();
        message.success(t("habbit.deleteSuccess"));
      }
    } catch (error) {
      message.error(t("habbit.deleteFailed"));
    }
  };
  const onSure = async () => {
    if (!habbitContent) {
      message.info(t("habbit.enterHabit"));
      return;
    }
    try {
      setLoading(true);
      if (pid) {
        // edit habbit
        if (contentBefore.trim() === habbitContent.trim()) {
          onCloseEdit();
          confirmProfiling(uid, pid);
          return;
        }
        const result = await HabbitApi.updateProfiling(
          uid,
          pid,
          contentBefore,
          habbitContent,
        );
        if (result) {
          getProfilingData();
          message.success(t("habbit.updateSuccess"));
        }
      } else {
        // add habbit
        const result = await HabbitApi.addProfiling(uid, habbitContent);
        if (result) {
          getProfilingData();
          message.success(t("habbit.addSuccess"));
        }
      }
    } catch (error) {
      message.error(t("common.networkError"));
    } finally {
      setLoading(false);
      onCloseEdit();
    }
  };
  const confirmProfiling = (uid: string, pid: string) => {
    try {
      HabbitApi.confirmProfiling(uid, pid).then((res) => {
        if (res) getProfilingData();
      });
    } catch (error) {
      console.error("Error confirming profiling:", error);
      message.error(t("habbit.confirmFailed"));
    }
  };
  return (
    <>
      <Modal
        title={t("habbit.savedTitle")}
        open={open}
        width={800}
        footer={false}
        onCancel={onClose}
        maskClosable={false}
      >
        <div style={{ height: "50vh", overflow: "auto" }}>
          <div>
            {t("habbit.description")}
          </div>
          {/* Use extracted Header component */}
          <Header
            searchKeyword={searchKeyword}
            setSearchKeyword={setSearchKeyword}
            copyHandle={copyHandle}
            downHandle={downHandle}
            addHabbit={addHabbit}
          />
          <List
            dataSource={filteredDataList}
            renderItem={(item) => (
              <List.Item className={styles.listItem}>
                <div className={styles.textEllipsis}>{item.content}</div>
                <div className={styles.icon}>
                  <Flex align="center" gap="small">
                    <Dropdown
                      menu={{
                        items: [
                          {
                            key: "1",
                            label: t("common.edit"),
                            icon: <SparkEditLine style={{ fontSize: 20 }} />,
                            onClick: () => {
                              editHabbit(item.content);
                              setPid(item.pid);
                            },
                          },
                          {
                            key: "2",
                            label: t("common.delete"),
                            danger: true,
                            icon: <SparkDeleteLine style={{ fontSize: 20 }} />,
                            onClick: () => {
                              AlertDialog.warning({
                                title: t("habbit.confirmDeleteHabitTitle"),
                                children: t("common.deleteConfirmDesc"),
                                centered: true,
                                okText: t("common.confirmDelete"),
                                onOk: () => {
                                  deleteProfiling(item.uid, item.pid);
                                },
                              });
                            },
                          },
                        ],
                      }}
                    >
                      <IconButton
                        size="middle"
                        shape="default"
                        className={styles.actionButtons}
                        icon={<SparkMoreLine style={{ fontSize: 20 }} />}
                      />
                    </Dropdown>
                    {item.metadata.is_confirmed === 0 && (
                      <Tooltip title={t("habbit.manualConfirmTip")}>
                        <IconButton
                          size="middle"
                          shape="default"
                          icon={
                            <SparkUserCheckedLine style={{ fontSize: 20 }} />
                          }
                          onDoubleClick={() => {
                            confirmProfiling(item.uid, item.pid);
                          }}
                        />
                      </Tooltip>
                    )}
                  </Flex>
                </div>
              </List.Item>
            )}
          />
        </div>
      </Modal>
      <Modal
        title={getTitle()}
        open={editOpen}
        width={700}
        okText={t("common.confirm")}
        onCancel={onCloseEdit}
        maskClosable={false}
        onOk={onSure}
        footer={
          <Flex gap={16} align="center" justify="flex-end">
            <Button onClick={onCloseEdit}>{t("common.cancel")}</Button>
            <Button type="primary" loading={loading} onClick={onSure}>
              {t("common.confirm")}
            </Button>
          </Flex>
        }
      >
        <TextArea
          rows={Math.min(Math.max(3, habbitContent.split("\n").length + 1), 20)}
          onChange={(v) => {
            setHabbitContent(v.target.value || "");
          }}
          value={habbitContent}
          autoSize={{ minRows: 3, maxRows: 20 }}
        />
      </Modal>
    </>
  );
};

export default memo(HabbitModal);
