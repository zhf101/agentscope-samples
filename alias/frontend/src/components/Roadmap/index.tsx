import React, {
  useState,
  useEffect,
  useContext,
  useMemo,
  createContext,
  memo,
} from "react";
import diff from "deep-diff";
import {
  Button,
  message,
  Input,
  AlertDialog,
  IconButton,
  Modal,
} from "@agentscope-ai/design";
import { List, Flex, GetProps } from "antd";
import {
  SparkPlusLine,
  SparkSaveLine,
  SparkDeleteLine,
  SparkEditLine,
  SparkDragDotLine,
  SparkIncompleteLine,
  SparkLoadingLine,
  SparkCheckCircleLine,
  SparkProcessFailedLine,
} from "@agentscope-ai/icons";
import classNames from "classnames";
import styles from "./index.module.scss";
import { SubtasksProps, RoadMapDataProps, RoadMapType } from "@/types/roadmap";
import { conversationApi } from "@/services/api/conversation";
import type { DragEndEvent, DraggableAttributes } from "@dnd-kit/core";
import { DndContext } from "@dnd-kit/core";
import type { SyntheticListenerMap } from "@dnd-kit/core/dist/hooks/utilities";
import { restrictToVerticalAxis } from "@dnd-kit/modifiers";
import {
  arrayMove,
  SortableContext,
  useSortable,
  verticalListSortingStrategy,
} from "@dnd-kit/sortable";
import { CSS } from "@dnd-kit/utilities";
import { useI18n } from "@/context/LanguageContext";

interface RoadmapProps {
  data?: RoadMapDataProps | null;
  conversationId: string;
  editable?: boolean;
  onSave?: (data: RoadMapDataProps) => void;
}

interface SortableListItemContextProps {
  setActivatorNodeRef?: (element: HTMLElement | null) => void;
  listeners?: SyntheticListenerMap;
  attributes?: DraggableAttributes;
}

const fontSize = { fontSize: 20 };
const SortableListItemContext = createContext<SortableListItemContextProps>({});
const DragHandle: React.FC = () => {
  const { setActivatorNodeRef, listeners, attributes } = useContext(
    SortableListItemContext,
  );
  return (
    <Button
      type="text"
      size="small"
      icon={<SparkDragDotLine />}
      style={{ cursor: "move" }}
      ref={setActivatorNodeRef}
      {...attributes}
      {...listeners}
    />
  );
};
const SortableListItem: React.FC<
  GetProps<typeof List.Item> & { itemKey: number }
> = (props) => {
  const { itemKey, style, ...rest } = props;
  const {
    attributes,
    listeners,
    setNodeRef,
    setActivatorNodeRef,
    transform,
    transition,
    isDragging,
  } = useSortable({ id: itemKey });

  const listStyle: React.CSSProperties = {
    ...style,
    transform: CSS.Translate.toString(transform),
    transition,
    ...(isDragging ? { position: "relative", zIndex: 9999 } : {}),
  };

  const memoizedValue = useMemo<SortableListItemContextProps>(
    () => ({ setActivatorNodeRef, listeners, attributes }),
    [setActivatorNodeRef, listeners, attributes],
  );

  return (
    <SortableListItemContext.Provider value={memoizedValue}>
      <List.Item {...rest} ref={setNodeRef} style={listStyle} />
    </SortableListItemContext.Provider>
  );
};
const ReadListItem: React.FC<
  GetProps<typeof List.Item> & { item: SubtasksProps }
> = ({ item }) => {
  const { state, description } = item || {};
  return (
    <List.Item className={styles.listItem}>
      <Flex
        gap="small"
        align="center"
        className={classNames(styles.itemFlex, {
          [styles.success]: state === RoadMapType.DONE,
        })}
      >
        <Flex gap="small">
          {state === RoadMapType.IN_PROGRESS && (
            <SparkLoadingLine style={{ ...fontSize, color: "#0B83F1" }} />
          )}
          {state === RoadMapType.DONE && (
            <SparkCheckCircleLine style={fontSize} />
          )}
          {state === RoadMapType.TODO && (
            <SparkIncompleteLine style={fontSize} />
          )}
          {state === RoadMapType.ABANDONED && (
            <SparkProcessFailedLine style={fontSize} />
          )}
          {description}
        </Flex>
      </Flex>
    </List.Item>
  );
};

