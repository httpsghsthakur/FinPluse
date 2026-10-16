"""
TensorFlow / Keras LSTM Forecasting Service for FinPulse.

Implements sequential neural network forecasting with:
- Feature scaling via MinMaxScaler
- Strict chronological train/test splitting (zero lookahead leakage)
- Sliding-window sequence construction
- Keras LSTM Sequential architecture
- Inverse transformation back to real price scale
- Chronological test evaluation metrics (MAE, RMSE)
"""
from __future__ import annotations

import logging
import os
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
import numpy as np
import pandas as pd
from sklearn.preprocessing import MinMaxScaler

logger = logging.getLogger(__name__)


def create_sequences(
    data: np.ndarray,
    seq_length: int,
) -> Tuple[np.ndarray, np.ndarray]:
    """Generate input sequences X and targets y without lookahead leakage.
    
    X[i] contains data[i : i + seq_length]
    y[i] contains data[i + seq_length]
    """
    xs, ys = [], []
    for i in range(len(data) - seq_length):
        xs.append(data[i : i + seq_length])
        ys.append(data[i + seq_length])
    return np.array(xs), np.array(ys)


class LSTMService:
    """TensorFlow/Keras LSTM Forecaster for stock price sequences."""

    @staticmethod
    def forecast(
        df: pd.DataFrame,
        seq_length: int = 15,
        horizon_days: int = 14,
        epochs: int = 25,
        batch_size: int = 16,
        test_ratio: float = 0.2,
    ) -> Dict[str, Any]:
        """Train or evaluate LSTM model on historical price series and project forward.
        
        Args:
            df: DataFrame containing 'timestamp' (or 'date') and 'close' (or 'price').
            seq_length: Number of historical days used in each input sequence window.
            horizon_days: Number of days forward to project.
            epochs: Training epochs for convergence.
            batch_size: Batch size for training.
            test_ratio: Proportion of series reserved for chronological hold-out test.
            
        Returns:
            Dict containing:
                - status: 'success' or 'error'
                - model: 'TensorFlow/Keras LSTM'
                - forecast: List of dicts with 'date' and 'predicted'
                - metrics: Dict with 'mae', 'rmse', 'test_points'
                - parameters: Dict with 'seq_length', 'epochs', 'history_points'
        """
        # Validate data
        if df is None or df.empty:
            return {"status": "error", "message": "Input dataframe is empty."}

        val_col = "close" if "close" in df.columns else ("price" if "price" in df.columns else df.columns[-1])
        date_col = "timestamp" if "timestamp" in df.columns else ("date" if "date" in df.columns else df.columns[0])

        clean_df = pd.DataFrame()
        clean_df["timestamp"] = pd.to_datetime(df[date_col]).dt.tz_localize(None)
        clean_df["close"] = pd.to_numeric(df[val_col], errors="coerce")
        clean_df = clean_df.dropna().sort_values(by="timestamp").reset_index(drop=True)

        min_required = seq_length * 2 + 10
        if len(clean_df) < min_required:
            return {
                "status": "error",
                "message": f"Insufficient data for LSTM ({len(clean_df)} points, minimum {min_required} required).",
            }

        prices = clean_df["close"].values.reshape(-1, 1)

        # Chronological hold-out partition
        split_idx = int(len(prices) * (1.0 - test_ratio))
        train_raw = prices[:split_idx]
        test_raw = prices[split_idx:]

        # Fit scaler ONLY on train data to prevent data leakage
        scaler = MinMaxScaler(feature_range=(0.0, 1.0))
        train_scaled = scaler.fit_transform(train_raw)

        # Scale full series with the fitted scaler
        full_scaled = scaler.transform(prices)

        # Create training sequences
        x_train, y_train = create_sequences(train_scaled, seq_length)
        if len(x_train) < 5:
            return {
                "status": "error",
                "message": "Not enough training sequences generated.",
            }

        # Build Keras LSTM model
        try:
            # Set random seeds for reproducibility
            import tensorflow as tf
            from tensorflow.keras.layers import Input, LSTM, Dense, Dropout
            from tensorflow.keras.models import Sequential
            from tensorflow.keras.callbacks import EarlyStopping

            tf.random.set_seed(42)
            np.random.seed(42)

            model = Sequential([
                Input(shape=(seq_length, 1)),
                LSTM(units=32, return_sequences=True),
                Dropout(0.15),
                LSTM(units=16, return_sequences=False),
                Dropout(0.15),
                Dense(units=8, activation="relu"),
                Dense(units=1),
            ])

            model.compile(optimizer="adam", loss="mean_squared_error")

            early_stop = EarlyStopping(monitor="loss", patience=5, restore_best_weights=True)

            # Fit model
            model.fit(
                x_train,
                y_train,
                epochs=epochs,
                batch_size=batch_size,
                verbose=0,
                callbacks=[early_stop],
            )

        except Exception as tf_err:
            logger.error(f"TensorFlow/Keras model compilation or fit failed: {tf_err}")
            return {
                "status": "error",
                "message": f"TensorFlow LSTM engine error: {str(tf_err)}",
            }

        # Chronological Hold-Out Evaluation
        metrics: Optional[Dict[str, Any]] = None
        try:
            # Use data up to split point to prepare test inputs
            test_inputs = full_scaled[split_idx - seq_length :]
            x_test, y_test_scaled = create_sequences(test_inputs, seq_length)

            if len(x_test) > 0:
                y_pred_scaled = model(x_test, training=False).numpy()
                y_pred_eval = scaler.inverse_transform(y_pred_scaled).flatten()
                y_true_eval = scaler.inverse_transform(y_test_scaled).flatten()

                mae = float(np.mean(np.abs(y_true_eval - y_pred_eval)))
                rmse = float(np.sqrt(np.mean((y_true_eval - y_pred_eval) ** 2)))

                test_start_dt = clean_df["timestamp"].iloc[split_idx].strftime("%Y-%m-%d")
                test_end_dt = clean_df["timestamp"].iloc[-1].strftime("%Y-%m-%d")

                metrics = {
                    "mae": round(mae, 2),
                    "rmse": round(rmse, 2),
                    "test_points": int(len(y_true_eval)),
                    "evaluation_period": f"{test_start_dt} to {test_end_dt}",
                }
        except Exception as eval_err:
            logger.warning(f"LSTM hold-out evaluation warning: {eval_err}")

        # Multi-Step Future Recursive Projection
        try:
            last_sequence = full_scaled[-seq_length:].copy().reshape(1, seq_length, 1)
            future_predictions_scaled = []

            curr_seq = last_sequence.copy()
            for _ in range(horizon_days):
                pred_tensor = model(curr_seq, training=False)
                next_pred = float(pred_tensor.numpy()[0, 0])
                future_predictions_scaled.append(next_pred)

                # Slide window forward by 1 step
                next_reshaped = np.array([[[next_pred]]])
                curr_seq = np.append(curr_seq[:, 1:, :], next_reshaped, axis=1)

            future_preds = scaler.inverse_transform(
                np.array(future_predictions_scaled).reshape(-1, 1)
            ).flatten()

            # Generate future business/calendar dates
            last_date = clean_df["timestamp"].iloc[-1]
            forecast_items: List[Dict[str, Any]] = []

            for i, p_val in enumerate(future_preds):
                f_date = last_date + timedelta(days=i + 1)
                forecast_items.append({
                    "date": f_date.strftime("%Y-%m-%d"),
                    "predicted": round(float(p_val), 2),
                })

            last_close = float(clean_df["close"].iloc[-1])
            final_pred = forecast_items[-1]["predicted"] if forecast_items else last_close
            trend_pct = ((final_pred - last_close) / last_close) * 100 if last_close != 0 else 0.0

            return {
                "status": "success",
                "model": "TensorFlow/Keras LSTM",
                "horizon_days": horizon_days,
                "history_points": len(clean_df),
                "last_actual_price": round(last_close, 2),
                "projected_price": round(final_pred, 2),
                "projected_change_percent": round(trend_pct, 2),
                "forecast": forecast_items,
                "metrics": metrics,
                "parameters": {
                    "sequence_length": seq_length,
                    "epochs": epochs,
                    "batch_size": batch_size,
                },
            }

        except Exception as proj_err:
            logger.error(f"LSTM projection failed: {proj_err}")
            return {
                "status": "error",
                "message": f"LSTM forward projection error: {str(proj_err)}",
            }
