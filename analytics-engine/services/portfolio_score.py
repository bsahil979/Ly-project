import numpy as np
import pandas as pd


def get_currency_symbol(currency_map: dict) -> str:
    """Determine dominant currency symbol. Favors INR if present."""
    if "INR" in currency_map.values():
        return "\u20b9"
    counts = pd.Series(list(currency_map.values())).value_counts()
    dominant = counts.index[0] if not counts.empty else "USD"
    symbols = {"USD": "$", "INR": "\u20b9", "EUR": "\u20ac", "GBP": "\u00a3"}
    return symbols.get(dominant, "$")


RISK_TOLERANCE_THRESHOLDS = {
    'HIGH_RISK_THRESHOLD': 0.35,
    'MEDIUM_RISK_THRESHOLD': 0.20,
    'HIGH_DRAWDOWN_THRESHOLD': -0.30,
    'HIGH_VAR_THRESHOLD': -0.03,
}

ASSET_CATEGORIES = {
    'AAPL': 'Technology',
    'MSFT': 'Technology',
    'GOOGL': 'Communication',
    'AMZN': 'Consumer Cyclical',
    'NVDA': 'Technology',
    'GOOG': 'Communication',
    'JPM': 'Financial',
    'JNJ': 'Healthcare',
    'V': 'Financial',
    'WMT': 'Consumer Defensive',
    'SPY': 'ETF',
    'QQQ': 'ETF',
    'IWM': 'ETF',
    'DIA': 'ETF',
    'XLF': 'ETF',
    'EFA': 'ETF',
    'EEM': 'ETF',
    'VNQ': 'ETF',
    'BND': 'ETF',
    'HYG': 'ETF',
    'TLT': 'ETF',
    'GLD': 'ETF',
    'SLV': 'ETF',
    'USO': 'ETF',
    'UNG': 'ETF',
    'FXI': 'ETF',
    'EWJ': 'ETF',
    'INDA': 'ETF',
    'EWT': 'ETF',
    'RSX': 'ETF',
    'EWZ': 'ETF',
    'EPI': 'ETF',
}

INDIA_TICKERS = {
    'TCS.NS': 'Technology',
    'RELIANCE.NS': 'Energy',
    'HDFCBANK.NS': 'Financial',
    'INFY.NS': 'Technology',
    'ICICIBANK.NS': 'Financial',
    'SBIN.NS': 'Financial',
    'BHARTIARTL.NS': 'Communication',
    'AXISBANK.NS': 'Financial',
    'KOTAKBANK.NS': 'Financial',
    'LT.NS': 'Industrials',
    'HCLTECH.NS': 'Technology',
    'WIPRO.NS': 'Technology',
    'ITC.NS': 'Consumer Defensive',
    'BAJFINANCE.NS': 'Financial',
    'BAJAJ-AUTO.NS': 'Consumer Cyclical',
    'HINDUNILVR.NS': 'Consumer Defensive',
    'ASIANPAINT.NS': 'Basic Materials',
    'NESTEIND.NS': 'Consumer Defensive',
    'DRREDDY.NS': 'Healthcare',
    'SUNPHARMA.NS': 'Healthcare',
    'DIVIOLABS.NS': 'Healthcare',
    'APOLLOHOSP.NS': 'Healthcare',
    'POWERGRID.NS': 'Utilities',
    'SBILIFE.NS': 'Financial',
    'HDFCLIFE.NS': 'Financial',
    'SHRIRAMFIN.NS': 'Financial',
    'TRENT.NS': 'Consumer Cyclical',
    'ADANIGREEN.NS': 'Energy',
    'ADANIPORTS.NS': 'Industrials',
    'TATAMOTORS.NS': 'Consumer Cyclical',
    'WIPRO.NS': 'Technology',
    'LTIM.NS': 'Technology',
    'HINDALIBAR.NS': 'Consumer Defensive',
    'MOTHERSLJS.NS': 'Financial',
    'PERSISTENT.NS': 'Technology',
    'COPPER.NS': 'Basic Materials',
    'NMDC.NS': 'Basic Materials',
    'COALINDIA.NS': 'Energy',
    'IOC.NS': 'Energy',
    'RIL.NS': 'Energy',
}


def get_asset_category(ticker: str) -> str:
    t = ticker.upper().strip()
    if t in ASSET_CATEGORIES:
        return ASSET_CATEGORIES[t]
    if t in INDIA_TICKERS:
        return INDIA_TICKERS[t]
    return 'Other'


