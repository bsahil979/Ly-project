"""
AI Advisor — LLM + RAG layer that augments the existing ML microservices.

This module sits on top of the Smart Portfolio Advisor analytics engine.
It gathers structured outputs from every ML service (risk metrics, HMM regime,
FinBERT sentiment, TimesFM price forecasts, stress tests, MarketMind meta-model, PPO RL
allocations, decision options) plus retrieved financial documents (news + a
static knowledge base), then calls an LLM to produce a natural-language
explanation of the analysis.

The LLM provider is fully configurable via environment variables:

    LLM_API_KEY     – API key (OpenAI, OpenRouter, Ollama token, etc.)
    LLM_BASE_URL    – API base URL (default: OpenAI)
    LLM_MODEL       – model name (default: gpt-4o-mini)

When LLM_API_KEY is absent the advisor falls back to a compact template
summary of the structured context so the endpoint remains usable offline.
"""

from __future__ import annotations

import datetime
import json
import logging
import os
import textwrap
import time
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Optional

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

_ANALYTICS_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_MODELS_DIR = os.path.join(_ANALYTICS_DIR, "models")
_KB_PATH = os.path.join(_ANALYTICS_DIR, "data", "knowledge_base.json")


# ─────────────────────────────────────────────────────────────────────────────
#  Serialization helpers
# ─────────────────────────────────────────────────────────────────────────────

