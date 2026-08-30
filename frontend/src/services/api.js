import axios from 'axios';
import { API_BASE_URL, API_TIMEOUT, CHAT_TIMEOUT, ENDPOINTS } from '../config/api';

const analyticsApi = axios.create({
  baseURL: API_BASE_URL,
  headers: { 'Content-Type': 'application/json' },
  timeout: API_TIMEOUT,
});

let connectionStatus = 'unknown';
let listeners = new Set();

export const ConnectionService = {
  getStatus: () => connectionStatus,
  subscribe: (cb) => {
    listeners.add(cb);
    return () => listeners.delete(cb);
  },
  _setStatus: (status) => {
    if (status !== connectionStatus) {
      connectionStatus = status;
      listeners.forEach((cb) => cb(status));
    }
  },
};

export const PortfolioService = {
  getAnalysis: async (tickers, weights) => {
    const payload = {
      tickers,
      weights: weights || tickers.map(() => 1 / tickers.length),
      portfolio_value: 100000,
      start: '2020-01-01',
      end: new Date().toISOString().split('T')[0],
    };

    try {
      const res = await analyticsApi.post(ENDPOINTS.analyze, payload, { timeout: 120000 });
      ConnectionService._setStatus('connected');
      return res.data;
    } catch (err) {
      if (err?.code === 'ECONNABORTED' || String(err?.message || '').toLowerCase().includes('timeout')) {
        const retryRes = await analyticsApi.post(ENDPOINTS.analyze, payload, { timeout: 180000 });
        ConnectionService._setStatus('connected');
        return retryRes.data;
      }
      ConnectionService._setStatus('disconnected');
      throw err;
    }
  },

  getForecast: async (ticker, horizon = 30, refresh = false) => {
    const sym = (ticker || '').toUpperCase().trim();
    const res = await analyticsApi.get(ENDPOINTS.forecast(sym), {
      params: { horizon, refresh: refresh ? 1 : 0 },
      timeout: 120000,
    });
    return res.data;
  },

  getMarketRegime: async () => {
    const res = await analyticsApi.get(ENDPOINTS.regime);
    return res.data;
  },

  getSentiment: async (ticker) => {
    const res = await analyticsApi.get(ENDPOINTS.sentiment(ticker));
    return res.data;
  },

  getFundamentals: async (ticker) => {
    const res = await analyticsApi.get(ENDPOINTS.fundamentals(ticker));
    return res.data;
  },

  getTradingDecision: async (ticker) => {
    const res = await analyticsApi.get(ENDPOINTS.tradingDecision, {
      params: { ticker },
    });
    return res.data;
  },

  getTrainedUniverse: async () => {
    const res = await analyticsApi.get(ENDPOINTS.modelsUniverse);
    return res.data;
  },

  getTrainingStatus: async () => {
    const res = await analyticsApi.get(ENDPOINTS.trainingStatus);
    return res.data;
  },

  startTraining: async ({ job_type, preset = 'quick', ticker, tickers }) => {
    const res = await analyticsApi.post(ENDPOINTS.trainingStart, {
      job_type,
      preset,
      ticker: ticker || null,
      tickers: tickers || null,
    });
    return res.data;
  },

  checkHealth: async () => {
    try {
      const res = await analyticsApi.get(ENDPOINTS.modelsStatus, { timeout: 10000 });
      ConnectionService._setStatus('connected');
      return { ok: true, data: res.data };
    } catch (err) {
      ConnectionService._setStatus('disconnected');
      return { ok: false, error: err.message };
    }
  },

  getPortfolioAnalysis: async (payload) => {
    const res = await analyticsApi.post(ENDPOINTS.portfolioAnalyze, payload, { timeout: 180000 });
    return res.data;
  },

  getBenchmarkComparison: async (payload) => {
    const res = await analyticsApi.post(ENDPOINTS.portfolioBenchmark, payload, { timeout: 120000 });
    return res.data;
  },

  getBenchmarks: async () => {
    const res = await analyticsApi.get(ENDPOINTS.benchmarks);
    return res.data;
  },

  getPortfolioAttribution: async (payload) => {
    const res = await analyticsApi.post(ENDPOINTS.portfolioAttribution, payload, { timeout: 120000 });
    return res.data;
  },

  getPortfolioRiskBudget: async (payload) => {
    const res = await analyticsApi.post(ENDPOINTS.portfolioRiskBudget, payload, { timeout: 120000 });
    return res.data;
  },

  analyzeGoal: async (payload) => {
    const res = await analyticsApi.post(ENDPOINTS.portfolioGoal, payload, { timeout: 180000 });
    return res.data;
  },

  getRecommendations: async (payload) => {
    const res = await analyticsApi.post(ENDPOINTS.recommendations, payload, { timeout: 180000 });
    return res.data;
  },

  chatWithTools: async (payload) => {
    const res = await analyticsApi.post(ENDPOINTS.chatTools, payload, { timeout: 180000 });
    return res.data;
  },

  getPpoStatus: async () => {
    const res = await analyticsApi.get(ENDPOINTS.ppoStatus);
    return res.data;
  },
};

export const ChatService = {
  getAdvisorStatus: async () => {
    const res = await analyticsApi.get(ENDPOINTS.advisorStatus);
    return res.data;
  },

  sendMessage: async (payload) => {
    const res = await analyticsApi.post(ENDPOINTS.chat, payload, { timeout: CHAT_TIMEOUT });
    return res.data;
  },

  sendMessageStream: async (payload, onChunk) => {
    const res = await fetch(`${API_BASE_URL}${ENDPOINTS.chatStream}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    const reader = res.body?.getReader();
    if (!reader) throw new Error('Streaming not supported in this browser.');

    const decoder = new TextDecoder();
    let buffer = '';

    while (true) {
      const { value, done } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });

      const parts = buffer.split('\n\n');
      buffer = parts.pop() || '';

      for (const part of parts) {
        const lines = part.split('\n');
        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.slice(6));
              if (data.content) onChunk(data.content);
              if (data.done || data.error) onChunk(null, data);
            } catch (e) {
              console.error('SSE parse error:', e);
            }
          }
        }
      }
    }
  },
};

export default analyticsApi;