const Roadmap: React.FC<RoadmapProps> = ({
  data,
  conversationId,
  editable,
  onSave = (data: RoadMapDataProps) => {},
}) => {
  const { t } = useI18n();
  const [isEditing, setIsEditing] = useState(false);
  const [taskValue, setTaskValue] = useState("");
  const [open, setOpen] = useState(false);
  const [list, setList] = useState<SubtasksProps[]>(data?.subtasks || []);
  const [taskKey, setTaskKey] = useState<number | undefined>();

  useEffect(() => {
    if (data?.subtasks && Array.isArray(data?.subtasks)) {
      const newList = data.subtasks.map((item, index) => {
        return {
          ...item,
          key: index + 1,
        };
      });
      setList(newList);
    }
  }, [data?.subtasks]);

  const onDragEnd = ({ active, over }: DragEndEvent) => {
    if (!active || !over) {
      return;
    }
    if (active.id !== over.id) {
      setList((prevState) => {
        const activeIndex = prevState.findIndex((i) => i.key === active.id);
        const overIndex = prevState.findIndex((i) => i.key === over.id);
        return arrayMove(prevState, activeIndex, overIndex);
      });
    }
  };

  const onSaveHandle = () => {
    AlertDialog.info({
      title: t("roadmap.confirmSaveTitle"),
      children: t("roadmap.confirmSaveDesc"),
      centered: true,
      okText: t("roadmap.save"),
      onOk: async () => {
        const newList = list.map(({ key, ...rest }) => rest);
        const newData = { subtasks: newList };
        const differences: any = diff(data, newData);
        if (differences) {
          try {
            const response: any = await conversationApi.setRoadmap(
              conversationId,
              newData,
            );
          if (response.status && response?.payload) {
            onSave(response?.payload);
          }
        } catch (error) {
            message.error(t("roadmap.updateFailed"));
            console.error("Error updating roadmap:", error);
          }
        } else {
          message.info(t("roadmap.noChanges"));
          setIsEditing(false);
        }
        onCancel();
      },
    });
  };
  const onAddTask = () => {
    setOpen(true);
    setTaskValue("");
    setTaskKey(undefined);
  };
  const deletedHandle = (key: number) => {
    AlertDialog.warning({
      title: t("roadmap.confirmDeleteTaskTitle"),
      children: t("roadmap.confirmDeleteTaskDesc"),
      centered: true,
      okText: t("roadmap.confirmDeleteTaskOk"),
      onOk: () => {
        setList(list.filter((item) => item.key !== key));
      },
    });
  };
  const updateTaskHandle = (content: string, key: number) => {
    setOpen(true);
    setTaskValue(content);
    setTaskKey(key);
  };
  const onCancel = () => {
    setOpen(false);
  };
  const onOk = () => {
    const trimmedValue = taskValue.trim();
    if (!trimmedValue) {
      message.info(t("roadmap.enterTask"));
      return;
    }
    if (taskKey) {
      setList(
        list.map((item) =>
          item.key === taskKey ? { ...item, description: taskValue } : item,
        ),
      );
    } else {
      setList([
        ...list,
        {
          key: new Date().getTime(),
          state: RoadMapType.TODO,
          description: taskValue.trim(),
        },
      ]);
    }
    onCancel();
  };
  // const renderReadItem =
  return (
    <div className={styles.roadmap}>
      <Flex align="center" justify="space-between">
        <div className={styles.title}>{t("roadmap.title")}</div>
        {editable && isEditing && (
          <Flex gap="small">
            <Button onClick={onAddTask}>
              <SparkPlusLine /> {t("roadmap.addTask")}
            </Button>
            <Button type="primary" onClick={onSaveHandle}>
              <SparkSaveLine /> {t("roadmap.save")}
            </Button>
          </Flex>
        )}
        {editable && !isEditing && (
          <Button
            onClick={() => {
              setIsEditing(true);
            }}
          >
            <SparkEditLine /> {t("common.edit")}
          </Button>
        )}
      </Flex>
      <DndContext
        modifiers={[restrictToVerticalAxis]}
        onDragEnd={onDragEnd}
        id="list-drag-sorting-handler"
      >
        <SortableContext
          items={list.map((item, index) => item.key || index)}
          strategy={verticalListSortingStrategy}
        >
          <List
            className={styles.roadmapList}
            dataSource={list}
            renderItem={(item, index) => {
              const { description, state, key } = item || {};
              if (isEditing && editable)
                return (
                  <SortableListItem
                    key={key}
                    itemKey={key || index}
                    className={styles.listItem}
                  >
                    <Flex
                      gap="small"
                      justify="space-between"
                      align="center"
                      className={styles.itemFlex}
                    >
                      <Flex gap="small">
                        <DragHandle />
                        {state === RoadMapType.IN_PROGRESS && (
                          <SparkLoadingLine
                            style={{ ...fontSize, color: "#0B83F1" }}
                          />
                        )}
                        {state === RoadMapType.DONE && (
                          <SparkCheckCircleLine style={fontSize} />
                        )}
                        {state === RoadMapType.TODO && (
                          <SparkIncompleteLine style={fontSize} />
                        )}
                        {state === RoadMapType.ABANDONED && (
                          <SparkProcessFailedLine style={fontSize} />
                        )}
                        {description}
                      </Flex>
                      <Flex gap="small">
                        {item.state === RoadMapType.TODO && (
                          <IconButton
                            icon={<SparkEditLine style={fontSize} />}
                            bordered={false}
                            onClick={() => {
                              updateTaskHandle(description, key || index);
                            }}
                          />
                        )}
                        <IconButton
                          icon={<SparkDeleteLine style={fontSize} />}
                          bordered={false}
                          onClick={() => {
                            deletedHandle(key || index);
                          }}
                        />
                      </Flex>
                    </Flex>
                  </SortableListItem>
                );
              return <ReadListItem item={item} />;
            }}
          />
        </SortableContext>
      </DndContext>
      <Modal
        open={open}
        onCancel={onCancel}
        onOk={onOk}
        okText={t("common.confirm")}
        title={t("roadmap.editTask")}
      >
        <Input.TextArea
          rows={Math.min(Math.max(3, taskValue.split("\n").length + 1), 20)}
          onChange={(v) => {
            setTaskValue(v.target.value || "");
          }}
          value={taskValue}
          autoSize={{ minRows: 10, maxRows: 20 }}
        />
      </Modal>
    </div>
  );
};
export default memo(Roadmap);
