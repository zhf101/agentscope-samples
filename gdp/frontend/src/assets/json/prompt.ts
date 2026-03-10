// Match the corresponding prompt key based on chatMode
export const promptJson = {
  // General
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
        "Generate a detailed report about Alibaba stock price in US market",
    },
    {
      title: "AI Agents Courses on Coursera",
      describe:
        "On Coursera, find 3 popular beginner-level courses about AI agents",
    },
    {
      title: "Fed Rate Outlook",
      describe:
        "Conduct a deep analysis of the expected Federal Reserve (Fed) interest rate cuts in early 2026",
    },
    {
      title: "US-China Chip Impact",
      describe:
        "Perform a comprehensive analysis of the long-term impact of US-China trade tensions on the semiconductor supply chain.",
    },
  ],
  // Browser Use
  browser: [
    {
      title: "AI Agents Courses on Coursera",
      describe:
        "On Coursera, find 3 popular beginner-level courses about AI agents",
    },
    {
      title: "Find Latest AI Browser Agent Papers",
      describe:
        "Search and summarize five recent research papers about browser-use agents",
    },
    {
      title: "Compare Two Product Pages",
      describe:
        "Open two product pages, compare key specs, and summarize differences in a table",
    },
    {
      title: "Collect Event Information",
      describe:
        "Visit the event website, collect schedule and venue details, and provide a concise summary",
    },
    {
      title: "US-China Chip Impact",
      describe:
        "Perform a comprehensive analysis of the long-term impact of US-China trade tensions on the semiconductor supply chain.",
    },
  ],
};

// If chatMode doesn't match any above, use the following
export const originalPromptsList = [
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
      "Generate a detailed report about Alibaba stock price in US market",
  },
  {
    title: "AI Agents Courses on Coursera",
    describe:
      "On Coursera, find 3 popular beginner-level courses about AI agents",
  },
  {
    title: "Fed Rate Outlook",
    describe:
      "Conduct a deep analysis of the expected Federal Reserve (Fed) interest rate cuts in early 2026",
  },
  {
    title: "US-China Chip Impact",
    describe:
      "Perform a comprehensive analysis of the long-term impact of US-China trade tensions on the semiconductor supply chain.",
  },
];
