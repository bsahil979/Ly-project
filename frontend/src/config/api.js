export const API_BASE_URL =
  import.meta.env.VITE_API_URL || 'http://localhost:8000';

export const API_TIMEOUT =
  import.meta.env.VITE_API_TIMEOUT_MS
    ? parseInt(import.meta.env.VITE_API_TIMEOUT_MS, 10)
    : 300000;

export const CHAT_TIMEOUT = 300000;

export const HEALTH_CHECK_ENDPOINT = '/models/status';

export const ENDPOINTS = {
  analyze: '/analyze',
  portfolioAnalyze: '/portfolio/analyze',
  forecast: (ticker) => `/forecast/${ticker}`,
  sentiment: (ticker) => `/sentiment/${ticker}`,
  regime: '/market-regime',
  fundamentals: (ticker) => `/fundamentals/${ticker}`,
  tradingDecision: '/trading/decision',
  modelsUniverse: '/models/universe',
  modelsStatus: '/models/status',
  trainingStatus: '/training/status',
  trainingStart: '/training/start',
  portfolioRl: '/portfolio/rl/allocation',
  advisorStatus: '/advisor/status',
  chat: '/chat',
  chatStream: '/chat/stream',
  chatTools: '/chat/tools',
  benchmarks: '/benchmarks',
  portfolioBenchmark: '/portfolio/benchmark',
  portfolioAttribution: '/portfolio/attribution',
  portfolioRiskBudget: '/portfolio/risk-budget',
  portfolioGoal: '/portfolio/goal',
  recommendations: '/recommendations',
  tools: '/tools',
  toolsCall: '/tools/call',
  ppoStatus: '/ppo/status',
};

export default {
  API_BASE_URL,
  API_TIMEOUT,
  CHAT_TIMEOUT,
  ENDPOINTS,
  HEALTH_CHECK_ENDPOINT,
};
