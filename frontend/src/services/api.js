import axios from 'axios';

const ANALYTICS_URL = 'http://localhost:8002';

const analyticsApi = axios.create({
  baseURL: ANALYTICS_URL,
  headers: { 'Content-Type': 'application/json' },
});

export const PortfolioService = {
  getAnalysis: async (tickers, weights) => {
    const res = await analyticsApi.post('/analyze', {
      tickers,
      weights: weights || tickers.map(() => 1 / tickers.length),
      portfolio_value: 100000,
      start: '2020-01-01',
      end: new Date().toISOString().split('T')[0],
    });
    return res.data;
  },

  getForecast: async (ticker, horizon = 30) => {
    const res = await analyticsApi.get(`/forecast/${ticker}?horizon=${horizon}`);
    return res.data;
  },

  getMarketRegime: async () => {
    const res = await analyticsApi.get('/market-regime');
    return res.data;
  },

  getSentiment: async (ticker) => {
    const res = await analyticsApi.get(`/sentiment/${ticker}`);
    return res.data;
  },
};

export const ChatService = {
  sendMessage: async (message) => {
    // Mock response — will be replaced with Gemini/FinBERT integration
    return {
      role: 'assistant',
      text: "I've analyzed your portfolio. Based on the current market regime, I recommend maintaining your current allocation while monitoring sector rotations.",
    };
  },
};

export default analyticsApi;