def _clean(obj: Any) -> Any:
    """Recursively convert pandas/numpy objects to JSON-serialisable values."""
    if isinstance(obj, dict):
        return {str(k): _clean(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_clean(v) for v in obj]
    if isinstance(obj, (pd.Series, pd.DataFrame)):
        try:
            return _clean(obj.to_dict())
        except Exception:
            return str(obj)
    if isinstance(obj, (np.integer,)):
        return int(obj)
    if isinstance(obj, (np.floating,)):
        v = float(obj)
        if np.isnan(v) or np.isinf(v):
            return None
        return v
    if isinstance(obj, np.bool_):
        return bool(obj)
    if not isinstance(obj, str):
        try:
            if pd.isna(obj):
                return None
        except (TypeError, ValueError):
            pass
    return obj


def _fmt_price_series(prices: pd.Series, maxlen: int = 30) -> str:
    """Summarise a price series to recent tail + basic stats (keeps prompt short)."""
    if prices is None or len(prices) == 0:
        return "no data"
    tail = prices.tail(min(maxlen, len(prices)))
    parts = []
    for d, v in tail.items():
        try:
            parts.append(f"{pd.Timestamp(d).strftime('%Y-%m-%d')}: {float(v):.2f}")
        except Exception:
            pass
    stats = (
        f"latest={float(prices.iloc[-1]):.2f}, "
        f"min={float(prices.min()):.2f}, max={float(prices.max()):.2f}"
    )
    return f"recent prices: {stats} | tail(10): {', '.join(parts[-10:])}"


# ─────────────────────────────────────────────────────────────────────────────
#  RAG Retriever
# ─────────────────────────────────────────────────────────────────────────────

class FinancialKnowledgeBase:
    """Static financial-concept documents for RAG retrieval."""

    DEFAULT_DOCS = [
        {
            "id": "kb-risk-var",
            "category": "risk_metrics",
            "content": (
                "Value at Risk (VaR) at 95% is the maximum expected loss over a given "
                "horizon at that confidence level. CVaR (Conditional Value at Risk) is "
                "the average loss beyond the VaR threshold — it is always worse than VaR "
                "and captures tail risk better."
            ),
        },
        {
            "id": "kb-risk-vol",
            "category": "risk_metrics",
            "content": (
                "Annualized volatility = daily std × sqrt(252). A stock with 35%+ annual "
                "volatility is considered high-risk; 15-20% is moderate; under 15% is low."
            ),
        },
        {
            "id": "kb-risk-drawdown",
            "category": "risk_metrics",
            "content": (
                "Maximum drawdown is the largest peak-to-trough decline. A drawdown over "
                "30% typically flags a HIGH risk portfolio that needs de-risking."
            ),
        },
        {
            "id": "kb-regime-hmm",
            "category": "market_regime",
            "content": (
                "Hidden Markov Models (HMM) infer latent market states from return "
                "sequences. States are labelled by mean return: highest = Bullish, lowest "
                "= Bearish, middle = Volatile/Neutral. Confidence is the model's predicted "
                "probability of the current state."
            ),
        },
        {
            "id": "kb-forecast",
            "category": "time_series_forecast",
            "content": (
                "Price forecasts use Google TimesFM 2.5 (200M parameter foundation model) "
                "with a 60-day lookback window to forecast `horizon` future days. "
                "Log-returns are forecasted and converted back to price levels. "
                "If TimesFM is unavailable, a custom LSTM (60-day lookback, 8 training epochs) "
                "serves as the fallback model."
            ),
        },
        {
            "id": "kb-sentiment-finbert",
            "category": "sentiment_analysis",
            "content": (
                "FinBERT (Financial BERT, ProsusAI) scores news headlines on a "
                "-1 to +1 compound scale (positive_prob - negative_prob). "
                "Bullish >0.15, Slightly Bullish >0.05, Neutral, "
                "Slightly Bearish <-0.05, Bearish <-0.15. News is sourced from "
                "Yahoo Finance and Google News."
            ),
        },
        {
            "id": "kb-stress-test",
            "category": "stress_testing",
            "content": (
                "Stress tests simulate losses under extreme historical events: 2008 Financial "
                "Crisis (~-40%), COVID Crash 2020 (~-30%), Tech Sector Crash (~-35%), Rate "
                "Hike Shock (~-15%). The worst scenario identifies the maximum potential loss."
            ),
        },
        {
            "id": "kb-decision-options",
            "category": "portfolio_theory",
            "content": (
                "Three decision options are generated: Conservative (50% equity cut + bonds), "
                "Balanced (25% equity cut + bonds), Aggressive (full equity). Risk level is "
                "HIGH if 2+ thresholds breached (>35% vol, <-3% VaR, <-30% drawdown), MEDIUM "
                "if 1 breached, LOW if none."
            ),
        },
        {
            "id": "kb-marketmind",
            "category": "meta_model",
            "content": (
                "MarketMind is a meta-model that fuses technical indicators (RSI, MACD, ADX, "
                "EMA, momentum, volatility) with sentiment and regime codes, then classifies "
                "the ticker as BUY/SELL/HOLD using an ensemble of Logistic Regression, Random "
                "Forest, and Histogram Gradient Boosting."
            ),
        },
        {
            "id": "kb-ppo-rl",
            "category": "rl_portfolio",
            "content": (
                "A PPO (Proximal Policy Optimization) reinforcement learning agent recommends "
                "dynamic portfolio weight allocations and cash management across 100 tickers. "
                "The reward balances Sharpe ratio against drawdown. The RL Optimized allocation "
                "appears when the trained policy checkpoint is available."
            ),
        },
    ]

    @classmethod
    def load(cls) -> list[dict]:
        docs = list(cls.DEFAULT_DOCS)
        if os.path.exists(_KB_PATH):
            try:
                with open(_KB_PATH, encoding="utf-8") as f:
                    extra = json.load(f)
                if isinstance(extra, list):
                    docs.extend(extra)
            except Exception as exc:
                logger.warning("Failed to load knowledge base from %s: %s", _KB_PATH, exc)
        return docs


class RAGRetriever:
    """
    Lightweight TF-IDF retriever for financial news + knowledge-base documents.

    Uses scikit-learn (already a dependency) — no external vector DB required.
    """

    def __init__(self):
        self._tfidf = None
        self._cosine = None
        self._news_cache: dict = {}

    # ── document collection ──────────────────────────────────────────

    def collect_news(self, tickers: list[str], max_per_ticker: int = 10) -> list[dict]:
        """Collect recent news headlines for *tickers* from Yahoo + Google News.

        Results are cached for 60 seconds to avoid repeated network calls.
        """
        cache_key = tuple(sorted(t.upper() for t in tickers))
        cached = self._news_cache.get(cache_key)
        now = time.time()
        if cached is not None and now - cached["ts"] < 60:
            return cached["docs"]

        from services.sentiment_analyzer import (
            _fetch_yahoo_news,
            _fetch_google_news,
            _deduplicate,
        )

        docs: list[dict] = []
        for ticker in tickers:
            try:
                articles = _deduplicate(
                    _fetch_yahoo_news(ticker) + _fetch_google_news(ticker)
                )
            except Exception:
                articles = []
            for a in articles[:max_per_ticker]:
                docs.append({
                    "type": "news",
                    "ticker": ticker.upper(),
                    "title": a.get("title", ""),
                    "content": f"{a.get('title', '')} ({a.get('publisher', 'Unknown')})",
                    "source": a.get("source", "Unknown"),
                    "published": a.get("published", ""),
                    "url": a.get("link", ""),
                })
        self._news_cache[cache_key] = {"ts": time.time(), "docs": docs}
        return docs

    def collect_knowledge_base(self) -> list[dict]:
        """Return financial-concept documents from the static knowledge base."""
        docs = []
        for entry in FinancialKnowledgeBase.load():
            docs.append({
                "type": "knowledge",
                "id": entry["id"],
                "category": entry["category"],
                "content": entry["content"],
                "source": f"knowledge_base:{entry['category']}",
            })
        return docs

    def collect_all(self, tickers: list[str], max_news: int = 8) -> list[dict]:
        """Combine news + knowledge-base documents into one retrieval corpus."""
        return self.collect_news(tickers, max_per_ticker=max_news) + self.collect_knowledge_base()

    # ── retrieval ────────────────────────────────────────────────────

    def retrieve(self, query: str, documents: list[dict], top_k: int = 5) -> list[dict]:
        """Return the *top_k* documents most relevant to *query* (TF-IDF cosine)."""
        if not documents:
            return []
        if self._tfidf is None:
            from sklearn.feature_extraction.text import TfidfVectorizer
            from sklearn.metrics.pairwise import cosine_similarity
            self._tfidf = TfidfVectorizer
            self._cosine = cosine_similarity

        texts = [d.get("content", "") for d in documents]
        corpus = texts + [query]
        try:
            matrix = self._tfidf(
                stop_words="english",
                ngram_range=(1, 2),
                max_features=5000,
            ).fit_transform(corpus)
            sims = self._cosine(matrix[-1], matrix[:-1]).flatten()
        except ValueError:
            return documents[:top_k]

        scored = list(zip(documents, sims))
        scored.sort(key=lambda pair: pair[1], reverse=True)
        return [doc for doc, score in scored[:top_k] if score > 0]


# ─────────────────────────────────────────────────────────────────────────────
#  Context gathering
# ─────────────────────────────────────────────────────────────────────────────

class AIAdvisor:
    """
    Orchestrates structured-context gathering, RAG retrieval, and LLM generation.
    """

    def __init__(self):
        self.api_key: Optional[str] = os.environ.get("LLM_API_KEY")
        self.base_url: str = os.environ.get("LLM_BASE_URL", "https://api.openai.com/v1")
        self.model: str = os.environ.get("LLM_MODEL", "gpt-4o-mini")
        self.max_tokens: int = int(os.environ.get("LLM_MAX_TOKENS", "1024"))
        self._client = None
        self._retriever = RAGRetriever()

        # Auto-detect provider from API key format
        if self.api_key and self.api_key.startswith("AIza"):
            self.provider = "gemini"
            if not os.environ.get("LLM_MODEL"):
                self.model = "gemini-3.6-flash"
        else:
            self.provider = os.environ.get("LLM_PROVIDER", "openai")

    # ── LLM client ───────────────────────────────────────────────────

    @property
    def is_configured(self) -> bool:
        return bool(self.api_key)

    def _get_client(self):
        if not self.api_key:
            raise RuntimeError("LLM_API_KEY is not set - configure it to enable LLM responses.")
        if self._client is None:
            if self.provider == "gemini":
                import google.generativeai as genai
                genai.configure(api_key=self.api_key)
                self._client = genai
            else:
                from openai import OpenAI
                self._client = OpenAI(api_key=self.api_key, base_url=self.base_url)
        return self._client

    # ── structured context ───────────────────────────────────────────

    @staticmethod
    def _price_series(prices, ticker: str) -> pd.Series:
        sym = ticker.upper().strip()
        if isinstance(prices, pd.Series):
            return prices.dropna()
        cols = {str(c).upper(): c for c in prices.columns}
        if sym in cols:
            return prices[cols[sym]].dropna()
        if len(prices.columns) == 1:
            return prices.iloc[:, 0].dropna()
        raise ValueError(f"No price column for {sym}")

    @staticmethod
    def _currency_symbol(currency_map: dict) -> str:
        if "INR" in currency_map.values():
            return "₹"
        counts = pd.Series(list(currency_map.values())).value_counts()
        dominant = counts.index[0] if not counts.empty else "USD"
        symbols = {"USD": "$", "INR": "₹", "EUR": "€", "GBP": "£"}
        return symbols.get(dominant, "$")

    def gather_structured_context(
        self,
        tickers: list[str],
        weights: list[float],
        portfolio_value: float = 100000,
        start: str = "2020-01-01",
        end: Optional[str] = None,
        horizon: int = 30,
    ) -> dict:
        """Collect structured outputs from every ML microservice.

        Optimized: a single batch price fetch replaces N+2 separate network
        calls, and independent services run in thread pools.
        """
        today = datetime.datetime.now().strftime("%Y-%m-%d")
        end = end or today
        result: dict[str, Any] = {"tickers": tickers, "portfolio_value": portfolio_value}

        if not (tickers and len(tickers) == len(weights or [])):
            result["portfolio_error"] = "Provide matching tickers and weights."
            return result

        # ── Single batch fetch for all tickers + SPY ───────────────────────
        from services.data_fetcher import get_portfolio_data
        from services.risk_metrics import get_risk_summary
        from services.regime_detector import detect_market_regime_hmm
        from services.stress_tester import get_stress_summary
        from agents.decision_engine import generate_decision_options

        all_symbols = list(dict.fromkeys(tickers)) + (["SPY"] if "SPY" not in tickers else [])
        try:
            data = get_portfolio_data(all_symbols, start, end)
        except Exception as exc:
            logger.exception("Batch price fetch failed")
            result["portfolio_error"] = str(exc)
            return result

        prices = data["prices"]
        returns = data["returns"]
        currency = self._currency_symbol(data.get("currencies", {}))

        # ── 1. Risk + regime + stress (parallel) ─────────────────────────────
        try:
            with ThreadPoolExecutor(max_workers=3) as pool:
                f_risk = pool.submit(get_risk_summary, prices, returns)
                f_regime = pool.submit(detect_market_regime_hmm, returns.mean(axis=1))
                f_stress = pool.submit(get_stress_summary, tickers, weights, portfolio_value)

                risk = f_risk.result()
                regime = f_regime.result()
                stress = f_stress.result()

            risk_summary = _clean(risk["summary"].round(4).to_dict())
            stress_table = _clean({k: v for k, v in stress.items() if k != "stress_table"})
            options = generate_decision_options(
                tickers, weights, risk["summary"], regime, stress,
                portfolio_value, currency,
            )
            result["portfolio"] = {
                "risk_summary": risk_summary,
                "market_regime": regime,
                "stress_test": {
                    **stress_table,
                    "stress_table": _clean(stress["stress_table"].to_dict()),
                },
                "decision_options": _clean(options),
                "currency": currency,
            }
        except Exception as exc:
            logger.exception("Portfolio analysis failed")
            result["portfolio_error"] = str(exc)

        # ── 2. Broad market regime (SPY proxy) from the same fetch ──────────
        try:
            if isinstance(returns, pd.DataFrame) and "SPY" in returns.columns:
                result["market_regime"] = detect_market_regime_hmm(returns["SPY"])
            elif isinstance(returns, pd.DataFrame):
                result["market_regime"] = detect_market_regime_hmm(returns.iloc[:, 0])
        except Exception as exc:
            logger.exception("Market regime detection failed")
            result["market_regime_error"] = str(exc)

        # ── 3. Per-ticker: forecast + sentiment + MarketMind (parallel) ─────
        from services.forecaster import get_lstm_forecast
        from services.sentiment_analyzer import get_sentiment_analysis

        def _process_ticker(ticker: str) -> tuple[str, dict]:
            info: dict[str, Any] = {}
            sym = ticker.upper().strip()

            # Reuse already-fetched prices — no extra network call
            try:
                ticker_prices = self._price_series(prices, sym)
                if len(ticker_prices) >= 30:
                    forecast = get_lstm_forecast(ticker_prices, horizon, train_epochs=8)
                    info["forecast"] = {
                        "spot_price": float(ticker_prices.iloc[-1]),
                        "predictions": forecast[:5] + (
                            [{"...": "truncated"}] if len(forecast) > 5 else []
                        ),
                        "horizon": horizon,
                    }
                else:
                    info["forecast"] = {
                        "error": f"Insufficient history for {sym} (need 30, got {len(ticker_prices)})"
                    }
            except Exception as exc:
                info["forecast_error"] = str(exc)

            try:
                info["sentiment"] = get_sentiment_analysis(sym)
            except Exception as exc:
                info["sentiment_error"] = str(exc)

            try:
                from trading_engine.meta_model import MarketMindMetaModel
                model = MarketMindMetaModel(model_dir=os.path.join(_MODELS_DIR, "meta_model"))
                if model.is_ready():
                    if model.model is None:
                        model.load()
                    info["marketmind"] = model.predict_for_ticker(sym)
                else:
                    info["marketmind"] = {"status": "not_trained"}
            except Exception as exc:
                info["marketmind_error"] = str(exc)

            return ticker, _clean(info)

        result["ticker_details"] = {}
        try:
            with ThreadPoolExecutor(max_workers=max(len(tickers), 1)) as pool:
                futures = [pool.submit(_process_ticker, t) for t in tickers]
                for fut in futures:
                    tname, tinfo = fut.result()
                    result["ticker_details"][tname] = tinfo
        except Exception as exc:
            logger.exception("Per-ticker processing partially failed")
            result["ticker_details_error"] = str(exc)

        return result

    # ── LLM generation ─────────────────────────────────────────────────

    def _build_system_prompt(self) -> str:
        return textwrap.dedent("""\
            You are *AI Wealth Advisor*, the conversational layer on top of the
            Smart Portfolio Advisor analytics engine. Your job is to explain the
            underlying quantitative analysis to the user in clear, conversational
            English — not to give generic financial advice.

            You have access to three sources of information:
              1. **Structured ML context** — risk metrics (VaR, CVaR, volatility,
                 max drawdown), HMM market-regime detection, TimesFM price forecasts,
                 FinBERT news sentiment, stress-test scenarios, MarketMind meta-model
                 recommendations (BUY/SELL/HOLD), and PPO RL allocation suggestions.
              2. **RAG documents** — relevant news headlines and a financial
                 knowledge base retrieved via TF-IDF.
              3. **The user's question.**

            Guidelines:
              • Answer the user's question using only the provided data.
              • Cite specific numbers (volatility %, VaR %, regime confidence,
                sentiment score, forecast levels).
              • When a metric is unavailable, say so clearly.
              • Keep answers concise but substantive — 2–4 short paragraphs.
              • Use a friendly, professional tone.
              • Include a brief disclaimer: "This is quantitative analysis, not
                personalized investment advice."
        """)

    def _format_context_block(self, structured: dict, retrieved_docs: list[dict]) -> str:
        lines = []

        # Portfolio summary
        port = structured.get("portfolio", {})
        if "portfolio_error" in structured:
            lines.append(f"Portfolio analysis error: {structured['portfolio_error']}")
        elif port:
            lines.append("## Portfolio Analysis")
            portfolio_value = structured.get("portfolio_value", 100000)
            currency = port.get("currency", "$")
            lines.append(f"Portfolio value: {currency}{portfolio_value:,.0f}")

            risk = port.get("risk_summary", {})
            if risk:
                lines.append("Risk metrics:")
                for ticker in structured.get("tickers", []):
                    vol = risk.get("Volatility (Annual)", {}).get(ticker, "n/a")
                    var = risk.get("VaR (95%)", {}).get(ticker, "n/a")
                    cvar = risk.get("CVaR (95%)", {}).get(ticker, "n/a")
                    dd = risk.get("Max Drawdown", {}).get(ticker, "n/a")
                    lines.append(
                        f"  {ticker}: volatility={vol}, VaR(95%)={var}, CVaR={cvar}, max_drawdown={dd}"
                    )

            regime = port.get("market_regime", {})
            if regime:
                lines.append(
                    f"Market regime: {regime.get('current_regime', 'unknown')} "
                    f"(state {regime.get('state_id')}, confidence {regime.get('confidence', 'n/a')})"
                )

            stress = port.get("stress_test", {})
            if stress:
                lines.append(
                    f"Worst-case stress: {stress.get('worst_scenario', 'unknown')} "
                    f"- loss {currency}{abs(stress.get('worst_loss', 0)):,.2f} "
                    f"({stress.get('worst_loss_pct', 0):.1f}%)"
                )

            options = port.get("decision_options", [])
            if options:
                lines.append("Decision options:")
                for opt in options[:3]:
                    lines.append(
                        f"  * {opt.get('option')}: {opt.get('description', '')} "
                        f"| expected return: {opt.get('expected_return', 'n/a')} "
                        f"| downside: {opt.get('downside_risk', 'n/a')}"
                    )

        # Broad market regime
        regime = structured.get("market_regime", {})
        if regime:
            lines.append(
                f"Broad market regime (SPY): {regime.get('current_regime', 'unknown')} "
                f"- confidence {regime.get('confidence', 'n/a')}"
            )

        # Per-ticker details
        details = structured.get("ticker_details", {})
        if details:
            lines.append("## Per-Ticker Details")
            for ticker, info in details.items():
                lines.append(f"### {ticker}")
                fc = info.get("forecast")
                if fc and "predictions" in fc:
                    preds = fc["predictions"]
                    valid = [p for p in preds if isinstance(p, dict) and "predicted_price" in p]
                    pred_strs = [f"{p['date']}:{float(p['predicted_price']):.2f}" for p in valid]
                    lines.append(
                        f"  Forecast (spot={fc.get('spot_price', 'n/a')}): "
                        f"{len(preds)} points - {', '.join(pred_strs[:3])}"
                    )
                elif fc and "error" in fc:
                    lines.append(f"  Forecast: {fc['error']}")

                sent = info.get("sentiment")
                if sent:
                    lines.append(
                        f"  Sentiment: {sent.get('overall_sentiment', 'unknown')} "
                        f"(score {sent.get('overall_score', 'n/a')}, "
                        f"{sent.get('articles_analyzed', 0)} headlines)"
                    )

                mm = info.get("marketmind")
                if mm and isinstance(mm, dict) and mm.get("status") != "not_trained":
                    lines.append(
                        f"  MarketMind: {mm.get('recommendation', 'unknown')} "
                        f"(score={mm.get('score')}, confidence={mm.get('confidence', 'n/a')})"
                    )

        # RAG documents
        if retrieved_docs:
            lines.append("## Retrieved Reference Documents")
            for doc in retrieved_docs:
                tag = doc.get("type", "doc")
                title = doc.get("title") or f"[{doc.get('category', 'doc')}]"
                lines.append(f"  [{tag}] {title}: {doc.get('content', '')[:300]}")

        return "\n".join(lines)

    def _build_user_prompt(self, query: str, structured: dict, retrieved_docs: list[dict]) -> str:
        context = self._format_context_block(structured, retrieved_docs)
        return textwrap.dedent(f"""\
            User question: {query}
            
            Available context (structured ML results + RAG documents):
            
            {context}
            
            Answer the user's question using this context. Cite specific numbers.
        """)

    def _generate_template_fallback(self, query: str, structured: dict, retrieved_docs: list[dict]) -> str:
        """When no LLM is configured, return a compact structured summary."""
        context = self._format_context_block(structured, retrieved_docs)
        return (
            "LLM is not configured (set LLM_API_KEY to enable AI-generated responses). "
            "Here is the structured analysis context:\n\n"
            f"{context}\n\n"
            "*This is quantitative analysis, not personalized investment advice.*"
        )

    def chat(
        self,
        query: str,
        tickers: list[str] | None = None,
        weights: list[float] | None = None,
        portfolio_value: float = 100000,
        start: str = "2020-01-01",
        end: Optional[str] = None,
        horizon: int = 30,
        top_k: int = 5,
    ) -> dict:
        """Non-streaming chat — gathers context, retrieves docs, calls LLM."""
        tickers = tickers or []
        weights = weights or (tickers and [1.0 / len(tickers)] * len(tickers)) or []

        structured = self.gather_structured_context(
            tickers, weights, portfolio_value, start, end, horizon
        )

        retrieved_docs: list[dict] = []
        try:
            corpus = self._retriever.collect_all(tickers)
            retrieved_docs = self._retriever.retrieve(query, corpus, top_k=top_k)
        except Exception as exc:
            logger.warning("RAG retrieval failed: %s", exc)

        if not self.is_configured:
            reply = self._generate_template_fallback(query, structured, retrieved_docs)
            return {
                "role": "assistant",
                "content": reply,
                "llm_used": False,
                "context": _clean(structured),
                "retrieved_docs": _clean(retrieved_docs),
            }

        client = self._get_client()
        system_prompt = self._build_system_prompt()
        user_prompt = self._build_user_prompt(query, structured, retrieved_docs)

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        if self.provider == "gemini":
            reply, usage = self._generate_gemini(system_prompt, user_prompt)
        else:
            reply, usage = self._generate_openai(messages)

        return {
            "role": "assistant",
            "content": reply,
            "llm_used": True,
            "model": self.model,
            "provider": self.provider,
            "usage": {
                "prompt_tokens": getattr(usage, "prompt_tokens", None) if usage else None,
                "completion_tokens": getattr(usage, "completion_tokens", None) if usage else None,
                "total_tokens": getattr(usage, "total_tokens", None) if usage else None,
            },
            "context": _clean(structured),
            "retrieved_docs": _clean(retrieved_docs),
        }

    def _generate_openai(self, messages: list[dict]):
        """Call an OpenAI-compatible chat completions endpoint (non-streaming)."""
        client = self._get_client()
        response = client.chat.completions.create(
            model=self.model,
            messages=messages,
            max_tokens=self.max_tokens,
            temperature=0.3,
        )
        reply = response.choices[0].message.content or ""
        usage = getattr(response, "usage", None)
        return reply, usage

    def _generate_gemini(self, system_prompt: str, user_prompt: str):
        """Call the Google Gemini API (non-streaming)."""
        import google.generativeai as genai

        client = self._get_client()
        model = client.GenerativeModel(
            self.model,
            system_instruction=system_prompt,
            generation_config={
                "max_output_tokens": self.max_tokens,
                "temperature": 0.3,
            },
            safety_settings={
                "harassment": "BLOCK_NONE",
                "hate": "BLOCK_NONE",
                "sexual": "BLOCK_NONE",
                "dangerous": "BLOCK_NONE",
            },
        )
        response = model.generate_content(user_prompt)

        reply = ""
        if response.candidates:
            for candidate in response.candidates:
                if hasattr(candidate, "content") and candidate.content and candidate.content.parts:
                    for part in candidate.content.parts:
                        if hasattr(part, "text") and part.text:
                            reply += part.text
        if not reply:
            reply = getattr(response, "text", "") or ""

        usage = getattr(response, "usage_metadata", None)
        if usage:
            usage = type("Usage", (), {
                "prompt_tokens": getattr(usage, "prompt_token_count", 0),
                "completion_tokens": getattr(usage, "candidates_token_count", 0),
                "total_tokens": getattr(usage, "total_token_count", 0),
            })()

        return reply, usage

    def stream_chat(
        self,
        query: str,
        tickers: list[str] | None = None,
        weights: list[float] | None = None,
        portfolio_value: float = 100000,
        start: str = "2020-01-01",
        end: Optional[str] = None,
        horizon: int = 30,
        top_k: int = 5,
    ):
        """Streaming chat — yields SSE-formatted text chunks."""
        tickers = tickers or []
        weights = weights or (tickers and [1.0 / len(tickers)] * len(tickers)) or []

        structured = self.gather_structured_context(
            tickers, weights, portfolio_value, start, end, horizon
        )

        retrieved_docs: list[dict] = []
        try:
            corpus = self._retriever.collect_all(tickers)
            retrieved_docs = self._retriever.retrieve(query, corpus, top_k=top_k)
        except Exception as exc:
            logger.warning("RAG retrieval failed: %s", exc)

        if not self.is_configured:
            reply = self._generate_template_fallback(query, structured, retrieved_docs)
            yield f"data: {json.dumps({'content': reply, 'llm_used': False, 'done': True})}\n\n"
            return

        client = self._get_client()
        system_prompt = self._build_system_prompt()
        user_prompt = self._build_user_prompt(query, structured, retrieved_docs)

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        if self.provider == "gemini":
            yield from self._stream_gemini(system_prompt, user_prompt)
        else:
            yield from self._stream_openai(messages)

    def _stream_openai(self, messages: list[dict]):
        """Stream from an OpenAI-compatible endpoint."""
        client = self._get_client()
        stream = client.chat.completions.create(
            model=self.model,
            messages=messages,
            max_tokens=self.max_tokens,
            temperature=0.3,
            stream=True,
        )
        for chunk in stream:
            delta = chunk.choices[0].delta
            if delta.content:
                yield f"data: {json.dumps({'content': delta.content})}\n\n"
        yield f"data: {json.dumps({'llm_used': True, 'model': self.model, 'provider': 'openai', 'done': True})}\n\n"

    def _stream_gemini(self, system_prompt: str, user_prompt: str):
        """Stream from the Google Gemini API."""
        import google.generativeai as genai

        client = self._get_client()
        model = client.GenerativeModel(
            self.model,
            system_instruction=system_prompt,
            generation_config={
                "max_output_tokens": self.max_tokens,
                "temperature": 0.3,
            },
            safety_settings={
                "harassment": "BLOCK_NONE",
                "hate": "BLOCK_NONE",
                "sexual": "BLOCK_NONE",
                "dangerous": "BLOCK_NONE",
            },
        )
        response = model.generate_content(user_prompt, stream=True)
        for chunk in response:
            if chunk.text:
                yield f"data: {json.dumps({'content': chunk.text})}\n\n"
        yield f"data: {json.dumps({'llm_used': True, 'model': self.model, 'provider': 'gemini', 'done': True})}\n\n"

    def get_status(self) -> dict:
        """Return advisor configuration status."""
        return {
            "llm_configured": self.is_configured,
            "provider": self.provider,
            "base_url": self.base_url,
            "model": self.model,
            "knowledge_base_path": _KB_PATH,
            "rag_documents_available": len(FinancialKnowledgeBase.load()),
        }

    # ── Tool-calling interface (Phase 7) ─────────────────────────────

    TOOL_DEFINITIONS = [
        {
            "name": "get_portfolio",
            "description": "Get portfolio summary: value, portfolio score, asset allocation. Use when the user asks about their portfolio overview.",
            "parameters": {
                "type": "object",
                "properties": {
                    "tickers": {"type": "array", "items": {"type": "string"}, "description": "Portfolio tickers"},
                    "weights": {"type": "array", "items": {"type": "number"}, "description": "Portfolio weights (sum to 1.0)"},
                    "portfolio_value": {"type": "number", "description": "Total portfolio value in currency"},
                },
            },
        },
        {
            "name": "analyze_portfolio",
            "description": "Full portfolio analytics: risk metrics, portfolio score, allocation. Use when the user asks about portfolio performance or holdings analysis.",
            "parameters": {
                "type": "object",
                "properties": {
                    "tickers": {"type": "array", "items": {"type": "string"}},
                    "weights": {"type": "array", "items": {"type": "number"}},
                    "portfolio_value": {"type": "number"},
                    "start": {"type": "string", "description": "Start date YYYY-MM-DD"},
                },
            },
        },
        {
            "name": "analyze_risk",
            "description": "Risk metrics: VaR, CVaR, volatility, max drawdown, risk contribution, concentration, correlation matrix. Use when the user asks about portfolio risk.",
            "parameters": {
                "type": "object",
                "properties": {
                    "tickers": {"type": "array", "items": {"type": "string"}},
                    "weights": {"type": "array", "items": {"type": "number"}},
                    "portfolio_value": {"type": "number"},
                },
            },
        },
        {
            "name": "compare_benchmark",
            "description": "Compare portfolio vs benchmark: alpha, beta, Sharpe, Sortino, max drawdown, tracking error, information ratio. Use when the user asks about benchmark comparison.",
            "parameters": {
                "type": "object",
                "properties": {
                    "tickers": {"type": "array", "items": {"type": "string"}},
                    "weights": {"type": "array", "items": {"type": "number"}},
                    "portfolio_value": {"type": "number"},
                    "benchmark_ticker": {"type": "string", "description": "e.g. SPY, QQQ, ^NSEI"},
                },
            },
        },
        {
            "name": "analyze_attribution",
            "description": "Return attribution: security contribution, sector contribution, asset-class contribution with absolute/percentage values. Use when the user asks about what is driving portfolio performance.",
            "parameters": {
                "type": "object",
                "properties": {
                    "tickers": {"type": "array", "items": {"type": "string"}},
                    "weights": {"type": "array", "items": {"type": "number"}},
                    "portfolio_value": {"type": "number"},
                },
            },
        },
        {
            "name": "analyze_risk_budget",
            "description": "Risk contribution analysis: marginal contribution to risk (MCR), component contribution (CCR), percentage contribution (PCR). Use when the user asks about risk contribution or which assets contribute most to risk.",
            "parameters": {
                "type": "object",
                "properties": {
                    "tickers": {"type": "array", "items": {"type": "string"}},
                    "weights": {"type": "array", "items": {"type": "number"}},
                    "portfolio_value": {"type": "number"},
                },
            },
        },
        {
            "name": "optimize_portfolio",
            "description": "Get PPO RL optimization suggestions (experimental). Returns recommended weight allocations. Use when the user asks about portfolio optimization - always mention PPO is experimental.",
            "parameters": {
                "type": "object",
                "properties": {
                    "tickers": {"type": "array", "items": {"type": "string"}},
                    "weights": {"type": "array", "items": {"type": "number"}},
                    "portfolio_value": {"type": "number"},
                },
            },
        },
        {
            "name": "run_stress_test",
            "description": "Run stress tests: 2008 Financial Crisis, COVID Crash, Tech Sector Crash, Rate Hike Shock. Returns portfolio loss under each scenario. Use when the user asks about stress testing or worst-case scenarios.",
            "parameters": {
                "type": "object",
                "properties": {
                    "tickers": {"type": "array", "items": {"type": "string"}},
                    "weights": {"type": "array", "items": {"type": "number"}},
                    "portfolio_value": {"type": "number"},
                },
            },
        },
        {
            "name": "analyze_goal",
            "description": "Goal-based analysis: Monte Carlo simulation, probability of success, required return, required monthly contribution. Use when the user asks about financial goals or retirement planning.",
            "parameters": {
                "type": "object",
                "properties": {
                    "tickers": {"type": "array", "items": {"type": "string"}},
                    "weights": {"type": "array", "items": {"type": "number"}},
                    "current_capital": {"type": "number"},
                    "monthly_contribution": {"type": "number"},
                    "target_amount": {"type": "number"},
                    "time_horizon_years": {"type": "number"},
                    "portfolio_value": {"type": "number"},
                },
            },
        },
        {
            "name": "forecast_asset",
            "description": "ML price forecast for a specific ticker using TimesFM + LSTM. Use when the user asks about price forecasts or predictions for a single asset.",
            "parameters": {
                "type": "object",
                "properties": {
                    "ticker": {"type": "string", "description": "e.g. AAPL"},
                    "horizon": {"type": "integer", "description": "Forecast days"},
                },
            },
        },
        {
            "name": "get_market_regime",
            "description": "Current market regime via HMM: Bullish, Bearish, or High/Low Volatility. Use when the user asks about market conditions.",
            "parameters": {
                "type": "object",
                "properties": {
                    "tickers": {"type": "array", "items": {"type": "string"}},
                },
            },
        },
    ]

    def _execute_tool(self, tool_name: str, params: dict) -> dict:
        """Execute a financial tool and return structured result."""
        from services.portfolio_pipeline import run_portfolio_pipeline
        if tool_name == "get_portfolio":
            result = run_portfolio_pipeline(
                params.get("tickers", []), params.get("weights", []),
                params.get("portfolio_value", 100000)
            )
            return {
                "portfolio_value": result["portfolio_value"],
                "currency": result["currency"],
                "tickers": result["tickers"],
                "portfolio_score": result.get("portfolio_score", {}),
                "asset_allocation": result.get("asset_allocation", []),
            }
        elif tool_name == "analyze_portfolio":
            result = run_portfolio_pipeline(
                params.get("tickers", []), params.get("weights", []),
                params.get("portfolio_value", 100000),
                params.get("start", "2020-01-01")
            )
            return {
                "risk_summary": result.get("risk_engine", {}),
                "portfolio_score": result.get("portfolio_score", {}),
                "asset_allocation": result.get("asset_allocation", []),
            }
        elif tool_name == "analyze_risk":
            result = run_portfolio_pipeline(
                params.get("tickers", []), params.get("weights", []),
                params.get("portfolio_value", 100000)
            )
            return {
                "risk_summary": result.get("risk_engine", {}),
                "risk_budget": result.get("risk_budget", {}),
                "correlation": result.get("correlation", {}),
                "stress_test": result.get("stress_test", {}),
            }
        elif tool_name == "compare_benchmark":
            result = run_portfolio_pipeline(
                params.get("tickers", []), params.get("weights", []),
                params.get("portfolio_value", 100000),
                benchmark=params.get("benchmark_ticker", "SPY")
            )
            return result.get("benchmark", {})
        elif tool_name == "analyze_attribution":
            result = run_portfolio_pipeline(
                params.get("tickers", []), params.get("weights", []),
                params.get("portfolio_value", 100000)
            )
            return result.get("attribution", {})
        elif tool_name == "analyze_risk_budget":
            result = run_portfolio_pipeline(
                params.get("tickers", []), params.get("weights", []),
                params.get("portfolio_value", 100000)
            )
            return result.get("risk_budget", {})
        elif tool_name == "optimize_portfolio":
            result = run_portfolio_pipeline(
                params.get("tickers", []), params.get("weights", []),
                params.get("portfolio_value", 100000)
            )
            return {
                "status": "experimental" if result.get("ml_models", {}).get("rl_ready", False) else "not_ready",
                "rl_allocation": result.get("ml_models", {}).get("rl_allocation", {}),
                "warning": "PPO is an experimental model. Do not use for production decisions.",
            }
        elif tool_name == "run_stress_test":
            result = run_portfolio_pipeline(
                params.get("tickers", []), params.get("weights", []),
                params.get("portfolio_value", 100000)
            )
            return result.get("stress_test", {})
        elif tool_name == "analyze_goal":
            from services.goal_analyzer import compute_goal_analysis
            from services.data_fetcher import get_portfolio_data
            end = datetime.datetime.now().strftime('%Y-%m-%d')
            data = get_portfolio_data(params.get("tickers", []), "2020-01-01", end)
            return compute_goal_analysis(
                tickers=params.get("tickers", []),
                weights=params.get("weights", []),
                current_capital=params.get("current_capital", 0),
                monthly_contribution=params.get("monthly_contribution", 0),
                target_amount=params.get("target_amount", 0),
                time_horizon_years=params.get("time_horizon_years", 0),
                returns=data["returns"],
                num_sims=500,
            )
        elif tool_name == "forecast_asset":
            from services.forecaster import get_lstm_forecast
            from services.data_fetcher import get_portfolio_data
            ticker = params.get("ticker", "")
            horizon = params.get("horizon", 30)
            end = datetime.datetime.now().strftime('%Y-%m-%d')
            data = get_portfolio_data([ticker], "2020-01-01", end)
            prices = data["prices"]
            if isinstance(prices, pd.DataFrame):
                prices = prices.iloc[:, 0] if len(prices.columns) == 1 else prices.get(ticker.upper())
            forecast = get_lstm_forecast(prices.dropna(), horizon, train_epochs=8)
            return {
                "ticker": ticker,
                "spot_price": float(prices.iloc[-1]),
                "forecast": forecast[:5],
                "horizon": horizon,
            }
        elif tool_name == "get_market_regime":
            result = run_portfolio_pipeline(
                params.get("tickers", []), params.get("weights", [])
            )
            return result.get("market_regime", {})
        else:
            raise ValueError(f"Unknown tool: {tool_name}")

    def chat_with_tools(self, query: str, tickers: list[str] | None = None,
                         weights: list[float] | None = None,
                         portfolio_value: float = 100000) -> dict:
        """
        Agentic chat flow: LLM -> Tool -> LLM response.

        The LLM receives the user query and available tools. When it calls a
        tool, we execute it and feed the result back. The LLM then generates
        a final response citing the tool output.

        If no LLM is configured, falls back to structured pipeline output.
        """
        tickers = tickers or []
        weights = weights or (tickers and [1.0 / len(tickers)] * len(tickers)) or []

        if not self.is_configured:
            # Fallback: run the full pipeline and format results
            try:
                from services.portfolio_pipeline import run_portfolio_pipeline
                result = run_portfolio_pipeline(tickers, weights, portfolio_value)
                summary = self._format_context_block(_clean(result), [])
                return {
                    "role": "assistant",
                    "content": "LLM is not configured. Structured analysis:\n\n" + summary,
                    "llm_used": False,
                    "tool_calls": [{"tool": "run_portfolio_pipeline", "result_truncated": True}],
                    "context": _clean(result),
                }
            except Exception as exc:
                return {
                    "role": "assistant",
                    "content": f"Analysis error: {str(exc)}",
                    "llm_used": False,
                }

        client = self._get_client()
        try:
            messages = [
                {"role": "system", "content": self._build_system_prompt_with_tools()},
                {"role": "user", "content": self._build_tool_user_prompt(query, tickers, weights, portfolio_value)},
            ]

            tool_calls_output = []
            max_iterations = 3
            response = {"tool_calls": [], "content": ""}
            for _ in range(max_iterations):
                if self.provider == "gemini":
                    response = self._gemini_chat_with_tools(messages)
                else:
                    response = self._openai_chat_with_tools(messages)

                tool_calls = response.get("tool_calls", [])
                if not tool_calls:
                    break

                for tool_call in tool_calls:
                    tool_name = tool_call["name"]
                    params = tool_call["params"]
                    try:
                        tool_result = self._execute_tool(tool_name, params)
                        tool_calls_output.append({
                            "tool": tool_name,
                            "params": params,
                            "result": _clean(tool_result),
                        })
                        messages.append({
                            "role": "assistant",
                            "tool_calls": [{"name": tool_name, "arguments": json.dumps(params)}],
                        })
                        messages.append({
                            "role": "tool",
                            "name": tool_name,
                            "content": json.dumps(_clean(tool_result)),
                        })
                    except Exception as exc:
                        tool_calls_output.append({
                            "tool": tool_name,
                            "params": params,
                            "error": str(exc),
                        })
                        messages.append({
                            "role": "tool",
                            "name": tool_name,
                            "content": json.dumps({"error": str(exc)}),
                        })

            final_reply = response.get("content", "")
            if not final_reply:
                try:
                    formatted = self._format_context_block(
                        _clean(tool_calls_output[0]["result"] if tool_calls_output else {}),
                        []
                    )
                except Exception:
                    formatted = json.dumps(
                        _clean({"tool_calls": tool_calls_output[:3]}), indent=2, default=str
                    )[:2000]
                if self.provider == "gemini":
                    _, final_reply = self._generate_gemini(
                        self._build_system_prompt_with_tools(),
                        self._build_tool_user_prompt(query, tickers, weights, portfolio_value)
                        + "\n\nTool results (summarised):\n" + formatted[:3000]
                        + "\n\nNow respond to the user's original question using the tool results above."
                    )
                else:
                    messages.append({"role": "user", "content": "Now generate a final response for the user based on the tool results."})
                    final_reply, _ = self._generate_openai(messages)

            return {
                "role": "assistant",
                "content": final_reply,
                "llm_used": True,
                "model": self.model,
                "provider": self.provider,
                "tool_calls": tool_calls_output,
            }
        except Exception as llme:
            logger.warning("Tool-calling flow failed, falling back to pipeline: %s", llme)
            from services.portfolio_pipeline import run_portfolio_pipeline
            try:
                result = run_portfolio_pipeline(tickers, weights, portfolio_value)
                summary = self._format_context_block(_clean(result), [])
                return {
                    "role": "assistant",
                    "content": f"Tool-calling not available with current provider. "
                               f"Here is the structured analysis:\n\n{summary}",
                    "llm_used": False,
                    "tool_calls": [],
                    "context": _clean(result),
                }
            except Exception as exc2:
                return {
                    "role": "assistant",
                    "content": f"Analysis error: {str(exc2)}",
                    "llm_used": False,
                }
        """System prompt for the tool-calling agentic flow."""
        import textwrap
        tools_str = "\n".join(
            f"- {t['name']}: {t['description']}"
            for t in self.TOOL_DEFINITIONS
        )
        return textwrap.dedent(f"""\
            You are *AI Wealth Advisor*, a portfolio-intelligence assistant.

            You have access to the following financial analysis tools:

            {tools_str}

            Guidelines:
            - Call tools when the user's question requires quantitative data.
            - NEVER fabricate metrics — always use tool results as the source of truth.
            - Each tool result is structured data; do not re-calculate.
            - If a tool fails, tell the user clearly and offer alternatives.
            - After receiving tool results, generate a conversational response
              that cites specific numbers from the tool output.
            - PPO optimization is experimental — always warn the user.
            - Keep responses concise: 2-3 short paragraphs max.
            - Include: "This is quantitative analysis, not personalized investment advice."
        """)

    def _build_tool_user_prompt(self, query: str, tickers: list, weights: list, portfolio_value: float) -> str:
        import textwrap
        tickers_str = ", ".join(tickers) if tickers else "N/A"
        weights_str = ", ".join(str(w) for w in weights) if weights else "N/A"
        return textwrap.dedent(f"""\
            User question: {query}

            User's portfolio context:
            - Tickers: {tickers_str}
            - Weights: {weights_str}
            - Portfolio value: ${portfolio_value:,.0f}

            Answer the user's question using the available tools.
            Call any tool that would help answer the question.
            You can call multiple tools in parallel if needed.
        """)

    def _openai_chat_with_tools(self, messages: list[dict]) -> dict:
        """Call OpenAI-compatible endpoint with tool definitions."""
        tools = [
            {
                "type": "function",
                "function": {
                    "name": t["name"],
                    "description": t["description"],
                    "parameters": {
                        "type": "object",
                        "properties": t["parameters"]["properties"],
                    },
                },
            }
            for t in self.TOOL_DEFINITIONS
        ]
        client = self._get_client()
        response = client.chat.completions.create(
            model=self.model,
            messages=messages,
            tools=tools,
            tool_choice="auto",
            max_tokens=self.max_tokens,
            temperature=0.3,
        )
        choice = response.choices[0]
        tool_calls = []
        for tc in (choice.message.tool_calls or []):
            if tc.type == "function":
                params = json.loads(tc.function.arguments) if tc.function.arguments else {}
                tool_calls.append({"name": tc.function.name, "params": params})
        return {
            "tool_calls": tool_calls,
            "content": choice.message.content or "",
        }

    def _gemini_chat_with_tools(self, messages: list[dict]) -> dict:
        """Call Gemini with tool definitions.
        Gemini uses a different tool format than OpenAI — function_declarations list.
        """
        tools = [{
            "function_declarations": [{
                "name": t["name"],
                "description": t["description"],
                "parameters": {
                    "type": "object",
                    "properties": t["parameters"]["properties"],
                },
            }]
            for t in self.TOOL_DEFINITIONS
        }]
        client = self._get_client()
        model = client.GenerativeModel(
            self.model,
            system_instruction=self._build_system_prompt_with_tools(),
            generation_config={"max_output_tokens": self.max_tokens, "temperature": 0.3},
            tools=tools,
        )
        prompt = "\n".join(f"{m['role']}: {m['content']}" for m in messages if m.get("content"))
        response = model.generate_content(prompt)

        tool_calls = []
        text_parts = []
        for part in (response.candidates[0].content.parts if response.candidates else []):
            if hasattr(part, "function_call") and part.function_call:
                params = dict(part.function_call.args) if hasattr(part.function_call, "args") else {}
                tool_calls.append({
                    "name": part.function_call.name,
                    "params": params,
                })
            elif hasattr(part, "text") and part.text:
                text_parts.append(part.text)

        return {
            "tool_calls": tool_calls,
            "content": "".join(text_parts) if text_parts else "",
        }