def compute_portfolio_score(
    tickers: list,
    weights: list,
    risk_summary: pd.DataFrame,
    returns: pd.DataFrame,
    portfolio_value: float = 100000,
) -> dict:
    if not tickers or not weights or risk_summary is None:
        return {
            'score': 0,
            'max_score': 1000,
            'grading': 'N/A',
            'components': {},
            'risks_identified': [],
        }

    vol_data = risk_summary['Volatility (Annual)'] if 'Volatility (Annual)' in risk_summary else pd.Series(dtype=float)
    var_data = risk_summary['VaR (95%)'] if 'VaR (95%)' in risk_summary else pd.Series(dtype=float)
    drawdown_data = risk_summary['Max Drawdown'] if 'Max Drawdown' in risk_summary else pd.Series(dtype=float)

    avg_volatility = float(np.mean(list(vol_data.values))) if len(vol_data) > 0 else 0
    avg_var = float(np.mean(list(var_data.values))) if len(var_data) > 0 else 0
    avg_drawdown = float(np.mean(list(drawdown_data.values))) if len(drawdown_data) > 0 else 0

    avg_return = float(returns.mean().mean() * 252) if returns is not None and not returns.empty else 0

    components = {}

    # 1. Downside Protection (max 400 points)
    # Lower drawdown and VaR = higher score
    drawdown_abs = abs(avg_drawdown)
    var_abs = abs(avg_var)
    downside_score = min(400, max(0, 400 * (1 - drawdown_abs / 0.5) * (1 - var_abs / 0.1)))
    components['downside_protection'] = {
        'score': round(downside_score, 1),
        'max': 400,
        'label': 'Downside Protection',
        'detail': f'Avg Max Drawdown: {avg_drawdown*100:.1f}%, Avg VaR(95%): {avg_var*100:.2f}%',
    }

    # 2. Risk-Adjusted Return (max 300 points)
    # Sharpe ratio proxy: return / volatility
    if avg_volatility > 0:
        sharpe = avg_return / avg_volatility
    else:
        sharpe = 0
    sharpe_score = min(300, max(0, 150 + sharpe * 50))
    components['risk_adjusted_return'] = {
        'score': round(sharpe_score, 1),
        'max': 300,
        'label': 'Risk-Adjusted Return',
        'detail': f'Proxy Sharpe: {sharpe:.2f} (annual return: {avg_return*100:.1f}%, vol: {avg_volatility*100:.1f}%)',
    }

    # 3. Allocation Quality (max 200 points)
    # Fewer concentrated positions = higher score
    max_weight = max(weights) if weights else 1.0
    unique_holdings = len(tickers)
    concentration_penalty = 0
    if max_weight > 0.5:
        concentration_penalty = (max_weight - 0.5) * 200
    elif max_weight > 0.3:
        concentration_penalty = (max_weight - 0.3) * 50
    diversification_bonus = min(100, unique_holdings * 10)
    allocation_score = min(200, max(0, 200 - concentration_penalty + diversification_bonus - 100))
    # Simpler: more tickers + less concentration = higher score
    allocation_score = min(200, unique_holdings * 25 + (1 - max_weight) * 50)
    components['allocation_quality'] = {
        'score': round(allocation_score, 1),
        'max': 200,
        'label': 'Allocation Quality',
        'detail': f'{unique_holdings} holdings, max position: {max_weight*100:.0f}%',
    }

    # 4. Stress Resilience (max 100 points)
    # Based on how well the portfolio handles stress scenarios
    # Lower average drawdown and VaR → better stress resilience
    stress_score = min(100, max(0, 100 * (1 - drawdown_abs / 0.5)))
    components['stress_resilience'] = {
        'score': round(stress_score, 1),
        'max': 100,
        'label': 'Stress Resilience',
        'detail': 'Based on historical drawdown & VaR',
    }

    total_score = round(
        components['downside_protection']['score']
        + components['risk_adjusted_return']['score']
        + components['allocation_quality']['score']
        + components['stress_resilience']['score']
    )

    # Grading
    pct = total_score / 1000
    if pct >= 0.9:
        grade = 'A+'
    elif pct >= 0.8:
        grade = 'A'
    elif pct >= 0.7:
        grade = 'B'
    elif pct >= 0.6:
        grade = 'C'
    elif pct >= 0.5:
        grade = 'D'
    else:
        grade = 'F'

    # Risk identification
    risks = identify_portfolio_risks(tickers, weights, avg_volatility, avg_drawdown)

    return {
        'score': total_score,
        'max_score': 1000,
        'grade': grade,
        'grading': grade,
        'pct': round(pct * 100, 1),
        'components': components,
        'risks_identified': risks,
    }


