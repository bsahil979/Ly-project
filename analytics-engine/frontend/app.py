import streamlit as st
import requests

st.set_page_config(
    page_title="Smart Portfolio Advisor",
    page_icon="📈",
    layout="wide"
)

st.title("📈 Smart Portfolio Advisor")
st.markdown("*Your AI-powered investment decision co-pilot*")
st.markdown("---")

# ─────────────────────────────────────────
# SIDEBAR — Portfolio Input
# ─────────────────────────────────────────
st.sidebar.header("📊 Portfolio Input")

tickers = st.sidebar.text_input(
    "Tickers (comma separated)",
    "AAPL,MSFT,GOOGL"
)
weights = st.sidebar.text_input(
    "Weights (comma separated, must sum to 1)",
    "0.4,0.3,0.3"
)
portfolio_value = st.sidebar.number_input(
    "Portfolio Value ($)",
    value=100000,
    step=1000
)
start = st.sidebar.text_input("Start Date", "2020-01-01")
end   = st.sidebar.text_input("End Date",   "2024-01-01")

analyze = st.sidebar.button("🔍 Analyze Portfolio")

# ─────────────────────────────────────────
# MAIN — Results
# ─────────────────────────────────────────
if analyze:

    try:
        tickers_list = [t.strip().upper() for t in tickers.split(",")]
        weights_list = [float(w.strip()) for w in weights.split(",")]
        if len(tickers_list) != len(weights_list):
            st.error("❌ Number of tickers and weights must match.")
        elif abs(sum(weights_list) - 1.0) > 0.01:
            st.error(f"❌ Weights must sum to 1.0 — current sum: {sum(weights_list)}")
        else:
            payload = {
                "tickers":         tickers_list,
                "weights":         weights_list,
                "portfolio_value": portfolio_value,
                "start":           start,
                "end":             end
            }
            with st.spinner("⏳ Analyzing your portfolio... this may take 15-20 seconds"):
                try:
                    response = requests.post(
                        "http://127.0.0.1:8000/analyze",
                        json=payload,
                        timeout=120
                    )

                    if response.status_code == 200:
                        data = response.json()

                        # ── RISK SUMMARY ──
                        st.markdown("## 📊 Risk Summary")
                        st.dataframe(data["risk_summary"], use_container_width=True)

                        col1, col2, col3 = st.columns(3)
                        risk_df = data["risk_summary"]
                        tickers_in = list(risk_df.get("Volatility (Annual)", {}).keys())
                        if tickers_in:
                            first = tickers_in[0]
                            col1.metric("Avg Volatility",  f"{round(sum(risk_df['Volatility (Annual)'].values()) / len(tickers_in) * 100, 1)}%")
                            col2.metric("Avg VaR (95%)",   f"{round(sum(risk_df['VaR (95%)'].values()) / len(tickers_in) * 100, 2)}%")
                            col3.metric("Avg Max Drawdown", f"{round(sum(risk_df['Max Drawdown'].values()) / len(tickers_in) * 100, 1)}%")

                        st.markdown("---")

                        # ── MARKET REGIME ──
                        st.markdown("## 🧠 Market Regime Detection")
                        st.dataframe(data["regime_summary"], use_container_width=True)
                        st.markdown("---")

                        # ── STRESS TEST ──
                        st.markdown("## 💥 Stress Test Results")
                        st.dataframe(data["stress_test"], use_container_width=True)
                        st.markdown("---")

                        # ── DECISION OPTIONS ──
                        st.markdown("## 💡 Decision Options")
                        st.markdown("*Choose the strategy that matches your risk appetite:*")

                        cols = st.columns(3)
                        for i, option in enumerate(data["decision_options"]):
                            with cols[i]:
                                st.markdown(f"### {option['emoji']} {option['option']}")
                                st.markdown(f"*{option['description']}*")
                                st.markdown("**📊 Allocations:**")
                                for asset, alloc in option["allocations"].items():
                                    st.write(f"• {asset}: {alloc}")
                                st.success(f"📈 Expected Return: {option['expected_return']}")
                                st.error(f"📉 Downside Risk: {option['downside_risk']}")
                                st.markdown("**🧠 Reasoning:**")
                                for reason in option["reasoning"]:
                                    st.write(f"• {reason}")
                                st.info(f"👤 Best For: {option['best_for']}")

                    else:
                        st.error(f"❌ API Error: {response.status_code} - {response.text}")

                except requests.exceptions.ConnectionError:
                    st.error("❌ Cannot connect to FastAPI backend.")
                    st.info("💡 Make sure FastAPI is running in another terminal: `uvicorn api:app --reload`")

                except requests.exceptions.Timeout:
                    st.error("❌ Request to backend API timed out. Try again later.")

                except Exception as e:
                    st.error(f"❌ Unexpected error: {str(e)}")

    except ValueError:
        st.error("❌ Please enter valid numbers for weights.")
    except Exception as e:
        st.error(f"❌ Unexpected error: {str(e)}")

else:
    # ── WELCOME SCREEN ──
    st.markdown("## 👋 Welcome to Smart Portfolio Advisor")
    col1, col2, col3 = st.columns(3)
    col1.info("📊 **Risk Analysis**\n\nVolatility, VaR, CVaR, Max Drawdown")
    col2.info("🧠 **Market Regimes**\n\nBull, Bear, Volatile detection")
    col3.info("💡 **Smart Decisions**\n\nConservative, Balanced, Aggressive options")
    st.markdown("---")
    st.markdown("👈 **Enter your portfolio details in the sidebar and click Analyze Portfolio**")