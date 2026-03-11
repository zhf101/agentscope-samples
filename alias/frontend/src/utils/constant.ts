const MAX_FILE_SIZE = 10 * 1024 * 1024; // 10MB

const FILE_IDS_STORAGE_KEY = "conversation_file_ids";

enum STORAGE_KEY {
  CONVERSATION_ID = "current_conversation_id",
  CONVERSATION = "current_conversation",
}
enum LANGUAGETYPE {
  en_US = "en-US",
  zh_Hans = "zh-Hans",
}
enum ChatModeType {
  GENERAL = "general",
  BROWSER = "browser",
}
const markdownRegex = /^```markdown\n([\s\S]*?)```$/;
const codeBlockRegex = /^```\n([\s\S]*?)```$/;
const ChatModeList = [
  {
    value: ChatModeType.GENERAL,
    labelKey: "chat.mode.general",
  },
  {
    value: ChatModeType.BROWSER,
    labelKey: "chat.mode.browser",
  },
];
export {
  MAX_FILE_SIZE,
  FILE_IDS_STORAGE_KEY,
  STORAGE_KEY,
  LANGUAGETYPE,
  ChatModeType,
  ChatModeList,
  markdownRegex,
  codeBlockRegex,
};