def identify_portfolio_risks(
    tickers: list,
    weights: list,
    avg_volatility: float,
    avg_drawdown: float,
) -> list:
    risks = []

    # Concentration risk
    max_weight = max(weights) if weights else 0
    if max_weight > 0.5:
        risks.append({
            'type': 'concentration',
            'severity': 'high',
            'label': 'Concentration Risk',
            'description': f"Single position represents {max_weight*100:.0f}% of portfolio. A single stock's decline heavily impacts total value.",
        })
    elif max_weight > 0.3:
        risks.append({
            'type': 'concentration',
            'severity': 'medium',
            'label': 'Moderate Concentration Risk',
            'description': f'Largest position is {max_weight*100:.0f}% of portfolio.',
        })

    # Sector concentration
    sector_weights = {}
    for t, w in zip(tickers, weights):
        cat = get_asset_category(t)
        sector_weights[cat] = sector_weights.get(cat, 0) + w

    dominant_sector = max(sector_weights, key=sector_weights.get) if sector_weights else 'Unknown'
    dominant_pct = sector_weights.get(dominant_sector, 0)
    if dominant_pct > 0.5:
        risks.append({
            'type': 'sector',
            'severity': 'high',
            'label': f'{dominant_sector} Sector Concentration',
            'description': f'{dominant_pct*100:.0f}% of portfolio in {dominant_sector} stocks. Sector-specific shocks could significantly impact value.',
        })
    elif dominant_pct > 0.35:
        risks.append({
            'type': 'sector',
            'severity': 'medium',
            'label': f'Moderate {dominant_sector} Exposure',
            'description': f'{dominant_pct*100:.0f}% in {dominant_sector} sector.',
        })

    # Volatility risk
    if avg_volatility > RISK_TOLERANCE_THRESHOLDS['HIGH_RISK_THRESHOLD']:
        risks.append({
            'type': 'volatility',
            'severity': 'high',
            'label': 'High Volatility Risk',
            'description': f'Portfolio volatility ({avg_volatility*100:.1f}%) exceeds typical risk thresholds. Expect significant price swings.',
        })
    elif avg_volatility > RISK_TOLERANCE_THRESHOLDS['MEDIUM_RISK_THRESHOLD']:
        risks.append({
            'type': 'volatility',
            'severity': 'medium',
            'label': 'Elevated Volatility',
            'description': f'Portfolio volatility: {avg_volatility*100:.1f}% annualized.',
        })

    # Drawdown risk
    if abs(avg_drawdown) > 0.30:
        risks.append({
            'type': 'drawdown',
            'severity': 'high',
            'label': 'Severe Drawdown Risk',
            'description': f'Historical max drawdown of {avg_drawdown*100:.1f}% indicates significant downside potential.',
        })
    elif abs(avg_drawdown) > 0.20:
        risks.append({
            'type': 'drawdown',
            'severity': 'medium',
            'label': 'Moderate Drawdown Risk',
            'description': f'Historical max drawdown: {avg_drawdown*100:.1f}%.',
        })

    # Inflation risk (all stocks = no inflation hedge)
    has_inflation_hedge = any(
        t.upper() in ('GLD', 'TLT', 'VNQ', 'SLV', 'PDBC', 'VAW', 'GSG')
        or t.upper().endswith(('G', 'S', '.NS'))
        for t in tickers
    )
    if not has_inflation_hedge:
        risks.append({
            'type': 'inflation',
            'severity': 'medium',
            'label': 'Inflation Risk',
            'description': 'No dedicated inflation-hedging assets (e.g., TIPS, commodities, real estate) in portfolio.',
        })

    # Geography risk (US-only stocks)
    all_us = all(not t.upper().endswith(('.NS', '.BO', '.L', '.T')) for t in tickers)
    if all_us and len(tickers) > 1:
        risks.append({
            'type': 'geography',
            'severity': 'low',
            'label': 'Geography Risk',
            'description': 'Portfolio is concentrated in US markets. Consider international diversification.',
        })

    # Credit risk (high-yield concentration)
    credit_weights = 0
    for t in tickers:
        t_upper = t.upper()
        if t_upper in ('JNK', 'HYG', 'IJR', 'IWM') or t_upper.endswith('.NS') and 'FINANCE' in t_upper:
            credit_weights += 0.1
    if credit_weights > 0.3:
        risks.append({
            'type': 'credit',
            'severity': 'medium',
            'label': 'Credit Risk',
            'description': 'Significant exposure to credit-sensitive instruments may suffer during rate hikes.',
        })

    return risks


def compute_asset_allocation(tickers: list, weights: list) -> list:
    allocations = []
    for t, w in zip(tickers, weights):
        cat = get_asset_category(t)
        allocations.append({
            'ticker': t.upper(),
            'weight': round(w * 100, 1),
            'category': cat,
            'value': None,
        })
    return allocations
