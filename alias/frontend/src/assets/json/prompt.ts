import type { Locale } from "@/i18n/messages";

const promptJsonByLocale: Record<Locale, Record<string, { title: string; describe: string }[]>> = {
  zh: {
    general: [
      {
        title: "阿里巴巴股价",
        describe: "阿里巴巴当前股价是多少？",
      },
      {
        title: "杭州旅行计划",
        describe: "帮我生成本周末从上海出发去杭州的两日旅行计划",
      },
      {
        title: "阿里巴巴股价报告",
        describe: "生成一份关于阿里巴巴在美股市场股价的详细报告",
      },
      {
        title: "Coursera 上的 AI Agent 课程",
        describe: "在 Coursera 上找 3 门热门的 AI Agent 入门课程",
      },
      {
        title: "AI 服务投资",
        describe:
          "评估未来一年在大模型与边缘计算驱动下、核心 AI 芯片之外的 AI 基础设施软件与服务的投资前景与主要风险",
      },
      {
        title: "美联储利率展望",
        describe: "深入分析 2026 年初美联储（Fed）降息预期",
      },
      {
        title: "英伟达未来财务",
        describe: "预测英伟达 2026 年的财务数据",
      },
      {
        title: "中美芯片影响",
        describe: "全面分析中美贸易紧张局势对半导体供应链的长期影响",
      },
    ],
    browser: [
      {
        title: "Coursera 上的 AI Agent 课程",
        describe: "在 Coursera 上找 3 门热门的 AI Agent 入门课程",
      },
      {
        title: "AI 服务投资",
        describe:
          "评估未来一年在大模型与边缘计算驱动下、核心 AI 芯片之外的 AI 基础设施软件与服务的投资前景与主要风险",
      },
      {
        title: "美联储利率展望",
        describe: "深入分析 2026 年初美联储（Fed）降息预期",
      },
      {
        title: "英伟达未来财务",
        describe: "预测英伟达 2026 年的财务数据",
      },
      {
        title: "中美芯片影响",
        describe: "全面分析中美贸易紧张局势对半导体供应链的长期影响",
      },
    ],
  },
  en: {
    general: [
      {
        title: "Alibaba Stock Price",
        describe: "What's the current stock price of Alibaba?",
      },
      {
        title: "Travel Plan to Hangzhou",
        describe:
          "Help generate a two-day travel plan to Hangzhou this weekend from Shanghai",
      },
      {
        title: "Alibaba Stock Report",
        describe:
          "Generate a detailed report about Alibaba stock price in the US market",
      },
      {
        title: "AI Agents Courses on Coursera",
        describe:
          "On Coursera, find 3 popular beginner-level courses about AI agents",
      },
      {
        title: "AI Service Investment",
        describe:
          "Evaluate the investment outlook and primary risks for AI infrastructure software and services outside the core AI chip sector over the next year, driven by large language models and edge computing",
      },
      {
        title: "Fed Rate Outlook",
        describe:
          "Conduct a deep analysis of the expected Federal Reserve (Fed) interest rate cuts in early 2026",
      },
      {
        title: "Nvidia Future Earnings",
        describe: "Forecast Nvidia’s financial data for 2026",
      },
      {
        title: "US-China Chip Impact",
        describe:
          "Perform a comprehensive analysis of the long-term impact of US-China trade tensions on the semiconductor supply chain",
      },
    ],
    browser: [
      {
        title: "AI Agents Courses on Coursera",
        describe:
          "On Coursera, find 3 popular beginner-level courses about AI agents",
      },
      {
        title: "AI Service Investment",
        describe:
          "Evaluate the investment outlook and primary risks for AI infrastructure software and services outside the core AI chip sector over the next year, driven by large language models and edge computing",
      },
      {
        title: "Fed Rate Outlook",
        describe:
          "Conduct a deep analysis of the expected Federal Reserve (Fed) interest rate cuts in early 2026",
      },
      {
        title: "Nvidia Future Earnings",
        describe: "Forecast Nvidia’s financial data for 2026",
      },
      {
        title: "US-China Chip Impact",
        describe:
          "Perform a comprehensive analysis of the long-term impact of US-China trade tensions on the semiconductor supply chain",
      },
    ],
  },
};

const originalPromptsByLocale: Record<Locale, { title: string; describe: string }[]> = {
  zh: [
    {
      title: "阿里巴巴股价",
      describe: "阿里巴巴当前股价是多少？",
    },
    {
      title: "杭州旅行计划",
      describe: "帮我生成本周末从上海出发去杭州的两日旅行计划",
    },
    {
      title: "阿里巴巴股价报告",
      describe: "生成一份关于阿里巴巴在美股市场股价的详细报告",
    },
    {
      title: "iPhone 17 对比 17 Pro",
      describe: "给出 iPhone 17 与 17 Pro 的详细对比",
    },
    {
      title: "Coursera 上的 AI Agent 课程",
      describe: "在 Coursera 上找 3 门热门的 AI Agent 入门课程",
    },
    {
      title: "AI 服务投资",
      describe:
        "评估未来一年在大模型与边缘计算驱动下、核心 AI 芯片之外的 AI 基础设施软件与服务的投资前景与主要风险",
    },
    {
      title: "美联储利率展望",
      describe: "深入分析 2026 年初美联储（Fed）降息预期",
    },
    {
      title: "英伟达未来财务",
      describe: "预测英伟达 2026 年的财务数据",
    },
    {
      title: "中美芯片影响",
      describe: "全面分析中美贸易紧张局势对半导体供应链的长期影响",
    },
  ],
  en: [
    {
      title: "Alibaba Stock Price",
      describe: "What's the current stock price of Alibaba?",
    },
    {
      title: "Travel Plan to Hangzhou",
      describe:
        "Help generate a two-day travel plan to Hangzhou this weekend from Shanghai",
    },
    {
      title: "Alibaba Stock Report",
      describe:
        "Generate a detailed report about Alibaba stock price in the US market",
    },
    {
      title: "iPhone 17 vs 17 Pro",
      describe: "Give a detailed comparison between iPhone 17 and 17 Pro",
    },
    {
      title: "AI Agents Courses on Coursera",
      describe:
        "On Coursera, find 3 popular beginner-level courses about AI agents",
    },
    {
      title: "AI Service Investment",
      describe:
        "Evaluate the investment outlook and primary risks for AI infrastructure software and services outside the core AI chip sector over the next year, driven by large language models and edge computing",
    },
    {
      title: "Fed Rate Outlook",
      describe:
        "Conduct a deep analysis of the expected Federal Reserve (Fed) interest rate cuts in early 2026",
    },
    {
      title: "Nvidia Future Earnings",
      describe: "Forecast Nvidia’s financial data for 2026",
    },
    {
      title: "US-China Chip Impact",
      describe:
        "Perform a comprehensive analysis of the long-term impact of US-China trade tensions on the semiconductor supply chain",
    },
  ],
};

export const getPromptsByLocale = (locale: Locale) =>
  promptJsonByLocale[locale] || promptJsonByLocale.zh;

export const getOriginalPromptsByLocale = (locale: Locale) =>
  originalPromptsByLocale[locale] || originalPromptsByLocale.zh;
