import unittest
import math
from datetime import datetime, timezone
import pandas as pd
from analysis_engine import MIN_CANDLES, MarketDataError, _parse_klines, analyze_market, calculate_indicators, calculate_risk, score_timeframe


def make_frame(direction="up", length=400):
    if direction == "up":
        close = [100.0 + 0.15 * i + 2.0 * math.sin(i * 0.21 + 1.5) for i in range(length)]
        volume = [100.0] * length
        volume[-1] = 150.0
    elif direction == "down":
        close = [300.0 - 0.15 * i + 2.0 * math.sin(i * 0.21) for i in range(length)]
        volume = [100.0] * length
        volume[-1] = 150.0
    else:
        close = [200.0 + (0.03 if i % 2 else -0.03) for i in range(length)]
        volume = [100.0] * length
    return pd.DataFrame({"open": close, "high": [v + 0.25 for v in close], "low": [v - 0.25 for v in close], "close": close, "volume": volume})


class IndicatorAndSignalTests(unittest.TestCase):
    def test_bullish_signal_requires_confirmation(self):
        frame = make_frame("up")
        result = score_timeframe(frame)
        self.assertGreater(result["long_score"], result["short_score"])
        self.assertTrue(0 <= result["long_score"] <= 100)
        analysis = analyze_market("TEST/USDT", {"15m": frame, "1h": frame}, 1000, 1, 1)
        self.assertEqual(analysis["signal"], "BUY / LONG")

    def test_bearish_signal_requires_confirmation(self):
        frame = make_frame("down")
        result = score_timeframe(frame)
        self.assertGreater(result["short_score"], result["long_score"])
        self.assertTrue(0 <= result["short_score"] <= 100)
        analysis = analyze_market("TEST/USDT", {"15m": frame, "1h": frame}, 1000, 1, 1)
        self.assertEqual(analysis["signal"], "SELL / SHORT")

    def test_sideways_market_returns_wait(self):
        frame = make_frame("flat")
        result = score_timeframe(frame)
        self.assertLess(result["long_score"], 70)
        self.assertLess(result["short_score"], 70)
        self.assertEqual(analyze_market("TEST/USDT", {"15m": frame, "1h": frame}, 1000, 1, 1)["signal"], "WAIT / NO TRADE")

    def test_scores_are_always_bounded(self):
        for direction in ("up", "down", "flat"):
            result = score_timeframe(make_frame(direction))
            self.assertTrue(0 <= result["long_score"] <= 100)
            self.assertTrue(0 <= result["short_score"] <= 100)

    def test_ema200_rsi_and_atr_are_available(self):
        frame = calculate_indicators(make_frame("up"))
        for name in ("ema200", "rsi", "atr"):
            self.assertTrue(pd.notna(frame[name].iloc[-1]))

    def test_insufficient_candles_raise_clear_error(self):
        with self.assertRaises(MarketDataError):
            score_timeframe(make_frame("up", MIN_CANDLES - 1))


class RiskTests(unittest.TestCase):
    def test_long_stop_targets_quantity_notional_margin_and_loss(self):
        result = calculate_risk(100, 2, "LONG", 1000, 1, 2)
        self.assertEqual(result["stop"], 97)
        self.assertEqual(result["target1"], 104)
        self.assertEqual(result["target2"], 107)
        self.assertAlmostEqual(result["planned_loss"], 10)
        self.assertAlmostEqual(result["notional"], result["quantity"] * 100)
        self.assertAlmostEqual(result["margin"], result["notional"] / 2)

    def test_short_stop_targets_and_risk_reward(self):
        result = calculate_risk(100, 2, "SHORT", 1000, 1, 4)
        self.assertEqual(result["stop"], 103)
        self.assertEqual(result["target1"], 96)
        self.assertEqual(result["target2"], 93)
        self.assertAlmostEqual(result["planned_loss"], 10)
        self.assertAlmostEqual(result["rr_target1"], 2 / 1.5)

    def test_invalid_risk_inputs_are_rejected(self):
        with self.assertRaises(ValueError):
            calculate_risk(100, 0, "LONG", 1000, 1, 1)


class CandleParsingTests(unittest.TestCase):
    def test_incomplete_candle_is_excluded(self):
        now = datetime(2026, 10, 20, tzinfo=timezone.utc)
        base = int(datetime(2026, 10, 1, tzinfo=timezone.utc).timestamp() * 1000)
        rows = []
        for i in range(MIN_CANDLES + 1):
            opened = base + i * 60000
            closed = opened + 59999
            if i == MIN_CANDLES:
                closed = int(now.timestamp() * 1000) + 60000
            rows.append([opened, "100", "101", "99", "100.5", "10", closed])
        self.assertEqual(len(_parse_klines(rows, "TESTUSDT", now)), MIN_CANDLES)


if __name__ == "__main__":
    unittest.main()
