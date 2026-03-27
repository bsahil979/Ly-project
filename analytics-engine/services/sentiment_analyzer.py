import yfinance as yf
from gnews import GNews
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import datetime

analyzer = SentimentIntensityAnalyzer()

# ── Yahoo Finance News ──────────────────────────────────
def _fetch_yahoo_news(ticker: str) -> list:
    """Fetch news from Yahoo Finance via yfinance."""
    try:
        stock = yf.Ticker(ticker)
        raw = stock.news or []
    except Exception:
        return []

    articles = []
    for item in raw[:10]:
        content = item.get("content", item)
        title = content.get("title", "") or ""
        if not title:
            continue

        provider = content.get("provider", {})
        publisher = provider.get("displayName", "Unknown") if isinstance(provider, dict) else str(provider or "Unknown")

        link = content.get("canonicalUrl", {})
        link = link.get("url", "#") if isinstance(link, dict) else (link or "#")

        pub_raw = content.get("pubDate", "")
        try:
            dt = datetime.datetime.fromisoformat(pub_raw.replace("Z", "+00:00"))
            pub_date = dt.strftime('%Y-%m-%d %H:%M')
        except:
            pub_date = str(pub_raw)[:16] if pub_raw else "Unknown"

        articles.append({
            "title": title,
            "publisher": publisher,
            "link": link,
            "published": pub_date,
            "source": "Yahoo Finance"
        })
    return articles


# ── Google News ─────────────────────────────────────────
def _fetch_google_news(ticker: str) -> list:
    """Fetch stock news from Google News."""
    try:
        gn = GNews(language="en", country="US", max_results=10, period="7d")
        raw = gn.get_news(f"{ticker} stock") or []
    except Exception:
        return []

    articles = []
    for item in raw[:10]:
        title = item.get("title", "") or ""
        if not title:
            continue

        publisher = item.get("publisher", {})
        if isinstance(publisher, dict):
            publisher = publisher.get("title", "Unknown")
        else:
            publisher = str(publisher or "Unknown")

        articles.append({
            "title": title,
            "publisher": publisher,
            "link": item.get("url", "#"),
            "published": item.get("published date", "Unknown"),
            "source": "Google News"
        })
    return articles


# ── Deduplication ───────────────────────────────────────
def _deduplicate(articles: list) -> list:
    """Remove duplicate headlines based on title similarity."""
    seen = set()
    unique = []
    for a in articles:
        # Use first 50 chars as a fingerprint
        key = a["title"][:50].lower().strip()
        if key not in seen:
            seen.add(key)
            unique.append(a)
    return unique


# ── Main Analysis ───────────────────────────────────────
def get_sentiment_analysis(ticker: str):
    """
    Multi-source sentiment analysis:
    1. Fetches news from Yahoo Finance + Google News
    2. Deduplicates headlines
    3. Runs VADER sentiment on each headline
    4. Returns aggregate sentiment profile
    """

    # Fetch from both sources
    yahoo_articles = _fetch_yahoo_news(ticker)
    google_articles = _fetch_google_news(ticker)

    all_articles = _deduplicate(yahoo_articles + google_articles)

    if not all_articles:
        return {
            "ticker": ticker,
            "overall_sentiment": "Neutral",
            "overall_score": 0.0,
            "confidence": 0.5,
            "articles_analyzed": 0,
            "sources_used": [],
            "articles": [],
            "sentiment_breakdown": {"positive": 0, "negative": 0, "neutral": 0}
        }

    analyzed = []
    total_compound = 0.0
    pos_count = neg_count = neu_count = 0

    for a in all_articles:
        scores = analyzer.polarity_scores(a["title"])
        compound = scores["compound"]
        total_compound += compound

        if compound >= 0.05:
            label = "Positive"
            pos_count += 1
        elif compound <= -0.05:
            label = "Negative"
            neg_count += 1
        else:
            label = "Neutral"
            neu_count += 1

        analyzed.append({
            **a,
            "sentiment": label,
            "score": round(compound, 3),
            "scores": {
                "positive": round(scores["pos"], 3),
                "negative": round(scores["neg"], 3),
                "neutral": round(scores["neu"], 3),
            }
        })

    n = len(analyzed)
    avg = total_compound / n if n > 0 else 0

    if avg >= 0.15:
        overall = "Bullish"
    elif avg >= 0.05:
        overall = "Slightly Bullish"
    elif avg <= -0.15:
        overall = "Bearish"
    elif avg <= -0.05:
        overall = "Slightly Bearish"
    else:
        overall = "Neutral"

    confidence = min(abs(avg) * 5, 1.0)

    # Which sources contributed
    sources_used = list(set(a["source"] for a in analyzed))

    return {
        "ticker": ticker,
        "overall_sentiment": overall,
        "overall_score": round(avg, 4),
        "confidence": round(confidence, 2),
        "articles_analyzed": n,
        "sources_used": sources_used,
        "articles": analyzed,
        "sentiment_breakdown": {
            "positive": pos_count,
            "negative": neg_count,
            "neutral": neu_count
        }
    }
