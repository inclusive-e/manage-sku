"""Hybrid Analysis Pipeline for Smart Heuristic Selection

Analyzes SKU data characteristics and selects the best forecasting
heuristic through a hybrid approach: analyze + backtest.

Pure heuristics, no ML models. Transparent reasoning per-SKU.
"""

from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd
import statsmodels.api as sm

from app.services.heuristic_forecaster import HeuristicForecaster


class AnalysisPipeline:
    """
    Hybrid analysis pipeline for smart heuristic selection.

    Combines data characteristic analysis with backtesting to select
    the optimal forecasting method for each SKU.

    Usage:
        pipeline = AnalysisPipeline()
        result = pipeline.select_best_method(df)
        # result contains selected_method, analysis, reasoning
    """

    def __init__(self):
        self.forecaster = HeuristicForecaster()

    def analyze_data(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Analyze SKU data characteristics.

        Calculates:
        - Intermittency (% zero sales days)
        - Seasonality (weekly pattern strength via autocorrelation at lag 7)
        - Trend (R-squared, slope using linear regression)
        - Volatility (coefficient of variation = std/mean)
        - Data quality (days of history, completeness)

        Args:
            df: DataFrame with 'sales_quantity' column and date index

        Returns:
            Dict containing analysis metrics
        """
        # Handle edge cases
        if df is None or len(df) == 0:
            return {
                "intermittency": 0.0,
                "seasonality_strength": 0.0,
                "trend_r_squared": 0.0,
                "trend_slope": 0.0,
                "volatility_cv": 0.0,
                "days_of_history": 0,
                "completeness": 0.0,
                "mean_sales": 0.0,
                "std_sales": 0.0,
                "total_sales": 0.0,
            }

        sales = df["sales_quantity"].values
        n = len(sales)

        # Intermittency: % of zero sales days
        zero_count = np.sum(sales == 0)
        intermittency = zero_count / n if n > 0 else 0.0

        # Data quality metrics
        days_of_history = n
        completeness = 1.0  # Assumes complete daily series from data processor

        # Basic statistics
        mean_sales = float(np.mean(sales))
        std_sales = float(np.std(sales)) if n > 1 else 0.0
        total_sales = float(np.sum(sales))

        # Volatility: Coefficient of variation (std/mean)
        # Use CV only if mean is significantly positive
        if mean_sales > 0.01:
            volatility_cv = std_sales / mean_sales
        else:
            volatility_cv = 0.0 if std_sales == 0 else float("inf")

        # Seasonality: Autocorrelation at lag 7 (weekly pattern)
        seasonality_strength = 0.0
        if n >= 14:  # Need at least 2 weeks of data
            try:
                # Calculate autocorrelation at lag 7
                sales_series = pd.Series(sales)
                autocorr = sales_series.autocorr(lag=7)
                seasonality_strength = abs(autocorr) if not np.isnan(autocorr) else 0.0
            except Exception:
                seasonality_strength = 0.0

        # Trend: Linear regression R-squared and slope using statsmodels
        trend_r_squared = 0.0
        trend_slope = 0.0
        if n >= 7:  # Need at least a week for meaningful trend
            try:
                x = np.arange(n)
                # Remove NaN values
                mask = ~np.isnan(sales)
                if np.sum(mask) >= 3:  # Need at least 3 points for regression
                    # Use statsmodels OLS for better time series analysis
                    x_clean = x[mask]
                    y_clean = sales[mask]
                    x_with_const = sm.add_constant(x_clean)
                    model = sm.OLS(y_clean, x_with_const)
                    results = model.fit()
                    trend_r_squared = results.rsquared
                    trend_slope = results.params[1]  # slope is the second parameter
            except Exception:
                trend_r_squared = 0.0
                trend_slope = 0.0

        return {
            "intermittency": round(float(intermittency), 4),
            "seasonality_strength": round(float(seasonality_strength), 4),
            "trend_r_squared": round(float(trend_r_squared), 4),
            "trend_slope": round(float(trend_slope), 4),
            "volatility_cv": round(float(volatility_cv), 4),
            "days_of_history": int(days_of_history),
            "completeness": round(float(completeness), 4),
            "mean_sales": round(float(mean_sales), 4),
            "std_sales": round(float(std_sales), 4),
            "total_sales": round(float(total_sales), 4),
        }

    def select_candidate_methods(self, analysis: Dict[str, Any]) -> List[str]:
        """
        Select candidate forecasting methods based on data analysis.

        Selection rules:
        - Intermittent (>30% zeros) → ['croston'] (basic version)
        - Strong trend (R²>0.7) → ['with_trend', 'weighted_average']
        - Strong seasonality (>0.6) → ['seasonal_naive', 'weighted_average']
        - High volatility (CV>1.0) → ['rolling_mean_28d', 'weighted_average']
        - Short history (<60 days) → ['naive', 'rolling_mean_7d']
        - Default → ['weighted_average', 'rolling_mean_28d', 'naive']

        Args:
            analysis: Dict from analyze_data() with data characteristics

        Returns:
            List of method names to consider for backtesting
        """
        candidates = set()

        # Rule 1: Intermittent demand (>30% zeros)
        if analysis.get("intermittency", 0) > 0.30:
            candidates.add("croston")
            # For intermittent data, also consider simple methods
            candidates.add("rolling_mean_28d")
            return list(candidates) if candidates else ["weighted_average"]

        # Rule 2: Strong trend (R² > 0.7)
        if analysis.get("trend_r_squared", 0) > 0.7:
            candidates.add("with_trend")
            candidates.add("weighted_average")

        # Rule 3: Strong seasonality (>0.6 autocorrelation)
        if analysis.get("seasonality_strength", 0) > 0.6:
            candidates.add("seasonal_naive")
            if "weighted_average" not in candidates:
                candidates.add("weighted_average")

        # Rule 4: High volatility (CV > 1.0)
        cv = analysis.get("volatility_cv", 0)
        if cv > 1.0 and cv != float("inf"):
            candidates.add("rolling_mean_28d")
            if "weighted_average" not in candidates:
                candidates.add("weighted_average")

        # Rule 5: Short history (<60 days)
        if analysis.get("days_of_history", 0) < 60:
            candidates.add("naive")
            candidates.add("rolling_mean_7d")
            # Remove methods that need more data
            candidates.discard("seasonal_naive")
            candidates.discard("with_trend")

        # Default fallback
        if not candidates:
            candidates = {"weighted_average", "rolling_mean_28d", "naive"}

        # Always ensure we have at least one simple method as fallback
        if not any(m in candidates for m in ["naive", "weighted_average"]):
            candidates.add("weighted_average")

        return list(candidates)

    def _croston_forecast(
        self, df: pd.DataFrame, horizon: int
    ) -> pd.DataFrame:
        """
        Basic Croston's method for intermittent demand.

        Separates demand size and inter-demand intervals.
        Simplified version for MVP.

        Args:
            df: DataFrame with 'sales_quantity' column
            horizon: Number of periods to forecast

        Returns:
            DataFrame with forecast and method columns
        """
        if len(df) == 0:
            return pd.DataFrame(
                {"forecast": [0.0] * horizon, "method": ["croston"] * horizon}
            )

        sales = df["sales_quantity"].values

        # Find demand occurrences (non-zero sales)
        demand_periods = np.where(sales > 0)[0]

        if len(demand_periods) == 0:
            # No demand observed
            return pd.DataFrame(
                {"forecast": [0.0] * horizon, "method": ["croston"] * horizon}
            )

        if len(demand_periods) == 1:
            # Single demand event - use simple average
            avg_demand = sales[demand_periods].mean()
            return pd.DataFrame(
                {
                    "forecast": [float(avg_demand)] * horizon,
                    "method": ["croston"] * horizon,
                }
            )

        # Calculate demand sizes (non-zero values)
        demand_sizes = sales[demand_periods]

        # Calculate inter-demand intervals
        intervals = np.diff(demand_periods)

        # Simple exponential smoothing for demand size and interval
        alpha = 0.1  # Smoothing parameter

        # Initialize with simple averages
        smoothed_size = np.mean(demand_sizes)
        smoothed_interval = np.mean(intervals) if len(intervals) > 0 else 1.0

        # Apply smoothing
        for size in demand_sizes:
            smoothed_size = alpha * size + (1 - alpha) * smoothed_size

        for interval in intervals:
            smoothed_interval = alpha * interval + (1 - alpha) * smoothed_interval

        # Forecast = smoothed_size / smoothed_interval
        if smoothed_interval > 0:
            forecast_val = smoothed_size / smoothed_interval
        else:
            forecast_val = smoothed_size

        return pd.DataFrame(
            {
                "forecast": [float(forecast_val)] * horizon,
                "method": ["croston"] * horizon,
            }
        )

    def backtest_methods(
        self, df: pd.DataFrame, methods: List[str], test_days: int = 7
    ) -> Dict[str, float]:
        """
        Backtest candidate methods and calculate MAE for each.

        Splits data into train (all but last test_days) and test (last test_days),
        generates forecasts for each method, and calculates MAE.

        Args:
            df: DataFrame with 'sales_quantity' column
            methods: List of method names to backtest
            test_days: Number of days to use for testing (default: 7)

        Returns:
            Dict mapping method names to MAE scores
        """
        # Handle edge cases
        if df is None or len(df) == 0:
            return {method: float("inf") for method in methods}

        # Need enough data for train/test split
        if len(df) < test_days + 7:
            # Not enough data - return equal high error for all
            return {method: float("inf") for method in methods}

        # Split data
        train_data = df.iloc[:-test_days].copy()
        test_data = df.iloc[-test_days:].copy()

        actual = test_data["sales_quantity"].values

        backtest_results = {}

        for method in methods:
            try:
                # Generate forecast
                if method == "croston":
                    pred_df = self._croston_forecast(train_data, test_days)
                elif method == "naive":
                    pred_df = self.forecaster.forecast_naive(train_data, test_days)
                elif method == "rolling_mean_7d":
                    pred_df = self.forecaster.forecast_rolling_mean(
                        train_data, test_days, 7
                    )
                elif method == "rolling_mean_28d":
                    pred_df = self.forecaster.forecast_rolling_mean(
                        train_data, test_days, 28
                    )
                elif method == "seasonal_naive":
                    pred_df = self.forecaster.forecast_seasonal_naive(
                        train_data, test_days, 28
                    )
                elif method == "weighted_average":
                    pred_df = self.forecaster.forecast_weighted_average(
                        train_data, test_days
                    )
                elif method == "with_trend":
                    pred_df = self.forecaster.forecast_with_trend(train_data, test_days)
                else:
                    # Unknown method
                    backtest_results[method] = float("inf")
                    continue

                pred = pred_df["forecast"].values

                # Calculate MAE
                if len(pred) == len(actual):
                    mae = float(np.mean(np.abs(pred - actual)))
                else:
                    # Handle length mismatch
                    min_len = min(len(pred), len(actual))
                    mae = float(np.mean(np.abs(pred[:min_len] - actual[:min_len])))

                backtest_results[method] = round(mae, 4)

            except Exception:
                backtest_results[method] = float("inf")

        return backtest_results

    def select_best_method(
        self, df: pd.DataFrame, test_days: int = 7
    ) -> Dict[str, Any]:
        """
        Select the best forecasting method using hybrid analyze+backtest approach.

        Process:
        1. Analyze data characteristics
        2. Select candidate methods based on analysis
        3. Backtest candidates and calculate MAE
        4. Select method with lowest MAE
        5. Generate transparent reasoning

        Args:
            df: DataFrame with 'sales_quantity' column
            test_days: Number of days for backtesting (default: 7)

        Returns:
            Dict containing:
                - selected_method: str
                - analysis: Dict (from analyze_data)
                - backtest_results: Dict (method names and MAE scores)
                - reasoning: str (explanation of selection)
        """
        # Step 1: Analyze data
        analysis = self.analyze_data(df)

        # Handle empty data
        if analysis["days_of_history"] == 0:
            return {
                "selected_method": "naive",
                "analysis": analysis,
                "backtest_results": {},
                "reasoning": "No data available. Defaulting to naive method.",
            }

        # Step 2: Select candidate methods
        candidates = self.select_candidate_methods(analysis)

        # Step 3: Backtest candidates
        backtest_results = self.backtest_methods(df, candidates, test_days)

        # Step 4: Select best method (lowest MAE)
        if not backtest_results:
            selected_method = "weighted_average"
        else:
            # Filter out infinite errors
            valid_results = {
                k: v for k, v in backtest_results.items() if v != float("inf")
            }

            if valid_results:
                selected_method = min(valid_results, key=valid_results.get)
            else:
                # All methods failed, use default
                selected_method = "weighted_average"

        # Step 5: Generate reasoning
        reasoning_parts = []

        # Add data characteristics to reasoning
        if analysis["intermittency"] > 0.30:
            reasoning_parts.append(
                f"intermittent demand ({analysis['intermittency']:.1%} zero days)"
            )

        if analysis["trend_r_squared"] > 0.7:
            trend_direction = "upward" if analysis["trend_slope"] > 0 else "downward"
            reasoning_parts.append(
                f"strong {trend_direction} trend (R²={analysis['trend_r_squared']:.2f})"
            )

        if analysis["seasonality_strength"] > 0.6:
            reasoning_parts.append(
                f"strong seasonality (autocorr={analysis['seasonality_strength']:.2f})"
            )

        if analysis["volatility_cv"] > 1.0 and analysis["volatility_cv"] != float(
            "inf"
        ):
            reasoning_parts.append(
                f"high volatility (CV={analysis['volatility_cv']:.2f})"
            )

        if analysis["days_of_history"] < 60:
            reasoning_parts.append(f"short history ({analysis['days_of_history']} days)")

        # Get MAE for selected method
        selected_mae = backtest_results.get(selected_method, float("inf"))
        if selected_mae == float("inf"):
            mae_str = "N/A"
        else:
            mae_str = f"{selected_mae:.2f}"

        # Build final reasoning string
        if reasoning_parts:
            characteristics = ", ".join(reasoning_parts)
            reasoning = f"Selected '{selected_method}' based on {characteristics} and lowest backtest error (MAE={mae_str})"
        else:
            reasoning = f"Selected '{selected_method}' based on lowest backtest error (MAE={mae_str})"

        return {
            "selected_method": selected_method,
            "analysis": analysis,
            "backtest_results": backtest_results,
            "reasoning": reasoning,
        }

    def get_method_recommendation(
        self, df: pd.DataFrame, quick: bool = False
    ) -> Dict[str, Any]:
        """
        Get method recommendation with optional quick mode.

        Quick mode skips backtesting and uses heuristics only.
        Full mode runs complete analyze+backtest pipeline.

        Args:
            df: DataFrame with 'sales_quantity' column
            quick: If True, skip backtesting (default: False)

        Returns:
            Dict with selected_method, analysis, and reasoning
        """
        analysis = self.analyze_data(df)
        candidates = self.select_candidate_methods(analysis)

        if quick or len(df) < 14:  # Not enough data for backtesting
            # Use first candidate as best guess
            selected = candidates[0] if candidates else "weighted_average"

            reasoning_parts = []
            if analysis["intermittency"] > 0.30:
                reasoning_parts.append("intermittent demand detected")
            if analysis["trend_r_squared"] > 0.7:
                reasoning_parts.append("strong trend detected")
            if analysis["seasonality_strength"] > 0.6:
                reasoning_parts.append("strong seasonality detected")

            if reasoning_parts:
                reason_str = ", ".join(reasoning_parts)
                reasoning = f"Selected '{selected}' based on {reason_str} (quick mode, no backtesting)"
            else:
                reasoning = f"Selected '{selected}' as default method (quick mode)"

            return {
                "selected_method": selected,
                "analysis": analysis,
                "backtest_results": {},
                "reasoning": reasoning,
            }

        # Full analysis with backtesting
        return self.select_best_method(df)
