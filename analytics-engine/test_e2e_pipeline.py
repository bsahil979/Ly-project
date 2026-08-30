"""
End-to-end test for the Portfolio Intelligence Integration Pipeline.

Tests the complete flow:
  User Portfolio -> Market Data -> Portfolio Analytics -> ML Models ->
  Risk Engine -> Stress Engine -> Benchmark -> Attribution -> Risk Budget ->
  Recommendation Engine -> LLM Advisor

Run:
    python test_e2e_pipeline.py
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

import requests
import json
import numpy as np

BASE = "http://127.0.0.1:8000"
TICKERS = ["AAPL", "MSFT"]
WEIGHTS = [0.5, 0.5]
PORTFOLIO_VALUE = 100000.0
START = "2023-01-01"


class TestResult:
    def __init__(self, name):
        self.name = name
        self.passed = 0
        self.failed = 0
        self.errors = []

    def check(self, label, condition, detail=""):
        if condition:
            self.passed += 1
        else:
            self.failed += 1
            self.errors.append(f"FAIL: {label} — {detail}")

    def summary(self):
        status = "PASS" if self.failed == 0 else "FAIL"
        print(f"\n{'='*60}")
        print(f"  {self.name}: {self.passed} passed, {self.failed} failed [{status}]")
        if self.errors:
            for e in self.errors:
                print(f"  {e}")
        print(f"{'='*60}")
        return self.failed == 0


def main():
    results = TestResult("E2E Pipeline Test")

    # ── Phase 2: Benchmark ──────────────────────────────────────────
    print("\n[Phase 2] Benchmark Engine...")
    try:
        r = requests.post(f"{BASE}/portfolio/benchmark", json={
            "tickers": TICKERS, "weights": WEIGHTS,
            "portfolio_value": PORTFOLIO_VALUE, "start": START,
            "benchmark_ticker": "SPY"
        }, timeout=60)
        data = r.json()
        results.check("benchmark_status", r.status_code == 200, f"status={r.status_code}")
        results.check("benchmark_has_alpha", "alpha" in str(data.get("comparison", {})),
                       f"comparison={data.get('comparison', {})}")
        results.check("benchmark_has_beta", "beta" in str(data.get("comparison", {})), "")
        results.check("benchmark_has_ir", "information_ratio" in str(data.get("comparison", {})), "")
    except Exception as e:
        results.check("benchmark_endpoint", False, str(e))

    # ── Phase 3: Attribution ─────────────────────────────────────────
    print("\n[Phase 3] Attribution Engine...")
    try:
        r = requests.post(f"{BASE}/portfolio/attribution", json={
            "tickers": TICKERS, "weights": WEIGHTS,
            "portfolio_value": PORTFOLIO_VALUE, "start": START
        }, timeout=60)
        data = r.json()
        results.check("attribution_status", r.status_code == 200, f"status={r.status_code}")
        results.check("attribution_has_security", len(data.get("security_contribution", [])) > 0, "")
        results.check("attribution_has_sector", len(data.get("sector_contribution", [])) > 0, "")
        results.check("attribution_has_asset_class", len(data.get("asset_class_contribution", [])) > 0, "")
        results.check("attribution_has_total_return", "portfolio_total_return" in data, "")
    except Exception as e:
        results.check("attribution_endpoint", False, str(e))

    # ── Phase 4: Risk Budgeting ──────────────────────────────────────
    print("\n[Phase 4] Risk Budgeting Engine...")
    try:
        r = requests.post(f"{BASE}/portfolio/risk-budget", json={
            "tickers": TICKERS, "weights": WEIGHTS,
            "portfolio_value": PORTFOLIO_VALUE, "start": START
        }, timeout=60)
        data = r.json()
        results.check("risk_budget_status", r.status_code == 200, f"status={r.status_code}")
        rb = data.get("risk_budget", {})
        results.check("risk_budget_has_vol", "portfolio_volatility" in rb, "")
        results.check("risk_budget_has_var", "var_95" in rb, "")
        results.check("risk_budget_has_cvar", "cvar_95" in rb, "")
        results.check("risk_budget_has_diversification", "diversification_ratio" in rb, "")
        results.check("risk_budget_has_contributions", len(rb.get("risk_contributions", [])) > 0, "")
        results.check("risk_budget_has_hhi", "herfindahl_index" in rb, "")
        results.check("risk_budget_has_correlation", "matrix" in data.get("correlation", {}), "")
    except Exception as e:
        results.check("risk_budget_endpoint", False, str(e))

    # ── Phase 5: Goal Analysis (Monte Carlo) ────────────────────────
    print("\n[Phase 5] Goal Engine (Monte Carlo)...")
    try:
        r = requests.post(f"{BASE}/portfolio/goal", json={
            "tickers": TICKERS, "weights": WEIGHTS,
            "current_capital": 100000,
            "monthly_contribution": 1000,
            "target_amount": 1000000,
            "time_horizon_years": 20,
            "num_sims": 200,
            "start": START
        }, timeout=120)
        data = r.json()
        results.check("goal_status", r.status_code == 200, f"status={r.status_code}")
        analysis = data.get("analysis", {})
        results.check("goal_has_success_rate", "probability_of_success_pct" in analysis, "")
        results.check("goal_has_required_return", "required_return_cagr" in analysis, "")
        results.check("goal_has_expected_return", "expected_annual_return" in analysis, "")
        results.check("goal_has_required_contribution", "required_monthly_contribution" in analysis, "")
        results.check("goal_has_distribution", "p10" in data.get("distribution", {}),
                       f"dist keys={list(data.get('distribution', {}).keys())[:5]}")
        results.check("goal_has_trajectory", "p50" in data.get("trajectory", {}), "")
    except Exception as e:
        results.check("goal_endpoint", False, str(e))

    # ── Phase 1: Unified Pipeline ────────────────────────────────────
    print("\n[Phase 1] Unified Portfolio Pipeline...")
    try:
        r = requests.post(f"{BASE}/portfolio/analyze", json={
            "tickers": TICKERS, "weights": WEIGHTS,
            "portfolio_value": PORTFOLIO_VALUE, "start": START,
            "benchmark": "SPY"
        }, timeout=180)
        data = r.json()
        results.check("analyze_status", r.status_code == 200, f"status={r.status_code}")
        required_keys = [
            "risk_engine", "market_regime", "stress_test", "benchmark",
            "attribution", "risk_budget", "ml_models", "portfolio_score",
            "asset_allocation", "recommendations",
        ]
        for key in required_keys:
            results.check(f"analyze_has_{key}", key in data, f"missing key: {key}")
    except Exception as e:
        results.check("analyze_endpoint", False, str(e))

    # ── Phase 6: Recommendations ────────────────────────────────────
    print("\n[Phase 6] Recommendation Engine...")
    try:
        r = requests.post(f"{BASE}/recommendations", json={
            "tickers": TICKERS, "weights": WEIGHTS,
            "portfolio_value": PORTFOLIO_VALUE, "start": START,
            "benchmark": "SPY"
        }, timeout=180)
        data = r.json()
        recs = data.get("recommendations", [])
        results.check("recommendations_status", r.status_code == 200, f"status={r.status_code}")
        results.check("recommendations_nonempty", len(recs) > 0, f"got {len(recs)} recs")
        if recs:
            rec = recs[0]
            required_fields = ["action", "asset", "reason", "supporting_metrics",
                               "supporting_models", "expected_impact", "confidence", "timestamp"]
            for field in required_fields:
                results.check(f"recommendation_has_{field}", field in rec, f"missing: {field}")
    except Exception as e:
        results.check("recommendations_endpoint", False, str(e))

    # ── Phase 7: LLM Tool Integration ────────────────────────────────
    print("\n[Phase 7] LLM Tool Integration...")
    try:
        r = requests.get(f"{BASE}/tools", timeout=10)
        data = r.json()
        results.check("tools_list_status", r.status_code == 200, f"status={r.status_code}")
        tool_names = [t["name"] for t in data.get("tools", [])]
        expected_tools = ["get_portfolio", "analyze_risk", "compare_benchmark",
                          "analyze_attribution", "analyze_risk_budget", "optimize_portfolio",
                          "run_stress_test", "analyze_goal", "forecast_asset",
                          "get_market_regime"]
        for tool in expected_tools:
            results.check(f"tool_{tool}", tool in tool_names, f"missing tool: {tool}")
    except Exception as e:
        results.check("tools_list_endpoint", False, str(e))

    # ── Phase 9: PPO Status ──────────────────────────────────────────
    print("\n[Phase 9] PPO Status...")
    try:
        r = requests.get(f"{BASE}/ppo/status", timeout=10)
        data = r.json()
        results.check("ppo_status_code", r.status_code == 200, f"status={r.status_code}")
        results.check("ppo_is_experimental", data.get("status") == "experimental",
                       f"status={data.get('status')}")
        results.check("ppo_has_requirements", "requirements_met" in data, "")
        results.check("ppo_not_production", all(not v for v in data.get("requirements_met", {}).values()),
                       "PPO must not be production-ready")
    except Exception as e:
        results.check("ppo_status_endpoint", False, str(e))

    # ── Summary ─────────────────────────────────────────────────────
    if results.failed > 0:
        print("\n--- FAIL DETAILS ---")
        for err in results.errors:
            print(f"  {err}")

    print("\n\n" + "=" * 60)
    total_passed = results.passed
    total_failed = results.failed
    print(f"  TOTAL: {total_passed} passed, {total_failed} failed")
    print(f"  Overall: {'ALL TESTS PASSED' if total_failed == 0 else 'SOME TESTS FAILED'}")
    print("=" * 60)

    return 0 if total_failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
