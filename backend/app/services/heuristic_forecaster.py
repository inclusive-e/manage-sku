"""MVP Heuristic Forecasting Service

Simple, explainable forecasts without ML models.
Rule-based heuristics that work immediately.
"""

from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd


class HeuristicForecaster:
    """
    Simple heuristic forecasts - no ML models needed

    Methods:
    1. naive: Last value
    2. rolling_mean: Average of last N days
    3. seasonal_naive: Value from same time last season
    4. weighted_average: Weighted combination of recent periods
    5. with_trend: Naive + trend component
    """

    def __init__(self):
        self.methods = {
            "naive": self.forecast_naive,
            "rolling_mean_7d": lambda df, h: self.forecast_rolling_mean(df, h, 7),
            "rolling_mean_28d": lambda df, h: self.forecast_rolling_mean(df, h, 28),
            "seasonal_naive": self.forecast_seasonal_naive,
            "weighted_average": self.forecast_weighted_average,
            "with_trend": self.forecast_with_trend,
        }

    def forecast_naive(self, df: pd.DataFrame, horizon: int) -> pd.DataFrame:
        """Naive forecast: Use last observed value"""
        if len(df) == 0:
            return pd.DataFrame(
                {"forecast": [0.0] * horizon, "method": ["naive"] * horizon}
            )

        last_value = df["sales_quantity"].iloc[-1]
        return pd.DataFrame(
            {"forecast": [float(last_value)] * horizon, "method": ["naive"] * horizon}
        )

    def forecast_rolling_mean(
        self, df: pd.DataFrame, horizon: int, window: int = 28
    ) -> pd.DataFrame:
        """Rolling mean forecast: Average of last N days"""
        if len(df) == 0:
            return pd.DataFrame(
                {
                    "forecast": [0.0] * horizon,
                    "method": [f"rolling_mean_{window}d"] * horizon,
                }
            )

        mean_value = df["sales_quantity"].tail(window).mean()

        return pd.DataFrame(
            {
                "forecast": [float(mean_value)] * horizon,
                "method": [f"rolling_mean_{window}d"] * horizon,
            }
        )

    def forecast_seasonal_naive(
        self, df: pd.DataFrame, horizon: int, season_length: int = 28
    ) -> pd.DataFrame:
        """Seasonal naive forecast: Use value from same time last season"""
        if len(df) < season_length:
            return self.forecast_rolling_mean(df, horizon, 7)

        seasonal_values = []
        for i in range(horizon):
            idx = -(season_length - i)
            if abs(idx) <= len(df):
                val = df["sales_quantity"].iloc[idx]
                seasonal_values.append(float(val))
            else:
                val = df["sales_quantity"].mean()
                seasonal_values.append(float(val))

        return pd.DataFrame(
            {"forecast": seasonal_values, "method": ["seasonal_naive_28d"] * horizon}
        )

    def forecast_weighted_average(self, df: pd.DataFrame, horizon: int) -> pd.DataFrame:
        """Weighted average: 50% last 7d, 30% last 28d, 20% overall mean"""
        if len(df) == 0:
            return pd.DataFrame(
                {"forecast": [0.0] * horizon, "method": ["weighted_average"] * horizon}
            )

        val_7d = float(df["sales_quantity"].tail(7).mean())
        val_28d = (
            float(df["sales_quantity"].tail(28).mean()) if len(df) >= 28 else val_7d
        )
        val_long = float(df["sales_quantity"].mean())

        weights = {"last_7d": 0.5, "last_28d": 0.3, "long_term": 0.2}
        weighted_avg = (
            weights["last_7d"] * val_7d
            + weights["last_28d"] * val_28d
            + weights["long_term"] * val_long
        )

        return pd.DataFrame(
            {
                "forecast": [float(weighted_avg)] * horizon,
                "method": ["weighted_average"] * horizon,
            }
        )

    def forecast_with_trend(self, df: pd.DataFrame, horizon: int) -> pd.DataFrame:
        """Forecast with trend: continues recent growth/decline"""
        if len(df) < 14:
            return self.forecast_naive(df, horizon)

        recent_avg = df["sales_quantity"].tail(7).mean()
        previous_avg = df["sales_quantity"].iloc[-14:-7].mean()
        trend = recent_avg - previous_avg

        forecasts = []
        base = df["sales_quantity"].iloc[-1]
        for i in range(1, horizon + 1):
            forecast_val = base + (trend * i)
            forecast_val = max(0.0, forecast_val)
            forecasts.append(float(forecast_val))

        return pd.DataFrame({"forecast": forecasts, "method": ["with_trend"] * horizon})

    def select_best_heuristic(self, df: pd.DataFrame, test_days: int = 7) -> str:
        """Backtest heuristics and pick best one"""
        if len(df) < test_days + 7:
            return "rolling_mean_28d"

        test_data = df.iloc[-test_days:].copy()
        train_data = df.iloc[:-test_days].copy()

        methods_to_test = {
            "naive": self.forecast_naive,
            "rolling_mean_7d": lambda df, h: self.forecast_rolling_mean(df, h, 7),
            "rolling_mean_28d": lambda df, h: self.forecast_rolling_mean(df, h, 28),
            "weighted_average": self.forecast_weighted_average,
        }

        errors = {}
        actual = test_data["sales_quantity"].values

        for name, method in methods_to_test.items():
            try:
                pred_df = method(train_data, test_days)
                pred = pred_df["forecast"].values
                mae = np.mean(np.abs(pred - actual))
                errors[name] = mae
            except Exception:
                errors[name] = float("inf")

        return min(errors, key=errors.get)

    def generate_forecast(
        self, df: pd.DataFrame, horizon_weeks: int, method: Optional[str] = None
    ) -> Dict[str, Any]:
        """Generate forecast for a SKU"""
        if len(df) == 0:
            return {
                "method": "error",
                "historical_avg": 0,
                "historical_std": 0,
                "horizon_weeks": horizon_weeks,
                "weekly_forecasts": [
                    {"week": w, "forecast": 0.0, "lower_bound": 0.0, "upper_bound": 0.0}
                    for w in range(1, horizon_weeks + 1)
                ],
            }

        if method is None or method == "auto":
            method = self.select_best_heuristic(df)

        if method not in self.methods:
            method = "rolling_mean_28d"

        historical_std = float(df["sales_quantity"].std()) if len(df) > 1 else 0.0
        historical_avg = float(df["sales_quantity"].mean())

        # Generate daily forecasts
        horizon_days = horizon_weeks * 7
        forecast_df = self.methods[method](df, horizon_days)

        # Aggregate to weekly (last day of each week)
        weekly_forecasts = []
        for week in range(1, horizon_weeks + 1):
            idx = min(week * 7 - 1, len(forecast_df) - 1)
            if idx >= 0:
                fc = float(forecast_df.iloc[idx]["forecast"])
                weekly_forecasts.append(
                    {
                        "week": week,
                        "forecast": round(fc, 2),
                        "lower_bound": round(max(0.0, fc - historical_std), 2),
                        "upper_bound": round(max(0.0, fc + historical_std), 2),
                    }
                )

        return {
            "method": method,
            "historical_avg": round(historical_avg, 2),
            "historical_std": round(historical_std, 2),
            "horizon_weeks": horizon_weeks,
            "weekly_forecasts": weekly_forecasts,
        }


class ForecastEvaluator:
    """Evaluate forecast accuracy with standard metrics"""

    @staticmethod
    def calculate_metrics(actual: np.ndarray, forecast: np.ndarray) -> Dict[str, float]:
        """Calculate MAE, MAPE, RMSE, bias"""
        mask = ~(np.isnan(actual) | np.isnan(forecast))
        actual_clean = actual[mask]
        forecast_clean = forecast[mask]

        if len(actual_clean) == 0:
            return {"mae": 0.0, "mape": 0.0, "rmse": 0.0, "bias": 0.0}

        mae = np.mean(np.abs(actual_clean - forecast_clean))
        mape = (
            np.mean(np.abs((actual_clean - forecast_clean) / (actual_clean + 1e-8)))
            * 100
        )
        rmse = np.sqrt(np.mean((actual_clean - forecast_clean) ** 2))
        bias = np.mean(forecast_clean - actual_clean)

        return {
            "mae": round(float(mae), 2),
            "mape": round(float(mape), 2),
            "rmse": round(float(rmse), 2),
            "bias": round(float(bias), 2),
        }

    @staticmethod
    def backtest_all_methods(
        df: pd.DataFrame, test_days: int = 7
    ) -> List[Dict[str, Any]]:
        """Backtest all heuristics and return comparison"""
        if len(df) < test_days + 7:
            return []

        test_data = df.iloc[-test_days:].copy()
        train_data = df.iloc[:-test_days].copy()
        actual = test_data["sales_quantity"].values

        forecaster = HeuristicForecaster()
        methods_to_test = {
            "naive": forecaster.forecast_naive,
            "rolling_mean_7d": lambda df, h: forecaster.forecast_rolling_mean(df, h, 7),
            "rolling_mean_28d": lambda df, h: forecaster.forecast_rolling_mean(
                df, h, 28
            ),
            "weighted_average": forecaster.forecast_weighted_average,
            "with_trend": forecaster.forecast_with_trend,
        }

        results = []
        for name, method in methods_to_test.items():
            try:
                pred_df = method(train_data, test_days)
                pred = pred_df["forecast"].values
                metrics = ForecastEvaluator.calculate_metrics(actual, pred)
                results.append({"method": name, **metrics, "selected": False})
            except Exception as e:
                results.append(
                    {
                        "method": name,
                        "mae": float("inf"),
                        "mape": float("inf"),
                        "rmse": float("inf"),
                        "bias": 0.0,
                        "error": str(e),
                        "selected": False,
                    }
                )

        results.sort(key=lambda x: x["mae"])
        if results:
            results[0]["selected"] = True

        return results
